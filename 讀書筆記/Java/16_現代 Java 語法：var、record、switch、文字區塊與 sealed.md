# 16. 現代 Java 語法：var、record、switch、文字區塊與 sealed

> 來源：[筆記平台 · Java](https://hhtim.github.io/notes-platform/java/#/lesson/java-modern-syntax)　第 16 課 / 共 18 課 · 約 60 分鐘

**Java 10 到 21 的新語法一次走完：var 的界線、用 record 寫不可變的資料、switch 運算式與模式比對、文字區塊的縮排規則，以及用 sealed 讓 switch 不寫 default 也能窮舉。**

### 讀完這課你會

- 判斷哪裡能寫 var、何時不該寫
- 用 record 寫不可變的資料類別
- 用 switch 運算式與模式比對取代轉型
- 寫文字區塊，用 sealed 讓 switch 窮舉

---

*【先看全貌，每個功能哪一版定案】*

## Java 10 到 21 新增的語法，一張表

〈Java 是什麼、環境怎麼裝〉列過幾個分水嶺：Java 10 有 `var`，Java 14〜17 有 switch 運算式、文字區塊、record、sealed，Java 21 有虛擬執行緒與 switch 的模式比對。新語法在 OpenJDK 裡都用 **JEP**（JDK Enhancement Proposal，描述一項新功能的公開提案文件）追蹤，多數先當幾版**預覽功能**（preview，要加 `--enable-preview` 才能用、之後可能再改）才正式定案。各功能的 JEP 與正式版本：

| 功能 | JEP | 正式版本 | 一句話 |
|---|---|---|---|
| **`var` 區域變數型別推論** | [286](https://openjdk.org/jeps/286) | 10 | 區域變數的型別讓編譯器從初始值推論 |
| **switch 運算式與箭頭** | [361](https://openjdk.org/jeps/361) | 14 | switch 可以產生值，箭頭寫法不會穿透 |
| **文字區塊** | [378](https://openjdk.org/jeps/378) | 15 | 三個雙引號包起來的多行字串 |
| **`instanceof` 模式比對** | [394](https://openjdk.org/jeps/394) | 16 | 檢查型別的同時宣告好變數，不必再轉型 |
| **record** | [395](https://openjdk.org/jeps/395) | 16 | 一行宣告不可變的資料類別 |
| **sealed 類別與介面** | [409](https://openjdk.org/jeps/409) | 17 | 限定誰可以繼承或實作 |
| **record 解構模式** | [440](https://openjdk.org/jeps/440) | 21 | 比對 record 的同時把元件拆出來 |
| **switch 模式比對** | [441](https://openjdk.org/jeps/441) | 21 | case 可以寫型別模式、`when` 守衛與 `case null` |
| **虛擬執行緒** | [444](https://openjdk.org/jeps/444) | 21 | 由 JVM 排程的輕量執行緒 |

上表全部在 Java 21 可以直接用；Java 22 之後又加了幾個相關功能。

---

*【型別交給編譯器，名字交給你】*

## var：區域變數型別推論

`var`（JEP 286）把型別推論延伸到有初始值的區域變數宣告。能用的地方只有：

- 有初始值的區域變數
- 增強型 for 的迴圈變數
- 傳統 for 迴圈裡宣告的區域變數 [[出處]](https://openjdk.org/jeps/286)
- try-with-resources 的資源宣告（它也算區域變數） [[出處]](https://docs.oracle.com/javase/specs/jls/se21/html/jls-14.html#jls-14.4)

方法參數、建構子參數、方法回傳型別、欄位、catch 參數等其他宣告都不能用。 [[出處]](https://openjdk.org/jeps/286)

```java
var amounts = new ArrayList<Long>();         // 推論成 ArrayList<Long>
amounts.add(1_200L);
for (var a : amounts) {                      // 增強型 for 的迴圈變數也可以
    System.out.println(a + 1);               // 1201
}

var n = 10;                                  // int
var big = 10L;                               // long

var var = "var 不是關鍵字";                    // 可以當變數名稱
System.out.println(var);                     // var 不是關鍵字
```

最後那兩行不是筆誤：`var` 不是關鍵字，而是**保留的型別名稱**。所以拿它當變數、方法或套件名稱的舊程式都不受影響，只有把類別取名叫 `var` 的會受影響。 [[出處]](https://openjdk.org/jeps/286)

用 `var` 時，下面這些寫法是編譯錯誤： [[出處]](https://docs.oracle.com/javase/specs/jls/se21/html/jls-14.html#jls-14.4)

- 一次宣告多個變數
- 名稱後面加陣列括號
- 沒有初始值
- 初始值是陣列初始化器（`{ 6 }` 這種）
- 初始值裡引用了自己
- 初始值是 `null`

這些規則有同一個道理：編譯器必須單看右邊就推得出一個明確的型別。

| 寫法 | 結果（javac 21 的訊息） |
|---|---|
| `var count = 0;`（欄位） | `'var' is not allowed here` |
| `var total() { ... }`（回傳型別） | `'var' is not allowed here` |
| `void m(var x)`（方法參數） | `'var' is not allowed here` |
| `var x; x = 1;` | `cannot use 'var' on variable without initializer` |
| `var x = null;` | `variable initializer is 'null'` |
| `var arr = {1, 2, 3};` | `array initializer needs an explicit target-type` |
| `var a = 1, b = 2;` | `'var' is not allowed in a compound declaration` |

**可讀性的取捨。**讀程式碼比寫程式碼重要，所以初始值已經讓讀的人看得出型別時，才考慮用 `var`。兩個陷阱： [[出處]](https://openjdk.org/projects/amber/guides/lvti-style-guide)

- `var` 配菱形 `<>`：推論出的型別會變，例如 `var itemQueue = new PriorityQueue<>();` 會推成 `PriorityQueue<Object>`
- `var` 配不帶 `L` 的整數字面值：推成 `int`，原本寫 `byte`、`long` 時的自動轉換就沒了

```java
var raw = new ArrayList<>();      // 菱形沒有東西可推：ArrayList<Object>
raw.add("A");
raw.add(1);                       // 什麼都放得進去，泛型的保護沒了
System.out.println(raw);          // [A, 1]
```

> 💡 **var 只用在區域變數，而且右邊要一眼看得出型別；var 配菱形會推成 Object**

**🧩 小練習：** 下面哪一行能編譯？

- (A) var x = new HashMap<String, Long>();
- (B) var x; x = new HashMap<String, Long>();
- (C) var x = null; // 之後再指定
- (D) var x = {1, 2, 3};

<details><summary>看答案</summary>

**答案：(A)** 有初始值、而且初始值有明確型別，`var` 才推得出來。沒有初始值、初始值是 null、初始值是陣列初始化器，都是編譯錯誤。

</details>

**🧩 小練習：** 在類別裡寫 `private var balance = 0L;` 會怎樣？

- (A) 編譯錯誤，var 不能用在欄位
- (B) 可以，推論成 long
- (C) 可以，推論成 Long
- (D) 可以，但只在 Java 21 以後

<details><summary>看答案</summary>

**答案：(A)** JEP 286 只開放區域變數；欄位、方法參數、回傳型別都不行，javac 報 `'var' is not allowed here`。

</details>

**🧩 小練習：** `var n = 10;` 之後寫 `n = 10_000_000_000L;` 會怎樣？

- (A) 可以，n 會自動變成 long
- (B) 可以，但數字會被截斷成 int 的範圍
- (C) 執行時丟出例外
- (D) 編譯錯誤

<details><summary>看答案</summary>

**答案：(D)** `var` 在宣告那一刻就把型別定成 `int`，之後不會變。Java 仍是靜態型別語言，`var` 只是少寫型別名稱。

</details>

**🧩 小練習：** 下面哪一個用法是合法的？

- (A) void transfer(var amount) { }
- (B) catch (var e) { }
- (C) try (var in = open(path)) { }
- (D) var amount() { return 0; }

<details><summary>看答案</summary>

**答案：(C)** try-with-resources 的資源是區域變數，可以用 `var`。方法參數、catch 參數、方法回傳型別都在 JEP 286 排除的清單裡。

</details>

**🧩 小練習：** `var var = "TWD";` 會怎樣？

- (A) 編譯錯誤，var 是關鍵字
- (B) 編譯錯誤，變數名稱不能跟型別同名
- (C) 可以，但編譯時會出現警告
- (D) 可以，var 不是關鍵字

<details><summary>看答案</summary>

**答案：(D)** JEP 286 刻意不把 var 做成關鍵字，舊程式裡叫 var 的變數、方法、套件照樣能用；只有取名叫 var 的類別或介面會受影響。

</details>

**🧩 小練習：** 這段程式能編譯嗎？會印出什麼？

- (A) 編譯錯誤，500 不是字串
- (B) 編譯錯誤，菱形不能配 var
- (C) 可以，印出 1
- (D) 可以，印出 2

<details><summary>看答案</summary>

**答案：(D)** 菱形左邊沒有型別可參考，`list` 被推成 `ArrayList<Object>`，字串和整數都放得進去。能編譯，但泛型的型別檢查等於沒了，所以 var 配菱形要避免。

</details>

**🧩 小練習：** 下面哪一行最**不**適合用 var？

- (A) var reader = new BufferedReader(new FileReader(path));
- (B) var accounts = new ArrayList<Account>();
- (C) var result = service.process(request);
- (D) var count = 0L;

<details><summary>看答案</summary>

**答案：(C)** 原則是讀程式碼比寫程式碼重要，初始值提供足夠資訊才用 var。`service.process(...)` 回傳什麼，光看這行看不出來；其餘三行右邊都看得到型別（`0L` 一看就是 long）。

</details>

**🧩 小練習：** `var a = 1, b = 2;` 會怎樣？

- (A) 可以，a、b 都是 int
- (B) 可以，a 是 int、b 是 Object
- (C) 編譯錯誤，var 不能一次宣告多個變數
- (D) 可以，但 b 要另外寫型別

<details><summary>看答案</summary>

**答案：(C)** 用 `var` 時列出超過一個變數是編譯錯誤，javac 報 `'var' is not allowed in a compound declaration`。

</details>

---

*【只裝資料的類別，一行寫完】*

## record：不可變的資料載體

record（Java 16 正式加入，JEP 395）是透明地裝著不可變資料的類別。 [[出處]](https://openjdk.org/jeps/395)

宣告時只寫「元件」（component，也就是組成這筆資料的欄位），編譯器自動產生其餘的東西。自動產生的成員：

- 每個元件一個同名的 public 讀取方法（accessor）與一個 private final 欄位
- 一個參數跟宣告一模一樣的**標準建構子**（canonical constructor）
- 依元件值判斷相等的 `equals` 與 `hashCode`
- 列出所有元件名稱與值的 `toString`。 [[出處]](https://openjdk.org/jeps/395)

讀取方法叫 `amount()`，不是 `getAmount()`。

銀行最常見的例子是「金額＋幣別」。下面在**緊湊建構子**（compact canonical constructor，不寫參數列的標準建構子）裡驗證幣別、統一小數位數：

```java
record Money(BigDecimal amount, String currency) {
    Money {                                          // 緊湊建構子：不寫參數列
        Objects.requireNonNull(amount, "amount");
        if (currency == null || !currency.matches("[A-Z]{3}")) {
            throw new IllegalArgumentException("幣別要是三個大寫字母：" + currency);
        }
        amount = amount.setScale(2);                 // 改的是參數，結尾才自動指定給欄位
                                                     // 超過兩位小數會丟 ArithmeticException
    }

    Money plus(Money other) {
        if (!currency.equals(other.currency)) {
            throw new IllegalArgumentException("幣別不同不能相加");
        }
        return new Money(amount.add(other.amount), currency);   // 不改自己，回傳新的
    }

    static Money twd(long value) {                   // 可以有靜態方法
        return new Money(BigDecimal.valueOf(value), "TWD");
    }
}

Money a = new Money(new BigDecimal("100"), "TWD");
Money b = Money.twd(100);
System.out.println(a);                     // Money[amount=100.00, currency=TWD]
System.out.println(a.amount() + " " + a.currency());   // 100.00 TWD
System.out.println(a.equals(b) + " " + (a == b) + " " + (a.hashCode() == b.hashCode()));
// true false true
System.out.println(a.plus(b));             // Money[amount=200.00, currency=TWD]
System.out.println(a);                     // Money[amount=100.00, currency=TWD]，a 沒變
new Money(BigDecimal.ONE, "twd");          // 丟出 IllegalArgumentException：幣別要是三個大寫字母：twd
new Money(new BigDecimal("1.234"), "TWD"); // 丟出 ArithmeticException：Rounding necessary
```

最後一行要注意：`setScale(2)` 沒指定捨入方式，只能補零、不能捨掉位數；需要捨入時就丟 `ArithmeticException`。 [[出處]](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/math/BigDecimal.html#setScale(int)) 真的要收超過兩位的金額，就改用指定捨入方式的 `setScale(2, RoundingMode.HALF_EVEN)` 這類寫法，用哪一種捨入依業務規則決定。

緊湊建構子的規則：

- 參數是隱含宣告的
- 對應元件的 private 欄位不能在本體裡指定，會在建構子結尾自動指定成對應的參數（`this.x = x;`）
- 本體專心做參數的驗證與正規化 [[出處]](https://openjdk.org/jeps/395)

所以上面改的是參數 `amount`；寫 `this.amount = ...` 反而會編譯錯誤（`cannot assign a value to final variable amount`）。

**限制。**record 類別有這些限制： [[出處]](https://openjdk.org/jeps/395)

- 沒有 `extends`：父類別一律是 `java.lang.Record`，連明確寫出 `Record` 都不行。可以實作介面。
- 隱含是 `final`、不能是 `abstract`，所以沒有人能繼承 record。
- 元件對應的欄位都是 `final`，而且不能自己再宣告實體欄位、不能有實體初始化區塊；`static` 欄位與方法可以。

**不可變只到第一層。**record 是**淺層不可變**（shallowly immutable）的。 [[出處]](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Record.html) 欄位本身不能換，但欄位指向的物件如果可以改（例如 `ArrayList`），裡面照樣改得動。要整份都不可變，就在緊湊建構子裡做**防禦性複製**（defensive copy，存一份自己的副本，不跟外面共用）：

```java
record Statement(String accountId, List<String> txIds) {
    Statement {
        txIds = List.copyOf(txIds);                  // 防禦性複製：外面再改原清單也影響不到
    }
}

List<String> ids = new ArrayList<>(List.of("T1", "T2"));
Statement st = new Statement("A001", ids);
ids.add("T3");
System.out.println(st.txIds());   // [T1, T2]
st.txIds().add("T4");             // 丟出 UnsupportedOperationException
```

> record 自動產生的 `equals`、`hashCode` 依元件值比較，所以很適合當 `HashMap` 的鍵或放進 `HashSet`；這兩個方法的約定見〈套件與 Object 類別〉。〈Lambda 與函式介面〉〈Stream API：把迴圈寫成資料流〉的交易資料也都是 record。

> 💡 **record 自動有讀取方法、標準建構子、equals、hashCode、toString；驗證寫在緊湊建構子；不能繼承類別，不可變只到第一層**

**🧩 小練習：** `record Money(BigDecimal amount, String currency) {}`，要取金額該怎麼寫？

- (A) money.getAmount()
- (B) money.amount
- (C) money.amount()
- (D) money.get("amount")

<details><summary>看答案</summary>

**答案：(C)** record 為每個元件產生一個跟元件同名的 public 讀取方法，沒有 get 前綴。欄位本身是 private，從外面不能直接 `money.amount`。

</details>

**🧩 小練習：** 這段程式印出什麼？

- (A) false false
- (B) true true
- (C) false true
- (D) true false

<details><summary>看答案</summary>

**答案：(D)** 自動產生的 `equals` 比的是元件值，兩筆都是 USD、32.5，所以相等；`==` 比的是不是同一個物件，兩個 `new` 出來的不是。

</details>

**🧩 小練習：** 這段程式印出什麼？

- (A) Rate[currency=JPY, value=0.21]
- (B) Rate@1b6d3586 這類雜湊值
- (C) JPY 0.21
- (D) {currency: JPY, value: 0.21}（JSON 格式）

<details><summary>看答案</summary>

**答案：(A)** record 自動產生的 `toString` 列出類別名稱、每個元件的名稱與值。只有一般類別沒覆寫 `toString` 時，才會印出類別名稱加雜湊值。

</details>

**🧩 小練習：** `record Money(BigDecimal amount, String currency) { Money { this.amount = amount.setScale(2); } }` 會怎樣？

- (A) 可以，欄位被設成兩位小數
- (B) 可以，但結尾會被原本的 amount 蓋回去
- (C) 執行時丟出例外
- (D) 編譯錯誤，緊湊建構子裡不能指定欄位

<details><summary>看答案</summary>

**答案：(D)** 緊湊建構子裡欄位不能指定，結尾才自動用參數指定欄位；javac 報 `cannot assign a value to final variable amount`。要正規化就改參數：`amount = amount.setScale(2);`。

</details>

**🧩 小練習：** 上面的 `Money`，`new Money(new BigDecimal("100"), "TWD").amount()` 回傳什麼？

- (A) 100
- (B) 100.00
- (C) 100.0
- (D) 丟出 IllegalArgumentException

<details><summary>看答案</summary>

**答案：(B)** 緊湊建構子把參數改成 `setScale(2)` 的結果，結尾自動指定給欄位，所以存進去的是兩位小數的 100.00。幣別 TWD 符合三個大寫字母，不會丟例外。

</details>

**🧩 小練習：** `record SavingsAccount(String id) extends Account {}` 會怎樣？

- (A) 可以，record 也能繼承一般類別
- (B) 可以，但 Account 要是抽象類別
- (C) 編譯錯誤
- (D) 可以，但只能繼承另一個 record，不能繼承一般類別

<details><summary>看答案</summary>

**答案：(C)** record 的父類別一律是 `java.lang.Record`，宣告不能有 `extends`。要共用行為可以實作介面：`record SavingsAccount(String id) implements Account {}`（Account 是介面時）。

</details>

**🧩 小練習：** `class VipMoney extends Money { ... }`（Money 是 record）會怎樣？

- (A) 可以，只要呼叫 super(...)
- (B) 可以，但 VipMoney 也要宣告成 record 才行
- (C) 可以，但不能覆寫 equals
- (D) 編譯錯誤，record 不能被繼承

<details><summary>看答案</summary>

**答案：(D)** record 隱含是 final，而且不能是 abstract，javac 報 `cannot inherit from final Money`。

</details>

**🧩 小練習：** 下面哪一個可以寫在 record 的大括號裡？

- (A) private int retryCount = 0;
- (B) { System.out.println("初始化完成"); }
- (C) static final String CUR = "TWD";
- (D) native void sign();

<details><summary>看答案</summary>

**答案：(C)** record 不能自己宣告實體欄位（javac 報 `field declaration must be static`）、不能有實體初始化區塊、不能有 native 方法；static 欄位、static 方法、實體方法都可以。

</details>

**🧩 小練習：** 這段程式印出什麼？

- (A) [T1]
- (B) [T1, T2]
- (C) 丟出 UnsupportedOperationException
- (D) 編譯錯誤，record 的元件不能是清單

<details><summary>看答案</summary>

**答案：(B)** record 只是淺層不可變：欄位一直指向同一個 `src` 清單，外面加了 T2，從 `b.ids()` 也看得到。要避免就在緊湊建構子裡寫 `ids = List.copyOf(ids);`。

</details>

**🧩 小練習：** 上面的 `Money` 呼叫 `a.plus(b)` 之後，`a` 本身會變嗎？

- (A) 會，a 的金額變成相加之後的結果
- (B) 會，但只有 a.amount() 變，toString 不變
- (C) 不會，plus 回傳新的 Money
- (D) 不會，因為 plus 會丟出例外

<details><summary>看答案</summary>

**答案：(C)** record 的欄位是 final，方法沒辦法改它；`plus` 用相加結果 new 一個新的 Money 回傳。實跑時 `a` 印出來還是 100.00。

</details>

---

*【switch 也能算出一個值】*

## switch 運算式、箭頭與 yield

JEP 361（Java 14）讓 switch 可以「當敘述也可以當運算式用」，兩種都能用傳統的 `case ... :`（會穿透）或新的 `case ... ->`（不會穿透），另外新增 `yield` 敘述讓 switch 運算式交出值。 [[出處]](https://openjdk.org/jeps/361) **穿透**（fall through）是舊寫法常見的錯：某個 case 沒寫 `break`，就會一路執行到下一個 case。

```java
enum Channel { BRANCH, ATM, MOBILE, INTERNET }

static int oldFee(Channel ch) {
    int fee = 0;
    switch (ch) {
        case BRANCH:
            fee = 30;
        case ATM:                    // 忘了 break：會一路穿透下去
            fee = 15;
            break;
        default:
            fee = 10;
    }
    return fee;
}
// oldFee(BRANCH) 回傳 15，不是 30（javac -Xlint 會警告 possible fall-through into case）

static int feeOf(Channel ch) {
    return switch (ch) {
        case BRANCH -> 30;
        case ATM, INTERNET -> 15;    // 多個常數用逗號
        case MOBILE -> {
            int base = 15;
            yield base - 5;          // 區塊裡用 yield 交出值
        }
    };
}
// BRANCH=30 ATM=15 MOBILE=10 INTERNET=15
```

switch 運算式（JEP 361）的規則： [[出處]](https://openjdk.org/jeps/361)

- 箭頭右邊只執行那個運算式或敘述，不會穿透（fall through）
- 右邊需要一整個區塊時，用 `yield` 交出值
- 必須窮舉：每一個可能的值都要有對應的 case
- enum 的每個常數都列出來時可以不寫 `default`，而且這樣更好：之後 enum 多了常數，重新編譯時編譯器就會指出漏掉的地方

漏掉一個常數，javac 報 `the switch expression does not cover all possible input values`；箭頭右邊的區塊沒有 `yield`，報 `switch rule completes without providing a value`。

> `yield` 跟 `var` 一樣不是關鍵字，而是**受限的識別字**（restricted identifier）。`break` 只能跳出 switch 敘述，`yield` 只能用在 switch 運算式。 [[出處]](https://openjdk.org/jeps/361)

**🧩 小練習：** 上面的 `oldFee(Channel.BRANCH)` 回傳什麼？

- (A) 30
- (B) 15
- (C) 10
- (D) 0

<details><summary>看答案</summary>

**答案：(B)** `case BRANCH:` 設成 30 之後沒有 `break`，穿透到 `case ATM:` 又設成 15，遇到 `break` 才離開。這正是箭頭寫法要消滅的錯。

</details>

**🧩 小練習：** 這段程式印出什麼？

- (A) 優先急件未知
- (B) 一般
- (C) 優先
- (D) 未知

<details><summary>看答案</summary>

**答案：(C)** 箭頭寫法只執行符合的那一個 case 右邊，不會穿透，所以只得到「優先」。

</details>

**🧩 小練習：** `enum Channel { BRANCH, ATM, MOBILE }`，下面這段會怎樣？

- (A) 可以，MOBILE 時 fee 是 0
- (B) 可以，MOBILE 時丟出例外
- (C) 可以，MOBILE 時 fee 是 15
- (D) 編譯錯誤，沒有窮舉，漏了 MOBILE

<details><summary>看答案</summary>

**答案：(D)** switch 運算式一定要窮舉：每個可能的值都要有 case。漏一個 enum 常數，javac 報 `the switch expression does not cover all possible input values`。補上 `case MOBILE` 或 `default` 都能解決。

</details>

**🧩 小練習：** switch 運算式的箭頭右邊是一個大括號區塊時，要怎麼交出值？

- (A) return 值;
- (B) break 值;
- (C) yield 值;
- (D) 區塊最後一行的運算式自動成為值

<details><summary>看答案</summary>

**答案：(C)** JEP 361 新增 `yield` 給 switch 運算式交出值。`return` 會直接離開整個方法；Java 12 第一次預覽時用 `break 值`，Java 13 第二次預覽就改成 yield。

</details>

**🧩 小練習：** 這段程式印出什麼？

- (A) 週五提早下班 0
- (B) 0
- (C) 8
- (D) 週五提早下班 6

<details><summary>看答案</summary>

**答案：(B)** SAT 對到第一個 case（逗號列出多個常數），得到 0；箭頭不會穿透到 FRI 那個區塊，所以那句不會印出。

</details>

**🧩 小練習：** 下面這段會怎樣？

- (A) 可以，BRANCH 時 fee 是 0
- (B) 可以，BRANCH 時 fee 是 15
- (C) 可以，但 BRANCH 時丟出例外
- (D) 編譯錯誤，BRANCH 的區塊沒有交出值

<details><summary>看答案</summary>

**答案：(D)** switch 運算式的每個分支都要交出值或丟出例外。區塊裡只有印字、沒有 `yield`，javac 報 `switch rule completes without providing a value`。

</details>

**🧩 小練習：** enum 的每個常數都已經寫進 switch 運算式了，為什麼不寫 `default` 反而比較好？

- (A) 寫 default 會讓程式跑得比較慢
- (B) enum 新增常數時，編譯器會指出漏掉的 case
- (C) 寫了 default 就會編譯錯誤
- (D) 不寫 default 的話，新常數會自動對到第一個 case

<details><summary>看答案</summary>

**答案：(B)** 沒有 default，編譯器每次都檢查是否窮舉；自己加了 default，新常數會默默落進 default，錯誤就被藏起來了。寫 default 本身不會編譯錯誤。

</details>

---

*【檢查型別、取出內容，一步做完】*

## 模式比對：instanceof、switch 型別模式與 record 解構

**模式比對**（pattern matching）是「檢查一個值的形狀，符合就順便把需要的部分取出來」。以前判斷型別要寫三步：`instanceof` 檢查、轉型、宣告變數；JEP 394（Java 16）合成一步。 [[出處]](https://openjdk.org/jeps/394)

```java
Object obj = "A001";
if (obj instanceof String s && s.length() == 4) {   // 比對成功才有 s，&& 右邊就能用
    System.out.println("帳號 " + s.toLowerCase());     // 帳號 a001
}

Object other = 42;
if (!(other instanceof String t)) {
    System.out.println("不是字串");                  // 不是字串
} else {
    System.out.println(t.length());                 // 這裡 t 一定比對成功了
}
```

`s` 叫**模式變數**（pattern variable）。它的範圍不是整個區塊，而是「流程範圍」：**模式變數只在一定比對成功的地方有效**。 [[出處]](https://openjdk.org/jeps/394) 所以 `&&` 右邊能用 `s`（左邊成立才會跑右邊），`||` 右邊就不行（左邊不成立才會跑右邊，那時 `s` 沒有值），javac 報 `cannot find symbol`。

**switch 的型別模式與 when 守衛（Java 21，JEP 441）。**case 可以寫型別模式，後面加 `when 條件` 叫**守衛**（guard，型別符合之外再加的條件）；也可以寫 `case null`。 [[出處]](https://openjdk.org/jeps/441)

```java
static String describe(Object o) {
    return switch (o) {
        case null -> "沒有資料";
        case Integer i when i > 1_000_000 -> "大額整數 " + i;
        case Integer i -> "整數 " + i;
        case String s -> "字串，長度 " + s.length();
        default -> "其他：" + o;
    };
}
describe(null);          // 沒有資料
describe(5_000_000);     // 大額整數 5000000
describe(7);             // 整數 7
describe("TWD");         // 字串，長度 3
describe(3.5);           // 其他：3.5
```

switch 模式比對（JEP 441）有四條規則要記： [[出處]](https://openjdk.org/jeps/441)

- **由上往下，第一個符合的生效。**寬的放在窄的前面，窄的就永遠輪不到，這叫「被支配」（dominated），是編譯錯誤：`case CharSequence cs` 放在 `case String s` 前面，javac 報 `this case label is dominated by a preceding case label`。同一個型別，沒有守衛的也會支配有守衛的，所以 `case Integer i when ...` 要放在 `case Integer i` 前面。
- **null 只看 case null。**有 `case null` 就執行它；沒有就跟以前一樣丟 `NullPointerException`。而且為了相容，`default` 不會比對到 null。
- **模式 switch 一定要窮舉**，連 switch 敘述也一樣：只要用了模式或 `null` 標籤，或選擇的值不是傳統型別（char、byte、short、int 與它們的包裝類別、String、enum），編譯器就檢查窮舉。對 `Object` 只列 `String` 和 `Integer` 兩種，javac 報 `does not cover all possible input values`。
- 不會穿透的箭頭寫法照舊。

**record 解構模式（Java 21，JEP 440）。**比對 record 時可以直接把元件拆出來： [[出處]](https://openjdk.org/jeps/440)

- record 模式與型別模式可以一層套一層，寫成宣告式、可組合的資料走訪與處理
- 元件的型別可以寫 `var`
- null 不會比對到 record 模式 [[出處]](https://docs.oracle.com/javase/specs/jls/se21/html/jls-14.html#jls-14.30.2)

下面用到的 `Payment`、`Transfer` 定義在下一段。

```java
Payment p = new Transfer("B002", Money.twd(5_000));
if (p instanceof Transfer(String to, Money(var amt, var cur))) {   // 兩層解構
    System.out.println(to + " " + amt + " " + cur);                  // B002 5000.00 TWD
}
```

record 模式在 switch 裡最好用，下一段配 sealed 一起看。

> **Java 22 起的差異：**用不到的元件可以寫 `_`（無名模式，JEP 456，Java 22 正式；Java 21 是預覽，直接編譯報 `unnamed variables are a preview feature and are disabled by default`）。 [[出處]](https://openjdk.org/jeps/456) 另外，讓 `int` 這類基本型別也能出現在模式裡的 JEP 507，在 Java 25 仍是第三次預覽，還沒定案。 [[出處]](https://openjdk.org/jeps/507) 以 Java 25 執行：

```java
// Java 22 起（以 Java 25 執行）
static String installments(Object o) {
    return switch (o) {
        case CardPayment(_, _, int n) when n > 1 -> "分 " + n + " 期";   // 只要期數
        case CardPayment _ -> "一次付清";
        default -> "不是刷卡";
    };
}
// installments(new CardPayment("4111", ..., 3)) → 分 3 期
// installments(new CardPayment("4111", ..., 1)) → 一次付清
```

**🧩 小練習：** 這段能編譯嗎？

- (A) 可以，印出 ok
- (B) 編譯錯誤，|| 右邊 s 不在範圍內
- (C) 可以，但 o 不是字串時丟出 NullPointerException
- (D) 可以，但什麼都不印

<details><summary>看答案</summary>

**答案：(B)** || 右邊只有在左邊不成立時才執行，那時 s 沒有值，所以 s 在那裡不在範圍內，javac 報 `cannot find symbol`。換成 && 就可以。

</details>

**🧩 小練習：** 這段印出什麼？

- (A) no
- (B) 421
- (C) 43
- (D) 編譯錯誤，i 要先轉型

<details><summary>看答案</summary>

**答案：(C)** o 是 Integer，比對成功，i 就是 42、型別已經是 Integer；42 > 40 成立，印出 42+1 = 43。不必再寫 `(Integer) o`。

</details>

**🧩 小練習：** 用上面的 `describe`，`describe(2_000_000)` 回傳什麼？

- (A) 大額整數 2000000
- (B) 整數 2000000
- (C) 其他：2000000
- (D) 編譯錯誤，兩個 case 都是 Integer

<details><summary>看答案</summary>

**答案：(A)** 由上往下找第一個符合的：`case Integer i when i > 1_000_000` 型別符合、守衛也成立，就停在這裡。有守衛的寫在沒守衛的前面是合法的。

</details>

**🧩 小練習：** 把 `describe` 裡的 `case Integer i -> ...` 移到 `case Integer i when i > 1_000_000 -> ...` 的前面，會怎樣？

- (A) 可以，大額整數那行從此不會被選到
- (B) 編譯錯誤
- (C) 可以，大額時兩個 case 都會依序執行
- (D) 可以，大額時會丟出例外

<details><summary>看答案</summary>

**答案：(B)** 沒有守衛的 `case Integer i` 涵蓋所有 Integer，後面同型別加守衛的 case 永遠輪不到。JEP 441 把這種「被支配」的 case 當成編譯錯誤，跟寫了執行不到的程式碼一樣。

</details>

**🧩 小練習：** 這段能編譯嗎？

- (A) 可以，字串會回傳「字串」
- (B) 可以，字串會回傳「文字」
- (C) 編譯錯誤，String 那個 case 被支配
- (D) 編譯錯誤，用了型別模式就一定要寫 case null

<details><summary>看答案</summary>

**答案：(C)** String 是 CharSequence 的子型別，前面那個 case 已經接走所有字串，`case String s` 永遠輪不到。javac 報 `this case label is dominated by a preceding case label`。窄的要放前面。

</details>

**🧩 小練習：** 這段程式執行 `label(null)` 會怎樣？

- (A) 丟出 NullPointerException
- (B) 回傳「其他」，null 會落進 default
- (C) 回傳「字串」
- (D) 編譯錯誤，少了 case null

<details><summary>看答案</summary>

**答案：(A)** 沒有 `case null` 時，switch 遇到 null 跟以前一樣丟 `NullPointerException`；`default` 不會比對到 null。要處理 null 就加 `case null`。

</details>

**🧩 小練習：** 這段能編譯嗎？

- (A) 可以，其他型別回傳 0
- (B) 可以，其他型別丟出 MatchException
- (C) 編譯錯誤，沒有窮舉 Object 的所有可能
- (D) 可以，其他型別回傳 null

<details><summary>看答案</summary>

**答案：(C)** 選擇的值型別是 Object，只列 String 和 Integer 涵蓋不完。javac 報 `the switch expression does not cover all possible input values`；加 `default` 才窮舉。

</details>

**🧩 小練習：** 這段 switch **敘述**（不是運算式）能編譯嗎？

- (A) 可以，switch 敘述本來就不必窮舉
- (B) 可以，但 o 不是字串時，執行到這裡會丟出例外
- (C) 編譯錯誤，switch 敘述不能用箭頭
- (D) 編譯錯誤，沒有窮舉

<details><summary>看答案</summary>

**答案：(D)** 傳統的 switch 敘述不必窮舉；但 JEP 441 規定只要用了模式或 null 標籤，敘述也要窮舉。javac 報 `the switch statement does not cover all possible input values`，加 `default -> {}` 即可。

</details>

**🧩 小練習：** `record Point(int x, int y) {}`，這段印出什麼？

- (A) 34
- (B) 12
- (C) 7
- (D) 編譯錯誤，要寫 Point p 才能取元件

<details><summary>看答案</summary>

**答案：(B)** record 模式比對成功時，會呼叫讀取方法把元件拆進 x、y，所以印出 3×4 = 12。不必先宣告 `Point p` 再呼叫 `p.x()`。

</details>

**🧩 小練習：** `Object o = null;`，`o instanceof Point(int x, int y)` 的結果是什麼？

- (A) true，x 和 y 都是 0
- (B) 丟出 NullPointerException
- (C) 編譯錯誤
- (D) false

<details><summary>看答案</summary>

**答案：(D)** null 不會比對到 record 模式。`instanceof` 對 null 一律是 false，不會丟例外。

</details>

**🧩 小練習：** Java 22 起，`case CardPayment(_, _, int n) when n > 1 -> ...` 裡的 `_` 是什麼意思？

- (A) 這兩個元件必須是 null
- (B) 這兩個元件會被設成預設值
- (C) 代表後面可以接任意數量的元件
- (D) 那兩格什麼值都符合、也不取名字

<details><summary>看答案</summary>

**答案：(D)** `_` 是無名模式（JEP 456，Java 22 正式）：那個位置什麼值都符合、也不宣告變數。一個 `_` 只對一個元件，CardPayment 有三個元件就要寫三格。

</details>

---

*【多行字串不再滿是跳脫字元】*

## 文字區塊：三個雙引號與縮排規則

文字區塊（Java 15，JEP 378）是多行字串字面值：免去大部分跳脫字元，以可預期的方式自動排版字串，需要時也讓開發者控制格式。 [[出處]](https://openjdk.org/jeps/378) 寫 JSON、SQL、HTML 範本時最有感：

```java
String json = """
        {
          "account": "A001",
          "amount": 1200
        }
        """;
System.out.print(json);
// {
//   "account": "A001",
//   "amount": 1200
// }
System.out.println(json.length() + " " + json.endsWith("\n"));   // 42 true
```

四條規則： [[出處]](https://openjdk.org/jeps/378)

- **開頭的 `"""` 後面必須換行。**開頭分隔符是「三個雙引號，接零個以上空白，再接一個換行」，內容從那個換行之後才開始。所以 `"""TWD"""` 寫在同一行是編譯錯誤（`illegal text block open delimiter sequence, missing line terminator`）。
- **共同的縮排會被拿掉。**為了配合 Java 原始碼縮排而多出來的空白叫「附帶空白」（incidental white space），編譯器會移除：把每一行（空白行不算）開頭的空白數取最小值，每行都去掉這麼多。**結尾 `"""` 自己獨占一行時，它的位置也算一行**，所以把結尾 `"""` 往左移，內容就整體往右多留空白。
- **每行行尾的空白會被刪掉。**行尾空白多半是無意的；真的要留就用新的跳脫字元 `\s`（一個空格）。
- **結尾 `"""` 放在最後一行內容後面，字串就不以換行結尾；**想把很長的一行拆成好幾行寫、但字串裡不要換行，就在行尾加 `\`（`\<換行>` 跳脫，取消這個換行）。

```java
String noNewline = """
        TWD""";
System.out.println("[" + noNewline + "]");   // [TWD]

String shifted = """
          兩格縮排
        """;                                 // 結尾 """ 比內容少兩格
// shifted 是 "  兩格縮排\n"

String oneLine = """
        第一段，\
        接在同一行
        """;
System.out.print(oneLine);                   // 第一段，接在同一行

String keep = """
        結尾留兩格\s\s
        """;
// keep 是 "結尾留兩格  \n"

String sql = """
        SELECT * FROM tx WHERE account = '%s' AND amount > %d
        """.formatted("A001", 1000);
System.out.print(sql);   // SELECT * FROM tx WHERE account = 'A001' AND amount > 1000
```

> 文字區塊不支援在字串裡直接插入變數，JEP 378 建議用新的 `String::formatted`（上面最後一段）。 [[出處]](https://openjdk.org/jeps/378) 但 SQL 用字串拼接或 `formatted` 填使用者輸入，有 SQL 注入（攻擊者把一段 SQL 混進輸入裡讓資料庫執行）的風險；實務上請用 `PreparedStatement` 的參數，這裡只示範字串格式。

**🧩 小練習：** 這段程式印出什麼？

- (A) 2
- (B) 4
- (C) 3
- (D) 20

<details><summary>看答案</summary>

**答案：(B)** 共同縮排被拿掉後，內容是 A、換行、B、換行，共 4 個字元。結尾 `"""` 自己一行，所以最後有換行。

</details>

**🧩 小練習：** 同上，但結尾寫成 `B""";`（跟 B 同一行），`s.length()` 是多少？

- (A) 4
- (B) 3
- (C) 2
- (D) 編譯錯誤

<details><summary>看答案</summary>

**答案：(B)** 結尾分隔符緊接在最後一行內容後面，字串就不以換行結尾：A、換行、B，共 3 個字元。

</details>

**🧩 小練習：** `String code = """TWD""";` 會怎樣？

- (A) 等於 "TWD"
- (B) 等於 "\"TWD\""
- (C) 編譯錯誤
- (D) 等於空字串，因為內容不在三引號之間的新行

<details><summary>看答案</summary>

**答案：(C)** 開頭分隔符是三個雙引號加上一個換行，內容從換行後開始。單行字串請用一般的 `"TWD"`。

</details>

**🧩 小練習：** 這段程式的 `s` 是什麼？

- (A) "X\n"
- (B) " X\n"
- (C) " X\n"
- (D) "X"

<details><summary>看答案</summary>

**答案：(B)** 內容那行有 10 格空白，結尾 `"""` 那行有 8 格；結尾分隔符獨占一行時也算進「共同縮排」，取最小值 8 去掉，X 前面剩 2 格。

</details>

**🧩 小練習：** 文字區塊裡，某一行的結尾刻意打了兩個空格。編譯後那兩個空格會怎樣？

- (A) 被刪掉；要保留就寫成 \s
- (B) 原樣保留在字串裡
- (C) 變成一個 \t 定位字元
- (D) 變成 \s 這兩個字元

<details><summary>看答案</summary>

**答案：(A)** JEP 378 的演算法會刪掉每一行行尾的空白，因為它們多半是無意的。`\s` 是 Java 15 新增的跳脫字元，代表一個空格，在刪除行尾空白之後才轉換，所以留得住。

</details>

**🧩 小練習：** 這段印出什麼？

- (A) 轉帳 換行 成功
- (B) 轉帳\成功
- (C) 編譯錯誤
- (D) 轉帳成功

<details><summary>看答案</summary>

**答案：(D)** 行尾的 `\` 取消了那個換行，兩行接成「轉帳成功」，最後再加結尾那個換行。這個跳脫只能用在文字區塊。

</details>

---

*【誰能繼承，由我說了算】*

## sealed 與 permits：封閉的類別階層，搭配 switch 窮舉

sealed 類別與介面（Java 17，JEP 409）限制哪些類別或介面可以延伸或實作它們。 [[出處]](https://openjdk.org/jeps/409) 銀行的付款方式只有三種，就把介面封起來，只准這三個 record 實作：

```java
sealed interface Payment permits Transfer, CardPayment, Cash {}
record Transfer(String toAccount, Money money) implements Payment {}
record CardPayment(String cardNo, Money money, int installments) implements Payment {}
record Cash(Money money) implements Payment {}

static String summary(Payment p) {
    return switch (p) {                          // sealed：三種都列出就不必 default
        case Transfer t -> "轉帳到 " + t.toAccount() + "：" + t.money().amount();
        case CardPayment(var card, var money, int n) when n > 1 ->
                "刷卡分 " + n + " 期：" + money.amount();
        case CardPayment c -> "刷卡一次付清：" + c.money().amount();
        case Cash(Money(var amount, var currency)) -> "現金 " + amount + " " + currency;
    };
}
// 轉帳到 B002：5000.00
// 刷卡分 6 期：12000.00
// 刷卡一次付清：800.00
// 現金 300.00 TWD
```

JEP 409 對被允許的子類別定了三條限制：跟 sealed 類別在同一個模組（沒有用模組時要在同一個套件）；必須直接繼承或實作它；而且每個子類別都要寫一個修飾字說明封閉要不要往下延續——`final`（到此為止，record 隱含就是 final）、`sealed`（再往下封閉）或 `non-sealed`（從這裡開放給任何人繼承）。子類別都寫在同一個原始檔時，可以省略 `permits`，由編譯器推論。 [[出處]](https://openjdk.org/jeps/409)

sealed 最大的用處在 switch：選擇的值是 sealed 型別時，窮舉檢查會參考 `permits` 清單，有時就不需要 `default`。 [[出處]](https://openjdk.org/jeps/441) 好處跟 enum 一樣：之後新增第四種付款方式，所有沒處理它的 switch 都會編譯失敗，不會默默落進 default。

| 寫法 | javac 21 的結果 |
|---|---|
| `class B implements Pay {}`（B 在 permits 裡，但沒寫修飾字） | `sealed, non-sealed or final modifiers expected` |
| `record C() implements Pay {}`（C 不在 permits 裡） | `class is not allowed to extend sealed class: Pay (as it is not listed in its 'permits' clause)` |
| 對 `Pay` 做 switch，只寫了 `case A a` | `the switch expression does not cover all possible input values` |

**🧩 小練習：** `sealed interface Payment permits Transfer, Cash {}`，另一個檔案寫 `record Crypto(String coin) implements Payment {}`，會怎樣？

- (A) 可以，record 隱含是 final
- (B) 編譯錯誤
- (C) 可以，但之後所有 switch 都要加 default
- (D) 可以，但要寫成 non-sealed record

<details><summary>看答案</summary>

**答案：(B)** sealed 只准 permits 列出的型別實作。javac 報 `class is not allowed to extend sealed class: Payment (as it is not listed in its 'permits' clause)`。record 本來就不能寫 non-sealed。

</details>

**🧩 小練習：** `sealed interface Pay permits A, B {}`，B 寫成 `class B implements Pay {}`（沒有任何修飾字），會怎樣？

- (A) 可以，B 預設是 final
- (B) 可以，B 預設是 non-sealed
- (C) 可以，B 預設是 sealed
- (D) 編譯錯誤，B 要寫修飾字

<details><summary>看答案</summary>

**答案：(D)** JEP 409 要求每個被允許的子類別明確說出封閉往下怎麼延續，沒有預設值；javac 報 `sealed, non-sealed or final modifiers expected`。record 不用寫，因為它隱含是 final。

</details>

**🧩 小練習：** 對上面的 `Payment`（Transfer、CardPayment、Cash）寫 switch 運算式，三個都有 case、沒有 default，能編譯嗎？

- (A) 可以，編譯器知道只有這三種
- (B) 不行，型別模式的 switch 一定要有 default
- (C) 可以，但會有警告
- (D) 不行，sealed 介面不能拿來 switch

<details><summary>看答案</summary>

**答案：(A)** 選擇的值是 sealed 型別時，窮舉檢查會參考 permits，三種都涵蓋就窮舉了，不需要 default。

</details>

**🧩 小練習：** 把 `summary` 裡的 `case Cash(...)` 那一行刪掉，會怎樣？

- (A) 可以，Cash 會回傳 null
- (B) 可以，Cash 會對到 CardPayment c
- (C) 編譯錯誤，switch 沒有窮舉
- (D) 可以，Cash 時丟出 MatchException

<details><summary>看答案</summary>

**答案：(C)** permits 裡的 Cash 沒有任何 case 涵蓋，switch 不再窮舉，javac 報 `does not cover all possible input values`。這正是 sealed 的價值：新增或漏掉一種型別，編譯期就抓到。

</details>

**🧩 小練習：** 用 `summary(new CardPayment("4111", Money.twd(800), 1))`，回傳什麼？

- (A) 刷卡分 1 期：800.00
- (B) 刷卡一次付清：800.00
- (C) 轉帳到 4111：800.00
- (D) 編譯錯誤

<details><summary>看答案</summary>

**答案：(B)** 第一個 CardPayment case 的守衛是 `n > 1`，1 期不成立，往下找到 `case CardPayment c`。

</details>

**🧩 小練習：** sealed 類別的子類別寫成 `non-sealed class`，代表什麼？

- (A) 這個子類別不能被繼承
- (B) 這個子類別也必須列 permits
- (C) 這個子類別不再算是 sealed 父類別的子型別
- (D) 從這個子類別開始，任何類別都可以再繼承它

<details><summary>看答案</summary>

**答案：(D)** `non-sealed` 讓這一支階層恢復成開放給未知的子類別延伸，sealed 父類別無法阻止。`final` 才是不能再被繼承；`sealed` 才需要自己的 permits。

</details>

---

*【Java 21 的另一個大功能】*

## 虛擬執行緒與 Java 25 的差異

**虛擬執行緒**（virtual thread，JEP 444）在 Java 21 正式定案 [[出處]](https://openjdk.org/jeps/444)：

- 由 Java 執行環境而不是作業系統排程
- 一個 JVM 可以撐數百萬條
- 適合大部分時間在等 I/O 的工作 [[出處]](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Thread.html)

它不是語法，而是 `Thread` 的另一種實作，入門在〈執行緒與並行〉的補充段，面試追問（不要池化、用 Semaphore 限量、Java 24 起 `synchronized` 不再釘住載體）在〈Java 並行快答：執行緒池、鎖與並行集合〉，它跟作業系統執行緒的關係在〈作業系統怎麼跑程式：行程、執行緒、記憶體與 I/O〉。

**Java 25 的建構子差異（JEP 513）。**Java 21 規定 `super(...)` 必須是建構子的第一行，想先驗證參數只能另寫靜態方法繞過。JEP 513 在 Java 25 定案：

- 允許 `super(...)`、`this(...)` 之前先放敘述
- 這些敘述不能引用正在建構的物件，但可以初始化它的欄位、做其他安全的計算 [[出處]](https://openjdk.org/jeps/513)
- record 的標準建構子仍然不能呼叫其他建構子，這條限制不變

```java
// Java 25 起（以 Java 25 執行）
class SavingsAccount extends Account {
    SavingsAccount(String id) {
        if (!id.startsWith("S")) {                       // super(...) 之前先驗證
            throw new IllegalArgumentException("儲蓄帳號要以 S 開頭：" + id);
        }
        super(id);
    }
}
// new SavingsAccount("C001") 丟出 IllegalArgumentException：儲蓄帳號要以 S 開頭：C001
// 同樣的程式用 Java 21 編譯：error: call to super must be first statement in constructor
```

**🧩 小練習：** 虛擬執行緒在 Java 21 屬於哪一類變更？

- (A) 新的語法，要用新的關鍵字宣告
- (B) Thread 的另一種實作，不是新語法
- (C) 預覽功能，要加 --enable-preview
- (D) 只能在 Spring 這類框架裡使用的功能，不屬於 JDK

<details><summary>看答案</summary>

**答案：(B)** JEP 444 在 Java 21 正式定案，不是預覽。它透過 `Thread.ofVirtual()`、`Executors.newVirtualThreadPerTaskExecutor()` 這些 API 使用，沒有新增語法。

</details>

**🧩 小練習：** 在 Java 21 編譯下面這個建構子，會怎樣？

- (A) 可以，先驗證再呼叫父類別建構子
- (B) 可以，但會有警告
- (C) 編譯錯誤
- (D) 可以，但 super(id) 會被忽略，父類別欄位是 null

<details><summary>看答案</summary>

**答案：(C)** javac 21 報 `call to super must be first statement in constructor`。super 之前放敘述是 JEP 513 在 Java 25 才定案的寫法。

</details>

**🧩 小練習：** 下面哪一個功能，在 Java 25 **仍是預覽**、還沒定案？

- (A) record 解構模式
- (B) 模式裡用 int 這類基本型別
- (C) switch 的型別模式與 when 守衛
- (D) 無名變數與無名模式 _

<details><summary>看答案</summary>

**答案：(B)** record 模式、switch 模式比對在 Java 21 定案（JEP 440、441），`_` 在 Java 22 定案（JEP 456）；基本型別模式的 JEP 507 在 Java 25 是第三次預覽。

</details>

### 重點整理

- `var`（Java 10）只用在有初始值的區域變數、for 迴圈與 try-with-resources；欄位、參數、回傳型別不行；它不是關鍵字。配菱形會推成 `Object`，右邊看不出型別時寫明比較好讀。
- `record`（Java 16）自動有讀取方法 `x()`、標準建構子、依值比較的 `equals`／`hashCode` 與 `toString`；驗證寫在緊湊建構子，改參數、不改欄位；隱含 final、不能 extends；不可變只到第一層，清單要 `List.copyOf`。
- switch 運算式（Java 14）要窮舉；箭頭不會穿透；區塊裡用 `yield` 交出值；enum 全列出時不寫 `default`，新增常數時編譯器才會提醒。
- 模式比對：`instanceof` 模式（Java 16）的變數只在一定比對成功處有效；switch 型別模式與 `when` 守衛、record 解構模式（Java 21）由上往下第一個符合的生效，窄的放前面；`default` 不接 null，要寫 `case null`。
- 文字區塊（Java 15）：開頭 `"""` 後要換行；共同縮排被拿掉，結尾 `"""` 的位置也算；行尾空白被刪，要留用 `\s`；行尾 `\` 取消換行。
- `sealed`／`permits`（Java 17）限定子型別，子類別要寫 `final`、`sealed` 或 `non-sealed`；配 switch 可以不寫 `default` 也窮舉。
- Java 22 起有 `_` 無名模式；Java 25 起 `super(...)` 之前可以先放驗證；基本型別模式在 Java 25 仍是預覽。

---

## 隨堂測驗

**Q1. 下面哪一個地方可以用 var 宣告？**

- (A) 方法裡、有初始值的區域變數
- (B) 方法的參數，呼叫時就知道型別
- (C) 類別的欄位，只要寫了初始值
- (D) 方法的回傳型別，從 return 推得出來

<details><summary>看答案</summary>

**答案：(A)** var 只能用在有初始值的區域變數、for 迴圈的變數（以及 try-with-resources 的資源）；欄位、參數、回傳型別、catch 參數都不行。

</details>

**Q2. var items = new ArrayList&lt;&gt;(); 推論出的型別是什麼？**

- (A) 編譯錯誤，var 不能配菱形
- (B) ArrayList&lt;String&gt;
- (C) ArrayList&lt;Object&gt;
- (D) List&lt;Object&gt;

<details><summary>看答案</summary>

**答案：(C)** 左邊沒有型別可參考，菱形只好推成 Object。能編譯，但什麼都放得進去；var 配菱形時，右邊要寫出型別參數。

</details>

**Q3. record Money(BigDecimal amount, String currency) {} 的兩個物件，什麼時候 equals 回傳 true？**

- (A) 兩者是同一個物件時，跟 == 一樣
- (B) 永遠不會，record 沒有覆寫 equals
- (C) 只要 amount 相等，幣別不比
- (D) amount 與 currency 都相等時

<details><summary>看答案</summary>

**答案：(D)** 自動產生的 equals 在同型別、而且元件值都相等時回傳 true，所以 record 適合當 Map 的鍵。

</details>

**Q4. 要在 record 建立時檢查幣別是三個大寫字母，最直接的寫法是什麼？**

- (A) 宣告一個 private boolean valid 欄位記錄
- (B) 在 toString 裡檢查，印出來時就知道
- (C) 寫一個 setCurrency 方法，設定時檢查
- (D) 在緊湊建構子 Money { ... } 裡檢查

<details><summary>看答案</summary>

**答案：(D)** 緊湊建構子就是為了驗證與正規化參數而設計；record 欄位是 final、沒有 setter，也不能自己加實體欄位。

</details>

**Q5. record 能不能寫 extends？**

- (A) 不能，但可以 implements 介面
- (B) 可以，但只能繼承一層，不能再往上
- (C) 可以，只要父類別是抽象類別就行
- (D) 不能，而且也不能 implements 任何介面

<details><summary>看答案</summary>

**答案：(A)** record 宣告沒有 extends，父類別固定是 java.lang.Record；它隱含是 final，可以實作任意介面。

</details>

**Q6. 舊的 switch 敘述 case BRANCH: fee = 30; 後面忘了寫 break，會發生什麼事？**

- (A) 執行時丟出例外，提醒少了 break
- (B) 編譯錯誤，缺 break 的 case 不能編譯
- (C) 只執行 BRANCH 這一段就離開
- (D) 繼續執行下一個 case（穿透）

<details><summary>看答案</summary>

**答案：(D)** 傳統的 case ... : 預設會穿透到下一個 case。箭頭寫法 case ... -&gt; 只執行右邊那一段，不會穿透。

</details>

**Q7. switch 運算式的 case 右邊是大括號區塊時，用什麼交出這個 case 的值？**

- (A) return
- (B) break
- (C) 最後一行的運算式自動成為值
- (D) yield

<details><summary>看答案</summary>

**答案：(D)** yield（JEP 361 新增）給 switch 運算式交出值；return 會離開整個方法，break 不能拿來跳出 switch 運算式。

</details>

**Q8. switch (obj) 裡依序寫 case CharSequence cs -&gt; ... 與 case String s -&gt; ...，會怎樣？**

- (A) 兩個 case 都會執行，先 CharSequence 再 String
- (B) 編譯錯誤，String 那個 case 被支配
- (C) 執行時丟出 MatchException
- (D) 字串會進 String 那個 case

<details><summary>看答案</summary>

**答案：(B)** 由上往下第一個符合的生效；String 是 CharSequence 的子型別，後面那個 case 永遠輪不到，這是編譯錯誤。窄的要放前面。

</details>

**Q9. 一個用了型別模式的 switch，選擇的值是 null，而且沒有寫 case null，會怎樣？**

- (A) 丟出 NullPointerException
- (B) 編譯錯誤，模式 switch 一定要寫 case null
- (C) 回傳 null，交給呼叫者處理
- (D) 落進 default 那個分支

<details><summary>看答案</summary>

**答案：(A)** 沒有 case null 就跟以前一樣丟 NullPointerException；為了相容，default 不會比對到 null。

</details>

**Q10. sealed interface Payment permits Transfer, Cash {}，對 Payment 寫 switch 運算式，列出 Transfer 與 Cash 兩個 case、不寫 default，會怎樣？**

- (A) 編譯錯誤，型別模式的 switch 一定要有 default
- (B) 可以編譯，但其他型別會回傳 null
- (C) 編譯錯誤，sealed 介面不能放進 switch
- (D) 可以編譯，編譯器依 permits 知道已經窮舉

<details><summary>看答案</summary>

**答案：(D)** 選擇的值是 sealed 型別時，窮舉檢查會參考 permits 清單。之後多一種付款方式，沒處理它的 switch 會編譯失敗。

</details>
