# lip-svc-cln-common

## lip-svc-cln-common｜共用服務 API

## 專案架構

這個模組不是只有共用 Java 工具的 library：目前可見 Spring Boot 啟動類別與 REST Controllers，提供 CLN 流程可重用的查詢、計算、資料整理和外部服務整合入口。以下定位依 Controller 與 POM 觀察；README 仍是通用範本。

| 觀察面向 | 目前程式可見內容 | 閱讀提示 |
| --- | --- | --- |
| 服務型態 | Java 8、Spring Boot 專案；有獨立 Application 與 REST Controller。 | 需與依賴的 `lip-lib-cln-common` 共用程式庫區分。 |
| 共用功能 | 地址正規化、客戶/科目資料查詢、承作權限、核定層級與案件相關共用資訊。 | 這些是由端點名稱和 Controller 註解辨識的功能範圍；欄位與業務規則仍看各 API 規格。 |
| 其他能力 | 有合約影本計算/列印入口，以及訊息發送等 API。 | 外部服務成功碼、錯誤轉換與重送行為應追到對應 Service 實作。 |
| 代表路徑 | `POST /common/address/query`、`POST /common/canDoCase/query`、`POST /calculate/contract/printCopy` | 共用功能的 Controller 分在 CommonController、CustomerController、CalculateController。 |

## API 慣例

Controller 依 `/common`、`/customer`、`/calculate` 分組，接收 RequestTemplate 並委派對應 Service。這是目前可觀察到的入口模式；欄位、錯誤碼和回應語意仍以各 API 契約為準。

## 實作流程

### 建議閱讀順序

**確認共用目的** 先判斷能力是否供多個 CLN 流程重用

**讀 Controller** 確認 URI、電文 ID 與輸入輸出型別

**追 Service** 分辨內部查詢、計算或外部發查

**核對回傳碼** 檢查錯誤轉換與共用回應格式

**對照呼叫端** 確認消費端如何處理結果與錯誤

## 完整案例

以地址正規化查詢為例，從 `POST /common/address/query` 追蹤 Controller、電文與 Service；承作權限查詢和合約影本列印則可作為其他共用能力的對照。

**pom.xml 專案依賴與 Java 版本 XML · 92 行**

lip-svc-cln-common/pom.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>cub.cloud</groupId>
        <artifactId>cub-cloud</artifactId>
        <version>1.1.1</version>
        <relativePath/><!-- lookup parent from repository -->
    </parent>

    <groupId>cub.lip</groupId>
    <artifactId>lip-svc-cln-common</artifactId>
    <properties>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <java.version>1.8</java.version>
        <tomcat.version>9.0.102</tomcat.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>cub.lip</groupId>
            <artifactId>lip-lib-cln-common</artifactId>
            <version>1.0.0-SNAPSHOT</version>
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
        <dependency>
            <groupId>ebaf.commons</groupId>
            <artifactId>BankCmn4eBAF</artifactId>
            <version>0.0.3</version>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-devtools</artifactId>
            <optional>true</optional>
        </dependency>
    </dependencies>
    <build>
        <finalName>lip-svc-cln-common</finalName>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
```

**LipSvcClnCommonApplication.java Spring Boot 啟動類別 Java · 16 行**

lip-svc-cln-common/src/main/java/cub/lip/svc/cln/common/LipSvcClnCommonApplication.java

```java
package cub.lip.svc.cln.common;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cache.annotation.EnableCaching;

@SpringBootApplication
@EnableCaching
//@EnableJpaRepositories(repositoryBaseClass = CUBRepositoryImpl.class, bootstrapMode = BootstrapMode.DEFERRED)
public class LipSvcClnCommonApplication {

    public static void main(String[] args) {
        SpringApplication.run(LipSvcClnCommonApplication.class, args);
    }

}
```

**CommonController.java 地址、承作權限、層級等共用端點 Java · 606 行**

lip-svc-cln-common/src/main/java/cub/lip/svc/cln/common/controller/CommonController.java

```java
package cub.lip.svc.cln.common.controller;

import java.io.IOException;

import javax.validation.Valid;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.validation.Errors;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import cub.lip.lib.common.controller.BaseController;
import cub.lip.lib.common.dto.base.EmptyDto;
import cub.lip.lib.common.dto.base.RequestTemplate;
import cub.lip.lib.common.dto.base.ResponseTemplate;
import cub.lip.lib.common.exception.DataNotFoundException;
import cub.lip.lib.common.exception.GetSeqFailException;
import cub.lip.lib.common.exception.ModuleException;
import cub.lip.lib.common.exception.RestException;
import cub.lip.svc.cln.common.dto.ccm.*;
import cub.lip.svc.cln.common.svc.*;
import io.swagger.v3.oas.annotations.Operation;

@RestController
@RequestMapping("/common")
public class CommonController extends BaseController {

    /** CCMADDRFQ001Svc 地址正規化和申請詐欺 */
    @Autowired
    private CCMADDRFQ001Svc theCCMADDRFQ001Svc;

    /** CCMCAADDQ001Svc 地址正規化整理 */
    @Autowired
    private CCMCAADDQ001Svc theCCMCAADDQ001Svc;

    /** CCMCACNTQ001Svc 取得共用科目代碼資訊 */
    @Autowired
    private CCMCACNTQ001Svc theCCMCACNTQ001Svc;

    /** CCMCALVLC001Svc 查詢計算核定層級 */
    @Autowired
    private CCMCALVLC001Svc theCCMCALVLC001Svc;

    /** CCMCANDOQ001Svc 查詢是否有權限承作本案 */
    @Autowired
    private CCMCANDOQ001Svc theCCMCANDOQ001Svc;

    /** CCMCHKIDQ001Svc IDType查詢 */
    @Autowired
    private CCMCHKIDQ001Svc theCCMCHKIDQ001Svc;

    /** CCMCIASEC001Svc CLN發查一鍵查詢共用API */
    @Autowired
    private CCMCIASEC001Svc theCCMCIASEC001Svc;

    /** CCMCLAMTQ001Svc 計算核定層級-金額 */
    @Autowired
    private CCMCLAMTQ001Svc theCCMCLAMTQ001Svc;

    /** CCMCHLVLQ001Svc 通路審核計算層級查詢 */
    @Autowired
    private CCMCHLVLQ001Svc theCCMCHLVLQ001Svc;
    
    /** CCMCLRATQ001Svc 計算核定層級-利率 */
    @Autowired
    private CCMCLRATQ001Svc theCCMCLRATQ001Svc;

    /** CCMCLOTHQ001Svc 計算核定層級-其他 */
    @Autowired
    private CCMCLOTHQ001Svc theCCMCLOTHQ001Svc;

    /** CCMCRTLTQ001Svc 檢核償還方式並計算期限 */
    @Autowired
    private CCMCRTLTQ001Svc theCCMCRTLTQ001Svc;

    /** CCMCUHUBQ001Svc 客登上傳 */
    @Autowired
    private CCMCUHUBQ001Svc theCCMCUHUBQ001Svc;

    /** CCMGCHIDQ001Svc 查詢ID換號名單異動檔 */
    @Autowired
    private CCMGCHIDQ001Svc theCCMGCHIDQ001Svc;

    /** CCMGCLVLQ001Svc 依借款人/共借人總資產取得 VIP 等級 */
    @Autowired
    private CCMGCLVLQ001Svc theCCMGCLVLQ001Svc;

    /** CCMGTNBRQ001Svc 案件編號產號 */
    @Autowired
    private CCMGTNBRQ001Svc theCCMGTNBRQ001Svc;

    /** CCMGTYGRQ001Svc 判斷授信燈號 */
    @Autowired
    private CCMGTYGRQ001Svc theCCMGTYGRQ001Svc;

    /** CCMIMGBCC001Svc 更新新影像平台帳務對保行 */
    @Autowired
    private CCMIMGBCC001Svc theCCMIMGBCC001Svc;

    /** CCMINBRHQ001Svc 取得進件行 */
    @Autowired
    private CCMINBRHQ001Svc theCCMINBRHQ001Svc;

    /** CCMLMDTLQ001Svc 名單檔案維護記錄檔 */
    @Autowired
    private CCMLMDTLQ001Svc theCCMLMDTLQ001Svc;

    /** CCMNCBRHQ001Svc 是否要做權限控管 */
    @Autowired
    private CCMNCBRHQ001Svc theCCMNCBRHQ001Svc;

    /** CCMQAUTHQ001Svc 過濾查詢權限 */
    @Autowired
    private CCMQAUTHQ001Svc theCCMQAUTHQ001Svc;

    /** CCMRATDTQ001Svc 查詢整合評分各功能確認訊息 */
    @Autowired
    private CCMRATDTQ001Svc theCCMRATDTQ001Svc;

    /** CCMRATESQ001 查詢專案適用項目 */
    @Autowired
    private CCMRATESQ001Svc theCCMRATESQ001Svc;

    /** CCMGCOSTQ001Svc 利率門檻查詢 */
    @Autowired
    private CCMGCOSTQ001Svc theCCMGCOSTQ001Svc;

    /** CCMRTMSGT001Svc 即時訊息通知 */
    @Autowired
    private CCMRTMSGT001Svc theCCMRTMSGT001Svc;

    /**
     * LIP-C-CCMADDRFQ001 地址正規化和申請詐欺
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     * @throws DataNotFoundException
     * @throws IOException
     * @throws ClassNotFoundException
     */
    @PostMapping("/addressRegFraud/send")
    @Operation(summary = "LIP-C-CCMADDRFQ001 地址正規化和申請詐欺")
    public ResponseTemplate<EmptyDto> addressRegFraud(@Valid
    @RequestBody
    RequestTemplate<CCMADDRFQ001Tranrq> req, Errors err) throws RestException, DataNotFoundException, IOException, ClassNotFoundException {
        validateRequest(err);
        return theCCMADDRFQ001Svc.addressRegFraud(req);
    }

    /**
     * LIP-C-CCMCAADDQ001 地址正規化整理
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     * @throws DataNotFoundException
     */
    @PostMapping("/address/query")
    @Operation(summary = "LIP-C-CCMCAADDQ001 地址正規化整理")
    public ResponseTemplate<CCMCAADDQ001Tranrs> queryAddress(@Valid
    @RequestBody
    RequestTemplate<CCMCAADDQ001Tranrq> req, Errors err) throws RestException, DataNotFoundException {
        validateRequest(err);
        return theCCMCAADDQ001Svc.queryAddress(req);
    }

    /**
     * LIP-B-CCMCACNTQ001 取得共用科目代碼資訊
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     */
    @PostMapping("/acntInfo/query")
    @Operation(summary = "LIP-B-CCMCACNTQ001 取得共用科目代碼資訊")
    public ResponseTemplate<CCMCACNTQ001Tranrs> queryAcntInfo(@Valid
    @RequestBody
    RequestTemplate<CCMCACNTQ001Tranrq> req, Errors err) throws RestException {
        validateRequest(err);
        return theCCMCACNTQ001Svc.queryAcntInfo(req);
    }

    /**
     * LIP-C-CCMCALVLC001 查詢計算核定層級
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     * @throws DataNotFoundException
     * @throws IOException
     * @throws ModuleException
     */
    @PostMapping("/countAgreeLevel/agreeLevelQuery")
    @Operation(summary = "LIP-C-CCMCALVLC001 查詢計算核定層級")
    public ResponseTemplate<CCMCALVLC001Tranrs> queryAgreeLevel(@Valid
    @RequestBody
    RequestTemplate<CCMCALVLC001Tranrq> req, Errors err) throws RestException, IOException, DataNotFoundException, ModuleException {
        validateRequest(err);
        return theCCMCALVLC001Svc.queryAgreeLevel(req);
    }

    /**
     * LIP-B-CCMCANDOQ001 查詢是否有權限承作本案
     *
     * @param req
     * @param err
     * @return
     * @throws IOException
     */
    @PostMapping("/canDoCase/query")
    @Operation(summary = "LIP-B-CCMCANDOQ001 查詢是否有權限承作本案")
    public ResponseTemplate<CCMCANDOQ001Tranrs> queryCanDoCase(@Valid
    @RequestBody
    RequestTemplate<CCMCANDOQ001Tranrq> req, Errors err) throws IOException {
        validateRequest(err);
        return theCCMCANDOQ001Svc.queryCanDoCase(req);
    }

    /**
     * LIP-C-CCMCHKIDQ001 IDType查詢
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     */
    @PostMapping("/idType/query")
    @Operation(summary = "LIP-C-CCMCHKIDQ001 IDType查詢")
    public ResponseTemplate<CCMCHKIDQ001Tranrs> queryIdType(@Valid
    @RequestBody
    RequestTemplate<CCMCHKIDQ001Tranrq> req, Errors err) throws RestException {
        validateRequest(err);
        return theCCMCHKIDQ001Svc.queryIdType(req);
    }

    /**
     * LIP-C-CCMCIASEC001 CLN發查一鍵查詢共用API
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     * @throws DataNotFoundException
     * @throws IOException
     */
    @PostMapping("/sendCia/query")
    @Operation(summary = "LIP-C-CCMCIASEC001 CLN發查一鍵查詢共用API")
    public ResponseTemplate<EmptyDto> querySendCia(@Valid
    @RequestBody
    RequestTemplate<CCMCIASEC001Tranrq> req, Errors err) throws RestException, DataNotFoundException, IOException {
        validateRequest(err);
        return theCCMCIASEC001Svc.querySendCia(req);
    }

    /**
     * LIP-B-CCMCHLVLQ001 通路審核計算層級查詢。
     *
     * @param req 通路審核計算層級請求
     * @param err 請求驗證結果
     * @return 通路審核計算層級結果
     * @throws IOException 資料讀取失敗
     * @throws DataNotFoundException 查無計算所需資料
     * @throws ModuleException 計算層級處理失敗
     */
    @PostMapping("/countAgreeLevel/channelLevelQuery")
    @Operation(summary = "LIP-B-CCMCHLVLQ001 通路審核計算層級查詢")
    public ResponseTemplate<CCMCHLVLQ001Tranrs> countChannelAgreeLevel(@Valid
    @RequestBody
    RequestTemplate<CCMCHLVLQ001Tranrq> req, Errors err)
            throws IOException, DataNotFoundException, ModuleException {
        validateRequest(err);
        return theCCMCHLVLQ001Svc.countChannelAgreeLevel(req);
    }
    
    /**
     * LIP-B-CCMCLAMTQ001 計算核定層級-金額
     *
     * @param req
     * @param err
     * @return
     * @throws IOException
     * @throws RestException
     * @throws DataNotFoundException
     * @throws ModuleException
     */
    @PostMapping("/countAgreeLevel/countLevelByAmount")
    @Operation(summary = "LIP-B-CCMCLAMTQ001 計算核定層級-金額")
    public ResponseTemplate<CCMCLAMTQ001Tranrs> countLevelByAmount(@Valid
    @RequestBody
    RequestTemplate<CCMCLAMTQ001Tranrq> req, Errors err) throws IOException, RestException, DataNotFoundException, ModuleException {
        validateRequest(err);
        return theCCMCLAMTQ001Svc.countLevelByAmount(req);
    }

    /**
     * LIP-B-CCMCLRATQ001 計算核定層級-利率
     *
     * @param req
     * @param err
     * @return
     * @throws IOException
     */
    @PostMapping("/countAgreeLevel/countLevelByRate")
    @Operation(summary = "LIP-B-CCMCLRATQ001 計算核定層級-利率")
    public ResponseTemplate<CCMCLRATQ001Tranrs> countLevelByRate(@Valid
    @RequestBody
    RequestTemplate<CCMCLRATQ001Tranrq> req, Errors err) throws IOException {
        validateRequest(err);
        return theCCMCLRATQ001Svc.countLevelByRate(req);
    }

    /**
     * LIP-C-CCMCLOTHQ001 計算核定層級-其他
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     * @throws DataNotFoundException
     * @throws IOException
     */
    @PostMapping("/countAgreeLevel/countLevelByOther")
    @Operation(summary = "LIP-C-CCMCLOTHQ001 計算核定層級-其他")
    public ResponseTemplate<CCMCLOTHQ001Tranrs> countLevelByOther(@Valid
    @RequestBody
    RequestTemplate<CCMCLOTHQ001Tranrq> req, Errors err) throws RestException, IOException, DataNotFoundException {
        validateRequest(err);
        return theCCMCLOTHQ001Svc.countLevelByOther(req);
    }

    /**
     * LIP-B-CCMCRTLTQ001 檢核償還方式並計算期限
     * 
     * @param request
     * @param err
     * @return
     * @throws ModuleException
     */
    @PostMapping("/limitTerm/check")
    @Operation(summary = "LIP-B-CCMCRTLTQ001 檢核償還方式並計算期限")
    public ResponseTemplate<CCMCRTLTQ001Tranrs> checkLimitTerm(@Valid
    @RequestBody
    RequestTemplate<CCMCRTLTQ001Tranrq> request, Errors err) throws ModuleException {
        validateRequest(err);
        return theCCMCRTLTQ001Svc.checkLimitTerm(request);
    }

    /**
     * LIP-C-CCMCUHUBQ001 客登上傳
     *
     * @param req
     * @param err
     * @return ResponseTemplate<EmptyDto>
     * @throws RestException
     * @throws IOException
     * @throws DataNotFoundException
     * @throws ClassNotFoundException
     */
    @PostMapping("/cusHubCIF/upload")
    @Operation(summary = "LIP-C-CCMCUHUBQ001 客登上傳")
    public ResponseTemplate<EmptyDto> uploadCusHubCIF(@Valid
    @RequestBody
    RequestTemplate<CCMCUHUBQ001Tranrq> req, Errors err) throws RestException, IOException, DataNotFoundException, ClassNotFoundException {
        validateRequest(err);
        return theCCMCUHUBQ001Svc.uploadCusHubCIF(req);
    }

    /**
     * LIP-B-CCMGCHIDQ001 查詢ID換號名單異動檔
     * 
     * @param req
     * @param err
     * @return
     */
    @PostMapping("/cusIdChange/query")
    @Operation(summary = "LIP-B-CCMGCHIDQ001 查詢ID換號名單異動檔")
    public ResponseTemplate<CCMGCHIDQ001Tranrs> commonCusIdChangeQuery(@Valid
    @RequestBody
    RequestTemplate<CCMGCHIDQ001Tranrq> req, Errors err) {
        validateRequest(err);
        return theCCMGCHIDQ001Svc.cusIdChangeQuery(req);
    }

    /**
     * LIP-B-CCMGCLVLQ001 依借款人/共借人總資產取得 VIP 等級
     *
     * @param req
     * @param err
     * @return
     * @throws IOException
     */
    @PostMapping("/getCustLevel")
    @Operation(summary = "LIP-B-CCMGCLVLQ001 依借款人/共借人總資產取得 VIP 等級")
    public ResponseTemplate<CCMGCLVLQ001Tranrs> getCustLevel(@Valid
    @RequestBody
    RequestTemplate<CCMGCLVLQ001Tranrq> req, Errors err) throws IOException {
        validateRequest(err);
        return theCCMGCLVLQ001Svc.getCustLevel(req);
    }

    /**
     * LIP-B-CCMGTNBRQ001 共用編號產號
     *
     * @param req
     * @param err
     * @return
     * @throws GetSeqFailException
     * @throws RestException
     */
    @PostMapping("/applyNbr/query")
    @Operation(summary = "LIP-B-CCMGTNBRQ001 共用編號產號")
    public ResponseTemplate<CCMGTNBRQ001Tranrs> updateCaseNumber(@Valid
    @RequestBody
    RequestTemplate<CCMGTNBRQ001Tranrq> req, Errors err) throws GetSeqFailException, RestException {
        validateRequest(err);
        return theCCMGTNBRQ001Svc.updateCaseNumber(req);
    }

    /**
     * LIP-C-CCMGTYGRQ001 判斷授信燈號
     *
     * @param req
     * @param err
     * @return
     * @throws IOException
     * @throws DataNotFoundException
     * @throws RestException
     */
    @PostMapping("/getYGR")
    @Operation(summary = "LIP-C-CCMGTYGRQ001 判斷授信燈號")
    public ResponseTemplate<CCMGTYGRQ001Tranrs> getYGR(@Valid
    @RequestBody
    RequestTemplate<CCMGTYGRQ001Tranrq> req, Errors err) throws IOException, DataNotFoundException, RestException {
        validateRequest(err);
        return theCCMGTYGRQ001Svc.getYGR(req);
    }

    /**
     * LIP-C-CCMIMGBCC001 更新新影像平台帳務對保行
     * 
     * @param req
     * @param err
     * @return
     * @throws ModuleException
     * @throws DataNotFoundException
     */
    @PostMapping("/imgBranch/checkAndUpdate")
    @Operation(summary = "LIP-C-CCMIMGBCC001 更新新影像平台帳務對保行")
    public ResponseTemplate<EmptyDto> checkAndUpdateImgBranch(@Valid
    @RequestBody
    RequestTemplate<CCMIMGBCC001Tranrq> req, Errors err) throws ModuleException, DataNotFoundException {
        validateRequest(err);
        return theCCMIMGBCC001Svc.checkAndUpdateImgBranch(req);
    }

    /**
     * LIP-B-CCMINBRHQ001 取得進件行
     *
     * @param req
     * @param err
     * @return
     * @throws DataNotFoundException
     */
    @PostMapping("/inputBranch/query")
    @Operation(summary = "LIP-B-CCMINBRHQ001 取得進件行")
    public ResponseTemplate<CCMINBRHQ001Tranrs> queryInputBranch(@Valid
    @RequestBody
    RequestTemplate<CCMINBRHQ001Tranrq> req, Errors err) throws DataNotFoundException, IOException {
        validateRequest(err);
        return theCCMINBRHQ001Svc.queryInputBranch(req);
    }

    /**
     * LIP-B-CCMLMDTLQ001 名單檔案維護記錄檔
     *
     * @param req
     * @param err
     * @return
     * @throws IOException
     */
    @PostMapping("/listMantainDetail/query")
    @Operation(summary = "LIP-B-CCMLMDTLQ001 名單檔案維護記錄檔")
    public ResponseTemplate<CCMLMDTLQ001Tranrs> queryListMantainDetail(@Valid
    @RequestBody
    RequestTemplate<CCMLMDTLQ001Tranrq> req, Errors err) throws IOException {
        validateRequest(err);
        return theCCMLMDTLQ001Svc.queryListMantainDetail(req);
    }

    /**
     * LIP-B-CCMNCBRHQ001 是否要做權限控管
     *
     * @param req
     * @param err
     * @return
     */
    @PostMapping("/checkBranch/query")
    @Operation(summary = "LIP-B-CCMNCBRHQ001 是否要做權限控管")
    public ResponseTemplate<CCMNCBRHQ001Tranrs> queryCheckBranch(@Valid
    @RequestBody
    RequestTemplate<CCMNCBRHQ001Tranrq> req, Errors err) {
        validateRequest(err);
        return theCCMNCBRHQ001Svc.queryCheckBranch(req);
    }

    /**
     * LIP-B-CCMQAUTHQ001 過濾查詢權限
     *
     * @param req
     * @param err
     * @return
     * @throws DataNotFoundException
     * @throws RestException
     * @throws ModuleException
     * @throws ClassNotFoundException
     * @throws IOException
     */
    @PostMapping("/auth/query")
    @Operation(summary = "LIP-B-CCMQAUTHQ001 過濾查詢權限")
    public ResponseTemplate<EmptyDto> queryAuth(@Valid
    @RequestBody
    RequestTemplate<CCMQAUTHQ001Tranrq> req, Errors err)
            throws DataNotFoundException, RestException, ModuleException, ClassNotFoundException, IOException {
        validateRequest(err);
        return theCCMQAUTHQ001Svc.queryAuth(req);
    }

    /**
     * LIP-B-CCMRATDTQ001 查詢整合評分各功能確認訊息
     *
     * @param req
     * @param err
     * @return
     * @throws IOException
     */
    @PostMapping("/scoreConfirmMsg/query")
    @Operation(summary = "LIP-B-CCMRATDTQ001 查詢整合評分各功能確認訊息")
    public ResponseTemplate<CCMRATDTQ001Tranrs> queryScoreConfirmMsg(@Valid
    @RequestBody
    RequestTemplate<CCMRATDTQ001Tranrq> req, Errors err) throws IOException {
        validateRequest(err);
        return theCCMRATDTQ001Svc.queryScoreConfirmMsg(req);
    }

    /**
     * LIP-B-CCMRATESQ001 查詢專案適用項目
     *
     * @param req
     * @param err
     * @return
     * @throws Exception
     */
    @PostMapping("/projectItem/query")
    @Operation(summary = "LIP-B-CCMRATESQ001 查詢專案適用項目")
    public ResponseTemplate<CCMRATESQ001Tranrs> queryApplyItem(@Valid
    @RequestBody
    RequestTemplate<CCMRATESQ001Tranrq> req, Errors err) throws Exception {
        validateRequest(err);
        return theCCMRATESQ001Svc.queryApplyItem(req);
    }

    /**
     * LIP-C-CCMGCOSTQ001 利率門檻查詢
     * 
     * @param req
     * @param err
     * @return
     * @throws ModuleException
     * @throws IOException
     * @throws RestException
     * @throws DataNotFoundException
     */
    @PostMapping("/riskcost/query")
    @Operation(summary = "LIP-C-CCMGCOSTQ001 利率門檻查詢")
    public ResponseTemplate<CCMGCOSTQ001Tranrs> riskcostQuery(@Valid
    @RequestBody
    RequestTemplate<CCMGCOSTQ001Tranrq> req, Errors err) throws ModuleException, RestException, IOException {
        validateRequest(err);
        return theCCMGCOSTQ001Svc.riskcostQuery(req);
    }

    /**
     * LIP-B-CCMRTMSGT001 即時訊息通知
     *
     * @param req
     * @param err
     * @return
     * @throws Exception
     */
    @PostMapping("/message/send")
    @Operation(summary = "LIP-B-CCMRTMSGT001 即時訊息通知")
    public ResponseTemplate<EmptyDto> sendMessage(@Valid
    @RequestBody
    RequestTemplate<CCMRTMSGT001Tranrq> req, Errors err) throws DataNotFoundException, RestException, IOException {
        validateRequest(err);
        return theCCMRTMSGT001Svc.sendMessage(req);
    }

}
```

**CalculateController.java 合約影本計算/列印入口 Java · 46 行**

lip-svc-cln-common/src/main/java/cub/lip/svc/cln/common/controller/CalculateController.java

```java
package cub.lip.svc.cln.common.controller;

import java.io.IOException;

import javax.validation.Valid;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.validation.Errors;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import cub.lip.lib.common.controller.BaseController;
import cub.lip.lib.common.dto.base.RequestTemplate;
import cub.lip.lib.common.dto.base.ResponseTemplate;
import cub.lip.svc.cln.common.dto.ccm.CCMCTPCPQ001Tranrq;
import cub.lip.svc.cln.common.dto.ccm.CCMCTPCPQ001Tranrs;
import cub.lip.svc.cln.common.svc.CCMCTPCPQ001Svc;
import io.swagger.v3.oas.annotations.Operation;

@RestController
@RequestMapping("/calculate")
public class CalculateController extends BaseController {

    /** CCMCINTRQ001Svc 借款人及共借人行內資料 */
    @Autowired
    private CCMCTPCPQ001Svc theCCMCTPCPQ001Svc;

    /**
     * LIP-B-CCMCTPCPQ001 共用計算契據列印份數
     * 
     * @param req
     * @param err
     * @return
     * @throws IOException
     */
    @PostMapping("/contract/printCopy")
    @Operation(summary = "LIP-B-CCMCTPCPQ001 共用計算契據列印份數")
    public ResponseTemplate<CCMCTPCPQ001Tranrs> calculatePrintCopy(@Valid
    @RequestBody
    RequestTemplate<CCMCTPCPQ001Tranrq> req, Errors err) throws IOException {
        validateRequest(err);
        return theCCMCTPCPQ001Svc.calculatePrintCopy(req);
    }
}
```

**README.md 目前仍是通用範本 Markdown · 20 行**

lip-svc-cln-common/README.md

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

-   [ ] 確認能力確實供多個 CLN 流程共用，服務邊界有依據。
-   [ ] 核對 API ID、URI、電文欄位、錯誤碼與回傳碼。
-   [ ] 確認外部整合失敗、重試與消費端相容性。
-   [ ] README 尚是範本；設定與用途依實際規格/部署環境核實。
