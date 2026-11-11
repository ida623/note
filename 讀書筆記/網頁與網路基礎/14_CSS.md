# 14. CSS

> 來源：[筆記平台 · 網頁與網路基礎](https://hhtim.github.io/notes-platform/web/#/lesson/css)　第 14 課 / 共 15 課 · 約 11 分鐘

**掌握選擇器、盒模型、版面配置與動態效果，讓 HTML 變成可讀又有彈性的介面。**

### 讀完這課你會

*   連結樣式表並讀懂 CSS 規則
*   判斷層疊、特定度與繼承的結果
*   用盒模型與 Flexbox 排版
*   建立轉場、動畫與字型設定

*【套用樣式】*

## 一條 CSS 規則包含選擇器與宣告

```
h1 {
  color: #b42318;
  line-height: 1.2;
}
```

`h1` 是選擇器；大括號內是屬性和值組成的宣告。正式專案通常以 `<link rel="stylesheet" href="styles.css">` 載入外部樣式表，便於快取與共同維護。行內樣式與文件內樣式適合有限情境，不宜散落各處。

顏色可用具名色、十六進位、`rgb()`、帶透明度的 `rgb()` 或 `hsl()` 表示。RGB 每個色彩通道常以 0 到 255 表達；透明度 0 代表透明，1 代表不透明。

*【找到元素】*

## 選擇器像寄件地址：越精確，命中範圍越小

| 選擇器 | 範例 | 命中對象 |
| --- | --- | --- |
| 元素 | `p` | 所有 p 元素 |
| 類別 | `.notice` | class 包含 notice 的元素 |
| ID | `#signup` | id 為 signup 的元素 |
| 後代 | `nav a` | nav 裡的所有 a |
| 屬性 | `input[type="email"]` | 電子郵件輸入框 |
| 偽類 | `button:hover` | 滑鼠指向的按鈕 |
| 偽元素 | `p::first-line` | 段落第一行 |

一個元素可以有多個 class；id 值在同一份文件中應保持唯一。`:focus` 表示取得焦點，鍵盤使用者也需要清楚可見的焦點樣式。

*【衝突裁判】*

## 層疊、特定度與繼承一起決定結果

當多條宣告競爭同一屬性時，瀏覽器會考量來源與重要性、層疊層（cascade layer，用 `@layer` 把樣式分組，先決定組與組之間誰優先）、特定度、作用範圍鄰近性（`@scope` 裡離目標元素比較近的規則優先）及出現順序。只有前面的判斷仍打平時，較後面的宣告才勝出。

> 一般選擇器權重概念：ID ＞ class／屬性／偽類 ＞ 元素／偽元素

```
.title { color: blue; }
h1.title { color: red; }
/* h1.title 的特定度較高，因此標題為紅色。 */
```

繼承則像家族特徵：沒有指定值時，「會繼承」的屬性（如 `color`、`font-family`）拿父元素的計算值；「不繼承」的屬性（如 `width`、`margin`、`border`）拿自己的初始值，不會去拿父元素的值[出處](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_cascade/Inheritance)。是否繼承是各屬性的定義，不是所有未指定的屬性都跟著父元素。

> 📝 查證更正：原筆記寫「如果自身沒有特定指定 CSS 屬性，則繼承父母的 CSS 屬性(non-inherited)」，查證後更正：只有會繼承的屬性（inherited）拿父元素的計算值；不繼承的屬性（non-inherited）拿的是自己的初始值

*【每個元素都是盒子】*

## 盒模型決定實際占用空間

盒模型由內容（content）、內距（padding）、邊框（border）與外距（margin）向外組成。預設 `box-sizing: content-box` 時，設定的寬高只計內容；常見的 `border-box` 則把 padding 與 border 算進指定寬高，比較直覺。

```
* {
  box-sizing: border-box;
}

.card {
  width: min(100%, 32rem);
  padding: 1rem 1.5rem;
  border: 1px solid #ccc;
  margin: 1rem auto;
}
```

`padding: 2px 10px 6px 3px` 依序是上、右、下、左；兩個值則是上下、左右。`rem` 相對於根元素字級，`%` 的基準依屬性而異。1vw 是視窗寬度的 1%，1vh 是視窗高度的 1%——視窗高度的 10% 要寫 `10vh`，不是 `10vw`[出處](https://developer.mozilla.org/en-US/docs/Web/CSS/length)。

> 📝 查證更正：原筆記在 viewport height 那行寫「10vw = 10%」，查證後更正：vw 是視窗寬度單位，視窗高度的 10% 要寫 10vh

*【正常排版流】*

## block、inline 與 inline-block

區塊盒（block box）通常在正常流中另起一行，行內盒（inline box）隨文字排列。正常流中的區塊盒預設（`width: auto`）會延伸填滿容器的行內方向空間，而不是等同宣告 `width: 100%`——後者在盒子另有 padding 或 margin 時會撐出容器[出處](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_display/Block_and_inline_layout_in_normal_flow)[CSS 2.2](https://www.w3.org/TR/CSS22/visudet.html#blockwidth)。

> 📝 查證更正：原筆記寫「Block Element：width = Device Width，頁面有多寬，該 block 就有多寬(width: 100%)」，查證後更正：正常流中 width: auto 的區塊盒是「延伸填滿容器的行內空間」，並不是被宣告成 width: 100%，兩者在有 padding 或 margin 時結果不同。CSS 2.2 §10.3.3 的等式：「margin-left + border-left-width + padding-left + width + padding-right + border-right-width + margin-right = width of containing block」「If width is set to auto, any other auto values become 0 and width follows from the resulting equality.」——width: auto 是用容器寬度扣掉 margin、border、padding 算出來的，所以剛好塞滿；width: 100% 則是內容寬就等於容器寬，再加上 padding、margin 就超出

一般非替換的 inline 元素不適合直接用 `width`、`height` 控制尺寸；`inline-block` 則能保持同行排列，同時接受盒子尺寸。`display: none` 會讓元素不產生盒子，也不占版面。`img`、`input` 等替換元素有自己的尺寸行為，不宜簡化成「固定五種 inline-block 元素」。

*【一維排版】*

## Flexbox 把容器剩餘空間分配給項目

在容器設 `display: flex` 後，它的直接子元素才會成為 flex items。主軸由 `flex-direction` 決定；`justify-content` 沿主軸排列，`align-items` 沿交叉軸對齊。

```
.cards {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.card {
  flex: 1 1 14rem;
}
```

`flex: 1 1 14rem` 依序是 `flex-grow`、`flex-shrink`、`flex-basis`。flex 項目設定的 `width` 是伸縮計算前的基準尺寸（`flex-basis` 為 auto 時：主軸水平沿用 width，`flex-direction: column` 時沿用 height），不是最大寬度；`flex-basis` 是初始主軸尺寸，也不是最小寬度——空間不足時項目會因預設的 `flex-shrink: 1` 被壓縮[出處](https://developer.mozilla.org/en-US/docs/Web/CSS/flex-basis)。

> 📝 查證更正：原筆記寫 flex 項目設定寬度「其實設定的是最大寬度 (max-width)」、flex-basis 是「該 box 最低寬度(類似 min-width 的概念?)」，查證後更正：width 是伸縮前的基準（flex-basis 非 auto 時 flex-basis 優先），flex-basis 是初始主軸尺寸，都不是 max-width 或 min-width

讓項目長大、分掉容器剩餘空間的是 `flex-grow`；`flex-shrink` 是空間不足時讓項目縮小的機制，兩者方向相反[出處](https://developer.mozilla.org/en-US/docs/Web/CSS/flex-grow)。

> 📝 查證更正：原筆記寫 box5「未設定 width，所以透過 flex-shrink 填滿整個 container」，查證後更正：分配剩餘空間讓項目長大的是 flex-grow；flex-shrink 只在空間不足時把項目縮小

*【精準定位】*

## position 決定元素以誰為座標基準

*   `static`：依正常流排列，`top`、`right`、`bottom`、`left` 與 `z-index` 都不起作用。
*   `relative`：保留原位置占位，再相對自己的正常位置偏移；也常用來建立 absolute 的包含區塊。
*   `absolute`：脫離正常流，通常相對最近的定位祖先排列。
*   `fixed`：脫離正常流，通常相對視窗固定。
*   `sticky`：先留在正常流，捲動到指定門檻後於所屬捲動區域內黏住。

`z-index` 比較的是堆疊脈絡（stacking context，瀏覽器分層比大小的範圍）中的層級，並非只要數字較大就能跨越所有祖先蓋住其他元素。relative 或 absolute 要搭配非 auto 的 `z-index` 才會建立堆疊脈絡；`fixed` 與 `sticky` 則一律建立[出處](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_positioned_layout/Stacking_context)。

> 📝 查證更正：原筆記寫 relative、absolute、fixed、sticky 都「Stacking context (可以設定 z-index)」，查證後更正：relative 與 absolute 要搭配非 auto 的 z-index 才建立堆疊脈絡；fixed 與 sticky 才是一律建立

*【文字與媒體】*

## 可讀性先於裝飾

常用文字屬性包含 `font-size`、`font-weight`、`line-height`、`letter-spacing`、`text-align` 與 `text-decoration`。字型可提供一串後備選項，避免第一套字型無法載入時失去可讀性。

```
@font-face {
  font-family: "Course Sans";
  src: url("/fonts/course-sans.woff2") format("woff2");
  font-display: swap;
}

body {
  font-family: "Course Sans", system-ui, sans-serif;
  line-height: 1.6;
}

.cover {
  width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
}
```

`object-fit: cover` 會維持媒體比例並填滿框，超出的部分可能被裁掉。背景圖的 `background-size: cover` 有類似視覺結果，但背景圖不應承擔必須被讀到的內容。

*【動態效果】*

## transition 是狀態間過場，animation 是時間腳本

```
.button {
  transition: transform 150ms ease, opacity 150ms ease;
}

.button:hover {
  transform: translateY(-2px) scale(1.02);
}

@keyframes pulse {
  from { opacity: .6; }
  to { opacity: 1; }
}

.status {
  animation: pulse 800ms ease-in-out infinite alternate;
}
```

`transform` 可平移、旋轉與縮放；`transition` 控制屬性從舊狀態變到新狀態的過程；`@keyframes` 則定義多階段動畫。應避免無止境或大幅移動造成不適，並尊重使用者的減少動態效果偏好。

*【進階維護】*

## SCSS 是產生 CSS 的工具，不是瀏覽器直接理解的新語法

SCSS 提供巢狀規則、變數、模組與 mixin，可減少重複，但必須先編譯成 CSS。巢狀不要太深，否則會產生難覆寫、特定度偏高的選擇器。Sass 的 `@import` 已被官方標記棄用（Dart Sass 1.80.0 起，預計 3.0.0 移除），新專案應改用 `@use` 與 `@forward` 模組系統[出處](https://sass-lang.com/documentation/at-rules/import/)。

> 📝 查證更正：原筆記把 import 列為 SCSS 的主要作法之一，查證後補充：Sass 官方文件自 Dart Sass 1.80.0 起把 @import 標記為棄用，將在 3.0.0 移除

HTML 錨點可配合 `scroll-behavior: smooth` 產生平滑捲動，但仍要考量減少動態效果設定。圖片與圖示也要確認授權，重要圖像需提供合適替代文字。

### 重點整理

*   層疊不只是「後蓋前」；特定度與來源等條件先決定勝負。
*   盒模型與 box-sizing 會直接影響元素實際尺寸。
*   Flexbox 處理一維空間分配；position 處理脫離或相對正常流的位置。
*   動態效果應服務狀態回饋，並兼顧效能與可及性。

## 隨堂測驗

**Q1. 兩條 CSS 規則特定度相同且其他層疊條件相同時，通常由哪一條勝出？**

- (A) 樣式表中較後出現的規則
- (B) 選擇器字串較短的規則
- (C) 屬性值字數較多的規則
- (D) 最接近頁面頂端的元素

<details><summary>看答案</summary>

**答案：(A)** 只有前面的層疊條件打平時，來源順序才由後者勝出。

</details>

**Q2. 在預設 content-box 下，width: 200px 代表哪一部分寬度？**

- (A) 內容區寬度
- (B) 內容加 padding 的寬度
- (C) 內容加 border 的寬度
- (D) 包含 margin 的總占用寬度

<details><summary>看答案</summary>

**答案：(A)** content-box 的 width 只指定內容區；padding 與 border 會另外加上。

</details>

**Q3. 哪一種 display 同時保留同行排列特性，又能設定寬高？**

- (A) inline-block
- (B) inline
- (C) none
- (D) contents

<details><summary>看答案</summary>

**答案：(A)** inline-block 對外像行內盒排列，盒本身則能接受寬高。

</details>

**Q4. flex-direction: row 時，justify-content 主要控制哪個方向？**

- (A) 水平方向的主軸
- (B) 垂直方向的交叉軸
- (C) 頁面的 z 軸
- (D) 文字基線以外的所有方向

<details><summary>看答案</summary>

**答案：(A)** row 讓主軸成為水平方向，justify-content 沿主軸分配空間。

</details>

**Q5. flex: 1 1 14rem 中的 14rem 是什麼？**

- (A) 伸縮計算前的主軸基準尺寸
- (B) 不可縮小的最小寬度
- (C) 永遠不會超過的最大寬度
- (D) 容器的固定高度

<details><summary>看答案</summary>

**答案：(A)** 第三值是 flex-basis，不等於 min-width 或 max-width。

</details>

**Q6. absolute 定位元素通常以誰作為定位基準？**

- (A) 最近的定位祖先
- (B) 前一個兄弟元素
- (C) 永遠以 body
- (D) 滑鼠游標

<details><summary>看答案</summary>

**答案：(A)** absolute 通常參考最近建立相應包含區塊的祖先；若沒有，才回到初始包含區塊。

</details>

**Q7. transition 與 animation 的差異何者正確？**

- (A) transition 適合狀態間過場；animation 可依 keyframes 自行播放多階段變化
- (B) transition 一定會無限循環
- (C) animation 不能改變 opacity
- (D) 兩者只能套用在圖片

<details><summary>看答案</summary>

**答案：(A)** transition 需要屬性狀態發生變化，animation 則可由關鍵影格描述時間序列。

</details>

**Q8. 關於 CSS 繼承，哪項正確？**

- (A) 是否預設繼承由個別屬性定義
- (B) 所有屬性都會繼承
- (C) 所有排版屬性都會繼承
- (D) 只有 ID 選擇器設定的值能繼承

<details><summary>看答案</summary>

**答案：(A)** color 等屬性通常會繼承，margin、border 等通常不會；應查個別屬性的定義。

</details>

**Q9. position: sticky 的元素會怎麼表現？**

- (A) 先照正常流排列，捲動超過門檻後在所屬捲動範圍內固定
- (B) 從一開始就完全脫離正常流
- (C) 永遠固定在視窗左上角
- (D) 等同於 display: none

<details><summary>看答案</summary>

**答案：(A)** sticky 先占正常流位置，捲動到 top 等門檻值後才在捲動祖先範圍內黏住。

</details>

**Q10. 為什麼 font-family 建議寫一串後備字型（font stack）？**

- (A) 第一套字型載入失敗或系統沒有時，還有後備字型維持可讀性
- (B) 可以讓字型檔案變小
- (C) 瀏覽器會同時顯示所有字型
- (D) 這樣才能使用 rem 單位

<details><summary>看答案</summary>

**答案：(A)** 字型可能載入失敗或平台未安裝，後備清單確保文字仍以合理字型顯示。

</details>
