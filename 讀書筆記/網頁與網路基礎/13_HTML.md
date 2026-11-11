# 13. HTML

> 來源：[筆記平台 · 網頁與網路基礎](https://hhtim.github.io/notes-platform/web/#/lesson/html)　第 13 課 / 共 15 課 · 約 12 分鐘

**用語義化標籤建立結構清楚、可操作且能提交資料的網頁。**

### 讀完這課你會

*   理解 HTML 在網頁傳輸與呈現流程中的角色
*   用常見標籤組織文字、連結、清單與表格
*   用語義元素表達內容結構
*   建立標示完整、可提交資料的表單

*【先懂角色】*

## HTML 是網頁的骨架

瀏覽器向伺服器發出 HTTP 請求後，可能取得 HTML 文件，再由上到下解析成文件物件模型（DOM）。CSS 負責外觀，JavaScript 負責互動；HTML 的首要任務則是描述「這段內容是什麼」。

標籤通常由開始標籤、內容與結束標籤組成。元素還能帶有屬性（attribute），補充瀏覽器需要的資訊。

```
<h1>課程公告</h1>
<p>本週開始學習 HTML。</p>
<a href="/courses/html">進入課程</a>
```

常見入口檔名是 `index.html`，但這是伺服器與工具常用的慣例，不是 HTML 語法的硬性規定。

*【起手式】*

## HTML 文件骨架

每份 HTML 文件都從同一套骨架開始：宣告、根元素、放設定的 `<head>` 與放內容的 `<body>`。

```
<!DOCTYPE html>
<html lang="zh-Hant">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>頁面標題</title>
  </head>
  <body>
    <!-- 網頁呈現的內容 -->
  </body>
</html>
```

*   **`<!DOCTYPE html>`**：HTML5 的文件類型宣告，告訴瀏覽器用標準模式解析。
*   **`<html lang>`**：標註網頁語系，幫助搜尋引擎與螢幕報讀器。
*   **`<meta charset="UTF-8">`**：宣告字元編碼（character set，字的集合），瀏覽器才能正確解讀文字、不出亂碼。
*   **viewport meta：**`width=device-width` 讓版面寬度等於裝置寬度，`initial-scale=1.0` 表示初始不縮放——行動裝置排版的起點。

`<head>` 內還常見 `<meta name="description">`（網站簡介，常出現在搜尋結果摘要）、`<meta name="robots">`（給搜尋引擎的收錄指示）與 `<meta name="author">`。

骨架常被記成「頭 head、身體 body、腳 footer」，這是錯的：footer 是放在 body 裡的語義元素（見下文），不是文件骨架的一層。

*【文字與導覽】*

## 標題、段落、連結與清單

`<h1>` 到 `<h6>` 表示不同層級的標題，`<p>` 表示段落。標題層級應反映文章結構，不要只因為字體大小而跳級。

`<a>` 是錨點元素（anchor），`href` 指定目的地。連到同頁某元素時，可把該元素的唯一 `id` 寫成片段網址。

```
<nav>
  <a href="#signup">前往報名</a>
</nav>

<section id="signup">
  <h2>報名方式</h2>
</section>
```

`target="_self"` 會在目前瀏覽情境開啟；`target="_blank"` 通常開啟新分頁。新分頁連結若前往不受信任的網站，可搭配適當的 `rel` 值降低安全風險。

`<base target="_blank">` 會讓連結開新分頁，但作用範圍是整份文件：所有沒有自己寫 `target` 的連結與表單（`<a>`、`<area>`、`<form>`）都會照它開；`<base href>` 則一次決定文件內所有相對網址的基準 URL。只想讓某一個連結開新分頁，在那個 `<a>` 上寫 `target` 就好[出處](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/base)。

無順序清單使用 `<ul>`，有先後順序的步驟使用 `<ol>`，每一項都用 `<li>`。

*【內容結構】*

## 語義標籤比萬用容器更會「自我介紹」

`<div>` 像沒有標籤的收納箱，只負責分組；語義元素則像箱外的分類貼紙，能向瀏覽器、搜尋引擎與輔助科技說明內容用途。

*   **header**：頁面或區段的前導內容，例如標題與工具列。
*   **nav**：主要導覽連結。
*   **main**：頁面的主要內容；通常應聚焦於一份文件的核心內容。
*   **article**：可獨立理解或散布的內容，例如文章、貼文。
*   **section**：有共同主題的內容區段，通常帶有標題。
*   **aside**：與主要內容間接相關的補充資訊。
*   **footer**：頁面或區段的頁尾資訊。

`<figure>` 可包住圖片、圖表或程式碼範例，並以 `<figcaption>` 提供說明；`<details>` 與 `<summary>` 可建立可展開內容；`<time>` 可用 `datetime` 提供機器可讀時間。

這些語義元素仍有瀏覽器給的預設樣式——使用者代理樣式表（user agent stylesheet，瀏覽器內建的那份 CSS）會給它們 `display: block`，`figure` 還有預設外距[出處](https://html.spec.whatwg.org/multipage/rendering.html)。

> 📝 查證更正：原筆記寫「以上的標籤都沒有 css 的 default styling!」，查證後更正：HTML 標準的 rendering 章節明列這些元素的預設樣式，例如 article、aside、nav、section 都是 display: block，figure 還有預設外距

*【二維資料】*

## 表格用來呈現資料關係，不拿來硬排版

`<table>` 包住表格，`<tr>` 是列，`<th>` 是標題儲存格，`<td>` 是資料儲存格。`colspan` 與 `rowspan` 分別讓儲存格跨欄與跨列。

| 標籤 | 用途 |
| --- | --- |
| `thead` | 表頭列群組 |
| `tbody` | 主要資料列群組 |
| `caption` | 描述整張表格的標題 |

```
<table>
  <caption>課程時數</caption>
  <thead>
    <tr><th scope="col">課程</th><th scope="col">分鐘</th></tr>
  </thead>
  <tbody>
    <tr><td>HTML</td><td>45</td></tr>
  </tbody>
</table>
```

*【蒐集資料】*

## 表單是有欄位名稱的寄件單

`action` 是 `<form>` 的屬性（不是一個標籤），指定表單提交到哪個網址；`method` 指定 HTTP 方法[出處](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/form)。GET 通常把成功控制項（會被提交的欄位：有 `name` 且未被停用）組成查詢字串，適合查詢與可分享網址；POST 通常把資料放在請求本文，適合造成變更或資料較多的操作，但 POST 本身不等於加密，仍需 HTTPS。

> 📝 查證更正：原筆記把它寫成標籤「<action>：資料要傳去的目的地」，查證後更正：action 是 form 元素的屬性；GET 與 POST 的差異也不只「內容是否顯示在 URL 上」，語意、快取與副作用都不同

```
<form action="/signup" method="post">
  <label for="email">電子郵件</label>
  <input id="email" name="email" type="email" required>

  <label for="area">地區</label>
  <select id="area" name="area">
    <option value="north">北部</option>
    <option value="south">南部</option>
  </select>

  <button type="submit">送出</button>
</form>
```

`label` 的 `for` 應對上欄位的 `id`；點標籤便能聚焦或切換控制項。要提交的控制項通常需要 `name`，因為送出的資料以名稱和值配對。

常見 `input` 類型包括 `email`、`password`、`number`、`range`、`radio`、`checkbox` 與 `file`。`required`、`min`、`max`、`minlength` 與 `maxlength` 可提供瀏覽器端限制，但伺服器仍須重新驗證。

radio 與 checkbox 語法上可以省略 `value`，省略時勾選送出的預設值是 `on`；實務上建議明確設定，送到後端的資料才有意義[checkbox](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input/checkbox)[radio](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input/radio)。

> 📝 查證更正：原筆記先寫 radio、checkbox 的 value「一定要設定」，後文又寫「未必需填寫」，前後矛盾；查證後更正：語法上可省略，勾選送出的預設值是 on。MDN radio 頁：「If you omit the value attribute in the HTML, the submitted form data assigns the value on to the group.」

*【更多控制項】*

## 選項、建議清單與多行文字

`<select>` 限定使用者從選項中選擇；`<datalist>` 則為輸入框提供建議，使用者通常仍可輸入清單外的值。兩者用途不同。

```
<label for="city">城市</label>
<input id="city" name="city" list="city-list">
<datalist id="city-list">
  <option value="臺北">
  <option value="臺中">
  <option value="高雄">
</datalist>

<label for="message">留言</label>
<textarea id="message" name="message" rows="5"></textarea>
```

`rows` 與 `cols` 是文字區域的初始顯示尺寸提示；實際版面通常再交給 CSS 控制。`placeholder` 只是提示，不應取代可持續看見的標籤。

### 重點整理

*   HTML 描述內容與結構，CSS 處理外觀，JavaScript 增加行為。
*   能用語義元素時，優先表達內容用途，而不是全部塞進 div。
*   表格呈現二維資料；表單用 name-value 配對提交資料。
*   正確標籤、標題階層與 label 關聯，同時幫助維護與無障礙使用。

## 隨堂測驗

**Q1. HTML 在網頁中的主要責任是什麼？**

- (A) 描述內容的結構與語意
- (B) 決定字體、顏色與版面怎麼呈現
- (C) 在瀏覽器裡執行運算與互動邏輯
- (D) 規定瀏覽器與伺服器之間怎麼傳資料

<details><summary>看答案</summary>

**答案：(A)** HTML 是內容骨架；外觀通常由 CSS 負責，互動通常由 JavaScript 負責。

</details>

**Q2. 要連到同一頁 id="signup" 的區段，href 應寫成什麼？**

- (A) #signup
- (B) signup#
- (C) /signup.html#
- (D) id:signup

<details><summary>看答案</summary>

**答案：(A)** 片段網址以 # 加上目標元素的 id。

</details>

**Q3. &lt;meta charset="UTF-8"> 的作用是什麼？**

- (A) 宣告文件的字元編碼，讓瀏覽器正確解讀文字
- (B) 指定文件的語言，等同 html 的 lang 屬性
- (C) 設定整頁文字使用的字型
- (D) 讓版面寬度等於行動裝置的寬度

<details><summary>看答案</summary>

**答案：(A)** 字元編碼決定位元組如何還原成文字；語系是 lang 屬性，行動版寬度是 viewport meta 的事。

</details>

**Q4. 哪個元素最適合包住網站的主要導覽連結？**

- (A) nav
- (B) div
- (C) mark
- (D) time

<details><summary>看答案</summary>

**答案：(A)** nav 直接表達主要導覽區域的語意。

</details>

**Q5. 表格中的 th 最適合表示什麼？**

- (A) 列或欄的標題儲存格
- (B) 任意排版容器
- (C) 表單文字欄位
- (D) 整張表格的外框

<details><summary>看答案</summary>

**答案：(A)** th 是表頭儲存格，可再以 scope 說明它對應列或欄。

</details>

**Q6. 表單控制項若要以指定欄位名稱提交，最關鍵的屬性是哪個？**

- (A) name
- (B) class
- (C) placeholder
- (D) title

<details><summary>看答案</summary>

**答案：(A)** 成功提交的控制項會以 name 與目前值組成資料。

</details>

**Q7. 關於 GET 與 POST，哪項說法正確？**

- (A) GET 常用於查詢；POST 常用於提交可能造成變更的資料
- (B) 只要使用 POST，內容就自動加密
- (C) GET 完全不能帶參數
- (D) POST 資料必定不會被記錄

<details><summary>看答案</summary>

**答案：(A)** 方法應依請求語意選擇；傳輸機密性要靠 HTTPS，而不是只靠 POST。

</details>

**Q8. datalist 與 select 的主要差異是什麼？**

- (A) datalist 提供輸入建議；select 通常限制於既有選項
- (B) datalist 只能輸入數字
- (C) select 可自由輸入任何文字
- (D) 兩者沒有差異

<details><summary>看答案</summary>

**答案：(A)** datalist 搭配 input 提供候選值，select 則讓使用者從選項中選擇。

</details>

**Q9. 為什麼 placeholder 不應取代 label？**

- (A) 使用者輸入後提示會消失，且標籤能提供較穩定的欄位名稱
- (B) placeholder 不能顯示文字
- (C) label 會自動提交資料
- (D) placeholder 只能用在按鈕

<details><summary>看答案</summary>

**答案：(A)** 持續可見且正確關聯的 label 對理解欄位與無障礙操作更可靠。

</details>
