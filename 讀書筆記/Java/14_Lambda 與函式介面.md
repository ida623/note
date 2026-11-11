# 14. Lambda 與函式介面

> 來源：[筆記平台 · Java](https://hhtim.github.io/notes-platform/java/#/lesson/java-lambda-functional)　第 14 課 / 共 18 課 · 約 55 分鐘

**用 lambda 把一段行為當參數傳，挑對 java.util.function 的介面，看懂方法參考、變數捕獲、Comparator 組合與 Optional。**

### 讀完這課你會

- 把匿名類別改寫成 lambda
- 替一段行為挑對函式介面
- 認出方法參考的四種寫法
- 用 Comparator 組合多鍵排序

---

*【先看痛點，再看解法】*

## 為什麼要有 lambda：把「一段行為」當參數傳

排序、篩選、事件處理這類工作，常常要把「怎麼做」交給別的方法決定。例如排序交易時，`List.sort` 自己會排，但「誰排前面」要你告訴它。Java 8 以前，要傳這段行為就得包成一個物件，最常見的寫法是**匿名類別**（anonymous class，當場宣告、當場建立、沒有名字的類別）：

```java
record Tx(String id, long amount) {}

List<Tx> txs = new ArrayList<>(List.of(new Tx("T1", 500), new Tx("T2", 120), new Tx("T3", 980)));

txs.sort(new Comparator<Tx>() {          // Java 8 以前：匿名類別
    @Override
    public int compare(Tx a, Tx b) {
        return Long.compare(a.amount(), b.amount());
    }
});
System.out.println(txs);
// [Tx[id=T2, amount=120], Tx[id=T1, amount=500], Tx[id=T3, amount=980]]

txs.sort((a, b) -> Long.compare(b.amount(), a.amount()));   // Java 8 起：lambda（這次由大到小）
System.out.println(txs);
// [Tx[id=T3, amount=980], Tx[id=T1, amount=500], Tx[id=T2, amount=120]]
```

> `record` 是 Java 16 起的精簡資料類別：一行宣告就自動有建構子、讀取方法 `amount()`、`equals`、`hashCode` 與上面印出來的那種 `toString`，細節在〈現代 Java 語法：var、record、switch、文字區塊與 sealed〉。

匿名類別五行裡真正在做事的只有 `return` 那一行，其餘都是格式。lambda 把格式拿掉，只留「參數」與「本體」：

- 在某些特定情況下，lambda 是寫匿名類別實例的另一種、更簡單的方式 [[出處]](https://dev.java/learn/language/fp/lambdas/first-lambdas/)
- lambda 運算式就像一個方法：它提供一串形式參數，以及用這些參數寫成的本體（一個運算式或一個區塊） [[出處]](https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html#jls-15.27)

好處在設計上：方法只負責流程，「挑哪幾筆」這種會變的規則改由呼叫端傳進來。下面的 `select` 寫一次，就能配任何篩選條件（`Predicate` 是下一段會介紹的現成介面，意思是「回答是或否的規則」）：

```java
static List<Tx> select(List<Tx> txs, Predicate<Tx> rule) {
    List<Tx> result = new ArrayList<>();
    for (Tx tx : txs) {
        if (rule.test(tx)) {          // 「怎麼篩」由呼叫端決定
            result.add(tx);
        }
    }
    return result;
}

select(txs, tx -> tx.amount() >= 500);      // [Tx[id=T3, amount=980], Tx[id=T1, amount=500]]
select(txs, tx -> tx.id().equals("T2"));    // [Tx[id=T2, amount=120]]
```

還有一件常被忽略的事：**寫下 lambda 不等於執行它。**對 lambda 運算式求值會產生一個**函式介面**（只有一個抽象方法的介面，後面「函式介面與 @FunctionalInterface」那一段細講）的實例，但不會執行本體；本體要等之後函式介面對應的方法被呼叫時才執行。 [[出處]](https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html#jls-15.27) 上面 `select` 裡，是 `rule.test(tx)` 這一行才真的跑了呼叫端寫的那段程式碼。

> 💡 **lambda＝只留參數與本體的匿名方法；寫下它只是「準備好」，被呼叫時才執行**

**🧩 小練習：** 下面哪一句最能說明 lambda 解決的問題？

- (A) 讓一個方法可以同時回傳好幾個值
- (B) 讓一個介面能宣告好幾個抽象方法，再用一個 lambda 全部實作
- (C) 傳一段行為時，不必再寫整個匿名類別
- (D) 讓方法可以不宣告回傳型別

<details><summary>看答案</summary>

**答案：(C)** lambda 解決的是「傳一段行為很囉嗦」：匿名類別的類別名稱、方法簽名、`@Override` 都省掉，只留參數與本體。它也不會讓介面能有多個抽象方法——lambda 只能實作「只有一個抽象方法」的介面。

</details>

**🧩 小練習：** 這段程式印出什麼？

- (A) T2
- (B) T1 T3
- (C) T3 T1
- (D) T1 T2 T3

<details><summary>看答案</summary>

**答案：(B)** 規則是「金額大於等於 500」，T1（500）與 T3（980）符合；迴圈照清單順序走，所以先印 T1 再印 T3。

</details>

**🧩 小練習：** 這段程式印出什麼？

- (A) 先印「扣款」，再印「建立完成」
- (B) 先印「建立完成」，再印「扣款」
- (C) 編譯錯誤，lambda 不能沒有參數
- (D) 只印「建立完成」

<details><summary>看答案</summary>

**答案：(D)** 寫下 lambda 只建立了一個 `Runnable` 物件，本體要等有人呼叫 `r.run()` 才執行。這段沒有呼叫，所以「扣款」不會印出。沒有參數的 lambda 寫 `()` 是合法的。

</details>

**🧩 小練習：** 一個 lambda 運算式的型別由什麼決定？

- (A) 看它放在哪裡：那個位置要的是哪個函式介面
- (B) 一律是 `Object`
- (C) 一律先當成 `java.util.function.Function`，執行時再轉成需要的介面
- (D) 由本體最後一行的回傳值決定

<details><summary>看答案</summary>

**答案：(A)** lambda 的型別必須是函式介面，可以來自變數、欄位、方法參數或方法的回傳型別。同一段 `s -> s.isEmpty()` 放進 `Predicate<String>` 就是 `Predicate`，放進 `Function<String, Boolean>` 就是 `Function`。

</details>

---

*【參數、箭頭、本體，以及能省的地方】*

## lambda 的各種寫法與型別推論

語法只有三塊：參數列、箭頭 `->`、本體（就是方法的本體）。 [[出處]](https://dev.java/learn/language/fp/lambdas/first-lambdas/)

> 合法與不合法的寫法： [[出處]](https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html#jls-15.27)

| 寫法 | 說明 |
|---|---|
| `() -> 42` | 沒有參數，括號不能省 |
| `x -> x + 1` | 只有一個參數、不寫型別時，括號可以省 |
| `(x, y) -> x + y` | 兩個以上參數要括號；型別交給編譯器推論 |
| `(int x, int y) -> x + y` | 自己寫出型別也可以 |
| `(int x) -> { return x + 1; }` | 本體是區塊（大括號）時，有回傳值就要寫 `return` |
| `(x, int y) -> x + y` | 不合法：推論型別與自己寫的型別不能混用 |
| `(x, final y) -> x + y` | 不合法：推論型別的參數不能加修飾字 |

本體有兩種：

- **運算式本體**：一個運算式，它的值就是回傳值，不寫 `return` 也不寫分號。
- **區塊本體**：大括號包起來的一般程式碼，要回傳值就得寫 `return`。

lambda 本體不是單一運算式，就是一個區塊。 [[出處]](https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html#jls-15.27.2)

參數的型別也可以寫 `var` [[出處]](https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html#jls-15.27.1)：它由 JEP 323 在 Java 11 加入，目的是讓 lambda 參數的寫法跟區域變數宣告一致。 [[出處]](https://openjdk.org/jeps/323) 但同一個參數列裡要嘛全寫、要嘛全不寫，混用會被 javac 擋下。

**型別推論**（type inference，編譯器從上下文猜出型別）能成立，是因為 lambda 永遠有一個「目標型別」：它被指定給的變數、被傳進的參數、或被轉型成的型別。lambda 只能出現在**指定、方法呼叫、轉型**這三種場合，放在別處就是編譯錯誤。 [[出處]](https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html#jls-15.27) 所以下面這行編不過——`var` 要從右邊推型別，lambda 卻要從左邊拿型別，兩邊都在等對方：

```java
var f = x -> x + 1;
// error: cannot infer type for local variable f
//   (lambda expression needs an explicit target-type)
```

> **Java 22 起的差異：**用不到的 lambda 參數可以寫成底線 `_`（JEP 456），表示「這裡一定要有個參數，但我不用它」，而且編譯器會強制它真的沒被用到。 [[出處]](https://openjdk.org/jeps/456) 這個寫法在 Java 21 還是**預覽功能**（preview feature：規格與實作都已完成、但還不是永久定案的功能，要加 `--enable-preview` 才能用） [[出處]](https://openjdk.org/jeps/12)，直接編譯會報 `unnamed variables are a preview feature and are disabled by default`；以 Java 25 執行：

```java
// Java 22 起（以 Java 25 執行）
Map<String, Long> balances = new TreeMap<>(Map.of("A001", 3_000L, "A002", 12_500L));
balances.forEach((_, balance) -> System.out.println(balance));   // 只用值，不用鍵
// 3000
// 12500
```

**🧩 小練習：** 下面哪一個 lambda **不合法**？

- (A) x -> x + 1
- (B) (int x, int y) -> x + y
- (C) (x, y) -> x + y
- (D) (x, int y) -> x + y

<details><summary>看答案</summary>

**答案：(D)** 同一個參數列不能一個交給編譯器推論、一個自己寫型別。javac 的錯誤訊息是 `cannot mix implicitly-typed and explicitly-typed parameters`。

</details>

**🧩 小練習：** 要寫一個不收參數、回傳 42 的 `Supplier<Integer>`，哪一個寫法正確？

- (A) -> 42
- (B) () -> 42
- (C) (void) -> 42
- (D) {} -> 42

<details><summary>看答案</summary>

**答案：(B)** 沒有參數時一定要寫一對空括號 `()`。沒有特別的無參數寫法，因為單寫 `->` 會跟轉型的語法打架。

</details>

**🧩 小練習：** `Function<Integer, Integer> f = x -> { x * 2; };` 會怎樣？

- (A) 可以編譯，`f.apply(3)` 回傳 6
- (B) 可以編譯，但 `f.apply(3)` 回傳 null，因為區塊裡沒寫 return
- (C) 編譯錯誤：區塊本體要寫 `return`
- (D) 可以編譯，但執行時丟出例外

<details><summary>看答案</summary>

**答案：(C)** 加了大括號就是區塊本體，裡面要放完整的敘述；`x * 2;` 不是合法的敘述（javac 報 `not a statement`）。改成 `x -> x * 2` 或 `x -> { return x * 2; }` 都對。

</details>

**🧩 小練習：** `var f = x -> x + 1;` 會怎樣？

- (A) 編譯錯誤：lambda 需要明確的目標型別
- (B) f 被推論成 `Function<Integer, Integer>`
- (C) f 被推論成 `IntUnaryOperator`
- (D) f 被推論成 `Object`

<details><summary>看答案</summary>

**答案：(A)** `var` 靠右邊推出型別，lambda 卻沒有自己的型別、要靠左邊給。左邊寫出函式介面（例如 `IntUnaryOperator f = x -> x + 1;`）就能編譯。

</details>

**🧩 小練習：** 下面哪一個參數列**不合法**？

- (A) (var x, var y) -> x + y
- (B) (Integer x, Integer y) -> x + y
- (C) (var x, y) -> x + y
- (D) (x, y) -> x + y

<details><summary>看答案</summary>

**答案：(C)** `var` 可以用在 lambda 參數上，但要每個參數都寫；只寫一半會被 javac 擋下（`cannot mix 'var' and implicitly-typed parameters`）。

</details>

**🧩 小練習：** `(String s) -> s.length()` 和 `s -> s.length()` 放在同一個 `ToIntFunction<String>` 變數上，差在哪？

- (A) 前者回傳 int、後者回傳 Integer
- (B) 行為一樣，只差在型別有沒有自己寫
- (C) 後者編譯不過：只有一個參數時，括號也一定要寫
- (D) 前者每次呼叫都會建立新的字串

<details><summary>看答案</summary>

**答案：(B)** 兩者都實作 `applyAsInt(String)`，回傳型別由函式介面決定。只有一個參數又不寫型別時，括號可以省。

</details>

**🧩 小練習：** Java 22 起的 `balances.forEach((_, balance) -> System.out.println(balance));` 裡，`_` 是什麼意思？

- (A) 參數名稱就叫底線，本體裡可以讀它
- (B) 代表任意型別的萬用字元
- (C) 代表這個位置傳入 null
- (D) 這個參數用不到，所以不取名字

<details><summary>看答案</summary>

**答案：(D)** `forEach` 要的 `BiConsumer` 一定有鍵、值兩個參數；只用值時，鍵寫成 `_`。它是「沒有名字的變數」，本體裡不能讀它。這是 Java 22 正式的功能（JEP 456），Java 21 要開預覽才能編譯。

</details>

---

*【lambda 能放進哪種介面】*

## 函式介面與 @FunctionalInterface

**函式介面**（functional interface）就是「只有一個抽象方法的介面」，lambda 就是在實作那唯一的方法。default 方法有實作，所以不算抽象方法。 [[出處]](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/FunctionalInterface.html) 介面的 default、static 方法在〈介面與抽象類別〉講過，它們都不影響「是不是函式介面」。

還有一個容易看漏的例外：介面裡如果宣告了跟 `Object` 公開方法一樣的抽象方法（例如 `boolean equals(Object obj)`），也不算進去，因為任何實作都會從 `java.lang.Object` 或別處得到實作。 [[出處]](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/FunctionalInterface.html) `Comparator` 就是這樣：它列了 `compare` 與 `equals` 兩個抽象方法，卻是函式介面。 [[出處]](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Comparator.html)

自己也能定義函式介面。銀行的手續費規則就很適合：

```java
@FunctionalInterface
interface FeeRule {
    long fee(long amount);

    default String describe() {        // default 方法有實作，不算抽象方法
        return "手續費規則";
    }
}

FeeRule flat = amount -> 15;                 // 每筆固定 15 元
FeeRule perMille = amount -> amount / 1000;  // 千分之一
System.out.println(flat.fee(50_000) + " " + perMille.fee(50_000) + " " + perMille.describe());
// 15 50 手續費規則
```

`@FunctionalInterface` 是給編譯器看的「我打算讓它當函式介面」：

- 加了之後如果不符合條件，編譯器一定要報錯
- 沒加也照樣能用 lambda：不論有沒有這個標註，編譯器都會把符合定義的介面當成函式介面 [[出處]](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/FunctionalInterface.html)

它的價值在防呆：哪天有人往 `FeeRule` 多加一個抽象方法，編譯會直接失敗，而不是讓所有寫成 lambda 的地方一起壞掉。

```java
@FunctionalInterface
interface FeeRule {
    long fee(long amount);
    long discount(long amount);   // 多一個抽象方法
}
// error: Unexpected @FunctionalInterface annotation
//   FeeRule is not a functional interface
//     multiple non-overriding abstract methods found in interface FeeRule
```

呼叫 lambda 就是呼叫那個抽象方法；呼叫 default 方法則跑介面裡寫好的程式碼。lambda 沒有辦法覆寫 default 方法。 [[出處]](https://dev.java/learn/language/fp/lambdas/first-lambdas/)

**🧩 小練習：** 下面哪一個介面是函式介面？

- (A) interface B { void a(); void b(); }
- (B) interface A { void run(); default void log() { } }
- (C) interface C { }
- (D) interface D { default void x() { } }

<details><summary>看答案</summary>

**答案：(B)** A 只有 `run` 一個抽象方法，default 方法不算。B 有兩個抽象方法；C、D 一個抽象方法都沒有，lambda 沒有東西可以實作。

</details>

**🧩 小練習：** `Comparator` 列了 `compare` 與 `equals` 兩個抽象方法，為什麼它還是函式介面？

- (A) 因為 `equals` 其實是 default 方法
- (B) 因為 `Comparator` 是類別不是介面
- (C) 因為 `equals` 對應 `Object` 的公開方法，不算數
- (D) 因為加了 `@FunctionalInterface` 就能有兩個抽象方法

<details><summary>看答案</summary>

**答案：(C)** 任何物件都從 `Object` 繼承了 `equals` 的實作，所以介面裡重新宣告它不會多要求實作者什麼，這種方法不計數。

</details>

**🧩 小練習：** 把一個只有一個抽象方法的介面上的 `@FunctionalInterface` 拿掉，會怎樣？

- (A) 原本指定給它的 lambda 全部編譯失敗，要改回匿名類別
- (B) 照樣能用 lambda，只少了編譯器的檢查
- (C) 執行時才會丟出例外
- (D) 編譯器會自動把它改成抽象類別

<details><summary>看答案</summary>

**答案：(B)** 標註只是「宣告意圖、請編譯器幫忙檢查」。符合定義的介面不管有沒有標註都是函式介面，標註不是編譯器認得函式介面的必要條件。

</details>

**🧩 小練習：** 替帶有 `@FunctionalInterface` 的 `FeeRule` 多加一個抽象方法 `long discount(long amount);`，會怎樣？

- (A) 沒事，lambda 會實作第一個宣告的方法
- (B) 沒事，lambda 會同時實作兩個方法
- (C) 可以編譯，呼叫 `discount` 時才丟例外
- (D) 編譯錯誤，`FeeRule` 已經不是函式介面

<details><summary>看答案</summary>

**答案：(D)** 有了標註，編譯器在介面本身就會報 `Unexpected @FunctionalInterface annotation`，錯誤停在介面宣告處，而不是散落在每個 lambda 上。

</details>

**🧩 小練習：** `FeeRule perMille = amount -> amount / 1000;`，`perMille.describe()` 回傳什麼？（`describe` 是 `FeeRule` 的 default 方法，回傳 `"手續費規則"`）

- (A) "手續費規則"
- (B) 編譯錯誤，lambda 沒有實作 describe
- (C) null
- (D) "amount / 1000"

<details><summary>看答案</summary>

**答案：(A)** lambda 只實作抽象方法 `fee`；`describe` 跑的是介面裡寫好的 default 實作，lambda 也沒辦法覆寫它。

</details>

---

*【不用自己定義，JDK 先準備好了】*

## java.util.function：七個常用介面與基本型別版

大部分情況不必自己寫函式介面，`java.util.function` 已經備齊常見的形狀：這些是 JDK 自己使用的通用函式介面，使用者的程式碼也可以用；雖然沒有涵蓋所有可能的形狀，但足以應付常見需求。 [[出處]](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/function/package-summary.html) 用「收什麼、回什麼」來分：

| 介面 | 收什麼 → 回什麼 | 抽象方法 | 銀行例子 |
|---|---|---|---|
| **`Function<T, R>`** | 一個 T → 一個 R | `apply` | 帳號 → 戶名 |
| **`Predicate<T>`** | 一個 T → `boolean` | `test` | 這筆交易是不是大額 |
| **`Consumer<T>`** | 一個 T → 沒有回傳 | `accept` | 寫一筆稽核紀錄 |
| **`Supplier<T>`** | 不收參數 → 一個 T | `get` | 產生新的交易編號 |
| **`BiFunction<T, U, R>`** | 一個 T、一個 U → 一個 R | `apply` | 金額＋筆數 → 手續費 |
| **`UnaryOperator<T>`** | 一個 T → 同型別的 T | `apply` | 帳號 → 遮罩後的帳號 |
| **`BinaryOperator<T>`** | 兩個 T → 同型別的 T | `apply` | 兩筆金額相加 |

> 出處： [[出處]](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/function/package-summary.html)

命名規則：基本形狀是 `Function`（T 到 R）、`Consumer`（T 到 void）、`Predicate`（T 到 boolean）、`Supplier`（無參數到 R）；加上前綴 Bi 表示兩個參數；`UnaryOperator` 延伸 `Function`、`BinaryOperator` 延伸 `BiFunction`。

`Consumer` 跟大多數函式介面不同，它預期透過副作用運作。 [[出處]](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/function/Consumer.html) 副作用（side effect）指方法除了回傳值以外對外界造成的改變，例如印出東西、寫進資料庫。

```java
Function<String, Integer> length = s -> s.length();
Predicate<Long> isLarge = amount -> amount >= 500_000;
Consumer<String> log = msg -> System.out.println("[LOG] " + msg);
Supplier<List<String>> newList = () -> new ArrayList<>();
BiFunction<Long, Integer, Long> fee = (amount, count) -> amount / 1000 * count;
UnaryOperator<String> mask = acct -> "****" + acct.substring(acct.length() - 4);
BinaryOperator<Long> add = (a, b) -> a + b;

length.apply("A001");            // 4
isLarge.test(800_000L);          // true
log.accept("轉帳成功");            // 印出 [LOG] 轉帳成功
newList.get().size();            // 0
fee.apply(20_000L, 3);           // 60
mask.apply("0123456789");        // ****6789
add.apply(100L, 250L);           // 350
```

**組合：**這些介面帶有 default 方法，可以把小規則接成大規則。`Function.andThen(after)`「先把這個函式套用到輸入，再把 after 套用到結果」，`compose(before)` 則「先套用 before，再把這個函式套用到結果」。 [[出處]](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/function/Function.html) `Predicate` 有 `and`、`or`、`negate`，Java 11 起還有靜態的 `Predicate.not`，回傳「把傳入的條件反過來」的新條件。 [[出處]](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/function/Predicate.html)

```java
Function<Long, Long> addFee = amount -> amount + 15;
Function<Long, Long> doubled = amount -> amount * 2;
addFee.andThen(doubled).apply(100L);   // 230：先加 15 再乘 2
addFee.compose(doubled).apply(100L);   // 215：先乘 2 再加 15

Predicate<String> hasText = Predicate.not(String::isBlank);
Predicate<String> isTW = s -> s.startsWith("TW");
hasText.and(isTW).test("TW123");       // true
hasText.test("  ");                    // false
```

**基本型別版：**泛型只能放參考型別，所以 `Predicate<Integer>` 每次判斷都要把 `int` 包成 `Integer`（裝箱，boxing）再拆開（拆箱）。裝箱與拆箱不是免費的，多數時候比起查資料庫不算什麼，但有時無法接受。 [[出處]](https://dev.java/learn/language/fp/lambdas/functional-interfaces/)

所以 JDK 另外準備了直接收基本型別的版本，命名有規則：

- **參數是基本型別**：前綴 `Int`、`Long`、`Double`。
- **回傳基本型別**：`ToInt` 這類前綴，例如 `ToIntFunction`。 [[出處]](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/function/package-summary.html)

例如 `IntPredicate` 就是收 `int` 的 `Predicate`。 [[出處]](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/function/IntPredicate.html)

```java
IntPredicate isEven = n -> n % 2 == 0;          // 收 int，不裝箱
ToLongFunction<Tx> amountOf = Tx::amount;        // 回傳 long，不裝箱
IntUnaryOperator plusOne = n -> n + 1;

isEven.test(4);                          // true
amountOf.applyAsLong(new Tx("T9", 77));  // 77
plusOne.applyAsInt(41);                  // 42
```

**🧩 小練習：** 要寫一個規則：輸入帳號，回答「這個帳戶是不是被凍結」。最適合哪個介面？

- (A) Function<String, String>
- (B) Consumer<String>
- (C) Supplier<Boolean>
- (D) Predicate<String>

<details><summary>看答案</summary>

**答案：(D)** 收一個值、回答是或否，就是 `Predicate`（抽象方法 `test` 回傳 `boolean`）。`Supplier` 不收參數，拿不到帳號。

</details>

**🧩 小練習：** 要把一筆稽核事件寫進紀錄檔，寫完不需要回傳任何東西。最適合哪個介面？

- (A) Supplier<AuditEvent>
- (B) Consumer<AuditEvent>
- (C) Function<AuditEvent, Void>
- (D) Predicate<AuditEvent>

<details><summary>看答案</summary>

**答案：(B)** 收一個值、沒有回傳，靠副作用做事，正是 `Consumer`。`Function<AuditEvent, Void>` 也寫得出來，但每次都得 `return null;`，是硬湊。

</details>

**🧩 小練習：** 要一個「每次呼叫就產生一個新的交易編號」的物件，不需要任何輸入。最適合哪個介面？

- (A) Supplier<String>
- (B) Consumer<String>
- (C) UnaryOperator<String>
- (D) Predicate<String>

<details><summary>看答案</summary>

**答案：(A)** 不收參數、回傳一個值就是 `Supplier`，用 `get()` 取值。`UnaryOperator` 需要一個輸入。

</details>

**🧩 小練習：** 輸入本金（`Long`）與存款天數（`Integer`），回傳利息（`Long`）。最適合哪個介面？

- (A) Function<Long, Long>
- (B) BinaryOperator<Long>
- (C) BiFunction<Long, Integer, Long>
- (D) BiConsumer<Long, Integer>

<details><summary>看答案</summary>

**答案：(C)** 兩個輸入、一個輸出，而且型別不同，用 `BiFunction`。`BinaryOperator<Long>` 要求兩個輸入跟輸出全是 `Long`，天數是 `Integer` 就放不進去；`BiConsumer` 沒有回傳值。

</details>

**🧩 小練習：** `UnaryOperator<String>` 和 `Function<String, String>` 是什麼關係？

- (A) 兩者無關，只是剛好方法同名
- (B) UnaryOperator 延伸 Function，輸入輸出同型別
- (C) Function 延伸 UnaryOperator，是比較一般化的版本
- (D) UnaryOperator 只能用在數字

<details><summary>看答案</summary>

**答案：(B)** `UnaryOperator` 是 `Function` 在「運算元與結果同型別」時的特化版，介面宣告就是延伸 `Function<T, T>`，所以它的抽象方法一樣叫 `apply`。

</details>

**🧩 小練習：** 這段程式印出什麼？

- (A) 215
- (B) 200
- (C) 115
- (D) 230

<details><summary>看答案</summary>

**答案：(D)** `andThen` 先跑自己再跑參數：100 先加 15 得 115，再乘 2 得 230。

</details>

**🧩 小練習：** 同上兩個函式，`addFee.compose(doubled).apply(100L)` 回傳什麼？

- (A) 230
- (B) 215
- (C) 130
- (D) 200

<details><summary>看答案</summary>

**答案：(B)** `compose` 先跑參數再跑自己：100 先乘 2 得 200，再加 15 得 215。跟 `andThen` 方向相反。

</details>

**🧩 小練習：** `Predicate.not(String::isBlank).test("  ")` 回傳什麼？

- (A) false
- (B) true
- (C) 編譯錯誤，not 只能接 lambda
- (D) 丟出 NullPointerException

<details><summary>看答案</summary>

**答案：(A)** `"  "` 只有空白，`isBlank` 是 true；`not` 把它反過來，得到 false。`not` 收任何 `Predicate`，方法參考也行。

</details>

**🧩 小練習：** 這段程式印出什麼？

- (A) TWD 換行 結束
- (B) twd 換行 結束
- (C) 結束
- (D) 編譯錯誤，Consumer 不能接有回傳值的運算式

<details><summary>看答案</summary>

**答案：(C)** `toUpperCase()` 回傳一個新字串，但 `accept` 沒有回傳值，這個結果就被丟掉了；它也沒有印東西。回傳 void 的函式介面可以接「本身就能當一行敘述的運算式」，例如方法呼叫 [[出處]](https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html#jls-15.27.3)，所以能編譯；換成 `s -> s.length() + 1` 這種不能單獨成為敘述的運算式就編不過。

</details>

**🧩 小練習：** JDK 為什麼要另外準備 `IntPredicate`，而不是全部用 `Predicate<Integer>`？

- (A) 因為 `Predicate<Integer>` 不能用 lambda 實作
- (B) 因為 `Predicate<Integer>` 只能判斷正數
- (C) 因為 `IntPredicate` 可以有兩個抽象方法
- (D) 為了避免每次判斷都把 int 裝箱成 Integer 的成本

<details><summary>看答案</summary>

**答案：(D)** 泛型只收參考型別，`Predicate<Integer>` 的 `test` 收的是 `Integer` 物件。`IntPredicate.test(int)` 直接收基本型別，省掉裝箱與拆箱。

</details>

---

*【lambda 只是在轉呼叫時】*

## 方法參考的四種寫法

很多 lambda 只是把參數原封不動交給另一個現成的方法，例如 `s -> System.out.println(s)`。這時可以改寫成**方法參考**（method reference），用兩個冒號 `::` 指出「就用那個方法」：它指稱一個方法的呼叫，但不實際執行那個呼叫。 [[出處]](https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html#jls-15.13) 方法參考分成四類： [[出處]](https://dev.java/learn/language/fp/lambdas/method-references/)

| 種類 | 寫法 | 等價的 lambda | 例子 |
|---|---|---|---|
| **靜態方法** | `類別::靜態方法` | `(args) -> 類別.靜態方法(args)` | `Integer::parseInt` |
| **特定物件的實例方法** | `物件::實例方法` | `(args) -> 物件.實例方法(args)` | `System.out::println` |
| **某型別任意物件的實例方法** | `型別::實例方法` | `(arg0, rest) -> arg0.實例方法(rest)` | `String::toUpperCase` |
| **建構子** | `類別::new` | `(args) -> new 類別(args)` | `ArrayList::new` |

最容易搞混的是第二、三種，分別叫「綁定」（bound）與「未綁定」（unbound）： [[出處]](https://dev.java/learn/language/fp/lambdas/method-references/)

- **綁定**（特定物件）：呼叫方法的物件寫在方法參考裡
- **未綁定**（任意物件）：物件不在寫法裡，而是當成 lambda 的參數傳進來

所以 `String::toUpperCase` 看起來像呼叫靜態方法，其實是「拿第一個參數來呼叫 `toUpperCase()`」；`String::equalsIgnoreCase` 放進 `BiFunction` 時，第一個參數是呼叫者、第二個參數變成方法的引數。

```java
Function<String, Integer> parse = Integer::parseInt;            // 靜態方法
Consumer<String> printer = System.out::println;                 // 特定物件的實例方法
Function<String, String> upper = String::toUpperCase;           // 任意物件的實例方法
BiFunction<String, String, Boolean> same = String::equalsIgnoreCase;
Supplier<List<String>> make = ArrayList::new;                   // 建構子
Function<String, BigDecimal> toMoney = BigDecimal::new;         // 帶參數的建構子

System.out.println(parse.apply("42") + 1);       // 43
printer.accept("hello");                         // 印出 hello
upper.apply("twd");                              // TWD
same.apply("USD", "usd");                        // true，等於 "USD".equalsIgnoreCase("usd")
make.get();                                      // []
toMoney.apply("1250.50").add(BigDecimal.ONE);    // 1251.50
```

建構子參考要看目標型別才知道呼叫哪一個建構子：同一個 `ArrayList::new`，放進 `Supplier` 呼叫無參數建構子，放進 `Function<Integer, …>` 就呼叫帶容量的那個，兩者指的不是同一個建構子。 [[出處]](https://dev.java/learn/language/fp/lambdas/method-references/)

> Java 25 起也可以寫 `IO::println`：`java.lang.IO` 是 JEP 512 在 Java 25 加入的新類別 [[出處]](https://openjdk.org/jeps/512)；Java 21 要寫 `System.out::println`。

**🧩 小練習：** `Integer::parseInt` 屬於哪一種方法參考？

- (A) 特定物件的實例方法
- (B) 靜態方法
- (C) 某型別任意物件的實例方法
- (D) 建構子

<details><summary>看答案</summary>

**答案：(B)** `parseInt` 是 `Integer` 的靜態方法，`Integer::parseInt` 等於 `s -> Integer.parseInt(s)`。

</details>

**🧩 小練習：** `Function<String, String> upper = String::toUpperCase;` 等於哪一個 lambda？

- (A) s -> String.toUpperCase(s)
- (B) () -> "".toUpperCase()
- (C) s -> s.toUpperCase()
- (D) s -> toUpperCase(s)

<details><summary>看答案</summary>

**答案：(C)** `toUpperCase` 是實例方法，`String` 沒有叫這個名字的靜態方法。「型別::實例方法」的意思是拿第一個參數當呼叫者：`s.toUpperCase()`。

</details>

**🧩 小練習：** `System.out::println` 屬於哪一種方法參考？

- (A) 特定物件的實例方法
- (B) 靜態方法
- (C) 某型別任意物件的實例方法
- (D) 建構子

<details><summary>看答案</summary>

**答案：(A)** `System.out` 是一個已經存在的 `PrintStream` 物件，`println` 是它的實例方法；呼叫者寫在方法參考裡，屬於「綁定」的那一種。

</details>

**🧩 小練習：** `BiFunction<String, String, Boolean> same = String::equalsIgnoreCase;`，呼叫 `same.apply("USD", "usd")` 時，第一個參數 `"USD"` 扮演什麼角色？

- (A) 被丟掉，只比較 "usd"
- (B) 當成 `equalsIgnoreCase` 的引數
- (C) 當成 `String` 建構子的引數
- (D) 呼叫 `equalsIgnoreCase` 的那個物件

<details><summary>看答案</summary>

**答案：(D)** 未綁定的方法參考，第一個參數是呼叫者、其餘是引數，所以等於 `"USD".equalsIgnoreCase("usd")`，回傳 true。

</details>

**🧩 小練習：** `ArrayList::new` 分別指定給 `Supplier<List<String>>` 與 `Function<Integer, List<String>>`，兩者呼叫的建構子一樣嗎？

- (A) 一樣，都是無參數建構子
- (B) 不一樣：分別對到無參數與收容量的建構子
- (C) 後者編譯錯誤，建構子參考不能帶參數
- (D) 一樣，都呼叫收初始容量的建構子，只是前者把容量當成 0

<details><summary>看答案</summary>

**答案：(B)** 建構子參考依目標型別挑建構子：`Supplier.get()` 不收參數，就對到 `ArrayList()`；`Function.apply(Integer)` 收一個整數，就對到 `ArrayList(int initialCapacity)`。

</details>

**🧩 小練習：** 這段程式印出什麼？

- (A) 421
- (B) 42
- (C) 43
- (D) 編譯錯誤

<details><summary>看答案</summary>

**答案：(C)** `apply` 回傳 `Integer` 42，加 1 是數字相加得 43。如果回傳的是字串 `"42"`，加 1 才會變成 `"421"`。

</details>

**🧩 小練習：** 下面哪一個 lambda **沒辦法**直接改寫成方法參考？

- (A) s -> s.length()
- (B) s -> System.out.println(s)
- (C) () -> new ArrayList<String>()
- (D) tx -> tx.amount() > 500

<details><summary>看答案</summary>

**答案：(D)** 方法參考只能代表「呼叫一個現成的方法」。`tx.amount() > 500` 先呼叫方法、再跟 500 比較，多了一步運算，沒有對應的單一方法。其餘三個分別是 `String::length`、`System.out::println`、`ArrayList::new`。

</details>

---

*【lambda 看得到外面的什麼】*

## 變數捕獲：effectively final，以及 this 指誰

lambda 本體可以讀外面的區域變數，這叫**捕獲**（capture）。但有條件：lambda 裡用到、卻不是在 lambda 裡宣告的區域變數、方法參數或例外參數，必須是 **final 或 effectively final**。 [[出處]](https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html#jls-15.27.2) **effectively final**（實質上不變）是「沒寫 `final`，但行為跟 final 一樣」：宣告時給了值之後，從沒被重新指派，也從沒被 `++`、`--` 改過。判準是：加上 `final` 修飾字也不會產生任何編譯錯誤。 [[出處]](https://docs.oracle.com/javase/specs/jls/se21/html/jls-4.html#jls-4.12.4)

```java
long limit = 1_000;
Predicate<Long> over = amount -> amount > limit;
limit = 2_000;   // 這一行讓 limit 不再是 effectively final
// error: local variables referenced from a lambda expression must be final or effectively final
```

注意錯誤報在 lambda 那一行：只要變數在任何地方被改過，它就不是 effectively final，lambda 就不能用它。最常踩到的是想在 `forEach` 裡累加：

```java
long total = 0;
amounts.forEach(a -> total += a);
// error: local variables referenced from a lambda expression must be final or effectively final
```

為什麼要這樣限制？為了禁止存取一直在變動的區域變數，因為捕獲它們很可能引出並行問題。 [[出處]](https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html#jls-15.27.2) lambda 可能被交給別的執行緒、在之後才執行，那時外面的變數早就不是原來的值了。一句話：lambda **不能捕獲變數，只能捕獲值**。 [[出處]](https://dev.java/learn/language/fp/lambdas/first-lambdas/) 要加總就換個做法：用一般迴圈，或用〈Stream API：把迴圈寫成資料流〉的 `mapToLong(...).sum()`，讓加總變成回傳值而不是去改外面的變數。

兩個細節：

- 一般 `for (int i = 0; ...; i++)` 的 `i` 每圈都被 `++` 改，所以不能捕獲；增強型 `for (String id : ids)` 的 `id` 卻可以，因為它被當成每一圈各自不同的變數。 [[出處]](https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html#jls-15.27.2)
- 這條限制只管區域變數、參數與例外參數，物件的欄位不在其中，lambda 可以改欄位——但多執行緒時改欄位一樣要自己處理同步，見〈執行緒與並行〉。

**this 指誰：**匿名類別是一個新的類別，裡面的 `this` 指那個匿名類別的物件；lambda 不是新類別，本體裡的名稱以及 `this`、`super` 的意義，都跟周圍的程式碼相同。 [[出處]](https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html#jls-15.27.2)

```java
class Teller {
    String name = "櫃員 A";

    void demo() {
        Runnable byLambda = () -> System.out.println("lambda 裡的 this：" + this.name);
        Runnable byAnonymous = new Runnable() {
            String name = "匿名類別自己";
            @Override
            public void run() {
                System.out.println("匿名類別裡的 this：" + this.name);
            }
        };
        byLambda.run();
        byAnonymous.run();
    }
}
// new Teller().demo() 印出：
// lambda 裡的 this：櫃員 A
// 匿名類別裡的 this：匿名類別自己
```

受檢例外也有限制。`Function.apply`、`Consumer.accept` 這些方法都沒宣告 `throws`，而 lambda 本體丟出的受檢例外，必須是目標函式介面方法 `throws` 子句所宣告例外的子類別，否則編譯錯誤。 [[出處]](https://docs.oracle.com/javase/specs/jls/se21/html/jls-11.html#jls-11.2.3) 所以在 `forEach` 裡直接讀檔會編不過，要在 lambda 裡自己 `try`／`catch`，或改用一般迴圈；受檢例外本身見〈例外機制〉。

```java
paths.forEach(p -> System.out.println(Files.readString(p)));
// error: unreported exception IOException; must be caught or declared to be thrown
```

**🧩 小練習：** 這段程式會怎樣？

- (A) 印出 true
- (B) 印出 false
- (C) 編譯錯誤
- (D) 執行時丟出例外

<details><summary>看答案</summary>

**答案：(C)** `limit` 之後被重新指派，就不是 effectively final，lambda 不能捕獲它，javac 在 lambda 那行報錯。程式根本跑不到印出那一步。

</details>

**🧩 小練習：** `long total = 0; amounts.forEach(a -> total += a);` 編譯失敗。下面哪個說法對？

- (A) 因為 `forEach` 只能接方法參考
- (B) 因為 lambda 不能改外面的區域變數 total
- (C) 因為 long 不能用 `+=`
- (D) 把 total 宣告成 `final` 就能編譯，因為 final 變數可以給 lambda 用

<details><summary>看答案</summary>

**答案：(B)** `total += a` 是對 total 重新指派。加 `final` 反而更不能改。該做的是換寫法：一般迴圈，或讓加總成為回傳值（例如 Stream 的 `sum()`）。

</details>

**🧩 小練習：** 下面哪個區域變數是 effectively final？

- (A) 宣告 `int n = 0;` 之後在迴圈裡做了 `n++`
- (B) 宣告 `String s = "A";` 之後又寫了 `s = "B";`
- (C) 宣告 `long fee = 15;` 之後只被讀取，從沒被指派或遞增
- (D) 欄位 `private int count;`

<details><summary>看答案</summary>

**答案：(C)** effectively final 的條件是宣告後不再被指派、不被 `++`／`--`。欄位不是區域變數，這個概念不適用在它身上。

</details>

**🧩 小練習：** 下面兩段，哪一段能編譯？  
甲：`for (int i = 0; i < 3; i++) { Runnable r = () -> System.out.println(i); }`  
乙：`for (String id : ids) { Runnable r = () -> System.out.println(id); }`

- (A) 兩段都能
- (B) 只有甲
- (C) 只有乙
- (D) 兩段都不能

<details><summary>看答案</summary>

**答案：(C)** 甲的 `i` 每圈被 `i++` 修改，不是 effectively final；乙的 `id` 被當成每一圈各自獨立的變數，每個都沒被改過，可以捕獲。

</details>

**🧩 小練習：** 上面 `Teller` 的例子，為什麼 lambda 印「櫃員 A」，匿名類別印「匿名類別自己」？

- (A) lambda 的 this 指外面的 Teller；匿名類別的 this 指自己
- (B) lambda 裡的 this 指 Runnable 介面本身
- (C) 匿名類別裡的 this 指 Teller，lambda 裡的 this 指 lambda 物件
- (D) 因為兩個 name 宣告的先後順序不同

<details><summary>看答案</summary>

**答案：(A)** lambda 本體裡 `this`、`super` 與名稱的意義跟周圍程式碼相同；匿名類別裡就不是，它有自己的欄位 `name`，`this.name` 就讀到它自己的。

</details>

**🧩 小練習：** 限制 lambda 只能用 effectively final 的區域變數，主要是為了避免什麼？

- (A) 避免 lambda 佔用太多記憶體
- (B) 避免 lambda 執行得比匿名類別慢
- (C) 避免 lambda 讀到物件的欄位
- (D) 避免捕獲一直在變的區域變數而引出並行問題

<details><summary>看答案</summary>

**答案：(D)** 這個限制禁止存取一直在變動的區域變數，因為捕獲它們很可能引出並行問題。lambda 可能在別的執行緒、之後才執行。欄位反而不受這條限制。

</details>

**🧩 小練習：** 這段程式印出什麼？

- (A) 編譯錯誤，lambda 不能改外面的變數
- (B) 0
- (C) 3
- (D) 1

<details><summary>看答案</summary>

**答案：(C)** `count` 是欄位，不是區域變數，effectively final 的限制管不到它（lambda 裡的 `count` 其實是 `this.count`）。單執行緒依序跑三次，結果是 3；多執行緒同時改就要自己處理同步。

</details>

**🧩 小練習：** `paths.forEach(p -> System.out.println(Files.readString(p)));` 編譯失敗，原因是什麼？（`Files.readString` 宣告會丟 `IOException`）

- (A) `forEach` 不能用在 `List<Path>`，只能用在字串清單
- (B) `Consumer.accept` 沒宣告 `throws IOException`
- (C) lambda 裡不能呼叫靜態方法
- (D) p 不是 effectively final

<details><summary>看答案</summary>

**答案：(B)** lambda 能丟的受檢例外，受限於目標函式介面方法的 `throws` 子句。`accept` 什麼都沒宣告，所以要在 lambda 裡自己 `try`／`catch`，或改用一般迴圈。

</details>

---

*【多鍵排序一行寫完】*

## Comparator 的組合：comparing、thenComparing、reversed

`Comparator` 是函式介面，所以可以用 lambda 寫；但更好讀的是它的工廠方法與 default 方法： [[出處]](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Comparator.html)

- `Comparator.comparing(取鍵的函式)`：收一個從 T 取出可比較排序鍵的函式，回傳依那個鍵比較的 `Comparator<T>`
- `thenComparing(other)`：這個 Comparator 認為兩個元素相等（`compare(a, b) == 0`）時，用 other 決定順序
- `reversed()`：回傳順序相反的 comparator

跟 `Comparable`、`TreeSet` 怎麼用比較結果判斷重複的關係，見〈集合與泛型〉。

職場例子：轉帳清單依**金額由大到小**排，同金額再依**時間由早到晚**排。

```java
record Transfer(String id, long amount, LocalTime time) {}

List<Transfer> list = new ArrayList<>(List.of(
        new Transfer("T1", 3000, LocalTime.of(9, 30)),
        new Transfer("T2", 5000, LocalTime.of(10, 15)),
        new Transfer("T3", 3000, LocalTime.of(9, 5)),
        new Transfer("T4", 5000, LocalTime.of(9, 45))));

list.sort(Comparator.comparingLong(Transfer::amount).reversed()
        .thenComparing(Transfer::time));
// T4 5000 09:45
// T2 5000 10:15
// T3 3000 09:05
// T1 3000 09:30
```

關鍵在 `reversed()` 放在哪裡。它反轉的是「呼叫它的那整個 Comparator」，放在最後就連時間也一起反過來：

```text
list.sort(Comparator.comparingLong(Transfer::amount)
        .thenComparing(Transfer::time)
        .reversed());                 // 整串反轉：金額大到小，同金額時間「晚到早」
// T2 5000 10:15
// T4 5000 09:45
// T1 3000 09:30
// T3 3000 09:05

list.sort(Comparator.comparing(Transfer::amount, Comparator.reverseOrder())
        .thenComparing(Transfer::time));   // 只反轉金額這個鍵，結果跟第一段相同
// T4 5000 09:45
// T2 5000 10:15
// T3 3000 09:05
// T1 3000 09:30
```

`comparingLong`、`comparingInt` 是基本型別版，取出的鍵不必裝箱；這些特化版本就是為了省掉比較器裡的裝箱成本。 [[出處]](https://dev.java/learn/language/fp/lambdas/writing-comparators/)

> 一個常見的編譯錯誤：`Comparator.comparing(t -> t.amount()).reversed()` 編不過，javac 報 `cannot find symbol: method amount()`、`location: variable t of type Object`。因為 `.reversed()` 是呼叫在 `comparing(...)` 的結果上，`comparing(...)` 這段就不再位於指定或方法引數的位置；方法呼叫要出現在指定或方法呼叫的場合，才會從外面拿目標型別 [[出處]](https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html#jls-15.12)，於是 lambda 參數 `t` 只好推成 `Object`。改用方法參考 `Transfer::amount`，或把參數型別寫出來 `(Transfer t) -> t.amount()`，就能編譯。

**🧩 小練習：** 用上面四筆轉帳（T1 3000／09:30、T2 5000／10:15、T3 3000／09:05、T4 5000／09:45），`comparingLong(Transfer::amount).reversed().thenComparing(Transfer::time)` 排完後，第一筆是哪一筆？

- (A) T2
- (B) T3
- (C) T4
- (D) T1

<details><summary>看答案</summary>

**答案：(C)** 先依金額由大到小：T2、T4 是 5000。同金額再依時間由早到晚：T4（09:45）早於 T2（10:15），所以 T4 排第一。

</details>

**🧩 小練習：** 同樣四筆，改成 `comparingLong(Transfer::amount).thenComparing(Transfer::time).reversed()`，結果是哪一種？

- (A) 金額由大到小，同金額時間由早到晚
- (B) 金額由大到小，同金額時間由晚到早
- (C) 金額由小到大，同金額時間由晚到早
- (D) 只有金額反轉，時間不受影響

<details><summary>看答案</summary>

**答案：(B)** `reversed()` 接在整串後面，反轉的是「先金額、再時間」這整個比較器，兩個鍵都倒過來，實跑順序是 T2、T4、T1、T3。

</details>

**🧩 小練習：** `thenComparing` 裡的比較規則，什麼時候才會被用到？

- (A) 每一次比較都會先用它
- (B) 只有排序最後一輪才用
- (C) 前面的比較結果是 0 時
- (D) 前面的比較器丟出例外時

<details><summary>看答案</summary>

**答案：(C)** 這個 Comparator 認為兩個元素相等（`compare(a, b) == 0`）時，才用 other 決定順序。金額不同時，時間根本不會被比較。

</details>

**🧩 小練習：** `list.sort(Comparator.comparing(t -> t.amount()).reversed());` 編譯失敗，訊息說 `t` 的型別是 `Object`。怎麼改最直接？

- (A) 把 `reversed()` 換成 `reverse()`
- (B) 把 list 改成陣列
- (C) 在最前面加上 `@FunctionalInterface`
- (D) 改用方法參考 `Transfer::amount`

<details><summary>看答案</summary>

**答案：(D)** 鏈在後面的 `.reversed()` 讓編譯器沒辦法從 `list.sort` 推出 lambda 參數的型別。方法參考 `Transfer::amount` 自帶型別，或寫成 `(Transfer t) -> t.amount()` 也行。

</details>

**🧩 小練習：** 要「金額由大到小、同金額時間由早到晚」，下面哪一個比較器正確？

- (A) comparing(Transfer::amount, Comparator.reverseOrder()).thenComparing(Transfer::time)
- (B) comparing(Transfer::amount).thenComparing(Transfer::time).reversed()
- (C) comparing(Transfer::time).thenComparing(Transfer::amount).reversed()
- (D) comparing(Transfer::amount).reversed().thenComparing(Transfer::time).reversed()

<details><summary>看答案</summary>

**答案：(A)** 只把金額這個鍵的比較改成反序，時間照自然順序。`thenComparing(Transfer::time).reversed()` 那個把整串反轉，時間也變晚到早；`comparing(Transfer::time)` 開頭的那個以時間為主鍵；`reversed()` 出現兩次的那個，第二次又把整串翻回金額小到大、時間晚到早。

</details>

**🧩 小練習：** 這段程式印出什麼？

- (A) [a, ab, bb, c]
- (B) [a, c, bb, ab]
- (C) [bb, a, ab, c]
- (D) [a, c, ab, bb]

<details><summary>看答案</summary>

**答案：(D)** 先比長度：一個字的 a、c 在前，兩個字的 ab、bb 在後；同長度再依字母順序，a 在 c 前、ab 在 bb 前。

</details>

---

*【「可能查不到」寫進型別裡】*

## Optional：用回傳型別表達「沒有結果」

查帳戶戶名，查不到時以前多半回傳 `null`，呼叫端一忘記檢查就是 `NullPointerException`。`Optional` 把「可能沒有值」寫進回傳型別，逼呼叫端面對它： [[出處]](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Optional.html)

- 它是可能裝著、也可能沒裝著一個非 null 值的容器物件
- 主要設計來當方法的回傳型別，用在明確需要表達「沒有結果」、而用 null 很可能出錯的地方

| 方法 | 做什麼 |
|---|---|
| `Optional.of(v)` | 包一個**不是 null** 的值；傳 null 會丟 `NullPointerException` |
| `Optional.ofNullable(v)` | v 不是 null 就包起來，是 null 就回傳空的 Optional |
| `Optional.empty()` | 回傳空的 Optional |
| `map(f)` | 有值就套用 f、把結果再包成 Optional（f 回傳 null 就變空的）；沒值就維持空的 |
| `filter(p)` | 有值而且符合 p 才留下，否則變空的 |
| `orElse(other)` | 有值回傳值，沒值回傳 other |
| `orElseGet(supplier)` | 有值回傳值，沒值才呼叫 supplier 產生一個 |
| `orElseThrow()`／`orElseThrow(supplier)` | 有值回傳值，沒值丟 `NoSuchElementException`／丟 supplier 產生的例外 |

> 出處： [[出處]](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Optional.html)

`orElseThrow()` 是 Java 10 加的，是 `get()` 比較建議的替代寫法。 [[出處]](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Optional.html)

```java
static final Map<String, String> OWNERS = Map.of("A001", "王小明", "A002", "陳美玲");

static Optional<String> findOwner(String accountId) {
    return Optional.ofNullable(OWNERS.get(accountId));   // 查不到時 get 回傳 null
}

findOwner("A001").map(String::length).orElse(0);   // 3
findOwner("Z999").orElse("查無此帳戶");              // 查無此帳戶
findOwner("Z999").isPresent();                     // false
findOwner("Z999").orElseThrow(() -> new IllegalArgumentException("查無帳戶：Z999"));
// 丟出 IllegalArgumentException：查無帳戶：Z999
Optional.of(null);                                 // 丟出 NullPointerException
```

**`orElse` 與 `orElseGet` 的差別**在「預設值什麼時候算」：

- Java 呼叫方法前，會先把所有引數算出來（方法呼叫的執行步驟裡，第二步就是對引數運算式求值） [[出處]](https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html#jls-15.12.4)，所以 `orElse(查資料庫())` 不管有沒有值都會先查一次
- `orElseGet` 做的事一樣，但不必先建立那個預設物件，提供的 supplier 只在需要時才被呼叫 [[出處]](https://dev.java/learn/api/collections-and-streams/streams/optionals/)

```java
static String loadDefaultBranch() {
    System.out.println("（去資料庫查預設分行）");
    return "總行";
}

String a = Optional.of("信義分行").orElse(loadDefaultBranch());
// 印出：（去資料庫查預設分行）   ← 明明有值，還是查了一次
// a 是 信義分行
String b = Optional.of("信義分行").orElseGet(() -> loadDefaultBranch());
// 什麼都沒印，b 是 信義分行
String c = Optional.<String>empty().orElseGet(() -> loadDefaultBranch());
// 印出：（去資料庫查預設分行）
// c 是 總行
```

**不要怎麼用：**

- **不放欄位、參數、集合**：不要把 Optional 用在欄位、方法參數、集合與 Map 裡。 [[出處]](https://dev.java/learn/api/collections-and-streams/streams/optionals/)
- **本身不是 null**：Optional 型別的變數或回傳值永遠不要是 null，應該一律指向一個 Optional 實例。 [[出處]](https://dev.java/learn/api/collections-and-streams/streams/optionals/) [[出處]](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Optional.html)
- **不用 == 比**：不要拿 `==` 跟 `Optional.empty()` 比，它不保證是同一個物件，要用 `isEmpty()` 或 `isPresent()`。 [[出處]](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Optional.html)
- **少用 get**：先 `isPresent()` 再 `get()` 雖然不會錯，但跟直接判斷 null 沒有兩樣，`map`、`orElse` 這些方法才是 `Optional` 好用的地方；優先用 `ifPresent()`、`orElseThrow()`、`get()` 以外的替代寫法。 [[出處]](https://dev.java/learn/api/collections-and-streams/streams/optionals/)

> 💡 **Optional 當回傳型別用；查不到回傳 Optional.empty()，不回傳 null；預設值很貴就用 orElseGet**

**🧩 小練習：** `Optional.ofNullable(OWNERS.get("Z999")).orElse("查無此帳戶")` 回傳什麼？（OWNERS 裡沒有 Z999）

- (A) null
- (B) 丟出 NoSuchElementException
- (C) "查無此帳戶"
- (D) Optional.empty

<details><summary>看答案</summary>

**答案：(C)** `Map.get` 查不到回傳 null，`ofNullable(null)` 得到空的 Optional，`orElse` 就回傳給定的預設值。`orElse` 回傳的是值本身，不是 Optional。

</details>

**🧩 小練習：** `Optional.of(null)` 會怎樣？

- (A) 丟出 NullPointerException
- (B) 回傳空的 Optional
- (C) 回傳裝著 null 的 Optional
- (D) 編譯錯誤

<details><summary>看答案</summary>

**答案：(A)** `of` 要求傳入非 null 的值，傳 null 會丟 `NullPointerException`。值可能是 null 時要用 `ofNullable`。

</details>

**🧩 小練習：** `Optional.ofNullable(OWNERS.get("Z999")).map(String::length).orElse(-1)` 回傳什麼？

- (A) 0
- (B) -1
- (C) 丟出 NullPointerException
- (D) 4

<details><summary>看答案</summary>

**答案：(B)** 查不到，Optional 是空的；對空的 Optional 做 `map` 不會呼叫 `String::length`，結果還是空的，最後由 `orElse` 給 -1。不必自己判斷 null。

</details>

**🧩 小練習：** 這段程式印出什麼？

- (A) 只印「信義分行」
- (B) 只印「總行」
- (C) 先印「查預設值」，再印「總行」
- (D) 先印「查預設值」，再印「信義分行」

<details><summary>看答案</summary>

**答案：(D)** Java 先算引數才呼叫方法，`loadDefault()` 一定會先跑、印出「查預設值」；Optional 有值，所以 `orElse` 回傳「信義分行」。換成 `orElseGet(() -> loadDefault())` 就不會查。

</details>

**🧩 小練習：** 下面哪一種 Optional 用法是**不建議**的？

- (A) 查詢方法回傳 `Optional<Account>`
- (B) 對回傳的 Optional 呼叫 `map` 再 `orElse`
- (C) 欄位宣告成 `Optional<String>`
- (D) 查不到時回傳 `Optional.empty()`

<details><summary>看答案</summary>

**答案：(C)** 不要把 Optional 用在欄位、方法參數、集合與 Map 裡。它設計來當回傳型別，其餘三個都是正常用法。

</details>

**🧩 小練習：** 一個回傳 `Optional<String>` 的查詢方法，查不到時應該回傳什麼？

- (A) null
- (B) Optional.empty()
- (C) Optional.of(null)
- (D) Optional.ofNullable("")

<details><summary>看答案</summary>

**答案：(B)** 回傳型別是 Optional，就用空的 Optional 表達「沒有結果」；回傳 null 違反「Optional 變數永遠不該是 null」。`Optional.of(null)` 會丟例外；`ofNullable("")` 是「有值，值是空字串」，意思不同。

</details>

**🧩 小練習：** `Optional.of("A001").map(id -> OWNERS.get("Z999")).isPresent()` 回傳什麼？

- (A) true，因為原本的 Optional 有值
- (B) 丟出 NullPointerException
- (C) 編譯錯誤
- (D) false

<details><summary>看答案</summary>

**答案：(D)** `map` 的函式回傳 null（查不到 Z999）時，`map` 回傳空的 Optional，所以 `isPresent()` 是 false。

</details>

**🧩 小練習：** 要判斷一個 Optional 是不是空的，該用哪個寫法？

- (A) opt == Optional.empty()
- (B) opt == null
- (C) opt.isEmpty()
- (D) opt.get() == null

<details><summary>看答案</summary>

**答案：(C)** `Optional.empty()` 不保證每次都是同一個物件，不要用 `==` 比；Optional 變數本身不該是 null；對空的 Optional 呼叫 `get()` 會丟 `NoSuchElementException`。`isEmpty()` 是 Java 11 起的方法。

</details>

### 重點整理

- lambda 是只留參數與本體的匿名方法，用來把一段行為當參數傳；寫下它不會執行，被呼叫時才執行。
- lambda 一定要有目標型別，而且必須是函式介面（只有一個抽象方法；default、static 與覆寫 `Object` 公開方法的不算）。`@FunctionalInterface` 只是請編譯器幫忙檢查。
- `java.util.function` 用「收什麼、回什麼」挑：`Function`、`Predicate`、`Consumer`、`Supplier`、`BiFunction`、`UnaryOperator`、`BinaryOperator`；處理 int、long、double 時用 `IntPredicate`、`ToLongFunction` 這類版本省掉裝箱。
- 方法參考四種：靜態方法、特定物件的實例方法、某型別任意物件的實例方法（第一個參數當呼叫者）、建構子。
- lambda 只能讀 final 或 effectively final 的區域變數，不能在裡面改它們；lambda 裡的 `this` 跟外面一樣，匿名類別裡的 `this` 指自己。
- `comparing`＋`thenComparing` 寫多鍵排序；`reversed()` 反轉的是它前面的整串比較器。
- `Optional` 當回傳型別表達「沒有結果」：查不到回傳 `Optional.empty()`，用 `map`、`orElse`、`orElseThrow` 取值；預設值很貴用 `orElseGet`；不要用在欄位與參數。

---

## 隨堂測驗

**Q1. 寫下 Runnable r = () -&gt; System.out.println("入帳"); 之後，「入帳」什麼時候會印出來？**

- (A) 這個類別被 JVM 載入的時候
- (B) main 方法結束前統一執行一次
- (C) 寫下這行、建立 r 的當下
- (D) 呼叫 r.run() 的時候

<details><summary>看答案</summary>

**答案：(D)** 對 lambda 求值只產生一個函式介面的實例，不會執行本體；本體要等那個抽象方法（這裡是 run）被呼叫時才執行。

</details>

**Q2. interface Audit { void log(String m); default void flush() { } static Audit noop() { return m -&gt; { }; } } 能不能當 lambda 的目標型別？**

- (A) 不行，有 static 方法就不是函式介面
- (B) 只有加上 @FunctionalInterface 才可以
- (C) 可以，抽象方法只有 log 一個
- (D) 不行，有 default 方法就不是函式介面

<details><summary>看答案</summary>

**答案：(C)** 函式介面只看抽象方法的數量；default 與 static 方法都有實作，不算進去。@FunctionalInterface 只是請編譯器檢查，沒加也一樣是函式介面。

</details>

**Q3. 要寫「輸入一筆交易物件、回傳手續費 long」的函式，而且想避免把 long 裝箱成 Long，選哪個介面？**

- (A) Supplier&lt;Long&gt;
- (B) ToLongFunction&lt;Tx&gt;
- (C) Function&lt;Tx, Long&gt;
- (D) LongFunction&lt;Tx&gt;

<details><summary>看答案</summary>

**答案：(B)** ToXxx 前綴表示回傳基本型別：ToLongFunction 收一個物件、回傳 long。Function&lt;Tx, Long&gt; 會裝箱；LongFunction 是反過來「收 long、回傳物件」；Supplier 不收參數。

</details>

**Q4. Function&lt;String, Integer&gt; len = String::length; 這個方法參考屬於哪一種、等於哪個 lambda？**

- (A) 建構子參考，等於 s -&gt; new String(s)
- (B) 特定物件的實例方法，等於 s -&gt; "".length()
- (C) 某型別任意物件的實例方法，等於 s -&gt; s.length()
- (D) String 的靜態方法，等於 s -&gt; String.length(s)

<details><summary>看答案</summary>

**答案：(C)** length 是實例方法；「型別::實例方法」拿第一個參數當呼叫者，所以是 s.length()。String 沒有叫 length 的靜態方法。

</details>

**Q5. int count = 0; ids.forEach(id -&gt; count++); 這段放在方法裡，會怎樣？**

- (A) 可以編譯，但執行時丟出 ConcurrentModificationException
- (B) 可以編譯，跑完 count 等於 ids 的筆數
- (C) 編譯錯誤，count 是被修改的區域變數，lambda 不能捕獲
- (D) 可以編譯，但 count 永遠是 0

<details><summary>看答案</summary>

**答案：(C)** lambda 用到的外部區域變數必須是 final 或 effectively final；count++ 讓它不是，javac 直接報錯。要計數就用迴圈，或讓計數成為回傳值，例如 Stream 的 count()。

</details>

**Q6. 在一個實例方法裡寫 Runnable r = () -&gt; System.out.println(this);，this 指的是什麼？**

- (A) null，lambda 裡沒有 this
- (B) Runnable 介面本身
- (C) 外圍類別、正在執行這個方法的那個物件
- (D) lambda 自己產生的那個 Runnable 物件

<details><summary>看答案</summary>

**答案：(C)** lambda 本體裡 this 的意義跟周圍程式碼相同。匿名類別才會有自己的 this。

</details>

**Q7. 交易 Tx 有 branch（分行代碼）與 amount（金額）兩個欄位，要依分行代碼由小到大排，同一家分行再依金額由大到小。哪個比較器正確？**

- (A) comparing(Tx::branch, Comparator.reverseOrder()) .thenComparing(Tx::amount)
- (B) comparing(Tx::branch) .thenComparing(Tx::amount) .reversed()
- (C) comparing(Tx::branch) .thenComparing(Tx::amount, Comparator.reverseOrder())
- (D) comparing(Tx::amount, Comparator.reverseOrder()) .thenComparing(Tx::branch)

<details><summary>看答案</summary>

**答案：(C)** 只有金額這個鍵要反序，所以把 reverseOrder() 交給 thenComparing 的第二個參數。接在整串後面的 reversed() 會把分行也一起反過來；把 reverseOrder() 放在 comparing(Tx::branch, …) 反的是分行、金額反而由小到大；以金額當第一個鍵則主次顛倒。

</details>

**Q8. Optional 有值時，orElse(loadDefault()) 與 orElseGet(() -&gt; loadDefault()) 差在哪？**

- (A) 兩者都不會執行 loadDefault()
- (B) 兩者都會執行 loadDefault() 一次
- (C) 前者照樣執行 loadDefault()，後者不會
- (D) 前者不會執行 loadDefault()，後者一定會

<details><summary>看答案</summary>

**答案：(C)** Java 呼叫方法前會先算出引數，所以 orElse 的引數一定被算一次；orElseGet 收的是 Supplier，只在 Optional 是空的時候才呼叫。預設值很貴時用 orElseGet。

</details>

**Q9. Optional 最適合用在哪裡？**

- (A) 實體類別的欄位型別
- (B) Map 的值的型別
- (C) 方法的回傳型別
- (D) 方法的參數型別

<details><summary>看答案</summary>

**答案：(C)** Optional 主要設計來當方法回傳型別，用在需要表達「沒有結果」的地方；不要用在欄位、方法參數、集合與 Map 裡。

</details>

**Q10. Optional.of("A001").map(id -&gt; lookup(id))，如果 lookup 回傳 null，結果是什麼？**

- (A) 裝著 "A001" 的 Optional
- (B) 裝著 null 的 Optional
- (C) 空的 Optional
- (D) 丟出 NullPointerException

<details><summary>看答案</summary>

**答案：(C)** map 的函式回傳 null 時，map 回傳空的 Optional。Optional 不會裝著 null。

</details>
