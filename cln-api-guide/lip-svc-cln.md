# lip-svc-cln

## lip-svc-cln｜CLN 組合層 API（前端入口）

## 專案架構

前端 lip-web-cln 的 `/api/` 請求都進到這裡（LIP-C 電文）。它負責檢查上行，依電文 ID 透過 `restTempHelper` 呼叫 query、transaction、common、todo 等基礎層服務（LIP-B 電文），再組合回應給前端；部分功能也會直接查資料庫。程式中的呼叫次數：CQY 130、CTN 60、CCM 25、CTO 9。

| 觀察面向 | 目前程式可見內容 | 閱讀提示 |
| --- | --- | --- |
| 專案型態 | Java 8、Spring Boot REST application；POM 直接依賴 `lip-lib-auth` 與 `CommonZR`。 | 依賴版本和執行設定需以各環境為準；POM 不足以證明部署拓樸。 |
| API 路徑 | Controller 類別路徑包含 `/api/case`、`/api/approval`、`/api/review` 等。 | 這是前端呼叫的路徑；基礎層的路徑沒有 `/api` 前綴（如 query 的 `/case/inputInfo/query`）。 |
| 案件功能 | 基本資料、進件輸入、申請條件、起案、撤件及財所清等查詢/維護功能。 | CaseController 同時有 query 和 update，依電文 ID 區分行為。 |
| 其他功能 | 核決、覆核、信用、派件、商品、規則引擎與報表等 Controller。 | 這裡只概述程式入口分類；詳情仍需讀各功能規格與 Service。 |

## API 慣例

Controller 依 `/api/case`、`/api/approval` 等功能分組，常見 POST 與 RequestTemplate/ResponseTemplate。此服務的電文（LIP-C）與基礎層（LIP-B）是兩套，新功能通常兩邊各一支，功能碼相同，例如 CLNCINPTC001 ↔ CQYCINPTQ001。

## 實作流程

**選定功能入口** 從 API group 找 Controller

**核對電文契約** 追 Tranrq/Tranrs 和驗證

**追蹤 Service** 確認查詢/異動與整合

**核對資料元件** Repository、Entity 與 SQL

**比對消費端** 確認使用的服務版本

## 完整案例

以 `POST /api/case/baseInfo/query` 和 `POST /api/case/baseInfo/update` 作為查詢/維護對照，沿 CaseController 追到對應電文與 Service。

**pom.xml 專案依賴與 Java 版本 XML · 89 行**

lip-svc-cln/pom.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>cub.cloud</groupId>
        <artifactId>cub-cloud</artifactId>
        <version>1.1.1</version>
        <relativePath/><!-- lookup parent from repository -->
    </parent>

    <groupId>cub.lip</groupId>
    <artifactId>lip-svc-cln</artifactId>
    <properties>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <java.version>1.8</java.version>
        <tomcat.version>9.0.102</tomcat.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>cub.lip</groupId>
            <artifactId>lip-lib-auth</artifactId>
            <version>1.1.07-SNAPSHOT</version>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
            <scope>provided</scope>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web-services</artifactId>
        </dependency>

        <dependency>
            <groupId>ebaf.bank.subsys</groupId>
            <artifactId>CommonZR</artifactId>
            <version>1.0.1</version>
        </dependency>

        <!-- axis 1.4 -->
        <dependency>
            <groupId>commons-discovery</groupId>
            <artifactId>commons-discovery</artifactId>
            <version>0.2</version>
            <exclusions>
                <exclusion>
                    <groupId>commons-logging</groupId>
                    <artifactId>commons-logging</artifactId>
                </exclusion>
            </exclusions>
        </dependency>
        <dependency>
            <groupId>org.apache.axis</groupId>
            <artifactId>axis</artifactId>
            <version>1.4</version>
        </dependency>
        <dependency>
            <groupId>org.apache.axis</groupId>
            <artifactId>axis-jaxrpc</artifactId>
            <version>1.4</version>
        </dependency>
        <dependency>
            <groupId>org.apache.axis</groupId>
            <artifactId>axis-saaj</artifactId>
            <version>1.4</version>
        </dependency>
        <dependency>
            <groupId>wsdl4j</groupId>
            <artifactId>wsdl4j</artifactId>
        </dependency>
    </dependencies>
    <build>
        <finalName>lip-svc-cln</finalName>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
```

**ClnRestApplication.java Spring Boot 啟動類別 Java · 17 行**

lip-svc-cln/src/main/java/cub/lip/svc/cln/ClnRestApplication.java

```java
package cub.lip.svc.cln;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
@EnableCaching
@EnableAsync
public class ClnRestApplication {

    public static void main(String[] args) {
        SpringApplication.run(ClnRestApplication.class, args);
    }

}
```

**CaseController.java /api/case 基本資料與進件功能 Java · 389 行**

lip-svc-cln/src/main/java/cub/lip/svc/cln/controller/CaseController.java

```java
package cub.lip.svc.cln.controller;

import cub.lip.lib.common.controller.BaseController;
import cub.lip.lib.common.dto.base.EmptyDto;
import cub.lip.lib.common.dto.base.RequestTemplate;
import cub.lip.lib.common.dto.base.ResponseTemplate;
import cub.lip.lib.common.exception.RestException;
import cub.lip.svc.cln.dto.cln.*;
import cub.lip.svc.cln.svc.*;
import io.swagger.v3.oas.annotations.Operation;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.Errors;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;
import javax.validation.Valid;

/**
 * CaseController
 */
@RestController
@RequestMapping(value = "/api/case", consumes = MediaType.APPLICATION_JSON_VALUE)
public class CaseController extends BaseController {

    /** CLNBASIFC001Svc 基本資料查詢 */
    @Autowired
    private CLNBASIFC001Svc theCLNBASIFC001Svc;

    /** CLNBASIFC002Svc 基本資料維護 */
    @Autowired
    private CLNBASIFC002Svc theCLNBASIFC002Svc;

    /** CLNCHKTBC001Svc 進件主畫面頁籤檢核查詢 */
    @Autowired
    private CLNCHKTBC001Svc theCLNCHKTBC001Svc;

    /** CLNCINPTC001Svc 查詢進件輸入資訊 */
    @Autowired
    private CLNCINPTC001Svc theCLNCINPTC001Svc;

    /** CLNCINPTC002Svc 進件輸入維護 */
    @Autowired
    private CLNCINPTC002Svc theCLNCINPTC002Svc;

    /** CLNCITYAC001Svc 查詢所有縣市地區 */
    @Autowired
    private CLNCITYAC001Svc theCLNCITYAC001Svc;

    /** CLNIAPINC001Svc 查詢申請條件輸入資訊 */
    @Autowired
    private CLNIAPINC001Svc theCLNIAPINC001Svc;

    /** CLNIAPSEC001Svc 進件申請條件輸入送出 */
    @Autowired
    private CLNIAPSEC001Svc theCLNIAPSEC001Svc;

    /** CLNIAPSVC001Svc 進件申請條件輸入儲存 */
    @Autowired
    private CLNIAPSVC001Svc theCLNIAPSVC001Svc;

    /** CLNINITCC001Svc 新增起案 */
    @Autowired
    private CLNINITCC001Svc theCLNINITCC001Svc;

    /** CLNREJECC001Svc 撤件查詢 */
    @Autowired
    private CLNREJECC001Svc theCLNREJECC001Svc;

    /** CLNREJECC002Svc 撤件維護 */
    @Autowired
    private CLNREJECC002Svc theCLNREJECC002Svc;

    /** CLNCSMINC001Svc 進件主頁初始查詢 */
    @Autowired
    private CLNCSMINC001Svc theCLNCSMINC001Svc;

    /** CLNJCFINC001Svc 財所清清單查詢 */
    @Autowired
    private CLNJCFINC001Svc theCLNJCFINC001Svc;

    /** CLNJCFINC002Svc 財所清維護 */
    @Autowired
    private CLNJCFINC002Svc theCLNJCFINC002Svc;

    /** LIP-C-CLNJCFINC003 財所清重查 */
    @Autowired
    private CLNJCFINC003Svc theCLNJCFINC003Svc;

    /** CLNJCFINC004Svc 財所清附件查詢 */
    @Autowired
    private CLNJCFINC004Svc theCLNJCFINC004Svc;

    /**
     * LIP-C-CLNBASIFC001 基本資料查詢
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     */
    @PostMapping(value = "/baseInfo/query", produces = MediaType.APPLICATION_JSON_VALUE)
    @Operation(summary = "LIP-C-CLNBASIFC001 基本資料查詢")
    public ResponseTemplate<CLNBASIFC001Tranrs> queryBaseInfo(@Valid
    @RequestBody
    RequestTemplate<CLNBASIFC001Tranrq> req, Errors err) throws RestException {
        validateRequest(err);
        return theCLNBASIFC001Svc.queryBaseInfo(req);
    }

    /**
     * LIP-C-CLNBASIFC002 基本資料維護
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     */
    @PostMapping(value = "/baseInfo/update", produces = MediaType.APPLICATION_JSON_VALUE)
    @Operation(summary = "LIP-C-CLNBASIFC002 基本資料維護")
    public ResponseTemplate<EmptyDto> updateBaseInfo(@Valid
    @RequestBody
    RequestTemplate<CLNBASIFC002Tranrq> req, Errors err) throws RestException {
        validateRequest(err);
        return theCLNBASIFC002Svc.updateBaseInfo(req);
    }

    /**
     * LIP-C-CLNCHKTBC001 進件主畫面頁籤檢核查詢
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     */
    @PostMapping(value = "/tabsCheck/query", produces = MediaType.APPLICATION_JSON_VALUE)
    @Operation(summary = "LIP-C-CLNCHKTBC001 進件主畫面頁籤檢核查詢")
    public ResponseTemplate<CLNCHKTBC001Tranrs> queryTabsCheck(@Valid
    @RequestBody
    RequestTemplate<CLNCHKTBC001Tranrq> req, Errors err) throws RestException {
        validateRequest(err);
        return theCLNCHKTBC001Svc.queryTabsCheck(req);
    }

    /**
     * LIP-C-CLNCINPTC001 查詢進件輸入資訊
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     */
    @PostMapping(value = "/inputInfo/query", produces = MediaType.APPLICATION_JSON_VALUE)
    @Operation(summary = "LIP-C-CLNCINPTC001 查詢進件輸入資訊")
    public ResponseTemplate<CLNCINPTC001Tranrs> inputInfoQuery(@Valid
    @RequestBody
    RequestTemplate<CLNCINPTC001Tranrq> req, Errors err) throws RestException {
        validateRequest(err);
        return theCLNCINPTC001Svc.inputInfoQuery(req);
    }

    /**
     * LIP-C-CLNCINPTC002 進件輸入維護
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     */
    @PostMapping(value = "/inputInfo/modify", produces = MediaType.APPLICATION_JSON_VALUE)
    @Operation(summary = "LIP-C-CLNCINPTC002 進件輸入維護")
    public ResponseTemplate<EmptyDto> inputInfoModify(@Valid
    @RequestBody
    RequestTemplate<CLNCINPTC002Tranrq> req, Errors err) throws RestException {
        validateRequest(err);
        return theCLNCINPTC002Svc.inputInfoModify(req);
    }

    /**
     * LIP-C-CLNCITYAC001 查詢所有縣市地區
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     */
    @PostMapping(value = "/cityArea/query", produces = MediaType.APPLICATION_JSON_VALUE)
    @Operation(summary = "LIP-C-CLNCITYAC001 查詢所有縣市地區")
    public ResponseTemplate<CLNCITYAC001Tranrs> queryCityArea(@Valid
    @RequestBody
    RequestTemplate<EmptyDto> req, Errors err) throws RestException {
        validateRequest(err);
        return theCLNCITYAC001Svc.queryCityArea(req);
    }

    /**
     * LIP-C-CLNIAPINC001 查詢申請條件輸入資訊
     *
     * @param req
     * @param err
     * @return
     */
    @PostMapping(value = "/applyInput/query", produces = MediaType.APPLICATION_JSON_VALUE)
    @Operation(summary = "LIP-C-CLNIAPINC001 查詢申請條件輸入資訊")
    public ResponseTemplate<CLNIAPINC001Tranrs> queryApplyInput(@Valid
    @RequestBody
    RequestTemplate<CLNIAPINC001Tranrq> req, Errors err) {
        validateRequest(err);
        return theCLNIAPINC001Svc.queryApplyInput(req);
    }

    /**
     * LIP-C-CLNIAPSEC001 進件申請條件輸入送出
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     */
    @PostMapping(value = "/applyInput/send", produces = MediaType.APPLICATION_JSON_VALUE)
    @Operation(summary = "LIP-C-CLNIAPSEC001 進件申請條件輸入送出")
    public ResponseTemplate<EmptyDto> sendApplyInput(@Valid
    @RequestBody
    RequestTemplate<CLNIAPSEC001Tranrq> req, Errors err) throws RestException {
        validateRequest(err);
        return theCLNIAPSEC001Svc.sendApplyInput(req);
    }

    /**
     * LIP-C-CLNIAPSVC001 進件申請條件輸入儲存
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     */
    @PostMapping(value = "/applyInput/save", produces = MediaType.APPLICATION_JSON_VALUE)
    @Operation(summary = "LIP-C-CLNIAPSVC001 進件申請條件輸入儲存")
    public ResponseTemplate<EmptyDto> saveApplyInput(@Valid
    @RequestBody
    RequestTemplate<CLNIAPSVC001Tranrq> req, Errors err) throws RestException {
        validateRequest(err);
        return theCLNIAPSVC001Svc.saveApplyInput(req);
    }

    /**
     * LIP-C-CLNINITCC001 新增起案
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     */
    @PostMapping(value = "/init", produces = MediaType.APPLICATION_JSON_VALUE)
    @Operation(summary = "LIP-C-CLNINITCC001 新增起案")
    public ResponseTemplate<CLNINITCC001Tranrs> insertCase(@Valid
    @RequestBody
    RequestTemplate<CLNINITCC001Tranrq> req, Errors err) throws RestException {
        validateRequest(err);
        return theCLNINITCC001Svc.insertCase(req);
    }

    /**
     * LIP-C-CLNREJECC001 撤件查詢
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     */
    @PostMapping(value = "/reject/query", produces = MediaType.APPLICATION_JSON_VALUE)
    @Operation(summary = "LIP-C-CLNREJECC001 撤件查詢")
    public ResponseTemplate<CLNREJECC001Tranrs> rejectQuery(@Valid
    @RequestBody
    RequestTemplate<CLNREJECC001Tranrq> req, Errors err) throws RestException {
        validateRequest(err);
        return theCLNREJECC001Svc.rejectQuery(req);
    }

    /**
     * LIP-C-CLNREJECC002 撤件維護
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     */
    @PostMapping(value = "/reject/modify", produces = MediaType.APPLICATION_JSON_VALUE)
    @Operation(summary = "LIP-C-CLNREJECC002 撤件維護")
    public ResponseTemplate<CLNREJECC002Tranrs> rejectModify(@Valid
    @RequestBody
    RequestTemplate<CLNREJECC002Tranrq> req, Errors err) throws RestException {
        validateRequest(err);
        return theCLNREJECC002Svc.rejectModify(req);
    }

    /**
     * LIP-C-CLNCSMINC001 進件主頁初始查詢
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     */
    @PostMapping(value = "/main/query", produces = MediaType.APPLICATION_JSON_VALUE)
    @Operation(summary = "LIP-C-CLNCSMINC001 進件主頁初始查詢")
    public ResponseTemplate<EmptyDto> caseInitQuery(@Valid
    @RequestBody
    RequestTemplate<CLNCSMINC001Tranrq> req, Errors err) throws RestException {
        validateRequest(err);
        return theCLNCSMINC001Svc.caseInitQuery(req);
    }

    /**
     * LIP-C-CLNJCFINC001 財所清清單查詢
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     */
    @PostMapping(value = "/jcic/queryJcicFin", produces = MediaType.APPLICATION_JSON_VALUE)
    @Operation(summary = "LIP-C-CLNJCFINC001 財所清清單查詢")
    public ResponseTemplate<CLNJCFINC001Tranrs> queryJcicFin(@Valid
    @RequestBody
    RequestTemplate<CLNJCFINC001Tranrq> req, Errors err) throws RestException {
        validateRequest(err);
        return theCLNJCFINC001Svc.queryJcicFin(req);
    }

    /**
     * LIP-C-CLNJCFINC002 財所清維護
     *
     * @param req 請求資料
     * @param err 驗證錯誤
     * @param file 授權書檔案
     * @return 回應資料
     * @throws RestException REST 例外
     */
    @PostMapping(value = "/jcic/modifyJcicFin", consumes = { MediaType.APPLICATION_JSON_VALUE,
            MediaType.MULTIPART_FORM_DATA_VALUE }, produces = MediaType.APPLICATION_JSON_VALUE)
    @Operation(summary = "LIP-C-CLNJCFINC002 財所清維護")
    public ResponseTemplate<EmptyDto> modifyJcicFin(@Valid
    @RequestPart("RequestTemplate")
    RequestTemplate<CLNJCFINC002Tranrq> req, Errors err, @RequestPart(name = "File", required = false)
    MultipartFile file) throws RestException {
        validateRequest(err);
        return theCLNJCFINC002Svc.modifyJcicFin(req, file);
    }

    /**
     * LIP-C-CLNJCFINC003 財所清重查
     *
     * @param req 請求資料
     * @param err 驗證錯誤
     * @return 回應資料
     * @throws RestException REST 例外
     */
    @PostMapping(value = "/jcic/reSendJcicFin", produces = MediaType.APPLICATION_JSON_VALUE)
    @Operation(summary = "LIP-C-CLNJCFINC003 財所清重查")
    public ResponseTemplate<EmptyDto> reSendJcicFin(@Valid
    @RequestBody
    RequestTemplate<CLNJCFINC003Tranrq> req, Errors err) throws RestException {
        validateRequest(err);
        return theCLNJCFINC003Svc.reSendJcicFin(req);
    }

    /**
    * LIP-C-CLNJCFINC004 財所清附件查詢
    *
    * @param req 請求資料
    * @param err 驗證錯誤
    * @return HTML 附件
    * @throws RestException REST 例外
    */
    @PostMapping(value = "/jcic/getJcicFinHtml", produces = MediaType.APPLICATION_OCTET_STREAM_VALUE)
    @Operation(summary = "LIP-C-CLNJCFINC004 財所清附件查詢")
    public ResponseEntity<byte[]> getJcicFinHtml(@Valid
    @RequestBody
    RequestTemplate<CLNJCFINC004Tranrq> req, Errors err) throws RestException {
        validateRequest(err);
        return theCLNJCFINC004Svc.getJcicFinHtml(req);
    }

}
```

**ApprovalController.java /api/approval 核決相關 API Java · 403 行**

lip-svc-cln/src/main/java/cub/lip/svc/cln/controller/ApprovalController.java

```java
package cub.lip.svc.cln.controller;

import cub.lip.lib.common.controller.BaseController;
import cub.lip.lib.common.dto.base.EmptyDto;
import cub.lip.lib.common.dto.base.RequestTemplate;
import cub.lip.lib.common.dto.base.ResponseTemplate;
import cub.lip.lib.common.exception.DataNotFoundException;
import cub.lip.lib.common.exception.RestException;
import cub.lip.svc.cln.dto.cln.CLNARCTSC001Tranrq;
import cub.lip.svc.cln.dto.cln.CLNARLAYC001Tranrq;
import cub.lip.svc.cln.dto.cln.CLNARLAYC001Tranrs;
import cub.lip.svc.cln.dto.cln.CLNARLAYC002Tranrq;
import cub.lip.svc.cln.dto.cln.CLNARLAYC003Tranrq;
import cub.lip.svc.cln.dto.cln.CLNARLCTC001Tranrq;
import cub.lip.svc.cln.dto.cln.CLNARLCTC001Tranrs;
import cub.lip.svc.cln.dto.cln.CLNCHACCC001Tranrq;
import cub.lip.svc.cln.dto.cln.CLNCHACCC001Tranrs;
import cub.lip.svc.cln.dto.cln.CLNGUARAC001Tranrq;
import cub.lip.svc.cln.dto.cln.CLNGUARAC001Tranrs;
import cub.lip.svc.cln.dto.cln.CLNGUARAC002Tranrq;
import cub.lip.svc.cln.dto.cln.CLNGUARAC003Tranrq;
import cub.lip.svc.cln.dto.cln.CLNGUARAC003Tranrs;
import cub.lip.svc.cln.dto.cln.CLNREPOTC001Tranrq;
import cub.lip.svc.cln.dto.cln.CLNREPOTC002Tranrq;
import cub.lip.svc.cln.dto.cln.CLNREPOTC003Tranrq;
import cub.lip.svc.cln.dto.cln.CLNREPOTC004Tranrq;
import cub.lip.svc.cln.dto.cln.CLNREPOTC005Tranrq;
import cub.lip.svc.cln.dto.cln.CLNREPOTC006Tranrq;
import cub.lip.svc.cln.dto.cln.CLNREPOTC007Tranrq;
import cub.lip.svc.cln.svc.CLNARCTSC001Svc;
import cub.lip.svc.cln.svc.CLNARLAYC001Svc;
import cub.lip.svc.cln.svc.CLNARLAYC002Svc;
import cub.lip.svc.cln.svc.CLNARLAYC003Svc;
import cub.lip.svc.cln.svc.CLNARLCTC001Svc;
import cub.lip.svc.cln.svc.CLNCHACCC001Svc;
import cub.lip.svc.cln.svc.CLNGUARAC001Svc;
import cub.lip.svc.cln.svc.CLNGUARAC002Svc;
import cub.lip.svc.cln.svc.CLNGUARAC003Svc;
import cub.lip.svc.cln.svc.CLNREPOTC001Svc;
import cub.lip.svc.cln.svc.CLNREPOTC002Svc;
import cub.lip.svc.cln.svc.CLNREPOTC003Svc;
import cub.lip.svc.cln.svc.CLNREPOTC004Svc;
import cub.lip.svc.cln.svc.CLNREPOTC005Svc;
import cub.lip.svc.cln.svc.CLNREPOTC006Svc;
import cub.lip.svc.cln.svc.CLNREPOTC007Svc;
import io.swagger.v3.oas.annotations.Operation;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.Errors;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.validation.Valid;

/**
 * ApprovalController
 *
 * @author 00550349
 */
@RestController
@RequestMapping("/api/approval")
public class ApprovalController extends BaseController {

    /** CLNARCTSC001Svc 應徵提契據區塊儲存 */
    @Autowired
    private CLNARCTSC001Svc theCLNARCTSC001Svc;

    /** CLNARLAYC001Svc 核確條件初始查詢 */
    @Autowired
    private CLNARLAYC001Svc theCLNARLAYC001Svc;

    /** CLNARLAYC002Svc 核確條件儲存 */
    @Autowired
    private CLNARLAYC002Svc theCLNARLAYC002Svc;

    /** CLNARLAYC003Svc 核確條件送出 */
    @Autowired
    private CLNARLAYC003Svc theCLNARLAYC003Svc;

    /** CLNARLCTC001Svc 應徵提契據初始查詢 */
    @Autowired
    private CLNARLCTC001Svc theCLNARLCTC001Svc;

    /** CLNCHACCC001Svc 核定條件承作方式連動科目 */
    @Autowired
    private CLNCHACCC001Svc theCLNCHACCC001Svc;

    /** CLNGUARAC001Svc 對保查詢 */
    @Autowired
    private CLNGUARAC001Svc theCLNGUARAC001Svc;

    /** CLNGUARAC002Svc 對保維護 */
    @Autowired
    private CLNGUARAC002Svc theCLNGUARAC002Svc;

    /** CLNGUARAC003Svc 家事事件引入 */
    @Autowired
    private CLNGUARAC003Svc theCLNGUARAC003Svc;

    /** CLNREPOTC001Svc 共033查詢 */
    @Autowired
    private CLNREPOTC001Svc theCLNREPOTC001Svc;

    /** CLNREPOTC002Svc 企金75查詢 */
    @Autowired
    private CLNREPOTC002Svc theCLNREPOTC002Svc;

    /** CLNREPOTC003Svc 質001查詢 */
    @Autowired
    private CLNREPOTC003Svc theCLNREPOTC003Svc;

    /** CLNREPOTC004Svc 質002查詢 */
    @Autowired
    private CLNREPOTC004Svc theCLNREPOTC004Svc;

    /** CLNREPOTC004Svc 質003查詢 */
    @Autowired
    private CLNREPOTC005Svc theCLNREPOTC005Svc;

    /** CLNREPOTC006Svc 企金69查詢 */
    @Autowired
    private CLNREPOTC006Svc theCLNREPOTC006Svc;

    /** LIP-C-CLNREPOTC007 承作條件通知書查詢 */
    @Autowired
    private CLNREPOTC007Svc theCLNREPOTC007Svc;

    /**
     * LIP-C-CLNARCTSC001 應徵提契據區塊儲存
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     */
    @PostMapping("/contract/save")
    @Operation(summary = "LIP-C-CLNARCTSC001 應徵提契據區塊儲存")
    public ResponseTemplate<EmptyDto> saveApprovalContract(@Valid
    @RequestBody
    RequestTemplate<CLNARCTSC001Tranrq> req, Errors err) throws RestException {
        validateRequest(err);
        return theCLNARCTSC001Svc.saveApprovalContract(req);
    }

    /**
     * LIP-C-CLNARLAYC001 核確條件初始查詢
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     * @throws ClassNotFoundException
     * @throws DataNotFoundException
     */
    @PostMapping("/apply/query")
    @Operation(summary = "LIP-C-CLNARLAYC001 核確條件初始查詢")
    public ResponseTemplate<CLNARLAYC001Tranrs> applyQuery(@Valid
    @RequestBody
    RequestTemplate<CLNARLAYC001Tranrq> req, Errors err) throws RestException, ClassNotFoundException, DataNotFoundException {
        validateRequest(err);
        return theCLNARLAYC001Svc.applyQuery(req);
    }

    /**
     * LIP-C-CLNARLAYC002 核確條件儲存
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     */
    @PostMapping("/apply/save")
    @Operation(summary = "LIP-C-CLNARLAYC002 核確條件儲存")
    public ResponseTemplate<EmptyDto> saveApply(@Valid
    @RequestBody
    RequestTemplate<CLNARLAYC002Tranrq> req, Errors err) throws RestException {
        validateRequest(err);
        return theCLNARLAYC002Svc.saveApply(req);
    }

    /**
     * LIP-C-CLNARLAYC003 核確條件送出
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     */
    @PostMapping("/apply/send")
    @Operation(summary = "LIP-C-CLNARLAYC003 核確條件送出")
    public ResponseTemplate<EmptyDto> applySend(@Valid
    @RequestBody
    RequestTemplate<CLNARLAYC003Tranrq> req, Errors err) throws RestException {
        validateRequest(err);
        return theCLNARLAYC003Svc.applySend(req);
    }

    /**
     * LIP-C-CLNARLCTC001 應徵提契據初始查詢
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     */
    @PostMapping("/contract/query")
    @Operation(summary = "LIP-C-CLNARLCTC001 應徵提契據初始查詢")
    public ResponseTemplate<CLNARLCTC001Tranrs> queryApprovalContractInit(@Valid
    @RequestBody
    RequestTemplate<CLNARLCTC001Tranrq> req, Errors err) throws RestException {
        validateRequest(err);
        return theCLNARLCTC001Svc.queryApprovalContractInit(req);
    }

    /**
     * LIP-C-CLNCHACCC001 核定條件承作方式連動科目
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     */
    @PostMapping("/acntCode/change")
    @Operation(summary = "LIP-C-CLNCHACCC001 核定條件承作方式連動科目")
    public ResponseTemplate<CLNCHACCC001Tranrs> changeAcntCode(@Valid
    @RequestBody
    RequestTemplate<CLNCHACCC001Tranrq> req, Errors err) throws RestException {
        validateRequest(err);
        return theCLNCHACCC001Svc.changeAcntCode(req);
    }

    /**
     * LIP-C-CLNGUARAC001 對保查詢
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     */
    @PostMapping("/guarantee/query")
    @Operation(summary = "LIP-C-CLNGUARAC001 對保查詢")
    public ResponseTemplate<CLNGUARAC001Tranrs> queryGuarantee(@Valid
    @RequestBody
    RequestTemplate<CLNGUARAC001Tranrq> req, Errors err) throws RestException {
        validateRequest(err);
        return theCLNGUARAC001Svc.queryGuarantee(req);
    }

    /**
     * LIP-C-CLNGUARAC002 對保維護
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     */
    @PostMapping("/guarantee/save")
    @Operation(summary = "LIP-C-CLNGUARAC002 對保維護")
    public ResponseTemplate<EmptyDto> approvalGuaranteeSave(@Valid
    @RequestBody
    RequestTemplate<CLNGUARAC002Tranrq> req, Errors err) throws RestException {
        validateRequest(err);
        return theCLNGUARAC002Svc.approvalGuaranteeSave(req);
    }

    /**
     * LIP-C-CLNGUARAC003 家事事件引入
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     */
    @PostMapping("/guarantee/judicialfamily")
    @Operation(summary = "LIP-C-CLNGUARAC003 家事事件引入")
    public ResponseTemplate<CLNGUARAC003Tranrs> approvalGuaranteeJudicialfamily(@Valid
    @RequestBody
    RequestTemplate<CLNGUARAC003Tranrq> req, Errors err) throws RestException {
        validateRequest(err);
        return theCLNGUARAC003Svc.approvalGuaranteeJudicialfamily(req);
    }

    /**
     * LIP-C-CLNREPOTC001 共033查詢
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     */
    @PostMapping("/rptComm033/query")
    @Operation(summary = "LIP-C-CLNREPOTC001 共033查詢")
    public ResponseEntity<byte[]> getFile(@Valid
    @RequestBody
    RequestTemplate<CLNREPOTC001Tranrq> req, Errors err) throws RestException {
        validateRequest(err);
        return theCLNREPOTC001Svc.queryRptComm033(req);
    }

    /**
     * LIP-C-CLNREPOTC002 企金75查詢
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     */
    @PostMapping("/rptCorp75/query")
    @Operation(summary = "LIP-C-CLNREPOTC002 企金75查詢")
    public ResponseEntity<byte[]> queryRptCorp75(@Valid
    @RequestBody
    RequestTemplate<CLNREPOTC002Tranrq> req, Errors err) throws RestException {
        validateRequest(err);
        return theCLNREPOTC002Svc.queryRptCorp75(req);
    }

    /**
     * LIP-C-CLNREPOTC003 質001查詢
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     */
    @PostMapping("/rptColl001/query")
    @Operation(summary = "LIP-C-CLNREPOTC003 質001查詢")
    public ResponseEntity<byte[]> queryRptColl001(@Valid
    @RequestBody
    RequestTemplate<CLNREPOTC003Tranrq> req, Errors err) throws RestException {
        validateRequest(err);
        return theCLNREPOTC003Svc.queryRptColl001(req);
    }

    /**
     * LIP-C-CLNREPOTC004 質002查詢
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     */
    @PostMapping("/rptColl002/query")
    @Operation(summary = "LIP-C-CLNREPOTC004 質002查詢")
    public ResponseEntity<byte[]> queryRptColl002(@Valid
    @RequestBody
    RequestTemplate<CLNREPOTC004Tranrq> req, Errors err) throws RestException {
        validateRequest(err);
        return theCLNREPOTC004Svc.queryRptColl002(req);
    }

    /**
     * LIP-C-CLNREPOTC005 質003查詢
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     */
    @PostMapping("/rptColl003/query")
    @Operation(summary = "LIP-C-CLNREPOTC005 質003查詢")
    public ResponseEntity<byte[]> queryRptColl003(@Valid
    @RequestBody
    RequestTemplate<CLNREPOTC005Tranrq> req, Errors err) throws RestException {
        validateRequest(err);
        return theCLNREPOTC005Svc.queryRptColl003(req);
    }

    /**
     * LIP-C-CLNREPOTC006 企金69查詢
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     */
    @PostMapping("/rptCorp69/query")
    @Operation(summary = "LIP-C-CLNREPOTC006 企金69查詢")
    public ResponseEntity<byte[]> queryRptCorp69(@Valid
    @RequestBody
    RequestTemplate<CLNREPOTC006Tranrq> req, Errors err) throws RestException {
        validateRequest(err);
        return theCLNREPOTC006Svc.queryRptCorp69(req);
    }

    /**
     * LIP-C-CLNREPOTC007 承作條件通知書查詢
     *
     * @param req 含受理編號的請求電文
     * @param err 請求欄位驗證結果
     * @return 承作條件通知書 PDF 附件
     * @throws RestException 下游查詢失敗
     */
    @PostMapping("/rptLoanNotify/query")
    @Operation(summary = "LIP-C-CLNREPOTC007 承作條件通知書查詢")
    public ResponseEntity<byte[]> queryRptLoanNotify(@Valid
    @RequestBody
    RequestTemplate<CLNREPOTC007Tranrq> req, Errors err) throws RestException {
        validateRequest(err);
        return theCLNREPOTC007Svc.queryRptLoanNotify(req);
    }
}
```

**README.md 目前仍是通用範本 Markdown · 20 行**

lip-svc-cln/README.md

```markdown
# Introduction 
TODO: Give a short introduction of your project. Let this section explain the objectives or the motivation behind this project. 

# Getting Started
TODO: Guide users through getting your code up and running on their own system. In this section you can talk about:
1.	Installation process
2.	Software dependencies
3.	Latest releases
4.	API references

# Build and Test
TODO: Describe and show how to build your code and run the tests. 

# Contribute
TODO: Explain how other users and developers can contribute to make your code better. 

If you want to learn more about creating good readme files then refer the following [guidelines](https://docs.microsoft.com/en-us/azure/devops/repos/git/create-a-readme?view=azure-devops). You can also seek inspiration from the below readme files:
- [ASP.NET Core](https://github.com/aspnet/Home)
- [Visual Studio Code](https://github.com/Microsoft/vscode)
- [Chakra Core](https://github.com/Microsoft/ChakraCore)
```

## 交付檢查

-   [ ] LIP-C 電文呼叫的 LIP-B 電文正確，兩邊欄位與錯誤碼一致。
-   [ ] 核對 /api 路徑、電文 ID、欄位與錯誤碼。
-   [ ] 沿用該服務近似 Controller/Service 模式，不跨版本複製。
-   [ ] 確認共用 library 版本和目標環境設定。
