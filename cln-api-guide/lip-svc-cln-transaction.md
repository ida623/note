# lip-svc-cln-transaction

## lip-svc-cln-transaction

異動服務指南：從 API 契約進入，追蹤 Service 的業務編排、Check、VO 與 DataProcessor，理解跨表異動的交易邊界。

## 專案架構與異動資料流

Service 編排業務處理；Check 負責跨欄位、角色與狀態等業務檢核；跨多筆／多表的資料寫入可集中於 DataProcessor。各 API 實際使用的層次依需求而定。

lip-svc-cln-transaction/

src/main/java/cub/lip/svc/cln/transaction/

-   `controller/` HTTP API 入口、驗證與委派
    
-   `dto/` Request／Response 電文物件
    
-   `svc/ + impl/` Service 契約與流程編排
    
-   `check/` 業務條件與狀態檢核
    
-   `dataprocessor/` 資料異動與交易控制
    
-   `dataprocessor/vo/` Service 傳給 DataProcessor 的異動集合
    
-   `repo/ + entity/` 資料存取與資料表映射
    
-   `controller/advice/` 錯誤處理、電文與交易日誌
    

src/main/resources/

-   `sql/` 複雜查詢或重用 SQL
    
-   `config/` 環境資源設定
    
-   `application.yml` Spring Boot 設定
    
-   `logback-*.xml` 日誌設定
    

### 異動流程與交易邊界

以進件輸入維護為例：Service 讀取案件、執行檢核並準備異動 VO；DataProcessor 在交易內執行刪除和多個 Repository 儲存。外部 HTTP 呼叫不會隨資料庫交易自動回滾。

01 **Controller** 入口驗證

接受 RequestTemplate，驗證後委派 Service。

→

02 **Service** 流程編排

載入資料、依動作分支、呼叫 Check 或外部服務。

→

03 **Check + VO** 檢核與準備

驗證業務條件，收集待新增、更新、刪除的資料。

→

04 **DataProcessor** 交易寫入

在交易範圍內依序處理多個 Repository。

→

05 **Response** 標準回覆

以共用 ResponseFactory 包裝回應電文。

## 異動 API 慣例與檢查點

| 位置 | 常見模式 | 實作檢查點 |
| --- | --- | --- |
| Controller | 繼承 `BaseController`，以 `@PostMapping` 定義異動端點 | 用 `@Valid @RequestBody RequestTemplate<Tranrq>` 與 Errors；呼叫 `validateRequest(err)` 後委派 Service。 |
| DTO | `{電文代號}Tranrq`／`Tranrs`，常見 `@JsonProperty` | 必填、長度和格式由 DTO 驗證；巢狀 DTO／List 使用 `@Valid`。狀態、權限和跨欄位邏輯由 Check 處理。 |
| Service | Service interface + SvcImpl；成功回應沿用共用 ResponseFactory | 順序清楚呈現資料讀取、檢核、外部整合、異動準備與寫入。 |
| Check | Java Check 處理業務條件，必要時重用既有規則引擎 | 先找既有檢核和代碼；不把 DTO 長度檢查當成業務值合法，也不發明錯誤碼。 |
| 資料與交易 | 單表 CRUD 常見 JPA；多表寫入可用 DataProcessor + VO | 明確設計刪除／新增順序、原子性需求與 rollback 範圍。 |
| 外部服務 | 共用 RequestFactory／RestTemplateHelper，檢查業務 ReturnCode | DB 回滾不會撤銷外呼副作用；需定義逾時、失敗、重試、防重複或補償方式。 |
| 上傳與日誌 | 部分 API 使用 multipart/form-data；共用 Advice 處理錯誤及日誌 | 逐支確認 RequestPart、檔案限制和敏感欄位遮罩；不要把 HTTP 成功等同業務成功。 |

**以方法邊界判斷交易範圍。**

範例 `CTNCINPTT001DataProcessor.processData` 使用 `@Transactional(rollbackFor = Exception.class)`；該方法內 DB 操作依例外回滾，不涵蓋先前已完成的外部呼叫。

## 從規格到異動 API

### 拆解契約與動作語意

確認電文 ID、URI、HTTP method、欄位、錯誤碼，以及 ActionType 等操作方式。

### 區分 DTO 驗證和業務檢核

必填、長度、格式放在 DTO；狀態、角色、跨欄位限制找相近 Check 或規則引擎。

### 追一支完整相近 API

由 Controller 追 DTO、Service、Check、VO、DataProcessor、Repository、Entity 和測試。

### 列出資料異動與交易範圍

逐表定義新增、更新、刪除順序，確認原子性、歷程與回滾條件。

### 設計外部失敗處理

評估外呼成功但 DB 失敗、逾時和重送，明訂補償或防重複策略。

### 驗證成功與失敗情境

覆蓋動作分支、規則失敗、資料不存在、Repository 失敗與外部服務異常；確認測試實際啟用。

## 完整案例：LIP-B-CTNCINPTT001

| 資訊 | 目前程式觀察 | 對應位置 |
| --- | --- | --- |
| 功能 | 進件輸入維護 | Controller、DTO、Service、DataProcessor |
| 端點 | `POST /case/inputInfo/modify` | CaseController |
| 動作分支 | `ActionType` M 修改、D 刪除 | ServiceImpl；規格仍須確認允許操作 |
| 資料異動 | 案件主檔/子檔、客戶、借保人、還款財力、擔保品與歷程 | SvcVO、DataProcessor |
| 回應 | `ResponseTemplate<EmptyDto>` | NormalResponseFactory |

### Controller 與 DTO

```
@PostMapping("/inputInfo/modify")
@Operation(summary = "LIP-B-CTNCINPTT001 進件輸入維護")
public ResponseTemplate<EmptyDto> inputInfoModify(
        @Valid @RequestBody RequestTemplate<CTNCINPTT001Tranrq> req,
        Errors err) throws Exception {
    validateRequest(err);
    return theCTNCINPTT001Svc.inputInfoModify(req);
}

@NotBlank(message = "ActionType 不可為空")
@Size(max = 1)
@JsonProperty("ActionType")
private String actionType;

@Valid
@JsonProperty("BorGuarList")
private List<CTNCINPTT001TranrqBorGuar> borGuarList;
```

### Service 編排與 DataProcessor

**讀案件主檔** 依 ApplyId 載入既有資料

**判斷動作** M 修改或 D 刪除

**執行檢核** CaseCheck 驗證條件

**準備 VO** 收集 Entity、刪除與歷程

**交易寫入** 呼叫 DataProcessor

```
@Transactional(rollbackFor = Exception.class)
public void processData(CTNCINPTT001SvcVO vo) {
    executeDeleteOperations(vo.getDeleteOperations());
    if (CollectionUtils.isNotEmpty(vo.getCaseMainEntities())) {
        clnCaseMainRepository.saveAll(vo.getCaseMainEntities());
    }
    if (CollectionUtils.isNotEmpty(vo.getCaseSubEntities())) {
        clnCaseSubRepository.saveAll(vo.getCaseSubEntities());
    }
    // 其餘客戶、借保人、財力、擔保品與歷程資料
}
```

Service 會依 ActionType 和案件流程狀態準備資料；DataProcessor 先執行刪除，再寫入各類 Entity。上述分支只描述此範例，不代表所有交易 API 的通用規則。

**測試檔目前整體被註解。**

`CTNCINPTT001SvcImplTest.java` 可以參考其 mock 與情境，但不能視為已啟用或已通過的測試。新增測試前應先確認可執行性。

### 主要原始碼

**CaseController.java 端點與驗證 Java · 231 行**

lip-svc-cln-transaction/src/main/java/cub/lip/svc/cln/transaction/controller/CaseController.java

```java
package cub.lip.svc.cln.transaction.controller;

import java.io.IOException;
import javax.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.validation.Errors;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import cub.lip.lib.common.controller.BaseController;
import cub.lip.lib.common.dto.base.EmptyDto;
import cub.lip.lib.common.dto.base.RequestTemplate;
import cub.lip.lib.common.dto.base.ResponseTemplate;
import cub.lip.lib.common.exception.DataDuplicateException;
import cub.lip.lib.common.exception.DataNotFoundException;
import cub.lip.lib.common.exception.RestException;
import cub.lip.svc.cln.transaction.dto.ctn.*;
import cub.lip.svc.cln.transaction.svc.*;
import io.swagger.v3.oas.annotations.Operation;

/**
 * CaseController
 *
 * @author 00550352
 */
@RestController
@RequestMapping("/case")
public class CaseController extends BaseController {

    /** CTNBASIFT001Svc 基本資料維護 */
    @Autowired
    private CTNBASIFT001Svc theCTNBASIFT001Svc;

    /** CTNCINPTT001Svc 進件輸入維護 */
    @Autowired
    private CTNCINPTT001Svc theCTNCINPTT001Svc;

    /** CTNIAPSET001Svc 進件申請條件輸入送出 */
    @Autowired
    private CTNIAPSET001Svc theCTNIAPSET001Svc;

    /** CTNIAPSVT001Svc 進件申請條件輸入儲存 */
    @Autowired
    private CTNIAPSVT001Svc theCTNIAPSVT001Svc;

    /** CTNINITCT001Svc 新增起案(一般件) */
    @Autowired
    private CTNINITCT001Svc theCTNINITCT001Svc;

    /** CTNINITCT002Svc 新增起案(重提複製件) */
    @Autowired
    private CTNINITCT002Svc theCTNINITCT002Svc;

    /** CTNREJECT001Svc 撤件維護 */
    @Autowired
    private CTNREJECT001Svc theCTNREJECT001Svc;

    /** CTNJCFINT001Svc 維護財所清 */
    @Autowired
    private CTNJCFINT001Svc theCTNJCFINT001Svc;

    /** LIP-B-CTNJCFINT002 財所清重查 */
    @Autowired
    private CTNJCFINT002Svc theCTNJCFINT002Svc;

    /**
     * LIP-B-CTNBASIFT001 基本資料維護
     *
     * @param req
     * @param err
     * @return
     * @throws Exception
     */
    @PostMapping("/baseInfo/update")
    @Operation(summary = "LIP-B-CTNBASIFT001 基本資料維護")
    public ResponseTemplate<EmptyDto> updateBaseInfo(@Valid
    @RequestBody
    RequestTemplate<CTNBASIFT001Tranrq> req, Errors err) throws Exception {
        validateRequest(err);
        return theCTNBASIFT001Svc.updateBaseInfo(req);
    }

    /**
     * LIP-B-CTNCINPTT001 進件輸入維護
     *
     * @param req
     * @param err
     * @return
     * @throws Exception
     */
    @PostMapping("/inputInfo/modify")
    @Operation(summary = "LIP-B-CTNCINPTT001 進件輸入維護")
    public ResponseTemplate<EmptyDto> inputInfoModify(@Valid
    @RequestBody
    RequestTemplate<CTNCINPTT001Tranrq> req, Errors err) throws Exception {
        validateRequest(err);
        return theCTNCINPTT001Svc.inputInfoModify(req);
    }

    /**
     * LIP-C-CTNIAPSET001 進件申請條件輸入送出
     *
     * @param req
     * @param err
     * @return
     * @throws Exception
     */
    @PostMapping("/applyInput/send")
    @Operation(summary = "LIP-C-CTNIAPSET001 進件申請條件輸入送出")
    public ResponseTemplate<EmptyDto> sendApplyInput(@Valid
    @RequestBody
    RequestTemplate<CTNIAPSET001Tranrq> req, Errors err) throws Exception {
        validateRequest(err);
        return theCTNIAPSET001Svc.sendApplyInput(req);
    }

    /**
     * LIP-B-CTNIAPSVT001 進件申請條件輸入儲存
     *
     * @param req
     * @param err
     * @return
     * @throws Exception
     */
    @PostMapping("/applyInput/save")
    @Operation(summary = "LIP-B-CTNIAPSVT001 進件申請條件輸入儲存")
    public ResponseTemplate<EmptyDto> saveApplyInput(@Valid
    @RequestBody
    RequestTemplate<CTNIAPSVT001Tranrq> req, Errors err) throws Exception {
        validateRequest(err);
        return theCTNIAPSVT001Svc.saveApplyInput(req);
    }

    /**
     * LIP-C-CTNINITCT001 新增起案(一般件)
     *
     * @param req
     * @param err
     * @return
     * @throws DataDuplicateException
     * @throws DataNotFoundException
     * @throws RestException
     * @throws IOException
     * @throws ClassNotFoundException
     */
    @PostMapping("/normal/initiate")
    @Operation(summary = "LIP-C-CTNINITCT001 新增起案(一般件)")
    public ResponseTemplate<EmptyDto> initiateNormalCase(@Valid
    @RequestBody
    RequestTemplate<CTNINITCT001Tranrq> req, Errors err) throws Exception {
        validateRequest(err);
        return theCTNINITCT001Svc.initiateNormalCase(req);
    }

    /**
     * LIP-C-CTNINITCT002 新增起案(重提複製件)
     *
     * @param req
     * @param err
     * @return
     * @throws Exception
     */
    @PostMapping("/copy/initiate")
    @Operation(summary = "LIP-C-CTNINITCT002 新增起案(重提複製件)")
    public ResponseTemplate<CTNINITCT002Tranrs> insertCaseResubmitting(@Valid
    @RequestBody
    RequestTemplate<CTNINITCT002Tranrq> req, Errors err) throws Exception {
        validateRequest(err);
        return theCTNINITCT002Svc.insertCaseResubmitting(req);
    }

    /**
     * LIP-B-CTNREJECT001 撤件維護
     *
     * @param req
     * @param err
     * @return
     * @throws DataNotFoundException
     * @throws RestException
     * @throws IOException
     * @throws Exception
     */
    @PostMapping("/reject/modify")
    @Operation(summary = "LIP-B-CTNREJECT001 撤件維護")
    public ResponseTemplate<EmptyDto> rejectModify(@Valid
    @RequestBody
    RequestTemplate<CTNREJECT001Tranrq> req, Errors err) throws Exception {
        validateRequest(err);
        return theCTNREJECT001Svc.rejectModify(req);
    }

    /**
     * LIP-B-CTNJCFINT001 維護財所清
     *
     * @param req
     * @param err
     * @return
     * @throws RestException
     */
    @PostMapping(value = "/jcic/modifyJcicFin", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @Operation(summary = "LIP-B-CTNJCFINT001 維護財所清")
    public ResponseTemplate<EmptyDto> modifyJcicFin(@Valid
    @RequestPart("RequestTemplate")
    RequestTemplate<CTNJCFINT001Tranrq> req, Errors err, @RequestPart(name = "File", required = false)
    MultipartFile file) throws Exception {
        validateRequest(err);
        return theCTNJCFINT001Svc.modifyJcicFin(req, file);
    }

    /* LIP-B-CTNJCFINT002 財所清重查
     *
     * @param req 請求資料
     * @param err 驗證錯誤
     * @return 回應資料
     * @throws Exception 處理失敗
     */
    @PostMapping(value = "/jcic/reSendJcicFin", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @Operation(summary = "LIP-B-CTNJCFINT002 財所清重查")
    public ResponseTemplate<EmptyDto> reSendJcicFin(@Valid
    @RequestBody
    RequestTemplate<CTNJCFINT002Tranrq> req, Errors err) throws Exception {
        validateRequest(err);
        return theCTNJCFINT002Svc.reSendJcicFin(req);
    }

}
```

**CTNCINPTT001Tranrq.java 輸入 DTO Java · 90 行**

lip-svc-cln-transaction/src/main/java/cub/lip/svc/cln/transaction/dto/ctn/CTNCINPTT001Tranrq.java

```java
package cub.lip.svc.cln.transaction.dto.ctn;

import java.io.Serializable;
import java.util.List;

import javax.validation.Valid;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.Size;

import com.fasterxml.jackson.annotation.JsonProperty;

import lombok.Data;

/**
 * LIP-B-CTNCINPTT001進件輸入維護
 * 上行/請求電文
 *
 * @author 00550352
 */
@Data
public class CTNCINPTT001Tranrq implements Serializable {

    private static final long serialVersionUID = 1L;

    /** 動作 */
    @NotBlank(message = "ActionType 不可為空")
    @Size(message = "ActionType 長度不得超過1", max = 1)
    @JsonProperty("ActionType")
    private String actionType;

    /** 受理編號 */
    @NotBlank(message = "ApplyId 不可為空")
    @Size(message = "ApplyId 長度不得超過16", max = 16)
    @JsonProperty("ApplyId")
    private String applyId;

    /** 貸款類別 */
    @Size(message = "LoanType 長度不得超過1", max = 1)
    @JsonProperty("LoanType")
    private String loanType;

    /** 擔保種類 */
    @Size(message = "GageType 長度不得超過1", max = 1)
    @JsonProperty("GageType")
    private String gageType;

    /** 借款人姓名 */
    @Size(message = "BorrowName 長度不得超過120", max = 120)
    @JsonProperty("BorrowName")
    private String borrowName;

    /** 重提原因 */
    @Size(message = "ReapplyReason 長度不得超過60", max = 60)
    @JsonProperty("ReapplyReason")
    private String reapplyReason;

    /** 借保人清單 */
    @Valid
    @JsonProperty("BorGuarList")
    private List<CTNCINPTT001TranrqBorGuar> borGuarList;

    /** 進件單位資訊*/
    @Valid
    @JsonProperty("InputBranchInfo")
    private CTNCINPTT001TranrqInputBranchInfo inputBranchInfo;

    /** 使用者員編 */
    @Size(message = "EmpId 長度不得超過10", max = 10)
    @JsonProperty("EmpId")
    private String empId;

    /** 使用者單位代碼 */
    @Size(message = "BranchId 長度不得超過5", max = 5)
    @JsonProperty("BranchId")
    private String branchId;

    /** 使用者角色 */
    @JsonProperty("UserRole")
    private String userRole;

    /** 使用者名稱 */
    @JsonProperty("UserName")
    private String userName;

    /** 是否為直效單位 Y/N */
    @Size(message = "IsEffectBranch 長度不得超過1", max = 1)
    @JsonProperty("IsEffectBranch")
    private String isEffectBranch;

}
```

**CaseCheck.java 業務檢核 Java · 823 行**

lip-svc-cln-transaction/src/main/java/cub/lip/svc/cln/transaction/check/CaseCheck.java

```java
package cub.lip.svc.cln.transaction.check;

import java.io.IOException;
import java.math.BigDecimal;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Collectors;

import org.apache.commons.collections4.CollectionUtils;
import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import cub.lip.lib.cln.common.base.dto.BaseRateVO;
import cub.lip.lib.cln.common.base.dto.CodeOptionItem;
import cub.lip.lib.cln.common.enums.ClnBranchType;
import cub.lip.lib.cln.common.util.BaseRateUtil;
import cub.lip.lib.cln.common.util.BusinessUtil;
import cub.lip.lib.cln.common.util.CommCodeUtil;
import cub.lip.lib.cln.common.validator.Validator;
import cub.lip.lib.common.dto.base.MwHeaderResponse;
import cub.lip.lib.common.dto.base.RequestTemplate;
import cub.lip.lib.common.dto.base.ResponseTemplate;
import cub.lip.lib.common.enums.CommonBranchDeptMappingType;
import cub.lip.lib.common.exception.DataNotFoundException;
import cub.lip.lib.common.exception.ModuleException;
import cub.lip.lib.common.exception.RestException;
import cub.lip.lib.common.util.cache.BranchTypeUtil;
import cub.lip.lib.common.util.cache.RoleGroupUtil;
import cub.lip.lib.common.util.common.OrikaMapperUtil;
import cub.lip.lib.common.util.resttemplate.RestTemplateHelper;
import cub.lip.lib.common.util.sql.SqlAction;
import cub.lip.lib.common.util.sql.SqlUtils;
import cub.lip.lib.common.util.transfer.NormalRequestFactory;
import cub.lip.svc.cln.transaction.dto.ccm.CCMCANDOQ001Tranrq;
import cub.lip.svc.cln.transaction.dto.ccm.CCMCANDOQ001Tranrs;
import cub.lip.svc.cln.transaction.dto.ccm.CCMCINTRQ001Tranrq;
import cub.lip.svc.cln.transaction.dto.ccm.CCMCINTRQ001Tranrs;
import cub.lip.svc.cln.transaction.dto.ccm.CCMCINTRQ001TranrsCustomerInfo;
import cub.lip.svc.cln.transaction.dto.chu.CHUBSCIF001Tranrq;
import cub.lip.svc.cln.transaction.dto.chu.CHUBSCIF001Tranrs;
import cub.lip.svc.cln.transaction.dto.ctn.CTNCINPTT001Tranrq;
import cub.lip.svc.cln.transaction.dto.imp.IMGSTATUSO001Tranrq;
import cub.lip.svc.cln.transaction.dto.imp.IMGSTATUSO001Tranrs;
import cub.lip.svc.cln.transaction.entity.cln.ClnApplyDetailEntity;
import cub.lip.svc.cln.transaction.entity.cln.ClnApplyMainEntity;
import cub.lip.svc.cln.transaction.entity.cln.ClnApplyMainPKEntity;
import cub.lip.svc.cln.transaction.entity.cln.ClnCaseMainEntity;
import cub.lip.svc.cln.transaction.entity.cln.ClnCollDetailEntity;
import cub.lip.svc.cln.transaction.entity.cln.ClnCustomerGuarantorEntity;
import cub.lip.svc.cln.transaction.entity.cln.ClnCustomerGuarantorPKEntity;
import cub.lip.svc.cln.transaction.entity.cln.ClnCustomerInfoEntity;
import cub.lip.svc.cln.transaction.entity.cln.ClnSupplementEntity;
import cub.lip.svc.cln.transaction.repo.ClnApplyDetailRepository;
import cub.lip.svc.cln.transaction.repo.ClnApplyMainRepository;
import cub.lip.svc.cln.transaction.repo.ClnApplyRateRepository;
import cub.lip.svc.cln.transaction.repo.ClnAttachmentRepository;
import cub.lip.svc.cln.transaction.repo.ClnBaseRateRepository;
import cub.lip.svc.cln.transaction.repo.ClnCaseMainRepository;
import cub.lip.svc.cln.transaction.repo.ClnCollDetailRepository;
import cub.lip.svc.cln.transaction.repo.ClnCustomerGuarantorRepository;
import cub.lip.svc.cln.transaction.repo.ClnCustomerInfoRepository;
import cub.lip.svc.cln.transaction.repo.ClnFinMainRepository;
import cub.lip.svc.cln.transaction.repo.ClnSupplementRepository;
import cub.lip.svc.cln.transaction.vo.CaseCheckVO;
import cub.lip.svc.cln.transaction.vo.CheckApplySaveVO;
import cub.lip.svc.cln.transaction.vo.ClnBaseRateVO;
import cub.lip.svc.cln.transaction.vo.ClnCustIntraVO;
import cub.lip.svc.cln.transaction.vo.ProductCheckVO;

/**
 * CaseCheck 檢核
 */
@Component
public class CaseCheck {

    /** NormalRequestFactory */
    @Autowired
    private NormalRequestFactory normalReqFactory;

    /** RestTemplateHelper */
    @Autowired
    private RestTemplateHelper restTempHelper;

    /** Validator */
    @Autowired
    private Validator validator;

    /** CommCodeUtil */
    @Autowired
    private CommCodeUtil commCodeUtil;

    /** BusinessUtil */
    @Autowired
    private BusinessUtil businessUtil;

    /** BranchTypeUtil */
    @Autowired
    private BranchTypeUtil branchTypeUtil;

    /** RoleGroupUtil */
    @Autowired
    private RoleGroupUtil roleGroupUtil;

    /** OrikaMapperUtil */
    @Autowired
    private OrikaMapperUtil orikaMapper;

    /** ClnCaseMainRepository */
    @Autowired
    private ClnCaseMainRepository clnCaseMainRepository;

    /** ClnSupplementRepository */
    @Autowired
    private ClnSupplementRepository clnSupplementRepository;

    /** ClnCustomerInfoRepository */
    @Autowired
    private ClnCustomerInfoRepository clnCustomerInfoRepository;

    /** ClnCollDetailRepository */
    @Autowired
    private ClnCollDetailRepository clnCollDetailRepository;

    /** ClnCustomerGuarantorRepository */
    @Autowired
    private ClnCustomerGuarantorRepository clnCustomerGuarantorRepository;

    /** ClnAttachmentRepository */
    @Autowired
    private ClnAttachmentRepository clnAttachmentRepository;

    /** ClnApplyMainRepository */
    @Autowired
    private ClnApplyMainRepository clnApplyMainRepository;

    /** ClnApplyDetailRepository */
    @Autowired
    private ClnApplyDetailRepository clnApplyDetailRepository;

    /** ClnApplyRateRepository */
    @Autowired
    private ClnApplyRateRepository clnApplyRateRepository;

    /** ClnBaseRateRepository */
    @Autowired
    private ClnBaseRateRepository clnBaseRateRepository;

    /** ClnFinMainRepository */
    @Autowired
    private ClnFinMainRepository clnFinMainRepository;

    /** ProductCheck */
    @Autowired
    private ProductCheck productCheck;

    /** BaseRateUtil */
    @Autowired
    private BaseRateUtil baseRateUtil;

    /** SqlAction */
    @Autowired
    private SqlAction sqlAction;

    /** SqlUtils */
    @Autowired
    private SqlUtils sqlUtils;

    /** CTNIAPSET001_QUERY_001 */
    private static final String CTNIAPSET001_QUERY_001 = "CTNIAPSET001_query_001.sql";

    /** CASE_CHECK_APPLY_SUBMIT_QUERY_001 */
    private static final String CASE_CHECK_APPLY_SUBMIT_QUERY_001 = "CaseCheck.checkApplySubmit_query_001.sql";

    /** CASE_CHECK_APPLY_SUBMIT_QUERY_002 */
    private static final String CASE_CHECK_APPLY_SUBMIT_QUERY_002 = "CaseCheck.checkApplySubmit_query_002.sql";

    /**
     * checkInputSave
     * 
     * @param <T>
     * @param oriReq
     * @param clnCaseMain
     * @param caseCheckVO
     * @throws Exception
     */
    public <T> void checkInputSave(RequestTemplate<T> oriReq, ClnCaseMainEntity clnCaseMain, CaseCheckVO caseCheckVO) throws Exception {

        // 1.檢核績效行是否為區部所屬子行
        String initBranch = StringUtils.equalsAny(caseCheckVO.getLoanType(), "1", "2") ? caseCheckVO.getAgentBranch()
                : caseCheckVO.getRemitBranchId();

        String isIntroLegal = businessUtil.checkIntroBranch(oriReq, caseCheckVO.getIntroBranchId(), initBranch, caseCheckVO.getBranchId());

        // 2.檢核招攬人角色是否為A0-001(經手人) or B1-001(PS授信人員) or A0-002(招攬人員)
        boolean hasPermission = roleGroupUtil.hasPermissionByEmpId("CLN", "cln-case-input-info:save", caseCheckVO.getAgentId());
        String isAgent = hasPermission ? "Y" : "N";

        // 3.查詢是否有權限承作本案
        CCMCANDOQ001Tranrq ccmTranrq = orikaMapper.map(caseCheckVO, CCMCANDOQ001Tranrq.class);
        ccmTranrq.setUserRole(caseCheckVO.getUserRole());
        String canDoCase = getCanDoCase(oriReq, ccmTranrq);

        // 4.貸款中心案件招攬行需為貸中對應之PS區部
        String isAgentBranchRight = "Y";
        if (StringUtils.equals("82400", clnCaseMain.getInputBranch())) {
            List<CodeOptionItem> itemList = commCodeUtil.getAllComnCodes("LOAN_CENTER_MAPPING", caseCheckVO.getAgentBranch());
            if (CollectionUtils.isEmpty(itemList)) {
                isAgentBranchRight = "N";
            }
        }

        // 5.帳務行是否存在清單中
        boolean hasRemitBranch = branchTypeUtil
                .getBranchIdByFullComplianceBranchTypes(CommonBranchDeptMappingType.CLN, ClnBranchType.REMIT_BRANCH)
                .contains(caseCheckVO.getRemitBranchId());
        String remitBranchIsvalid = hasRemitBranch ? "Y" : "N";

        // 6.對保行是否存在清單中
        boolean hasGuarantorBranch = branchTypeUtil
                .getBranchIdByFullComplianceBranchTypes(CommonBranchDeptMappingType.CLN, ClnBranchType.GUARANTOR_BRANCH)
                .contains(caseCheckVO.getGuarantorBranch());
        String guarantorBranchIsvalid = hasGuarantorBranch ? "Y" : "N";

        // 7.建立檢核map(@CheckMap)
        Map<String, String> checkMap = new HashMap<>();
        checkMap.put("IS_INTRO_LEGAL", isIntroLegal);
        checkMap.put("IS_AGENT", isAgent);
        checkMap.put("CAN_DO_CASE", canDoCase);
        checkMap.put("APPLY_PROCESS", clnCaseMain.getApplyProcess());
        checkMap.put("INPUT_BRANCH", clnCaseMain.getInputBranch());
        checkMap.put("IS_AGENT_BRANCH_RIGHT", isAgentBranchRight);
        checkMap.put("REMIT_BRANCH_ISVALID", remitBranchIsvalid);
        checkMap.put("GUARANTOR_BRANCH_ISVALID", guarantorBranchIsvalid);

        // 9.執行規則檢核
        String errMsg = validator.executeRuleForMsg("DSA0A3", checkMap);
        if (StringUtils.isNotBlank(errMsg)) {
            throw new ModuleException(errMsg);
        }
    }

    /**
     * checkInputDelete
     * 
     * @param oriReq
     * @param clnCaseMain
     * @param caseCheckVO
     * @param <T>
     * @throws Exception
     */
    public <T> void checkInputDelete(RequestTemplate<T> oriReq, ClnCaseMainEntity clnCaseMain) throws Exception {

        // 1.若在登打流程(掃描受理)需打電文查詢案件狀態
        String applyProcess = clnCaseMain.getApplyProcess();
        String imgStatus = "1";
        CTNCINPTT001Tranrq tranrq = (CTNCINPTT001Tranrq) oriReq.getTranrq();
        if (StringUtils.equals("6", applyProcess)) {
            // A.發查電文【IMP-B-IMGSTATUSO001 影像案件狀態查詢】
            IMGSTATUSO001Tranrq imgTranrq = new IMGSTATUSO001Tranrq();
            imgTranrq.setProduct("CLN");
            imgTranrq.setCaseNo(tranrq.getApplyId());
            imgTranrq.setUserId(tranrq.getEmpId());
            imgTranrq.setUserName(tranrq.getUserName());
            imgTranrq.setDepartment(tranrq.getBranchId());

            ResponseTemplate<IMGSTATUSO001Tranrs> imgRes = restTempHelper.postForEntity(
                normalReqFactory.genRequestTemplate(oriReq, imgTranrq, "IMP-B-IMGSTATUSO001"), IMGSTATUSO001Tranrs.class);

            MwHeaderResponse mwHeader = imgRes.getMwHeaderResponse();
            if (!StringUtils.equals("0000", mwHeader.getReturnCode())) {
                throw new RestException(mwHeader);
            }

            imgStatus = imgRes.getTranrs().getCode();
        }

        // 2.查詢是否有權限承作本案
        CCMCANDOQ001Tranrq ccmTranrq = orikaMapper.map(tranrq, CCMCANDOQ001Tranrq.class);
        ccmTranrq.setUserRole(tranrq.getUserRole());
        String canDoCase = getCanDoCase(oriReq, ccmTranrq);

        // 3.建立檢核map(@CheckMap)
        Map<String, String> checkMap = new HashMap<>();
        checkMap.put("APPLY_PROCESS", applyProcess);
        checkMap.put("IS_ONLINE_APPLY", clnCaseMain.getIsOnlineApply());
        checkMap.put("IMG_STATUS", imgStatus);
        checkMap.put("INTRA_JCIC_IS_EXIST", StringUtils.equals("1", clnCaseMain.getIsSendJcic()) ? "Y" : "N");
        checkMap.put("CAN_DO_CASE", canDoCase);

        // 9.執行規則檢核
        String errMsg = validator.executeRuleForMsg("DSA0A4", checkMap);
        if (StringUtils.isNotBlank(errMsg)) {
            throw new ModuleException(errMsg);
        }
    }

    /**
     * checkApplySave
     *
     * @param checkApplySaveVO
     * @param productCheckVOList
     * @param requestTemplate
     * @param <T>
     * @throws Exception
     */
    public <T> void checkApplySave(CheckApplySaveVO checkApplySaveVO, List<ProductCheckVO> productCheckVOList,
            RequestTemplate<T> requestTemplate) throws Exception {

        ClnCaseMainEntity clnCaseMainEntity = clnCaseMainRepository.findById(checkApplySaveVO.getApplyId())
                .orElseThrow(() -> new DataNotFoundException("CLN_CASE_MAIN查無資料"));

        List<Integer> supplyId = Arrays.asList(98, 102);

        List<ClnSupplementEntity> clnSupplementEntity = clnSupplementRepository
                .findByApplyIdAndIsAgreeAndSupplyIdInAndFinishIdIsNull(checkApplySaveVO.getApplyId(), "0", supplyId);

        String hasSupplyment = CollectionUtils.isEmpty(clnSupplementEntity) ? "N" : "Y";

        /** 4. 借款用途是否為消費性支出或其他(@Has451458) */
        String has451458 = productCheck.checkHas451458(productCheckVOList);

        /** 5. 所屬單位可否承作本案 */

        if (StringUtils.isBlank(clnCaseMainEntity.getInputBranch())) {
            throw new ModuleException("進行件不得為空");
        }

        List<String> roleList = Arrays.stream(checkApplySaveVO.getUserRole().split(",")).map(String::trim).collect(Collectors.toList());

        String canDoCase = "N";
        if (roleList.contains("A0-003")) { // TODO批次服務判斷未完成
            canDoCase = "Y";
        } else if (roleList.contains("D0-001") || roleList.contains("B1-001") || roleList.contains("A0-001")) {

            // 呼叫【LIP-B-CCMCANDOQ001 查詢是否有權限承作本案】
            CCMCANDOQ001Tranrq ccmcandoq001Tranrq = new CCMCANDOQ001Tranrq();
            ccmcandoq001Tranrq.setApplyId(checkApplySaveVO.getApplyId());
            ccmcandoq001Tranrq.setUserRole(checkApplySaveVO.getUserRole());
            ccmcandoq001Tranrq.setBranchId(checkApplySaveVO.getBranchId());

            ResponseTemplate<CCMCANDOQ001Tranrs> response = restTempHelper.postForEntity(
                normalReqFactory.genRequestTemplate(requestTemplate, ccmcandoq001Tranrq, "LIP-B-CCMCANDOQ001"), CCMCANDOQ001Tranrs.class);

            MwHeaderResponse headerResponse = response.getMwHeaderResponse();
            if (!"0000".equals(headerResponse.getReturnCode())) {
                throw new RestException(headerResponse);
            }
            canDoCase = response.getTranrs().getCanDoCase();
        }

        /** 6. 循環理財貸款(WMA)不得勾選提前清償違約金 */
        // TODO

        /** 7. 檢核帳務管理費 */

        List<CodeOptionItem> rcamt = commCodeUtil.getAllComnCodes("ACNT_FEE_RCAMT", "0");
        String overAcntFee = new BigDecimal(checkApplySaveVO.getAcntFeeRvAmt()).compareTo(new BigDecimal(rcamt.get(0).getCodeName())) > 0
                ? "Y"
                : "N";

        /** 8. 擔保品為特金，承作方式借款幣別是否只能有一種外幣幣別(@CheckCurrency) */

        String checkCurrency = productCheck.checkMCurrency(checkApplySaveVO.getGageType(), productCheckVOList);

        /** 9. 取得HAS_LOAN_POS_NOTE */

        String hasLoanPosNote = StringUtils.isNotBlank(checkApplySaveVO.getLoanPosNote()) ? "Y" : "N";

        Map<String, String> applyFormRelationCheckMap = productCheck.checkApplyFormRelation(checkApplySaveVO.getGageType(),
            productCheckVOList, checkApplySaveVO.getSelectedCollateralApplyFormList());

        /** 10. 建立檢核map(@CheckMap) */

        Map<String, String> checkMap = new HashMap<>();
        checkMap.put("CAN_DO_CASE", canDoCase);
        // TODO checkMap.put("NO_HAS_PAYOFF", applyId);
        checkMap.put("CURRENCY_CHECK", checkCurrency);
        checkMap.put("OVER_ACNT_FEE", overAcntFee);
        checkMap.put("HAS_451_458", has451458);
        checkMap.put("HAS_LOAN_POS_NOTE", hasLoanPosNote);
        checkMap.put("HAS_SUPPLYMENT", hasSupplyment);
        checkMap.put("APPLY_PROCESS", clnCaseMainEntity.getApplyProcess());
        checkMap.putAll(applyFormRelationCheckMap);

        /** 11. 執行規則檢核 */
        String errMsg = validator.executeRuleForMsg("DSA0AA", checkMap);

        if (StringUtils.isNotBlank(errMsg)) {
            throw new ModuleException(errMsg);
        }
    }

    /**
     * checkAMLType12
     *
     * @param req
     * @param caseCheckVO
     * @param <T>
     * @throws ModuleException
     * @throws IOException
     */
    public <T> void checkAMLType12(RequestTemplate<T> req, CaseCheckVO caseCheckVO) throws ModuleException, IOException {

        String isAMLPrcheck = commCodeUtil.getAllComnCodes("AML_PRCHECK", "IS_AML_PRCHECK").stream().findFirst()
                .map(CodeOptionItem::getCodeName).orElse("N");

        if (StringUtils.isNotBlank(isAMLPrcheck) && "Y".equals(isAMLPrcheck)) {
            Map<String, Object> prcheckMap = new HashMap<>();
            prcheckMap.put("ApplyId", caseCheckVO.getApplyId());

            // 保留發查後有查到的值，並做後續的動作
            List<ClnCustomerInfoEntity> resultList = sqlAction.queryForList(sqlUtils.getQuerySql(CTNIAPSET001_QUERY_001), prcheckMap,
                ClnCustomerInfoEntity.class);

            if (CollectionUtils.isNotEmpty(resultList)) {
                // 組成用逗號分隔的 customerId
                String refuseId = resultList.stream().map(customer -> {

                    // 組上行
                    CHUBSCIF001Tranrq chubscif001Tranrq = CHUBSCIF001Tranrq.builder().branch(caseCheckVO.getBranchId())
                            .userId(caseCheckVO.getUserId()).customerId(customer.getCustomerId()).idType(customer.getIdType()).build();

                    // 發查【CUS-B-CHUBSCIF001 CIF資料查詢服務】
                    ResponseTemplate<CHUBSCIF001Tranrs> response = restTempHelper.postForEntity(
                        normalReqFactory.genRequestTemplate(req, chubscif001Tranrq, "CUS-B-CHUBSCIF001"), CHUBSCIF001Tranrs.class);

                    // 取出每筆的 customerId
                    return ("S0000000".equals(response.getMwHeaderResponse().getReturnCode())
                            && StringUtils.isNotBlank(response.getTranrs().getPrChkFlg())) ? customer.getCustomerId() : null;

                }).filter(Objects::nonNull).collect(Collectors.joining(","));

                if (StringUtils.isNotBlank(refuseId)) {
                    throw new ModuleException("ID:" + refuseId + "為定審/EDD不配合客戶，無法提交。");
                }
            }
        }
    }

    /**
     * checkApplySubmit
     *
     * @param req
     * @param caseCheckVO
     * @param <T>
     * @throws Exception
     */
    public <T> void checkApplySubmit(RequestTemplate<T> req, CaseCheckVO caseCheckVO) throws Exception {

        String applyId = caseCheckVO.getApplyId();

        // ----------1.查詢CLN_CASE_MAIN------------------
        ClnCaseMainEntity clnCaseMainEntity = clnCaseMainRepository.findById(applyId)
                .orElseThrow(() -> new DataNotFoundException("CLN_CASE_MAIN 查無資料"));

        // ----------2.所屬單位可否承作本案------------------
        String canDoCase = checkApplySubmitCanDoCase(req, caseCheckVO, clnCaseMainEntity);

        // ----------3.提交AML檢核(做成public方法：CaseCheck.checkAMLType12())------------------
        checkAMLType12(req, caseCheckVO);

        // ----------4.檢核借保人------------------
        String chkCustomer;
        String consistentFlag = "Y";
        String chkCustGuar = "Y";

        // 查詢 ClnCustomerInfoList
        List<ClnCustomerInfoEntity> clnCustomerInfoList = clnCustomerInfoRepository.findByApplyIdOrderByCustomerId(applyId);

        // 查詢 ClnCollDetailList
        List<ClnCollDetailEntity> clnCollDetailList = clnCollDetailRepository.findByApplyIdOrderByApplyId(applyId);

        // GageOwnerList
        List<ClnCustomerInfoEntity> gageOwnerList = clnCustomerInfoList.stream().filter(gageOwner -> "1".equals(gageOwner.getIsGageOwner()))
                .collect(Collectors.toList());

        // 1. 活定存單,比對 @GageOwnerList的CustomerId 和 @ClnCollDetailList中的ProviderId

        if ("D".equals(caseCheckVO.getGageType())) {
            List<String> gageOwnerIdList = gageOwnerList.stream().map(ClnCustomerInfoEntity::getCustomerId).collect(Collectors.toList());
            List<String> providerIdList = clnCollDetailList.stream().map(ClnCollDetailEntity::getProviderId).collect(Collectors.toList());
            boolean hasInconsistent = gageOwnerIdList.stream().anyMatch(customerId -> !providerIdList.contains(customerId))
                    || providerIdList.stream().anyMatch(providerId -> !gageOwnerIdList.contains(providerId));
            consistentFlag = hasInconsistent ? "N" : "Y";
        }

        // 2. 比對ClnCustomerInfoList的checkCustInfo，是否有一個不為"1"
        chkCustomer = clnCustomerInfoList.stream().map(ClnCustomerInfoEntity::getCheckCustInfo).anyMatch(custInfo -> !"1".equals(custInfo))
                ? "N"
                : "Y";

        // 查詢 ClnCustomerGuarantorList
        chkCustGuar = checkApplySubmitChkCustGuar(clnCustomerInfoList, caseCheckVO);

        // ----------5.檢核附件掛檔------------------

        String attachmentIsEmpty = clnAttachmentRepository.findByApplyIdAndFileKind(applyId, "27").isEmpty() ? "Y" : "N";

        // ----------6.規則檢核參數 @HasSubmitRecord & @HasNoGuar & @IsChgBaserate------------------

        // 是否有送件紀錄 (ApplyMain + ApplyDetail + ApplyRate)
        // (1)判斷是否有 CLN_APPLY_MAIN
        boolean hasMain = !clnApplyMainRepository.findByApplyId(applyId).isEmpty();

        List<ClnApplyDetailEntity> detailList = clnApplyDetailRepository.findByApplyIdAndType(applyId, "I");
        boolean hasDetail = !detailList.isEmpty();

        // 是否有保證人
        String hasNoGuar = detailList.stream().anyMatch(detail -> "2".equals(detail.getHasGuar())) ? "Y" : "N";

        Map<String, Object> rateParamMap = new HashMap<>();
        rateParamMap.put("ApplyId", applyId);
        List<ClnBaseRateVO> rateList = sqlAction.queryForListVO(sqlUtils.getQuerySql(CASE_CHECK_APPLY_SUBMIT_QUERY_001), rateParamMap,
            ClnBaseRateVO.class, false);
        boolean hasRate = !rateList.isEmpty();

        // 最後綜合判斷送件紀錄
        String hasSubmitRecord = (hasMain && hasDetail && hasRate) ? "Y" : "N";

        // 取得指標利率清單
        List<BaseRateVO> baseRateList = baseRateUtil.queryBaseRateList();
        String isChgBaserate = "N";
        for (ClnBaseRateVO rate : rateList) {
            String baseCode = rate.getBaseCode();
            if ("1".equals(baseCode) || "2".equals(baseCode) || "3".equals(baseCode)) {
                // 1.取得BASE_CODE_MAPPING對應的codeName，比對BaseInterest是否和BaseRateValue相同
                List<CodeOptionItem> mappingList = commCodeUtil.getAllComnCodes("BASE_CODE_MAPPING", baseCode);
                if (CollectionUtils.isNotEmpty(mappingList)) {
                    String codeName = mappingList.get(0).getCodeName();
                    boolean changed = baseRateList.stream().filter(br -> codeName.equals(br.getRateDataCode()))
                            .anyMatch(br -> !StringUtils.equals(rate.getBaseInterest(), br.getBaseRateValue()));
                    if (changed) {
                        isChgBaserate = "Y";
                        break;
                    }
                }
            } else if ("6".equals(baseCode)) {
                // 2.比對CurrencyCode=RateDataCcy的資料，BaseInterest是否和BaseRateValue相同
                boolean changed = baseRateList.stream().filter(br -> rate.getCurrencyCode().equals(br.getRateDataCcy()))
                        .anyMatch(br -> !StringUtils.equals(rate.getBaseInterest(), br.getBaseRateValue()));
                if (changed) {
                    isChgBaserate = "Y";
                    break;
                }
            }
        }

        // TODO ----------7.規則檢核參數: @HasSubmitIntra----------

        // TODO ----------8.規則檢核參數: 是否為PS/貸中 @IsCenter----------

        // TODO ----------9.規則檢核參數: 若@CLN_CIA_INTRA查詢有資料，判斷利害關係人----------

        // ----------10.規則檢核參數 @IsGageOwner------------------
        String isGageOwner = gageOwnerList.isEmpty() ? "N" : "Y";

        // 11.規則檢核參數: 利害關係人總金額檢核，傳入@TotalAmt----------
        String borrAmtIsvalid = "Y";
        String comborrAmtIsvalid = "Y";
        Map<String, Object> custParamMap = new HashMap<>();
        custParamMap.put("ApplyId", applyId);
        List<ClnCustIntraVO> custIntraList = sqlAction.queryForListVO(sqlUtils.getQuerySql(CASE_CHECK_APPLY_SUBMIT_QUERY_002), custParamMap,
            ClnCustIntraVO.class, false);

        BigDecimal totalAmt = detailList.stream().map(detail -> Optional.ofNullable(detail.getLoanAmt()).orElse(BigDecimal.ZERO))
                .reduce(BigDecimal.ZERO, BigDecimal::add);

        if (totalAmt.compareTo(new BigDecimal("100000000")) >= 0) {
            for (ClnCustIntraVO custIntra : custIntraList) {
                if ("0".equals(custIntra.getCustomerType())
                        && ("Y".equals(custIntra.getBankRelFlag()) || "Y".equals(custIntra.getHodRelFlag44()))) {
                    borrAmtIsvalid = "N";
                }
                if ("1".equals(custIntra.getCustomerType())
                        && ("Y".equals(custIntra.getBankRelFlag()) || "Y".equals(custIntra.getHodRelFlag44()))) {
                    comborrAmtIsvalid = "N";
                }
            }
        }

        // ----------12.規則檢核參數: @J001NoConfirm------------------
        String j001NoConfirm = clnFinMainRepository.findByApplyIdAndIsValid(applyId, "1").stream()
                .anyMatch(clnFinMain -> "1".equals(clnFinMain.getStatus())) ? "Y" : "N";

        // ----------13.處理 HASNOGUAR_ISREL(檢核Map要用的)-----------------
        String hasNoGuarIsRel = "N";
        CCMCINTRQ001Tranrq ccmcintrq001Tranrq = new CCMCINTRQ001Tranrq();
        ccmcintrq001Tranrq.setApplyId(applyId);
        ResponseTemplate<CCMCINTRQ001Tranrs> responseTemplate = restTempHelper.postForEntity(
            normalReqFactory.genRequestTemplate(req, ccmcintrq001Tranrq, "LIP-B-CCMCINTRQ001"), CCMCINTRQ001Tranrs.class);
        MwHeaderResponse mwHeaderResponse = responseTemplate.getMwHeaderResponse();
        // 檢核時，有可能還未送一鍵查詢，查無資料視為正常
        if ("0000".equals(mwHeaderResponse.getReturnCode()) && responseTemplate.getTranrs() != null) {
            if (responseTemplate.getTranrs().getCustomerInfo() != null) {
                CCMCINTRQ001TranrsCustomerInfo customerInfo = responseTemplate.getTranrs().getCustomerInfo();
                // 判斷hasNoGuar : 比較borrorcomborrBankRelFlag、borrorcomborrHodRelFlag44
                if (("Y".equals(customerInfo.getBorrorcomborrBankRelFlag()) || "Y".equals(customerInfo.getBorrorcomborrHodRelFlag44()))
                        && "Y".equals(hasNoGuar)) {
                    hasNoGuarIsRel = "Y";
                }
            }
        }

        // ----------14.建立一個檢核Map------------------
        Map<String, String> checkMap = new HashMap<>();
        checkMap.put("CAN_DO_CASE", canDoCase);
        checkMap.put("APPLY_PROCESS", clnCaseMainEntity.getApplyProcess());
        checkMap.put("HAS_SUBMIT_RECORD", hasSubmitRecord);
        checkMap.put("IS_SEND_IMG", clnCaseMainEntity.getIsSendImg());
        checkMap.put("HASNOGUAR_ISREL", hasNoGuarIsRel);
        checkMap.put("IS_CHG_BASERATE", isChgBaserate);
        checkMap.put("IS_GAGE_OWNER", isGageOwner);
        checkMap.put("IS_CHECK_KYC", Optional.ofNullable(clnCaseMainEntity.getContCredNote())
                .filter(caseMain -> caseMain.contains("本案未完成KYC")).map(caseMain -> "N").orElse("Y"));
        checkMap.put("BORR_AMT_ISVALID", borrAmtIsvalid);
        checkMap.put("COMBORR_AMT_ISVALID", comborrAmtIsvalid);
        checkMap.put("J001NoConfirm", j001NoConfirm);
        checkMap.put("CONSISTENT_FLAG", consistentFlag);
        checkMap.put("CHK_CUSTOMER", chkCustomer);
        checkMap.put("CHK_CUST_GUAR", chkCustGuar);
        checkMap.put("ATTACHMENT_EMPTY", attachmentIsEmpty);

        // ----------15.執行規則檢核------------------
        String errMsg = validator.executeRuleForMsg("DSA0A8", checkMap);
        if (StringUtils.isNotBlank(errMsg)) {
            throw new ModuleException(errMsg);
        }

    }

    /**
     * checkApplySubmit 檢核canDoCase
     * 
     * @param req
     * @param caseCheckVO
     * @param clnCaseMainEntity
     * @return
     * @param <T>
     * @throws RestException
     * @throws ModuleException
     */
    private <T> String checkApplySubmitCanDoCase(RequestTemplate<T> req, CaseCheckVO caseCheckVO, ClnCaseMainEntity clnCaseMainEntity)
            throws RestException, ModuleException {

        if (StringUtils.isBlank(clnCaseMainEntity.getInputBranch())) {
            throw new ModuleException("進行件不得為空");
        }

        String userRole = caseCheckVO.getUserRole();
        String canDoCase = "N";
        if ("A0-003".equals(userRole)) {
            canDoCase = "Y";
        }

        if (userRole.contains("D0-001") || userRole.contains("B1-001") || userRole.contains("A0-001")) {
            CCMCANDOQ001Tranrq ccmcandoq001Tranrq = CCMCANDOQ001Tranrq.builder().applyId(caseCheckVO.getApplyId())
                    .userRole(caseCheckVO.getUserRole()).branchId(caseCheckVO.getBranchId()).build();
            canDoCase = getCanDoCase(req, ccmcandoq001Tranrq);
        }

        return canDoCase;
    }

    /**
     * checkApplySubmit 檢核chkCustGuar
     *
     * @param clnCustomerInfoList
     * @param caseCheckVO
     * @return
     */
    private String checkApplySubmitChkCustGuar(List<ClnCustomerInfoEntity> clnCustomerInfoList, CaseCheckVO caseCheckVO) {

        return clnCustomerInfoList.stream().allMatch(customerInfo -> {

            // 取得ClnCustomerGuarantor
            ClnCustomerGuarantorEntity clnCustomerGuarantor = clnCustomerGuarantorRepository
                    .findById(new ClnCustomerGuarantorPKEntity(caseCheckVO.getApplyId(), customerInfo.getCustomerId())).orElse(null);

            // 3. 逐步比對 ClnCustomerInfoList 和 ClnCustomerGuarantor，任一項不符 CHK_CUST_GUAR = N
            return isCustomerGuarantorMatch(customerInfo, clnCustomerGuarantor);

        }) ? "Y" : "N";

    }

    /**
     * checkApplySubmit 檢核chkCustGuar : 判斷ClnCustomerInfoEntity、ClnCustomerGuarantorEntity的值是否match
     *
     * @param customerInfo
     * @param guarantor
     * @return
     */
    private boolean isCustomerGuarantorMatch(ClnCustomerInfoEntity customerInfo, ClnCustomerGuarantorEntity guarantor) {

        // 基本ID比對
        if (guarantor == null || !customerInfo.getCustomerId().equals(guarantor.getGuarId())) {
            return false;
        }
        // 基本姓名比對
        if (!Objects.equals(guarantor.getGuarName(), customerInfo.getCustomerName())) {
            return false;
        }
        // 根據 guarKind、isGageOwner 判斷
        if ("1".equals(customerInfo.getGuarKind()) && !"1".equals(guarantor.getGuarKind1())) {
            return false;
        }
        if ("2".equals(customerInfo.getGuarKind()) && !"1".equals(guarantor.getGuarKind2())) {
            return false;
        }
        if ("3".equals(customerInfo.getGuarKind()) && !"1".equals(guarantor.getGuarKind3())) {
            return false;
        }
        if ("3".equals(customerInfo.getIsGageOwner()) && !"1".equals(guarantor.getGuarKind4())) {
            return false;
        }
        if ("0".equals(customerInfo.getGuarKind()) && !"1".equals(guarantor.getGuarKind5())) {
            return false;
        }

        return true;
    }

    /**
     * checkReAquire
     * 
     * @param req
     * @param customerInfoList
     * @param customerGuarantorList
     * @param oldCaseMain
     * @param caseCheckVO
     * @param <T>
     * @throws Exception
     */
    public <T> void checkReAquire(RequestTemplate<T> req, List<ClnCustomerInfoEntity> customerInfoList,
            List<ClnCustomerGuarantorEntity> customerGuarantorList, ClnCaseMainEntity oldCaseMain, CaseCheckVO caseCheckVO)
            throws Exception {

        String customerIdCheck = "Y";

        // 2.本案無法重提/複製，請人工起案
        if (customerInfoList.size() != customerGuarantorList.size()) {
            customerIdCheck = "N";
        }

        if (CollectionUtils.isNotEmpty(customerInfoList)) {
            Set<String> guarIds = customerGuarantorList.stream().map(guar -> guar.getGuarId()).collect(Collectors.toSet());

            boolean allCustomersFound = customerInfoList.stream().allMatch(info -> guarIds.contains(info.getCustomerId()));

            if (!allCustomersFound) {
                customerIdCheck = "N";
            }
        }

        // 3.所屬單位無法承作本案(@CanDoCase)
        CCMCANDOQ001Tranrq ccmcandoq001Tranrq = CCMCANDOQ001Tranrq.builder().applyId(caseCheckVO.getBefApplyId())
                .userRole(String.join(",", caseCheckVO.getRoleList())).branchId(caseCheckVO.getUserBranch()).build();
        String canDoCase = getCanDoCase(req, ccmcandoq001Tranrq);

        Map<String, String> checkMap = new HashMap<>();
        checkMap.put("APPLY_PROCESS", oldCaseMain.getApplyProcess());
        checkMap.put("CAN_DO_CASE", canDoCase);
        checkMap.put("OLD_LOAN_TYPE", oldCaseMain.getLoanType());
        checkMap.put("LOAN_TYPE", caseCheckVO.getLoanType());
        checkMap.put("GAGE_TYPE", caseCheckVO.getGageType());
        checkMap.put("IS_END", clnApplyMainRepository.findById(new ClnApplyMainPKEntity(caseCheckVO.getBefApplyId(), "B"))
                .map(ClnApplyMainEntity::getIsEnd).orElse(""));
        checkMap.put("CASE_TYPE", caseCheckVO.getCaseType());
        checkMap.put("CUSTOMER_ID_CHECK", customerIdCheck);

        String errMsg = validator.executeRuleForMsg("DSA0A2", checkMap);
        if (StringUtils.isNotBlank(errMsg)) {
            throw new ModuleException(errMsg);
        }
    }

    /**
     * 發查【LIP-B-CCMCANDOQ001 查詢是否有權限承作本案】取得@canDoCase
     * 
     * @param <T>
     * @param oriReq
     * @param ccmTranrq
     * @return
     * @throws RestException
     */
    private <T> String getCanDoCase(RequestTemplate<T> oriReq, CCMCANDOQ001Tranrq ccmTranrq) throws RestException {

        ResponseTemplate<CCMCANDOQ001Tranrs> response = restTempHelper
                .postForEntity(normalReqFactory.genRequestTemplate(oriReq, ccmTranrq, "LIP-B-CCMCANDOQ001"), CCMCANDOQ001Tranrs.class);

        MwHeaderResponse headerResponse = response.getMwHeaderResponse();
        if (!"0000".equals(headerResponse.getReturnCode())) {
            throw new RestException(headerResponse);
        }

        return response.getTranrs().getCanDoCase();
    }

    /**
     * checkNormal
     * 
     * @param loanType
     * @param gageType
     * @throws Exception
     */
    public void checkNormal(String loanType, String gageType) throws Exception {
        Map<String, String> checkMap = new HashMap<>();
        checkMap.put("LOAN_TYPE", loanType);
        checkMap.put("GAGE_TYPE", gageType);

        String errMsg = validator.executeRuleForMsg("DSA0B4", checkMap);
        if (StringUtils.isNotBlank(errMsg)) {
            throw new ModuleException(errMsg);
        }
    }

}
```

**CTNCINPTT001SvcImpl.java 異動準備與流程編排 Java · 775 行**

lip-svc-cln-transaction/src/main/java/cub/lip/svc/cln/transaction/svc/impl/CTNCINPTT001SvcImpl.java

```java
package cub.lip.svc.cln.transaction.svc.impl;

import java.io.IOException;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.sql.Date;
import java.sql.Timestamp;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.function.Consumer;
import java.util.stream.Collectors;

import cub.lip.lib.common.dto.base.MwHeaderResponse;
import cub.lip.lib.common.exception.RestException;
import cub.lip.svc.cln.transaction.dto.msp.CHECKIDC001Tranrq;
import cub.lip.svc.cln.transaction.dto.msp.CHECKIDC001Tranrs;
import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import cub.lip.lib.cln.common.base.dto.DeptCodeList;
import cub.lip.lib.cln.common.util.CommonUtil;
import cub.lip.lib.common.dto.base.EmptyDto;
import cub.lip.lib.common.dto.base.RequestTemplate;
import cub.lip.lib.common.dto.base.ResponseTemplate;
import cub.lip.lib.common.exception.DataNotFoundException;
import cub.lip.lib.common.util.common.OrikaMapperUtil;
import cub.lip.lib.common.util.resttemplate.RestTemplateHelper;
import cub.lip.lib.common.util.transfer.NormalRequestFactory;
import cub.lip.lib.common.util.transfer.NormalResponseFactory;
import cub.lip.svc.cln.transaction.check.CaseCheck;
import cub.lip.svc.cln.transaction.dto.ccm.CCMINBRHQ001Tranrq;
import cub.lip.svc.cln.transaction.dto.ccm.CCMINBRHQ001Tranrs;
import cub.lip.svc.cln.transaction.dto.ctn.CTNCINPTT001Tranrq;
import cub.lip.svc.cln.transaction.dto.ctn.CTNCINPTT001TranrqBorGuar;
import cub.lip.svc.cln.transaction.dto.ctn.CTNCINPTT001TranrqInputBranchInfo;
import cub.lip.svc.cln.transaction.dto.fns.FNSCIF0000Tranrq;
import cub.lip.svc.cln.transaction.dto.fns.FNSCIF0000Tranrs;
import cub.lip.svc.cln.transaction.dto.wms.CUSTTYPEQ003Tranrq;
import cub.lip.svc.cln.transaction.dto.wms.CUSTTYPEQ003Tranrs;
import cub.lip.svc.cln.transaction.dto.wms.GETKYCSTATQ002Tranrq;
import cub.lip.svc.cln.transaction.dto.wms.GETKYCSTATQ002Tranrs;
import cub.lip.svc.cln.transaction.entity.base.ClnCaseHistoryEntity;
import cub.lip.svc.cln.transaction.entity.cln.ClnCaseMainEntity;
import cub.lip.svc.cln.transaction.entity.cln.ClnCaseSubEntity;
import cub.lip.svc.cln.transaction.entity.cln.ClnCollInfoEntity;
import cub.lip.svc.cln.transaction.entity.cln.ClnCustomerGuarantorEntity;
import cub.lip.svc.cln.transaction.entity.cln.ClnCustomerGuarantorPKEntity;
import cub.lip.svc.cln.transaction.entity.cln.ClnCustomerInfoEntity;
import cub.lip.svc.cln.transaction.entity.cln.ClnCustomerInfoPKEntity;
import cub.lip.svc.cln.transaction.entity.cln.ClnRepayFinAssetsEntity;
import cub.lip.svc.cln.transaction.entity.base.ClnTxLogArchiveEntity;
import cub.lip.svc.cln.transaction.repo.ClnCaseMainRepository;
import cub.lip.svc.cln.transaction.repo.ClnCaseSubRepository;
import cub.lip.svc.cln.transaction.repo.ClnCustomerGuarantorRepository;
import cub.lip.svc.cln.transaction.repo.ClnCustomerInfoRepository;
import cub.lip.svc.cln.transaction.repo.ClnRepayFinAssetsRepository;
import cub.lip.svc.cln.transaction.repo.base.ClnTxLogArchiveRepository;
import cub.lip.svc.cln.transaction.svc.CTNCINPTT001Svc;
import cub.lip.svc.cln.transaction.svc.dataprocessor.CTNCINPTT001DataProcessor;
import cub.lip.svc.cln.transaction.svc.dataprocessor.vo.CTNCINPTT001RecvDataVO;
import cub.lip.svc.cln.transaction.svc.dataprocessor.vo.CTNCINPTT001SvcVO;
import cub.lip.svc.cln.transaction.vo.CaseCheckVO;

/**
 * LIP-B-CTNCINPTT001 進件輸入維護
 *
 * @author 00550352
 */
@Service
public class CTNCINPTT001SvcImpl implements CTNCINPTT001Svc {

    /** NormalRequestFactory */
    @Autowired
    private NormalRequestFactory normalReqFactory;

    /** NormalResponseFactory */
    @Autowired
    private NormalResponseFactory normalRespFactory;

    /** RestTemplateHelper */
    @Autowired
    private RestTemplateHelper restTempHelper;

    /** ObjectMapper */
    @Autowired
    private ObjectMapper objectMapper;

    /** OrikaMapperUtil */
    @Autowired
    private OrikaMapperUtil orikaMapper;

    /** CTNCINPTT001DataProcessor */
    @Autowired
    private CTNCINPTT001DataProcessor dataProcessor;

    /** ClnCaseMainRepository */
    @Autowired
    private ClnCaseMainRepository clnCaseMainRepository;

    /** ClnCustomerGuarantorRepository */
    @Autowired
    private ClnCustomerGuarantorRepository clnCustomerGuarantorRepository;

    /** ClnRepayFinAssetsRepository */
    @Autowired
    private ClnRepayFinAssetsRepository clnRepayFinAssetsRepository;

    /** ClnCustomerInfoRepository */
    @Autowired
    private ClnCustomerInfoRepository clnCustomerInfoRepository;

    /** ClnTxLogTempRepository */
    @Autowired
    private ClnTxLogArchiveRepository cLnTxLogArchiveRepository;

    /** ClnCaseSubRepository */
    @Autowired
    private ClnCaseSubRepository clnCaseSubRepository;

    /** CommonUtil */
    @Autowired
    private CommonUtil commonUtil;

    /** CaseCheck */
    @Autowired
    private CaseCheck caseCheck;

    @Value("${cub.project-name}")
    private String serviceName;

    private final Map<String, Consumer<ClnCaseSubEntity>> caseOriginMap = new HashMap<>();

    private final Map<String, Consumer<ClnCaseSubEntity>> oriTmMap = new HashMap<>();

    private final Map<String, Consumer<ClnCaseSubEntity>> oriNtmMap = new HashMap<>();

    private static final DateTimeFormatter INPUTFORMATTER = DateTimeFormatter.ofPattern("ddMMyyyy");

    public CTNCINPTT001SvcImpl() {
        caseOriginMap.put("BUILDER", entity -> entity.setCaseOriginBuilder("1"));
        caseOriginMap.put("BROKER", entity -> entity.setCaseOriginBroker("1"));
        caseOriginMap.put("BOOK", entity -> entity.setCaseOriginBook("1"));
        caseOriginMap.put("AO", entity -> entity.setCaseOriginAo("1"));
        caseOriginMap.put("EMP", entity -> entity.setCaseOriginEmp("1"));
        caseOriginMap.put("DS", entity -> entity.setCaseOriginDs("1"));
        caseOriginMap.put("CLIENT", entity -> entity.setCaseOriginClient("1"));
        caseOriginMap.put("COUNTER", entity -> entity.setCaseOriginCounter("1"));
        caseOriginMap.put("TM", entity -> entity.setCaseOriginTm("1"));
        caseOriginMap.put("NTM", entity -> entity.setCaseOriginNtm("1"));
        caseOriginMap.put("OTHER", entity -> entity.setCaseOriginOther("1"));

        oriTmMap.put("LOAN", entity -> entity.setOriginTmLoan("1"));
        oriTmMap.put("SLOAN", entity -> entity.setOriginTmSloan("1"));
        oriTmMap.put("OB", entity -> entity.setOriginTmOb("1"));
        oriTmMap.put("OTHER", entity -> entity.setOriginTmOther("1"));

        oriNtmMap.put("CLIENT", entity -> entity.setOriginNtmClient("1"));
        oriNtmMap.put("TRF", entity -> entity.setOriginNtmTrf("1"));
        oriNtmMap.put("DS", entity -> entity.setOriginNtmDs("1"));
        oriNtmMap.put("OLD_CLIENT", entity -> entity.setOriginNtmOldClient("1"));
        oriNtmMap.put("LIST_CLIENT", entity -> entity.setOriginNtmListClient("1"));
        oriNtmMap.put("RELATION", entity -> entity.setOriginNtmRelation("1"));
        oriNtmMap.put("BROKER", entity -> entity.setOriginNtmBroker("1"));
        oriNtmMap.put("OTHER", entity -> entity.setOriginNtmOther("1"));
        oriNtmMap.put("TRANS", entity -> entity.setOriginNtmTrans("1"));
        oriNtmMap.put("NETWORK", entity -> entity.setOriginNtmNetwork("1"));
        oriNtmMap.put("CREDIT", entity -> entity.setOriginNtmCredit("1"));
        oriNtmMap.put("ADVISORY", entity -> entity.setOriginNtmAdvisory("1"));
        oriNtmMap.put("ACC_TRANS", entity -> entity.setOriginNtmAccTrans("1"));
        oriNtmMap.put("ACC_REIMBURSE", entity -> entity.setOriginNtmAccReimburse("1"));
        oriNtmMap.put("EMP_FAMILY", entity -> entity.setOriginNtmEmpFamily("1"));
        oriNtmMap.put("NAGENT_LIST_CLIENT", entity -> entity.setOriginNtmNagentListClient("1"));
        oriNtmMap.put("NAGENT_OLD_CLIENT", entity -> entity.setOriginNtmNagentOldClient("1"));
    }

    @Override
    public ResponseTemplate<EmptyDto> inputInfoModify(RequestTemplate<CTNCINPTT001Tranrq> req) throws Exception {

        CTNCINPTT001Tranrq tranrq = req.getTranrq();
        String applyId = tranrq.getApplyId();

        // 二、取得CLN_CASE_MAIN案件受理檔
        ClnCaseMainEntity clnCaseMain = clnCaseMainRepository.findById(applyId)
                .orElseThrow(() -> new DataNotFoundException("CLN_CASE_MAIN 查無資料"));

        CTNCINPTT001TranrqInputBranchInfo inputBranchInfo = tranrq.getInputBranchInfo();
        List<CTNCINPTT001TranrqBorGuar> borGuarList = tranrq.getBorGuarList();
        CTNCINPTT001SvcVO vo = new CTNCINPTT001SvcVO();
        String applyProcess = clnCaseMain.getApplyProcess();

        CaseCheckVO caseCheckVO = orikaMapper.map(tranrq, CaseCheckVO.class);
        String action = "";

        // 判斷ActionType = M (修改)
        if (StringUtils.equals("M", tranrq.getActionType())) {
            BeanUtils.copyProperties(inputBranchInfo, caseCheckVO);

            // 三、規則檢核
            caseCheck.checkInputSave(req, clnCaseMain, caseCheckVO);
            String transferInputBranch = getTransferInputBranch(req, clnCaseMain);
            boolean canUpdateBranch = "Y".equals(tranrq.getIsEffectBranch())
                    || (StringUtils.isNotBlank(transferInputBranch) && StringUtils.equals(tranrq.getBranchId(), transferInputBranch));
            if (canUpdateBranch && StringUtils.equalsAny(applyProcess, "70", "71")) {
                updateClnCaseMain(clnCaseMain, inputBranchInfo, vo);

            } else if (StringUtils.equals("5", applyProcess)) {
                // 2.1 查詢CLN_CUSTOMER_GUARANTOR既有資料
                Set<String> guarIdSet = clnCustomerGuarantorRepository.findAllByApplyId(applyId).stream()
                        .map(ClnCustomerGuarantorEntity::getGuarId).collect(Collectors.toSet());

                // 2.2 比對新舊保證人ID(需要更新及新增)
                Set<String> borGuarIdSet = borGuarList.stream().map(CTNCINPTT001TranrqBorGuar::getBorGuarId).collect(Collectors.toSet());

                // 需要刪除
                Set<String> idsToDelete = new HashSet<>(guarIdSet);
                idsToDelete.removeAll(borGuarIdSet);

                // 2.8 刪除借保人
                for (String guarId : idsToDelete) {
                    vo.addDeleteThreeTableOperation(applyId, guarId, "1", guarId, "03");
                }

                List<String> valCustlevels = new ArrayList<>();
                for (CTNCINPTT001TranrqBorGuar guar : borGuarList) {
                    //客戶資料不存在時查詢FNS，並處理WMS與借保人資料
                    processSingleGuarantor(req, tranrq, guar, vo, valCustlevels);
                }

                // 2.6 判斷借款人與共借人是否為本行專業投資人(PI資格)
                checkProfessionalInvestor(req, tranrq, borGuarList, vo);

                // 2.7 更新 CLN_CASE_MAIN
                String isAgency = valCustlevels.stream().anyMatch(Arrays.asList("01", "05", "06")::contains) ? "Y" : "N";
                updateCaseMain(tranrq, inputBranchInfo, isAgency, vo);

                // 2.8 更新 CLN_CASE_SUB
                updateCaseSub(tranrq, inputBranchInfo, vo);
            }

            // 案件歷程記錄
            action = "修改";

        } else if (StringUtils.equals("D", tranrq.getActionType())) {
            // 三、規則檢核
            caseCheck.checkInputDelete(req, clnCaseMain);
            vo.addDeleteFourTableOperation(applyId);

            // 案件歷程記錄
            action = "刪除";
        }

        // 案件歷程記錄
        ClnCaseHistoryEntity clnCaseHistoryEntity = commonUtil.getCaseHistory(applyId, "新貸/增貸進件", action, tranrq.getEmpId(),
            tranrq.getBranchId(), ClnCaseHistoryEntity.class);
        vo.addCaseHistoryEntity(clnCaseHistoryEntity);

        dataProcessor.processData(vo);

        return normalRespFactory.genNormalResponse(new EmptyDto(), req);
    }

    /**
     * 呼叫【LIP-B-CCMINBRHQ001】取得進件行的PS集中單位
     *
     * @param req 原上行電文
     * @param clnCaseMain 案件受理檔
     * @return 第一筆主單位代碼，查無對應單位時回傳空字串
     * @throws RestException 取得進件行失敗
     * @throws IOException 讀取單位對照資料失敗
     */
    private String getTransferInputBranch(RequestTemplate<CTNCINPTT001Tranrq> req, ClnCaseMainEntity clnCaseMain)
            throws RestException, IOException {
        CCMINBRHQ001Tranrq inputReq = new CCMINBRHQ001Tranrq(clnCaseMain.getLoanType(), clnCaseMain.getInputBranch(),
                clnCaseMain.getAgentBranch(), clnCaseMain.getRemitBranch());
        ResponseTemplate<CCMINBRHQ001Tranrs> response = restTempHelper
                .postForEntity(normalReqFactory.genRequestTemplate(req, inputReq, "LIP-B-CCMINBRHQ001"), CCMINBRHQ001Tranrs.class);
        if (!"0000".equals(response.getMwHeaderResponse().getReturnCode())) {
            throw new RestException(response.getMwHeaderResponse());
        }
        String inputBranch = response.getTranrs().getInputBranch();
        if (StringUtils.isBlank(inputBranch)) {
            return "";
        }
        return commonUtil.getDeptCodeList(inputBranch, null).stream().map(DeptCodeList::getMainDeptCode).findFirst().orElse(null);
    }

    /**
     * 若(IsEffectBranch == 'Y' or BranchId == transferInputBranch)且ApplyProcess= 70 or 71 更新CLN_CASE_MAIN
     *
     * @param clnCaseMain
     * @param inputBranchInfo
     * @param vo
     */
    private void updateClnCaseMain(ClnCaseMainEntity clnCaseMain, CTNCINPTT001TranrqInputBranchInfo inputBranchInfo, CTNCINPTT001SvcVO vo) {
        clnCaseMain.setAgentId(inputBranchInfo.getAgentId());
        clnCaseMain.setAgentName(inputBranchInfo.getAgentName());
        clnCaseMain.setAgentBranch(inputBranchInfo.getAgentBranch());
        clnCaseMain.setReferralId(inputBranchInfo.getReferralId());
        clnCaseMain.setReferralName(inputBranchInfo.getReferralName());
        clnCaseMain.setIntroBranch(inputBranchInfo.getIntroBranchId());
        clnCaseMain.setAoHeadId(inputBranchInfo.getAoHeadId());
        clnCaseMain.setAoHeadName(inputBranchInfo.getAoHeadName());
        clnCaseMain.setAoHeadBranch(inputBranchInfo.getAoHeadBranch());
        vo.addCaseMainEntity(clnCaseMain);
    }

    /**
    * 客戶資料不存在時查詢FNS，並處理WMS與借保人資料
     *
     * @param req
     * @param tranrq
     * @param guar
     * @param vo
     * @param valCustlevels
     * @throws JsonProcessingException
     */
    private void processSingleGuarantor(RequestTemplate<CTNCINPTT001Tranrq> req, CTNCINPTT001Tranrq tranrq, CTNCINPTT001TranrqBorGuar guar,
            CTNCINPTT001SvcVO vo, List<String> valCustlevels) throws JsonProcessingException, RestException {

        // 以案件編號、客戶類別及借保人ID判斷是否已有客戶資料；前端Type=1對應後端CustomerType=0，其餘對應1。
        // 既有客戶仍處理WMS與借保人關係更新，但不以FNS覆寫通訊資料。
        ClnCustomerInfoPKEntity customerInfoPk = new ClnCustomerInfoPKEntity(tranrq.getApplyId(),
            "1".equals(guar.getType()) ? "0" : "1", guar.getBorGuarId());
        boolean isNewCustomer = !clnCustomerInfoRepository.findById(customerInfoPk).isPresent();
        ResponseTemplate<FNSCIF0000Tranrs> fnsResponse = null;
        String sIdentity = null;
        if (isNewCustomer) {
            FNSCIF0000Tranrq fnsTranrq = new FNSCIF0000Tranrq();
            fnsTranrq.setBranchId("9999");
            fnsTranrq.setTellerId("00000");
            fnsTranrq.setFnsFlagX("");
            fnsTranrq.setIdNo(guar.getBorGuarId());
            fnsTranrq.setIdType("");
            fnsResponse = restTempHelper
                .postForEntity(normalReqFactory.genRequestTemplate(req, fnsTranrq, "FNSCIF0000"), FNSCIF0000Tranrs.class);

            // 2.4 如果RETURN_CODE='2214'，發查【MSP-B-CHECKIDC001 IDType查詢服務】
            if ("2214".equals(fnsResponse.getMwHeaderResponse().getReturnCode())) {
                ResponseTemplate<CHECKIDC001Tranrs> checkidc001Resp = restTempHelper.postForEntity(
                    normalReqFactory.genRequestTemplate(req, new CHECKIDC001Tranrq(guar.getBorGuarId()), "MSP-B-CHECKIDC001"),
                    CHECKIDC001Tranrs.class);
                MwHeaderResponse mwHeaderResponse = checkidc001Resp.getMwHeaderResponse();
                if (!"0000".equals(mwHeaderResponse.getReturnCode())) {
                    throw new RestException(mwHeaderResponse);
                }
                sIdentity = checkidc001Resp.getTranrs().getSIdentity();
            }
        }

        BigDecimal avgBal;
        String valCustlevel;

        // 2.5 檢查是否發查過WMS電文
        Optional<ClnTxLogArchiveEntity> archiveOpt = cLnTxLogArchiveRepository
                .findFirstByMsgIdAndCaseNbrAndSendDataContainingOrderBySendtimeAsc("WMS-B-CUSTTYPEQ003", tranrq.getApplyId(),
                    guar.getBorGuarId());

        if (archiveOpt.isPresent()) {
            // 2.5 (一) 解析RECV_DATA JSON字串（已發查過，不應重複寫入CLN_REPAY_FIN_ASSETS）
            CTNCINPTT001RecvDataVO dataModel = objectMapper.readValue(archiveOpt.get().getRecvData(), CTNCINPTT001RecvDataVO.class);
            avgBal = dataModel.getTranrs().getAvgBal();
            valCustlevel = dataModel.getTranrs().getValCustlevel();
            if (isValidGuarantorType(guar)) {
                valCustlevels.add(valCustlevel);
            }
        } else {
            // 2.5 (二) 若查無資料，發查【WMS-B-CUSTTYPEQ003 取得客戶身分資訊】
            CUSTTYPEQ003Tranrq custReq = new CUSTTYPEQ003Tranrq();
            custReq.setInCustomerId(guar.getBorGuarId());
            ResponseTemplate<CUSTTYPEQ003Tranrs> custResp = restTempHelper
                    .postForEntity(normalReqFactory.genRequestTemplate(req, custReq, "WMS-B-CUSTTYPEQ003"), CUSTTYPEQ003Tranrs.class);

            avgBal = custResp.getTranrs().getAvgBal();
            valCustlevel = custResp.getTranrs().getValCustlevel();
            if (isValidGuarantorType(guar))
                valCustlevels.add(valCustlevel);
        }
        // 僅新客戶查詢FNS並回寫CLN_CUSTOMER_INFO，避免覆蓋既有客戶資料
        if (isNewCustomer) {
            saveOrUpdateCustomerInfo(tranrq, guar, fnsResponse, valCustlevel, avgBal, vo, sIdentity);
        }

        processCustomerData(tranrq, guar, fnsResponse, avgBal, !archiveOpt.isPresent(), vo);
    }

    /**
     * 判斷Type 給2.6的valCustlevels
     *
     * @param guar
     * @return
     */
    private boolean isValidGuarantorType(CTNCINPTT001TranrqBorGuar guar) {
        return "1".equals(guar.getType()) || ("0".equals(guar.getType()) && "3".equals(guar.getBorGuarKind()));
    }

    /**
     * 2.6 判斷借款人與共借人是否為本行專業投資人(PI資格)
     *
     * @param req
     * @param tranrq
     * @param borGuarList
     */
    private void checkProfessionalInvestor(RequestTemplate<CTNCINPTT001Tranrq> req, CTNCINPTT001Tranrq tranrq,
            List<CTNCINPTT001TranrqBorGuar> borGuarList, CTNCINPTT001SvcVO vo) {
        String invFlag = "Y";
        if (StringUtils.equalsAny(tranrq.getGageType(), "M", "B")) {
            List<CTNCINPTT001TranrqBorGuar> newBorGuarList = borGuarList.stream().filter(this::isValidGuarantorType)
                    .collect(Collectors.toList());

            for (CTNCINPTT001TranrqBorGuar newBorGuar : newBorGuarList) {
                // (二) 發查【WMS-B-GETKYCSTATQ002 取得客戶KYC現況狀態】
                GETKYCSTATQ002Tranrq getkycReq = new GETKYCSTATQ002Tranrq(tranrq.getBranchId(), tranrq.getEmpId(),
                        newBorGuar.getBorGuarId());
                ResponseTemplate<GETKYCSTATQ002Tranrs> getkycTranrsResponse = restTempHelper.postForEntity(
                    normalReqFactory.genRequestTemplate(req, getkycReq, "WMS-B-GETKYCSTATQ002"), GETKYCSTATQ002Tranrs.class);

                if ("0".equals(getkycTranrsResponse.getTranrs().getFlgIsproinvestor())) {
                    invFlag = "N";
                    break;
                }
            }

            List<String> types = Arrays.asList("I", "B", "D", "A");
            List<ClnCollInfoEntity> entitiesToSave = new ArrayList<>();
            for (String type : types) {
                ClnCollInfoEntity entity = new ClnCollInfoEntity();
                entity.setApplyId(tranrq.getApplyId());
                entity.setType(type);
                entity.setCustProfinvFlag(invFlag);
                entity.setGageType(tranrq.getGageType());
                entity.setUpdId(tranrq.getEmpId());
                entity.setUpdTime(Timestamp.valueOf(LocalDateTime.now()));

                entitiesToSave.add(entity);
            }
            vo.addCollInfoEntities(entitiesToSave);
        }
    }

    /**
     * 更新 CLN_CASE_MAIN
     *
     * @param tranrq
     * @param inputBranchInfo
     * @param isAgency
     * @param vo
     */
    private void updateCaseMain(CTNCINPTT001Tranrq tranrq, CTNCINPTT001TranrqInputBranchInfo inputBranchInfo, String isAgency,
            CTNCINPTT001SvcVO vo) {
        clnCaseMainRepository.findById(tranrq.getApplyId()).ifPresent(clnCaseMain -> {
            clnCaseMain.setBorrowName(tranrq.getBorrowName());
            clnCaseMain.setReapplyReason(tranrq.getReapplyReason());
            clnCaseMain.setAgentId(inputBranchInfo.getAgentId());
            clnCaseMain.setAgentName(inputBranchInfo.getAgentName());
            clnCaseMain.setAgentBranch(inputBranchInfo.getAgentBranch());
            clnCaseMain.setReferralId(inputBranchInfo.getReferralId());
            clnCaseMain.setReferralName(inputBranchInfo.getReferralName());
            clnCaseMain.setIntroBranch(inputBranchInfo.getIntroBranchId());
            clnCaseMain.setContApprComId(inputBranchInfo.getContactId());
            clnCaseMain.setContApprComName(inputBranchInfo.getContactName());
            clnCaseMain.setContApprTelArea(inputBranchInfo.getContactTelArea());
            clnCaseMain.setContApprTelNum(inputBranchInfo.getContactTelNum());
            clnCaseMain.setContApprTelExt(inputBranchInfo.getContactTelExt());
            clnCaseMain.setContApprMobile(inputBranchInfo.getContactMobile());
            clnCaseMain.setContApprEmail(inputBranchInfo.getContactEmail());
            clnCaseMain.setIsAgency(isAgency);
            clnCaseMain.setAoHeadId(inputBranchInfo.getAoHeadId());
            clnCaseMain.setAoHeadName(inputBranchInfo.getAoHeadName());
            clnCaseMain.setAoHeadBranch(inputBranchInfo.getAoHeadBranch());
            vo.addCaseMainEntity(clnCaseMain);
        });
    }

    /**
     * 更新 CLN_CASE_SUB
     *
     * @param tranrq
     * @param inputBranchInfo
     * @param vo
     */
    private void updateCaseSub(CTNCINPTT001Tranrq tranrq, CTNCINPTT001TranrqInputBranchInfo inputBranchInfo, CTNCINPTT001SvcVO vo) {
        clnCaseSubRepository.findById(tranrq.getApplyId()).ifPresent(entity -> {
            entity.setApplyId(tranrq.getApplyId());
            entity.setUpdId(tranrq.getEmpId());
            entity.setUpdDate(Date.valueOf(LocalDate.now()));

            resetCaseSubEntity(entity);
            Consumer<ClnCaseSubEntity> caseOriginAction = caseOriginMap.getOrDefault(inputBranchInfo.getCaseOrigin(), e -> {
            });
            caseOriginAction.accept(entity);
            entity.setCaseOriginOtherDesc(inputBranchInfo.getCaseOriginOtherDesc());

            String oriTmString = inputBranchInfo.getOriTm();
            if (StringUtils.isNotBlank(oriTmString)) {
                String[] oriTmOptions = oriTmString.split(",");

                for (String option : oriTmOptions) {
                    Consumer<ClnCaseSubEntity> oriTmAction = oriTmMap.getOrDefault(option, e -> {
                    });

                    oriTmAction.accept(entity);
                }
            }

            entity.setOriginTmOtherDesc(inputBranchInfo.getOriTmOthrDesc());
            entity.setOriginTmOtherCode(inputBranchInfo.getOriTmOthrCode());
            entity.setOriginTmOtherSeqno(inputBranchInfo.getOriTmOthrSeq());

            String oriNtmString = inputBranchInfo.getOriNtm();
            if (StringUtils.isNotBlank(oriNtmString)) {
                String[] oriNtmOptions = oriNtmString.split(",");

                for (String option : oriNtmOptions) {
                    Consumer<ClnCaseSubEntity> oriNtmAction = oriNtmMap.getOrDefault(option, e -> {
                    });

                    oriNtmAction.accept(entity);
                }
            }
            entity.setOriginNtmOtherDesc(inputBranchInfo.getOriNtmOtherDesc());
            entity.setOriginNtmAdvisoryDesc(inputBranchInfo.getOriNtmAdvisoryDesc());
            vo.addCaseSubEntity(entity);
        });
    }

    /**
     * 2.7 逐筆處理@BorGuarList
     *
     * @param tranrq
     * @param guar
     * @param fnsResponse
     * @param avgBal
     * @param isNewQuery 是否為新發查（true:新發查需寫入CLN_REPAY_FIN_ASSETS; false:已存在不重複寫入）
     * @param vo
     */
    public void processCustomerData(CTNCINPTT001Tranrq tranrq, CTNCINPTT001TranrqBorGuar guar,
            ResponseTemplate<FNSCIF0000Tranrs> fnsResponse, BigDecimal avgBal, boolean isNewQuery, CTNCINPTT001SvcVO vo) {

        // (三) 新增 CLN_REPAY_FIN_ASSETS（僅在新發查時寫入，避免重複）
        if (isNewQuery && isValidGuarantorType(guar) && avgBal.compareTo(BigDecimal.ZERO) > 0) {
            saveRepayFinAssets(tranrq, guar, avgBal, vo);
        }
        // (四) 新增/更新CLN_CUSTOMER_GUARANTOR
        saveOrUpdateCustomerGuarantor(tranrq, guar, fnsResponse == null ? null : fnsResponse.getTranrs(), vo);

    }

    /**
     * 新增/更新 CLN_CUSTOMER_INFO
     *
     * @param tranrq
     * @param guar
     * @param fnsResponse
     * @param valCustlevel
     * @param avgBal
     * @param vo
     */
    private void saveOrUpdateCustomerInfo(CTNCINPTT001Tranrq tranrq, CTNCINPTT001TranrqBorGuar guar,
            ResponseTemplate<FNSCIF0000Tranrs> fnsResponse, String valCustlevel, BigDecimal avgBal, CTNCINPTT001SvcVO vo,
            String sIdentity) {
        FNSCIF0000Tranrs fnscif0000Tranrs = fnsResponse.getTranrs();

        // CTNCINPTT001TranrqBorGuar中的Type是CUSTOMER_GUARANTOR.GUAR_KIND5的定義，在此進行與CLN_CUSTOMER_INFO.CUSTOMER_TYPE的定義轉換
        ClnCustomerInfoPKEntity pkEntity = new ClnCustomerInfoPKEntity(tranrq.getApplyId(), ("1".equals(guar.getType())) ? "0" : "1",
                guar.getBorGuarId());

        ClnCustomerInfoEntity entity = clnCustomerInfoRepository.findById(pkEntity)
                .orElse(orikaMapper.map(pkEntity, ClnCustomerInfoEntity.class));

        entity.setCustomerName(guar.getBorGuarName());

        try {
            LocalDate birthDate = LocalDate.parse(safeString(fnscif0000Tranrs.getBirthday()), INPUTFORMATTER);
            entity.setBirthday(Date.valueOf(birthDate));
        } catch (DateTimeParseException e) {
            entity.setBirthday(null);
        }

        entity.setConZip(safeString(fnscif0000Tranrs.getPostCode()));
        entity.setConAddr(safeString(fnscif0000Tranrs.getAddress1()));
        entity.setDayTelArea(processPhoneNumber(fnscif0000Tranrs.getBusinessPhone(), true));
        entity.setDayTelNum(processPhoneNumber(fnscif0000Tranrs.getBusinessPhone(), false));
        entity.setDayTelExt(safeString(fnscif0000Tranrs.getPhoneBusExt()));
        entity.setNightTelArea(processPhoneNumber(fnscif0000Tranrs.getPhoneNo(), true));
        entity.setNightTelNum(processPhoneNumber(fnscif0000Tranrs.getPhoneNo(), false));
        entity.setNightTelExt(safeString(fnscif0000Tranrs.getPhoneResExt()));
        entity.setMobile(safeString(fnscif0000Tranrs.getMobilePhoneNumber()));
        entity.setEmail(safeString(fnscif0000Tranrs.getEmailAddress()));
        entity.setMarry(safeString(fnscif0000Tranrs.getMaritalStatus()));
        entity.setRegZip(safeString(fnscif0000Tranrs.getRegisteredPostCode()));
        entity.setRegAddr(safeString(fnscif0000Tranrs.getRegisteredAddress1()));
        entity.setIdType(
            safeString("2214".equals(fnsResponse.getMwHeaderResponse().getReturnCode()) ? sIdentity : fnscif0000Tranrs.getIdType()));
        entity.setResidenceCountry(safeString(fnscif0000Tranrs.getCountryCode()));
        entity.setFaxTelArea(processPhoneNumber(fnscif0000Tranrs.getFaxNumber(), true));
        entity.setFaxTelNum(processPhoneNumber(fnscif0000Tranrs.getFaxNumber(), false));

        entity.setGuarKind(guar.getBorGuarKind());
        entity.setIsGageOwner(guar.getIsGageOwner());
        entity.setUpdId(tranrq.getEmpId());
        entity.setUpdDate(Date.valueOf(LocalDate.now()));
        entity.setCustLevel(valCustlevel);
        entity.setAvgbal(
            avgBal.compareTo(BigDecimal.ZERO) == 0 ? BigDecimal.ZERO : avgBal.divide(new BigDecimal(10000), 2, RoundingMode.FLOOR));
        entity.setCheckCustInfo("0");

        vo.addCustomerInfoEntity(entity);
    }

    /**
     * 安全檢查字串
     *
     * @param value
     * @return
     */
    private String safeString(String value) {
        return StringUtils.isNotBlank(value) ? value.trim() : "";
    }

    /**
     * 新增 CLN_REPAY_FIN_ASSETS
     *
     * @param tranrq
     * @param guar
     * @param avgBal
     * @param vo
     */
    private void saveRepayFinAssets(CTNCINPTT001Tranrq tranrq, CTNCINPTT001TranrqBorGuar guar, BigDecimal avgBal, CTNCINPTT001SvcVO vo) {
        Integer seqNo = clnRepayFinAssetsRepository.findTopByApplyIdAndCustomerIdOrderBySeqNoDesc(tranrq.getApplyId(), guar.getBorGuarId())
                .map(ClnRepayFinAssetsEntity::getSeqNo).map(max -> max + 1).orElse(1);
        ClnRepayFinAssetsEntity clnRepayFinAssetsEntity = new ClnRepayFinAssetsEntity();
        clnRepayFinAssetsEntity.setApplyId(tranrq.getApplyId());
        clnRepayFinAssetsEntity.setCustomerId(guar.getBorGuarId());
        clnRepayFinAssetsEntity.setSeqNo(seqNo);
        clnRepayFinAssetsEntity.setIncomeCode("03");
        clnRepayFinAssetsEntity.setIncomeName(guar.getBorGuarName());
        clnRepayFinAssetsEntity.setIncomeItem(null);
        clnRepayFinAssetsEntity.setIncome(avgBal == null || avgBal.compareTo(BigDecimal.ZERO) == 0 ? BigDecimal.ZERO
                : avgBal.divide(new BigDecimal(10000), 2, RoundingMode.FLOOR));
        clnRepayFinAssetsEntity.setIncomeMsg(null);
        clnRepayFinAssetsEntity.setUpdId(tranrq.getEmpId());
        clnRepayFinAssetsEntity.setUpdDate(Date.valueOf(LocalDate.now()));
        clnRepayFinAssetsEntity.setSysImport("1");

        vo.addRepayFinAssetsEntity(clnRepayFinAssetsEntity);

    }

    /**
     * 新增/更新CLN_CUSTOMER_GUARANTOR
     *
     * @param tranrq
     * @param guar
     * @param fnscif0000Tranrs
     * @param vo
     */
    private void saveOrUpdateCustomerGuarantor(CTNCINPTT001Tranrq tranrq, CTNCINPTT001TranrqBorGuar guar, FNSCIF0000Tranrs fnscif0000Tranrs,
            CTNCINPTT001SvcVO vo) {
        String applyId = tranrq.getApplyId();
        ClnCustomerGuarantorPKEntity pkEntity = new ClnCustomerGuarantorPKEntity(applyId, guar.getBorGuarId());

        ClnCustomerGuarantorEntity entity = clnCustomerGuarantorRepository.findById(pkEntity)
                .orElse(orikaMapper.map(pkEntity, ClnCustomerGuarantorEntity.class));

        entity.setGuarName(guar.getBorGuarName());
        entity.setGuarKind1(guar.getBorGuarKind().equals("1") ? "1" : "0");
        entity.setGuarKind2(guar.getBorGuarKind().equals("2") ? "1" : "0");
        entity.setGuarKind3(guar.getBorGuarKind().equals("3") ? "1" : "0");
        entity.setGuarKind4(guar.getIsGageOwner().equals("1") ? "1" : "0");
        entity.setGuarKind5(guar.getType());
        entity.setUpdId(tranrq.getEmpId());
        entity.setUpdDate(Date.valueOf(LocalDate.now()));

        if (fnscif0000Tranrs == null) {
            vo.addCustomerGuarantorEntity(entity);
            return;
        }

        try {
            LocalDate birthDate = LocalDate.parse(safeString(fnscif0000Tranrs.getBirthday()), INPUTFORMATTER);
            entity.setBirthday(Date.valueOf(birthDate));
        } catch (DateTimeParseException e) {
            entity.setBirthday(null);
        }

        entity.setMarry(safeString(fnscif0000Tranrs.getMaritalStatus()));
        entity.setEmail(safeString(fnscif0000Tranrs.getEmailAddress()));
        entity.setRegZip(safeString(fnscif0000Tranrs.getRegisteredPostCode()));
        entity.setRegAddr(safeString(fnscif0000Tranrs.getRegisteredAddress1()));
        entity.setConZip(safeString(fnscif0000Tranrs.getPostCode()));
        entity.setConAddr(safeString(fnscif0000Tranrs.getAddress1()));
        entity.setMobile(safeString(fnscif0000Tranrs.getMobilePhoneNumber()));
        entity.setDayTelArea(processPhoneNumber(fnscif0000Tranrs.getBusinessPhone(), true));
        entity.setDayTelNum(processPhoneNumber(fnscif0000Tranrs.getBusinessPhone(), false));
        entity.setDayTelExt(safeString(fnscif0000Tranrs.getPhoneBusExt()));
        entity.setNightTelArea(processPhoneNumber(fnscif0000Tranrs.getPhoneNo(), true));
        entity.setNightTelNum(processPhoneNumber(fnscif0000Tranrs.getPhoneNo(), false));
        entity.setNightTelExt(safeString(fnscif0000Tranrs.getPhoneResExt()));
        entity.setFaxTelArea(processPhoneNumber(fnscif0000Tranrs.getFaxNumber(), true));
        entity.setFaxTelNum(processPhoneNumber(fnscif0000Tranrs.getFaxNumber(), false));

        vo.addCustomerGuarantorEntity(entity);
    }

    /**
     * 清空CLN_CASE_SUB原有的案件來源、TM來源、非TM來源資料
     *
     * @param entity
     */
    private void resetCaseSubEntity(ClnCaseSubEntity entity) {
        entity.setCaseOriginBuilder("0");
        entity.setCaseOriginBroker("0");
        entity.setCaseOriginBook("0");
        entity.setCaseOriginAo("0");
        entity.setCaseOriginEmp("0");
        entity.setCaseOriginDs("0");
        entity.setCaseOriginClient("0");
        entity.setCaseOriginCounter("0");
        entity.setCaseOriginTm("0");
        entity.setCaseOriginNtm("0");
        entity.setCaseOriginOther("0");
        entity.setOriginTmLoan("0");
        entity.setOriginTmSloan("0");
        entity.setOriginTmOb("0");
        entity.setOriginTmOther("0");
        entity.setOriginNtmClient("0");
        entity.setOriginNtmTrf("0");
        entity.setOriginNtmDs("0");
        entity.setOriginNtmOldClient("0");
        entity.setOriginNtmListClient("0");
        entity.setOriginNtmRelation("0");
        entity.setOriginNtmBroker("0");
        entity.setOriginNtmOther("0");
        entity.setOriginNtmTrans("0");
        entity.setOriginNtmNetwork("0");
        entity.setOriginNtmCredit("0");
        entity.setOriginNtmAdvisory("0");
        entity.setOriginNtmAccTrans("0");
        entity.setOriginNtmAccReimburse("0");
        entity.setOriginNtmEmpFamily("0");
        entity.setOriginNtmNagentListClient("0");
        entity.setOriginNtmNagentOldClient("0");
    }

    /**
     * 號碼處理
     *
     * @param phoneData
     * @param isArea
     * @return
     */
    private String processPhoneNumber(String phoneData, boolean isArea) {
        String safePhoneData = safeString(phoneData);
        if (safePhoneData.length() >= 5) {
            return isArea ? safePhoneData.substring(0, 2) : safePhoneData.substring(3, Math.min(13, safePhoneData.length()));
        }
        return null;
    }
}
```

**CTNCINPTT001SvcVO.java 跨層異動資料 Java · 104 行**

lip-svc-cln-transaction/src/main/java/cub/lip/svc/cln/transaction/svc/dataprocessor/vo/CTNCINPTT001SvcVO.java

```java
package cub.lip.svc.cln.transaction.svc.dataprocessor.vo;

import java.util.ArrayList;
import java.util.List;

import cub.lip.svc.cln.transaction.entity.base.ClnCaseHistoryEntity;
import cub.lip.svc.cln.transaction.entity.cln.ClnCaseMainEntity;
import cub.lip.svc.cln.transaction.entity.cln.ClnCaseSubEntity;
import cub.lip.svc.cln.transaction.entity.cln.ClnCollInfoEntity;
import cub.lip.svc.cln.transaction.entity.cln.ClnCustomerGuarantorEntity;
import cub.lip.svc.cln.transaction.entity.cln.ClnCustomerInfoEntity;
import cub.lip.svc.cln.transaction.entity.cln.ClnRepayFinAssetsEntity;
import lombok.Data;

/**
 * LIP-B-CTNCINPTT001進件輸入維護
 * VO
 *
 * @author 00550352
 */
@Data
public class CTNCINPTT001SvcVO {

    private List<ClnCaseMainEntity> caseMainEntities = new ArrayList<>();

    private List<ClnCaseSubEntity> caseSubEntities = new ArrayList<>();

    private List<ClnCustomerInfoEntity> customerInfoEntities = new ArrayList<>();

    private List<ClnCustomerGuarantorEntity> customerGuarantorEntities = new ArrayList<>();

    private List<ClnRepayFinAssetsEntity> repayFinAssetsEntities = new ArrayList<>();

    private List<ClnCollInfoEntity> collInfoEntities = new ArrayList<>();

    private List<ClnCaseHistoryEntity> caseHistoryEntities = new ArrayList<>();

    private List<DeleteOperation> deleteOperations = new ArrayList<>();

    @Data
    public static class DeleteOperation {
        private String operationType; // "THREE_TABLE" 或 "FOUR_TABLE"

        private String applyId;

        private String customerId;

        private String customerType;

        private String guarId;

        private String incomeCode;

        public DeleteOperation(String applyId, String customerId, String customerType, String guarId, String incomeCode) {
            this.operationType = "THREE_TABLE";
            this.applyId = applyId;
            this.customerId = customerId;
            this.customerType = customerType;
            this.guarId = guarId;
            this.incomeCode = incomeCode;
        }

        public DeleteOperation(String applyId) {
            this.operationType = "FOUR_TABLE";
            this.applyId = applyId;
        }
    }

    public void addCaseMainEntity(ClnCaseMainEntity entity) {
        this.caseMainEntities.add(entity);
    }

    public void addCaseSubEntity(ClnCaseSubEntity entity) {
        this.caseSubEntities.add(entity);
    }

    public void addCustomerInfoEntity(ClnCustomerInfoEntity entity) {
        this.customerInfoEntities.add(entity);
    }

    public void addCustomerGuarantorEntity(ClnCustomerGuarantorEntity entity) {
        this.customerGuarantorEntities.add(entity);
    }

    public void addRepayFinAssetsEntity(ClnRepayFinAssetsEntity entity) {
        this.repayFinAssetsEntities.add(entity);
    }

    public void addCollInfoEntities(List<ClnCollInfoEntity> entities) {
        this.collInfoEntities.addAll(entities);
    }

    public void addCaseHistoryEntity(ClnCaseHistoryEntity entity) {
        this.caseHistoryEntities.add(entity);
    }

    public void addDeleteThreeTableOperation(String applyId, String customerId, String customerType, String guarId, String incomeCode) {
        this.deleteOperations.add(new DeleteOperation(applyId, customerId, customerType, guarId, incomeCode));
    }

    public void addDeleteFourTableOperation(String applyId) {
        this.deleteOperations.add(new DeleteOperation(applyId));
    }
}
```

**CTNCINPTT001DataProcessor.java 交易寫入 Java · 158 行**

lip-svc-cln-transaction/src/main/java/cub/lip/svc/cln/transaction/svc/dataprocessor/CTNCINPTT001DataProcessor.java

```java
package cub.lip.svc.cln.transaction.svc.dataprocessor;

import java.util.List;

import org.apache.commons.collections.CollectionUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import cub.lip.svc.cln.transaction.entity.cln.ClnCustomerGuarantorPKEntity;
import cub.lip.svc.cln.transaction.entity.cln.ClnCustomerInfoPKEntity;
import cub.lip.svc.cln.transaction.repo.ClnCaseHistoryRepository;
import cub.lip.svc.cln.transaction.repo.ClnCaseMainRepository;
import cub.lip.svc.cln.transaction.repo.ClnCaseSubRepository;
import cub.lip.svc.cln.transaction.repo.ClnCollInfoRepository;
import cub.lip.svc.cln.transaction.repo.ClnCustomerGuarantorRepository;
import cub.lip.svc.cln.transaction.repo.ClnCustomerInfoRepository;
import cub.lip.svc.cln.transaction.repo.ClnRepayFinAssetsRepository;
import cub.lip.svc.cln.transaction.svc.dataprocessor.vo.CTNCINPTT001SvcVO;

/**
 * LIP-B-CTNCINPTT001進件輸入維護
 * 交易控制
 *
 * @author 00550352
 */
@Service
public class CTNCINPTT001DataProcessor {

    /** ClnCaseMainRepository */
    @Autowired
    private ClnCaseMainRepository clnCaseMainRepository;

    /** ClnCustomerGuarantorRepository */
    @Autowired
    private ClnCustomerGuarantorRepository clnCustomerGuarantorRepository;

    /** ClnCustomerInfoRepository */
    @Autowired
    private ClnCustomerInfoRepository clnCustomerInfoRepository;

    /** ClnRepayFinAssetsRepository */
    @Autowired
    private ClnRepayFinAssetsRepository clnRepayFinAssetsRepository;

    /** ClnCaseSubRepository */
    @Autowired
    private ClnCaseSubRepository clnCaseSubRepository;

    /** ClnCollInfoRepository */
    @Autowired
    private ClnCollInfoRepository clnCollInfoRepository;

    /** ClnCaseHistoryRepository */
    @Autowired
    private ClnCaseHistoryRepository clnCaseHistoryRepository;

    @Transactional(rollbackFor = Exception.class)
    public void processData(CTNCINPTT001SvcVO vo) {

        // 1. 先刪除
        executeDeleteOperations(vo.getDeleteOperations());

        // 2. 後新增/更新

        // 儲存 CLN_CASE_MAIN
        if (CollectionUtils.isNotEmpty(vo.getCaseMainEntities())) {
            clnCaseMainRepository.saveAll(vo.getCaseMainEntities());
        }

        // 儲存 CLN_CASE_SUB
        if (CollectionUtils.isNotEmpty(vo.getCaseSubEntities())) {
            clnCaseSubRepository.saveAll(vo.getCaseSubEntities());
        }

        // 儲存 CLN_CUSTOMER_INFO
        if (CollectionUtils.isNotEmpty(vo.getCustomerInfoEntities())) {
            clnCustomerInfoRepository.saveAll(vo.getCustomerInfoEntities());
        }

        // 儲存 CLN_CUSTOMER_GUARANTOR
        if (CollectionUtils.isNotEmpty(vo.getCustomerGuarantorEntities())) {
            clnCustomerGuarantorRepository.saveAll(vo.getCustomerGuarantorEntities());
        }

        // 儲存 CLN_REPAY_FIN_ASSETS
        if (CollectionUtils.isNotEmpty(vo.getRepayFinAssetsEntities())) {
            clnRepayFinAssetsRepository.saveAll(vo.getRepayFinAssetsEntities());
        }

        // 儲存 CLN_COLL_INFO
        if (CollectionUtils.isNotEmpty(vo.getCollInfoEntities())) {
            clnCollInfoRepository.saveAll(vo.getCollInfoEntities());
        }

        // 儲存 CLN_CASE_HISTORY
        if (CollectionUtils.isNotEmpty(vo.getCaseHistoryEntities())) {
            clnCaseHistoryRepository.saveAll(vo.getCaseHistoryEntities());
        }
    }

    /**
     * 執行刪除操作
     *
     * @param deleteOperations
     */
    private void executeDeleteOperations(List<CTNCINPTT001SvcVO.DeleteOperation> deleteOperations) {
        for (CTNCINPTT001SvcVO.DeleteOperation deleteOp : deleteOperations) {
            if ("THREE_TABLE".equals(deleteOp.getOperationType())) {
                deleteThreeTable(deleteOp.getApplyId(), deleteOp.getCustomerId(), deleteOp.getCustomerType(), deleteOp.getGuarId(),
                    deleteOp.getIncomeCode());
            } else if ("FOUR_TABLE".equals(deleteOp.getOperationType())) {
                deleteFourTable(deleteOp.getApplyId());
            }
        }
    }

    /**
     * 刪除借保人
     *
     * @param applyId
     * @param customerId
     * @param customerType
     * @param guarId
     * @param incomeCode
     */
    public void deleteThreeTable(String applyId, String customerId, String customerType, String guarId, String incomeCode) {

        // 刪除CLN_CUSTOMER_GUARANTOR
        clnCustomerGuarantorRepository.deleteById(new ClnCustomerGuarantorPKEntity(applyId, guarId));

        // 刪除CLN_CUSTOMER_INFO
        clnCustomerInfoRepository.deleteById(new ClnCustomerInfoPKEntity(applyId, customerType, customerId));

        // 刪除CLN_REPAY_FIN_ASSETS
        clnRepayFinAssetsRepository.deleteByApplyIdAndCustomerIdAndIncomeCode(applyId, customerId, incomeCode);
    }

    /**
     * ActionType = 'D' 刪除
     *
     * @param applyId
     */
    public void deleteFourTable(String applyId) {

        // 刪除CLN_CASE_MAIN(案件受理檔)
        clnCaseMainRepository.deleteById(applyId);

        // 刪除CLN_CUSTOMER_INFO
        clnCustomerInfoRepository.deleteByApplyId(applyId);

        // 刪除CLN_CUSTOMER_GUARANTOR
        clnCustomerGuarantorRepository.deleteByApplyId(applyId);

        // 刪除CLN_CASE_SUB(影像受理檔)
        clnCaseSubRepository.deleteById(applyId);
    }
}
```

**CTNCINPTT001SvcImplTest.java 目前為註解狀態 Java · 2479 行**

lip-svc-cln-transaction/src/test/java/lip/svc/cln/transaction/service/impl/CTNCINPTT001SvcImplTest.java

```java
//package lip.svc.cln.transaction.service.impl;
//
//import static org.junit.jupiter.api.Assertions.assertEquals;
//import static org.junit.jupiter.api.Assertions.assertNotNull;
//import static org.junit.jupiter.api.Assertions.assertTrue;
//import static org.mockito.ArgumentMatchers.any;
//import static org.mockito.ArgumentMatchers.eq;
//import static org.mockito.Mockito.times;
//import static org.mockito.Mockito.never;
//import static org.mockito.Mockito.verify;
//import static org.mockito.Mockito.when;
//
//import java.math.BigDecimal;
//import java.util.ArrayList;
//import java.util.Arrays;
//import java.util.List;
//import java.util.Optional;
//
//import org.junit.jupiter.api.DisplayName;
//import org.junit.jupiter.api.Test;
//import org.mockito.ArgumentCaptor;
//import org.mockito.InjectMocks;
//import org.mockito.Mock;
//import org.springframework.test.util.ReflectionTestUtils;
//
//import cub.lip.lib.common.dto.base.EmptyDto;
//import cub.lip.lib.common.dto.base.MwHeader;
//import cub.lip.lib.common.dto.base.MwHeaderResponse;
//import cub.lip.lib.common.dto.base.RequestTemplate;
//import cub.lip.lib.common.dto.base.ResponseTemplate;
//import cub.lip.svc.cln.transaction.check.CaseCheck;
//import cub.lip.svc.cln.transaction.dto.ctn.CTNCINPTT001Tranrq;
//import cub.lip.svc.cln.transaction.dto.ctn.CTNCINPTT001TranrqBorGuar;
//import cub.lip.svc.cln.transaction.dto.ctn.CTNCINPTT001TranrqInputBranchInfo;
//import cub.lip.svc.cln.transaction.dto.fns.FNSCIF0000Tranrs;
//import cub.lip.svc.cln.transaction.dto.wms.CUSTTYPEQ003Tranrs;
//import cub.lip.svc.cln.transaction.dto.wms.GETKYCSTATQ002Tranrs;
//import cub.lip.svc.cln.transaction.entity.base.ClnCaseHistoryEntity;
//import cub.lip.svc.cln.transaction.entity.cln.ClnCaseMainEntity;
//import cub.lip.svc.cln.transaction.entity.cln.ClnCaseSubEntity;
//import cub.lip.svc.cln.transaction.entity.cln.ClnCustomerGuarantorEntity;
//import cub.lip.svc.cln.transaction.entity.cln.ClnCustomerGuarantorPKEntity;
//import cub.lip.svc.cln.transaction.entity.cln.ClnCustomerInfoEntity;
//import cub.lip.svc.cln.transaction.entity.cln.ClnCustomerInfoPKEntity;
//import cub.lip.svc.cln.transaction.entity.base.ClnTxLogArchiveEntity;
//import cub.lip.svc.cln.transaction.repo.ClnCaseMainRepository;
//import cub.lip.svc.cln.transaction.repo.ClnCaseSubRepository;
//import cub.lip.svc.cln.transaction.repo.ClnCustomerGuarantorRepository;
//import cub.lip.svc.cln.transaction.repo.ClnCustomerInfoRepository;
//import cub.lip.svc.cln.transaction.repo.ClnRepayFinAssetsRepository;
//import cub.lip.svc.cln.transaction.repo.base.ClnTxLogArchiveRepository;
//import cub.lip.svc.cln.transaction.svc.dataprocessor.CTNCINPTT001DataProcessor;
//import cub.lip.svc.cln.transaction.svc.dataprocessor.vo.CTNCINPTT001RecvDataTranrsVO;
//import cub.lip.svc.cln.transaction.svc.dataprocessor.vo.CTNCINPTT001RecvDataVO;
//import cub.lip.svc.cln.transaction.svc.dataprocessor.vo.CTNCINPTT001SvcVO;
//import cub.lip.svc.cln.transaction.svc.impl.CTNCINPTT001SvcImpl;
//import lip.svc.cln.transaction.service.BaseTest;
//
///**
// * LIP-B-CTNCINPTT001 進件輸入維護（單元測試）
// *
// * @author 00550352
// */
//class CTNCINPTT001SvcImplTest extends BaseTest {
//
//    @InjectMocks
//    private CTNCINPTT001SvcImpl service;
//
//    @Mock
//    private CTNCINPTT001DataProcessor dataProcessor;
//
//    @Mock
//    private ClnCaseMainRepository clnCaseMainRepository;
//
//    @Mock
//    private ClnCustomerGuarantorRepository clnCustomerGuarantorRepository;
//
//    @Mock
//    private ClnRepayFinAssetsRepository clnRepayFinAssetsRepository;
//
//    @Mock
//    private ClnCustomerInfoRepository clnCustomerInfoRepository;
//
//    @Mock
//    private ClnTxLogArchiveRepository cLnTxLogArchiveRepository;
//
//    @Mock
//    private ClnCaseSubRepository clnCaseSubRepository;
//
//    @Mock
//    private CaseCheck caseCheck;
//
//    /** 驗證既有客戶不查詢FNS或覆寫資料。 */
//    @Test
//    void testProcessSingleGuarantor_ExistingCustomerPreserved() {
//        RequestTemplate<CTNCINPTT001Tranrq> req = prepareCustomerQuery();
//        CTNCINPTT001TranrqBorGuar guar = prepareGuarantor("C001", "1");
//        ClnCustomerInfoEntity customer = new ClnCustomerInfoEntity();
//        customer.setCustomerName("Original customer");
//        customer.setConAddr("Original address");
//        customer.setCustLevel("02");
//        customer.setCheckCustInfo("1");
//        when(clnCustomerInfoRepository.findById(new ClnCustomerInfoPKEntity("TEST001", "0", "C001")))
//                .thenReturn(Optional.of(customer));
//        when(clnCustomerInfoRepository.existsById(new ClnCustomerInfoPKEntity("TEST001", "0", "C001"))).thenReturn(true);
//        ClnCustomerGuarantorEntity guarantor = new ClnCustomerGuarantorEntity();
//        guarantor.setConAddr("Original guarantor address");
//        when(clnCustomerGuarantorRepository.findById(new ClnCustomerGuarantorPKEntity("TEST001", "C001")))
//                .thenReturn(Optional.of(guarantor));
//        CTNCINPTT001SvcVO vo = new CTNCINPTT001SvcVO();
//        List<String> levels = new ArrayList<>();
//
//        ReflectionTestUtils.invokeMethod(service, "processSingleGuarantor", req, req.getTranrq(), guar, vo, levels);
//
//        verify(clnCustomerInfoRepository).existsById(new ClnCustomerInfoPKEntity("TEST001", "0", "C001"));
//        verify(clnCustomerInfoRepository, never()).findById(any(ClnCustomerInfoPKEntity.class));
//        verify(restTempHelper, never()).postForEntity(any(), eq(FNSCIF0000Tranrs.class));
//        assertTrue(vo.getCustomerInfoEntities().isEmpty());
//        assertEquals("Original customer", customer.getCustomerName());
//        assertEquals("Original address", customer.getConAddr());
//        assertEquals("02", customer.getCustLevel());
//        assertEquals("1", customer.getCheckCustInfo());
//        assertEquals("Original guarantor address", guarantor.getConAddr());
//        assertEquals("1", guarantor.getGuarKind4());
//        assertEquals(Arrays.asList("01"), levels);
//        assertEquals(1, vo.getRepayFinAssetsEntities().size());
//    }
//
//    /** 驗證新增客戶查詢FNS並建立資料。 */
//    @Test
//    void testProcessSingleGuarantor_NewCustomerQueriesFns() {
//        RequestTemplate<CTNCINPTT001Tranrq> req = prepareCustomerQuery();
//        CTNCINPTT001TranrqBorGuar guar = prepareGuarantor("C002", "0");
//        CTNCINPTT001SvcVO vo = new CTNCINPTT001SvcVO();
//
//        ReflectionTestUtils.invokeMethod(service, "processSingleGuarantor", req, req.getTranrq(), guar, vo,
//                new ArrayList<String>());
//
//        verify(restTempHelper).postForEntity(any(), eq(FNSCIF0000Tranrs.class));
//        assertEquals(1, vo.getCustomerInfoEntities().size());
//        ClnCustomerInfoEntity customer = vo.getCustomerInfoEntities().get(0);
//        assertEquals("TEST001", customer.getApplyId());
//        assertEquals("1", customer.getCustomerType());
//        assertEquals("C002", customer.getCustomerId());
//        assertEquals("FNS address", customer.getConAddr());
//        assertEquals("01", customer.getCustLevel());
//        assertEquals("FNS address", vo.getCustomerGuarantorEntities().get(0).getConAddr());
//    }
//
//    /** 驗證混合清單僅查詢不存在的客戶。 */
//    @Test
//    void testProcessSingleGuarantor_MixedCustomerList() {
//        RequestTemplate<CTNCINPTT001Tranrq> req = prepareCustomerQuery();
//        CTNCINPTT001TranrqBorGuar existing = prepareGuarantor("C001", "1");
//        CTNCINPTT001TranrqBorGuar added = prepareGuarantor("C002", "0");
//        when(clnCustomerInfoRepository.findById(new ClnCustomerInfoPKEntity("TEST001", "0", "C001")))
//                .thenReturn(Optional.of(new ClnCustomerInfoEntity()));
//        when(clnCustomerInfoRepository.existsById(new ClnCustomerInfoPKEntity("TEST001", "0", "C001"))).thenReturn(true);
//        req.getTranrq().setBorGuarList(Arrays.asList(existing, added));
//        CTNCINPTT001SvcVO vo = new CTNCINPTT001SvcVO();
//        List<String> levels = new ArrayList<>();
//
//        for (CTNCINPTT001TranrqBorGuar guar : req.getTranrq().getBorGuarList()) {
//            ReflectionTestUtils.invokeMethod(service, "processSingleGuarantor", req, req.getTranrq(), guar, vo, levels);
//        }
//
//        verify(restTempHelper, times(1)).postForEntity(any(), eq(FNSCIF0000Tranrs.class));
//        verify(restTempHelper, times(2)).postForEntity(any(), eq(CUSTTYPEQ003Tranrs.class));
//        assertEquals(1, vo.getCustomerInfoEntities().size());
//        assertEquals("C002", vo.getCustomerInfoEntities().get(0).getCustomerId());
//        assertEquals(2, vo.getCustomerGuarantorEntities().size());
//        assertEquals(2, levels.size());
//    }
//
//    /** 準備逐筆客戶查詢的回應與映射。 */
//    private RequestTemplate<CTNCINPTT001Tranrq> prepareCustomerQuery() {
//        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
//        tranrq.setApplyId("TEST001");
//        tranrq.setEmpId("EMP001");
//        RequestTemplate<CTNCINPTT001Tranrq> req = new RequestTemplate<>();
//        req.setTranrq(tranrq);
//        when(clnCustomerInfoRepository.existsById(any(ClnCustomerInfoPKEntity.class))).thenReturn(false);
//        when(clnCustomerInfoRepository.findById(any(ClnCustomerInfoPKEntity.class))).thenReturn(Optional.empty());
//        when(orikaMapper.map(any(ClnCustomerInfoPKEntity.class), eq(ClnCustomerInfoEntity.class))).thenAnswer(answer -> {
//            ClnCustomerInfoPKEntity key = answer.getArgument(0);
//            ClnCustomerInfoEntity customer = new ClnCustomerInfoEntity();
//            customer.setApplyId(key.getApplyId());
//            customer.setCustomerType(key.getCustomerType());
//            customer.setCustomerId(key.getCustomerId());
//            return customer;
//        });
//        when(orikaMapper.map(any(ClnCustomerGuarantorPKEntity.class), eq(ClnCustomerGuarantorEntity.class)))
//                .thenAnswer(answer -> new ClnCustomerGuarantorEntity());
//        FNSCIF0000Tranrs fns = new FNSCIF0000Tranrs();
//        fns.setAddress1("FNS address");
//        MwHeaderResponse header = new MwHeaderResponse();
//        header.setReturnCode("0000");
//        ResponseTemplate<FNSCIF0000Tranrs> fnsResponse = new ResponseTemplate<>();
//        fnsResponse.setMwHeaderResponse(header);
//        fnsResponse.setTranrs(fns);
//        when(restTempHelper.postForEntity(any(), eq(FNSCIF0000Tranrs.class))).thenReturn(fnsResponse);
//        CUSTTYPEQ003Tranrs wms = new CUSTTYPEQ003Tranrs();
//        wms.setValCustlevel("01");
//        wms.setAvgBal(new BigDecimal("10000"));
//        ResponseTemplate<CUSTTYPEQ003Tranrs> wmsResponse = new ResponseTemplate<>();
//        wmsResponse.setTranrs(wms);
//        when(restTempHelper.postForEntity(any(), eq(CUSTTYPEQ003Tranrs.class))).thenReturn(wmsResponse);
//        return req;
//    }
//
//    /** 準備借保人測試資料。 */
//    private CTNCINPTT001TranrqBorGuar prepareGuarantor(String customerId, String type) {
//        CTNCINPTT001TranrqBorGuar guar = new CTNCINPTT001TranrqBorGuar();
//        guar.setBorGuarId(customerId);
//        guar.setBorGuarName("Customer " + customerId);
//        guar.setType(type);
//        guar.setBorGuarKind("3");
//        guar.setIsGageOwner("1");
//        return guar;
//    }
//
//    @Test
//    @DisplayName("測試 inputInfoModify - ActionType=M, ApplyProcess=70")
//    void testInputInfoModify_ActionTypeM_ApplyProcess70() throws Exception {
//        // Arrange
//        RequestTemplate<CTNCINPTT001Tranrq> req = new RequestTemplate<>();
//        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
//        tranrq.setActionType("M");
//        tranrq.setApplyId("TEST001");
//
//        CTNCINPTT001TranrqInputBranchInfo branchInfo = new CTNCINPTT001TranrqInputBranchInfo();
//        branchInfo.setAgentId("A001");
//        branchInfo.setAgentName("測試代理人");
//        branchInfo.setAgentBranch("分行1");
//        branchInfo.setReferralId("R001");
//        branchInfo.setReferralName("轉介人1");
//        branchInfo.setRemitBranchId("B001");
//
//        tranrq.setInputBranchInfo(branchInfo);
//        req.setTranrq(tranrq);
//
//        ClnCaseMainEntity caseMain = new ClnCaseMainEntity();
//        when(clnCaseMainRepository.findById("TEST001")).thenReturn(Optional.of(caseMain));
//
//        ResponseTemplate<EmptyDto> expectedResponse = new ResponseTemplate<>();
//        when(normalResponseFactory.genNormalResponse(any(EmptyDto.class), any(RequestTemplate.class))).thenReturn(expectedResponse);
//
//        // Act
//        ResponseTemplate<EmptyDto> result = service.inputInfoModify(req);
//
//        // Assert
//        verify(clnCaseMainRepository).findById("TEST001");
//        verify(dataProcessor).processData(any(CTNCINPTT001SvcVO.class));
//        assertEquals(expectedResponse, result);
//
//        assertEquals("A001", caseMain.getAgentId());
//        assertEquals("測試代理人", caseMain.getAgentName());
//        assertEquals("分行1", caseMain.getAgentBranch());
//        assertEquals("R001", caseMain.getReferralId());
//        assertEquals("轉介人1", caseMain.getReferralName());
//        assertEquals("B001", caseMain.getIntroBranch());
//    }
//
//    @Test
//    @DisplayName("測試 inputInfoModify - ActionType=M, ApplyProcess=71")
//    void testInputInfoModify_ActionTypeM_ApplyProcess71() throws Exception {
//        // Arrange
//        RequestTemplate<CTNCINPTT001Tranrq> req = new RequestTemplate<>();
//        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
//        tranrq.setActionType("M");
//        tranrq.setApplyId("TEST001");
//
//        CTNCINPTT001TranrqInputBranchInfo branchInfo = new CTNCINPTT001TranrqInputBranchInfo();
//        branchInfo.setAgentId("A001");
//        branchInfo.setAgentName("測試代理人");
//        branchInfo.setAgentBranch("分行1");
//        branchInfo.setReferralId("R001");
//        branchInfo.setReferralName("轉介人1");
//        branchInfo.setRemitBranchId("B001");
//
//        tranrq.setInputBranchInfo(branchInfo);
//        req.setTranrq(tranrq);
//
//        ClnCaseMainEntity caseMain = new ClnCaseMainEntity();
//        when(clnCaseMainRepository.findById("TEST001")).thenReturn(Optional.of(caseMain));
//
//        ResponseTemplate<EmptyDto> expectedResponse = new ResponseTemplate<>();
//        when(normalResponseFactory.genNormalResponse(any(EmptyDto.class), any(RequestTemplate.class))).thenReturn(expectedResponse);
//
//        // Act
//        ResponseTemplate<EmptyDto> result = service.inputInfoModify(req);
//
//        // Assert
//        verify(clnCaseMainRepository).findById("TEST001");
//        verify(dataProcessor).processData(any(CTNCINPTT001SvcVO.class));
//        assertEquals(expectedResponse, result);
//
//        assertEquals("A001", caseMain.getAgentId());
//        assertEquals("測試代理人", caseMain.getAgentName());
//        assertEquals("分行1", caseMain.getAgentBranch());
//        assertEquals("R001", caseMain.getReferralId());
//        assertEquals("轉介人1", caseMain.getReferralName());
//        assertEquals("B001", caseMain.getIntroBranch());
//    }
//
//    @Test
//    @DisplayName("測試 inputInfoModify - ActionType=D")
//    void testInputInfoModify_ActionTypeD() throws Exception {
//        // Arrange
//        RequestTemplate<CTNCINPTT001Tranrq> req = new RequestTemplate<>();
//        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
//        tranrq.setActionType("D");
//        tranrq.setApplyId("TEST001");
//        tranrq.setEmpId("E001");
//        tranrq.setBranchId("B001");
//        req.setTranrq(tranrq);
//
//        ClnCaseHistoryEntity historyEntity = new ClnCaseHistoryEntity();
//        when(commonUtil.getCaseHistory("TEST001", "新貸/增貸進件", "修改", "E001", "B001", ClnCaseHistoryEntity.class)).thenReturn(historyEntity);
//
//        ResponseTemplate<EmptyDto> expectedResponse = new ResponseTemplate<>();
//        when(normalResponseFactory.genNormalResponse(any(EmptyDto.class), any(RequestTemplate.class))).thenReturn(expectedResponse);
//
//        // Act
//        ResponseTemplate<EmptyDto> result = service.inputInfoModify(req);
//
//        // Assert
//        verify(commonUtil).getCaseHistory("TEST001", "新貸/增貸進件", "修改", "E001", "B001", ClnCaseHistoryEntity.class);
//        verify(dataProcessor).processData(any(CTNCINPTT001SvcVO.class));
//        assertEquals(expectedResponse, result);
//    }
//
//    @Test
//    @DisplayName("測試 inputInfoModify - ActionType=M, ApplyProcess=5, WMS有紀錄")
//    void testInputInfoModify_ActionTypeM_ApplyProcess5_WMS() throws Exception {
//        // Arrange
//        RequestTemplate<CTNCINPTT001Tranrq> req = new RequestTemplate<>();
//        MwHeader mwHeader = new MwHeader();
//        mwHeader.setMsgId("LIP-B-CTNCINPTT001");
//        mwHeader.setSourceChannel("LON-LX-LIP-01");
//        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
//        tranrq.setActionType("M");
//        tranrq.setApplyId("TEST001");
//        tranrq.setEmpId("E001");
//        tranrq.setGageType("M");
//        req.setMwHeader(mwHeader);
//        req.setTranrq(tranrq);
//
//        // 設置借保人清單
//        List<CTNCINPTT001TranrqBorGuar> borGuarList = new ArrayList<>();
//        CTNCINPTT001TranrqBorGuar borGuar1 = new CTNCINPTT001TranrqBorGuar();
//        borGuar1.setBorGuarId("B001");
//        borGuar1.setBorGuarName("借保人1");
//        borGuar1.setType("0");
//        borGuar1.setBorGuarKind("3");
//        borGuar1.setIsGageOwner("1");
//        borGuarList.add(borGuar1);
//        tranrq.setBorGuarList(borGuarList);
//
//        CTNCINPTT001TranrqInputBranchInfo inputBranchInfo = new CTNCINPTT001TranrqInputBranchInfo();
//        inputBranchInfo.setOriTm("LOAN,SLOAN");
//        inputBranchInfo.setOriNtm("CLIENT");
//        tranrq.setInputBranchInfo(inputBranchInfo);
//
//        // 模擬現有保證人資料
//        List<ClnCustomerGuarantorEntity> existingGuarantors = new ArrayList<>();
//        ClnCustomerGuarantorEntity existingGuarantor = new ClnCustomerGuarantorEntity();
//        existingGuarantor.setGuarId("B001");
//        existingGuarantors.add(existingGuarantor);
//        when(clnCustomerGuarantorRepository.findAllByApplyId("TEST001")).thenReturn(existingGuarantors);
//
//        // 模擬 FNSCIF0000 回應
//        FNSCIF0000Tranrs fnsTranrs = new FNSCIF0000Tranrs();
//        fnsTranrs.setBirthday("01012000");
//        fnsTranrs.setMaritalStatus("1");
//        fnsTranrs.setAddress1("測試地址");
//        fnsTranrs.setPostCode("100");
//        ResponseTemplate<FNSCIF0000Tranrs> fnsResponse = new ResponseTemplate<>();
//        fnsResponse.setTranrs(fnsTranrs);
//        when(restTempHelper.postForEntity(any(), eq(FNSCIF0000Tranrs.class))).thenReturn(fnsResponse);
//
//        // 模擬 WMS 電文記錄查詢
//        ClnTxLogArchiveEntity archiveEntity = new ClnTxLogArchiveEntity();
//        String mockRecvData = "{" + "\"tranrs\": {" + "\"valCustlevel\": \"02\"," + "\"avgBal\": 2000000" + "}" + "}";
//        archiveEntity.setRecvData(mockRecvData);
//        when(cLnTxLogArchiveRepository.findFirstByMsgIdAndCaseNbrAndSendDataContainingOrderBySendtimeAsc("WMS-B-CUSTTYPEQ003", "TEST001",
//                "B001")).thenReturn(Optional.of(archiveEntity));
//
//        CTNCINPTT001RecvDataVO dataModel = new CTNCINPTT001RecvDataVO();
//        CTNCINPTT001RecvDataTranrsVO tranrs = new CTNCINPTT001RecvDataTranrsVO();
//        tranrs.setValCustlevel("02");
//        tranrs.setAvgBal(new BigDecimal("2000000"));
//        dataModel.setTranrs(tranrs);
//        when(objectMapper.readValue(mockRecvData, CTNCINPTT001RecvDataVO.class)).thenReturn(dataModel);
//
//        // 模擬 GETKYCSTATQ002Tranrs 回應
//        GETKYCSTATQ002Tranrs getkycTranrsResponse = new GETKYCSTATQ002Tranrs();
//        MwHeaderResponse mwHeaderRes = new MwHeaderResponse();
//        mwHeaderRes.setMsgId("LIP-B-CTNCINPTT001");
//        mwHeaderRes.setReturnCode("0000");
//        ResponseTemplate<GETKYCSTATQ002Tranrs> getkycResponseTemplate = new ResponseTemplate<>();
//        getkycResponseTemplate.setMwHeaderResponse(mwHeaderRes);
//        getkycResponseTemplate.setTranrs(getkycTranrsResponse);
//        when(restTempHelper.postForEntity(any(), eq(GETKYCSTATQ002Tranrs.class))).thenReturn(getkycResponseTemplate);
//
//        // 模擬案件主檔查詢
//        ClnCaseMainEntity caseMain = new ClnCaseMainEntity();
//        when(clnCaseMainRepository.findById("TEST001")).thenReturn(Optional.of(caseMain));
//
//        // 模擬案件子檔查詢
//        ClnCaseSubEntity caseSub = new ClnCaseSubEntity();
//        when(clnCaseSubRepository.findById("TEST001")).thenReturn(Optional.of(caseSub));
//
//        ResponseTemplate<EmptyDto> expectedResponse = new ResponseTemplate<>();
//        when(normalResponseFactory.genNormalResponse(any(EmptyDto.class), any(RequestTemplate.class))).thenReturn(expectedResponse);
//
//        // Act
//        ResponseTemplate<EmptyDto> result = service.inputInfoModify(req);
//
//        // Assert
//        // 驗證保證人資料處理
//        verify(clnCustomerGuarantorRepository).findAllByApplyId("TEST001");
//        verify(restTempHelper, times(1)).postForEntity(any(), eq(FNSCIF0000Tranrs.class));
//        verify(cLnTxLogArchiveRepository).findFirstByMsgIdAndCaseNbrAndSendDataContainingOrderBySendtimeAsc("WMS-B-CUSTTYPEQ003", "TEST001",
//                "B001");
//
//        // 驗證案件主檔和子檔更新
//        verify(clnCaseMainRepository).findById("TEST001");
//        verify(clnCaseSubRepository).findById("TEST001");
//
//        // 驗證資料處理器調用
//        verify(dataProcessor).processData(any(CTNCINPTT001SvcVO.class));
//
//        // 驗證回應
//        assertEquals(expectedResponse, result);
//    }
//
//    @Test
//    @DisplayName("測試 inputInfoModify - ActionType=M, ApplyProcess=5, WMS無紀錄")
//    void testInputInfoModify_ActionTypeM_ApplyProcess5() throws Exception {
//        // Arrange
//        RequestTemplate<CTNCINPTT001Tranrq> req = new RequestTemplate<>();
//        MwHeader mwHeader = new MwHeader();
//        mwHeader.setMsgId("LIP-B-CTNCINPTT001");
//        mwHeader.setSourceChannel("LON-LX-LIP-01");
//        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
//        tranrq.setActionType("M");
//        tranrq.setApplyId("TEST001");
//        tranrq.setEmpId("E001");
//        tranrq.setGageType("C");
//        req.setMwHeader(mwHeader);
//        req.setTranrq(tranrq);
//
//        // 設置借保人清單
//        List<CTNCINPTT001TranrqBorGuar> borGuarList = new ArrayList<>();
//        CTNCINPTT001TranrqBorGuar borGuar1 = new CTNCINPTT001TranrqBorGuar();
//        borGuar1.setBorGuarId("B001");
//        borGuar1.setBorGuarName("借保人1");
//        borGuar1.setType("0");
//        borGuar1.setBorGuarKind("1");
//        borGuar1.setIsGageOwner("0");
//        borGuarList.add(borGuar1);
//        tranrq.setBorGuarList(borGuarList);
//
//        CTNCINPTT001TranrqInputBranchInfo inputBranchInfo = new CTNCINPTT001TranrqInputBranchInfo();
//        inputBranchInfo.setOriTm("LOAN,SLOAN");
//        inputBranchInfo.setOriNtm("CLIENT");
//        tranrq.setInputBranchInfo(inputBranchInfo);
//
//        // 模擬現有保證人資料
//        List<ClnCustomerGuarantorEntity> existingGuarantors = new ArrayList<>();
//        ClnCustomerGuarantorEntity existingGuarantor = new ClnCustomerGuarantorEntity();
//        existingGuarantor.setGuarId("B001");
//        existingGuarantors.add(existingGuarantor);
//        when(clnCustomerGuarantorRepository.findAllByApplyId("TEST001")).thenReturn(existingGuarantors);
//
//        // 模擬 FNSCIF0000 回應
//        ResponseTemplate<FNSCIF0000Tranrs> fnsResponse = new ResponseTemplate<>();
//        when(restTempHelper.postForEntity(any(), eq(FNSCIF0000Tranrs.class))).thenReturn(fnsResponse);
//
//        // 模擬 WMS 電文記錄查詢
//        when(cLnTxLogArchiveRepository.findFirstByMsgIdAndCaseNbrAndSendDataContainingOrderBySendtimeAsc("WMS-B-CUSTTYPEQ003", "TEST001",
//                "B001")).thenReturn(Optional.empty());
//
//        // 模擬 CUSTTYPEQ003 回應
//        CUSTTYPEQ003Tranrs wmsResponse = new CUSTTYPEQ003Tranrs();
//        wmsResponse.setValCustlevel("01");
//        wmsResponse.setAvgBal(new BigDecimal("1000000"));
//        MwHeaderResponse mwHeaderResponse = new MwHeaderResponse();
//        mwHeaderResponse.setMsgId("LIP-B-CTNCINPTT001");
//        mwHeaderResponse.setReturnCode("0000");
//        ResponseTemplate<CUSTTYPEQ003Tranrs> wmsResponseTemplate = new ResponseTemplate<>();
//        wmsResponseTemplate.setMwHeaderResponse(mwHeaderResponse);
//        wmsResponseTemplate.setTranrs(wmsResponse);
//        when(restTempHelper.postForEntity(any(), eq(CUSTTYPEQ003Tranrs.class))).thenReturn(wmsResponseTemplate);
//
//        // 模擬 GETKYCSTATQ002Tranrs 回應
//        GETKYCSTATQ002Tranrs getkycTranrsResponse = new GETKYCSTATQ002Tranrs();
//        MwHeaderResponse mwHeaderRes = new MwHeaderResponse();
//        mwHeaderRes.setMsgId("LIP-B-CTNCINPTT001");
//        mwHeaderRes.setReturnCode("0000");
//        ResponseTemplate<GETKYCSTATQ002Tranrs> getkycResponseTemplate = new ResponseTemplate<>();
//        getkycResponseTemplate.setMwHeaderResponse(mwHeaderRes);
//        getkycResponseTemplate.setTranrs(getkycTranrsResponse);
//
//        // 模擬案件主檔查詢
//        ClnCaseMainEntity caseMain = new ClnCaseMainEntity();
//        when(clnCaseMainRepository.findById("TEST001")).thenReturn(Optional.of(caseMain));
//
//        // 模擬案件子檔查詢
//        ClnCaseSubEntity caseSub = new ClnCaseSubEntity();
//        when(clnCaseSubRepository.findById("TEST001")).thenReturn(Optional.of(caseSub));
//
//        ResponseTemplate<EmptyDto> expectedResponse = new ResponseTemplate<>();
//        when(normalResponseFactory.genNormalResponse(any(EmptyDto.class), any(RequestTemplate.class))).thenReturn(expectedResponse);
//
//        // Act
//        ResponseTemplate<EmptyDto> result = service.inputInfoModify(req);
//
//        // Assert
//        // 驗證保證人資料處理
//        verify(clnCustomerGuarantorRepository).findAllByApplyId("TEST001");
//        verify(restTempHelper, times(1)).postForEntity(any(), eq(FNSCIF0000Tranrs.class));
//        verify(cLnTxLogArchiveRepository).findFirstByMsgIdAndCaseNbrAndSendDataContainingOrderBySendtimeAsc("WMS-B-CUSTTYPEQ003", "TEST001",
//                "B001");
//
//        // 驗證案件主檔和子檔更新
//        verify(clnCaseMainRepository).findById("TEST001");
//        verify(clnCaseSubRepository).findById("TEST001");
//
//        // 驗證資料處理器調用
//        verify(dataProcessor).processData(any(CTNCINPTT001SvcVO.class));
//
//        // 驗證回應
//        assertEquals(expectedResponse, result);
//    }
//
//    @Test
//    @DisplayName("測試 inputInfoModify - ActionType=M, ApplyProcess=5, InputBranchInfo=null")
//    void testInputInfoModify_ActionTypeM_ApplyProcess5_inputBranchInfoIsNull() throws Exception {
//        // Arrange
//        RequestTemplate<CTNCINPTT001Tranrq> req = new RequestTemplate<>();
//        MwHeader mwHeader = new MwHeader();
//        mwHeader.setMsgId("LIP-B-CTNCINPTT001");
//        mwHeader.setSourceChannel("LON-LX-LIP-01");
//        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
//        tranrq.setActionType("M");
//        tranrq.setApplyId("TEST001");
//        tranrq.setEmpId("E001");
//        tranrq.setGageType("M");
//        req.setMwHeader(mwHeader);
//        req.setTranrq(tranrq);
//
//        // 設置借保人清單
//        List<CTNCINPTT001TranrqBorGuar> borGuarList = new ArrayList<>();
//        CTNCINPTT001TranrqBorGuar borGuar1 = new CTNCINPTT001TranrqBorGuar();
//        borGuar1.setBorGuarId("B001");
//        borGuar1.setBorGuarName("借保人1");
//        borGuar1.setType("1");
//        borGuar1.setBorGuarKind("1");
//        borGuar1.setIsGageOwner("1");
//        borGuarList.add(borGuar1);
//        tranrq.setBorGuarList(borGuarList);
//
//        CTNCINPTT001TranrqInputBranchInfo inputBranchInfo = new CTNCINPTT001TranrqInputBranchInfo();
//        inputBranchInfo.setOriTm(null);
//        inputBranchInfo.setOriNtm(null);
//        tranrq.setInputBranchInfo(inputBranchInfo);
//
//        // 模擬現有保證人資料
//        List<ClnCustomerGuarantorEntity> existingGuarantors = new ArrayList<>();
//        ClnCustomerGuarantorEntity existingGuarantor = new ClnCustomerGuarantorEntity();
//        existingGuarantor.setGuarId("B001");
//        existingGuarantors.add(existingGuarantor);
//        when(clnCustomerGuarantorRepository.findAllByApplyId("TEST001")).thenReturn(existingGuarantors);
//
//        // 模擬 FNSCIF0000 回應
//        FNSCIF0000Tranrs fnsTranrs = new FNSCIF0000Tranrs();
//        fnsTranrs.setBirthday("01012000");
//        fnsTranrs.setMaritalStatus("1");
//        fnsTranrs.setAddress1("測試地址");
//        fnsTranrs.setPostCode("100");
//        ResponseTemplate<FNSCIF0000Tranrs> fnsResponse = new ResponseTemplate<>();
//        fnsResponse.setTranrs(fnsTranrs);
//        when(restTempHelper.postForEntity(any(), eq(FNSCIF0000Tranrs.class))).thenReturn(null);
//
//        // 模擬 WMS 電文記錄查詢
//        ClnTxLogArchiveEntity archiveEntity = new ClnTxLogArchiveEntity();
//        String mockRecvData = "{" + "\"tranrs\": {" + "\"valCustlevel\": \"02\"," + "\"avgBal\": 2000000" + "}" + "}";
//        archiveEntity.setRecvData(mockRecvData);
//        when(cLnTxLogArchiveRepository.findFirstByMsgIdAndCaseNbrAndSendDataContainingOrderBySendtimeAsc("WMS-B-CUSTTYPEQ003", "TEST001",
//                "B001")).thenReturn(Optional.of(archiveEntity));
//
//        CTNCINPTT001RecvDataVO dataModel = new CTNCINPTT001RecvDataVO();
//        CTNCINPTT001RecvDataTranrsVO tranrs = new CTNCINPTT001RecvDataTranrsVO();
//        tranrs.setValCustlevel("02");
//        tranrs.setAvgBal(new BigDecimal("2000000"));
//        dataModel.setTranrs(tranrs);
//        when(objectMapper.readValue(mockRecvData, CTNCINPTT001RecvDataVO.class)).thenReturn(dataModel);
//
//        // 模擬 GETKYCSTATQ002Tranrs 回應
//        GETKYCSTATQ002Tranrs getkycTranrsResponse = new GETKYCSTATQ002Tranrs();
//        MwHeaderResponse mwHeaderRes = new MwHeaderResponse();
//        mwHeaderRes.setMsgId("LIP-B-CTNCINPTT001");
//        mwHeaderRes.setReturnCode("0000");
//        ResponseTemplate<GETKYCSTATQ002Tranrs> getkycResponseTemplate = new ResponseTemplate<>();
//        getkycResponseTemplate.setMwHeaderResponse(mwHeaderRes);
//        getkycResponseTemplate.setTranrs(getkycTranrsResponse);
//        when(restTempHelper.postForEntity(any(), eq(GETKYCSTATQ002Tranrs.class))).thenReturn(getkycResponseTemplate);
//
//        // 模擬案件主檔查詢
//        ClnCaseMainEntity caseMain = new ClnCaseMainEntity();
//        when(clnCaseMainRepository.findById("TEST001")).thenReturn(Optional.of(caseMain));
//
//        // 模擬案件子檔查詢
//        ClnCaseSubEntity caseSub = new ClnCaseSubEntity();
//        when(clnCaseSubRepository.findById("TEST001")).thenReturn(Optional.of(caseSub));
//
//        ResponseTemplate<EmptyDto> expectedResponse = new ResponseTemplate<>();
//        when(normalResponseFactory.genNormalResponse(any(EmptyDto.class), any(RequestTemplate.class))).thenReturn(expectedResponse);
//
//        // Act
//        ResponseTemplate<EmptyDto> result = service.inputInfoModify(req);
//
//        // Assert
//        // 驗證保證人資料處理
//        verify(clnCustomerGuarantorRepository).findAllByApplyId("TEST001");
//        verify(restTempHelper, times(1)).postForEntity(any(), eq(FNSCIF0000Tranrs.class));
//        verify(cLnTxLogArchiveRepository).findFirstByMsgIdAndCaseNbrAndSendDataContainingOrderBySendtimeAsc("WMS-B-CUSTTYPEQ003", "TEST001",
//                "B001");
//
//        // 驗證案件主檔和子檔更新
//        verify(clnCaseMainRepository).findById("TEST001");
//        verify(clnCaseSubRepository).findById("TEST001");
//
//        // 驗證資料處理器調用
//        verify(dataProcessor).processData(any(CTNCINPTT001SvcVO.class));
//
//        // 驗證回應
//        assertEquals(expectedResponse, result);
//    }
//
//    @Test
//    @DisplayName("測試 inputInfoModify - ActionType=M, ApplyProcess=5, oriTm=''")
//    void testInputInfoModify_ActionTypeM_ApplyProcess5_oriTmIsEmpty() throws Exception {
//        // Arrange
//        RequestTemplate<CTNCINPTT001Tranrq> req = new RequestTemplate<>();
//        MwHeader mwHeader = new MwHeader();
//        mwHeader.setMsgId("LIP-B-CTNCINPTT001");
//        mwHeader.setSourceChannel("LON-LX-LIP-01");
//        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
//        tranrq.setActionType("M");
//        tranrq.setApplyId("TEST001");
//        tranrq.setEmpId("E001");
//        tranrq.setGageType("B");
//        req.setMwHeader(mwHeader);
//        req.setTranrq(tranrq);
//
//        // 設置借保人清單
//        List<CTNCINPTT001TranrqBorGuar> borGuarList = new ArrayList<>();
//        CTNCINPTT001TranrqBorGuar borGuar1 = new CTNCINPTT001TranrqBorGuar();
//        borGuar1.setBorGuarId("B001");
//        borGuar1.setBorGuarName("借保人1");
//        borGuar1.setType("2");
//        borGuar1.setBorGuarKind("3");
//        borGuar1.setIsGageOwner("1");
//        borGuarList.add(borGuar1);
//        tranrq.setBorGuarList(borGuarList);
//
//        CTNCINPTT001TranrqInputBranchInfo inputBranchInfo = new CTNCINPTT001TranrqInputBranchInfo();
//        inputBranchInfo.setOriTm("");
//        inputBranchInfo.setOriNtm("");
//        tranrq.setInputBranchInfo(inputBranchInfo);
//
//        // 模擬現有保證人資料
//        List<ClnCustomerGuarantorEntity> existingGuarantors = new ArrayList<>();
//        ClnCustomerGuarantorEntity existingGuarantor = new ClnCustomerGuarantorEntity();
//        existingGuarantor.setGuarId("B001");
//        existingGuarantors.add(existingGuarantor);
//        when(clnCustomerGuarantorRepository.findAllByApplyId("TEST001")).thenReturn(existingGuarantors);
//
//        // 模擬 FNSCIF0000 回應
//        FNSCIF0000Tranrs fnsTranrs = new FNSCIF0000Tranrs();
//        fnsTranrs.setMaritalStatus("1");
//        fnsTranrs.setAddress1("測試地址");
//        fnsTranrs.setPostCode("100");
//        fnsTranrs.setBusinessPhone("1234");
//        ResponseTemplate<FNSCIF0000Tranrs> fnsResponse = new ResponseTemplate<>();
//        fnsResponse.setTranrs(fnsTranrs);
//        when(restTempHelper.postForEntity(any(), eq(FNSCIF0000Tranrs.class))).thenReturn(fnsResponse);
//
//        // 模擬 WMS 電文記錄查詢
//        ClnTxLogArchiveEntity archiveEntity = new ClnTxLogArchiveEntity();
//        String mockRecvData = "{" + "\"tranrs\": {" + "\"valCustlevel\": \"02\"," + "\"avgBal\": 2000000" + "}" + "}";
//        archiveEntity.setRecvData(mockRecvData);
//        when(cLnTxLogArchiveRepository.findFirstByMsgIdAndCaseNbrAndSendDataContainingOrderBySendtimeAsc("WMS-B-CUSTTYPEQ003", "TEST001",
//                "B001")).thenReturn(Optional.of(archiveEntity));
//
//        // 模擬 CUSTTYPEQ003 回應
//        CTNCINPTT001RecvDataVO dataModel = new CTNCINPTT001RecvDataVO();
//        CTNCINPTT001RecvDataTranrsVO tranrs = new CTNCINPTT001RecvDataTranrsVO();
//        tranrs.setValCustlevel("02");
//        tranrs.setAvgBal(new BigDecimal("2000000"));
//        dataModel.setTranrs(tranrs);
//        when(objectMapper.readValue(mockRecvData, CTNCINPTT001RecvDataVO.class)).thenReturn(dataModel);
//
//        // 模擬 GETKYCSTATQ002Tranrs 回應
//        GETKYCSTATQ002Tranrs getkycTranrsResponse = new GETKYCSTATQ002Tranrs();
//        MwHeaderResponse mwHeaderRes = new MwHeaderResponse();
//        mwHeaderRes.setMsgId("LIP-B-CTNCINPTT001");
//        mwHeaderRes.setReturnCode("0000");
//        ResponseTemplate<GETKYCSTATQ002Tranrs> getkycResponseTemplate = new ResponseTemplate<>();
//        getkycResponseTemplate.setMwHeaderResponse(mwHeaderRes);
//        getkycResponseTemplate.setTranrs(getkycTranrsResponse);
//
//        // 模擬案件主檔查詢
//        ClnCaseMainEntity caseMain = new ClnCaseMainEntity();
//        when(clnCaseMainRepository.findById("TEST001")).thenReturn(Optional.of(caseMain));
//
//        // 模擬案件子檔查詢
//        ClnCaseSubEntity caseSub = new ClnCaseSubEntity();
//        when(clnCaseSubRepository.findById("TEST001")).thenReturn(Optional.of(caseSub));
//
//        ResponseTemplate<EmptyDto> expectedResponse = new ResponseTemplate<>();
//        when(normalResponseFactory.genNormalResponse(any(EmptyDto.class), any(RequestTemplate.class))).thenReturn(expectedResponse);
//
//        // Act
//        ResponseTemplate<EmptyDto> result = service.inputInfoModify(req);
//
//        // Assert
//        // 驗證保證人資料處理
//        verify(clnCustomerGuarantorRepository).findAllByApplyId("TEST001");
//        verify(restTempHelper, times(1)).postForEntity(any(), eq(FNSCIF0000Tranrs.class));
//        verify(cLnTxLogArchiveRepository).findFirstByMsgIdAndCaseNbrAndSendDataContainingOrderBySendtimeAsc("WMS-B-CUSTTYPEQ003", "TEST001",
//                "B001");
//
//        // 驗證案件主檔和子檔更新
//        verify(clnCaseMainRepository).findById("TEST001");
//        verify(clnCaseSubRepository).findById("TEST001");
//
//        // 驗證資料處理器調用
//        verify(dataProcessor).processData(any(CTNCINPTT001SvcVO.class));
//
//        // 驗證回應
//        assertEquals(expectedResponse, result);
//    }
//
//    @Test
//    @DisplayName("測試 inputInfoModify - ActionType=M, ApplyProcess=5, idsToDelete 非空")
//    void testInputInfoModify_ActionTypeM_ApplyProcess5_idsToDelete() throws Exception {
//        // Arrange
//        RequestTemplate<CTNCINPTT001Tranrq> req = new RequestTemplate<>();
//        MwHeader mwHeader = new MwHeader();
//        mwHeader.setMsgId("LIP-B-CTNCINPTT001");
//        mwHeader.setSourceChannel("LON-LX-LIP-01");
//        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
//        tranrq.setActionType("M");
//        tranrq.setApplyId("TEST001");
//        tranrq.setEmpId("E001");
//        tranrq.setGageType("B");
//        req.setMwHeader(mwHeader);
//        req.setTranrq(tranrq);
//
//        // 設置新的借保人清單
//        List<CTNCINPTT001TranrqBorGuar> borGuarList = new ArrayList<>();
//        // 保留的借款人
//        CTNCINPTT001TranrqBorGuar borrower = createBorGuar("B001", "0", "3", "1");
//
//        borGuarList.add(borrower);
//        tranrq.setBorGuarList(borGuarList);
//        req.setTranrq(tranrq);
//
//        // 設置借保人清單
//        // 模擬現有的保證人資料
//        List<ClnCustomerGuarantorEntity> existingGuarantors = new ArrayList<>();
//        // 將被刪除的保證人
//        existingGuarantors.add(createExistingGuarantor("G001", "一般保證人1"));
//        existingGuarantors.add(createExistingGuarantor("G002", "一般保證人2"));
//        existingGuarantors.add(createExistingGuarantor("G003", "擔保品提供人"));
//        // 保留的借款人
//        existingGuarantors.add(createExistingGuarantor("B001", "借款人"));
//
//        when(clnCustomerGuarantorRepository.findAllByApplyId("TEST001")).thenReturn(existingGuarantors);
//
//        CTNCINPTT001TranrqInputBranchInfo inputBranchInfo = new CTNCINPTT001TranrqInputBranchInfo();
//        inputBranchInfo.setOriTm("LOAN,SLOAN");
//        inputBranchInfo.setOriNtm("CLIENT");
//        tranrq.setInputBranchInfo(inputBranchInfo);
//
//        // 模擬 FNSCIF0000 回應
//        FNSCIF0000Tranrs fnsTranrs = new FNSCIF0000Tranrs();
//        fnsTranrs.setBirthday("01012000");
//        fnsTranrs.setMaritalStatus("1");
//        fnsTranrs.setAddress1("測試地址");
//        fnsTranrs.setPostCode("100");
//        fnsTranrs.setBusinessPhone("123456789");
//        ResponseTemplate<FNSCIF0000Tranrs> fnsResponse = new ResponseTemplate<>();
//        fnsResponse.setTranrs(fnsTranrs);
//        when(restTempHelper.postForEntity(any(), eq(FNSCIF0000Tranrs.class))).thenReturn(fnsResponse);
//
//        // 模擬 WMS 電文記錄查詢
//        when(cLnTxLogArchiveRepository.findFirstByMsgIdAndCaseNbrAndSendDataContainingOrderBySendtimeAsc("WMS-B-CUSTTYPEQ003", "TEST001",
//                "B001")).thenReturn(Optional.empty());
//
//        // 模擬 CUSTTYPEQ003 回應
//        CUSTTYPEQ003Tranrs wmsResponse = new CUSTTYPEQ003Tranrs();
//        wmsResponse.setValCustlevel("01");
//        wmsResponse.setAvgBal(null);
//        MwHeaderResponse mwHeaderResponse = new MwHeaderResponse();
//        mwHeaderResponse.setMsgId("LIP-B-CTNCINPTT001");
//        mwHeaderResponse.setReturnCode("0000");
//        ResponseTemplate<CUSTTYPEQ003Tranrs> wmsResponseTemplate = new ResponseTemplate<>();
//        wmsResponseTemplate.setMwHeaderResponse(mwHeaderResponse);
//        wmsResponseTemplate.setTranrs(wmsResponse);
//        when(restTempHelper.postForEntity(any(), eq(CUSTTYPEQ003Tranrs.class))).thenReturn(wmsResponseTemplate);
//
//        // 模擬 GETKYCSTATQ002Tranrs 回應
//        GETKYCSTATQ002Tranrs getkycTranrsResponse = new GETKYCSTATQ002Tranrs();
//        getkycTranrsResponse.setFlgIsproinvestor("0");
//        MwHeaderResponse mwHeaderRes = new MwHeaderResponse();
//        mwHeaderRes.setMsgId("LIP-B-CTNCINPTT001");
//        mwHeaderRes.setReturnCode("0000");
//        ResponseTemplate<GETKYCSTATQ002Tranrs> getkycResponseTemplate = new ResponseTemplate<>();
//        getkycResponseTemplate.setMwHeaderResponse(mwHeaderRes);
//        getkycResponseTemplate.setTranrs(getkycTranrsResponse);
//        when(restTempHelper.postForEntity(any(), eq(GETKYCSTATQ002Tranrs.class))).thenReturn(getkycResponseTemplate);
//
//        // 模擬案件主檔查詢
//        ClnCaseMainEntity caseMain = new ClnCaseMainEntity();
//        when(clnCaseMainRepository.findById("TEST001")).thenReturn(Optional.of(caseMain));
//
//        // 模擬案件子檔查詢
//        ClnCaseSubEntity caseSub = new ClnCaseSubEntity();
//        when(clnCaseSubRepository.findById("TEST001")).thenReturn(Optional.of(caseSub));
//
//        ResponseTemplate<EmptyDto> expectedResponse = new ResponseTemplate<>();
//        when(normalResponseFactory.genNormalResponse(any(EmptyDto.class), any(RequestTemplate.class))).thenReturn(expectedResponse);
//
//        // Act
//        ResponseTemplate<EmptyDto> result = service.inputInfoModify(req);
//
//        // Assert
//        // 驗證保證人資料處理
//        verify(clnCustomerGuarantorRepository).findAllByApplyId("TEST001");
//        verify(restTempHelper, times(1)).postForEntity(any(), eq(FNSCIF0000Tranrs.class));
//        verify(cLnTxLogArchiveRepository).findFirstByMsgIdAndCaseNbrAndSendDataContainingOrderBySendtimeAsc("WMS-B-CUSTTYPEQ003", "TEST001",
//                "B001");
//
//        // 驗證案件主檔和子檔更新
//        verify(clnCaseMainRepository).findById("TEST001");
//        verify(clnCaseSubRepository).findById("TEST001");
//
//        // 驗證資料處理器調用
//        verify(dataProcessor).processData(any(CTNCINPTT001SvcVO.class));
//
//        // 驗證回應
//        assertEquals(expectedResponse, result);
//    }
//
//    @Test
//    @DisplayName("測試 inputInfoModify - ActionType=M, ApplyProcess=5, 生日格式錯誤")
//    void testInputInfoModify_ActionTypeM_ApplyProcess5_InvalidBirthday() throws Exception {
//        // Arrange
//        RequestTemplate<CTNCINPTT001Tranrq> req = new RequestTemplate<>();
//        MwHeader mwHeader = new MwHeader();
//        mwHeader.setMsgId("LIP-B-CTNCINPTT001");
//        mwHeader.setSourceChannel("LON-LX-LIP-01");
//        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
//        tranrq.setActionType("M");
//        tranrq.setApplyId("TEST001");
//        tranrq.setEmpId("E001");
//        tranrq.setGageType("B");
//        req.setMwHeader(mwHeader);
//        req.setTranrq(tranrq);
//
//        // 設置借保人清單
//        List<CTNCINPTT001TranrqBorGuar> borGuarList = new ArrayList<>();
//        CTNCINPTT001TranrqBorGuar borGuar1 = new CTNCINPTT001TranrqBorGuar();
//        borGuar1.setBorGuarId("B001");
//        borGuar1.setBorGuarName("借保人1");
//        borGuar1.setType("0");
//        borGuar1.setBorGuarKind("3");
//        borGuar1.setIsGageOwner("0");
//        borGuarList.add(borGuar1);
//        tranrq.setBorGuarList(borGuarList);
//
//        CTNCINPTT001TranrqInputBranchInfo inputBranchInfo = new CTNCINPTT001TranrqInputBranchInfo();
//        tranrq.setInputBranchInfo(inputBranchInfo);
//
//        // 模擬現有保證人資料
//        when(clnCustomerGuarantorRepository.findAllByApplyId("TEST001")).thenReturn(new ArrayList<>());
//
//        // 模擬 FNSCIF0000 回應 - 錯誤的生日格式
//        FNSCIF0000Tranrs fnsTranrs = new FNSCIF0000Tranrs();
//        fnsTranrs.setBirthday("invalid_date"); // 錯誤的日期格式
//        fnsTranrs.setMaritalStatus("1");
//        ResponseTemplate<FNSCIF0000Tranrs> fnsResponse = new ResponseTemplate<>();
//        fnsResponse.setTranrs(fnsTranrs);
//        when(restTempHelper.postForEntity(any(), eq(FNSCIF0000Tranrs.class))).thenReturn(fnsResponse);
//
//        // 模擬 WMS 電文記錄查詢
//        when(cLnTxLogArchiveRepository.findFirstByMsgIdAndCaseNbrAndSendDataContainingOrderBySendtimeAsc("WMS-B-CUSTTYPEQ003", "TEST001",
//                "B001")).thenReturn(Optional.empty());
//
//        // 模擬 CUSTTYPEQ003 回應
//        CUSTTYPEQ003Tranrs wmsResponse = new CUSTTYPEQ003Tranrs();
//        wmsResponse.setValCustlevel("01");
//        wmsResponse.setAvgBal(new BigDecimal("1000000"));
//        MwHeaderResponse mwHeaderResponse = new MwHeaderResponse();
//        mwHeaderResponse.setMsgId("LIP-B-CTNCINPTT001");
//        mwHeaderResponse.setReturnCode("0000");
//        ResponseTemplate<CUSTTYPEQ003Tranrs> wmsResponseTemplate = new ResponseTemplate<>();
//        wmsResponseTemplate.setMwHeaderResponse(mwHeaderResponse);
//        wmsResponseTemplate.setTranrs(wmsResponse);
//        when(restTempHelper.postForEntity(any(), eq(CUSTTYPEQ003Tranrs.class))).thenReturn(wmsResponseTemplate);
//
//        // 模擬 GETKYCSTATQ002Tranrs 回應
//        GETKYCSTATQ002Tranrs getkycTranrsResponse = new GETKYCSTATQ002Tranrs();
//        getkycTranrsResponse.setFlgIsproinvestor("0");
//        MwHeaderResponse mwHeaderRes = new MwHeaderResponse();
//        mwHeaderRes.setMsgId("LIP-B-CTNCINPTT001");
//        mwHeaderRes.setReturnCode("0000");
//        ResponseTemplate<GETKYCSTATQ002Tranrs> getkycResponseTemplate = new ResponseTemplate<>();
//        getkycResponseTemplate.setMwHeaderResponse(mwHeaderRes);
//        getkycResponseTemplate.setTranrs(getkycTranrsResponse);
//        when(restTempHelper.postForEntity(any(), eq(GETKYCSTATQ002Tranrs.class))).thenReturn(getkycResponseTemplate);
//
//        // 模擬案件主檔查詢
//        ClnCaseMainEntity caseMain = new ClnCaseMainEntity();
//        when(clnCaseMainRepository.findById("TEST001")).thenReturn(Optional.of(caseMain));
//
//        // 模擬案件子檔查詢
//        ClnCaseSubEntity caseSub = new ClnCaseSubEntity();
//        when(clnCaseSubRepository.findById("TEST001")).thenReturn(Optional.of(caseSub));
//
//        ResponseTemplate<EmptyDto> expectedResponse = new ResponseTemplate<>();
//        when(normalResponseFactory.genNormalResponse(any(EmptyDto.class), any(RequestTemplate.class))).thenReturn(expectedResponse);
//
//        // Act
//        ResponseTemplate<EmptyDto> result = service.inputInfoModify(req);
//
//        // Assert
//        verify(dataProcessor).processData(any(CTNCINPTT001SvcVO.class));
//        assertNotNull(result);
//    }
//
//    @Test
//    @DisplayName("測試 inputInfoModify - ActionType=M, ApplyProcess=5, 平均餘額為0")
//    void testInputInfoModify_ActionTypeM_ApplyProcess5_ZeroAvgBalance() throws Exception {
//        // Arrange
//        RequestTemplate<CTNCINPTT001Tranrq> req = new RequestTemplate<>();
//        MwHeader mwHeader = new MwHeader();
//        mwHeader.setMsgId("LIP-B-CTNCINPTT001");
//        mwHeader.setSourceChannel("LON-LX-LIP-01");
//        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
//        tranrq.setActionType("M");
//        tranrq.setApplyId("TEST001");
//        tranrq.setEmpId("E001");
//        tranrq.setGageType("B");
//        req.setMwHeader(mwHeader);
//        req.setTranrq(tranrq);
//
//        // 設置借保人清單
//        List<CTNCINPTT001TranrqBorGuar> borGuarList = new ArrayList<>();
//        CTNCINPTT001TranrqBorGuar borGuar1 = new CTNCINPTT001TranrqBorGuar();
//        borGuar1.setBorGuarId("B001");
//        borGuar1.setBorGuarName("借保人1");
//        borGuar1.setType("1");
//        borGuar1.setBorGuarKind("2");
//        borGuar1.setIsGageOwner("0");
//        borGuarList.add(borGuar1);
//        tranrq.setBorGuarList(borGuarList);
//
//        CTNCINPTT001TranrqInputBranchInfo inputBranchInfo = new CTNCINPTT001TranrqInputBranchInfo();
//        tranrq.setInputBranchInfo(inputBranchInfo);
//
//        // 模擬現有保證人資料
//        when(clnCustomerGuarantorRepository.findAllByApplyId("TEST001")).thenReturn(new ArrayList<>());
//
//        // 模擬 FNSCIF0000 回應
//        FNSCIF0000Tranrs fnsTranrs = new FNSCIF0000Tranrs();
//        fnsTranrs.setBirthday("01012000");
//        ResponseTemplate<FNSCIF0000Tranrs> fnsResponse = new ResponseTemplate<>();
//        fnsResponse.setTranrs(fnsTranrs);
//        when(restTempHelper.postForEntity(any(), eq(FNSCIF0000Tranrs.class))).thenReturn(fnsResponse);
//
//        // 模擬 CUSTTYPEQ003 回應 - 平均餘額為0
//        when(cLnTxLogArchiveRepository.findFirstByMsgIdAndCaseNbrAndSendDataContainingOrderBySendtimeAsc(any(), any(), any()))
//                .thenReturn(Optional.empty());
//
//        CUSTTYPEQ003Tranrs wmsResponse = new CUSTTYPEQ003Tranrs();
//        wmsResponse.setValCustlevel("01");
//        wmsResponse.setAvgBal(BigDecimal.ZERO); // 餘額為0
//        MwHeaderResponse mwHeaderResponse = new MwHeaderResponse();
//        mwHeaderResponse.setReturnCode("0000");
//        ResponseTemplate<CUSTTYPEQ003Tranrs> wmsResponseTemplate = new ResponseTemplate<>();
//        wmsResponseTemplate.setMwHeaderResponse(mwHeaderResponse);
//        wmsResponseTemplate.setTranrs(wmsResponse);
//        when(restTempHelper.postForEntity(any(), eq(CUSTTYPEQ003Tranrs.class))).thenReturn(wmsResponseTemplate);
//
//        // 模擬其他回應
//        GETKYCSTATQ002Tranrs getkycTranrsResponse = new GETKYCSTATQ002Tranrs();
//        getkycTranrsResponse.setFlgIsproinvestor("1");
//        ResponseTemplate<GETKYCSTATQ002Tranrs> getkycResponseTemplate = new ResponseTemplate<>();
//        getkycResponseTemplate.setMwHeaderResponse(mwHeaderResponse);
//        getkycResponseTemplate.setTranrs(getkycTranrsResponse);
//        when(restTempHelper.postForEntity(any(), eq(GETKYCSTATQ002Tranrs.class))).thenReturn(getkycResponseTemplate);
//
//        when(clnCaseMainRepository.findById("TEST001")).thenReturn(Optional.of(new ClnCaseMainEntity()));
//        when(clnCaseSubRepository.findById("TEST001")).thenReturn(Optional.of(new ClnCaseSubEntity()));
//
//        ResponseTemplate<EmptyDto> expectedResponse = new ResponseTemplate<>();
//        when(normalResponseFactory.genNormalResponse(any(EmptyDto.class), any(RequestTemplate.class))).thenReturn(expectedResponse);
//
//        // Act
//        ResponseTemplate<EmptyDto> result = service.inputInfoModify(req);
//
//        // Assert
//        verify(dataProcessor).processData(any(CTNCINPTT001SvcVO.class));
//        assertEquals(expectedResponse, result);
//    }
//
//    @Test
//    @DisplayName("測試 inputInfoModify - ActionType=M, ApplyProcess=0")
//    void testInputInfoModify_ApplyProcess0_NoUpdateActions() throws Exception {
//        // Arrange
//        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
//        tranrq.setActionType("M");
//        tranrq.setApplyId("TEST_APPLY_ID");
//        tranrq.setEmpId("EMP001");
//        tranrq.setBranchId("BR001");
//
//        CTNCINPTT001TranrqInputBranchInfo branchInfo = new CTNCINPTT001TranrqInputBranchInfo();
//        tranrq.setInputBranchInfo(branchInfo);
//
//        RequestTemplate<CTNCINPTT001Tranrq> request = new RequestTemplate<>();
//        request.setTranrq(tranrq);
//
//        when(commonUtil.getCaseHistory(any(), any(), any(), any(), any(), any())).thenReturn(new ClnCaseHistoryEntity());
//
//        // Act
//        service.inputInfoModify(request);
//
//        // Assert
//        ArgumentCaptor<CTNCINPTT001SvcVO> voCaptor = ArgumentCaptor.forClass(CTNCINPTT001SvcVO.class);
//        verify(dataProcessor).processData(voCaptor.capture());
//
//        CTNCINPTT001SvcVO vo = voCaptor.getValue();
//        assertTrue(vo.getCaseMainEntities().isEmpty());
//        assertTrue(vo.getCustomerGuarantorEntities().isEmpty());
//        assertTrue(vo.getRepayFinAssetsEntities().isEmpty());
//        assertEquals(1, vo.getCaseHistoryEntities().size());
//    }
//
//    @Test
//    @DisplayName("測試 saveOrUpdateCustomerGuarantor - 已存在保證人且 GuarKind1 = '1'")
//    void testSaveOrUpdateCustomerGuarantor_ExistingGuarantor_GuarKind1IsZero() {
//        // Arrange
//        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
//        tranrq.setApplyId("TEST001");
//        tranrq.setEmpId("EMP001");
//
//        CTNCINPTT001TranrqBorGuar guar = new CTNCINPTT001TranrqBorGuar();
//        guar.setBorGuarId("G001");
//        guar.setBorGuarName("測試保證人");
//        guar.setBorGuarKind("1");
//        guar.setType("1");
//        guar.setIsGageOwner("0");
//
//        FNSCIF0000Tranrs fnsTranrs = new FNSCIF0000Tranrs();
//        fnsTranrs.setBirthday("01012000");
//        fnsTranrs.setEmailAddress("test@example.com");
//        fnsTranrs.setMaritalStatus("1");
//
//        CTNCINPTT001SvcVO vo = new CTNCINPTT001SvcVO();
//
//        // Mock: 保證人已存在
//        ClnCustomerGuarantorEntity existingEntity = new ClnCustomerGuarantorEntity();
//        existingEntity.setGuarId("G001");
//        existingEntity.setGuarName("舊保證人");
//        when(clnCustomerGuarantorRepository.findById(new ClnCustomerGuarantorPKEntity("TEST001", "G001")))
//                .thenReturn(Optional.of(existingEntity));
//
//        // Act
//        service.processFullCustomerData(tranrq, guar, fnsTranrs, "01", BigDecimal.ZERO, vo);
//
//        // Assert
//        List<ClnCustomerGuarantorEntity> result = vo.getCustomerGuarantorEntities();
//        assertEquals(1, result.size());
//        ClnCustomerGuarantorEntity entity = result.get(0);
//        assertEquals("1", entity.getGuarKind1());
//        assertEquals("G001", entity.getGuarId());
//        assertEquals("測試保證人", entity.getGuarName());
//    }
//
//    @Test
//    @DisplayName("測試 inputInfoModify - ActionType=X")
//    void testInputInfoModify_ActionTypeIsX() throws Exception {
//        // Arrange
//        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
//        tranrq.setActionType("X");
//        tranrq.setApplyId("TEST_APPLY_ID");
//        tranrq.setEmpId("EMP001");
//        tranrq.setBranchId("BR001");
//
//        RequestTemplate<CTNCINPTT001Tranrq> request = new RequestTemplate<>();
//        request.setTranrq(tranrq);
//
//        // Act
//        service.inputInfoModify(request);
//
//        // Assert
//        verify(dataProcessor).processData(any());
//    }
//
//    @Test
//    @DisplayName("測試 saveOrUpdateCustomerInfo - 已存在客戶資料")
//    void testSaveOrUpdateCustomerInfo_ExistingCustomerInfo() {
//        // Arrange
//        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
//        tranrq.setApplyId("TEST001");
//        tranrq.setEmpId("EMP001");
//
//        CTNCINPTT001TranrqBorGuar guar = new CTNCINPTT001TranrqBorGuar();
//        guar.setBorGuarId("C001");
//        guar.setBorGuarName("測試客戶");
//        guar.setBorGuarKind("3");
//        guar.setType("0");
//        guar.setIsGageOwner("1");
//
//        FNSCIF0000Tranrs fnsTranrs = new FNSCIF0000Tranrs();
//        fnsTranrs.setBirthday("01012000");
//        fnsTranrs.setEmailAddress("test@example.com");
//        fnsTranrs.setMaritalStatus("1");
//        fnsTranrs.setAddress1("台北市信義路");
//        fnsTranrs.setPostCode("110");
//
//        CTNCINPTT001SvcVO vo = new CTNCINPTT001SvcVO();
//
//        // Mock: 客戶資料已存在
//        ClnCustomerInfoEntity existingEntity = new ClnCustomerInfoEntity();
//        existingEntity.setCustomerId("C001");
//        existingEntity.setCustomerType("1");
//        existingEntity.setApplyId("TEST001");
//        when(clnCustomerInfoRepository.findById(any(ClnCustomerInfoPKEntity.class))).thenReturn(Optional.of(existingEntity));
//
//        // Act
//        service.processFullCustomerData(tranrq, guar, fnsTranrs, "01", BigDecimal.ZERO, vo);
//
//        // Assert
//        List<ClnCustomerInfoEntity> result = vo.getCustomerInfoEntities();
//        assertEquals(1, result.size());
//        ClnCustomerInfoEntity entity = result.get(0);
//        assertEquals("C001", entity.getCustomerId());
//        assertEquals("測試客戶", entity.getCustomerName());
//        assertEquals("01", entity.getCustLevel());
//        assertEquals(BigDecimal.ZERO, entity.getAvgbal());
//    }
//
//    @Test
//    @DisplayName("測試 ApplyProcess=5 - idsToUpdate 與 idsToInsert 皆為空")
//    void testApplyProcess5_IdsToUpdateInsertEmpty() throws Exception {
//        // Arrange
//        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
//        tranrq.setApplyId("TEST001");
//        tranrq.setActionType("M");
//        tranrq.setEmpId("EMP001");
//
//        CTNCINPTT001TranrqInputBranchInfo branchInfo = new CTNCINPTT001TranrqInputBranchInfo();
//        branchInfo.setAgentId("A001");
//        branchInfo.setRemitBranchId("B001");
//        tranrq.setInputBranchInfo(branchInfo);
//
//        // existing 保證人 ID = A
//        ClnCustomerGuarantorEntity existing = new ClnCustomerGuarantorEntity();
//        existing.setGuarId("A");
//        when(clnCustomerGuarantorRepository.findAllByApplyId("TEST001")).thenReturn(Arrays.asList(existing));
//
//        // 新的保證人 ID = A → 完全相同 → 不更新、不新增
//        CTNCINPTT001TranrqBorGuar guar = new CTNCINPTT001TranrqBorGuar();
//        guar.setBorGuarId("A");
//        guar.setBorGuarKind("1");
//        guar.setType("1");
//        guar.setIsGageOwner("0");
//        List<CTNCINPTT001TranrqBorGuar> borGuarList = new ArrayList<>();
//        borGuarList.add(guar);
//        tranrq.setBorGuarList(new ArrayList<>());
//
//        RequestTemplate<CTNCINPTT001Tranrq> req = new RequestTemplate<>();
//        req.setTranrq(tranrq);
//
//        when(normalResponseFactory.genNormalResponse(any(), any())).thenReturn(new ResponseTemplate<>());
//        when(commonUtil.getCaseHistory(any(), any(), any(), any(), any(), any())).thenReturn(new ClnCaseHistoryEntity());
//
//        // Act
//        ResponseTemplate<EmptyDto> result = service.inputInfoModify(req);
//
//        // Assert
//        verify(dataProcessor).processData(any());
//        assertNotNull(result);
//    }
//
//    @Test
//    @DisplayName("測試 saveRepayFinAssets - 條件不成立不執行")
//    void testSaveRepayFinAssets_ConditionNotMet() {
//        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
//        tranrq.setApplyId("TEST001");
//        tranrq.setEmpId("EMP001");
//
//        CTNCINPTT001TranrqBorGuar guar = new CTNCINPTT001TranrqBorGuar();
//        guar.setBorGuarId("X001");
//        guar.setBorGuarName("不符合條件的保證人");
//        guar.setType("0");
//        guar.setBorGuarKind("2"); // ≠ "3"
//        guar.setIsGageOwner("0");
//
//        FNSCIF0000Tranrs fnsTranrs = new FNSCIF0000Tranrs();
//        fnsTranrs.setBirthday("01012000");
//
//        CTNCINPTT001SvcVO vo = new CTNCINPTT001SvcVO();
//
//        // Mock: 保證人不存在
//        when(clnCustomerGuarantorRepository.findById(new ClnCustomerGuarantorPKEntity("TEST001", "X001"))).thenReturn(Optional.empty());
//        when(clnCustomerInfoRepository.findById(any(ClnCustomerInfoPKEntity.class))).thenReturn(Optional.empty());
//
//        // Act
//        service.processFullCustomerData(tranrq, guar, fnsTranrs, "01", BigDecimal.TEN, vo);
//
//        // Assert
//        assertTrue(vo.getRepayFinAssetsEntities().isEmpty()); // 不應新增任何資料
//    }
//
//    @Test
//    @DisplayName("測試 valCustlevels 條件不成立 - type=0 且 kind≠3")
//    void testValCustlevelsConditionNotMet() throws Exception {
//        // Arrange
//        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
//        tranrq.setApplyId("TEST001");
//        tranrq.setEmpId("EMP001");
//        tranrq.setActionType("M");
//
//        CTNCINPTT001TranrqInputBranchInfo branchInfo = new CTNCINPTT001TranrqInputBranchInfo();
//        branchInfo.setAgentId("A001");
//        branchInfo.setRemitBranchId("B001");
//        tranrq.setInputBranchInfo(branchInfo);
//
//        CTNCINPTT001TranrqBorGuar guar = new CTNCINPTT001TranrqBorGuar();
//        guar.setBorGuarId("B001");
//        guar.setBorGuarName("測試人員");
//        guar.setType("0");
//        guar.setBorGuarKind("2"); // 不符合條件
//        guar.setIsGageOwner("0");
//
//        List<CTNCINPTT001TranrqBorGuar> borGuarList = new ArrayList<>();
//        borGuarList.add(guar);
//        tranrq.setBorGuarList(borGuarList);
//
//        RequestTemplate<CTNCINPTT001Tranrq> req = new RequestTemplate<>();
//        req.setTranrq(tranrq);
//
//        // 模擬 WMS 有紀錄
//        ClnTxLogArchiveEntity archiveEntity = new ClnTxLogArchiveEntity();
//        String mockRecvData = "{\"tranrs\": {\"valCustlevel\": \"02\", \"avgBal\": 2000000}}";
//        archiveEntity.setRecvData(mockRecvData);
//        when(cLnTxLogArchiveRepository.findFirstByMsgIdAndCaseNbrAndSendDataContainingOrderBySendtimeAsc(any(), any(), any()))
//                .thenReturn(Optional.of(archiveEntity));
//
//        CTNCINPTT001RecvDataVO dataModel = new CTNCINPTT001RecvDataVO();
//        CTNCINPTT001RecvDataTranrsVO tranrsVO = new CTNCINPTT001RecvDataTranrsVO();
//        tranrsVO.setValCustlevel("02");
//        tranrsVO.setAvgBal(new BigDecimal("2000000"));
//        dataModel.setTranrs(tranrsVO);
//        when(objectMapper.readValue(mockRecvData, CTNCINPTT001RecvDataVO.class)).thenReturn(dataModel);
//
//        when(clnCustomerGuarantorRepository.findAllByApplyId("TEST001")).thenReturn(new ArrayList<>());
//        when(normalResponseFactory.genNormalResponse(any(), any())).thenReturn(new ResponseTemplate<>());
//        when(commonUtil.getCaseHistory(any(), any(), any(), any(), any(), any())).thenReturn(new ClnCaseHistoryEntity());
//
//        // Act
//        service.inputInfoModify(req);
//
//        // Assert
//        ArgumentCaptor<CTNCINPTT001SvcVO> voCaptor = ArgumentCaptor.forClass(CTNCINPTT001SvcVO.class);
//        verify(dataProcessor).processData(voCaptor.capture());
//    }
//
//    // 輔助方法
//    private CTNCINPTT001TranrqBorGuar createBorGuar(String id, String type, String kind, String isGageOwner) {
//        CTNCINPTT001TranrqBorGuar borGuar = new CTNCINPTT001TranrqBorGuar();
//        borGuar.setBorGuarId(id);
//        borGuar.setType(type);
//        borGuar.setBorGuarKind(kind);
//        borGuar.setIsGageOwner(isGageOwner);
//        borGuar.setBorGuarName("測試人員" + id);
//        return borGuar;
//    }
//
//    private ClnCustomerGuarantorEntity createExistingGuarantor(String guarId, String name) {
//        ClnCustomerGuarantorEntity guarantor = new ClnCustomerGuarantorEntity();
//        guarantor.setGuarId(guarId);
//        guarantor.setGuarName(name);
//        guarantor.setApplyId("TEST001");
//        return guarantor;
//    }
//}
////package lip.svc.cln.transaction.service.impl;
////
////import static org.junit.jupiter.api.Assertions.assertEquals;
////import static org.junit.jupiter.api.Assertions.assertNotNull;
////import static org.junit.jupiter.api.Assertions.assertTrue;
////import static org.mockito.ArgumentMatchers.any;
////import static org.mockito.ArgumentMatchers.eq;
////import static org.mockito.Mockito.times;
////import static org.mockito.Mockito.verify;
////import static org.mockito.Mockito.when;
////
////import java.math.BigDecimal;
////import java.util.ArrayList;
////import java.util.Arrays;
////import java.util.List;
////import java.util.Optional;
////
////import org.junit.jupiter.api.DisplayName;
////import org.junit.jupiter.api.Test;
////import org.mockito.ArgumentCaptor;
////import org.mockito.InjectMocks;
////import org.mockito.Mock;
////
////import cub.lip.lib.common.dto.base.EmptyDto;
////import cub.lip.lib.common.dto.base.MwHeader;
////import cub.lip.lib.common.dto.base.MwHeaderResponse;
////import cub.lip.lib.common.dto.base.RequestTemplate;
////import cub.lip.lib.common.dto.base.ResponseTemplate;
////import cub.lip.svc.cln.transaction.check.CaseCheck;
////import cub.lip.svc.cln.transaction.dto.ctn.CTNCINPTT001Tranrq;
////import cub.lip.svc.cln.transaction.dto.ctn.CTNCINPTT001TranrqBorGuar;
////import cub.lip.svc.cln.transaction.dto.ctn.CTNCINPTT001TranrqInputBranchInfo;
////import cub.lip.svc.cln.transaction.dto.fns.FNSCIF0000Tranrs;
////import cub.lip.svc.cln.transaction.dto.wms.CUSTTYPEQ003Tranrs;
////import cub.lip.svc.cln.transaction.dto.wms.GETKYCSTATQ002Tranrs;
////import cub.lip.svc.cln.transaction.entity.base.ClnCaseHistoryEntity;
////import cub.lip.svc.cln.transaction.entity.cln.ClnCaseMainEntity;
////import cub.lip.svc.cln.transaction.entity.cln.ClnCaseSubEntity;
////import cub.lip.svc.cln.transaction.entity.cln.ClnCustomerGuarantorEntity;
////import cub.lip.svc.cln.transaction.entity.cln.ClnCustomerGuarantorPKEntity;
////import cub.lip.svc.cln.transaction.entity.cln.ClnCustomerInfoEntity;
////import cub.lip.svc.cln.transaction.entity.cln.ClnCustomerInfoPKEntity;
////import cub.lip.svc.cln.transaction.entity.base.ClnTxLogArchiveEntity;
////import cub.lip.svc.cln.transaction.repo.ClnCaseMainRepository;
////import cub.lip.svc.cln.transaction.repo.ClnCaseSubRepository;
////import cub.lip.svc.cln.transaction.repo.ClnCustomerGuarantorRepository;
////import cub.lip.svc.cln.transaction.repo.ClnCustomerInfoRepository;
////import cub.lip.svc.cln.transaction.repo.ClnRepayFinAssetsRepository;
////import cub.lip.svc.cln.transaction.repo.base.ClnTxLogArchiveRepository;
////import cub.lip.svc.cln.transaction.svc.dataprocessor.CTNCINPTT001DataProcessor;
////import cub.lip.svc.cln.transaction.svc.dataprocessor.vo.CTNCINPTT001RecvDataTranrsVO;
////import cub.lip.svc.cln.transaction.svc.dataprocessor.vo.CTNCINPTT001RecvDataVO;
////import cub.lip.svc.cln.transaction.svc.dataprocessor.vo.CTNCINPTT001SvcVO;
////import cub.lip.svc.cln.transaction.svc.impl.CTNCINPTT001SvcImpl;
////import lip.svc.cln.transaction.service.BaseTest;
////
/////**
//// * LIP-B-CTNCINPTT001 進件輸入維護（單元測試）
//// *
//// * @author 00550352
//// */
////class CTNCINPTT001SvcImplTest extends BaseTest {
////
////    @InjectMocks
////    private CTNCINPTT001SvcImpl service;
////
////    @Mock
////    private CTNCINPTT001DataProcessor dataProcessor;
////
////    @Mock
////    private ClnCaseMainRepository clnCaseMainRepository;
////
////    @Mock
////    private ClnCustomerGuarantorRepository clnCustomerGuarantorRepository;
////
////    @Mock
////    private ClnRepayFinAssetsRepository clnRepayFinAssetsRepository;
////
////    @Mock
////    private ClnCustomerInfoRepository clnCustomerInfoRepository;
////
////    @Mock
////    private ClnTxLogArchiveRepository cLnTxLogArchiveRepository;
////
////    @Mock
////    private ClnCaseSubRepository clnCaseSubRepository;
////
////    @Mock
////    private CaseCheck caseCheck;
////
////    @Test
////    @DisplayName("測試 inputInfoModify - ActionType=M, ApplyProcess=70")
////    void testInputInfoModify_ActionTypeM_ApplyProcess70() throws Exception {
////        // Arrange
////        RequestTemplate<CTNCINPTT001Tranrq> req = new RequestTemplate<>();
////        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
////        tranrq.setActionType("M");
////        tranrq.setApplyId("TEST001");
////
////        CTNCINPTT001TranrqInputBranchInfo branchInfo = new CTNCINPTT001TranrqInputBranchInfo();
////        branchInfo.setAgentId("A001");
////        branchInfo.setAgentName("測試代理人");
////        branchInfo.setAgentBranch("分行1");
////        branchInfo.setReferralId("R001");
////        branchInfo.setReferralName("轉介人1");
////        branchInfo.setRemitBranchId("B001");
////
////        tranrq.setInputBranchInfo(branchInfo);
////        req.setTranrq(tranrq);
////
////        ClnCaseMainEntity caseMain = new ClnCaseMainEntity();
////        when(clnCaseMainRepository.findById("TEST001")).thenReturn(Optional.of(caseMain));
////
////        ResponseTemplate<EmptyDto> expectedResponse = new ResponseTemplate<>();
////        when(normalResponseFactory.genNormalResponse(any(EmptyDto.class), any(RequestTemplate.class))).thenReturn(expectedResponse);
////
////        // Act
////        ResponseTemplate<EmptyDto> result = service.inputInfoModify(req);
////
////        // Assert
////        verify(clnCaseMainRepository).findById("TEST001");
////        verify(dataProcessor).processData(any(CTNCINPTT001SvcVO.class));
////        assertEquals(expectedResponse, result);
////
////        assertEquals("A001", caseMain.getAgentId());
////        assertEquals("測試代理人", caseMain.getAgentName());
////        assertEquals("分行1", caseMain.getAgentBranch());
////        assertEquals("R001", caseMain.getReferralId());
////        assertEquals("轉介人1", caseMain.getReferralName());
////        assertEquals("B001", caseMain.getIntroBranch());
////    }
////
////    @Test
////    @DisplayName("測試 inputInfoModify - ActionType=M, ApplyProcess=71")
////    void testInputInfoModify_ActionTypeM_ApplyProcess71() throws Exception {
////        // Arrange
////        RequestTemplate<CTNCINPTT001Tranrq> req = new RequestTemplate<>();
////        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
////        tranrq.setActionType("M");
////        tranrq.setApplyId("TEST001");
////
////        CTNCINPTT001TranrqInputBranchInfo branchInfo = new CTNCINPTT001TranrqInputBranchInfo();
////        branchInfo.setAgentId("A001");
////        branchInfo.setAgentName("測試代理人");
////        branchInfo.setAgentBranch("分行1");
////        branchInfo.setReferralId("R001");
////        branchInfo.setReferralName("轉介人1");
////        branchInfo.setRemitBranchId("B001");
////
////        tranrq.setInputBranchInfo(branchInfo);
////        req.setTranrq(tranrq);
////
////        ClnCaseMainEntity caseMain = new ClnCaseMainEntity();
////        when(clnCaseMainRepository.findById("TEST001")).thenReturn(Optional.of(caseMain));
////
////        ResponseTemplate<EmptyDto> expectedResponse = new ResponseTemplate<>();
////        when(normalResponseFactory.genNormalResponse(any(EmptyDto.class), any(RequestTemplate.class))).thenReturn(expectedResponse);
////
////        // Act
////        ResponseTemplate<EmptyDto> result = service.inputInfoModify(req);
////
////        // Assert
////        verify(clnCaseMainRepository).findById("TEST001");
////        verify(dataProcessor).processData(any(CTNCINPTT001SvcVO.class));
////        assertEquals(expectedResponse, result);
////
////        assertEquals("A001", caseMain.getAgentId());
////        assertEquals("測試代理人", caseMain.getAgentName());
////        assertEquals("分行1", caseMain.getAgentBranch());
////        assertEquals("R001", caseMain.getReferralId());
////        assertEquals("轉介人1", caseMain.getReferralName());
////        assertEquals("B001", caseMain.getIntroBranch());
////    }
////
////    @Test
////    @DisplayName("測試 inputInfoModify - ActionType=D")
////    void testInputInfoModify_ActionTypeD() throws Exception {
////        // Arrange
////        RequestTemplate<CTNCINPTT001Tranrq> req = new RequestTemplate<>();
////        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
////        tranrq.setActionType("D");
////        tranrq.setApplyId("TEST001");
////        tranrq.setEmpId("E001");
////        tranrq.setBranchId("B001");
////        req.setTranrq(tranrq);
////
////        ClnCaseHistoryEntity historyEntity = new ClnCaseHistoryEntity();
////        when(commonUtil.getCaseHistory("TEST001", "新貸/增貸進件", "修改", "E001", "B001", ClnCaseHistoryEntity.class)).thenReturn(historyEntity);
////
////        ResponseTemplate<EmptyDto> expectedResponse = new ResponseTemplate<>();
////        when(normalResponseFactory.genNormalResponse(any(EmptyDto.class), any(RequestTemplate.class))).thenReturn(expectedResponse);
////
////        // Act
////        ResponseTemplate<EmptyDto> result = service.inputInfoModify(req);
////
////        // Assert
////        verify(commonUtil).getCaseHistory("TEST001", "新貸/增貸進件", "修改", "E001", "B001", ClnCaseHistoryEntity.class);
////        verify(dataProcessor).processData(any(CTNCINPTT001SvcVO.class));
////        assertEquals(expectedResponse, result);
////    }
////
////    @Test
////    @DisplayName("測試 inputInfoModify - ActionType=M, ApplyProcess=5, WMS有紀錄")
////    void testInputInfoModify_ActionTypeM_ApplyProcess5_WMS() throws Exception {
////        // Arrange
////        RequestTemplate<CTNCINPTT001Tranrq> req = new RequestTemplate<>();
////        MwHeader mwHeader = new MwHeader();
////        mwHeader.setMsgId("LIP-B-CTNCINPTT001");
////        mwHeader.setSourceChannel("LON-LX-LIP-01");
////        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
////        tranrq.setActionType("M");
////        tranrq.setApplyId("TEST001");
////        tranrq.setEmpId("E001");
////        tranrq.setGageType("M");
////        req.setMwHeader(mwHeader);
////        req.setTranrq(tranrq);
////
////        // 設置借保人清單
////        List<CTNCINPTT001TranrqBorGuar> borGuarList = new ArrayList<>();
////        CTNCINPTT001TranrqBorGuar borGuar1 = new CTNCINPTT001TranrqBorGuar();
////        borGuar1.setBorGuarId("B001");
////        borGuar1.setBorGuarName("借保人1");
////        borGuar1.setType("0");
////        borGuar1.setBorGuarKind("3");
////        borGuar1.setIsGageOwner("1");
////        borGuarList.add(borGuar1);
////        tranrq.setBorGuarList(borGuarList);
////
////        CTNCINPTT001TranrqInputBranchInfo inputBranchInfo = new CTNCINPTT001TranrqInputBranchInfo();
////        inputBranchInfo.setOriTm("LOAN,SLOAN");
////        inputBranchInfo.setOriNtm("CLIENT");
////        tranrq.setInputBranchInfo(inputBranchInfo);
////
////        // 模擬現有保證人資料
////        List<ClnCustomerGuarantorEntity> existingGuarantors = new ArrayList<>();
////        ClnCustomerGuarantorEntity existingGuarantor = new ClnCustomerGuarantorEntity();
////        existingGuarantor.setGuarId("B001");
////        existingGuarantors.add(existingGuarantor);
////        when(clnCustomerGuarantorRepository.findAllByApplyId("TEST001")).thenReturn(existingGuarantors);
////
////        // 模擬 FNSCIF0000 回應
////        FNSCIF0000Tranrs fnsTranrs = new FNSCIF0000Tranrs();
////        fnsTranrs.setBirthday("01012000");
////        fnsTranrs.setMaritalStatus("1");
////        fnsTranrs.setAddress1("測試地址");
////        fnsTranrs.setPostCode("100");
////        ResponseTemplate<FNSCIF0000Tranrs> fnsResponse = new ResponseTemplate<>();
////        fnsResponse.setTranrs(fnsTranrs);
////        when(restTempHelper.postForEntity(any(), eq(FNSCIF0000Tranrs.class))).thenReturn(fnsResponse);
////
////        // 模擬 WMS 電文記錄查詢
////        ClnTxLogArchiveEntity archiveEntity = new ClnTxLogArchiveEntity();
////        String mockRecvData = "{" + "\"tranrs\": {" + "\"valCustlevel\": \"02\"," + "\"avgBal\": 2000000" + "}" + "}";
////        archiveEntity.setRecvData(mockRecvData);
////        when(cLnTxLogArchiveRepository.findFirstByMsgIdAndCaseNbrAndSendDataContainingOrderBySendtimeAsc("WMS-B-CUSTTYPEQ003", "TEST001",
////            "B001")).thenReturn(Optional.of(archiveEntity));
////
////        CTNCINPTT001RecvDataVO dataModel = new CTNCINPTT001RecvDataVO();
////        CTNCINPTT001RecvDataTranrsVO tranrs = new CTNCINPTT001RecvDataTranrsVO();
////        tranrs.setValCustlevel("02");
////        tranrs.setAvgBal(new BigDecimal("2000000"));
////        dataModel.setTranrs(tranrs);
////        when(objectMapper.readValue(mockRecvData, CTNCINPTT001RecvDataVO.class)).thenReturn(dataModel);
////
////        // 模擬 GETKYCSTATQ002Tranrs 回應
////        GETKYCSTATQ002Tranrs getkycTranrsResponse = new GETKYCSTATQ002Tranrs();
////        MwHeaderResponse mwHeaderRes = new MwHeaderResponse();
////        mwHeaderRes.setMsgId("LIP-B-CTNCINPTT001");
////        mwHeaderRes.setReturnCode("0000");
////        ResponseTemplate<GETKYCSTATQ002Tranrs> getkycResponseTemplate = new ResponseTemplate<>();
////        getkycResponseTemplate.setMwHeaderResponse(mwHeaderRes);
////        getkycResponseTemplate.setTranrs(getkycTranrsResponse);
////        when(restTempHelper.postForEntity(any(), eq(GETKYCSTATQ002Tranrs.class))).thenReturn(getkycResponseTemplate);
////
////        // 模擬案件主檔查詢
////        ClnCaseMainEntity caseMain = new ClnCaseMainEntity();
////        when(clnCaseMainRepository.findById("TEST001")).thenReturn(Optional.of(caseMain));
////
////        // 模擬案件子檔查詢
////        ClnCaseSubEntity caseSub = new ClnCaseSubEntity();
////        when(clnCaseSubRepository.findById("TEST001")).thenReturn(Optional.of(caseSub));
////
////        ResponseTemplate<EmptyDto> expectedResponse = new ResponseTemplate<>();
////        when(normalResponseFactory.genNormalResponse(any(EmptyDto.class), any(RequestTemplate.class))).thenReturn(expectedResponse);
////
////        // Act
////        ResponseTemplate<EmptyDto> result = service.inputInfoModify(req);
////
////        // Assert
////        // 驗證保證人資料處理
////        verify(clnCustomerGuarantorRepository).findAllByApplyId("TEST001");
////        verify(restTempHelper, times(1)).postForEntity(any(), eq(FNSCIF0000Tranrs.class));
////        verify(cLnTxLogArchiveRepository).findFirstByMsgIdAndCaseNbrAndSendDataContainingOrderBySendtimeAsc("WMS-B-CUSTTYPEQ003", "TEST001",
////            "B001");
////
////        // 驗證案件主檔和子檔更新
////        verify(clnCaseMainRepository).findById("TEST001");
////        verify(clnCaseSubRepository).findById("TEST001");
////
////        // 驗證資料處理器調用
////        verify(dataProcessor).processData(any(CTNCINPTT001SvcVO.class));
////
////        // 驗證回應
////        assertEquals(expectedResponse, result);
////    }
////
////    @Test
////    @DisplayName("測試 inputInfoModify - ActionType=M, ApplyProcess=5, WMS無紀錄")
////    void testInputInfoModify_ActionTypeM_ApplyProcess5() throws Exception {
////        // Arrange
////        RequestTemplate<CTNCINPTT001Tranrq> req = new RequestTemplate<>();
////        MwHeader mwHeader = new MwHeader();
////        mwHeader.setMsgId("LIP-B-CTNCINPTT001");
////        mwHeader.setSourceChannel("LON-LX-LIP-01");
////        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
////        tranrq.setActionType("M");
////        tranrq.setApplyId("TEST001");
////        tranrq.setEmpId("E001");
////        tranrq.setGageType("C");
////        req.setMwHeader(mwHeader);
////        req.setTranrq(tranrq);
////
////        // 設置借保人清單
////        List<CTNCINPTT001TranrqBorGuar> borGuarList = new ArrayList<>();
////        CTNCINPTT001TranrqBorGuar borGuar1 = new CTNCINPTT001TranrqBorGuar();
////        borGuar1.setBorGuarId("B001");
////        borGuar1.setBorGuarName("借保人1");
////        borGuar1.setType("0");
////        borGuar1.setBorGuarKind("1");
////        borGuar1.setIsGageOwner("0");
////        borGuarList.add(borGuar1);
////        tranrq.setBorGuarList(borGuarList);
////
////        CTNCINPTT001TranrqInputBranchInfo inputBranchInfo = new CTNCINPTT001TranrqInputBranchInfo();
////        inputBranchInfo.setOriTm("LOAN,SLOAN");
////        inputBranchInfo.setOriNtm("CLIENT");
////        tranrq.setInputBranchInfo(inputBranchInfo);
////
////        // 模擬現有保證人資料
////        List<ClnCustomerGuarantorEntity> existingGuarantors = new ArrayList<>();
////        ClnCustomerGuarantorEntity existingGuarantor = new ClnCustomerGuarantorEntity();
////        existingGuarantor.setGuarId("B001");
////        existingGuarantors.add(existingGuarantor);
////        when(clnCustomerGuarantorRepository.findAllByApplyId("TEST001")).thenReturn(existingGuarantors);
////
////        // 模擬 FNSCIF0000 回應
////        ResponseTemplate<FNSCIF0000Tranrs> fnsResponse = new ResponseTemplate<>();
////        when(restTempHelper.postForEntity(any(), eq(FNSCIF0000Tranrs.class))).thenReturn(fnsResponse);
////
////        // 模擬 WMS 電文記錄查詢
////        when(cLnTxLogArchiveRepository.findFirstByMsgIdAndCaseNbrAndSendDataContainingOrderBySendtimeAsc("WMS-B-CUSTTYPEQ003", "TEST001",
////            "B001")).thenReturn(Optional.empty());
////
////        // 模擬 CUSTTYPEQ003 回應
////        CUSTTYPEQ003Tranrs wmsResponse = new CUSTTYPEQ003Tranrs();
////        wmsResponse.setValCustlevel("01");
////        wmsResponse.setAvgBal(new BigDecimal("1000000"));
////        MwHeaderResponse mwHeaderResponse = new MwHeaderResponse();
////        mwHeaderResponse.setMsgId("LIP-B-CTNCINPTT001");
////        mwHeaderResponse.setReturnCode("0000");
////        ResponseTemplate<CUSTTYPEQ003Tranrs> wmsResponseTemplate = new ResponseTemplate<>();
////        wmsResponseTemplate.setMwHeaderResponse(mwHeaderResponse);
////        wmsResponseTemplate.setTranrs(wmsResponse);
////        when(restTempHelper.postForEntity(any(), eq(CUSTTYPEQ003Tranrs.class))).thenReturn(wmsResponseTemplate);
////
////        // 模擬 GETKYCSTATQ002Tranrs 回應
////        GETKYCSTATQ002Tranrs getkycTranrsResponse = new GETKYCSTATQ002Tranrs();
////        MwHeaderResponse mwHeaderRes = new MwHeaderResponse();
////        mwHeaderRes.setMsgId("LIP-B-CTNCINPTT001");
////        mwHeaderRes.setReturnCode("0000");
////        ResponseTemplate<GETKYCSTATQ002Tranrs> getkycResponseTemplate = new ResponseTemplate<>();
////        getkycResponseTemplate.setMwHeaderResponse(mwHeaderRes);
////        getkycResponseTemplate.setTranrs(getkycTranrsResponse);
////
////        // 模擬案件主檔查詢
////        ClnCaseMainEntity caseMain = new ClnCaseMainEntity();
////        when(clnCaseMainRepository.findById("TEST001")).thenReturn(Optional.of(caseMain));
////
////        // 模擬案件子檔查詢
////        ClnCaseSubEntity caseSub = new ClnCaseSubEntity();
////        when(clnCaseSubRepository.findById("TEST001")).thenReturn(Optional.of(caseSub));
////
////        ResponseTemplate<EmptyDto> expectedResponse = new ResponseTemplate<>();
////        when(normalResponseFactory.genNormalResponse(any(EmptyDto.class), any(RequestTemplate.class))).thenReturn(expectedResponse);
////
////        // Act
////        ResponseTemplate<EmptyDto> result = service.inputInfoModify(req);
////
////        // Assert
////        // 驗證保證人資料處理
////        verify(clnCustomerGuarantorRepository).findAllByApplyId("TEST001");
////        verify(restTempHelper, times(1)).postForEntity(any(), eq(FNSCIF0000Tranrs.class));
////        verify(cLnTxLogArchiveRepository).findFirstByMsgIdAndCaseNbrAndSendDataContainingOrderBySendtimeAsc("WMS-B-CUSTTYPEQ003", "TEST001",
////            "B001");
////
////        // 驗證案件主檔和子檔更新
////        verify(clnCaseMainRepository).findById("TEST001");
////        verify(clnCaseSubRepository).findById("TEST001");
////
////        // 驗證資料處理器調用
////        verify(dataProcessor).processData(any(CTNCINPTT001SvcVO.class));
////
////        // 驗證回應
////        assertEquals(expectedResponse, result);
////    }
////
////    @Test
////    @DisplayName("測試 inputInfoModify - ActionType=M, ApplyProcess=5, InputBranchInfo=null")
////    void testInputInfoModify_ActionTypeM_ApplyProcess5_inputBranchInfoIsNull() throws Exception {
////        // Arrange
////        RequestTemplate<CTNCINPTT001Tranrq> req = new RequestTemplate<>();
////        MwHeader mwHeader = new MwHeader();
////        mwHeader.setMsgId("LIP-B-CTNCINPTT001");
////        mwHeader.setSourceChannel("LON-LX-LIP-01");
////        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
////        tranrq.setActionType("M");
////        tranrq.setApplyId("TEST001");
////        tranrq.setEmpId("E001");
////        tranrq.setGageType("M");
////        req.setMwHeader(mwHeader);
////        req.setTranrq(tranrq);
////
////        // 設置借保人清單
////        List<CTNCINPTT001TranrqBorGuar> borGuarList = new ArrayList<>();
////        CTNCINPTT001TranrqBorGuar borGuar1 = new CTNCINPTT001TranrqBorGuar();
////        borGuar1.setBorGuarId("B001");
////        borGuar1.setBorGuarName("借保人1");
////        borGuar1.setType("1");
////        borGuar1.setBorGuarKind("1");
////        borGuar1.setIsGageOwner("1");
////        borGuarList.add(borGuar1);
////        tranrq.setBorGuarList(borGuarList);
////
////        CTNCINPTT001TranrqInputBranchInfo inputBranchInfo = new CTNCINPTT001TranrqInputBranchInfo();
////        inputBranchInfo.setOriTm(null);
////        inputBranchInfo.setOriNtm(null);
////        tranrq.setInputBranchInfo(inputBranchInfo);
////
////        // 模擬現有保證人資料
////        List<ClnCustomerGuarantorEntity> existingGuarantors = new ArrayList<>();
////        ClnCustomerGuarantorEntity existingGuarantor = new ClnCustomerGuarantorEntity();
////        existingGuarantor.setGuarId("B001");
////        existingGuarantors.add(existingGuarantor);
////        when(clnCustomerGuarantorRepository.findAllByApplyId("TEST001")).thenReturn(existingGuarantors);
////
////        // 模擬 FNSCIF0000 回應
////        FNSCIF0000Tranrs fnsTranrs = new FNSCIF0000Tranrs();
////        fnsTranrs.setBirthday("01012000");
////        fnsTranrs.setMaritalStatus("1");
////        fnsTranrs.setAddress1("測試地址");
////        fnsTranrs.setPostCode("100");
////        ResponseTemplate<FNSCIF0000Tranrs> fnsResponse = new ResponseTemplate<>();
////        fnsResponse.setTranrs(fnsTranrs);
////        when(restTempHelper.postForEntity(any(), eq(FNSCIF0000Tranrs.class))).thenReturn(null);
////
////        // 模擬 WMS 電文記錄查詢
////        ClnTxLogArchiveEntity archiveEntity = new ClnTxLogArchiveEntity();
////        String mockRecvData = "{" + "\"tranrs\": {" + "\"valCustlevel\": \"02\"," + "\"avgBal\": 2000000" + "}" + "}";
////        archiveEntity.setRecvData(mockRecvData);
////        when(cLnTxLogArchiveRepository.findFirstByMsgIdAndCaseNbrAndSendDataContainingOrderBySendtimeAsc("WMS-B-CUSTTYPEQ003", "TEST001",
////            "B001")).thenReturn(Optional.of(archiveEntity));
////
////        CTNCINPTT001RecvDataVO dataModel = new CTNCINPTT001RecvDataVO();
////        CTNCINPTT001RecvDataTranrsVO tranrs = new CTNCINPTT001RecvDataTranrsVO();
////        tranrs.setValCustlevel("02");
////        tranrs.setAvgBal(new BigDecimal("2000000"));
////        dataModel.setTranrs(tranrs);
////        when(objectMapper.readValue(mockRecvData, CTNCINPTT001RecvDataVO.class)).thenReturn(dataModel);
////
////        // 模擬 GETKYCSTATQ002Tranrs 回應
////        GETKYCSTATQ002Tranrs getkycTranrsResponse = new GETKYCSTATQ002Tranrs();
////        MwHeaderResponse mwHeaderRes = new MwHeaderResponse();
////        mwHeaderRes.setMsgId("LIP-B-CTNCINPTT001");
////        mwHeaderRes.setReturnCode("0000");
////        ResponseTemplate<GETKYCSTATQ002Tranrs> getkycResponseTemplate = new ResponseTemplate<>();
////        getkycResponseTemplate.setMwHeaderResponse(mwHeaderRes);
////        getkycResponseTemplate.setTranrs(getkycTranrsResponse);
////        when(restTempHelper.postForEntity(any(), eq(GETKYCSTATQ002Tranrs.class))).thenReturn(getkycResponseTemplate);
////
////        // 模擬案件主檔查詢
////        ClnCaseMainEntity caseMain = new ClnCaseMainEntity();
////        when(clnCaseMainRepository.findById("TEST001")).thenReturn(Optional.of(caseMain));
////
////        // 模擬案件子檔查詢
////        ClnCaseSubEntity caseSub = new ClnCaseSubEntity();
////        when(clnCaseSubRepository.findById("TEST001")).thenReturn(Optional.of(caseSub));
////
////        ResponseTemplate<EmptyDto> expectedResponse = new ResponseTemplate<>();
////        when(normalResponseFactory.genNormalResponse(any(EmptyDto.class), any(RequestTemplate.class))).thenReturn(expectedResponse);
////
////        // Act
////        ResponseTemplate<EmptyDto> result = service.inputInfoModify(req);
////
////        // Assert
////        // 驗證保證人資料處理
////        verify(clnCustomerGuarantorRepository).findAllByApplyId("TEST001");
////        verify(restTempHelper, times(1)).postForEntity(any(), eq(FNSCIF0000Tranrs.class));
////        verify(cLnTxLogArchiveRepository).findFirstByMsgIdAndCaseNbrAndSendDataContainingOrderBySendtimeAsc("WMS-B-CUSTTYPEQ003", "TEST001",
////            "B001");
////
////        // 驗證案件主檔和子檔更新
////        verify(clnCaseMainRepository).findById("TEST001");
////        verify(clnCaseSubRepository).findById("TEST001");
////
////        // 驗證資料處理器調用
////        verify(dataProcessor).processData(any(CTNCINPTT001SvcVO.class));
////
////        // 驗證回應
////        assertEquals(expectedResponse, result);
////    }
////
////    @Test
////    @DisplayName("測試 inputInfoModify - ActionType=M, ApplyProcess=5, oriTm=''")
////    void testInputInfoModify_ActionTypeM_ApplyProcess5_oriTmIsEmpty() throws Exception {
////        // Arrange
////        RequestTemplate<CTNCINPTT001Tranrq> req = new RequestTemplate<>();
////        MwHeader mwHeader = new MwHeader();
////        mwHeader.setMsgId("LIP-B-CTNCINPTT001");
////        mwHeader.setSourceChannel("LON-LX-LIP-01");
////        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
////        tranrq.setActionType("M");
////        tranrq.setApplyId("TEST001");
////        tranrq.setEmpId("E001");
////        tranrq.setGageType("B");
////        req.setMwHeader(mwHeader);
////        req.setTranrq(tranrq);
////
////        // 設置借保人清單
////        List<CTNCINPTT001TranrqBorGuar> borGuarList = new ArrayList<>();
////        CTNCINPTT001TranrqBorGuar borGuar1 = new CTNCINPTT001TranrqBorGuar();
////        borGuar1.setBorGuarId("B001");
////        borGuar1.setBorGuarName("借保人1");
////        borGuar1.setType("2");
////        borGuar1.setBorGuarKind("3");
////        borGuar1.setIsGageOwner("1");
////        borGuarList.add(borGuar1);
////        tranrq.setBorGuarList(borGuarList);
////
////        CTNCINPTT001TranrqInputBranchInfo inputBranchInfo = new CTNCINPTT001TranrqInputBranchInfo();
////        inputBranchInfo.setOriTm("");
////        inputBranchInfo.setOriNtm("");
////        tranrq.setInputBranchInfo(inputBranchInfo);
////
////        // 模擬現有保證人資料
////        List<ClnCustomerGuarantorEntity> existingGuarantors = new ArrayList<>();
////        ClnCustomerGuarantorEntity existingGuarantor = new ClnCustomerGuarantorEntity();
////        existingGuarantor.setGuarId("B001");
////        existingGuarantors.add(existingGuarantor);
////        when(clnCustomerGuarantorRepository.findAllByApplyId("TEST001")).thenReturn(existingGuarantors);
////
////        // 模擬 FNSCIF0000 回應
////        FNSCIF0000Tranrs fnsTranrs = new FNSCIF0000Tranrs();
////        fnsTranrs.setMaritalStatus("1");
////        fnsTranrs.setAddress1("測試地址");
////        fnsTranrs.setPostCode("100");
////        fnsTranrs.setBusinessPhone("1234");
////        ResponseTemplate<FNSCIF0000Tranrs> fnsResponse = new ResponseTemplate<>();
////        fnsResponse.setTranrs(fnsTranrs);
////        when(restTempHelper.postForEntity(any(), eq(FNSCIF0000Tranrs.class))).thenReturn(fnsResponse);
////
////        // 模擬 WMS 電文記錄查詢
////        ClnTxLogArchiveEntity archiveEntity = new ClnTxLogArchiveEntity();
////        String mockRecvData = "{" + "\"tranrs\": {" + "\"valCustlevel\": \"02\"," + "\"avgBal\": 2000000" + "}" + "}";
////        archiveEntity.setRecvData(mockRecvData);
////        when(cLnTxLogArchiveRepository.findFirstByMsgIdAndCaseNbrAndSendDataContainingOrderBySendtimeAsc("WMS-B-CUSTTYPEQ003", "TEST001",
////            "B001")).thenReturn(Optional.of(archiveEntity));
////
////        // 模擬 CUSTTYPEQ003 回應
////        CTNCINPTT001RecvDataVO dataModel = new CTNCINPTT001RecvDataVO();
////        CTNCINPTT001RecvDataTranrsVO tranrs = new CTNCINPTT001RecvDataTranrsVO();
////        tranrs.setValCustlevel("02");
////        tranrs.setAvgBal(new BigDecimal("2000000"));
////        dataModel.setTranrs(tranrs);
////        when(objectMapper.readValue(mockRecvData, CTNCINPTT001RecvDataVO.class)).thenReturn(dataModel);
////
////        // 模擬 GETKYCSTATQ002Tranrs 回應
////        GETKYCSTATQ002Tranrs getkycTranrsResponse = new GETKYCSTATQ002Tranrs();
////        MwHeaderResponse mwHeaderRes = new MwHeaderResponse();
////        mwHeaderRes.setMsgId("LIP-B-CTNCINPTT001");
////        mwHeaderRes.setReturnCode("0000");
////        ResponseTemplate<GETKYCSTATQ002Tranrs> getkycResponseTemplate = new ResponseTemplate<>();
////        getkycResponseTemplate.setMwHeaderResponse(mwHeaderRes);
////        getkycResponseTemplate.setTranrs(getkycTranrsResponse);
////
////        // 模擬案件主檔查詢
////        ClnCaseMainEntity caseMain = new ClnCaseMainEntity();
////        when(clnCaseMainRepository.findById("TEST001")).thenReturn(Optional.of(caseMain));
////
////        // 模擬案件子檔查詢
////        ClnCaseSubEntity caseSub = new ClnCaseSubEntity();
////        when(clnCaseSubRepository.findById("TEST001")).thenReturn(Optional.of(caseSub));
////
////        ResponseTemplate<EmptyDto> expectedResponse = new ResponseTemplate<>();
////        when(normalResponseFactory.genNormalResponse(any(EmptyDto.class), any(RequestTemplate.class))).thenReturn(expectedResponse);
////
////        // Act
////        ResponseTemplate<EmptyDto> result = service.inputInfoModify(req);
////
////        // Assert
////        // 驗證保證人資料處理
////        verify(clnCustomerGuarantorRepository).findAllByApplyId("TEST001");
////        verify(restTempHelper, times(1)).postForEntity(any(), eq(FNSCIF0000Tranrs.class));
////        verify(cLnTxLogArchiveRepository).findFirstByMsgIdAndCaseNbrAndSendDataContainingOrderBySendtimeAsc("WMS-B-CUSTTYPEQ003", "TEST001",
////            "B001");
////
////        // 驗證案件主檔和子檔更新
////        verify(clnCaseMainRepository).findById("TEST001");
////        verify(clnCaseSubRepository).findById("TEST001");
////
////        // 驗證資料處理器調用
////        verify(dataProcessor).processData(any(CTNCINPTT001SvcVO.class));
////
////        // 驗證回應
////        assertEquals(expectedResponse, result);
////    }
////
////    @Test
////    @DisplayName("測試 inputInfoModify - ActionType=M, ApplyProcess=5, idsToDelete 非空")
////    void testInputInfoModify_ActionTypeM_ApplyProcess5_idsToDelete() throws Exception {
////        // Arrange
////        RequestTemplate<CTNCINPTT001Tranrq> req = new RequestTemplate<>();
////        MwHeader mwHeader = new MwHeader();
////        mwHeader.setMsgId("LIP-B-CTNCINPTT001");
////        mwHeader.setSourceChannel("LON-LX-LIP-01");
////        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
////        tranrq.setActionType("M");
////        tranrq.setApplyId("TEST001");
////        tranrq.setEmpId("E001");
////        tranrq.setGageType("B");
////        req.setMwHeader(mwHeader);
////        req.setTranrq(tranrq);
////
////        // 設置新的借保人清單
////        List<CTNCINPTT001TranrqBorGuar> borGuarList = new ArrayList<>();
////        // 保留的借款人
////        CTNCINPTT001TranrqBorGuar borrower = createBorGuar("B001", "0", "3", "1");
////
////        borGuarList.add(borrower);
////        tranrq.setBorGuarList(borGuarList);
////        req.setTranrq(tranrq);
////
////        // 設置借保人清單
////        // 模擬現有的保證人資料
////        List<ClnCustomerGuarantorEntity> existingGuarantors = new ArrayList<>();
////        // 將被刪除的保證人
////        existingGuarantors.add(createExistingGuarantor("G001", "一般保證人1"));
////        existingGuarantors.add(createExistingGuarantor("G002", "一般保證人2"));
////        existingGuarantors.add(createExistingGuarantor("G003", "擔保品提供人"));
////        // 保留的借款人
////        existingGuarantors.add(createExistingGuarantor("B001", "借款人"));
////
////        when(clnCustomerGuarantorRepository.findAllByApplyId("TEST001")).thenReturn(existingGuarantors);
////
////        CTNCINPTT001TranrqInputBranchInfo inputBranchInfo = new CTNCINPTT001TranrqInputBranchInfo();
////        inputBranchInfo.setOriTm("LOAN,SLOAN");
////        inputBranchInfo.setOriNtm("CLIENT");
////        tranrq.setInputBranchInfo(inputBranchInfo);
////
////        // 模擬 FNSCIF0000 回應
////        FNSCIF0000Tranrs fnsTranrs = new FNSCIF0000Tranrs();
////        fnsTranrs.setBirthday("01012000");
////        fnsTranrs.setMaritalStatus("1");
////        fnsTranrs.setAddress1("測試地址");
////        fnsTranrs.setPostCode("100");
////        fnsTranrs.setBusinessPhone("123456789");
////        ResponseTemplate<FNSCIF0000Tranrs> fnsResponse = new ResponseTemplate<>();
////        fnsResponse.setTranrs(fnsTranrs);
////        when(restTempHelper.postForEntity(any(), eq(FNSCIF0000Tranrs.class))).thenReturn(fnsResponse);
////
////        // 模擬 WMS 電文記錄查詢
////        when(cLnTxLogArchiveRepository.findFirstByMsgIdAndCaseNbrAndSendDataContainingOrderBySendtimeAsc("WMS-B-CUSTTYPEQ003", "TEST001",
////            "B001")).thenReturn(Optional.empty());
////
////        // 模擬 CUSTTYPEQ003 回應
////        CUSTTYPEQ003Tranrs wmsResponse = new CUSTTYPEQ003Tranrs();
////        wmsResponse.setValCustlevel("01");
////        wmsResponse.setAvgBal(null);
////        MwHeaderResponse mwHeaderResponse = new MwHeaderResponse();
////        mwHeaderResponse.setMsgId("LIP-B-CTNCINPTT001");
////        mwHeaderResponse.setReturnCode("0000");
////        ResponseTemplate<CUSTTYPEQ003Tranrs> wmsResponseTemplate = new ResponseTemplate<>();
////        wmsResponseTemplate.setMwHeaderResponse(mwHeaderResponse);
////        wmsResponseTemplate.setTranrs(wmsResponse);
////        when(restTempHelper.postForEntity(any(), eq(CUSTTYPEQ003Tranrs.class))).thenReturn(wmsResponseTemplate);
////
////        // 模擬 GETKYCSTATQ002Tranrs 回應
////        GETKYCSTATQ002Tranrs getkycTranrsResponse = new GETKYCSTATQ002Tranrs();
////        getkycTranrsResponse.setFlgIsproinvestor("0");
////        MwHeaderResponse mwHeaderRes = new MwHeaderResponse();
////        mwHeaderRes.setMsgId("LIP-B-CTNCINPTT001");
////        mwHeaderRes.setReturnCode("0000");
////        ResponseTemplate<GETKYCSTATQ002Tranrs> getkycResponseTemplate = new ResponseTemplate<>();
////        getkycResponseTemplate.setMwHeaderResponse(mwHeaderRes);
////        getkycResponseTemplate.setTranrs(getkycTranrsResponse);
////        when(restTempHelper.postForEntity(any(), eq(GETKYCSTATQ002Tranrs.class))).thenReturn(getkycResponseTemplate);
////
////        // 模擬案件主檔查詢
////        ClnCaseMainEntity caseMain = new ClnCaseMainEntity();
////        when(clnCaseMainRepository.findById("TEST001")).thenReturn(Optional.of(caseMain));
////
////        // 模擬案件子檔查詢
////        ClnCaseSubEntity caseSub = new ClnCaseSubEntity();
////        when(clnCaseSubRepository.findById("TEST001")).thenReturn(Optional.of(caseSub));
////
////        ResponseTemplate<EmptyDto> expectedResponse = new ResponseTemplate<>();
////        when(normalResponseFactory.genNormalResponse(any(EmptyDto.class), any(RequestTemplate.class))).thenReturn(expectedResponse);
////
////        // Act
////        ResponseTemplate<EmptyDto> result = service.inputInfoModify(req);
////
////        // Assert
////        // 驗證保證人資料處理
////        verify(clnCustomerGuarantorRepository).findAllByApplyId("TEST001");
////        verify(restTempHelper, times(1)).postForEntity(any(), eq(FNSCIF0000Tranrs.class));
////        verify(cLnTxLogArchiveRepository).findFirstByMsgIdAndCaseNbrAndSendDataContainingOrderBySendtimeAsc("WMS-B-CUSTTYPEQ003", "TEST001",
////            "B001");
////
////        // 驗證案件主檔和子檔更新
////        verify(clnCaseMainRepository).findById("TEST001");
////        verify(clnCaseSubRepository).findById("TEST001");
////
////        // 驗證資料處理器調用
////        verify(dataProcessor).processData(any(CTNCINPTT001SvcVO.class));
////
////        // 驗證回應
////        assertEquals(expectedResponse, result);
////    }
////
////    @Test
////    @DisplayName("測試 inputInfoModify - ActionType=M, ApplyProcess=5, 生日格式錯誤")
////    void testInputInfoModify_ActionTypeM_ApplyProcess5_InvalidBirthday() throws Exception {
////        // Arrange
////        RequestTemplate<CTNCINPTT001Tranrq> req = new RequestTemplate<>();
////        MwHeader mwHeader = new MwHeader();
////        mwHeader.setMsgId("LIP-B-CTNCINPTT001");
////        mwHeader.setSourceChannel("LON-LX-LIP-01");
////        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
////        tranrq.setActionType("M");
////        tranrq.setApplyId("TEST001");
////        tranrq.setEmpId("E001");
////        tranrq.setGageType("B");
////        req.setMwHeader(mwHeader);
////        req.setTranrq(tranrq);
////
////        // 設置借保人清單
////        List<CTNCINPTT001TranrqBorGuar> borGuarList = new ArrayList<>();
////        CTNCINPTT001TranrqBorGuar borGuar1 = new CTNCINPTT001TranrqBorGuar();
////        borGuar1.setBorGuarId("B001");
////        borGuar1.setBorGuarName("借保人1");
////        borGuar1.setType("0");
////        borGuar1.setBorGuarKind("3");
////        borGuar1.setIsGageOwner("0");
////        borGuarList.add(borGuar1);
////        tranrq.setBorGuarList(borGuarList);
////
////        CTNCINPTT001TranrqInputBranchInfo inputBranchInfo = new CTNCINPTT001TranrqInputBranchInfo();
////        tranrq.setInputBranchInfo(inputBranchInfo);
////
////        // 模擬現有保證人資料
////        when(clnCustomerGuarantorRepository.findAllByApplyId("TEST001")).thenReturn(new ArrayList<>());
////
////        // 模擬 FNSCIF0000 回應 - 錯誤的生日格式
////        FNSCIF0000Tranrs fnsTranrs = new FNSCIF0000Tranrs();
////        fnsTranrs.setBirthday("invalid_date"); // 錯誤的日期格式
////        fnsTranrs.setMaritalStatus("1");
////        ResponseTemplate<FNSCIF0000Tranrs> fnsResponse = new ResponseTemplate<>();
////        fnsResponse.setTranrs(fnsTranrs);
////        when(restTempHelper.postForEntity(any(), eq(FNSCIF0000Tranrs.class))).thenReturn(fnsResponse);
////
////        // 模擬 WMS 電文記錄查詢
////        when(cLnTxLogArchiveRepository.findFirstByMsgIdAndCaseNbrAndSendDataContainingOrderBySendtimeAsc("WMS-B-CUSTTYPEQ003", "TEST001",
////            "B001")).thenReturn(Optional.empty());
////
////        // 模擬 CUSTTYPEQ003 回應
////        CUSTTYPEQ003Tranrs wmsResponse = new CUSTTYPEQ003Tranrs();
////        wmsResponse.setValCustlevel("01");
////        wmsResponse.setAvgBal(new BigDecimal("1000000"));
////        MwHeaderResponse mwHeaderResponse = new MwHeaderResponse();
////        mwHeaderResponse.setMsgId("LIP-B-CTNCINPTT001");
////        mwHeaderResponse.setReturnCode("0000");
////        ResponseTemplate<CUSTTYPEQ003Tranrs> wmsResponseTemplate = new ResponseTemplate<>();
////        wmsResponseTemplate.setMwHeaderResponse(mwHeaderResponse);
////        wmsResponseTemplate.setTranrs(wmsResponse);
////        when(restTempHelper.postForEntity(any(), eq(CUSTTYPEQ003Tranrs.class))).thenReturn(wmsResponseTemplate);
////
////        // 模擬 GETKYCSTATQ002Tranrs 回應
////        GETKYCSTATQ002Tranrs getkycTranrsResponse = new GETKYCSTATQ002Tranrs();
////        getkycTranrsResponse.setFlgIsproinvestor("0");
////        MwHeaderResponse mwHeaderRes = new MwHeaderResponse();
////        mwHeaderRes.setMsgId("LIP-B-CTNCINPTT001");
////        mwHeaderRes.setReturnCode("0000");
////        ResponseTemplate<GETKYCSTATQ002Tranrs> getkycResponseTemplate = new ResponseTemplate<>();
////        getkycResponseTemplate.setMwHeaderResponse(mwHeaderRes);
////        getkycResponseTemplate.setTranrs(getkycTranrsResponse);
////        when(restTempHelper.postForEntity(any(), eq(GETKYCSTATQ002Tranrs.class))).thenReturn(getkycResponseTemplate);
////
////        // 模擬案件主檔查詢
////        ClnCaseMainEntity caseMain = new ClnCaseMainEntity();
////        when(clnCaseMainRepository.findById("TEST001")).thenReturn(Optional.of(caseMain));
////
////        // 模擬案件子檔查詢
////        ClnCaseSubEntity caseSub = new ClnCaseSubEntity();
////        when(clnCaseSubRepository.findById("TEST001")).thenReturn(Optional.of(caseSub));
////
////        ResponseTemplate<EmptyDto> expectedResponse = new ResponseTemplate<>();
////        when(normalResponseFactory.genNormalResponse(any(EmptyDto.class), any(RequestTemplate.class))).thenReturn(expectedResponse);
////
////        // Act
////        ResponseTemplate<EmptyDto> result = service.inputInfoModify(req);
////
////        // Assert
////        verify(dataProcessor).processData(any(CTNCINPTT001SvcVO.class));
////        assertNotNull(result);
////    }
////
////    @Test
////    @DisplayName("測試 inputInfoModify - ActionType=M, ApplyProcess=5, 平均餘額為0")
////    void testInputInfoModify_ActionTypeM_ApplyProcess5_ZeroAvgBalance() throws Exception {
////        // Arrange
////        RequestTemplate<CTNCINPTT001Tranrq> req = new RequestTemplate<>();
////        MwHeader mwHeader = new MwHeader();
////        mwHeader.setMsgId("LIP-B-CTNCINPTT001");
////        mwHeader.setSourceChannel("LON-LX-LIP-01");
////        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
////        tranrq.setActionType("M");
////        tranrq.setApplyId("TEST001");
////        tranrq.setEmpId("E001");
////        tranrq.setGageType("B");
////        req.setMwHeader(mwHeader);
////        req.setTranrq(tranrq);
////
////        // 設置借保人清單
////        List<CTNCINPTT001TranrqBorGuar> borGuarList = new ArrayList<>();
////        CTNCINPTT001TranrqBorGuar borGuar1 = new CTNCINPTT001TranrqBorGuar();
////        borGuar1.setBorGuarId("B001");
////        borGuar1.setBorGuarName("借保人1");
////        borGuar1.setType("1");
////        borGuar1.setBorGuarKind("2");
////        borGuar1.setIsGageOwner("0");
////        borGuarList.add(borGuar1);
////        tranrq.setBorGuarList(borGuarList);
////
////        CTNCINPTT001TranrqInputBranchInfo inputBranchInfo = new CTNCINPTT001TranrqInputBranchInfo();
////        tranrq.setInputBranchInfo(inputBranchInfo);
////
////        // 模擬現有保證人資料
////        when(clnCustomerGuarantorRepository.findAllByApplyId("TEST001")).thenReturn(new ArrayList<>());
////
////        // 模擬 FNSCIF0000 回應
////        FNSCIF0000Tranrs fnsTranrs = new FNSCIF0000Tranrs();
////        fnsTranrs.setBirthday("01012000");
////        ResponseTemplate<FNSCIF0000Tranrs> fnsResponse = new ResponseTemplate<>();
////        fnsResponse.setTranrs(fnsTranrs);
////        when(restTempHelper.postForEntity(any(), eq(FNSCIF0000Tranrs.class))).thenReturn(fnsResponse);
////
////        // 模擬 CUSTTYPEQ003 回應 - 平均餘額為0
////        when(cLnTxLogArchiveRepository.findFirstByMsgIdAndCaseNbrAndSendDataContainingOrderBySendtimeAsc(any(), any(), any()))
////                .thenReturn(Optional.empty());
////
////        CUSTTYPEQ003Tranrs wmsResponse = new CUSTTYPEQ003Tranrs();
////        wmsResponse.setValCustlevel("01");
////        wmsResponse.setAvgBal(BigDecimal.ZERO); // 餘額為0
////        MwHeaderResponse mwHeaderResponse = new MwHeaderResponse();
////        mwHeaderResponse.setReturnCode("0000");
////        ResponseTemplate<CUSTTYPEQ003Tranrs> wmsResponseTemplate = new ResponseTemplate<>();
////        wmsResponseTemplate.setMwHeaderResponse(mwHeaderResponse);
////        wmsResponseTemplate.setTranrs(wmsResponse);
////        when(restTempHelper.postForEntity(any(), eq(CUSTTYPEQ003Tranrs.class))).thenReturn(wmsResponseTemplate);
////
////        // 模擬其他回應
////        GETKYCSTATQ002Tranrs getkycTranrsResponse = new GETKYCSTATQ002Tranrs();
////        getkycTranrsResponse.setFlgIsproinvestor("1");
////        ResponseTemplate<GETKYCSTATQ002Tranrs> getkycResponseTemplate = new ResponseTemplate<>();
////        getkycResponseTemplate.setMwHeaderResponse(mwHeaderResponse);
////        getkycResponseTemplate.setTranrs(getkycTranrsResponse);
////        when(restTempHelper.postForEntity(any(), eq(GETKYCSTATQ002Tranrs.class))).thenReturn(getkycResponseTemplate);
////
////        when(clnCaseMainRepository.findById("TEST001")).thenReturn(Optional.of(new ClnCaseMainEntity()));
////        when(clnCaseSubRepository.findById("TEST001")).thenReturn(Optional.of(new ClnCaseSubEntity()));
////
////        ResponseTemplate<EmptyDto> expectedResponse = new ResponseTemplate<>();
////        when(normalResponseFactory.genNormalResponse(any(EmptyDto.class), any(RequestTemplate.class))).thenReturn(expectedResponse);
////
////        // Act
////        ResponseTemplate<EmptyDto> result = service.inputInfoModify(req);
////
////        // Assert
////        verify(dataProcessor).processData(any(CTNCINPTT001SvcVO.class));
////        assertEquals(expectedResponse, result);
////    }
////
////    @Test
////    @DisplayName("測試 inputInfoModify - ActionType=M, ApplyProcess=0")
////    void testInputInfoModify_ApplyProcess0_NoUpdateActions() throws Exception {
////        // Arrange
////        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
////        tranrq.setActionType("M");
////        tranrq.setApplyId("TEST_APPLY_ID");
////        tranrq.setEmpId("EMP001");
////        tranrq.setBranchId("BR001");
////
////        CTNCINPTT001TranrqInputBranchInfo branchInfo = new CTNCINPTT001TranrqInputBranchInfo();
////        tranrq.setInputBranchInfo(branchInfo);
////
////        RequestTemplate<CTNCINPTT001Tranrq> request = new RequestTemplate<>();
////        request.setTranrq(tranrq);
////
////        when(commonUtil.getCaseHistory(any(), any(), any(), any(), any(), any())).thenReturn(new ClnCaseHistoryEntity());
////
////        // Act
////        service.inputInfoModify(request);
////
////        // Assert
////        ArgumentCaptor<CTNCINPTT001SvcVO> voCaptor = ArgumentCaptor.forClass(CTNCINPTT001SvcVO.class);
////        verify(dataProcessor).processData(voCaptor.capture());
////
////        CTNCINPTT001SvcVO vo = voCaptor.getValue();
////        assertTrue(vo.getCaseMainEntities().isEmpty());
////        assertTrue(vo.getCustomerGuarantorEntities().isEmpty());
////        assertTrue(vo.getRepayFinAssetsEntities().isEmpty());
////        assertEquals(1, vo.getCaseHistoryEntities().size());
////    }
////
////    @Test
////    @DisplayName("測試 saveOrUpdateCustomerGuarantor - 已存在保證人且 GuarKind1 = '1'")
////    void testSaveOrUpdateCustomerGuarantor_ExistingGuarantor_GuarKind1IsZero() {
////        // Arrange
////        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
////        tranrq.setApplyId("TEST001");
////        tranrq.setEmpId("EMP001");
////
////        CTNCINPTT001TranrqBorGuar guar = new CTNCINPTT001TranrqBorGuar();
////        guar.setBorGuarId("G001");
////        guar.setBorGuarName("測試保證人");
////        guar.setBorGuarKind("1");
////        guar.setType("1");
////        guar.setIsGageOwner("0");
////
////        FNSCIF0000Tranrs fnsTranrs = new FNSCIF0000Tranrs();
////        fnsTranrs.setBirthday("01012000");
////        fnsTranrs.setEmailAddress("test@example.com");
////        fnsTranrs.setMaritalStatus("1");
////
////        CTNCINPTT001SvcVO vo = new CTNCINPTT001SvcVO();
////
////        // Mock: 保證人已存在
////        ClnCustomerGuarantorEntity existingEntity = new ClnCustomerGuarantorEntity();
////        existingEntity.setGuarId("G001");
////        existingEntity.setGuarName("舊保證人");
////        when(clnCustomerGuarantorRepository.findById(new ClnCustomerGuarantorPKEntity("TEST001", "G001")))
////                .thenReturn(Optional.of(existingEntity));
////
////        // Act
////        service.processFullCustomerData(tranrq, guar, fnsTranrs, "01", BigDecimal.ZERO, false, vo);
////
////        // Assert
////        List<ClnCustomerGuarantorEntity> result = vo.getCustomerGuarantorEntities();
////        assertEquals(1, result.size());
////        ClnCustomerGuarantorEntity entity = result.get(0);
////        assertEquals("1", entity.getGuarKind1());
////        assertEquals("G001", entity.getGuarId());
////        assertEquals("測試保證人", entity.getGuarName());
////    }
////
////    @Test
////    @DisplayName("測試 inputInfoModify - ActionType=X")
////    void testInputInfoModify_ActionTypeIsX() throws Exception {
////        // Arrange
////        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
////        tranrq.setActionType("X");
////        tranrq.setApplyId("TEST_APPLY_ID");
////        tranrq.setEmpId("EMP001");
////        tranrq.setBranchId("BR001");
////
////        RequestTemplate<CTNCINPTT001Tranrq> request = new RequestTemplate<>();
////        request.setTranrq(tranrq);
////
////        // Act
////        service.inputInfoModify(request);
////
////        // Assert
////        verify(dataProcessor).processData(any());
////    }
////
////    @Test
////    @DisplayName("測試 saveOrUpdateCustomerInfo - 已存在客戶資料")
////    void testSaveOrUpdateCustomerInfo_ExistingCustomerInfo() {
////        // Arrange
////        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
////        tranrq.setApplyId("TEST001");
////        tranrq.setEmpId("EMP001");
////
////        CTNCINPTT001TranrqBorGuar guar = new CTNCINPTT001TranrqBorGuar();
////        guar.setBorGuarId("C001");
////        guar.setBorGuarName("測試客戶");
////        guar.setBorGuarKind("3");
////        guar.setType("0");
////        guar.setIsGageOwner("1");
////
////        FNSCIF0000Tranrs fnsTranrs = new FNSCIF0000Tranrs();
////        fnsTranrs.setBirthday("01012000");
////        fnsTranrs.setEmailAddress("test@example.com");
////        fnsTranrs.setMaritalStatus("1");
////        fnsTranrs.setAddress1("台北市信義路");
////        fnsTranrs.setPostCode("110");
////
////        CTNCINPTT001SvcVO vo = new CTNCINPTT001SvcVO();
////
////        // Mock: 客戶資料已存在
////        ClnCustomerInfoEntity existingEntity = new ClnCustomerInfoEntity();
////        existingEntity.setCustomerId("C001");
////        existingEntity.setCustomerType("1");
////        existingEntity.setApplyId("TEST001");
////        when(clnCustomerInfoRepository.findById(any(ClnCustomerInfoPKEntity.class))).thenReturn(Optional.of(existingEntity));
////
////        // Act
////        service.processFullCustomerData(tranrq, guar, fnsTranrs, "01", BigDecimal.ZERO, false, vo);
////
////        // Assert
////        List<ClnCustomerInfoEntity> result = vo.getCustomerInfoEntities();
////        assertEquals(1, result.size());
////        ClnCustomerInfoEntity entity = result.get(0);
////        assertEquals("C001", entity.getCustomerId());
////        assertEquals("測試客戶", entity.getCustomerName());
////        assertEquals("01", entity.getCustLevel());
////        assertEquals(BigDecimal.ZERO, entity.getAvgbal());
////    }
////
////    @Test
////    @DisplayName("測試 ApplyProcess=5 - idsToUpdate 與 idsToInsert 皆為空")
////    void testApplyProcess5_IdsToUpdateInsertEmpty() throws Exception {
////        // Arrange
////        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
////        tranrq.setApplyId("TEST001");
////        tranrq.setActionType("M");
////        tranrq.setEmpId("EMP001");
////
////        CTNCINPTT001TranrqInputBranchInfo branchInfo = new CTNCINPTT001TranrqInputBranchInfo();
////        branchInfo.setAgentId("A001");
////        branchInfo.setRemitBranchId("B001");
////        tranrq.setInputBranchInfo(branchInfo);
////
////        // existing 保證人 ID = A
////        ClnCustomerGuarantorEntity existing = new ClnCustomerGuarantorEntity();
////        existing.setGuarId("A");
////        when(clnCustomerGuarantorRepository.findAllByApplyId("TEST001")).thenReturn(Arrays.asList(existing));
////
////        // 新的保證人 ID = A → 完全相同 → 不更新、不新增
////        CTNCINPTT001TranrqBorGuar guar = new CTNCINPTT001TranrqBorGuar();
////        guar.setBorGuarId("A");
////        guar.setBorGuarKind("1");
////        guar.setType("1");
////        guar.setIsGageOwner("0");
////        List<CTNCINPTT001TranrqBorGuar> borGuarList = new ArrayList<>();
////        borGuarList.add(guar);
////        tranrq.setBorGuarList(new ArrayList<>());
////
////        RequestTemplate<CTNCINPTT001Tranrq> req = new RequestTemplate<>();
////        req.setTranrq(tranrq);
////
////        when(normalResponseFactory.genNormalResponse(any(), any())).thenReturn(new ResponseTemplate<>());
////        when(commonUtil.getCaseHistory(any(), any(), any(), any(), any(), any())).thenReturn(new ClnCaseHistoryEntity());
////
////        // Act
////        ResponseTemplate<EmptyDto> result = service.inputInfoModify(req);
////
////        // Assert
////        verify(dataProcessor).processData(any());
////        assertNotNull(result);
////    }
////
////    @Test
////    @DisplayName("測試 saveRepayFinAssets - 條件不成立不執行")
////    void testSaveRepayFinAssets_ConditionNotMet() {
////        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
////        tranrq.setApplyId("TEST001");
////        tranrq.setEmpId("EMP001");
////
////        CTNCINPTT001TranrqBorGuar guar = new CTNCINPTT001TranrqBorGuar();
////        guar.setBorGuarId("X001");
////        guar.setBorGuarName("不符合條件的保證人");
////        guar.setType("0");
////        guar.setBorGuarKind("2"); // ≠ "3"
////        guar.setIsGageOwner("0");
////
////        FNSCIF0000Tranrs fnsTranrs = new FNSCIF0000Tranrs();
////        fnsTranrs.setBirthday("01012000");
////
////        CTNCINPTT001SvcVO vo = new CTNCINPTT001SvcVO();
////
////        // Mock: 保證人不存在
////        when(clnCustomerGuarantorRepository.findById(new ClnCustomerGuarantorPKEntity("TEST001", "X001"))).thenReturn(Optional.empty());
////        when(clnCustomerInfoRepository.findById(any(ClnCustomerInfoPKEntity.class))).thenReturn(Optional.empty());
////
////        // Act
////        service.processFullCustomerData(tranrq, guar, fnsTranrs, "01", BigDecimal.TEN, true, vo);
////
////        // Assert
////        assertTrue(vo.getRepayFinAssetsEntities().isEmpty()); // 不應新增任何資料
////    }
////
////    @Test
////    @DisplayName("測試 valCustlevels 條件不成立 - type=0 且 kind≠3")
////    void testValCustlevelsConditionNotMet() throws Exception {
////        // Arrange
////        CTNCINPTT001Tranrq tranrq = new CTNCINPTT001Tranrq();
////        tranrq.setApplyId("TEST001");
////        tranrq.setEmpId("EMP001");
////        tranrq.setActionType("M");
////
////        CTNCINPTT001TranrqInputBranchInfo branchInfo = new CTNCINPTT001TranrqInputBranchInfo();
////        branchInfo.setAgentId("A001");
////        branchInfo.setRemitBranchId("B001");
////        tranrq.setInputBranchInfo(branchInfo);
////
////        CTNCINPTT001TranrqBorGuar guar = new CTNCINPTT001TranrqBorGuar();
////        guar.setBorGuarId("B001");
////        guar.setBorGuarName("測試人員");
////        guar.setType("0");
////        guar.setBorGuarKind("2"); // 不符合條件
////        guar.setIsGageOwner("0");
////
////        List<CTNCINPTT001TranrqBorGuar> borGuarList = new ArrayList<>();
////        borGuarList.add(guar);
////        tranrq.setBorGuarList(borGuarList);
////
////        RequestTemplate<CTNCINPTT001Tranrq> req = new RequestTemplate<>();
////        req.setTranrq(tranrq);
////
////        // 模擬 WMS 有紀錄
////        ClnTxLogArchiveEntity archiveEntity = new ClnTxLogArchiveEntity();
////        String mockRecvData = "{\"tranrs\": {\"valCustlevel\": \"02\", \"avgBal\": 2000000}}";
////        archiveEntity.setRecvData(mockRecvData);
////        when(cLnTxLogArchiveRepository.findFirstByMsgIdAndCaseNbrAndSendDataContainingOrderBySendtimeAsc(any(), any(), any()))
////                .thenReturn(Optional.of(archiveEntity));
////
////        CTNCINPTT001RecvDataVO dataModel = new CTNCINPTT001RecvDataVO();
////        CTNCINPTT001RecvDataTranrsVO tranrsVO = new CTNCINPTT001RecvDataTranrsVO();
////        tranrsVO.setValCustlevel("02");
////        tranrsVO.setAvgBal(new BigDecimal("2000000"));
////        dataModel.setTranrs(tranrsVO);
////        when(objectMapper.readValue(mockRecvData, CTNCINPTT001RecvDataVO.class)).thenReturn(dataModel);
////
////        when(clnCustomerGuarantorRepository.findAllByApplyId("TEST001")).thenReturn(new ArrayList<>());
////        when(normalResponseFactory.genNormalResponse(any(), any())).thenReturn(new ResponseTemplate<>());
////        when(commonUtil.getCaseHistory(any(), any(), any(), any(), any(), any())).thenReturn(new ClnCaseHistoryEntity());
////
////        // Act
////        service.inputInfoModify(req);
////
////        // Assert
////        ArgumentCaptor<CTNCINPTT001SvcVO> voCaptor = ArgumentCaptor.forClass(CTNCINPTT001SvcVO.class);
////        verify(dataProcessor).processData(voCaptor.capture());
////    }
////
////    // 輔助方法
////    private CTNCINPTT001TranrqBorGuar createBorGuar(String id, String type, String kind, String isGageOwner) {
////        CTNCINPTT001TranrqBorGuar borGuar = new CTNCINPTT001TranrqBorGuar();
////        borGuar.setBorGuarId(id);
////        borGuar.setType(type);
////        borGuar.setBorGuarKind(kind);
////        borGuar.setIsGageOwner(isGageOwner);
////        borGuar.setBorGuarName("測試人員" + id);
////        return borGuar;
////    }
////
////    private ClnCustomerGuarantorEntity createExistingGuarantor(String guarId, String name) {
////        ClnCustomerGuarantorEntity guarantor = new ClnCustomerGuarantorEntity();
////        guarantor.setGuarId(guarId);
////        guarantor.setGuarName(name);
////        guarantor.setApplyId("TEST001");
////        return guarantor;
////    }
////}
```

## 異動 API 交付檢查

### 契約與檢核

-   [ ] 電文 ID、URI、HTTP method、Content-Type 與 Controller 一致。
-   [ ] DTO 驗證、業務檢核和錯誤語意分別清楚。
-   [ ] 每一項異動有來源、轉換方式或明確預設值。
-   [ ] 案件狀態、角色與 ActionType 的允許條件有規格依據。

### 交易與整合

-   [ ] 跨表寫入順序、原子性、歷程和回滾範圍已確認。
-   [ ] 外部呼叫失敗、重送、防重複與 DB rollback 的差異已處理。
-   [ ] 成功、規則失敗、資料不存在與重要動作分支已驗證。
-   [ ] 測試檔未被註解，且測試命令實際可執行。
