# lip-svc-cln-query

## lip-svc-cln-query

查詢服務指南：從專案結構與資料流開始，再以 CQYCINPTQ001 說明規格、DTO、SQL、Service 和測試如何互相對照。

## 專案架構與資料流

### Package 與資源目錄

左側為 Java packages，右側為設定及 SQL 資源。目錄圖表示程式歸屬，不表示呼叫順序。

lip-svc-cln-query/

src/main/java/cub/lip/svc/cln/query/

-   `controller/` HTTP API 入口、路徑與驗證
    
-   `svc/ + impl/` 服務契約與查詢流程實作
    
-   `repo/` Repository 資料存取
    
-   `entity/` 資料實體與欄位映射
    
-   `dto/ + vo/` 電文與服務資料結構
    
-   `adapter/` 共用或外部能力轉接
    
-   `soap/` SOAP 服務整合
    
-   `check/` 查詢相關檢核
    
-   `config/ + util/` 設定與工具
    

src/main/resources/

-   `sql/` 外部 SQL 查詢檔
    
-   `config/` 資源設定
    
-   `application.yml` Spring Boot 設定
    
-   `logback-*.xml` 日誌設定
    

### Request 如何成為 Response

01 **Controller** 接收與驗證

解析請求、檢查輸入，委派 Service。

→

02 **Service / Impl** 查詢編排

執行業務處理、補值並整理結果。

→

03 **Repository / SQL** 資料查詢

依查詢條件讀取資料庫結果。

→

04 **DTO / VO** 資料映射

將資料組成 API 回應所需結構。

→

05 **Response** 標準回覆

由共用工廠包裝 ResponseTemplate。

## API 慣例與檢查點

| 位置 | 常見模式 | 實作檢查點 |
| --- | --- | --- |
| Controller | `@RestController`、`@RequestMapping`、`@PostMapping` | `@Operation` 說明電文 ID；以 `@Valid @RequestBody RequestTemplate<Tranrq>` 和 `Errors` 驗證，先 `validateRequest(err)` 再委派。 |
| DTO | `{API}Tranrq`／`{API}Tranrs`，Java 欄位 camelCase、JSON 欄位依契約 | 沿用 Serializable、Lombok、`@JsonProperty` 與 Bean Validation；JSON 名稱逐欄核對規格。 |
| Service | 介面放在 `svc/`，實作放在 `svc/impl/` | 主流程保持輸入解析、資料查詢、結果組裝、標準回應；避免把查詢塞進 Controller。 |
| 資料存取 | 單純查詢可用 JPA；多表 JOIN、複雜條件或排序使用 SQL 資源 | 用命名參數，不串接使用者輸入；確認 SQL alias 可對應 Entity／DTO。 |
| 空資料與錯誤 | 沿用共用例外和回應封裝 | 規格需定義查無資料、空集合、null、驗證失敗與系統錯誤各自如何回應。 |
| 測試 | ServiceImpl 測試常見 JUnit 5、Mockito、`@Mock`、`@InjectMocks` | 覆蓋成功、查無資料、空集合、規則分支與轉換錯誤；外部依賴以 mock 隔離。 |

## 從規格到查詢 API

### 拆 API 契約

確認 API ID、URI、HTTP method、Content-Type、輸入/輸出欄位、必填、長度與錯誤碼。

### 整理欄位對照

記錄 JSON 欄位、型別、驗證、資料來源、計算方式與空值行為；矛盾處保留依據並標註待確認。

### 找最近的同類 API

先看同類 Controller、Service、DTO、Repository／SQL 和測試，只沿用相關模式。

### 實作查詢與組裝

依複雜度選擇 Repository 或 SQL；在 ServiceImpl 做映射、代碼補值、清單組裝與空值處理。

### 逐情境驗證

測成功、查無資料、空集合和重要規則分支，再逐欄對照規格與 Response JSON。

## 完整案例：LIP-B-CQYCINPTQ001

| 資訊 | 目前程式觀察 | 對應位置 |
| --- | --- | --- |
| 功能 | 查詢進件輸入資訊 | Service、DTO、測試命名 |
| 端點 | `POST /case/inputInfo/query` | CaseController |
| 輸入 | ApplyId；目前 DTO 另含 UserBranch | CQYCINPTQ001Tranrq |
| 資料與輸出 | 案件、影像受理、借保人資料；案件欄位及巢狀清單 | SQL、Repository、Tranrs |

### Controller 與 Request DTO

```
@PostMapping("/inputInfo/query")
@Operation(summary = "LIP-B-CQYCINPTQ001 查詢進件輸入資訊")
public ResponseTemplate<CQYCINPTQ001Tranrs> inputInfoQuery(
        @Valid @RequestBody RequestTemplate<CQYCINPTQ001Tranrq> req,
        Errors err) throws Exception {
    validateRequest(err);
    return theCQYCINPTQ001Svc.inputInfoQuery(req);
}

@NotBlank(message = "ApplyId 不得為空")
@Size(max = 16)
@JsonProperty("ApplyId")
private String applyId;
```

### SQL 與 ServiceImpl 流程

```
from LONLXLIP01CLN.CLN_CASE_MAIN CCM
left join LONLXLIP01CLN.CLN_CASE_SUB CCS
  on CCM.APPLY_ID = CCS.APPLY_ID
where CCM.APPLY_ID = :ApplyId
  and CCM.LOAN_TYPE in ('1', '2')
```

**取得條件** ApplyId、使用者單位

**查主資料** 案件主檔與影像子檔

**轉換補值** 代碼、分行與員工名稱

**組清單** 帳務行與借保人

**包裝回應** NormalResponseFactory

-   以命名參數執行 SQL；保證人資料另由 Repository 查詢。
-   ServiceImpl 映射 Entity 至 Response DTO，並補上代碼名稱、快取顯示名稱及巢狀清單。
-   以規格定義查無資料和欄位為 null 時的回應語意。

### 主要原始碼

**CaseController.java 端點與驗證 Java · 184 行**

lip-svc-cln-query/src/main/java/cub/lip/svc/cln/query/controller/CaseController.java

```java
package cub.lip.svc.cln.query.controller;

import java.io.IOException;

import javax.validation.Valid;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.validation.Errors;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.fasterxml.jackson.core.JsonProcessingException;

import cub.lip.lib.common.controller.BaseController;
import cub.lip.lib.common.dto.base.RequestTemplate;
import cub.lip.lib.common.dto.base.ResponseTemplate;
import cub.lip.lib.common.exception.DataNotFoundException;
import cub.lip.lib.common.exception.RestException;
import cub.lip.svc.cln.query.dto.cqy.CQYBASIFQ001Tranrq;
import cub.lip.svc.cln.query.dto.cqy.CQYBASIFQ001Tranrs;
import cub.lip.svc.cln.query.dto.cqy.CQYCHKTBQ001Tranrq;
import cub.lip.svc.cln.query.dto.cqy.CQYCHKTBQ001Tranrs;
import cub.lip.svc.cln.query.dto.cqy.CQYCINPTQ001Tranrq;
import cub.lip.svc.cln.query.dto.cqy.CQYCINPTQ001Tranrs;
import cub.lip.svc.cln.query.dto.cqy.CQYIAPINQ001Tranrq;
import cub.lip.svc.cln.query.dto.cqy.CQYIAPINQ001Tranrs;
import cub.lip.svc.cln.query.dto.cqy.CQYJCFINQ001Tranrq;
import cub.lip.svc.cln.query.dto.cqy.CQYJCFINQ001Tranrs;
import cub.lip.svc.cln.query.dto.cqy.CQYREJECQ001Tranrq;
import cub.lip.svc.cln.query.dto.cqy.CQYREJECQ001Tranrs;
import cub.lip.svc.cln.query.svc.CQYBASIFQ001Svc;
import cub.lip.svc.cln.query.svc.CQYCHKTBQ001Svc;
import cub.lip.svc.cln.query.svc.CQYCINPTQ001Svc;
import cub.lip.svc.cln.query.svc.CQYIAPINQ001Svc;
import cub.lip.svc.cln.query.svc.CQYJCFINQ001Svc;
import cub.lip.svc.cln.query.svc.CQYREJECQ001Svc;
import io.swagger.v3.oas.annotations.Operation;

/**
 * CaseController
 *
 * @author 00550352
 */
@RestController
@RequestMapping("/case")
public class CaseController extends BaseController {

    /** CQYBASIFQ001Svc 基本資料查詢 */
    @Autowired
    private CQYBASIFQ001Svc theCQYBASIFQ001Svc;

    /** CQYCHKTBQ001Svc 進件主畫面頁籤檢核查詢 */
    @Autowired
    private CQYCHKTBQ001Svc theCQYCHKTBQ001Svc;

    /** CQYCINPTQ001Svc 查詢進件輸入資訊 */
    @Autowired
    private CQYCINPTQ001Svc theCQYCINPTQ001Svc;

    /** CQYIAPINQ001Svc 查詢申請條件輸入資訊 */
    @Autowired
    private CQYIAPINQ001Svc theCQYIAPINQ001Svc;

    /** CQYREJECQ001Svc 撤件查詢 */
    @Autowired
    private CQYREJECQ001Svc theCQYREJECQ001Svc;

    /** CQYJCFINQ001Svc 財所清清單查詢 */
    @Autowired
    private CQYJCFINQ001Svc theCQYJCFINQ001Svc;

    /**
     * LIP-B-CQYBASIFQ001 基本資料查詢
     *
     * @param req
     * @param err
     * @return
     * @throws IOException
     * @throws DataNotFoundException
     */
    @PostMapping("/baseInfo/query")
    @Operation(summary = "LIP-B-CQYBASIFQ001 基本資料查詢")
    public ResponseTemplate<CQYBASIFQ001Tranrs> queryBaseInfo(@Valid
    @RequestBody
    RequestTemplate<CQYBASIFQ001Tranrq> req, Errors err) throws IOException, DataNotFoundException {
        validateRequest(err);
        return theCQYBASIFQ001Svc.queryBaseInfo(req);
    }

    /**
     * LIP-B-CQYCHKTBQ001 進件主畫面頁籤檢核查詢
     *
     * @param req
     * @param err
     * @return
     * @throws IOException
     */
    @PostMapping("/tabsCheck/query")
    @Operation(summary = "LIP-B-CQYCHKTBQ001 進件主畫面頁籤檢核查詢")
    public ResponseTemplate<CQYCHKTBQ001Tranrs> queryTabsCheck(@Valid
    @RequestBody
    RequestTemplate<CQYCHKTBQ001Tranrq> req, Errors err) throws IOException {
        validateRequest(err);
        return theCQYCHKTBQ001Svc.queryTabsCheck(req);
    }

    /**
     * LIP-B-CQYCINPTQ001 查詢進件輸入資訊
     *
     * @param req
     * @param err
     * @return
     * @throws DataNotFoundException
     * @throws ClassNotFoundException
     * @throws JsonProcessingException
     */
    @PostMapping("/inputInfo/query")
    @Operation(summary = "LIP-B-CQYCINPTQ001 查詢進件輸入資訊")
    public ResponseTemplate<CQYCINPTQ001Tranrs> inputInfoQuery(@Valid
    @RequestBody
    RequestTemplate<CQYCINPTQ001Tranrq> req, Errors err) throws DataNotFoundException, ClassNotFoundException, IOException, RestException {
        validateRequest(err);
        return theCQYCINPTQ001Svc.inputInfoQuery(req);
    }

    /**
     * LIP-B-CQYIAPINQ001 查詢申請條件輸入資訊
     *
     * @param req
     * @param err
     * @return
     * @throws DataNotFoundException
     * @throws IOException
     */
    @PostMapping("/applyInput/query")
    @Operation(summary = "LIP-B-CQYIAPINQ001 查詢申請條件輸入資訊")
    public ResponseTemplate<CQYIAPINQ001Tranrs> queryApplyInput(@Valid
    @RequestBody
    RequestTemplate<CQYIAPINQ001Tranrq> req, Errors err) throws IOException, DataNotFoundException {
        validateRequest(err);
        return theCQYIAPINQ001Svc.queryApplyInput(req);
    }

    /**
     * LIP-B-CQYREJECQ001 撤件查詢
     *
     * @param req
     * @param err
     * @return
     * @throws IOException
     * @throws DataNotFoundException
     * @throws ClassNotFoundException
     */
    @PostMapping("/reject/query")
    @Operation(summary = "LIP-B-CQYREJECQ001 撤件查詢")
    public ResponseTemplate<CQYREJECQ001Tranrs> rejectQuery(@Valid
    @RequestBody
    RequestTemplate<CQYREJECQ001Tranrq> req, Errors err) throws IOException, DataNotFoundException, ClassNotFoundException {
        validateRequest(err);
        return theCQYREJECQ001Svc.rejectQuery(req);
    }

    /**
     * LIP-B-CQYJCFINQ001 財所清清單查詢
     *
     * @param req
     * @param err
     * @return
     * @throws IOException
     * @throws DataNotFoundException
     * @throws ClassNotFoundException
     */
    @PostMapping("/jcic/queryJcicFin")
    @Operation(summary = "LIP-B-CQYJCFINQ001 財所清清單查詢")
    public ResponseTemplate<CQYJCFINQ001Tranrs> queryJcicFin(@Valid
    @RequestBody
    RequestTemplate<CQYJCFINQ001Tranrq> req, Errors err) throws IOException, DataNotFoundException, ClassNotFoundException {
        validateRequest(err);
        return theCQYJCFINQ001Svc.queryJcicFin(req);
    }

}
```

**CQYCINPTQ001Tranrq.java 輸入 DTO Java · 33 行**

lip-svc-cln-query/src/main/java/cub/lip/svc/cln/query/dto/cqy/CQYCINPTQ001Tranrq.java

```java
package cub.lip.svc.cln.query.dto.cqy;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.Size;
import java.io.Serializable;

/**
 * LIP-B-CQYCINPTQ001查詢進件輸入資訊
 * 上行/請求
 *
 * @author 00550352
 */
@Data
public class CQYCINPTQ001Tranrq implements Serializable {

    /** serialVersionUID */
    private static final long serialVersionUID = 1L;

    /** 受理編號 */
    @NotBlank(message = "ApplyId 不得為空")
    @Size(message = "ApplyId 長度不得超過 16", max = 16)
    @JsonProperty("ApplyId")
    private String applyId;

    /** 登入者單位 */
    @NotBlank(message = "UserBranch 不得為空")
    @Size(message = "UserBranch 長度不得超過 10", max = 10)
    @JsonProperty("UserBranch")
    private String userBranch;
}
```

**CQYCINPTQ001Svc.java Service 契約 Java · 21 行**

lip-svc-cln-query/src/main/java/cub/lip/svc/cln/query/svc/CQYCINPTQ001Svc.java

```java
package cub.lip.svc.cln.query.svc;

import java.io.IOException;

import cub.lip.lib.common.dto.base.RequestTemplate;
import cub.lip.lib.common.dto.base.ResponseTemplate;
import cub.lip.lib.common.exception.DataNotFoundException;
import cub.lip.lib.common.exception.RestException;
import cub.lip.svc.cln.query.dto.cqy.CQYCINPTQ001Tranrq;
import cub.lip.svc.cln.query.dto.cqy.CQYCINPTQ001Tranrs;

/**
 * LIP-B-CQYCINPTQ001 查詢進件輸入資訊
 *
 * @author 00550352
 */
public interface CQYCINPTQ001Svc {

    ResponseTemplate<CQYCINPTQ001Tranrs> inputInfoQuery(RequestTemplate<CQYCINPTQ001Tranrq> request)
            throws ClassNotFoundException, DataNotFoundException, IOException, RestException;
}
```

**CQYCINPTQ001SvcImpl.java 查詢與回應組裝 Java · 197 行**

lip-svc-cln-query/src/main/java/cub/lip/svc/cln/query/svc/impl/CQYCINPTQ001SvcImpl.java

```java
package cub.lip.svc.cln.query.svc.impl;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.stream.Collectors;

import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;

import cub.lip.lib.cln.common.base.dto.CodeOptionItem;
import cub.lip.lib.cln.common.enums.ClnBranchType;
import cub.lip.lib.cln.common.util.CommCodeUtil;
import cub.lip.lib.common.dto.base.DeptDto;
import cub.lip.lib.common.dto.base.DeptI18nDto;
import cub.lip.lib.common.dto.base.EmployeeDto;
import cub.lip.lib.common.dto.base.RequestTemplate;
import cub.lip.lib.common.dto.base.ResponseTemplate;
import cub.lip.lib.common.enums.CommonBranchDeptMappingType;
import cub.lip.lib.common.enums.CommonCacheType;
import cub.lip.lib.common.exception.DataNotFoundException;
import cub.lip.lib.common.exception.RestException;
import cub.lip.lib.common.factory.CacheBasicFactory;
import cub.lip.lib.common.util.cache.BranchTypeUtil;
import cub.lip.lib.common.util.common.OrikaMapperUtil;
import cub.lip.lib.common.util.sql.SqlAction;
import cub.lip.lib.common.util.sql.SqlUtils;
import cub.lip.lib.common.util.transfer.NormalResponseFactory;
import cub.lip.svc.cln.query.dto.cqy.CQYCINPTQ001Tranrq;
import cub.lip.svc.cln.query.dto.cqy.CQYCINPTQ001Tranrs;
import cub.lip.svc.cln.query.dto.cqy.CQYCINPTQ001TranrsBorGuar;
import cub.lip.svc.cln.query.dto.cqy.CQYCINPTQ001TranrsRemitBranch;
import cub.lip.svc.cln.query.entity.cln.ClnCaseMainEntity;
import cub.lip.svc.cln.query.entity.cln.ClnCaseSubEntity;
import cub.lip.svc.cln.query.entity.cln.ClnCustomerGuarantorEntity;
import cub.lip.svc.cln.query.repo.ClnCustomerGuarantorRepository;
import cub.lip.svc.cln.query.svc.CQYCINPTQ001Svc;

/**
 * LIP-B-CQYCINPTQ001查詢進件輸入資訊
 *
 * @author 00550352
 */
@Service
public class CQYCINPTQ001SvcImpl implements CQYCINPTQ001Svc {

    /** NormalResponseFactory */
    @Autowired
    private NormalResponseFactory normalResponseFactory;

    /** ClnCustomerGuarantorRepository */
    @Autowired
    private ClnCustomerGuarantorRepository clnCustomerGuarantorRepository;

    /** CommCodeUtil */
    @Autowired
    private CommCodeUtil commCodeUtil;

    /** BranchTypeUtil */
    @Autowired
    private BranchTypeUtil branchTypeUtil;

    /** CacheBasicFactory */
    @Autowired
    private CacheBasicFactory cacheBasicFactory;

    /** OrikaMapperUtil */
    @Autowired
    private OrikaMapperUtil orikaMapperUtil;

    /** ObjectMapper */
    @Autowired
    private ObjectMapper objectMapper;

    /** SqlAction */
    @Autowired
    private SqlAction sqlAction;

    /** SqlUtils */
    @Autowired
    private SqlUtils sqlUtils;

    /** CQYCINPTQ001_QUERY_001 */
    private static final String CQYCINPTQ001_QUERY_001 = "CQYCINPTQ001_query_001.sql";

    @Override
    public ResponseTemplate<CQYCINPTQ001Tranrs> inputInfoQuery(RequestTemplate<CQYCINPTQ001Tranrq> request)
            throws ClassNotFoundException, DataNotFoundException, IOException, RestException {

        CQYCINPTQ001Tranrq tranrq = request.getTranrq();
        boolean isEffectBranch = branchTypeUtil.isDirectMarketingDept(CommonBranchDeptMappingType.CLN, tranrq.getUserBranch());
        Optional<Map<String, DeptDto>> deptMapOpt = Optional.ofNullable(objectMapper.readValue(
            objectMapper
                    .writeValueAsString(cacheBasicFactory.getCacheBasicService(CommonCacheType.DEPT.getCacheName()).getCacheReadOnlyData()),
            new TypeReference<Map<String, DeptDto>>() {
            }));

        Optional<Map<String, EmployeeDto>> empMapOpt = Optional.ofNullable(objectMapper.readValue(
            objectMapper
                    .writeValueAsString(cacheBasicFactory.getCacheBasicService(CommonCacheType.EMP.getCacheName()).getCacheReadOnlyData()),
            new TypeReference<Map<String, EmployeeDto>>() {
            }));

        // 1.查詢CLN_CASE_MAIN (案件受理檔), CLN_CASE_SUB(影像受理檔)
        Map<String, Object> paramMap = new HashMap<>();
        paramMap.put("ApplyId", tranrq.getApplyId());
        return sqlAction.queryForList(sqlUtils.getQuerySql(CQYCINPTQ001_QUERY_001), paramMap).stream().map(row -> {
            ClnCaseMainEntity entity = objectMapper.convertValue(row, ClnCaseMainEntity.class);
            ClnCaseSubEntity subEntity = objectMapper.convertValue(row, ClnCaseSubEntity.class);

            CQYCINPTQ001Tranrs tranrs = orikaMapperUtil.map(entity, CQYCINPTQ001Tranrs.class);
            tranrs.setApplyId(tranrq.getApplyId());
            tranrs.setIsOnlineApplyName("Y".equals(entity.getIsOnlineApply()) ? "是" : "否");
            tranrs.setLoanTypeName(getCommonCodeName("LOAN_TYPE", entity.getLoanType()));
            tranrs.setApplyProcessName(getCommonCodeName("APPLY_PROCESS", entity.getApplyProcess()));

            // 取CLN_CASE_SUB中，CaseOrigin、OriginTm、OriginNtm相關值
            BeanUtils.copyProperties(subEntity, tranrs);

            deptMapOpt.ifPresent(deptMap -> {
                tranrs.setRmBranchName(getDeptFullName(deptMap, entity.getRmBranch()));
                tranrs.setAgentBranchName(getDeptFullName(deptMap, entity.getAgentBranch()));
                tranrs.setRemitBranchName(getDeptFullName(deptMap, entity.getRemitBranch()));
                tranrs.setGuarantorBranchName(getDeptFullName(deptMap, entity.getGuarantorBranch()));
                tranrs.setAoHeadBranchName(getDeptFullName(deptMap, entity.getAoHeadBranch()));
            });
            empMapOpt.ifPresent(empMap -> tranrs.setRmName(empMap.getOrDefault(entity.getRmId(), new EmployeeDto()).getEmployeeName()));

            // 2.取得帳務行下拉選單清單
            try {
                List<DeptDto> deptList = branchTypeUtil.getDeptDtoByFullComplianceBranchTypes(CommonBranchDeptMappingType.CLN,
                    ClnBranchType.REMIT_BRANCH);
                List<CQYCINPTQ001TranrsRemitBranch> remitBranchList = deptList.stream().filter(Objects::nonNull).map(deptDto -> {
                    CQYCINPTQ001TranrsRemitBranch remitBranch = new CQYCINPTQ001TranrsRemitBranch();

                    if (deptDto.getI18nInfo() != null && deptDto.getI18nInfo().get("zh_TW") != null) {
                        DeptI18nDto zhTwInfo = deptDto.getI18nInfo().get("zh_TW");

                        remitBranch.setRemitBranchId(zhTwInfo.getBranchId() != null ? zhTwInfo.getBranchId() : "");
                        remitBranch.setRemitBranchName(zhTwInfo.getFullName() != null ? zhTwInfo.getFullName() : "");
                    }
                    return remitBranch;
                }).collect(Collectors.toList());
                tranrs.setRemitBranchList(remitBranchList);
            } catch (Exception e) {
                tranrs.setRemitBranchList(null);
            }

            // 3. TODO

            // 4. TODO

            // 5.查詢CLN_CUSTOMER_GUARANTOR (保證人異動檔)
            List<ClnCustomerGuarantorEntity> cgList = clnCustomerGuarantorRepository.findByApplyIdOrderByGuarKind5Desc(tranrq.getApplyId());
            if (!cgList.isEmpty()) {
                List<CQYCINPTQ001TranrsBorGuar> borGuarList = new ArrayList<>();
                cgList.forEach(cg -> {
                    CQYCINPTQ001TranrsBorGuar borGuar = new CQYCINPTQ001TranrsBorGuar();
                    borGuar.setBorGuarId(cg.getGuarId());
                    borGuar.setBorGuarName(cg.getGuarName());
                    borGuar.setType(cg.getGuarKind5());
                    String borGuarKind = "1".equals(cg.getGuarKind1()) ? "1"
                            : "1".equals(cg.getGuarKind2()) ? "2" : "1".equals(cg.getGuarKind3()) ? "3" : "0";
                    borGuar.setBorGuarKind(borGuarKind);
                    borGuar.setBorGuarKindName(getCommonCodeName("GUAR_KIND", borGuarKind));
                    borGuar.setIsGageOwner("1".equals(cg.getGuarKind4()) ? "1" : "0");
                    borGuarList.add(borGuar);
                });
                tranrs.setBorGuarList(borGuarList);
            }

            // 6. TODO

            // 7.判斷登入者是否為直效單位
            tranrs.setIsEffectBranch(isEffectBranch ? "Y" : "N");

            return normalResponseFactory.genNormalResponse(tranrs, request);
        }).findFirst().orElse(normalResponseFactory.genNormalResponse(new CQYCINPTQ001Tranrs(), request));
    }

    private String getCommonCodeName(String type, String code) {
        return commCodeUtil.getAllComnCodes(type, code).stream().findFirst().map(CodeOptionItem::getCodeName).orElse(null);
    }

    private String getDeptFullName(Map<String, DeptDto> deptMap, String branchId) {
        return Optional.ofNullable(deptMap.get(branchId)).map(DeptDto::getI18nInfo).map(i18n -> i18n.get("zh_TW"))
                .map(DeptI18nDto::getFullName).orElse("");
    }
}
```

**CQYCINPTQ001\_query\_001.sql SQL 查詢 SQL · 97 行**

lip-svc-cln-query/src/main/resources/sql/CQYCINPTQ001\_query\_001.sql

```sql
select
    CCM.*,
    CCS.APPLY_ID as CCS_APPLY_ID,
    CCS.LAND_DOC,
    CCS.APPLY_DOC,
    CCS.MONEY_DOC,
    CCS.TRADE_DOC,
    CCS.INVEST_DOC,
    CCS.RENT_DOC,
    CCS.PAY_DOC,
    CCS.GUAR_DOC,
    CCS.AGREE_DOC,
    CCS.RELATION_DOC,
    CCS.OTHER_DOC,
    CCS.OTHER_DOC_DESC,
    CCS.APP_CONFIRM_ID,
    CCS.APP_CONFIRM_DEPT,
    CCS.APP_CONFIRM_TIME,
    CCS.REJECT_SERV_DATE,
    CCS.REJECT_CODE,
    CCS.BATCH_STATUS,
    CCS.REUPLOAD_PIC_KEY,
    CCS.UPD_ID,
    CCS.UPD_DATE,
    CCS.SUPPLY_CODE as CCS_SUPPLY_CODE,
    CCS.SUPPLY_DATE,
    CCS.OTHER_ITEM,
    CCS.APPLY_CHANGE,
    CCS.CASE_ORIGIN_BUILDER,
    CCS.CASE_ORIGIN_BROKER,
    CCS.CASE_ORIGIN_BOOK,
    CCS.CASE_ORIGIN_AO,
    CCS.CASE_ORIGIN_EMP,
    CCS.CASE_ORIGIN_DS,
    CCS.CASE_ORIGIN_CLIENT,
    CCS.CASE_ORIGIN_COUNTER,
    CCS.CASE_ORIGIN_TM,
    CCS.CASE_ORIGIN_NTM,
    CCS.CASE_ORIGIN_OTHER,
    CCS.CASE_ORIGIN_OTHER_DESC,
    CCS.ORIGIN_TM_LOAN,
    CCS.ORIGIN_TM_SLOAN,
    CCS.ORIGIN_TM_OB,
    CCS.ORIGIN_TM_OTHER,
    CCS.ORIGIN_TM_OTHER_DESC,
    CCS.ORIGIN_TM_OTHER_CODE,
    CCS.ORIGIN_TM_OTHER_SEQNO,
    CCS.ORIGIN_NTM_CLIENT,
    CCS.ORIGIN_NTM_TRF,
    CCS.ORIGIN_NTM_DS,
    CCS.ORIGIN_NTM_OLD_CLIENT,
    CCS.ORIGIN_NTM_LIST_CLIENT,
    CCS.ORIGIN_NTM_RELATION,
    CCS.ORIGIN_NTM_BROKER,
    CCS.ORIGIN_NTM_OTHER,
    CCS.ORIGIN_NTM_OTHER_DESC,
    CCS.REJECT_REASON,
    CCS.ORIGIN_NTM_TRANS,
    CCS.ORIGIN_NTM_NETWORK,
    CCS.ORIGIN_NTM_CREDIT,
    CCS.ORIGIN_NTM_ADVISORY,
    CCS.ORIGIN_NTM_ADVISORY_DESC,
    CCS.ORIGIN_NTM_ACC_TRANS,
    CCS.ORIGIN_NTM_ACC_REIMBURSE,
    CCS.ORIGIN_NTM_EMP_FAMILY,
    CCS.BRANCH_NOTE_NOSELF,
    CCS.BRANCH_NOTE_AGREEMENT,
    CCS.BRANCH_NOTE_SIMPLE,
    CCS.BRANCH_NOTE_FORSALE,
    CCS.ORIGIN_NTM_NAGENT_LIST_CLIENT,
    CCS.ORIGIN_NTM_NAGENT_OLD_CLIENT,
    CCS.COLL_NO,
    CCS.APPR_MESSAGE,
    CCS.APPR_CHECK_STATUS,
    CCS.APPR_CHECK_DATE,
    CCS.RENTAL,
    CCS.DEPOSIT,
    CCS.RENTAL_START_DATE,
    CCS.RENTAL_END_DATE,
    CCS.TRACKDATA,
    CCS.REC_API_FLAG,
    CCS.INVESTMENT_AMT,
    CCS.INVESTMENT_PERIOD,
    CCS.INVESTMENT_RATE_OF_RETURN,
    CCS.GRACE_PERIOD,
    CCS.CLIENT_ID,
    CCS.AGREE_PROJECT,
    CCS.HAS_PAYOFF,
    CCS.IS_KYC,
    CCS.CASE_ORIGIN,
    CCS.BOND_AMT,
    CCS.BOND_AMT_DESC
from LONLXLIP01CLN.CLN_CASE_MAIN CCM
         left join LONLXLIP01CLN.CLN_CASE_SUB CCS
                   on CCM.APPLY_ID = CCS.APPLY_ID
where CCM.APPLY_ID = :ApplyId
  and CCM.LOAN_TYPE in ('1','2')
```

**CQYCINPTQ001SvcImplTest.java 單元測試參考 Java · 353 行**

lip-svc-cln-query/src/test/java/lip/svc/cln/query/impl/CQYCINPTQ001SvcImplTest.java

```java
package lip.svc.cln.query.impl;

import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentMatchers;
import org.mockito.InjectMocks;
import org.mockito.Mock;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;

import cub.lip.lib.cln.common.base.dto.CodeOptionItem;
import cub.lip.lib.cln.common.enums.ClnBranchType;
import cub.lip.lib.common.cache.CacheBasicService;
import cub.lip.lib.common.dto.base.DeptDto;
import cub.lip.lib.common.dto.base.EmployeeDto;
import cub.lip.lib.common.dto.base.EmptyDto;
import cub.lip.lib.common.dto.base.RequestTemplate;
import cub.lip.lib.common.dto.base.ResponseTemplate;
import cub.lip.lib.common.enums.CommonBranchDeptMappingType;
import cub.lip.lib.common.enums.CommonCacheType;
import cub.lip.lib.common.factory.CacheBasicFactory;
import cub.lip.lib.common.util.cache.BranchTypeUtil;
import cub.lip.svc.cln.query.dto.cqy.CQYCINPTQ001Tranrq;
import cub.lip.svc.cln.query.dto.cqy.CQYCINPTQ001Tranrs;
import cub.lip.svc.cln.query.entity.cln.ClnCaseMainEntity;
import cub.lip.svc.cln.query.entity.cln.ClnCustomerGuarantorEntity;
import cub.lip.svc.cln.query.repo.ClnCaseMainRepository;
import cub.lip.svc.cln.query.repo.ClnCustomerGuarantorRepository;
import cub.lip.svc.cln.query.svc.impl.CQYCINPTQ001SvcImpl;
import lip.svc.cln.query.BaseTest;

/**
 * LIP-B-CQYCINPTQ001查詢進件輸入資訊（單元測試）
 *
 * @author 00550352
 */
class CQYCINPTQ001SvcImplTest extends BaseTest {

    @Mock
    private ClnCaseMainRepository clnCaseMainRepository;

    @Mock
    private ClnCustomerGuarantorRepository clnCustomerGuarantorRepository;

    @Mock
    private BranchTypeUtil branchTypeUtil;

    @Mock
    private CacheBasicFactory cacheBasicFactory;

    @Mock
    private CacheBasicService<String, EmptyDto> cacheBasicService;

    @InjectMocks
    private CQYCINPTQ001SvcImpl service;

    private RequestTemplate<CQYCINPTQ001Tranrq> requestTemplate;

    private CQYCINPTQ001Tranrq tranrq;

    private ClnCaseMainEntity caseMainEntity;

    private CQYCINPTQ001Tranrs tranrs;

    private ResponseTemplate<CQYCINPTQ001Tranrs> responseTemplate;

    @BeforeEach
    void setUp() {
        tranrq = new CQYCINPTQ001Tranrq();
        tranrq.setApplyId("TEST123456");

        requestTemplate = new RequestTemplate<>();
        requestTemplate.setTranrq(tranrq);

        caseMainEntity = new ClnCaseMainEntity();
        caseMainEntity.setApplyId("TEST123456");
        caseMainEntity.setIsOnlineApply("Y");
        caseMainEntity.setLoanType("1");
        caseMainEntity.setApplyProcess("01");
        caseMainEntity.setRmBranch("001");
        caseMainEntity.setRmId("EMP001");
        caseMainEntity.setAgentBranch("002");

        tranrs = new CQYCINPTQ001Tranrs();
        tranrs.setApplyId("TEST123456");

        responseTemplate = new ResponseTemplate<>();
        responseTemplate.setTranrs(tranrs);
    }

    @Test
    @DisplayName("查詢進件輸入資訊 - 成功")
    void testInputInfoQuery_Success() throws Exception {

        // Given
        when(clnCaseMainRepository.findByApplyIdAndLoanTypeIn(eq("TEST123456"), any())).thenReturn(Optional.of(caseMainEntity));

        when(cacheBasicFactory.getCacheBasicService(CommonCacheType.DEPT.getCacheName())).thenAnswer(invocation -> cacheBasicService);
        when(cacheBasicFactory.getCacheBasicService(CommonCacheType.EMP.getCacheName())).thenAnswer(invocation -> cacheBasicService);

        Map<String, DeptDto> deptMap = createDeptMap();
        Map<String, EmployeeDto> empMap = createEmpMap();

        when(cacheBasicService.getCacheReadOnlyData()).thenAnswer(invocation -> deptMap).thenAnswer(invocation -> empMap);
        when(objectMapper.writeValueAsString(any())).thenReturn("{}");
        when(objectMapper.readValue(eq("{}"), ArgumentMatchers.<TypeReference<?>> any())).thenAnswer(invocation -> deptMap)
                .thenAnswer(invocation -> empMap);
        when(orikaMapper.map(caseMainEntity, CQYCINPTQ001Tranrs.class)).thenReturn(tranrs);

        List<CodeOptionItem> loanTypeOptions = Arrays.asList(createCodeOptionItem("1", "個人信貸"));
        when(commCodeUtil.getAllComnCodes("LOAN_TYPE", "1")).thenReturn(loanTypeOptions);

        List<CodeOptionItem> applyProcessOptions = Arrays.asList(createCodeOptionItem("01", "申請中"));
        when(commCodeUtil.getAllComnCodes("APPLY_PROCESS", "01")).thenReturn(applyProcessOptions);

        List<DeptDto> deptList = createDeptList();
        when(branchTypeUtil.getDeptDtoByFullComplianceBranchTypes(CommonBranchDeptMappingType.CLN, ClnBranchType.REMIT_BRANCH))
                .thenReturn(deptList);

        List<ClnCustomerGuarantorEntity> guarantorList = createGuarantorList();
        when(clnCustomerGuarantorRepository.findByApplyIdOrderByGuarKind5Desc("TEST123456")).thenReturn(guarantorList);

        List<CodeOptionItem> guarKindOptions = Arrays.asList(createCodeOptionItem("1", "連帶保證人"));
        when(commCodeUtil.getAllComnCodes("GUAR_KIND", "1")).thenReturn(guarKindOptions);

        when(normalResponseFactory.genNormalResponse(any(CQYCINPTQ001Tranrs.class), eq(requestTemplate))).thenReturn(responseTemplate);

        // When
        ResponseTemplate<CQYCINPTQ001Tranrs> result = service.inputInfoQuery(requestTemplate);

        // Then
        assertNotNull(result);
    }

    @Test
    @DisplayName("查詢進件輸入資訊 - 查無資料")
    void testInputInfoQuery_CaseNotFound() throws Exception {
        // Given
        when(clnCaseMainRepository.findByApplyIdAndLoanTypeIn(eq("TEST123456"), any())).thenReturn(Optional.empty());

        when(cacheBasicFactory.getCacheBasicService(CommonCacheType.DEPT.getCacheName())).thenAnswer(invocation -> cacheBasicService);
        when(cacheBasicFactory.getCacheBasicService(CommonCacheType.EMP.getCacheName())).thenAnswer(invocation -> cacheBasicService);

        Map<String, DeptDto> deptMap = createDeptMap();
        Map<String, EmployeeDto> empMap = createEmpMap();

        when(cacheBasicService.getCacheReadOnlyData()).thenAnswer(invocation -> deptMap).thenAnswer(invocation -> empMap);
        when(objectMapper.writeValueAsString(any())).thenReturn("{}");
        when(objectMapper.readValue(eq("{}"), ArgumentMatchers.<TypeReference<?>> any())).thenAnswer(invocation -> deptMap)
                .thenAnswer(invocation -> empMap);

        CQYCINPTQ001Tranrs emptyTranrs = new CQYCINPTQ001Tranrs();
        responseTemplate = new ResponseTemplate<>();
        responseTemplate.setTranrs(emptyTranrs);
        when(normalResponseFactory.genNormalResponse(any(CQYCINPTQ001Tranrs.class), eq(requestTemplate))).thenReturn(responseTemplate);

        // When
        ResponseTemplate<CQYCINPTQ001Tranrs> result = service.inputInfoQuery(requestTemplate);

        // Then
        assertNotNull(result);
    }

    @Test
    @DisplayName("查詢進件輸入資訊 - IsOnlineApply為N")
    void testInputInfoQuery_IsOnlineApplyN() throws Exception {
        // Given
        caseMainEntity.setIsOnlineApply("N");
        when(clnCaseMainRepository.findByApplyIdAndLoanTypeIn(eq("TEST123456"), any())).thenReturn(Optional.of(caseMainEntity));

        setupBasicMocks();

        // When
        service.inputInfoQuery(requestTemplate);

        // Then
        verify(orikaMapper).map(caseMainEntity, CQYCINPTQ001Tranrs.class);
    }

    @Test
    @DisplayName("查詢進件輸入資訊 - CLN_CUSTOMER_GUARANTOR查無資料")
    void testInputInfoQuery_EmptyGuarantorList() throws Exception {
        // Given
        when(clnCaseMainRepository.findByApplyIdAndLoanTypeIn(eq("TEST123456"), any())).thenReturn(Optional.of(caseMainEntity));

        setupBasicMocks();

        when(clnCustomerGuarantorRepository.findByApplyIdOrderByGuarKind5Desc("TEST123456")).thenReturn(Collections.emptyList());

        when(normalResponseFactory.genNormalResponse(any(CQYCINPTQ001Tranrs.class), eq(requestTemplate))).thenReturn(responseTemplate);

        // When
        ResponseTemplate<CQYCINPTQ001Tranrs> result = service.inputInfoQuery(requestTemplate);

        // Then
        assertNotNull(result);
    }

    @Test
    @DisplayName("查詢進件輸入資訊 - 轉換失敗")
    void testInputInfoQuery_JsonProcessingException() throws Exception {

        when(cacheBasicFactory.getCacheBasicService(CommonCacheType.DEPT.getCacheName())).thenAnswer(invocation -> cacheBasicService);
        when(cacheBasicService.getCacheReadOnlyData()).thenReturn(new HashMap<>());
        when(objectMapper.writeValueAsString(any())).thenThrow(new JsonProcessingException("JSON error") {
            private static final long serialVersionUID = 1L;
        });

        // When & Then
        assertThrows(JsonProcessingException.class, () -> {
            service.inputInfoQuery(requestTemplate);
        });
    }

    @Test
    @DisplayName("查詢進件輸入資訊 - 驗證GuarKind邏輯")
    void testGuarantorKindLogic() throws Exception {
        // Given
        ClnCustomerGuarantorEntity guarantor1 = new ClnCustomerGuarantorEntity();
        guarantor1.setGuarId("G001");
        guarantor1.setGuarName("保證人1");
        guarantor1.setGuarKind1("1");
        guarantor1.setGuarKind2("0");
        guarantor1.setGuarKind3("0");
        guarantor1.setGuarKind4("1");

        ClnCustomerGuarantorEntity guarantor2 = new ClnCustomerGuarantorEntity();
        guarantor2.setGuarId("G002");
        guarantor2.setGuarName("保證人2");
        guarantor2.setGuarKind1("0");
        guarantor2.setGuarKind2("1");
        guarantor2.setGuarKind3("0");
        guarantor2.setGuarKind4("0");

        ClnCustomerGuarantorEntity guarantor3 = new ClnCustomerGuarantorEntity();
        guarantor3.setGuarId("G003");
        guarantor3.setGuarName("保證人3");
        guarantor3.setGuarKind1("0");
        guarantor3.setGuarKind2("0");
        guarantor3.setGuarKind3("1");
        guarantor3.setGuarKind4("0");

        when(clnCaseMainRepository.findByApplyIdAndLoanTypeIn(eq("TEST123456"), any())).thenReturn(Optional.of(caseMainEntity));

        setupBasicMocks();

        when(clnCustomerGuarantorRepository.findByApplyIdOrderByGuarKind5Desc("TEST123456"))
                .thenReturn(Arrays.asList(guarantor1, guarantor2, guarantor3));

        List<CodeOptionItem> guarKindOptions = Arrays.asList(createCodeOptionItem("1", "連帶保證人"));
        when(commCodeUtil.getAllComnCodes(eq("GUAR_KIND"), anyString())).thenReturn(guarKindOptions);

        when(normalResponseFactory.genNormalResponse(any(CQYCINPTQ001Tranrs.class), eq(requestTemplate))).thenReturn(responseTemplate);

        // When
        service.inputInfoQuery(requestTemplate);

        // Then
        verify(clnCustomerGuarantorRepository).findByApplyIdOrderByGuarKind5Desc("TEST123456");
        verify(commCodeUtil, times(3)).getAllComnCodes(eq("GUAR_KIND"), anyString());
    }

    private void setupBasicMocks() throws Exception {
        when(cacheBasicFactory.getCacheBasicService(CommonCacheType.DEPT.getCacheName())).thenAnswer(invocation -> cacheBasicService);
        when(cacheBasicFactory.getCacheBasicService(CommonCacheType.EMP.getCacheName())).thenAnswer(invocation -> cacheBasicService);

        Map<String, DeptDto> deptMap = createDeptMap();
        Map<String, EmployeeDto> empMap = createEmpMap();

        when(cacheBasicService.getCacheReadOnlyData()).thenAnswer(invocation -> deptMap).thenAnswer(invocation -> empMap);
        when(objectMapper.writeValueAsString(any())).thenReturn("{}");
        when(objectMapper.readValue(eq("{}"), ArgumentMatchers.<TypeReference<?>> any())).thenAnswer(invocation -> deptMap)
                .thenAnswer(invocation -> empMap);
        when(orikaMapper.map(caseMainEntity, CQYCINPTQ001Tranrs.class)).thenReturn(tranrs);

        List<CodeOptionItem> options = Arrays.asList(createCodeOptionItem("1", "測試"));
        when(commCodeUtil.getAllComnCodes(anyString(), anyString())).thenReturn(options);

        List<DeptDto> deptList = createDeptList();
        when(branchTypeUtil.getDeptDtoByFullComplianceBranchTypes(CommonBranchDeptMappingType.CLN, ClnBranchType.REMIT_BRANCH))
                .thenReturn(deptList);

        when(clnCustomerGuarantorRepository.findByApplyIdOrderByGuarKind5Desc("TEST123456")).thenReturn(Collections.emptyList());
    }

    private Map<String, DeptDto> createDeptMap() {
        Map<String, DeptDto> deptMap = new HashMap<>();
        DeptDto dept1 = new DeptDto();
        dept1.setFullName("測試分行");
        deptMap.put("001", dept1);

        DeptDto dept2 = new DeptDto();
        dept2.setFullName("代理分行");
        deptMap.put("002", dept2);

        return deptMap;
    }

    private Map<String, EmployeeDto> createEmpMap() {
        Map<String, EmployeeDto> empMap = new HashMap<>();
        EmployeeDto emp = new EmployeeDto();
        emp.setEmployeeName("測試員工");
        empMap.put("EMP001", emp);
        return empMap;
    }

    private CodeOptionItem createCodeOptionItem(String code, String name) {
        CodeOptionItem item = new CodeOptionItem();
        item.setCodeOption(code);
        item.setCodeName(name);
        return item;
    }

    private List<DeptDto> createDeptList() {
        List<DeptDto> deptList = new ArrayList<>();
        DeptDto dept = new DeptDto();
        dept.setFullName("帳務行1");
        deptList.add(dept);
        return deptList;
    }

    private List<ClnCustomerGuarantorEntity> createGuarantorList() {
        List<ClnCustomerGuarantorEntity> guarantorList = new ArrayList<>();
        ClnCustomerGuarantorEntity guarantor = new ClnCustomerGuarantorEntity();
        guarantor.setGuarId("G001");
        guarantor.setGuarName("測試保證人");
        guarantor.setGuarKind1("1");
        guarantor.setGuarKind2("0");
        guarantor.setGuarKind3("0");
        guarantor.setGuarKind4("1");
        guarantorList.add(guarantor);
        return guarantorList;
    }
}
```

## 查詢 API 交付檢查

### 契約與資料

-   [ ] API ID、URI、HTTP method、Content-Type 與 Controller 一致。
-   [ ] Request／Response 欄位及 JSON 名稱逐欄對照規格。
-   [ ] 每個輸出欄位都有資料來源或計算方式。
-   [ ] SQL 參數綁定，無資料和空集合行為明確。

### 測試與專案

-   [ ] 成功、查無資料、空集合和重要分支都有測試。
-   [ ] Service、DTO、SQL 與測試命名互相對得上。
-   [ ] Java 8、共用 DTO、工具及 ResponseFactory 使用方式已確認。
-   [ ] 規格矛盾與 TODO 有明確處置，不以猜測補值。
