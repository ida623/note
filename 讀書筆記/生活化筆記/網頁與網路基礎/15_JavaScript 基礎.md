# 15. JavaScript 基礎

> 🏠 **生活化版本**：每個段落開頭的「生活比喻」先用日常情境帶你抓到感覺，接著再看原本的技術說明與程式碼；篇末有「比喻對照表」可以快速複習。

> 來源：[筆記平台 · 網頁與網路基礎](https://hhtim.github.io/notes-platform/web/#/lesson/javascript)　第 15 課 / 共 15 課 · 約 11 分鐘

**從資料、流程與物件開始，學會用 JavaScript 執行邏輯並操作網頁內容。**

### 讀完這課你會

*   說出 JavaScript 引擎、瀏覽器與 Node.js 的關係
*   宣告變數並辨認常見資料型別
*   用條件、迴圈與函式組合程式邏輯
*   操作陣列、物件與基本 DOM

*【執行程式】*

## JavaScript 需要執行環境提供舞台

> 🏠 **生活比喻**
>
> JavaScript 像**演員**，需要**舞台**才能演：在瀏覽器舞台可以操作網頁，在 Node.js 舞台可以讀檔、開伺服器；演員一樣，舞台給的道具不同。

JavaScript 引擎負責解析與執行語言；Chrome 與 Node.js 都使用 V8。瀏覽器另外提供 DOM、事件與網路等 Web API，Node.js 則提供檔案、程序與伺服器相關 API。同一套 JavaScript 語法可以在不同環境執行，但可使用的全域 API 不完全相同。

Node.js 是「其中一種」JavaScript 執行環境，它把 Chrome 的核心 V8 引擎搬到瀏覽器外執行；瀏覽器本身也是執行環境，只是提供的 API 不同[出處](https://nodejs.org/en/learn/getting-started/introduction-to-nodejs)。

REPL 是「讀取、求值、輸出、循環」（Read-Eval-Print Loop），適合快速測試運算式：

```
> 2 + 3
5
> "Hi".toUpperCase()
'HI'
```

*【名字與資料】*

## 變數像有名稱的置物盒

> 🏠 **生活比喻**
>
> - `const`＝**貼了封條的盒子**，不能換掉裡面的東西（但盒子裡的物件內容還能改）
> - `let`＝**可以換內容的盒子**
> - `var`＝**舊式盒子**，範圍規則容易出錯，盡量不用

`=` 是賦值，不是數學等號。現代 JavaScript 通常先選 `const`；只有需要把變數重新指向另一個值時才用 `let`。`var` 具有函式作用域，而且有提升（hoisting，宣告會被當成寫在作用域最前面，所以宣告之前就能讀到 `undefined`）這種容易混淆的行為，新程式通常不需要優先使用。

```
const course = "JavaScript";
let progress = 0;
progress = progress + 1;
```

`let` 與 `const` 是區塊作用域（block scope），有效範圍受大括號限制。`const` 禁止重新賦值，但若值是物件，物件內容仍可能被修改。

```
const learner = { name: "小安" };
learner.name = "小華"; // 可以：修改物件內容
// learner = {};       // 不可以：重新指派變數
```

var 與 let 還有兩個常見差異。第一是迴圈綁定：`for (var i …)` 整個迴圈共用同一個 i，迴圈結束後 i 仍讀得到（外洩到函式作用域）；`for (let i …)` 每輪迭代各有一份 i，迴圈外不存在。第二是重複宣告：var 允許同一作用域重複宣告同名變數，容易互相覆蓋而不自知；let 與 const 重複宣告會直接拋出語法錯誤。

*【資料型別】*

## 先分清值的種類，才知道能做什麼

> 🏠 **生活比喻**
>
> - 基本型別＝**寫在紙上的數字或文字**，複製就是另一張紙
> - 物件＝**倉庫的地址**，複製的是地址，兩人去的是同一個倉庫

基本型別（primitive）包含字串、數字、布林值、`undefined`、`null`、`bigint` 與 `symbol`。物件型別則包含一般物件、陣列與函式等。

*   **undefined**：變數已存在，但目前沒有指定值；也可能是缺少屬性的結果。
*   **未宣告識別字**：名稱根本不在可見作用域內，直接讀取通常產生 ReferenceError。
*   **null**：由程式主動表達「目前沒有值」。
*   **NaN**：表示某次數值運算得不到有效數字；它的型別仍是 number。

基本型別通常按值複製；物件變數保存的是對物件的參照。兩個變數指向同一物件時，從其中一個變數修改內容，另一個也會看到變化。

*【流程控制】*

## 條件做選擇，迴圈處理重複工作

> 🏠 **生活比喻**
>
> - `if`＝**岔路口的路標**
> - 迴圈＝**洗碗機重複洗每一個碗**
> - `===`＝**連型別都要一樣才算相等**；`==` 會偷偷幫你轉換，像把「1」和 1 當成一樣，容易出包

```
const score = 82;

if (score >= 60) {
  console.log("通過");
} else {
  console.log("再試一次");
}

for (let i = 0; i < 3; i += 1) {
  console.log(`第 ${i + 1} 次`);
}
```

條件判斷通常優先使用嚴格相等 `===` 與嚴格不相等 `!==`，避免自動型別轉換帶來意外。設計迴圈時要確認初始值、繼續條件與每輪更新，否則可能形成無限迴圈。

*【封裝步驟】*

## 函式把輸入轉成可重複使用的結果

> 🏠 **生活比喻**
>
> 函式像**果汁機**：放進水果（參數），按下開關（呼叫），倒出果汁（回傳值），可以一直重複使用。

```
function calculateTotal(price, quantity) {
  return price * quantity;
}

const total = calculateTotal(120, 3);
console.log(total); // 360
```

`price` 與 `quantity` 是參數，呼叫時傳入的是引數；`return` 把結果交回呼叫端。函式若沒有明確回傳值，呼叫結果是 `undefined`。

*【集合資料】*

## 陣列按順序收納，物件以 key 描述資料

> 🏠 **生活比喻**
>
> - 陣列＝**編號的置物櫃**，從 0 號開始
> - 物件＝**一張個人資料卡**，用「姓名」「年齡」這種欄位名稱找資料

```
const lessons = ["HTML", "CSS", "JavaScript"];
console.log(lessons[0]); // HTML

const player = {
  firstName: "Tim",
  lastName: "Huang",
  fullName() {
    return `${this.firstName} ${this.lastName}`;
  }
};

console.log(player.fullName());
```

陣列索引從 0 開始。物件屬性可用 `object.key` 或 `object["key"]` 取得；當 key 存在變數中或不是合法識別字時，方括號寫法特別有用。物件中的函式常稱為方法，呼叫方法要加括號。

`slice(begin, end)` 回傳從 begin 到 end 之前的淺拷貝，不修改原陣列；`splice(start, deleteCount, ...items)` 則會直接修改原陣列，可刪除或插入項目。

```
const names = ["安", "柏", "晴", "德"];
const copy = names.slice(1, 3); // ["柏", "晴"]
// names 仍維持原樣

names.splice(1, 1, "文");
// names 變成 ["安", "文", "晴", "德"]
```

*【隨機整數】*

## 先縮放區間，再無條件捨去

> 🏠 **生活比喻**
>
> `Math.random()` 像**轉一個 0 到 1 的輪盤**；要 1~6 的骰子，就**把輪盤放大 6 倍、去掉小數、再加 1**。

`Math.random()` 會產生大於等於 0、且小於 1 的偽隨機數——最小值可能就是 0，最大不會到 1[出處](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Math/random)。乘上區間長度、用 `Math.floor()` 捨去小數，再加回最小值，即可得到指定範圍的整數。

> 📝 查證更正：原筆記寫「最小的數不會等於 0，也就是0.0000…01」，查證後更正：Math.random() 的範圍是大於等於 0、小於 1，最小值可能就是 0

> min 到 max（不含 max）：Math.floor(Math.random() \* (max - min)) + min

> min 到 max（包含 max）：Math.floor(Math.random() \* (max - min + 1)) + min

```
function rollDice() {
  return Math.floor(Math.random() * 6) + 1;
}
```

這類亂數適合遊戲與介面效果；密碼、權杖或抽獎安全需求應使用密碼學安全的亂數來源。

*【日期】*

## Date 表示時間點，但解析字串要小心

> 🏠 **生活比喻**
>
> `Date` 內部是**從 1970 年起算的毫秒數**，像一個絕對的時間戳；顯示時會**換成你所在的時區**，跨時區交換資料要用標準格式（ISO 8601）。

```
const now = new Date();
console.log(now.getFullYear());

const launch = new Date("2026-09-21T09:00:00+08:00");
console.log(launch.toISOString());
```

`Date` 內部以時間戳記表示時間點，顯示時會受到時區影響。交換資料時宜使用明確、標準化且帶有時區資訊的日期時間字串，避免依賴含糊的地區格式。

*【操作網頁】*

## DOM 把 HTML 變成 JavaScript 可操作的物件

> 🏠 **生活比喻**
>
> DOM 像**把網頁變成一棵家族樹**，JavaScript 可以找到某個家族成員（`querySelector`），幫他換衣服、改名字或加新成員。

```
<h1 id="title">尚未開始</h1>
<script>
  const title = document.querySelector("#title");
  title.textContent = "開始學 JavaScript";
</script>
```

`document.querySelector()` 會回傳第一個符合 CSS 選擇器的元素；`textContent` 用來讀寫純文字。若元素不存在，結果會是 `null`，操作前要確認。

傳統做法把 script 放在 body 結尾，讓前面的元素先被解析。另一種常見作法是在外部腳本使用 `defer`，下載時不阻塞 HTML 解析，並在文件解析完成後按順序執行。

```
<script src="/app.js" defer></script>
```

*【理解執行環境】*

## Node.js 與 Java 不宜硬做一對一類比

> 🏠 **生活比喻**
>
> Node.js 和 Java 像**兩種不同的餐廳經營方式**：Node.js 是**一位超級服務生用號碼牌輪流處理**（單執行緒事件迴圈），Java 傳統上是**多位服務生各自服務一桌**（多執行緒）。

V8 是用 C++ 寫成、在 Chrome 與 Node.js 使用的 JavaScript 引擎，在各平台上直接把 JavaScript 原始碼編譯並執行，不會先產出一份通用的中間產物；「一次編譯、到處執行」是 Java 位元碼的模式，不是 V8 的[出處](https://v8.dev/docs)。

> 📝 查證更正：原筆記寫「與 Java 中的 JVM 有類似特性，V8 編譯後可在不同平台執行」。照字面讀（V8 這個引擎本身有各平台的版本）是對的，v8.dev 自己也寫「runs on Windows, macOS, and Linux systems」；但同一篇下文把 JVM 寫成「Java 的編譯器，讓 Java 能夠實現一次編譯後，在不同的平台執行」，拿來類比 V8，所以這句實際上是在說「JavaScript 經 V8 編譯後的產物可跨平台執行」——這點不對：V8 在每個平台上直接編譯並執行 JavaScript 原始碼（v8.dev/docs：「V8 compiles and executes JavaScript source code」），不會先產生一份通用的中間產物；「一次編譯、到處執行」是 Java 位元碼的模式

JVM 是執行 Java 位元碼的虛擬機；把 `.java` 原始碼編譯成 `.class` 位元碼的是 `javac` 編譯器[出處](https://docs.oracle.com/javase/tutorial/getStarted/intro/definition.html)。JRE 提供執行 Java 程式所需的 JVM 與函式庫，JDK 則再包含編譯器等開發工具。

> 📝 查證更正：原筆記寫「JVM 是 Java 的編譯器」，查證後更正：JVM 是執行 .class 位元碼的虛擬機，把 .java 編譯成位元碼的是 javac

流傳很廣的對照「Node ≒ JDK、V8 ≒ JVM、Node.js ≒ JRE」也要小心：這些元件的邊界與責任不同，只能當非常粗略的輔助類比，不能視為等價。

| 面向 | JavaScript／Node.js | Java |
| --- | --- | --- |
| 語言執行核心 | V8 等 JavaScript 引擎 | JVM 執行位元碼 |
| 常見執行套件 | Node.js runtime 與其 API | Java runtime 與標準函式庫 |
| 開發工具 | 另搭配套件管理器、編輯器與建置工具 | JDK 包含 javac 等工具 |

### 🗺️ 比喻對照表

| 技術名詞 | 生活比喻 |
| --- | --- |
| 執行環境 | 演員的舞台 |
| const / let | 貼封條的盒子 / 可換內容的盒子 |
| 基本型別 / 物件 | 紙上的字 / 倉庫地址 |
| === | 連型別都要一樣 |
| 函式 | 果汁機 |
| DOM | 網頁的家族樹 |
| Node.js 事件迴圈 | 一位服務生用號碼牌輪流 |

### 重點整理

*   JavaScript 引擎執行語言，執行環境決定還能使用哪些 API。
*   預設使用 const，需要重新賦值時用 let，並留意區塊作用域。
*   陣列適合有順序的集合，物件適合以 key-value 描述實體。
*   slice 不改原陣列，splice 會修改原陣列。
*   DOM 是 JavaScript 與 HTML 內容互動的橋梁。

## 隨堂測驗

**Q1. 瀏覽器中的 JavaScript 引擎與 Web API 是什麼關係？**

- (A) 引擎執行語言，瀏覽器再提供 DOM 等環境 API
- (B) 引擎提供 DOM，瀏覽器只負責執行語法
- (C) Web API 是 ECMAScript 規格的一部分
- (D) Node.js 也提供同一套 DOM API

<details><summary>看答案</summary>

**答案：(A)** 語言引擎與宿主提供的 API 是不同層次；DOM 是瀏覽器環境能力。

</details>

**Q2. for (var i …) 與 for (let i …) 的差異，哪項正確？**

- (A) let 的 i 每輪迭代各有一份，且迴圈外讀不到；var 的 i 整個迴圈共用並外洩到函式作用域
- (B) var 的 i 每輪迭代都是新變數
- (C) let 的 i 在迴圈結束後仍可讀取
- (D) 兩者在迴圈裡的行為完全相同

<details><summary>看答案</summary>

**答案：(A)** var 是函式作用域、迴圈變數會外洩；let 是區塊作用域且每輪一個綁定。

</details>

**Q3. 哪項最能說明 undefined 與未宣告識別字的差別？**

- (A) undefined 可是既有變數的值；直接讀取未宣告名稱通常拋出 ReferenceError
- (B) 兩者永遠完全相同
- (C) undefined 只能出現在陣列
- (D) 未宣告名稱的值固定是 null

<details><summary>看答案</summary>

**答案：(A)** 變數存在但沒有值與名稱根本不存在，是不同情況。

</details>

**Q4. const 保存一個物件時，哪項操作通常允許？**

- (A) 修改該物件的既有屬性
- (B) 把變數重新指派成另一個物件
- (C) 再次以 const 宣告同名變數
- (D) 刪除目前區塊作用域

<details><summary>看答案</summary>

**答案：(A)** const 限制的是變數綁定重新賦值，不會自動凍結物件內容。

</details>

**Q5. slice(1, 3) 會選取哪些索引？**

- (A) 索引 1 與 2
- (B) 索引 1、2、3
- (C) 只有索引 3
- (D) 索引 0 到 3

<details><summary>看答案</summary>

**答案：(A)** slice 的結束索引不包含在結果中。

</details>

**Q6. 哪個方法會直接修改原陣列？**

- (A) splice
- (B) slice
- (C) map
- (D) concat

<details><summary>看答案</summary>

**答案：(A)** splice 會在原陣列刪除或插入項目；slice 則回傳淺拷貝。

</details>

**Q7. 要產生 1 到 6 且包含兩端的隨機整數，應使用哪個算式？**

- (A) Math.floor(Math.random() \* 6) + 1
- (B) Math.floor(Math.random()) \* 6
- (C) Math.random() + 6
- (D) Math.floor(Math.random() \* 5)

<details><summary>看答案</summary>

**答案：(A)** Math.random()\*6 的範圍是 0 到小於 6，floor 後為 0 到 5，再加 1 得到 1 到 6。

</details>

**Q8. 為什麼外部 script 常加上 defer？**

- (A) 下載時可繼續解析 HTML，並在文件解析完成後執行
- (B) 下載時就先暫停解析 HTML，下載完立刻執行
- (C) 下載完成後立刻執行，不等 HTML 解析完
- (D) 把腳本的執行延到使用者第一次捲動之後

<details><summary>看答案</summary>

**答案：(A)** defer 可避免傳統腳本阻塞 HTML 解析，也讓程式在 DOM 建立後執行。

</details>

**Q9. 兩個變數指向同一個物件時，透過其中一個修改屬性會發生什麼？**

- (A) 另一個變數也看得到變化，因為兩者保存同一個參照
- (B) 會自動複製出第二份物件
- (C) JavaScript 會拋出型別錯誤
- (D) 另一個變數會變成 undefined

<details><summary>看答案</summary>

**答案：(A)** 物件變數保存的是參照，不是各自獨立的複本。

</details>

**Q10. typeof NaN 的結果是什麼？**

- (A) number
- (B) nan
- (C) undefined
- (D) object

<details><summary>看答案</summary>

**答案：(A)** NaN 表示無效的數值運算結果，但它本身仍屬於 number 型別。

</details>
