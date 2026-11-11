# lip-web-cln

## lip-web-cln｜CLN Angular 前端

前端指南：先看專案結構與共用攔截器，再盤點 6 種頁面寫法、說明拿到頁面後怎麼寫（必須遵守的規則見「前端共通規範」），最後以「進件輸入」頁串起 Component、Service、電文與後端 lip-svc-cln。

## 專案架構

Angular 8 單頁應用（SPA），UI 使用 PrimeNG 與公司元件庫 `cub-lib-view-*`。業務頁面依功能分成 `pages/system/cln-*` 共 17 個 lazy-load 模組，每個模組內都是 components／services／interfaces 三層。

lip-web-cln/

src/app/

-   `core/` 攔截器、Guard、登入與使用者資訊等全域服務
    
-   `shared/` 共用元件（table、search-block、file-upload…）、pipes、validators
    
-   `shared-primeng/` 集中匯入 PrimeNG 模組
    
-   `layouts/` base-layout 與 topbar、container、footer
    
-   `pages/common/` SSO、選單、角色權限、錯誤頁等系統頁
    
-   `pages/system/` 業務功能：cln-case、cln-todo、cln-approval…
    
    -   `components/` 頁面元件（html／ts／scss）
        
    -   `services/` 每頁一支 Service，負責呼叫 API
        
    -   `interfaces/` 電文 Req／Res 型別
        

設定與部署

-   `environments/` apiUrl、sourceChannel 等環境值
    
-   `assets/i18n/` zh-TW、zh-CN、en-US 語系檔
    
-   `angular.json` 建置組態（cub、tpi…）
    
-   `nginx.conf` /api/ 反向代理到後端
    
-   `Dockerfile` Node 建置 + nginx 映像
    

| 觀察面向 | 目前程式可見內容 | 閱讀提示 |
| --- | --- | --- |
| 技術棧 | Angular 8、RxJS 6、PrimeNG 8（8.1.1）、公司 UXD 套件 `cub-lib-view-primeng` 2.7.2、ngx-translate、oidc-client、angular-jwt。 | 開發注意事項寫的「PrimeNG v2.7.2」指的是 UXD 套件版本；查元件用法看 UXD 網站（見前端開發規範）。 |
| 路由 | `app-routing.module.ts` 以 `cln/case`、`cln/todo` 等路徑 lazy-load 各功能模組，外層有 AuthGuard。 | 各模組的 PermissionGuard 目前是註解狀態，權限行為需另外確認。 |
| 環境 | 開發 apiUrl 為 `http://localhost:8080`；prod／cub 為 `.`（同源，經 nginx 轉發）。 | Dockerfile 引用的建置指令與 template 檔需對照實際部署管線。 |

## API 慣例

頁面 Service 只負責「哪支 API、帶什麼電文 ID」，電文外殼、網址、Token 和錯誤處理都交給 `core/interceptors`。不要在頁面裡自己組 MWHEADER。

```
// pages/system/cln-case/services/.../cln-case-inputinfo001.service.ts
callCLNCINPTC001(req: QueryInputInfoReq): Observable<ResponseBody<QueryInputInfoRes>> {
  const params = new HttpParams().append('msgid', 'LIP-C-CLNCINPTC001').append('msgHidden', 'true');
  return this.http.post<ResponseBody<QueryInputInfoRes>>('/api/case/inputInfo/query', req, { params });
}
```

| 攔截器 | 做什麼 |
| --- | --- |
| `MwheaderInterceptor` | 取出 `msgid`，把 body 包成 `{ MWHEADER: { MSGID, TXNSEQ, SOURCECHANNEL… }, TRANRQ: body }`；FormData 上傳時改包 `RequestTemplate` 欄位。 |
| `BaseUrlInterceptor` | 在網址前加上 `environment.apiUrl`。 |
| `LanguageInterceptor`／`AuthHeaderInterceptor` | 加上語系與 `Authorization` Token。 |
| `ErrorInterceptor` | `RETURNCODE` 不是 `0000` 就顯示錯誤並拋出；成功時只回傳 `TRANRS`。帶 `msgHidden=true` 則回傳完整 body，由頁面自己判斷 RETURNCODE。也處理 401 等 HTTP 錯誤。 |
| `LoadingInterceptor` | 控制全域 loading 遮罩。 |

**msgHidden 會改變回傳型別**

沒帶 msgHidden 時，subscribe 拿到的是 TRANRS；帶了則是 `ResponseBody<T>`（含 MWHEADER）。Service 的回傳型別要跟著寫對，否則頁面會讀錯欄位。

## 頁面類型盤點

盤點 `pages/system` 下全部 110 個頁面元件（2026-10-26 掃描），依「怎麼出現在畫面上」和「做什麼事」可歸成 6 種寫法。拿到新頁面時，先判斷屬於哪一種，再找同類代表檔照著寫。

| 類型 | 數量 | 怎麼出現在畫面上 | 辨識特徵 | 代表檔 |
| --- | --- | --- | --- | --- |
| **A. 頁籤主頁** | 13 | 掛在路由上 | 上方是案件編號查詢列，下方 `p-tabView` 頁籤，每個頁籤嵌一個案件區塊；ts 很短（約 20–90 行），通常只負責切換與檢核頁籤。 | `cln-case-main001` |
| **B. 查詢清單頁** | 27 | 多數掛路由（22）；少數嵌在主頁頁籤裡（5） | 上半部 `searchForm` 查詢條件，下半部 `p-table`（lazy）+ `cub-paginator`；點列或按鈕開彈窗、或跳到作業頁。 | `cln-list-rdcommoncode001` |
| **C. 案件資料區塊** | 36 | 嵌在主頁頁籤（`@Input() applyId`）；其中 18 個是「雙模式」，也能單獨掛路由 | 用 `ngOnChanges` 監聽 applyId 變化後查詢；用 `titleNotDisplay` 判斷要不要自己顯示標題與案件編號查詢列。 | `cln-credit-highrisk001` |
| **D. 申請送出頁** | 7 | 多數嵌在主頁（5），少數掛路由（2） | 用 `@ViewChild` 抓好幾個子區塊，送出前逐一檢核表單、確認案件編號沒被改過，再呼叫「儲存」或「送出」電文。 | `cln-approval-apply001` |
| **E. 彈窗** | 23 | 由 `dialogService.open()` 開啟 | 注入 `DynamicDialogConfig`（拿父層傳入的資料）與 `DynamicDialogRef`（用 `close(結果)` 回傳）；要登記在模組的 `entryComponents`。 | `cln-list-rdcommoncode-insert-dialog` |
| **F. 特殊工具頁** | 3 | 掛在路由上 | 外部連結／影像（imglink）、資料修改（datamodify）、報表下載（report-dispatchprocess），各自獨立寫法。 | `cln-other-imglink001` |

另有 1 個共用的案件編號查詢列 `cln-comm-applyid`，被主頁與雙模式區塊重複使用，不另成一類。數量依程式特徵自動分類，少數元件同時帶有兩種特徵，歸在最主要的那一類。

### 案件編號怎麼在頁面之間流動

多數頁面都圍繞「案件編號（applyId）」運作。理解這條路徑，就知道 A、B、C 三種頁面怎麼串在一起：

B **待辦清單** 查詢清單頁

點一筆後把 ApplyId 存進 `sessionStorage`，再 `router.navigate` 到作業頁。

→

A **主頁載入** cln-comm-applyid

查詢列在 `ngOnInit` 讀到 sessionStorage 的 applyId，自動帶入並發出 `applyIdChange`。

→

A **主頁查詢** initQuery

主頁收到 applyId 後先查一次，成功才顯示頁籤（`visibleTab`）。

→

C **案件區塊** @Input() applyId

頁籤內的區塊在 `ngOnChanges` 收到 applyId，各自查自己的電文。

→

D **儲存／送出** checkApplyIdChange

送出前比對查詢列目前的編號（tempApplyId），被改過就擋下並提示重新查詢。

**雙模式區塊的開關：titleNotDisplay**

同一個區塊元件，單獨開時（路由）要自己顯示標題和案件編號查詢列；嵌進主頁時，主頁會傳 `[titleNotDisplay]="'Y'"` 把這兩塊藏起來，改由主頁統一提供 applyId。新寫區塊時，先決定要不要支援單獨開。

## 拿到頁面怎麼寫

拿到一份頁面規格（畫面＋電文）後，照下面順序做。重點是「先判斷類型、找同類代表檔」，結構照抄、只換業務內容，比從零寫更不容易漏掉專案慣例。

### 第一步：判斷頁面類型

拿到一份頁面規格

↓

按了某個按鈕才跳出來、做完要把結果交回原頁面？

是 →是 ↓

[**E**彈窗看骨架 →](#skel-e)

否 ↓

要先輸入案件編號，底下有好幾個頁籤？

是 →是 ↓

[**A**頁籤主頁看骨架 →](#skel-a)

否 ↓

有查詢條件、結果表格和分頁？

是 →是 ↓

[**B**查詢清單頁看骨架 →](#skel-b)

否 ↓

要把好幾個區塊的資料收齊，整筆「儲存／送出」？

是 →是 ↓

[**D**申請送出頁看骨架 →](#skel-d)

否 ↓

只負責顯示或編輯「某一個案件」的某一面向？

是 →是 ↓

[**C**案件資料區塊看骨架 → 需要從選單單獨開嗎？ _是_雙模式（路由＋嵌入） _否_純嵌入主頁](#skel-c)

否 ↓

**F**特殊工具頁：找功能最接近的現有頁面當範本，或先跟需求方確認規格

問題順序有意義：彈窗裡也可能有表格、申請送出頁也算在編輯某個案件，所以先問特徵最明確的，最後才問最廣的 Q5，避免歸錯類。

### 第二步之後：撰寫順序

### 讀規格，列清單

電文 ID（LIP-C-\*）、URI、Tranrq／Tranrs 欄位、要用的代碼表 CodeType、按鈕權限 key、放在哪個 feature module、是否掛在某主頁頁籤。缺任何一項先問清楚，不要猜。

### 找代表檔

到同類型、最好同 feature 的現有頁面，打開它的 component／service／interfaces／module 當範本。上方盤點表的「代表檔」是起點。

### 建檔與命名

放在 `pages/system/cln-<feature>/`：`components/cln-<feature>-<name>001/`、`services/cln-<feature>-<name>001/`，型別加進 `interfaces/cln-<feature>.ts`；selector 用 `app-cln-<feature>-<name>001`。

### 寫 interfaces

每支電文一組 Req／Res，欄位名稱照後端大寫開頭（如 `ApplyId`、`PageNumber`），每個欄位加中文註解。

### 寫 Service

一支電文一個方法，用 `HttpParams` 帶 `msgid`；需要自己判斷 RETURNCODE 才加 `msgHidden`；下載檔案用 `responseType: 'blob'`。方法上方註解寫電文 ID 與中文名稱。

### 寫 Component

依類型套用下方骨架。表單用 `FormBuilder`＋Validators；下拉選項用 `commonService.getComnCodeOptionsByCodetype()` 搭配 `mapToOptions`；開彈窗的元件要在 `providers` 放 `DialogService`。執行成功一律給 toast（`MessageService`），儲存成功要重查畫面；使用者權限從 `CommonService` 的 `userProfile$` 拿。成員依規定順序排列；FormControl 預設值用 `null`、不用 `any`、subscribe 不寫 error、不要巢狀 subscribe。

### 寫 HTML

欄位包在 `cub-input-container`，錯誤時加 `cub-invalid` 並用 `cub-invalid-feedback` 顯示訊息；按鈕權限寫 `[disabled]="!(commonService.isPermissionGranted('功能:動作') | async)"`；表格用 `p-table`＋`cub-paginator`，`th` 加 `scope="col"`。純文字欄位與表格值加 `| noblank`；數字欄位用 `lip-inputNumber`；input／textarea 停用寫 `[attr.disabled]="條件 ? true : null"`；textarea 加 `fixAutoResizeTextarea`；p-card 唯讀欄位用 `cln-card-label`／`cln-card-content`；權限不足的按鈕一律 disabled。完整清單見「Code Review 要點」。

### 登記到模組與選單

feature module 的 `declarations` 一定要加；要從選單開就在 routing module 加路徑，並在 `core/guards/function-id-auth-map.ts` 補麵包屑規格名，另外新增 LON\_MENU、LON\_MENU\_TRANSLATION、LON\_FUNCTION\_AUTH 資料；彈窗要加進 `entryComponents`（Angular 8 動態開啟的元件必須登記），並在標題下方寫元件名稱；嵌進主頁就在主頁 HTML 加上 selector 與 `[applyId]`。

### 自己測一輪並準備測試報告

成功、查無資料、必填未填、後端回錯誤碼；案件區塊要測「單獨開」與「嵌在主頁」兩種；申請頁要測改了案件編號後按送出會被擋。最後執行 `ng lint --files 檔案路徑`，並截正反向畫面（含彈窗）放進測試報告；送 CR 前可先用 AI 輔助 CR 工具自查一輪。

### 動手時的檔案位置（以 cln-case 為例）

| 步驟 | 檔案位置 | 要做什麼 |
| --- | --- | --- |
| 1\. Function ID 對應 | `src/app/core/guards/function-id-auth-map.ts` | 在 `functionIdAuthMap` 加上 URL Path 與 Function ID，例如 `['/cln/case/casemain', 'cln-case-main001'],`。先搜尋同功能區域（如 case）確認擺放位置與命名。 |
| 2\. Routing | `src/app/pages/system/cln-case/cln-case-routing.module.ts` | 在功能所屬模組的 routing 加路由，之後就能用 `http://localhost:4200/cln/case/casemain` 進畫面。 |
| 3\. Component | `src/app/pages/system/cln-case/components/` | 建畫面元件，搭配上一步的路由直接用 URL 進去確認。 |
| 4\. Service | `src/app/pages/system/cln-case/services/cln-case-main001/` | 放 API 發查方法，方法上方註解寫 MSGID 與功能說明（範例見下）。 |
| 5\. Interface | `src/app/pages/system/cln-case/interfaces/cln-case.ts` | 定義上行 Request／下行 Response。新建前先找有沒有可共用的 Interface，避免重複。 |

專案根目錄：`D:\DEVTOOLS\Projects\cln\lip-web-cln`。

#### Service 方法範例

```
/**
 * LIP-C-CLNCSMINC001 進件主頁初始查詢
 *
 * @param req
 * @returns
 */
callCLNCSMINC001(req: QueryMainReq): Observable<EmptyResp> {
  return this.http.post<EmptyResp>("/api/case/main/query", req,
    { params: { msgid: 'LIP-C-CLNCSMINC001' } })
}
```

#### Interface 共用時要標 MSGID

```
/**
 * LIP-C-CLNIAPSVC001 進件申請條件輸入儲存上行
 * LIP-C-CLNIAPSEC001 進件申請條件輸入送出上行
 */
export interface SaveAndSendApplyInputReq {
  ...
}
```

多支 API 共用同一個 Interface 時，上方要列出所有使用它的 MSGID。新 API 大部分欄位能沿用、只多幾個欄位時，依專案既有方式擴充，只補新增的欄位，擴充後的 Interface 一樣要標 MSGID。

**測試前端：直接打 URL 進頁面**

側邊選單不是 PG 自己設定的，開發測試時不要從左側選單進，直接輸入路徑，例如契據產製頁 `http://localhost:4200/cln/approval/contract`。

### 本機 Node.js 版本切換

-   到 [nodejs.org/download/release](https://nodejs.org/download/release/) 下載想要版本的 zip，解壓到 `C:\Program Files`，資料夾改名為 `nodejs`（CLI 路徑設定在這裡）。
    
    接著在 cmd 安裝 Angular CLI：`npm install -g @angular/cli@版本`，用 `ng v` 檢查版本。要換回原版本，只要把 nodejs 資料夾換回來，就能直接 `ng s`。
    
-   把全域 Angular CLI 降版（移除後重裝舊版）：
    
    `npm uninstall -g @angular/cli` → `npm cache clean --force` → `npm cache verify` → `npm install -g @angular/cli@8.3.29`
    

### 各類型骨架

以下從代表檔精簡而來，只留結構；實際欄位、電文與檢核以規格為準。

<a id="skel-a"></a>

**A. 頁籤主頁**

```
export class ClnXxxMain001Component {
  applyId: string;
  visibleTab = false;
  currentTabIndex = 0;

  applyIdChangeQuery(applyId: string) {                 // 查詢列換了案件編號：重置頁籤再查
    this.applyId = applyId; this.currentTabIndex = 0; this.visibleTab = false;
    if (applyId) { this.svc.queryMain({ ApplyId: applyId }).subscribe(() => this.visibleTab = true); }
  }
}

<app-cln-comm-applyid (applyIdChange)="applyIdChangeQuery($event)"></app-cln-comm-applyid>
<p-tabView *ngIf="visibleTab" [(activeIndex)]="currentTabIndex" (onChange)="onTabChange($event)">
  <p-tabPanel [cache]="false" header="頁籤名稱">
    <ng-template pTemplate="content">
      <app-cln-xxx-info001 [applyId]="applyId" [titleNotDisplay]="'Y'"></app-cln-xxx-info001>
    </ng-template>
  </p-tabPanel>
</p-tabView>
```

<a id="skel-b"></a>

**B. 查詢清單頁**

```
@Component({ selector: 'app-cln-xxx-list001', templateUrl: '...', providers: [DialogService] })
export class ClnXxxList001Component {
  searchForm = this.fb.group({ CodeType: [null, Validators.required] });
  hasSearched = false;                                  // 查過才顯示結果區
  paging = { perPage: 20, currentPage: 1, totalItem: 0, data: [] };
  sortInfo = { SortBy: 'ASC', SortColumn: '' };

  search() {                                            // 按「查詢」：檢核 → 回到第 1 頁
    if (this.searchForm.invalid) { this.searchForm.markAllAsTouched(); return; }
    this.paging.currentPage = 1;
    this.queryData();
  }
  queryData() {                                         // 組 Req（頁碼、筆數、排序）呼叫 API
    const req = { ...this.searchForm.getRawValue(),
      PageNumber: String(this.paging.currentPage), PageSize: String(this.paging.perPage), SortInfo: this.sortInfo };
    this.svc.queryList(req).subscribe(res => {
      this.hasSearched = true;
      this.paging.data = res.List || [];
      this.paging.totalItem = Number(res.TotalCount || 0);
    });
  }
  onPageChange(p: Paging) { this.paging.perPage = p.perPage; this.paging.currentPage = p.currentPage; this.queryData(); }
  openDialog(row?) {                                    // 新增／編輯：開彈窗，關閉有結果才重查
    const ref = this.dialogService.open(ClnXxxEditDialogComponent, { styleClass: 'cub-modal-lg', data: { Row: row } });
    ref.onClose.subscribe(result => { if (result) { this.queryData(); } });
  }
}
```

<a id="skel-c"></a>

**C. 案件資料區塊（雙模式）**

```
export class ClnXxxInfo001Component implements OnChanges {
  @Input() titleNotDisplay: string;                     // 'Y' = 嵌在主頁，不顯示標題與查詢列
  @Input() applyId: string;

  ngOnChanges(changes: SimpleChanges) {                 // 主頁傳入 applyId 時觸發
    if (changes['applyId'] && changes['applyId'].currentValue) {
      this.applyIdChangeQuery(changes['applyId'].currentValue);
    }
  }
  applyIdChangeQuery(applyId: string) {                 // 單獨開時，由查詢列 (applyIdChange) 呼叫
    this.applyId = applyId;
    this.svc.queryInfo({ ApplyId: applyId }).subscribe(res => { /* 綁資料 */ });
  }
}

<!-- HTML 開頭 -->
<ng-container *ngIf="titleNotDisplay !== 'Y'">
  <h1 class="cub-title-h1">頁面標題</h1>
  <app-cln-comm-applyid (applyIdChange)="applyIdChangeQuery($event)"></app-cln-comm-applyid>
</ng-container>
```

<a id="skel-d"></a>

**D. 申請送出頁**

```
export class ClnXxxApply001Component {
  @Input() applyId: string;
  @ViewChild('fee', { static: false }) fee: ClnCommFee001Component;     // 子區塊
  @ViewChild('caseinfo', { static: false }) caseinfo: ClnCommCaseinfo001Component;

  send() {
    if (!this.validateAllSections()) { return; }                         // 1. 每個子區塊表單都要通過
    if (this.commonService.checkApplyIdChange(this.applyId, '送出失敗')) { return; }  // 2. 案件編號沒被改
    const req = { ...this.parentForm.value, ApplyId: this.applyId, FeeInfo: this.fee.getValidData() };
    this.svc.sendApply(req).subscribe(() => {                           // 3. 送出成功：提示並重新載入
      this.messageService.add({ severity: 'success', summary: '成功', detail: '已送出' });
      this.loadData();
    });
  }
  private validateAllSections(): boolean {
    const invalid = this.fee.feeForm.invalid || this.caseinfo.caseInfoForm.invalid || this.parentForm.invalid;
    if (invalid) { /* 每個表單 markAllAsTouched() 讓紅字出現 */ }
    return !invalid;
  }
}
```

<a id="skel-e"></a>

**E. 彈窗**

```
export class ClnXxxEditDialogComponent implements OnInit {
  form = this.fb.group({ CodeName: [null, Validators.required] });
  constructor(private fb: FormBuilder, private svc: ClnXxxService,
              private config: DynamicDialogConfig, private ref: DynamicDialogRef) { }

  ngOnInit() { if (this.config.data.Row) { this.form.patchValue(this.config.data.Row); } }  // 父層傳入的資料
  save() {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.svc.update(this.form.getRawValue()).subscribe(() => this.ref.close({ saved: true }));  // 回傳結果
  }
  cancel() { this.ref.close(); }                                         // 不帶值 = 父層不處理
}

// feature module：declarations 與 entryComponents 都要加
entryComponents: [ClnXxxEditDialogComponent]

<!-- 彈窗 HTML：標題下方寫死元件名稱（麵包屑規則 b） -->
<div class="cub-modal-title mb-0">彈窗標題</div>
<div class="cub-font-12 cub-text-gray cub-text-center mb-32">(cln-xxx-edit-dialog)</div>
```

更細的命名、版面與待確認需求清單，可參考專案內的 `project-page-playbook.html`（下方可展開原始碼）。

**project-page-playbook.html 專案慣例與新頁面指南 HTML · 302 行**

lip-web-cln/docs/project-page-playbook.html

```html
<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>LIP Web CLN 專案慣例與新頁面指南</title>
  <style>
    :root {
      color-scheme: light;
      --ink: #1d2926;
      --muted: #5f6c67;
      --paper: #f4f5f1;
      --surface: #fff;
      --line: #d7ded8;
      --green: #176b55;
      --green-soft: #e7f1ec;
      --orange: #b75d29;
      --orange-soft: #fff0e5;
      --code: #edf1ee;
      font-family: "Microsoft JhengHei", "Noto Sans TC", sans-serif;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--paper);
      color: var(--ink);
      line-height: 1.7;
    }
    header {
      background: #163c32;
      color: #f7fbf8;
      padding: 42px max(24px, calc((100% - 1020px) / 2)) 38px;
      border-bottom: 5px solid #d7864b;
    }
    header p { max-width: 720px; color: #d2e2d9; margin: 10px 0 0; }
    .eyebrow { color: #b9d8c9; font-size: 12px; font-weight: 700; letter-spacing: 1.4px; }
    h1 { font-size: 30px; line-height: 1.3; margin: 8px 0; }
    h2 { font-size: 21px; margin: 0 0 14px; }
    h3 { font-size: 16px; margin: 0 0 8px; }
    main { max-width: 1020px; margin: 28px auto 60px; padding: 0 22px; }
    section { margin: 0 0 22px; }
    .panel {
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 24px;
      box-shadow: 0 3px 12px rgba(29, 41, 38, .035);
    }
    .intro { display: grid; grid-template-columns: 1.2fr .8fr; gap: 20px; align-items: start; }
    .callout { border-left: 4px solid var(--green); background: var(--green-soft); padding: 14px 16px; }
    .note { color: var(--muted); font-size: 13px; }
    .tag { display: inline-block; background: var(--green-soft); color: var(--green); font-weight: 700; font-size: 12px; padding: 2px 8px; border-radius: 3px; }
    .grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
    .item { border-top: 1px solid var(--line); padding: 12px 0 2px; }
    .item p { margin: 4px 0; color: var(--muted); }
    code, pre { font-family: Consolas, "Courier New", monospace; }
    code { background: var(--code); padding: 1px 5px; border-radius: 3px; color: #174e40; overflow-wrap: anywhere; }
    pre { white-space: pre-wrap; background: #202d29; color: #edf4ef; padding: 14px 16px; border-radius: 4px; overflow-wrap: anywhere; }
    ol { padding-left: 22px; margin: 8px 0 0; }
    li { padding: 3px 0; }
    a { color: #176b55; text-underline-offset: 3px; }
    .questions { display: grid; gap: 14px; }
    fieldset { border: 1px solid var(--line); border-radius: 5px; margin: 0; padding: 16px; min-width: 0; }
    legend { font-weight: 700; padding: 0 6px; }
    .choice { display: flex; gap: 9px; align-items: flex-start; padding: 5px 0; cursor: pointer; }
    .choice input { margin-top: 6px; accent-color: var(--green); }
    textarea, input[type="text"] {
      width: 100%; border: 1px solid #aebbb3; border-radius: 4px; padding: 10px 11px;
      color: var(--ink); background: #fff; font: inherit;
    }
    textarea { min-height: 84px; resize: vertical; }
    .actions { display: flex; flex-wrap: wrap; gap: 10px; margin: 16px 0 0; }
    button {
      border: 0; border-radius: 4px; padding: 10px 15px; font: inherit; font-weight: 700;
      cursor: pointer; background: var(--green); color: white;
    }
    button.secondary { background: #e5eae6; color: var(--ink); }
    button:hover { filter: brightness(.94); }
    #reply { min-height: 140px; margin-top: 14px; }
    .warning { background: var(--orange-soft); border-left: 4px solid var(--orange); padding: 12px 15px; }
    footer { color: var(--muted); font-size: 12px; padding: 8px 0 0; }
    @media (max-width: 680px) {
      header { padding: 30px 22px; }
      h1 { font-size: 25px; }
      .intro, .grid { grid-template-columns: 1fr; }
      .panel { padding: 18px; }
    }
  </style>
</head>
<body>
  <header>
    <div class="eyebrow">ENGINEERING NOTES / CLN WEB</div>
    <h1>專案慣例與新頁面指南</h1>
    <p>依目前專案程式與設定整理。上半部是已觀察到的寫法，下半部可填新頁需求並產生一段回覆，方便確認尚未決定的規格。</p>
  </header>

  <main>
    <section class="panel intro">
      <div>
        <h2>專案輪廓</h2>
        <p>這是以 <strong>Angular 8</strong> 建置的 CLN 前端，使用 TypeScript 3.5、PrimeNG 8、RxJS 6。功能頁集中在 <code>src/app/pages/system/&lt;feature&gt;</code>，功能模組由根路由 lazy-load。</p>
        <p class="note">這份盤點以根路由、<code>cln-other</code> 功能模組、簽核附件彈窗及訊息設定查詢頁為主要樣本；其他功能可能有局部差異，開工時仍要比照最接近的同類頁。</p>
      </div>
      <div class="callout">
        <strong>優先沿用的路徑</strong>
        <div>同一功能群的新畫面：在現有 feature module 加元件和子路由。</div>
        <div>不同功能邊界或獨立載入需求：新增 feature module，再由根路由 lazy-load。</div>
      </div>
    </section>

    <section class="panel">
      <h2>專案結構</h2>
      <p class="note">以下列出主要原始碼與設定；功能模組名稱以 <code>cln-other</code> 示意，其他 feature 會採相近結構但內容依功能調整。</p>
      <pre>lip-web-cln/
├─ angular.json, package.json, tsconfig*.json, tslint.json
├─ Dockerfile, nginx.conf
├─ docs/                         專案文件與異動紀錄
├─ e2e/                          Protractor 端對端測試
├─ fonts/                         字型資源
├─ styles/                        共用 SCSS 樣式片段
├─ src/
│  ├─ app/
│  │  ├─ core/                    全域核心服務、守衛與攔截器
│  │  ├─ layouts/                 系統版型與頁面外框
│  │  ├─ pages/
│  │  │  ├─ common/               共用系統頁（登入、錯誤等）
│  │  │  └─ system/
│  │  │     └─ cln-other/         功能模組範例
│  │  │        ├─ components/     頁面與功能元件
│  │  │        ├─ services/       該功能的 API service
│  │  │        ├─ interfaces/     Request/response 與資料型別
│  │  │        ├─ cln-other.module.ts
│  │  │        └─ cln-other-routing.module.ts
│  │  ├─ shared/                  可跨功能重用的元件、指令、pipe、服務
│  │  └─ shared-primeng/          集中匯入/匯出 PrimeNG 元件
│  ├─ assets/                     圖片、字型、語系及靜態資源
│  ├─ environments/               各環境設定
│  ├─ styles.scss                 全域樣式入口
│  ├─ main.ts, polyfills.ts       Angular 啟動與相容性設定
│  └─ index.html
└─ tmp/                           暫存/產生的建置輸出，不是主要原始碼</pre>
      <div class="grid">
        <div class="item">
          <h3>新增頁面通常會碰到</h3>
          <p><code>pages/system/&lt;feature&gt;/components</code>、<code>services</code>、<code>interfaces</code>，以及 feature 的 module 和 routing module。</p>
        </div>
        <div class="item">
          <h3>跨功能共用位置</h3>
          <p>通用 UI/管線/指令放 <code>shared</code>；PrimeNG 模組集中在 <code>shared-primeng</code>；全域認證與 HTTP 行為先查 <code>core</code>。</p>
        </div>
      </div>
    </section>

    <section class="panel">
      <h2>常見寫法</h2>
      <div class="grid">
        <div class="item">
          <h3>檔案與命名</h3>
          <p>元件採一個資料夾一組檔案：<code>.component.ts</code>、<code>.component.html</code>、<code>.component.scss</code>、<code>.component.spec.ts</code>。類別 PascalCase，selector 為 <code>app-...</code>，檔名與功能代碼保持一致。</p>
        </div>
        <div class="item">
          <h3>元件與責任</h3>
          <p>元件以 Angular decorator 指定 template/style，複雜互動放 TypeScript 方法；畫面標記與表格放 HTML。元件通常注入 service、FormBuilder、共用服務，避免把 HTTP 細節塞在 template。</p>
        </div>
        <div class="item">
          <h3>路由與模組</h3>
          <p>根路由在 <code>app-routing.module.ts</code> 以 <code>loadChildren</code> 載入功能模組；功能路由在各自的 <code>*-routing.module.ts</code> 指向頁面元件。功能模組負責 declarations 和共用模組 imports。</p>
        </div>
        <div class="item">
          <h3>表單與 UI</h3>
          <p>共用 <code>SharedModule</code> 已匯出 Forms/Reactive Forms 和專案元件；<code>SharedPrimengModule</code> 集中匯出 PrimeNG 元件。查詢表單樣本用 Reactive Forms、Validators，表格常見 <code>p-table</code>。</p>
        </div>
        <div class="item">
          <h3>Service 與 API</h3>
          <p>service 常用 <code>providedIn: 'root'</code>、HttpClient 與明確的 request/response 型別，回傳 Observable。既有 API 常以 <code>HttpParams</code> 傳 <code>msgid</code>，POST 到 <code>/api/...</code>；共用攔截器會處理通訊封裝。</p>
        </div>
        <div class="item">
          <h3>彈窗和測試</h3>
          <p>PrimeNG Dynamic Dialog 由 <code>DialogService</code> 開啟；Angular 8 的動態元件需在模組 <code>entryComponents</code> 登記。現有 spec 常見 TestBed 建立元件測試；新增功能應補上輸入驗證、查詢結果/錯誤等行為測試。</p>
        </div>
      </div>
    </section>

    <section class="panel">
      <h2>新增一個頁面的建議步驟</h2>
      <ol>
        <li><strong>先定義功能邊界與入口：</strong>確認它屬於哪個 <code>pages/system</code> feature、頁面 URL、是否需要選單/權限設定。先找同類既有頁作模板。</li>
        <li><strong>建立元件：</strong>新增 component 的 TS/HTML/SCSS/spec，沿用 feature 代碼命名；版面優先使用共用元件、PrimeNG 與 <code>cub-*</code> 樣式。</li>
        <li><strong>接上路由與模組：</strong>在 feature module imports/declarations 登記元件，在 feature routing 加路徑；若是動態 dialog，補 <code>entryComponents</code>。全新功能才評估改根路由 lazy-load。</li>
        <li><strong>定義資料契約：</strong>在該 feature 的 interfaces 定義 request/response，service 單獨處理 API URL、msgid、HttpParams 和型別；先確認後端 API 規格。</li>
        <li><strong>實作頁面狀態：</strong>明確處理初始、載入、空資料、成功、錯誤、驗證及重複送出狀態；訂閱的結果更新元件資料，錯誤訊息沿用共用訊息服務。</li>
        <li><strong>驗證與測試：</strong>補正常/異常路徑測試，執行 <code>npm test -- --watch=false</code>、<code>npm run lint</code> 和適用的 build（如 <code>npm run build:cub</code>）。</li>
        <li><strong>檢查整合：</strong>確認實際 URL、選單可達性、權限、部署環境 API 設定，以及桌面/窄螢幕的表格與表單呈現。</li>
      </ol>
      <p class="warning"><strong>容易漏掉：</strong>在 feature routing 加路由，不代表系統選單一定會出現；選單/權限可能由另一套設定提供，需依這次需求確認其維護位置。</p>
    </section>

    <section class="panel">
      <h2>待確認需求</h2>
      <p class="note">請每題選一項；若選項不合適，可在補充欄說明。按「產生回覆」會整理成可直接貼回對話的文字。</p>
      <form id="decision-form" class="questions">
        <fieldset>
          <legend>1. 這次新畫面的型態是？</legend>
          <label class="choice"><input type="radio" name="pageType" value="獨立路由頁（有自己的 URL）" required> 獨立路由頁（有自己的 URL）</label>
          <label class="choice"><input type="radio" name="pageType" value="既有頁面中的區塊或分頁"> 既有頁面中的區塊或分頁</label>
          <label class="choice"><input type="radio" name="pageType" value="彈窗／Dynamic Dialog"> 彈窗／Dynamic Dialog</label>
        </fieldset>
        <fieldset>
          <legend>2. 功能歸屬？</legend>
          <label class="choice"><input type="radio" name="feature" value="擴充既有 cln-other 功能" required> 擴充既有 <code>cln-other</code> 功能</label>
          <label class="choice"><input type="radio" name="feature" value="擴充其他既有功能（請在補充欄寫名稱）"> 擴充其他既有功能（請在補充欄寫名稱）</label>
          <label class="choice"><input type="radio" name="feature" value="新增獨立 feature module"> 新增獨立 feature module</label>
          <label class="choice"><input type="radio" name="feature" value="尚未決定，請先協助判斷"> 尚未決定，請先協助判斷</label>
        </fieldset>
        <fieldset>
          <legend>3. 頁面主要操作？</legend>
          <label class="choice"><input type="radio" name="behavior" value="查詢條件 + 結果清單／表格" required> 查詢條件 + 結果清單／表格</label>
          <label class="choice"><input type="radio" name="behavior" value="新增／編輯表單"> 新增／編輯表單</label>
          <label class="choice"><input type="radio" name="behavior" value="明細檢視或檔案下載"> 明細檢視或檔案下載</label>
          <label class="choice"><input type="radio" name="behavior" value="其他，補充如下"> 其他，補充如下</label>
        </fieldset>
        <fieldset>
          <legend>4. 資料來源與 API 規格？</legend>
          <label class="choice"><input type="radio" name="api" value="已有 API 規格，可提供 endpoint、msgid 與欄位" required> 已有 API 規格，可提供 endpoint、msgid 與欄位</label>
          <label class="choice"><input type="radio" name="api" value="API 尚未完成，先以既有介面或假資料開發"> API 尚未完成，先以既有介面或假資料開發</label>
          <label class="choice"><input type="radio" name="api" value="不需呼叫 API，由父層傳入資料"> 不需呼叫 API，由父層傳入資料</label>
          <label class="choice"><input type="radio" name="api" value="尚未確認"> 尚未確認</label>
        </fieldset>
        <fieldset>
          <legend>5. URL、選單與權限如何處理？</legend>
          <label class="choice"><input type="radio" name="access" value="需要新 URL，並加入選單／權限設定" required> 需要新 URL，並加入選單／權限設定</label>
          <label class="choice"><input type="radio" name="access" value="需要新 URL，不需要新增選單"> 需要新 URL，不需要新增選單</label>
          <label class="choice"><input type="radio" name="access" value="不需要新 URL（彈窗或頁內區塊）"> 不需要新 URL（彈窗或頁內區塊）</label>
          <label class="choice"><input type="radio" name="access" value="尚未確認"> 尚未確認</label>
        </fieldset>
        <label for="details"><strong>補充：頁面名稱/功能代碼、欄位、驗證、操作、參考畫面或其他限制</strong></label>
        <textarea id="details" name="details" placeholder="例如：查詢條件、表格欄位、按鈕行為、錯誤處理、設計參考"></textarea>
        <div class="actions">
          <button type="button" id="make-reply">產生回覆</button>
          <button type="button" class="secondary" id="copy-reply">複製回覆</button>
        </div>
        <label for="reply"><strong>回覆草稿</strong></label>
        <textarea id="reply" readonly placeholder="完成選擇後按「產生回覆」"></textarea>
        <div id="copy-status" class="note" aria-live="polite"></div>
      </form>
    </section>

    <section class="panel">
      <h2>參考程式位置</h2>
      <ul>
        <li><a href="../src/app/app-routing.module.ts">根路由與 lazy-load</a></li>
        <li><a href="../src/app/pages/system/cln-other/cln-other-routing.module.ts">cln-other 子路由</a></li>
        <li><a href="../src/app/pages/system/cln-other/cln-other.module.ts">功能模組 declarations / entryComponents</a></li>
        <li><a href="../src/app/pages/system/cln-other/components/cln-other-msgsetting001/cln-other-msgsetting001.component.ts">查詢頁元件範例</a></li>
        <li><a href="../src/app/pages/system/cln-other/services/cln-other-msgsetting001/cln-other-msgsetting001.service.ts">API service 範例</a></li>
        <li><a href="../src/app/shared/shared.module.ts">SharedModule</a>、<a href="../src/app/shared-primeng/shared-primeng.module.ts">SharedPrimengModule</a></li>
        <li><a href="../package.json">版本與 npm scripts</a>、<a href="../angular.json">Angular CLI build/test/lint 設定</a></li>
      </ul>
      <footer>建立日期：2026-10-21。版本與慣例依目前工作區內容整理；新增頁面時以同功能、同互動類型的現行程式為最終依據。</footer>
    </section>
  </main>

  <script>
    (function () {
      var form = document.getElementById('decision-form');
      var reply = document.getElementById('reply');
      var status = document.getElementById('copy-status');

      document.getElementById('make-reply').addEventListener('click', function () {
        if (!form.reportValidity()) return;
        var data = new FormData(form);
        reply.value = [
          '新頁面需求確認：',
          '1. 畫面型態：' + data.get('pageType'),
          '2. 功能歸屬：' + data.get('feature'),
          '3. 主要操作：' + data.get('behavior'),
          '4. 資料/API：' + data.get('api'),
          '5. URL/選單/權限：' + data.get('access'),
          '補充：' + (data.get('details').trim() || '無')
        ].join('\n');
        status.textContent = '回覆草稿已產生。';
      });

      document.getElementById('copy-reply').addEventListener('click', function () {
        if (!reply.value) {
          status.textContent = '請先產生回覆草稿。';
          return;
        }
        if (navigator.clipboard && window.isSecureContext) {
          navigator.clipboard.writeText(reply.value).then(function () {
            status.textContent = '已複製回覆草稿。';
          });
        } else {
          reply.focus();
          reply.select();
          status.textContent = '瀏覽器不允許直接複製，已選取草稿文字，請使用 Ctrl+C。';
        }
      });
    }());
  </script>
</body>
</html>
```

## 完整案例

以「進件輸入」頁為例，從前端一路追到組合層與基礎層。後端 Query 章節的範例（CQYCINPTQ001）就是這條鏈的最後一站。

### 路由進入頁面

`cln/case` lazy-load ClnCaseModule，子路徑 `inputinfo` 對應 ClnCaseInputinfo001Component。

### Component 初始化並查詢

建立 InputInfo FormGroup，呼叫 `svc.callCLNCINPTC001(req)`；因帶 msgHidden，自己檢查 `res.MWHEADER.RETURNCODE`。

### Service 發出請求

`POST /api/case/inputInfo/query`，msgid 為 LIP-C-CLNCINPTC001；攔截器包成 MWHEADER + TRANRQ 並補 Token。

### nginx 轉發到組合層

`/api/` 轉給 lip-svc-cln，由 CaseController 的 `/inputInfo/query` 交給 CLNCINPTC001SvcImpl。

### 組合層呼叫基礎層

CLNCINPTC001SvcImpl 用 `restTempHelper.postForEntity` 送出電文 `LIP-B-CQYCINPTQ001`，由 lip-svc-cln-query 的 CQYCINPTQ001SvcImpl 查資料後回傳。

### 儲存走另一支電文

使用者確認後呼叫 `callCLNCINPTC002`（`POST /api/case/inputInfo/modify`，LIP-C-CLNCINPTC002），組合層再呼叫 `LIP-B-CTNCINPTT001` 由 transaction 寫入；成功時以 MessageService 顯示提示。

**app-routing.module.ts 頂層路由與 lazy-load TypeScript · 155 行**

lip-web-cln/src/app/app-routing.module.ts

```typescript
import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { BaseLayoutComponent } from 'app/layouts/base-layout/base-layout.component';
import { ForbiddenComponent } from 'app/pages/common/forbidden/forbidden.component';
import { LogoutComponent } from 'app/pages/common/logout/logout.component';
import { NotFoundComponent } from 'app/pages/common/not-found/not-found.component';
import { RedirectComponent } from 'app/pages/common/redirect/redirect.component';
import { SsoComponent } from 'app/pages/common/sso/sso.component';
import { AuthGuard } from './core/guards/auth.guard';
import { PermissionGuard } from './core/guards/permission.guard';
import { UnauthComponent } from './pages/common/unauth/unauth.component';
import { PdfViewerComponent } from './shared/components/pdf-viewer/pdf-viewer.component';

const routes: Routes = [
  {
    path: '',
    component: BaseLayoutComponent,
    canActivate: [AuthGuard],
    children: [
      {
        path: 'cln/rule',
        loadChildren: () => import('./pages/system/cln-rule/cln-rule.module').then(mod => mod.ClnRuleModule),
        // canActivateChild: [PermissionGuard]
      },
      {
        path: 'cln/comm',
        loadChildren: () => import('./pages/system/cln-common/cln-common.module').then(mod => mod.ClnCommonModule),
        // canActivateChild: [PermissionGuard]
      },
      {
        path: 'cln/case',
        loadChildren: () => import('./pages/system/cln-case/cln-case.module').then(mod => mod.ClnCaseModule),
        // canActivateChild: [PermissionGuard]
      },
      {
        path: 'cln/todo',
        loadChildren: () => import('./pages/system/cln-todo/cln-todo.module').then(mod => mod.ClnTodoModule),
        // canActivateChild: [PermissionGuard]
      },
      {
        path: 'cln/product',
        loadChildren: () => import('./pages/system/cln-product/cln-product.module').then(mod => mod.ClnProductModule),
        // canActivateChild: [PermissionGuard]
      },
      {
        path: 'cln/channel',
        loadChildren: () => import('./pages/system/cln-channel/cln-channel.module').then(mod => mod.ClnChannelModule),
        // canActivateChild: [PermissionGuard]
      },
      {
        path: 'cln/supply',
        loadChildren: () => import('./pages/system/cln-supply/cln-supply.module').then(mod => mod.ClnSupplyModule),
        // canActivateChild: [PermissionGuard]
      },
      {
        path: 'cln/review',
        loadChildren: () => import('./pages/system/cln-review/cln-review.module').then(mod => mod.ClnReviewModule),
        // canActivateChild: [PermissionGuard]
      },
      {
        path: 'cln/credit',
        loadChildren: () => import('./pages/system/cln-credit/cln-credit.module').then(mod => mod.ClnCreditModule),
        // canActivateChild: [PermissionGuard]
      },
      {
        path: 'cln/dispatch',
        loadChildren: () => import('./pages/system/cln-dispatch/cln-dispatch.module').then(mod => mod.ClnDispatchModule),
        // canActivateChild: [PermissionGuard]
      },
      {
        path: 'cln/other',
        loadChildren: () => import('./pages/system/cln-other/cln-other.module').then(mod => mod.ClnOtherModule),
        // canActivateChild: [PermissionGuard]
      },
      {
        path: 'cln/management',
        loadChildren: () => import('./pages/system/cln-management/cln-management.module').then(mod => mod.ClnManagementModule),
        // canActivateChild: [PermissionGuard]
      },
      {
        path: 'cln/listbatch',
        loadChildren: () => import('./pages/system/cln-list-batch/cln-list-batch.module').then(mod => mod.ClnListBatchModule),
        // canActivateChild: [PermissionGuard]
      },
      {
        path: 'cln/project',
        loadChildren: () => import('./pages/system/cln-project/cln-project.module').then(mod => mod.ClnProjectModule),
        // canActivateChild: [PermissionGuard]
      },
      {
        path: 'cln/approval',
        loadChildren: () => import('./pages/system/cln-approval/cln-approval.module').then(mod => mod.ClnApprovalModule),
        // canActivateChild: [PermissionGuard]
      },
      {
        path: 'cln/list',
        loadChildren: () => import('./pages/system/cln-list/cln-list.module').then(mod => mod.ClnListModule),
        // canActivateChild: [PermissionGuard]
      },
      {
        path: 'cln/report',
        loadChildren: () => import('./pages/system/cln-report/cln-report.module').then(mod => mod.ClnReportModule),
        // canActivateChild: [PermissionGuard]
      },
      {
        path: 'redirect',
        component: RedirectComponent
      },
      // {
      //   path: 'menu',
      //   loadChildren: () => import('./pages/common/menu/menu.module').then(mod => mod.MenuModule),
      //   canActivateChild: [PermissionGuard]
      // },
      // {
      //   path: 'switch',
      //   component: SwitchComponent
      // },
    ]
  },
  {
    path: 'logout',
    component: LogoutComponent
  },
  {
    path: 'sso',
    component: SsoComponent
  },
  {
    path: 'pdf',
    component: PdfViewerComponent
  },
  {
    path: '403',
    component: ForbiddenComponent
  },
  {
    path: '404',
    component: NotFoundComponent
  },
  {
    path: '401',
    component: UnauthComponent
  },
  {
    path: '**',
    component: NotFoundComponent
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule],
  providers: [PermissionGuard]
})
export class AppRoutingModule { }
```

**core.module.ts 攔截器註冊順序 TypeScript · 87 行**

lip-web-cln/src/app/core/core.module.ts

```typescript
import { CommonModule } from '@angular/common';
import { HttpBackend, HttpClient, HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { NgModule, Optional, SkipSelf } from '@angular/core';
import { TranslateLoader, TranslateModule } from '@ngx-translate/core';
import { TranslateHttpLoader } from '@ngx-translate/http-loader';
import { AuthService } from 'app/core/services/auth.service';
import { CustomLoader } from 'app/core/services/custom-loader';
import { JwtAuthService } from 'app/core/services/jwt-auth.service';
import { ConfirmationService, MessageService } from 'primeng/api';
import { AuthHeaderInterceptor } from './interceptors/auth-header-interceptor';
import { BaseUrlInterceptor } from './interceptors/base-url-interceptor';
import { ErrorInterceptor } from './interceptors/error-interceptor';
import { LanguageInterceptor } from './interceptors/language-interceptor';
import { LoadingInterceptor } from './interceptors/loading-interceptor';
import { MwheaderInterceptor } from './interceptors/mwheader-interceptor';
import { NotifyService } from './services/notify.service';


// AoT requires an exported function for factories
export function httpLoaderFactory(handler: HttpBackend) {
  return new TranslateHttpLoader(new HttpClient(handler), './assets/i18n/');
}

@NgModule({
  imports: [
    CommonModule,
    HttpClientModule,
    TranslateModule.forRoot({
      loader: {
        provide: TranslateLoader,
        useClass: CustomLoader
      }
    })
  ],
  providers: [
    ConfirmationService,
    MessageService,
    NotifyService,
    {
      provide: HTTP_INTERCEPTORS,
      useClass: MwheaderInterceptor,
      multi: true
    },
    {
      provide: HTTP_INTERCEPTORS,
      useClass: BaseUrlInterceptor,
      multi: true
    },
    {
      provide: HTTP_INTERCEPTORS,
      useClass: LanguageInterceptor,
      multi: true
    },
    {
      provide: HTTP_INTERCEPTORS,
      useClass: AuthHeaderInterceptor,
      multi: true
    },
    {
      provide: HTTP_INTERCEPTORS,
      useClass: ErrorInterceptor,
      multi: true
    },
    {
      provide: HTTP_INTERCEPTORS,
      useClass: LoadingInterceptor,
      multi: true
    },
    {
      provide: AuthService,
      useClass: JwtAuthService
    },
  ],
  declarations: []
})
export class CoreModule {
  /* make sure CoreModule is imported only by one NgModule the AppModule */
  constructor(
    @Optional()
    @SkipSelf()
    parentModule: CoreModule
  ) {
    if (parentModule) {
      throw new Error('CoreModule is already loaded. Import only in AppModule');
    }
  }
}
```

**mwheader-interceptor.ts 電文外殼包裝 TypeScript · 56 行**

lip-web-cln/src/app/core/interceptors/mwheader-interceptor.ts

```typescript
import { formatDate } from '@angular/common';
import { HttpEvent, HttpHandler, HttpInterceptor, HttpRequest } from '@angular/common/http';
import { Inject, Injectable, LOCALE_ID } from '@angular/core';
import { environment } from 'env/environment';
import { Observable } from 'rxjs';

@Injectable()
export class MwheaderInterceptor implements HttpInterceptor {

  constructor(@Inject(LOCALE_ID) private locale: string) { }

  public intercept(
    req: HttpRequest<any>,
    next: HttpHandler
  ): Observable<HttpEvent<any>> {
    const data = req.body;
    const msgid = req.params.get('msgid');
    if (data instanceof FormData) {
      this.processFormData(msgid, data);
      return next.handle(req);
    }

    const requestModel = this.mwheaderWapprer(msgid, data);

    req = req.clone({ params: req.params.delete('msgid'), body: requestModel });
    return next.handle(req);
  }

  private mwheaderWapprer(msgid: string, obj: any) {
    return {
      MWHEADER: {
        TXNSEQ:
          formatDate(Date.now(), 'yyyyMMddHHmmssSSS', this.locale) +
          Math.random()
            .toString(36)
            .substring(2, 5),
        RETURNMESSAGE: '',
        RETURNCODE: '',
        MSGID: msgid,
        SOURCECHANNEL: environment.sourceChannel,
      },
      TRANRQ: obj
    };
  }

  private processFormData(msgid: string, formData: FormData): FormData {
    const requestTemplate = formData.get('RequestTemplate') as string;
    const newRequestTemplate = this.mwheaderWapprer(msgid, JSON.parse(requestTemplate));

    formData.set('RequestTemplate', new Blob([JSON.stringify(newRequestTemplate)], {
      type: 'application/json',
    }));

    return formData;
  }
}
```

**error-interceptor.ts RETURNCODE 與 HTTP 錯誤處理 TypeScript · 135 行**

lip-web-cln/src/app/core/interceptors/error-interceptor.ts

```typescript
import { HttpErrorResponse, HttpEvent, HttpHandler, HttpInterceptor, HttpRequest, HttpResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { MessageUtilService } from 'app/core/services/message-util.service';
import { AlertDialogComponent } from 'app/shared/components/alert-dialog/alert-dialog.component';
import { CommonService } from 'app/shared/services/common.service';
import { DialogService, DynamicDialogRef, MessageService } from 'primeng/api';
import { EMPTY, Observable, of, throwError } from 'rxjs';
import { catchError, concatMap } from 'rxjs/operators';
import { NotifyService } from '../services/notify.service';


@Injectable()
export class ErrorInterceptor implements HttpInterceptor {
  constructor(
    private notifyService: NotifyService,
    private router: Router,
    private messageService: MessageService,
    private messageUtil: MessageUtilService,
    private dialogService: DialogService,
    private commonService: CommonService,
  ) { }

  correlationFlag = 'x-isshowcorrelationflag';
  correlationId = 'x-correlation-id';
  dialogRef: DynamicDialogRef[] = [];

  public intercept(
    req: HttpRequest<any>,
    next: HttpHandler
  ): Observable<HttpEvent<any>> {

    return next.handle(req).pipe(
      concatMap(event => {
        if (event instanceof HttpResponse && event.body) {
          localStorage.setItem('tokenTime', new Date().getTime().toString());
          // 如果是msgHidden為true，一律回傳event.body
          const msgHidden = req.params.get('msgHidden');
          if (msgHidden === 'true') {
            return of(event.clone({ body: event.body }));
          }
          if (event.body.isSuccess === false) {
            let message = event.body.returnMessage;
            const flag = event.headers.get(this.correlationFlag);
            if (flag) {
              message += `，Trace Id:${event.headers.get(this.correlationId)}`;
            }
            this.notifyService
              .confirmAcceptOnly(message, 'notifyErrorTitle')
              .subscribe();
            this.messageService.add({ severity: 'info', detail: 'Req Success' });
            return throwError(event.body);
          } else if (event.body.MWHEADER && event.body.MWHEADER.RETURNCODE !== '0000') {
            this.messageUtil.setErrorMsg(event.body.MWHEADER);
            return throwError(event.body);
          }
          // 將 ResponseTemplate.data 取出
          return of(event.clone({ body: event.body.TRANRS || event.body.data || event.body.Body || event.body }));
        }
        return of(event);
      }),
      catchError(e => {
        if (e instanceof HttpErrorResponse) {
          if (e.status === 401) {
            if (this.dialogRef.length > 0) {
              return EMPTY;
            }
            const ref = this.dialogService.open(AlertDialogComponent, {
              styleClass: 'cub-modal-md',
              dismissableMask: true,
              data: {
                title: '你已經被登出了，請重新登入',
                description: ' '
              }
            });

            this.dialogRef.push(ref);
            ref.onClose.subscribe(_ => {
              this.commonService.logoutImpl();
            });
            return EMPTY;
          } else if (e.status === 403) {
            this.router.navigate(['/403'], { skipLocationChange: true });
            return EMPTY;
          } else if (e.status === 405) {
            this.dialogRef.push(this.messageUtil.setErrorMsg(null, true, this.dialogRef));
            return EMPTY;
          } else if (e.status === 419) {
            // 419無權限/SessionTimeOut，直接導至/sso
            this.router.navigate(['/sso']);
            return EMPTY;
          } else if (e.status === 500) {
            if (e.error.isSuccess !== true) {
              let message = e.error.message;
              const flag = e.headers.get(this.correlationFlag);
              if (flag) {
                message += `，${e.headers.get(this.correlationId)}`;
              }
              this.notifyService
                .confirmAcceptOnly(message, 'notifyErrorTitle')
                .subscribe();
              return EMPTY;
            }
          } else if (e.status === 504) {
            this.dialogService.open(AlertDialogComponent, {
              styleClass: 'cub-modal-md cub-modal-error',
              dismissableMask: true,
              data: {
                title: 'COMMON.SYSTEM_ERROR_MODAL_TITLE',
                subTitle: 'COMMON.SYSTEM_ERROR_MODAL_SUBTITLE',
                description: '交易逾時'
              }
            });
            return EMPTY;
          } else {
            this.dialogService.open(AlertDialogComponent, {
              styleClass: 'cub-modal-md cub-modal-error',
              dismissableMask: true,
              data: {
                title: 'COMMON.SYSTEM_ERROR_MODAL_TITLE',
                subTitle: 'COMMON.SYSTEM_ERROR_MODAL_SUBTITLE',
                description: e.status + ': ' + e.message
              }
            });
            return EMPTY;
          }
          this.messageUtil.setErrorMsg(null, e.error)
          return throwError(e.error);
        }
        return EMPTY;
      })
    );
  }

}
```

**cln-case-inputinfo001.component.ts 進件輸入頁面 TypeScript · 262 行**

lip-web-cln/src/app/pages/system/cln-case/components/cln-case-inputinfo001/cln-case-inputinfo001.component.ts

```typescript
import { Component, Input, OnChanges, OnInit, SimpleChanges, ViewChild } from '@angular/core';
import { AbstractControl, FormBuilder, FormGroup, ValidationErrors, ValidatorFn, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ClnCommBranchorigin001Component } from 'app/pages/system/cln-common/components/cln-comm-branchorigin001/cln-comm-branchorigin001.component';
import { AlertDialogComponent } from 'app/shared/components/alert-dialog/alert-dialog.component';
import { ConfirmDialogComponent } from 'app/shared/components/comfirm-dialog/confirm-dialog.component';
import { BorGuar } from 'app/shared/interfaces/bor-guar';
import { CommonService } from 'app/shared/services/common.service';
import { DialogService, MessageService } from 'primeng/primeng';
import { ToastModule } from 'primeng/toast';
import { CaseService } from '../../../../../shared/services/case.service';
import { ModifyInputInfoReq, QueryInputInfoReq } from '../../interfaces/cln-case';
import { ClnCaseInputinfo001Service } from '../../services/cln-case-inputinfo001/cln-case-inputinfo001.service';
import { ClnCaseBorguarList001Component } from '../cln-case-borguar-list001/cln-case-borguar-list001.component';

@Component({
  selector: 'app-cln-case-inputinfo001',
  templateUrl: './cln-case-inputinfo001.component.html',
  styleUrls: ['./cln-case-inputinfo001.component.scss'],
  providers: [DialogService, ToastModule]
})
export class ClnCaseInputinfo001Component implements OnInit, OnChanges {

  /** 案件編號 */
  @Input() applyId: string;

  /** 進件單位及案件來源共用元件 */
  @ViewChild('branchOrigin001', { static: false }) branchOrigin001: ClnCommBranchorigin001Component;

  /** 進件輸入 */
  InputInfo: FormGroup = this.fb.group({
    LoanTypeName: '',
    ApplyId: '',
    BorrowId: '',
    BorrowName: ['', [Validators.required, this.validateBorrowName()]],
    BefApplyId: '',
    OriginName: '',
    ApplyProcessName: '',
    IsOnlineApplyName: '',
    ApplyProcess: '',
    LoanType: '',
    GageType: '',
    AoHeadId: '',
    AoHeadName: '',
    AoHeadBranch: '',
    AoHeadBranchName: '',
    IsEffectBranch: '',
  });

  /** 借保人資訊 */
  borGuarList: BorGuar[] = [];

  /** 是否有資料 */
  hasData = false;

  constructor(
    private fb: FormBuilder,
    private svc: ClnCaseInputinfo001Service,
    private dialogService: DialogService,
    public commonService: CommonService,
    public caseService: CaseService,
    private messageService: MessageService,
    private route: ActivatedRoute,
    private router: Router
  ) { }

  ngOnInit(): void {
    const routeApplyId = this.route.snapshot.queryParams.ApplyId || '';
    if (routeApplyId && this.router.url.indexOf('?') >= 0) {
      this.router.navigateByUrl(this.router.url.split('?')[0]);
    }

    if (!this.applyId) {
      this.applyId = routeApplyId || sessionStorage.getItem('applyId') || '';
    }

    this.init();
  }

  ngOnChanges(changes: SimpleChanges): void {
    const applyIdChange = changes['applyId'];
    if (applyIdChange && !applyIdChange.firstChange && applyIdChange.currentValue !== applyIdChange.previousValue) {
      this.applyId = applyIdChange.currentValue || '';
      this.init();
    }
  }

  /** 初始化填值 */
  init(): void {
    const applyId = this.applyId || this.InputInfo.get('ApplyId').value;
    if (!applyId) {
      this.clearData();
      return;
    }

    const req: QueryInputInfoReq = {
      ApplyId: applyId
    };

    this.svc.callCLNCINPTC001(req).subscribe((res) => {
      if (res.MWHEADER.RETURNCODE !== '0000') {
        this.applyId = null;
        sessionStorage.removeItem('applyId');
        this.dialogService.open(AlertDialogComponent, {
          styleClass: 'cub-modal-md cub-modal-error',
          data: { title: '查詢失敗', description: res.MWHEADER.RETURNDESC },
        });
        this.clearData();
        return;
      }

      if (!res.TRANRS.ApplyId) {
        this.clearData();
        return;
      }

      this.hasData = true;
      this.applyId = res.TRANRS.ApplyId;
      this.InputInfo.patchValue({
        ...res.TRANRS,
        OriginName: res.TRANRS.ReapplyReason || ''
      });

      this.borGuarList = (res.TRANRS.BorGuarList ? res.TRANRS.BorGuarList : [])
        .sort((a, b) => (a.Type === '1' ? -1 : 1));
    });
  }

  /** 清除資料並隱藏下方區塊 */
  private clearData(): void {
    this.hasData = false;
    this.InputInfo.reset();
    this.borGuarList = [];
  }

  /** 新增/編輯按鈕 */
  addBorGuar(): void {
    const ref = this.dialogService.open(ClnCaseBorguarList001Component, {
      styleClass: 'cub-modal-xl',
      dismissableMask: false,
      data: {
        BorGuarList: this.borGuarList,
        GageType: this.InputInfo.get('GageType').value
      }
    });

    ref.onClose.subscribe((result) => {
      if (result) {
        this.borGuarList = result;
        if (this.borGuarList.length > 0) {
          this.InputInfo.get('BorrowName').setValue(this.borGuarList[0].BorGuarName);
        }
      }
    });
  }

  /** 刪除 */
  delete() {
    // 檢核案件編號輸入框值是否異動
    if (this.commonService.checkApplyIdChange(this.applyId, '刪除失敗')) {
      return;
    }
    const ref = this.dialogService.open(ConfirmDialogComponent, {
      styleClass: 'cub-modal-md cub-modal-error',
      dismissableMask: true,
      data: {
        title: '確認刪除',
        description: `是否刪除案件${this.InputInfo.get('ApplyId').value}`,
        confirmBtn: {
          label: '確認',
          style: 'danger'
        },
        cancelBtn: {
          label: '取消',
          style: 'secondary'
        }
      }
    });

    ref.onClose.subscribe((response) => {
      if (response === 'confirm') {
        const req: ModifyInputInfoReq = {
          ActionType: 'D',
          ApplyId: this.InputInfo.get('ApplyId').value,
          GageType: this.InputInfo.get('GageType').value
        };

        this.svc.callCLNCINPTC002(req).subscribe(res => {
          if (res) {
            this.messageService.add({
              severity: 'success',
              summary: 'Success',
              detail: '刪除成功',
              life: 5000,
            });
            this.init();
          } else {
            console.log(res); // TODO 等刪除檢核
          }
        });
      }
    });
  }

  /** 儲存 */
  save(): void {
    // 檢核案件編號輸入框值是否異動
    if (this.commonService.checkApplyIdChange(this.applyId, '儲存失敗')) {
      return;
    }

    const inputBranchInfo = this.branchOrigin001 ? this.branchOrigin001.getValidData() : null;
    if (this.InputInfo.invalid || !inputBranchInfo) {
      this.InputInfo.markAllAsTouched();
      return;
    }

    const req: ModifyInputInfoReq = {
      ActionType: 'M',
      ApplyId: this.InputInfo.get('ApplyId').value,
      ApplyProcess: this.InputInfo.get('ApplyProcess').value,
      LoanType: this.InputInfo.get('LoanType').value,
      GageType: this.InputInfo.get('GageType').value,
      BorrowName: this.InputInfo.get('BorrowName').value,
      ReapplyReason: this.InputInfo.get('OriginName').value,
      BorGuarList: this.borGuarList,
      InputBranchInfo: inputBranchInfo,
      IsEffectBranch: this.InputInfo.get('IsEffectBranch').value
    };

    this.svc.callCLNCINPTC002(req).subscribe(res => {
      if (res) {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: '儲存成功',
          life: 5000,
        });
        this.init();
        if (this.branchOrigin001) {
          this.branchOrigin001.refresh();
        }
      }
    });
  }

  /** 特殊符號檢核 */
  validateBorrowName(): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      const value = control.value;
      if (!value) {
        return null;
      }

      if (this.caseService.hasSpecialChar(value)) {
        return { invalidChar: true };
      }

      return null;
    };
  }
}
```

**cln-case-inputinfo001.service.ts 查詢／維護電文呼叫 TypeScript · 45 行**

lip-web-cln/src/app/pages/system/cln-case/services/cln-case-inputinfo001/cln-case-inputinfo001.service.ts

```typescript
import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { ResponseBody } from 'app/core/interfaces/response-body';
import { Observable } from 'rxjs';
import { ModifyInputInfoReq, QueryEmployeeDepartmentReq, QueryEmployeeDepartmentRes, QueryInputInfoReq, QueryInputInfoRes } from '../../interfaces/cln-case';

@Injectable({
  providedIn: 'root'
})
export class ClnCaseInputinfo001Service {

  constructor(private http: HttpClient) { }

  /**
   * LIP-C-CLNCINPTC001 查詢進件輸入資訊
   *
   * @param {QueryInputInfoReq} req
   * @returns {*}  {Observable<QueryInputInfoRes>}
   * @memberof ClnCaseInputinfo001Service
   */
  callCLNCINPTC001(req: QueryInputInfoReq): Observable<ResponseBody<QueryInputInfoRes>> {
    const params = new HttpParams().append('msgid', 'LIP-C-CLNCINPTC001').append('msgHidden', 'true');
    return this.http.post<ResponseBody<QueryInputInfoRes>>("/api/case/inputInfo/query", req, { params })
  }

  /**
   * LIP-C-CLNEMPDTQ001 查詢人員部門資訊
   *
   * @param req
   * @returns
   */
  callCLNEMPDTQ001(req: QueryEmployeeDepartmentReq): Observable<QueryEmployeeDepartmentRes> {
    return this.http.post<QueryEmployeeDepartmentRes>("/api/common/empDept/query", req, { params: { msgid: 'LIP-C-CLNEMPDTQ001' } })
  }

  /**
   * LIP-C-CLNCINPTC002 進件輸入維護
   *
   * @param req
   * @returns
   */
  callCLNCINPTC002(req: ModifyInputInfoReq): Observable<{}> {
    return this.http.post("/api/case/inputInfo/modify", req, { params: { msgid: 'LIP-C-CLNCINPTC002' } })
  }
}
```

**nginx.conf /api/ 轉發到 lip-svc-cln nginx · 46 行**

lip-web-cln/nginx.conf

```
worker_processes auto;
error_log stderr;
pid /tmp/nginx.pid;
events {
    worker_connections 1024;
}

http {
    include       mime.types;
    default_type  application/octet-stream;

    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

    sendfile        on;
    #tcp_nopush     on;

    #keepalive_timeout  0;
    keepalive_timeout  65;

    gzip  on;

    client_max_body_size 30M;

  server {
      listen 8080;
      root  /usr/share/nginx/html;

      location /api/ {
            proxy_pass http://lip-svc-cln.lonlxlip01:8080/api/;
            proxy_redirect off;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Host $server_name;
      }

      location / {
          root /usr/share/nginx/html;
          index index.html index.htm;
          try_files $uri $uri/ /index.html =404;
          add_header Cache-Control 'max-age=86400'; # one day
      }
  }
}
```

**lip-svc-cln CaseController.java 後端對應入口 Java · 389 行**

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

## 交付檢查

-   [ ] 麵包屑已補規格名（function-id-auth-map 或彈窗標題下方），LON\_MENU 等選單資料已新增。
-   [ ] 文字與表格值加 noblank、th 加 scope、停用寫 \[attr.disabled\]、成功有 toast 且儲存後重查。
-   [ ] ng lint 無錯誤，正反向截圖（含彈窗）已放進測試報告。
-   [ ] 已依「Code Review 要點」自查（可用 AI 輔助 CR 工具），並比對程式與規格書 md 的邏輯一致。
-   [ ] 已判斷頁面類型，結構比照同類代表檔；元件已登記 declarations（彈窗另加 entryComponents）。
-   [ ] 案件區塊測過單獨開與嵌在主頁兩種；申請頁會擋下案件編號被改過的送出。
-   [ ] URI 與 msgid 對應到 lip-svc-cln 的 LIP-C 電文（前端不直接呼叫 LIP-B 基礎層 API）。
-   [ ] Req／Res 型別與後端 Tranrq／Tranrs 欄位一致；msgHidden 與回傳型別相符。
-   [ ] 表單驗證、查無資料、錯誤訊息與 loading 行為已確認。
-   [ ] 路由、選單與權限設定完成，三種語系文字都有補。
