# 05. Ajax、SPA 與路由

> 🏠 **生活化版本**：每個段落開頭的「生活比喻」先用日常情境帶你抓到感覺，接著再看原本的技術說明與程式碼；篇末有「比喻對照表」可以快速複習。

> 來源：[筆記平台 · Angular](https://hhtim.github.io/notes-platform/angular/#/lesson/ajax-spa)　第 5 課 / 共 7 課 · 約 9 分鐘

**從非同步請求理解單頁應用程式，設定 Angular Router、導覽與各種路由傳參方式。**

### 讀完這課你會

*   說出 Ajax、SPA 與 Angular Router 的關係
*   設定路由與 `router-outlet`，萬用路由放最後
*   分清路徑參數與查詢參數，會用 `routerLink`

*【網路互動基礎】*

## Ajax 不是某一套函式庫

> 🏠 **生活比喻**
>
> Ajax 像**用手機點外送**，不用親自去店裡排隊：下單後你照樣追劇，餐到了再開門拿。
> 而且是**只換掉桌上那盤菜**（局部更新），不是把整桌收掉重擺（整頁重載）。

Ajax（Asynchronous JavaScript and XML）是一組「在瀏覽器裡非同步交換資料、局部更新畫面」的做法，不是單一技術。名稱裡的 XML 是歷史痕跡，現代更常交換 JSON；實作可以用瀏覽器原生的 Fetch API、Angular 的 `HttpClient`，或其他 HTTP 工具。

同步請求像站在櫃台前傻等，等到回覆前什麼都不能做；非同步請求像先抽號碼牌，等待期間照常做別的事，結果送到再更新畫面。

> 非同步不保證回應更快，它讓應用程式不必在等待期間卡住其他工作

*【單頁應用程式】*

## SPA 只換內容、不重載整頁

> 🏠 **生活比喻**
>
> SPA 像**舞台劇換布景**：觀眾一直坐在同一間劇場（同一頁），只是舞台上的布景換了，不用全部人離場再進另一間劇場。
> 但後台還是要一直送道具上來（API 資料、圖片）；想要「停電也能演」（離線使用），得另外準備**發電機**（Service Worker）。

單頁應用程式（Single-Page Application，SPA）先載入一個應用程式外殼（版面骨架），之後的頁面切換由 JavaScript 依操作更新內容，不再整頁重新載入。Gmail 是經典例子：讀信、回信都在同一頁完成。

SPA 帶來流暢切換與前後端分工，但別誤會成「之後都不需要伺服器」：API 資料、按路由切割的程式碼檔、圖片仍會經由網路載入。初次載入速度、搜尋引擎收錄與錯誤處理也要另外設計。「離線也能用」常被當成 SPA 的天生優勢——其實那要另外實作 Service Worker（瀏覽器背景腳本，可攔截請求做快取）之類的機制才有，不是 SPA 內建。

*【現代 Angular Router】*

## 設定路由與出口

> 🏠 **生活比喻**
>
> 路由像**百貨公司大廳的樓層導覽**：你說要去哪（網址），導覽員查表，把對應的店（元件）帶到**電梯門口**（`router-outlet`）。
> 導覽表由上往下查、先查到先算。萬用路由 `**` 是「找不到的請洽服務台」，一定要寫在**最後一行**；寫在第一行的話，所有客人都會被直接帶去服務台。

SPA 的網址管理靠路由（Router）：它比對目前網址，把對應的元件放進樣板裡的 `router-outlet`。

```
import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: 'home', pathMatch: 'full' },
  { path: 'home', loadComponent: () =>
      import('./home.component').then(m => m.HomeComponent) },
  { path: 'users/:id', loadComponent: () =>
      import('./user.component').then(m => m.UserComponent) },
  { path: '**', loadComponent: () =>
      import('./not-found.component').then(m => m.NotFoundComponent) }
];
```

```
bootstrapApplication(AppComponent, {
  providers: [provideRouter(routes)]
});
```

```
<nav>...</nav>
<router-outlet />
```

路由由上而下、先到先得地配對，所以萬用路由 `**`（什麼都能配的 404 路由）一定放最後，不然所有網址都會被它搶走、永遠顯示 404。

*【導覽】*

## routerLink 與程式式導覽

> 🏠 **生活比喻**
>
> - `routerLink="/home"`＝**捷運站的固定指示牌**。
> - `[routerLink]="['/users', id]"`＝**填空式地址**：「XX 路 ＿＿ 號」。
> - `router.navigate()`＝**計程車司機**：等事情辦完，再依情況載你過去。
> - `router.navigateByUrl()`＝直接給司機一個完整地址。
> - `routerLinkActive`＝**到站時亮起的燈**；`exact: true` 是「真的到站才亮」，而不是只要在這條線上就一直亮。

| 方式 | 適用情境 |
| --- | --- |
| `routerLink="/home"` | 固定路徑，字串就夠。 |
| `[routerLink]="['/users', user.id]"` | 路徑帶參數時用陣列語法。 |
| `router.navigate(...)` | 在 TypeScript 裡，事件或邏輯完成後導覽。 |
| `router.navigateByUrl(...)` | 手上已有完整的網址字串。 |

```
<a
  [routerLink]="['/users', user.id]"
  routerLinkActive="active">
  {{ user.name }}
</a>
```

一句話分工：`routerLink` 決定要去哪裡，`routerLinkActive` 決定「到了」之後套什麼 CSS class，`routerLinkActiveOptions` 決定什麼條件算「到了」。首頁 `/` 這種短路徑預設用部分比對、很容易永遠是「到了」，可設 `[routerLinkActiveOptions]="{ exact: true }"`（方括號不能省，否則傳進去的是字串）[出處](https://angular.dev/api/router/RouterLinkActive) 改成精確比對；新版 Router 還接受更細的 `IsActiveMatchOptions`（可分別指定路徑、查詢參數、fragment——網址 `#` 後面那一段——的比對方式）。

> 📝 查證更正：原筆記寫 routerLinkActiveOptions="{exact: true}"（不加方括號），查證後更正：那樣傳進去的是字串不是物件，設定不會生效，必須用屬性綁定的方括號寫法

*【路由資料】*

## 路徑參數、查詢參數與巢狀路由

> 🏠 **生活比喻**
>
> - **路徑參數**＝**門牌號碼**：要去哪一間（`/users/42`）。
> - **查詢參數**＝到了之後的**要求**：「我要看歷史紀錄、價格由低到高」（`?tab=history`）。
> - `snapshot`＝**拍一張照片**，之後不會更新；訂閱 `paramMap`＝**監視器直播**。
>   同一家店換桌（元件被重用，從 42 號到 43 號），只看照片會一直停在舊桌號。
> - **巢狀路由**＝**百貨公司裡的店中店**：大店裡面再分小櫃位。

```
// /users/42?tab=history
this.router.navigate(['/users', userId], {
  queryParams: { tab: 'history' }
});

// 只讀一次
const id = this.route.snapshot.paramMap.get('id');

// 跟著變化
this.route.paramMap.subscribe(params => {
  const currentId = params.get('id');
});
```

路徑參數識別「哪一筆資源」（例如使用者 ID），查詢參數描述「怎麼看」（篩選、排序、分頁）。同一個元件會在參數改變時被重用（例如從 /users/42 切到 /users/43），這時訂閱 `paramMap` 才收得到新值，只讀一次 snapshot 會停在舊的。

巢狀路由讓子頁面顯示在父路由元件裡的另一個 `router-outlet`，適合「課程／章節」「設定／分頁」這種層級結構。

*【載入順序】*

## 從 index.html 到路由元件

> 🏠 **生活比喻**
>
> 像**走進餐廳**：大門（index.html）→ 店經理迎接（根元件）→ 用餐區格局（版面元件）→ 帶位員看你的訂位（Router 比對網址）→ 帶你入座（放進 router-outlet）。
> 現代 HTTP 的 keep-alive 像**電話不掛斷、連續點好幾道菜**，而不是每點一道就掛掉重撥。

> index.html → 啟動根元件 → 版面元件 → Router 比對網址 → 頁面元件放進 router-outlet

再往下一層，瀏覽器拿到網址後還要做 DNS 查詢、建立連線、送出 HTTP 請求、解析 HTML 與 JavaScript——完整流程見網頁與網路基礎模組的〈從輸入網址到看到網頁〉。「每次請求都做 TCP 三向交握、回應後四次揮手關閉」是早期教學的簡化：HTTP/1.1 起連線預設保持並重用（keep-alive），HTTP/2 在同一條連線上多工，HTTP/3 走 QUIC（建在 UDP 上、把建立連線與加密交握合併的傳輸協定），連線建立和加密合在同一套交握[出處](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Connection_management_in_HTTP_1.x)。

> 📝 查證更正：原筆記寫「2. 建立 TCP 連線(三次握手)…5. 關閉 TCP 連線(四次握手)」，查證後更正：HTTP/1.1 起連線預設保持重用，不會每次請求後都關閉；HTTP/3 甚至沒有獨立的 TCP 交握

### 🗺️ 比喻對照表

| 技術名詞 | 生活比喻 |
| --- | --- |
| Ajax | 手機點外送，只換桌上那盤菜 |
| SPA | 舞台劇換布景，不換劇場 |
| Router / router-outlet | 樓層導覽 / 電梯門口 |
| ** 萬用路由 | 「請洽服務台」，放最後 |
| routerLink / navigate() | 固定指示牌 / 計程車司機 |
| routerLinkActive | 到站亮燈 |
| 路徑參數 / 查詢參數 | 門牌號碼 / 到了之後的要求 |
| snapshot / paramMap | 拍照 / 監視器直播 |
| keep-alive | 電話不掛斷連續點菜 |

### 重點整理

*   Ajax＝非同步取資料＋局部更新畫面；SPA 靠它與路由維持單一應用程式外殼。
*   路由先到先得，萬用路由 `**` 放最後。
*   `routerLink` 去哪裡、`routerLinkActive` 到了套什麼、`routerLinkActiveOptions` 什麼算到了。
*   路徑參數識別資源、查詢參數描述檢視；元件被重用時要訂閱 `paramMap`。
*   現代 HTTP 連線會保持重用，不是一請求一連線。

## 隨堂測驗

**Q1. Ajax 的核心價值是什麼？**

- (A) 非同步取得資料並局部更新畫面，不必整頁重載
- (B) 保證每次請求的回應時間更短
- (C) 把資料格式統一成 XML
- (D) 讓瀏覽器不再需要發 HTTP 請求

<details><summary>看答案</summary>

**答案：(A)** Ajax 是一組非同步互動做法；它不加速單次回應，資料格式也早就以 JSON 為主。

</details>

**Q2. 「非同步請求」代表什麼？**

- (A) 送出請求後不必等待，期間可繼續處理其他事
- (B) 伺服器會用比較高的優先權處理
- (C) 請求失敗時會自動重試
- (D) 回應一定比同步請求快

<details><summary>看答案</summary>

**答案：(A)** 非同步解決的是「等待期間卡住」，不是速度，也不含自動重試。

</details>

**Q3. Angular SPA 中 router-outlet 的角色是什麼？**

- (A) 放置目前網址配對到的路由元件
- (B) 攔截 HTTP 請求並快取回應
- (C) 宣告全域樣式的作用範圍
- (D) 保存路由歷史供上一頁使用

<details><summary>看答案</summary>

**答案：(A)** Router 比對網址後，把對應元件渲染在 outlet 的位置。

</details>

**Q4. 為何 path: '\*\*' 要放在路由陣列最後？**

- (A) 路由先到先得，放前面會攔截所有網址、永遠顯示 404
- (B) 陣列最後一筆的優先權最高
- (C) Angular 規定萬用路由必須是預設路由
- (D) 放前面會讓延遲載入失效

<details><summary>看答案</summary>

**答案：(A)** 配對由上而下，萬用路由什麼都配得上，放前面就沒有別的路由出場機會。

</details>

**Q5. 網址 /users/42?tab=history 中，42 與 tab 各屬於哪類？**

- (A) 42 是路徑參數、tab 是查詢參數
- (B) 42 是查詢參數、tab 是路徑參數
- (C) 兩者都是路徑參數
- (D) 兩者都是 fragment

<details><summary>看答案</summary>

**答案：(A)** 路徑參數識別資源（哪個使用者），查詢參數描述檢視方式（看哪個頁籤）。

</details>

**Q6. 同一個元件會在路由參數改變時被重用，該怎麼拿到新參數？**

- (A) 訂閱 route.paramMap 這類 Observable
- (B) 只在建構時讀一次 snapshot 就夠
- (C) 改用 window.location 手動解析網址
- (D) 在 ngOnDestroy 裡讀取參數

<details><summary>看答案</summary>

**答案：(A)** 元件不重建時 snapshot 停在舊值；訂閱才收得到後續變化。

</details>

**Q7. routerLinkActive 的用途是什麼？**

- (A) 目前路由配對時，替連結加上指定的 CSS class
- (B) 點擊連結時觸發程式式導覽
- (C) 定義連結要前往的路徑
- (D) 控制路由的配對是精確還是部分

<details><summary>看答案</summary>

**答案：(A)** 去哪裡是 routerLink、什麼算到了是 routerLinkActiveOptions；routerLinkActive 管到了之後的樣式。

</details>

**Q8. 首頁連結 routerLink="/" 常設 { exact: true }，為什麼？**

- (A) 預設部分比對會讓 / 配到所有路徑，首頁永遠顯示為作用中
- (B) 不設 exact 首頁路由就無法載入
- (C) exact: true 會加快路由比對速度
- (D) 這是啟用巢狀路由的必要條件

<details><summary>看答案</summary>

**答案：(A)** 每個網址都以 / 開頭，部分比對下首頁連結永遠「到了」；exact 改成精確比對。

</details>

**Q9. 關於現代 HTTP 連線，哪個敘述正確？**

- (A) HTTP/1.1 起連線預設保持重用，不會每次請求後就關閉
- (B) 每個請求都必須經過獨立的 TCP 三向交握
- (C) HTTP/2 規定一個請求一條連線
- (D) HTTP/3 先做 TCP 交握再做 QUIC 交握

<details><summary>看答案</summary>

**答案：(A)** keep-alive 讓連線重用；HTTP/2 在一條連線上多工，HTTP/3 走 QUIC、沒有獨立的 TCP 交握。

</details>
