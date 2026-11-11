# 13. SOLID 與常見反模式

> 來源：[筆記平台 · Java](https://hhtim.github.io/notes-platform/java/#/lesson/java-solid-antipatterns)　第 13 課 / 共 18 課 · 約 50 分鐘

**五個設計原則各用一個銀行例子：先寫違反的版本、看它痛在哪、再重構；接著看原則跟設計模式的關係，以及上帝類別、貧血模型兩派、過早抽象、static 工具類別、吞掉例外。**

### 讀完這課你會

- 說出 SOLID 五個原則各在防什麼
- 指出程式違反哪一條並重構
- 分清原則與設計模式的關係
- 認得常見的反模式

---

*【原則，不是規定】*

## SOLID 是什麼：五個讓程式好改的設計原則

SOLID 是五個物件導向設計原則的英文首字母：

| 字母 | 原則 | 一句話 |
|---|---|---|
| **S** | 單一職責原則（Single Responsibility Principle） | 一個類別只該因為一種理由被修改 |
| **O** | 開放封閉原則（Open Closed Principle） | 加新功能時擴充，不要回頭改舊程式 |
| **L** | 里氏替換原則（Liskov Substitution Principle） | 子型別放進父型別的位置，程式要照常運作 |
| **I** | 介面隔離原則（Interface Segregation Principle） | 不要逼使用端依賴它用不到的方法 |
| **D** | 依賴反轉原則（Dependency Inversion Principle） | 高層規則依賴抽象，不依賴具體細節 |

這五條大多由 Robert C. Martin 整理推廣（主要是 2000 年的文章〈Design Principles and Design Patterns〉）。出發點是軟體為什麼會爛掉：需求一直變，模組之間的相依關係越纏越緊，改一處壞一片；要擋住這種退化，就得管理模組之間的相依，物件導向設計裡有很多原則與技巧，就是用來建立這種防火牆、管理模組相依。 [[出處]](https://web.archive.org/web/20150906155800/http://www.objectmentor.com/resources/articles/Principles_and_Patterns.pdf) 所以 SOLID 的目的只有一個：**讓程式在需求改變時好改**。

它們是**原則**，不是編譯器會檢查的規定。違反了程式照樣能跑，只是之後改起來比較痛；硬套也有代價（多出來的介面與類別）。〈介面與抽象類別〉講過的「耦合要低、凝聚要高」是這五條背後共同的方向。

> SOLID 這五個字母不是同一份文件同時提出的：2000 年那篇文章講的是開放封閉、里氏替換、依賴反轉、介面隔離四條（外加幾條套件層級的原則），單一職責原則出自 Martin 另一篇文章與他後來的書。

**🧩 小練習：** SOLID 五個原則最主要想解決的問題是什麼？

- (A) 需求改變時程式還是好改
- (B) 讓程式在任何機器上都跑得比較快
- (C) 讓專案裡的類別數量越多越好
- (D) 讓程式不需要寫測試

<details><summary>看答案</summary>

**答案：(A)** SOLID 從「相依關係越纏越緊、軟體爛掉」出發，原則是用來管理模組相依的。它們跟執行速度無關，也不是類別越多越好。

</details>

**🧩 小練習：** 一段程式違反了單一職責原則，會發生什麼事？

- (A) 編譯器報錯，整個專案無法編譯
- (B) 執行時一定丟出例外並中止
- (C) JVM 會在執行時自動把類別拆開
- (D) 照樣能跑，之後難改

<details><summary>看答案</summary>

**答案：(D)** SOLID 是設計原則，不是語言規則。違反它不會有任何錯誤訊息，代價出現在之後改需求的時候。

</details>

**🧩 小練習：** SOLID 五條裡，哪一條跟其他四條不是出自同一篇文章？

- (A) 開放封閉原則
- (B) 依賴反轉原則
- (C) 單一職責原則
- (D) 里氏替換原則

<details><summary>看答案</summary>

**答案：(C)** 那篇文章講類別層級的開放封閉、里氏替換、依賴反轉、介面隔離四條；單一職責原則出自他另一篇文章與後來的書。

</details>

---

*【誰會要求你改這段程式】*

## 單一職責原則：一個類別只為一群人負責

單一職責原則最早的定義：**一個類別不該有超過一個被修改的理由**，因為每一種職責都是一條會變動的軸。 [[出處]](https://web.archive.org/web/20150906155800/http://www.objectmentor.com/resources/articles/srp.pdf)

「理由」很容易被誤解成「功能」或「做一件事」。Martin 2014 年的補充： [[出處]](https://blog.cleancoder.com/uncle-bob/2014/05/08/SingleReponsibilityPrinciple.html)

- 每個軟體模組應該有一個、而且只有一個被修改的理由
- **這個原則講的是人**：修改的要求應該只來自一群緊密相關、代表單一業務功能的人
- 例子：一個員工類別同時有算薪水、存資料庫、出工時報表三個方法，分別由財務長、技術長、營運長的部門提出修改

換成銀行：一個 `Account` 同時負責算利息（財務部決定）、印對帳單（營運部決定）、存檔（資訊部決定），三個方法共用一個「四捨五入到元」的小工具：

```java
class Account {
    private final String id;
    private final BigDecimal balance;
    private static final BigDecimal YEARLY_RATE = new BigDecimal("0.0125");

    Account(String id, String balance) {
        this.id = id;
        this.balance = new BigDecimal(balance);
    }

    BigDecimal monthlyInterest() {                     // 財務部決定：利息怎麼算
        return toDollar(balance.multiply(YEARLY_RATE).divide(BigDecimal.valueOf(12), 10, RoundingMode.HALF_UP));
    }

    String statement() {                               // 營運部決定：對帳單長什麼樣
        return id + " 餘額 " + toDollar(balance) + " 元";
    }

    void save() {                                      // 資訊部決定：資料怎麼存
        System.out.println("寫入資料庫：" + id + " = " + balance);
    }

    private BigDecimal toDollar(BigDecimal v) {        // 三個方法共用的小工具：四捨五入到元
        return v.setScale(0, RoundingMode.HALF_UP);
    }
}
```

某天財務部要求「利息一律無條件捨去」。工程師看到利息用的是 `toDollar`，就把那一行改成 `RoundingMode.DOWN`（範例檔裡的 `AccountAfterFinanceChange` 就是把捨入那一行改成 DOWN）。實跑：

```text
改之前：利息 11 元；A-001 餘額 10501 元
財務部改完：利息 10 元；A-001 餘額 10500 元
```

利息照財務部的意思從 11 變 10，但**對帳單上的餘額也從 10501 變成 10500**，營運部根本沒要求改。這就是 Martin 說的：改了財務部要的東西，卻弄壞營運部負責的東西。重構的方向是照「誰會要求改」拆開：

```java
import java.math.BigDecimal;
import java.math.RoundingMode;

public class SrpAfter {
    public static void main(String[] args) {
        Account a = new Account("A-001", new BigDecimal("10500.50"));
        System.out.println("利息 " + new InterestPolicy().monthlyInterest(a) + " 元；" + new StatementPrinter().print(a));
        new AccountRepository().save(a);
    }
}

class Account {                                        // 帳戶自己的規則：餘額不能是負的
    private final String id;
    private BigDecimal balance;

    Account(String id, BigDecimal balance) {
        if (balance.signum() < 0) throw new IllegalArgumentException("餘額不可為負");
        this.id = id;
        this.balance = balance;
    }

    String id() { return id; }
    BigDecimal balance() { return balance; }
}

class InterestPolicy {                                 // 只有財務部會要求改這裡
    private static final BigDecimal YEARLY_RATE = new BigDecimal("0.0125");

    BigDecimal monthlyInterest(Account a) {
        return a.balance().multiply(YEARLY_RATE)
                .divide(BigDecimal.valueOf(12), 0, RoundingMode.DOWN);   // 無條件捨去
    }
}

class StatementPrinter {                               // 只有營運部會要求改這裡
    String print(Account a) {
        return a.id() + " 餘額 " + a.balance().setScale(0, RoundingMode.HALF_UP) + " 元";
    }
}

class AccountRepository {                              // 只有資訊部會要求改這裡
    void save(Account a) {
        System.out.println("寫入資料庫：" + a.id() + " = " + a.balance());
    }
}
```

```text
利息 10 元；A-001 餘額 10501 元
寫入資料庫：A-001 = 10500.50
```

![單一職責原則示意：左邊是一個 Account 類別，同時被財務部、營運部、資訊部三個方向的修改要求指著；右邊拆成 InterestPolicy、StatementPrinter、AccountRepository 三個類別，各自只被一個部門指著，Account 留下自己的餘額規則](images/13_java-solid-antipatterns_1.svg)

*圖：* 拆的依據不是「功能數量」，而是「誰會提出修改」。三個部門的修改各自落在不同類別，財務部改捨入方式不會再波及對帳單。

界線：拆到每個類別只剩一個方法不是目標。要做的是：同樣理由會變的東西放在一起，不同理由會變的分開。 [[出處]](https://blog.cleancoder.com/uncle-bob/2014/05/08/SingleReponsibilityPrinciple.html) 例如「餘額不能是負的」是帳戶本身的規則，就留在 `Account` 裡，沒有跟著拆出去。

**🧩 小練習：** 上面的 `Account` 同時有 `monthlyInterest()`、`statement()`、`save()`。判斷它是否違反單一職責原則，最該問哪一個問題？

- (A) 會有幾群不同的人要求改它
- (B) 這個類別有沒有超過一百行程式碼
- (C) 這個類別總共宣告了幾個方法
- (D) 這些方法是不是每個都很短

<details><summary>看答案</summary>

**答案：(A)** 這個原則講的是人：修改要求應該只來自單一業務功能的那群人。行數與方法數只是旁證。

</details>

**🧩 小練習：** 實跑結果裡，財務部只要求改利息的捨入方式，結果哪裡也跟著變了？

- (A) 寫進資料庫的帳戶金額
- (B) 帳戶編號的顯示格式
- (C) 什麼都沒有改變
- (D) 對帳單顯示的餘額

<details><summary>看答案</summary>

**答案：(D)** 利息與對帳單共用 toDollar，改成無條件捨去之後，對帳單餘額從 10501 變成 10500。兩個職責綁在同一個小工具上，就會互相波及。

</details>

**🧩 小練習：** 重構後，如果營運部要求「對帳單餘額改成顯示到角（小數一位）」，要改哪個類別？

- (A) `StatementPrinter`
- (B) `InterestPolicy`
- (C) `AccountRepository`
- (D) `Account`

<details><summary>看答案</summary>

**答案：(A)** 對帳單格式只歸營運部管，所以只動 StatementPrinter；利息與存檔的程式不會被碰到。

</details>

**🧩 小練習：** 下面哪一句最符合單一職責原則？

- (A) 同理由一起，不同理由分開
- (B) 每個類別最多只能有一個方法
- (C) 每個方法只能做一件事情
- (D) 每個類別都要搭配自己的介面

<details><summary>看答案</summary>

**答案：(A)** 同樣理由會變的放在一起、不同理由會變的分開。「只能有一個方法」是常見的誤讀。

</details>

**🧩 小練習：** 重構後的 `Account` 為什麼還留著「餘額不可為負」的檢查，沒有拆到別的類別？

- (A) 因為建構子不能被拆出去
- (B) Java 規定驗證要寫在建構子
- (C) 其實應該拆，這裡漏掉了
- (D) 那是帳戶本身的規則

<details><summary>看答案</summary>

**答案：(D)** 單一職責不是把類別拆空。帳戶本身的不變條件跟帳戶一起變，留在 Account 裡剛好；這也接到後面「貧血模型」的討論。

</details>

---

*【新增帳戶類型，不要回頭改舊程式】*

## 開放封閉原則：對擴充開放，對修改封閉

開放封閉原則（源自 Bertrand Meyer）：**一個模組應該對擴充開放、對修改封閉**。 [[出處]](https://web.archive.org/web/20150906155800/http://www.objectmentor.com/resources/articles/Principles_and_Patterns.pdf)

- 意思是改變模組做的事，卻不必改它的原始碼
- 做法只有一個方向：**抽象是開放封閉原則的關鍵**

跨行轉帳手續費依帳戶類型不同。違反的版本用一個 switch 判斷類型：

```java
public class OcpBefore {
    public static void main(String[] args) {
        FeeCalculator calc = new FeeCalculator();
        for (String type : new String[]{"一般戶", "薪轉戶", "數位帳戶", "VIP 戶"}) {
            try {
                System.out.println(type + " 跨行轉帳 5000 元，手續費 " + calc.fee(type, 5000) + " 元");
            } catch (IllegalArgumentException e) {
                System.out.println(type + "：" + e.getMessage());
            }
        }
    }
}

class FeeCalculator {
    int fee(String accountType, int amount) {
        return switch (accountType) {                  // 每多一種帳戶，就要回來改這裡
            case "一般戶" -> 15;
            case "薪轉戶" -> 0;
            case "數位帳戶" -> amount >= 1000 ? 10 : 0;
            default -> throw new IllegalArgumentException("不認得的帳戶類型");
        };
    }
}
```

```text
一般戶 跨行轉帳 5000 元，手續費 15 元
薪轉戶 跨行轉帳 5000 元，手續費 0 元
數位帳戶 跨行轉帳 5000 元，手續費 10 元
VIP 戶：不認得的帳戶類型
```

業務新推出 VIP 戶，`FeeCalculator` 不認得。要支援它，就得回頭打開這個已經上線、測過的方法加一個 case；而且所有判斷帳戶類型的 switch（算手續費、算利息、算額度……）都要一起找出來改。Martin 在文章裡描述過同樣的症狀：這樣設計的程式「到處是類似的 if/else 或 switch」。重構的做法是把「會變的那一塊」（手續費怎麼算）抽成介面：

```java
import java.util.List;

public class OcpAfter {
    public static void main(String[] args) {
        List<FeePolicy> policies = List.of(new RegularFee(), new PayrollFee(), new DigitalFee(), new VipFee());
        TransferService service = new TransferService();
        for (FeePolicy p : policies) {
            System.out.println(p.name() + " 跨行轉帳 5000 元，手續費 " + service.fee(p, 5000) + " 元");
        }
    }
}

interface FeePolicy {
    String name();
    int feeFor(int amount);
}

class TransferService {                                // 新增帳戶類型時，這個類別一個字都不用改
    int fee(FeePolicy policy, int amount) {
        return policy.feeFor(amount);
    }
}

class RegularFee implements FeePolicy {
    public String name() { return "一般戶"; }
    public int feeFor(int amount) { return 15; }
}

class PayrollFee implements FeePolicy {
    public String name() { return "薪轉戶"; }
    public int feeFor(int amount) { return 0; }
}

class DigitalFee implements FeePolicy {
    public String name() { return "數位帳戶"; }
    public int feeFor(int amount) { return amount >= 1000 ? 10 : 0; }
}

class VipFee implements FeePolicy {                    // 後來新增：只加這個類別
    public String name() { return "VIP 戶"; }
    public int feeFor(int amount) { return 0; }
}
```

```text
一般戶 跨行轉帳 5000 元，手續費 15 元
薪轉戶 跨行轉帳 5000 元，手續費 0 元
數位帳戶 跨行轉帳 5000 元，手續費 10 元
VIP 戶 跨行轉帳 5000 元，手續費 0 元
```

新增 VIP 戶只**加**了 `VipFee` 這個類別，`TransferService` 與其他三種手續費都沒有改。這個結構就是〈設計模式〉的策略模式（Strategy）。

界線：沒有程式能對所有變化都封閉。這裡封閉的是「新增帳戶類型」；如果變化反過來是「每種帳戶都要多一種費用」，就得改介面、改所有實作。所以先問「哪裡最常變」，只在那裡留擴充點。帳戶種類固定、很少新增時，〈現代 Java 語法：var、record、switch、文字區塊與 sealed〉講的 sealed 介面搭配 switch 模式比對也是合理的選擇：少處理一種，編譯器會提醒你。

**🧩 小練習：** 照開放封閉原則，新增一種「VIP 戶」最理想的改法是？

- (A) 在 switch 加一個 case
- (B) 複製一份 TransferService 改名
- (C) 在 TransferService 加 if 判斷
- (D) 新增實作 FeePolicy 的類別

<details><summary>看答案</summary>

**答案：(D)** 擴充靠新增類別，既有的 TransferService 與其他手續費類別都不用打開。加 case、加 if 都是在改舊程式。

</details>

**🧩 小練習：** 達成開放封閉原則的關鍵是什麼？

- (A) 把所有欄位設成 final
- (B) 把所有方法設成 static
- (C) 抽象
- (D) 盡量少寫類別

<details><summary>看答案</summary>

**答案：(C)** 抽象是開放封閉原則的關鍵。呼叫端依賴 FeePolicy 這個抽象，具體算法才能自由增加。

</details>

**🧩 小練習：** 重構前的版本跑到 VIP 戶時，實跑輸出是什麼？

- (A) VIP 戶：不認得的帳戶類型
- (B) VIP 戶跨行轉帳，手續費 0 元
- (C) VIP 戶跨行轉帳，手續費 15 元
- (D) 編譯失敗，switch 少了 case

<details><summary>看答案</summary>

**答案：(A)** switch 走到 default 丟出 IllegalArgumentException。要支援 VIP 戶只能回頭改 FeeCalculator。

</details>

**🧩 小練習：** 重構後的手續費設計，對下面哪一種變化**不**封閉，仍然要改到很多既有類別？

- (A) 新增一種「學生戶」帳戶
- (B) 每種帳戶都多算匯率加價
- (C) VIP 戶改成每筆收 5 元
- (D) 數位帳戶門檻從 1000 改成 2000

<details><summary>看答案</summary>

**答案：(B)** 新增類型或調整單一類型都只動一個類別；但「每種帳戶都多一種費用」要改 FeePolicy 介面與所有實作。開放封閉只對你選定的那種變化成立。

</details>

**🧩 小練習：** 重構後「把會變的演算法包成可替換的物件」這個結構，在〈設計模式〉裡叫什麼？

- (A) Singleton
- (B) Adapter
- (C) Facade
- (D) Strategy

<details><summary>看答案</summary>

**答案：(D)** 每種手續費算法各包成一個 FeePolicy 物件、執行時選一個用，就是策略模式。

</details>

---

*【子型別要守父型別的約定】*

## 里氏替換原則：放進父型別的位置，要照常運作

里氏替換原則的原始定義來自 Barbara Liskov 1987 年在 OOPSLA 的講稿〈Data Abstraction and Hierarchy〉：**如果對每個型別 S 的物件 o1，都有一個型別 T 的物件 o2，使得所有以 T 定義的程式 P 在把 o2 換成 o1 時行為不變，那麼 S 就是 T 的子型別**。 [[出處]](https://doi.org/10.1145/62139.62141)

- 子型別、父型別：語意上的區別
- 子類別、父類別：只是程式語言的語法概念

也就是說，`extends` 寫得出來，不代表語意上真的是子型別。

Martin 的濃縮版：**子類別應該能替換它們的父類別**。用約定來講： [[出處]](https://web.archive.org/web/20150906155800/http://www.objectmentor.com/resources/articles/Principles_and_Patterns.pdf)

- 子類別方法的**前置條件**（呼叫前必須成立的條件）不比父類別強
- 子類別方法的**後置條件**（方法保證做完之後成立的結果）不比父類別弱
- 一句話：要求不能更多，提供不能更少

定存「是一種」帳戶，直覺上就讓它繼承 `Account`。但 `Account.withdraw` 的約定是「金額不超過餘額就一定扣得成」，定存卻多加了「沒到期一律不能提」，前置條件變強了：

```java
import java.util.List;

public class LspBefore {
    public static void main(String[] args) {
        List<Account> accounts = List.of(new Account("活存-01", 3000), new FixedDeposit("定存-02", 100000), new Account("活存-03", 500));
        for (Account a : accounts) {                   // 月底批次：每個帳戶扣 10 元帳戶管理費
            try {
                a.withdraw(10);
                System.out.println(a.id() + " 扣款成功，餘額 " + a.balance());
            } catch (RuntimeException e) {
                System.out.println(a.id() + " 扣款失敗：" + e.getMessage());
            }
        }
    }
}

class Account {
    private final String id;
    protected int balance;

    Account(String id, int balance) { this.id = id; this.balance = balance; }

    // 約定：amount 不超過餘額就一定扣得成
    void withdraw(int amount) {
        if (amount > balance) throw new IllegalArgumentException("餘額不足");
        balance -= amount;
    }

    String id() { return id; }
    int balance() { return balance; }
}

class FixedDeposit extends Account {                   // 定存「是一種」帳戶？
    FixedDeposit(String id, int balance) { super(id, balance); }

    @Override
    void withdraw(int amount) {                        // 多加了條件：沒到期一律不能提
        throw new IllegalStateException("定存未到期，不能提款");
    }
}
```

```text
活存-01 扣款成功，餘額 2990
定存-02 扣款失敗：定存未到期，不能提款
活存-03 扣款成功，餘額 490
```

月底批次只認得 `Account`，照父型別的約定扣款，碰到定存就失敗。呼叫端只好開始寫 `if (a instanceof FixedDeposit)` 跳過它。這是違反里氏替換原則的典型後果：補救方式是在呼叫端加 if/else，所以**違反里氏替換原則，就是潛在地違反開放封閉原則**。 [[出處]](https://web.archive.org/web/20150906155800/http://www.objectmentor.com/resources/articles/Principles_and_Patterns.pdf) 〈封裝、繼承、多型〉也講過：程式到處判斷具體子型別，通常表示共同介面沒設計好。重構：把「能隨時提款」變成一個獨立的能力，定存不具備它：

```java
import java.util.List;

public class LspAfter {
    public static void main(String[] args) {
        List<Withdrawable> chargeable = List.of(new SavingsAccount("活存-01", 3000), new SavingsAccount("活存-03", 500));
        for (Withdrawable a : chargeable) {            // 批次只拿「能提款」的帳戶
            a.withdraw(10);
            System.out.println(a.id() + " 扣款成功，餘額 " + a.balance());
        }
        FixedDeposit fd = new FixedDeposit("定存-02", 100000, 12);
        System.out.println(fd.id() + " 到期可領 " + fd.maturityAmount() + " 元（不在扣款名單）");
    }
}

abstract class Account {
    private final String id;
    protected int balance;

    Account(String id, int balance) { this.id = id; this.balance = balance; }

    String id() { return id; }
    int balance() { return balance; }
}

interface Withdrawable {
    String id();
    int balance();
    void withdraw(int amount);                         // 約定：amount 不超過餘額就一定扣得成
}

class SavingsAccount extends Account implements Withdrawable {
    SavingsAccount(String id, int balance) { super(id, balance); }

    public void withdraw(int amount) {
        if (amount > balance) throw new IllegalArgumentException("餘額不足");
        balance -= amount;
    }

    public String id() { return super.id(); }
    public int balance() { return super.balance(); }
}

class FixedDeposit extends Account {                   // 不實作 Withdrawable：型別上就看得出它不能隨時提款
    private final int months;

    FixedDeposit(String id, int balance, int months) { super(id, balance); this.months = months; }

    int maturityAmount() { return balance + balance * months / 100 / 12; }   // 年利率 1%，簡化成整數
}
```

```text
活存-01 扣款成功，餘額 2990
活存-03 扣款成功，餘額 490
定存-02 到期可領 101000 元（不在扣款名單）
```

現在 `FixedDeposit` 根本不是 `Withdrawable`，批次也不可能把它放進扣款名單，問題在編譯時就擋掉了。

### 爭議：JDK 自己的「可選操作」

Java 的集合框架有一個常被拿來討論的設計：`Collection` 某些會修改內容的方法，可以被規定成在集合實作不支援那個操作時丟出 `UnsupportedOperationException`。 [[出處]](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Collection.html) 所以 `List.of(1, 2).add(3)` 會丟例外。兩派看法：

- **違反**：拿到一個 `List`，你不知道能不能 add
- **沒有違反**：父型別的約定本來就寫了「可能丟 UnsupportedOperationException」，子型別沒有比約定要求更多；代價是呼叫端得自己知道拿到的是哪一種

兩邊的共同點是：**里氏替換原則看的是約定寫了什麼**，不是方法名稱長得一不一樣。

**🧩 小練習：** 里氏替換原則的原始定義裡，判斷 S 是不是 T 的子型別，看的是什麼？

- (A) S 有沒有寫 extends T
- (B) 替換後程式行為不變
- (C) S 的方法名稱跟 T 一樣
- (D) S 的欄位比 T 多

<details><summary>看答案</summary>

**答案：(B)** 定義是「所有以 T 定義的程式，替換之後行為不變」。子類別只是語法概念，子型別才是語意上的關係。

</details>

**🧩 小練習：** 定存覆寫 `withdraw`、沒到期一律丟例外。從前置條件、後置條件的約定來看，它違反了哪一點？

- (A) 後置條件變強了
- (B) 前置條件變強了
- (C) 方法名稱改了
- (D) 存取權限變小了

<details><summary>看答案</summary>

**答案：(B)** 父類別只要求金額不超過餘額，定存多要求「已到期」，呼叫前必須成立的條件變多了，就是前置條件變強。一句話：要求不能更多，提供不能更少。

</details>

**🧩 小練習：** 月底批次扣款跑到定存失敗，呼叫端最常見的「補救」是什麼？它的問題在哪？

- (A) 加 instanceof 跳過；也違反開放封閉
- (B) 改用 static 方法就沒問題
- (C) 多 catch 一次，問題就解決
- (D) 把定存的餘額直接改成 0 元避開扣款

<details><summary>看答案</summary>

**答案：(A)** 每多一種「不能扣款」的帳戶，批次就得再加一個判斷，呼叫端被迫跟著改。違反里氏替換原則，就是潛在地違反開放封閉原則。

</details>

**🧩 小練習：** 重構後，批次扣款的名單型別是 `List<Withdrawable>`。想把定存放進去，會發生什麼事？

- (A) 執行時丟出 IllegalStateException
- (B) 可以放進去，扣款金額變成 0
- (C) 編譯失敗，型別不符
- (D) 可以放進去，批次自動跳過

<details><summary>看答案</summary>

**答案：(C)** FixedDeposit 沒有實作 Withdrawable，型別不符，編譯時就擋下來，不必等到批次執行。

</details>

**🧩 小練習：** 下面哪一個子類別寫法**符合**里氏替換原則？（父類別約定：金額大於 0 且不超過餘額就扣款成功）

- (A) 金額超過一萬元就丟出例外
- (B) 扣款成功但不更新帳戶餘額
- (C) 只在營業時間內允許扣款
- (D) 扣款後另外記一筆稽核紀錄

<details><summary>看答案</summary>

**答案：(D)** 多記一筆紀錄是「提供更多」，父類別承諾的結果一樣成立。另外三個不是多加要求（前置條件變強），就是少做了承諾的事（後置條件變弱）。

</details>

**🧩 小練習：** `List.of(1, 2).add(3)` 丟出 UnsupportedOperationException。關於它算不算違反里氏替換原則，這課的說法是？

- (A) 一定違反，JDK 這裡寫錯了
- (B) 一定沒違反，因為它是 JDK 自己
- (C) 兩派都有，要看約定寫了什麼
- (D) 跟里氏替換原則完全無關

<details><summary>看答案</summary>

**答案：(C)** Collection 的修改方法可以被規定成丟 UnsupportedOperationException。一派說呼叫端仍無法放心替換，一派說約定本來就允許。判斷都回到約定寫了什麼。

</details>

---

*【稽核人員不需要提款按鈕】*

## 介面隔離原則：介面照使用端切

介面隔離原則：**很多個針對使用端的介面，勝過一個通用的大介面**。做法是：一個類別有好幾種使用端時，不要把所有使用端需要的方法都塞進這個類別，而是替每一種使用端建立專屬的介面。 [[出處]](https://web.archive.org/web/20150906155800/http://www.objectmentor.com/resources/articles/Principles_and_Patterns.pdf)

```java
public class IspBefore {
    public static void main(String[] args) {
        BankOperations auditor = new AuditPortal();
        System.out.println(auditor.auditReport("2026-09"));
        try {
            auditor.withdraw("A-001", 1000);
        } catch (UnsupportedOperationException e) {
            System.out.println("稽核入口呼叫 withdraw：" + e.getMessage());
        }
    }
}

interface BankOperations {                             // 一個大介面，什麼都放
    void deposit(String accountId, int amount);
    void withdraw(String accountId, int amount);
    void approveLoan(String applicationId);
    String auditReport(String month);
}

class AuditPortal implements BankOperations {          // 稽核人員只看報表，卻被迫實作提款與核貸
    public void deposit(String accountId, int amount) { throw new UnsupportedOperationException("稽核不能存款"); }
    public void withdraw(String accountId, int amount) { throw new UnsupportedOperationException("稽核不能提款"); }
    public void approveLoan(String applicationId) { throw new UnsupportedOperationException("稽核不能核貸"); }
    public String auditReport(String month) { return month + " 稽核報表：共 3 筆異常交易"; }
}
```

```text
2026-09 稽核報表：共 3 筆異常交易
稽核入口呼叫 withdraw：稽核不能提款
```

稽核入口只看報表，卻被大介面逼著寫出三個「不支援」的方法；拿到 `BankOperations` 的人也看不出哪些方法真的能用，一呼叫就是執行期的例外。這同時也違反了里氏替換原則。另一個代價是：大介面每加一個方法，所有實作它的類別都要跟著改、重新編譯。照使用端切開：

```java
public class IspAfter {
    public static void main(String[] args) {
        AuditReports auditor = new AuditPortal();
        System.out.println(auditor.auditReport("2026-09"));
        CashOperations atm = new AtmTerminal();
        atm.deposit("A-001", 1000);
        atm.withdraw("A-001", 300);
    }
}

interface CashOperations {                             // 臨櫃與 ATM 用
    void deposit(String accountId, int amount);
    void withdraw(String accountId, int amount);
}

interface LoanApprovals {                              // 授信部門用
    void approveLoan(String applicationId);
}

interface AuditReports {                               // 稽核用
    String auditReport(String month);
}

class AuditPortal implements AuditReports {            // 只實作自己要用的那一個
    public String auditReport(String month) { return month + " 稽核報表：共 3 筆異常交易"; }
}

class AtmTerminal implements CashOperations {
    public void deposit(String accountId, int amount) { System.out.println("ATM 存入 " + accountId + "：" + amount + " 元"); }
    public void withdraw(String accountId, int amount) { System.out.println("ATM 提領 " + accountId + "：" + amount + " 元"); }
}
```

```text
2026-09 稽核報表：共 3 筆異常交易
ATM 存入 A-001：1000 元
ATM 提領 A-001：300 元
```

界線：切的依據是「使用端」，不是「每個方法一個介面」。存款與提款總是一起被臨櫃與 ATM 使用，就放在同一個 `CashOperations`。〈介面與抽象類別〉的 `Writable`、`Erasable` 拆成兩個小介面，也是同一個想法。

**🧩 小練習：** 重構前，`AuditPortal` 被迫實作 `withdraw` 並丟出 UnsupportedOperationException。這是因為違反了什麼？

- (A) 單一職責：AuditPortal 的方法太少
- (B) 介面隔離：被迫實作用不到的方法
- (C) 開放封閉：AuditPortal 不能被繼承
- (D) 沒有違反任何一條原則

<details><summary>看答案</summary>

**答案：(B)** BankOperations 把所有使用端的方法塞在一起，稽核入口只好實作一堆用不到的方法。它同時也讓 AuditPortal 無法安全替換 BankOperations。

</details>

**🧩 小練習：** 介面隔離原則說介面該照什麼來切？

- (A) 照資料表的結構來切
- (B) 照方法名稱的字母順序
- (C) 照使用端需要的方法
- (D) 每個方法各一個介面

<details><summary>看答案</summary>

**答案：(C)** 替每一種使用端建立專屬的介面。存款與提款總是被同一群使用端一起用，就放在同一個介面裡，不必拆到一個方法一個介面。

</details>

**🧩 小練習：** 重構後，授信部門要在 `LoanApprovals` 加一個 `rejectLoan` 方法。哪些類別要跟著改？

- (A) AuditPortal 與 AtmTerminal 都要改
- (B) 只有 AtmTerminal 要改
- (C) 只有實作 LoanApprovals 的類別要改
- (D) 所有類別都要重新編譯並修改

<details><summary>看答案</summary>

**答案：(C)** AuditPortal 與 AtmTerminal 沒有實作 LoanApprovals，不受影響。重構前所有類別都實作同一個大介面，加一個方法就全部要改。

</details>

**🧩 小練習：** 重構前，呼叫端拿到一個 `BankOperations` 型別的變數（實際是 AuditPortal）並呼叫 `withdraw`，問題在什麼時候才會被發現？

- (A) 寫程式時 IDE 就會標紅
- (B) 編譯時
- (C) 執行時丟出例外才發現
- (D) 永遠不會發現

<details><summary>看答案</summary>

**答案：(C)** 從型別上看 withdraw 是合法的方法，編譯器不會擋；要等執行時丟 UnsupportedOperationException。重構後 AuditReports 根本沒有 withdraw 可以呼叫。

</details>

**🧩 小練習：** ATM 終端機需要存款與提款，該實作哪一個介面？

- (A) AuditReports
- (B) LoanApprovals
- (C) CashOperations
- (D) 三個介面都要實作

<details><summary>看答案</summary>

**答案：(C)** CashOperations 只有 deposit 與 withdraw，剛好是 ATM 要的；不必為了核貸與報表寫空方法。

</details>

---

*【高層規則不該綁死在資料庫與簡訊商身上】*

## 依賴反轉原則：依賴抽象，不依賴具體

依賴反轉原則：**依賴抽象，不要依賴具體**。 [[出處]](https://web.archive.org/web/20150906155800/http://www.objectmentor.com/resources/articles/Principles_and_Patterns.pdf)

- 跟開放封閉原則的關係：開放封閉原則說的是物件導向架構的目標，依賴反轉原則說的是達成它的主要機制
- 為什麼叫「反轉」：傳統程序式設計是高層模組依賴低層模組，但高層模組處理的是應用程式的高層政策，這些政策通常不在乎實作它們的細節
- 依賴反轉之後，高層規則與低層細節都依賴中間的抽象

```java
public class DipBefore {
    public static void main(String[] args) {
        new TransferService().transfer("A-001", "B-002", 500);
    }
}

class TransferService {                                // 高層的轉帳規則，直接 new 出低層細節
    private final MySqlAccountStore store = new MySqlAccountStore();
    private final SmsSender sms = new SmsSender();

    void transfer(String from, String to, int amount) {
        store.debit(from, amount);
        store.credit(to, amount);
        sms.send(from, "您已轉出 " + amount + " 元");
    }
}

class MySqlAccountStore {
    MySqlAccountStore() { System.out.println("連線到 jdbc:mysql://prod-db/bank"); }
    void debit(String id, int amount) { System.out.println("UPDATE：" + id + " 扣 " + amount); }
    void credit(String id, int amount) { System.out.println("UPDATE：" + id + " 加 " + amount); }
}

class SmsSender {
    void send(String accountId, String text) { System.out.println("真的傳簡訊給 " + accountId + " 的手機：" + text); }
}
```

```text
連線到 jdbc:mysql://prod-db/bank
UPDATE：A-001 扣 500
UPDATE：B-002 加 500
真的傳簡訊給 A-001 的手機：您已轉出 500 元
```

轉帳規則（扣款、入帳、通知）是高層政策，卻在自己裡面 `new` 出正式資料庫與簡訊商。想單獨測試轉帳規則，一跑就連正式資料庫、傳真的簡訊。重構：

```java
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class DipAfter {
    public static void main(String[] args) {
        // 測試時：換成記憶體裡的假實作，不連資料庫、不傳簡訊
        InMemoryAccountStore store = new InMemoryAccountStore(Map.of("A-001", 1000, "B-002", 0));
        RecordingNotifier notifier = new RecordingNotifier();
        new TransferService(store, notifier).transfer("A-001", "B-002", 500);
        System.out.println("A-001 = " + store.balance("A-001") + "，B-002 = " + store.balance("B-002"));
        System.out.println("應該送出的通知：" + notifier.sent);
    }
}

interface AccountStore {                               // 抽象由高層需要什麼來決定
    void debit(String id, int amount);
    void credit(String id, int amount);
}

interface Notifier {
    void notify(String accountId, String text);
}

class TransferService {                                // 只依賴抽象；具體實作從建構子傳進來
    private final AccountStore store;
    private final Notifier notifier;

    TransferService(AccountStore store, Notifier notifier) {
        this.store = store;
        this.notifier = notifier;
    }

    void transfer(String from, String to, int amount) {
        store.debit(from, amount);
        store.credit(to, amount);
        notifier.notify(from, "您已轉出 " + amount + " 元");
    }
}

class InMemoryAccountStore implements AccountStore {
    private final Map<String, Integer> balances;
    InMemoryAccountStore(Map<String, Integer> initial) { balances = new HashMap<>(initial); }
    public void debit(String id, int amount) { balances.merge(id, -amount, Integer::sum); }
    public void credit(String id, int amount) { balances.merge(id, amount, Integer::sum); }
    int balance(String id) { return balances.get(id); }
}

class RecordingNotifier implements Notifier {
    final List<String> sent = new ArrayList<>();
    public void notify(String accountId, String text) { sent.add(accountId + "：" + text); }
}
```

```text
A-001 = 500，B-002 = 500
應該送出的通知：[A-001：您已轉出 500 元]
```

![依賴反轉示意：重構前 TransferService 的箭頭直接指向 MySqlAccountStore 與 SmsSender 兩個具體類別；重構後 TransferService 指向 AccountStore 與 Notifier 兩個介面，正式的 MySQL 實作、簡訊實作，以及測試用的記憶體實作，箭頭都往上指向這兩個介面](images/13_java-solid-antipatterns_2.svg)

*圖：* 重構前，箭頭從高層一路指到資料庫與簡訊商；重構後，具體實作的箭頭往上指向介面，這就是「反轉」的意思。測試時換成記憶體版與記錄版即可。

兩個常被混淆的詞：**依賴反轉**是設計原則（相依的方向要指向抽象），**依賴注入**（〈設計模式〉講過，把相依從外面交給物件）是實現它的一種技巧。上面是用建構子注入；Spring 的 IoC 容器（〈Spring 入門與 IoC、DI〉）就是幫你做這件事的工具。

界線：不是每個具體類別都要先包一層介面。依賴反轉假設任何具體的東西都會變動，但有例外：像 C 的 `string.h` 非常具體卻一點也不會變，依賴它無害；經過考驗、具體但不會變動的模組，依賴它們不算太糟。 [[出處]](https://web.archive.org/web/20150906155800/http://www.objectmentor.com/resources/articles/Principles_and_Patterns.pdf) 換成 Java，直接依賴 `String`、`BigDecimal` 完全沒問題；該抽象的是資料庫、外部 API、簡訊、時間這類會換、或測試時需要換掉的東西。

**🧩 小練習：** 重構前的 `TransferService` 最大的問題是什麼？

- (A) transfer 方法超過五十行太長
- (B) 完全沒有使用 static 方法
- (C) 自己 new 出正式資料庫與簡訊商
- (D) TransferService 沒有實作介面

<details><summary>看答案</summary>

**答案：(C)** 高層的轉帳規則直接依賴具體細節，一建立就連正式資料庫，一轉帳就真的傳簡訊。實跑輸出的第一行與最後一行就是證據。

</details>

**🧩 小練習：** 依賴反轉原則與開放封閉原則是什麼關係？

- (A) 兩者互相矛盾，只能二選一
- (B) 依賴反轉是目標，開放封閉是手段
- (C) 兩者是同一條原則的兩個名字
- (D) 開放封閉是目標，依賴反轉是機制

<details><summary>看答案</summary>

**答案：(D)** 開放封閉原則是目標，依賴反轉原則是主要機制。依賴抽象，才有辦法不改舊程式就換掉實作。

</details>

**🧩 小練習：** 「依賴反轉」和「依賴注入」的關係，哪一句正確？

- (A) 依賴反轉是原則，注入是技巧
- (B) 兩個詞指的是同一件事
- (C) 依賴注入是原則，依賴反轉是 Spring 功能
- (D) 用了 Spring 就自動符合依賴反轉

<details><summary>看答案</summary>

**答案：(A)** 原則講相依該指向哪裡；注入講相依怎麼交進來。用了 Spring 但到處依賴具體類別，一樣沒有符合依賴反轉。

</details>

**🧩 小練習：** 照依賴反轉的例外條件，下面哪一個**最不需要**先抽成介面？

- (A) 正式的資料庫存取程式
- (B) 外部銀行的匯率 API
- (C) 簡訊服務商的 SDK
- (D) `java.math.BigDecimal`

<details><summary>看答案</summary>

**答案：(D)** BigDecimal 很具體但幾乎不會變，依賴它無害。資料庫、外部 API、簡訊商都會換、測試時也需要換掉。

</details>

**🧩 小練習：** 重構後要做單元測試，最自然的做法是？

- (A) 測試前先啟動一台正式資料庫
- (B) 傳入記憶體版與記錄版的假實作
- (C) 用反射把 private 欄位換掉
- (D) 把 TransferService 改成 static

<details><summary>看答案</summary>

**答案：(B)** TransferService 只依賴介面，從建構子傳入假實作就好，實跑結果顯示餘額變化與該送出的通知，完全不碰外部系統。

</details>

---

*【原則是目標，模式是常見的做法】*

## 跟設計模式的關係

〈設計模式〉說過模式是「經驗的名字」。原則與模式怎麼接： [[出處]](https://web.archive.org/web/20150906155800/http://www.objectmentor.com/resources/articles/Principles_and_Patterns.pdf)

- 先有原則，再有技巧；技巧就是幫助維持應用程式相依架構的設計模式
- 照著原則做，會發現自己一再重複同樣的結構，這些重複出現的結構就叫設計模式
- 例子：程式最常依賴具體類別的地方是建立物件（抽象類別不能 new），解法是 Abstract Factory

| 原則 | 常一起出現的模式（不是一對一） | 本課的例子 |
|---|---|---|
| **開放封閉** | Strategy、Template Method、Decorator | 手續費 `FeePolicy` |
| **依賴反轉** | Abstract Factory、Factory Method，以及依賴注入 | `TransferService` 依賴 `AccountStore` |
| **介面隔離** | Adapter（把大介面轉成使用端要的小介面） | 稽核只拿 `AuditReports` |
| **單一職責** | Facade（拆開之後，對外仍給一個簡單入口） | 利息、對帳單、存檔拆成三個類別 |
| **里氏替換** | 所有靠多型的模式的前提 | 子型別要守父型別的約定 |

這張表是常見的搭配，不是規定：同一個模式可以同時服務好幾條原則，用了模式也不保證符合原則。判斷順序跟〈設計模式〉講的一樣：先找出會變的是哪一塊，再選做法。

**🧩 小練習：** 原則與設計模式的關係是？

- (A) 兩者之間沒有任何關係
- (B) 照原則做，同樣結構重複出現就是模式
- (C) 學了模式就不必再管原則
- (D) 原則只適用於 C++，模式才適用於 Java

<details><summary>看答案</summary>

**答案：(B)** 先有原則，再有維持相依架構的技巧，也就是設計模式；模式是遵循原則時一再重複出現的結構。

</details>

**🧩 小練習：** 程式最常依賴具體類別的地方是哪裡？常用哪個模式解決？

- (A) 寫日誌的地方；Observer
- (B) 建立物件的地方；Abstract Factory
- (C) 迴圈裡；Iterator
- (D) 例外處理；Chain of Responsibility

<details><summary>看答案</summary>

**答案：(B)** 要建立物件就得 new 一個具體類別，抽象類別不能 new。Abstract Factory 讓建立的動作也隔著抽象。

</details>

**🧩 小練習：** 下面哪一句對「原則與模式」的描述最不恰當？

- (A) 同一個模式可以同時服務好幾條原則
- (B) 先找出會變的地方，再選模式
- (C) 只要用了設計模式，就一定符合 SOLID
- (D) 里氏替換原則是所有靠多型的模式的前提

<details><summary>看答案</summary>

**答案：(C)** 模式用錯地方一樣會讓程式難改，例如為只有一種實作的東西套上 Strategy 加 Factory，就是下一段的過早抽象。

</details>

---

*【看起來能跑，其實在累積債務】*

## 常見反模式

**反模式**（anti-pattern）是很常見、看起來也合理，但長期會帶來麻煩的做法。下面五個都跟上面的原則有關。

### 上帝類別：什麼都管的類別

一個類別什麼都做：開戶、存提款、算利息、印報表、寄通知、寫資料庫，幾千行、幾十個欄位，大家都依賴它，誰都不敢改，這種類別常被叫做**上帝類別**（god class）。它是單一職責原則的反面：每個部門的需求都落在它身上，任何修改都可能波及別人。修法是照「誰會要求改」一塊一塊搬出去，Fowler 的重構目錄把這個動作叫 Extract Class（把一部分欄位與方法搬到新類別）。 [[出處]](https://refactoring.com/catalog/extractClass.html) 一次拆完風險很高，通常是每次碰到相關需求時順手搬一塊。

### 貧血模型對充血模型：兩派

**貧血模型**（anemic domain model）是實體只有欄位與 getter、setter，業務規則全部放在服務類別；**充血模型**（rich domain model，也叫豐富領域模型）是規則跟資料放在同一個物件裡。先看程式：

```java
public class Anemic {
    public static void main(String[] args) {
        Account a = new Account();
        a.setBalance(1000);
        new AccountService().withdraw(a, 300);
        System.out.println("透過服務提款後：" + a.getBalance());
        a.setBalance(-5000);                           // 規則寫在服務裡，誰都能繞過
        System.out.println("直接呼叫 setter 之後：" + a.getBalance());
    }
}

class Account {                                        // 只有資料：getter 與 setter
    private int balance;
    int getBalance() { return balance; }
    void setBalance(int balance) { this.balance = balance; }
}

class AccountService {                                 // 規則全部放在服務
    void withdraw(Account a, int amount) {
        if (amount <= 0 || amount > a.getBalance()) throw new IllegalArgumentException("金額不合法");
        a.setBalance(a.getBalance() - amount);
    }
}
```

```text
透過服務提款後：700
直接呼叫 setter 之後：-5000
```

```java
public class Rich {
    public static void main(String[] args) {
        Account a = new Account(1000);
        a.withdraw(300);
        System.out.println("提款後：" + a.balance());
        try {
            a.withdraw(5000);
        } catch (IllegalArgumentException e) {
            System.out.println("再提 5000：" + e.getMessage());
        }
    }
}

class Account {                                        // 資料與規則放在一起，沒有 setter 可以繞過
    private int balance;

    Account(int opening) {
        if (opening < 0) throw new IllegalArgumentException("開戶金額不可為負");
        this.balance = opening;
    }

    void withdraw(int amount) {
        if (amount <= 0 || amount > balance) throw new IllegalArgumentException("金額不合法");
        balance -= amount;
    }

    int balance() { return balance; }
}
```

```text
提款後：700
再提 5000：金額不合法
```

**反對貧血的一派**以 Fowler 為代表，2003 年把貧血模型稱為反模式： [[出處]](https://martinfowler.com/bliki/AnemicDomainModel.html)

- 這些物件只不過是一袋 getter 和 setter
- 根本的問題：完全違背物件導向設計的基本想法，也就是把資料和處理放在一起
- 更實際的問題：付出了領域模型的所有成本，卻得不到任何好處

上面實跑的 `setBalance(-5000)` 就是它的代價：規則放在服務裡，任何人都能繞過去。

**另一派**認為把資料與邏輯分開本身是正當的設計，例如 Java 語言架構師 Brian Goetz 2022 年介紹的資料導向程式設計（data-oriented programming）： [[出處]](https://www.infoq.com/articles/data-oriented-programming-java/)

- 把資料當成（不可變的）資料來建模，描述「怎麼處理這些資料」的業務邏輯分開放
- 物件導向與資料導向不互相衝突，是不同情境用的不同工具

用 Java 21 的 record 與 sealed 介面寫起來是這樣：

```java
public class Dop {
    public static void main(String[] args) {
        Account a = new Account("A-001", 1000);
        for (int amount : new int[]{300, 5000}) {
            String msg = switch (Withdrawals.withdraw(a, amount)) {
                case Withdrawals.Ok ok -> { a = ok.updated(); yield "提 " + amount + " 成功，餘額 " + a.balance(); }
                case Withdrawals.Rejected r -> "提 " + amount + " 被拒：" + r.reason();
            };
            System.out.println(msg);
        }
    }
}

record Account(String id, int balance) {               // 不可變的資料：只檢查「資料本身合不合法」
    Account {
        if (balance < 0) throw new IllegalArgumentException("餘額不可為負");
    }
}

final class Withdrawals {                              // 業務規則放在資料之外的函式
    sealed interface Result permits Ok, Rejected {}
    record Ok(Account updated) implements Result {}
    record Rejected(String reason) implements Result {}

    static Result withdraw(Account a, int amount) {
        if (amount <= 0 || amount > a.balance()) return new Rejected("金額不合法");
        return new Ok(new Account(a.id(), a.balance() - amount));
    }

    private Withdrawals() {}
}
```

```text
提 300 成功，餘額 700
提 5000 被拒：金額不合法
```

注意它跟上面的貧血版不一樣：record 不可變，沒有 setter 可以把餘額改成 -5000；結果用 sealed 介面表達，呼叫端的 switch 少處理一種會編譯失敗。

兩派其實有交集：Fowler 在同一篇文章也承認，領域模型不一定總是最好的工具。 [[出處]](https://martinfowler.com/bliki/AnemicDomainModel.html)

他在《企業應用架構模式》裡把「每個請求寫成一個程序」的做法叫 Transaction Script，跟 Domain Model 並列為兩種組織業務邏輯的方式。 [[出處]](https://martinfowler.com/eaaCatalog/transactionScript.html) [[出處]](https://martinfowler.com/eaaCatalog/domainModel.html)

實務上的判斷：

- **偏向充血模型**：規則多、彼此牽連、不變條件很重要（帳戶、額度、利率）。
- **record 加服務**：資料只是在服務之間流動、規則簡單（查詢結果、API 回應），把資料寫成 record、邏輯放在服務或函式裡也很合理。

真正要避免的是「看起來是物件、其實誰都能用 setter 亂改」的那一種。

![規則放在哪裡的三種做法：貧血模型的 Account 只有 getter 與 setter，規則在 AccountService，任何人都能直接呼叫 setter 繞過規則；充血模型的 Account 自己有 withdraw，沒有 setter；資料導向是不可變的 record 加上分開的 Withdrawals 函式，回傳 sealed 結果](images/13_java-solid-antipatterns_3.svg)

*圖：* 三種放規則的方式。爭論的焦點是「規則該不該跟資料放在一起」；三者裡只有貧血模型讓任何人都能用 setter 繞過規則。

### 過早抽象：為還沒出現的需求蓋架構

```java
public class Premature {
    public static void main(String[] args) {
        // 為了「以後可能有別種利息」先蓋好的三層：介面、工廠、唯一的實作
        InterestStrategy s = InterestStrategyFactory.create("DEFAULT");
        System.out.println("過早抽象版：" + s.monthly(12000));
        // 目前真正的需求只有一種算法
        System.out.println("直接寫版：" + monthlyInterest(12000));
    }

    static int monthlyInterest(int balance) { return balance / 100 / 12; }   // 年利率 1%
}

interface InterestStrategy { int monthly(int balance); }

class DefaultInterestStrategy implements InterestStrategy {
    public int monthly(int balance) { return balance / 100 / 12; }
}

final class InterestStrategyFactory {
    static InterestStrategy create(String type) {
        return switch (type) {
            case "DEFAULT" -> new DefaultInterestStrategy();
            default -> throw new IllegalArgumentException(type);
        };
    }
    private InterestStrategyFactory() {}
}
```

```text
過早抽象版：10
直接寫版：10
```

兩種寫法結果一樣，但第一種多了介面、工廠、字串參數三層，而目前只有一種算法。這叫**過早抽象**：為了「以後可能」先蓋好擴充點。

- **Yagni**（You Aren't Gonna Need It，你不會需要它）：預期軟體未來需要的能力，現在不應該先做；但 Yagni 不反對讓程式好改，它只有在程式容易修改時才是可行的策略 [[出處]](https://martinfowler.com/bliki/Yagni.html)
- **錯的抽象比重複更貴**：重複比錯誤的抽象便宜得多；抽象錯了，最快的前進方式是往回走，先把抽象拆回各個呼叫端 [[出處]](https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction)

這跟開放封閉原則看起來衝突，其實是同一件事的兩面：開放封閉要你在「會變的地方」留擴充點，過早抽象是在「還不知道會不會變」的地方先留。實務上常見的做法是：第一次直接寫；同樣的變化真的出現第二、三次，再抽出抽象。

### 到處 static 工具類別

```java
import java.math.BigDecimal;
import java.math.RoundingMode;

public class StaticUtil {
    public static void main(String[] args) {
        System.out.println("純函式的 static 工具：" + Money.toDollar(new BigDecimal("10500.50")));
        // 依賴外部狀態的 static：換算結果跟著「現在的匯率」走，測試沒辦法指定匯率
        System.out.println("static 版換匯：" + RateUtil.toTwd(new BigDecimal("100")));
        // 改成物件：匯率來源從外面傳進來，測試可以給固定值
        RateSource fixed = () -> new BigDecimal("32.0");
        System.out.println("注入固定匯率：" + new Exchanger(fixed).toTwd(new BigDecimal("100")));
    }
}

final class Money {                                    // 沒有狀態、同樣輸入永遠同樣輸出：static 很合適
    static BigDecimal toDollar(BigDecimal v) { return v.setScale(0, RoundingMode.HALF_UP); }
    private Money() {}
}

final class RateUtil {                                 // 藏著外部相依的 static 工具
    static BigDecimal toTwd(BigDecimal usd) {
        return usd.multiply(fetchRateFromBankApi());
    }
    private static BigDecimal fetchRateFromBankApi() {
        System.out.println("（呼叫外部匯率 API）");
        return new BigDecimal("31.85");
    }
    private RateUtil() {}
}

interface RateSource { BigDecimal usdToTwd(); }

class Exchanger {
    private final RateSource rates;
    Exchanger(RateSource rates) { this.rates = rates; }
    BigDecimal toTwd(BigDecimal usd) { return usd.multiply(rates.usdToTwd()); }
}
```

```text
純函式的 static 工具：10501
（呼叫外部匯率 API）
static 版換匯：3185.00
注入固定匯率：3200.0
```

static 方法不是壞東西。`Money.toDollar` 沒有狀態、同樣輸入永遠同樣輸出，`Math.abs` 也是這樣，寫成 static 很合適；上面資料導向那段的 `Withdrawals.withdraw` 也是。問題出在 `RateUtil` 這種**裡面藏著外部相依**的 static：呼叫端從簽章看不出它會打外部 API，測試時也沒辦法指定匯率。

- 單元測試靠的是能替換相依的「接縫」，接縫靠多型運作，而 static 方法沒有東西可以覆寫
- 例外：呼叫樹最底層、不再呼叫別人的 static 方法（leaf method）測起來沒有問題 [[出處]](https://testing.googleblog.com/2008/12/static-methods-are-death-to-testability.html)

判斷方式：純計算的放心寫成 static；碰到資料庫、網路、時間、亂數、全域狀態的，改成物件、從外面注入（就是上面的依賴反轉）。〈設計模式〉講單例「把相依藏起來」，是同一個問題。

### 吞掉例外

```java
public class Swallow {
    public static void main(String[] args) {
        AccountStore store = new AccountStore();
        System.out.println("吞掉版本：" + new SilentTransfer(store).transfer("A-001", 500));
        try {
            new HonestTransfer(store).transfer("A-001", 500);
        } catch (TransferFailedException e) {
            System.out.println("不吞版本：" + e.getMessage() + "；原因：" + e.getCause().getMessage());
        }
    }
}

class AccountStore {
    void debit(String id, int amount) {
        throw new IllegalStateException("資料庫連線逾時");   // 模擬底層失敗
    }
}

class SilentTransfer {
    private final AccountStore store;
    SilentTransfer(AccountStore store) { this.store = store; }

    String transfer(String from, int amount) {
        try {
            store.debit(from, amount);
        } catch (Exception e) {
            // 什麼都不做
        }
        return "轉帳成功";                             // 錢根本沒扣，卻回報成功
    }
}

class TransferFailedException extends Exception {
    TransferFailedException(String message, Throwable cause) { super(message, cause); }
}

class HonestTransfer {
    private final AccountStore store;
    HonestTransfer(AccountStore store) { this.store = store; }

    String transfer(String from, int amount) throws TransferFailedException {
        try {
            store.debit(from, amount);
        } catch (IllegalStateException e) {
            throw new TransferFailedException("轉帳失敗：" + from + " 扣款 " + amount + " 元", e);   // 補上情境、保留原因
        }
        return "轉帳成功";
    }
}
```

```text
吞掉版本：轉帳成功
不吞版本：轉帳失敗：A-001 扣款 500 元；原因：資料庫連線逾時
```

吞掉版本的 catch 什麼都不做，錢根本沒扣，卻回報「轉帳成功」。這比直接當掉更糟：錯誤被藏起來，之後的帳對不起來，也找不到原因。〈例外機制〉講過不要為了讓程式看起來沒壞就寫空的 catch；不吞版本照那課的做法：補上情境（哪個帳戶、多少錢）、把原本的例外當 cause 傳下去。為什麼要包一層而不是直接往外丟：上層的操作因為下層失敗而失敗時，讓下層丟出的例外直接往外傳是不好的設計，因為它通常跟上層提供的抽象無關。 [[出處]](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Throwable.html) 在 Spring 裡吞掉例外還有另一個後果：例外到不了交易攔截器，交易照常提交（〈Spring 面試快答：IoC、Bean、AOP 與交易〉）。

**🧩 小練習：** 一個 `BankService` 類別有 4000 行，開戶、存提款、利息、報表、通知、資料庫存取全在裡面。它最直接違反哪一條原則？

- (A) 單一職責原則
- (B) 里氏替換原則
- (C) 介面隔離原則
- (D) 沒有違反，只是比較長

<details><summary>看答案</summary>

**答案：(A)** 每個部門的需求都落在同一個類別，這是上帝類別，也就是單一職責原則的反面。修法是一塊一塊 Extract Class。

</details>

**🧩 小練習：** 貧血版的實跑輸出中，`a.setBalance(-5000)` 之後餘額變成多少？這說明了什麼？

- (A) 還是 700，setter 會檢查
- (B) 丟出例外，程式中止
- (C) 0，Java 自動把負數改 0
- (D) -5000，setter 繞過了規則

<details><summary>看答案</summary>

**答案：(D)** Account 只有 setter，不檢查任何規則；只有走 AccountService 才會檢查。這是 Fowler 批評貧血模型的實際代價。

</details>

**🧩 小練習：** 關於貧血模型，這課的立場是？

- (A) 兩派：反模式，或正當的分開設計
- (B) 一定是錯的，所有規則都要放進實體
- (C) 一定是對的，實體只該放資料
- (D) 兩派都同意貧血模型最好

<details><summary>看答案</summary>

**答案：(A)** Fowler 批評它違背「資料與處理放在一起」；Goetz 的資料導向主張不可變資料加分開的邏輯，並說兩種做法是不同情境的工具。兩派都反對「誰都能用 setter 亂改」。

</details>

**🧩 小練習：** 資料導向版本跟貧血版本都把規則放在資料之外，最大的差別是什麼？

- (A) 資料導向版本的執行速度比較快
- (B) 資料導向版本不需要寫規則
- (C) 兩者其實完全一樣
- (D) record 不可變，不能繞過規則

<details><summary>看答案</summary>

**答案：(D)** record 的欄位不能改，要改餘額只能透過 Withdrawals.withdraw 拿到新的 Account；結果用 sealed 介面表達，少處理一種情況編譯器會提醒。

</details>

**🧩 小練習：** 只有一種利息算法，卻先寫了 `InterestStrategy` 介面、`InterestStrategyFactory` 與唯一的實作。這屬於哪一種反模式？

- (A) 上帝類別
- (B) 過早抽象
- (C) 吞掉例外
- (D) 貧血模型

<details><summary>看答案</summary>

**答案：(B)** 為了還沒出現的需求先蓋三層結構，結果跟直接寫一樣。Yagni：現在不需要的能力，現在不要做。

</details>

**🧩 小練習：** 抽象做錯了，建議怎麼處理？

- (A) 拆回各呼叫端，先接受重複
- (B) 再多加一層抽象把它整個包起來
- (C) 加更多參數讓它支援新需求
- (D) 改寫成 static 工具類別

<details><summary>看答案</summary>

**答案：(A)** 重複比錯誤的抽象便宜得多，抽象錯了最快的前進方式是往回走。硬改錯的抽象，只會變成充滿條件判斷的程序。

</details>

**🧩 小練習：** 下面哪一個寫成 static 方法**最合適**？

- (A) 查詢目前匯率並換算成台幣金額
- (B) 把 BigDecimal 四捨五入到元
- (C) 寫一筆交易紀錄進資料庫
- (D) 取得現在時間判斷是否營業中

<details><summary>看答案</summary>

**答案：(B)** 四捨五入沒有狀態、同樣輸入同樣輸出，測起來沒問題。另外三個碰到外部 API、資料庫、時間，寫成 static 測試時就換不掉。

</details>

**🧩 小練習：** 吞掉例外的版本，實跑時回傳什麼？

- (A) 丟出 IllegalStateException
- (B) 轉帳成功
- (C) 轉帳失敗
- (D) null

<details><summary>看答案</summary>

**答案：(B)** catch 什麼都沒做，方法照常往下走回傳「轉帳成功」，但扣款其實失敗了。錯誤被藏起來，比直接失敗更難查。

</details>

---

*【每條一句話、一個例子、一個界線】*

## 面試怎麼講

建議的回答方式：每一條講「一句話定義、一個自己的例子、一個界線」，比背英文全名有說服力。

| 原則 | 一句話 | 例子 | 界線 |
|---|---|---|---|
| **單一職責** | 只因為一群人的需求而改 | 利息、對帳單、存檔拆開 | 不是一個類別一個方法 |
| **開放封閉** | 新增功能靠擴充，不改舊程式 | 手續費策略 | 只對你預期的那種變化封閉 |
| **里氏替換** | 子型別要守父型別的約定 | 定存不該繼承可提款帳戶 | 看的是約定，不是 extends |
| **介面隔離** | 照使用端切介面 | 稽核只拿報表介面 | 不是一個方法一個介面 |
| **依賴反轉** | 高層規則依賴抽象 | 轉帳服務依賴 AccountStore | 穩定的具體類別可以直接用 |

常見的追問與回答方向：

- **「SOLID 一定要遵守嗎？」**它們是原則不是規定，目的是讓程式好改；硬套會多出不需要的抽象（過早抽象），所以要看哪裡真的會變。
- **「依賴反轉和依賴注入差在哪？」**前者是原則（相依指向抽象），後者是技巧（相依從外面交進來）；Spring 是做注入的工具。
- **「舉一個違反里氏替換原則的例子。」**Martin 文章裡的例子是圓形繼承橢圓（橢圓的使用端可以預期「設定兩個焦點之後，讀回來就是剛設的那兩個點」，圓形為了保持兩個焦點重合守不住這個約定），本課的例子是定存繼承可提款帳戶；重點是講出「哪一個約定被打破」。
- **「貧血模型好不好？」**講兩派：Fowler 認為是反模式，資料導向認為資料與邏輯分開是正當的；再講自己的判斷依據（規則多寡、不變條件重不重要）。

**🧩 小練習：** 面試官問「SOLID 一定要遵守嗎？」，下面哪個回答最好？

- (A) 一定要遵守，違反的就是錯誤的程式
- (B) 不用，那是已經過時的觀念
- (C) 只有大型專案才需要遵守
- (D) 原則，不是規定；硬套會過早抽象

<details><summary>看答案</summary>

**答案：(D)** 原則不是規定。回答時講出目的（好改）與代價（多餘的抽象），比非黑即白的答案更有說服力。

</details>

**🧩 小練習：** 回答「舉一個違反里氏替換原則的例子」時，最關鍵要講出什麼？

- (A) 那個子類別總共用了幾次 extends
- (B) 子類別打破了父型別的哪一個約定
- (C) 子類別有幾個方法
- (D) 那個類別是哪一年寫的

<details><summary>看答案</summary>

**答案：(B)** 里氏替換看的是約定：前置條件變強或後置條件變弱。講出「父類別承諾什麼、子類別哪裡沒做到」，例子才算講對。

</details>

**🧩 小練習：** 用「一句話、一個例子、一個界線」講開放封閉原則，下面哪個界線講得最對？

- (A) 所有類別都要設成 final
- (B) 代表程式永遠不需要修改
- (C) 只對選定的那種變化封閉
- (D) 只能用繼承來擴充

<details><summary>看答案</summary>

**答案：(C)** 手續費例子對「新增帳戶類型」封閉，但「每種帳戶多一種費用」還是要改介面與所有實作。擴充也不一定要靠繼承，實作介面同樣可以。

</details>

### 重點整理

- SOLID 是五個讓程式在需求改變時好改的設計原則，不是編譯器會檢查的規定；每一條都有界線，硬套會變成過早抽象。原則是目標，設計模式是遵循原則時一再出現的做法：Strategy 對應開放封閉、Abstract Factory 與依賴注入對應依賴反轉。
- 單一職責：一個類別只該因為一群人的需求而改（這個原則講的是人）；拆的依據是「誰會要求改」，不是方法數量。
- 開放封閉：新增功能靠擴充、不改舊程式，關鍵是抽象；只對你選定的那種變化封閉。
- 里氏替換：子型別放進父型別的位置要照常運作；前置條件不能變強、後置條件不能變弱。extends 寫得出來不代表語意上是子型別；違反它，呼叫端就會冒出 instanceof 判斷。
- 介面隔離：照使用端切介面，不逼別人實作用不到的方法；也不是一個方法一個介面。
- 依賴反轉：高層規則與低層細節都依賴抽象；依賴注入是實現它的技巧。穩定的具體類別（String、BigDecimal）可以直接依賴。
- 反模式：上帝類別（違反單一職責）、貧血模型（兩派，共同反對 setter 亂改）、過早抽象（Yagni、重複比錯的抽象便宜）、藏著外部相依的 static 工具、吞掉例外（補上情境、保留 cause）。

---

## 隨堂測驗

**Q1. 單一職責原則的「一個理由」最好怎麼理解？**

- (A) 每個類別最多只能有一個公開方法
- (B) 每個類別都要有對應的介面
- (C) 每個方法的程式碼不能超過十行
- (D) 修改要求只來自同一群業務的人

<details><summary>看答案</summary>

**答案：(D)** 這個原則講的是人：修改要求應該只來自代表單一業務功能的那群人。方法數與行數不是判斷標準。

</details>

**Q2. 一個 Account 類別同時算利息、印對帳單、存資料庫，三者共用一個捨入小工具。財務部要求改利息的捨入方式，最可能發生什麼？**

- (A) 資料庫連線中斷
- (B) 整個專案編譯失敗
- (C) 對帳單也跟著變
- (D) 只有利息會改變，其他不受影響

<details><summary>看答案</summary>

**答案：(C)** 三個職責綁在同一個小工具上，改給財務部用的捨入方式，營運部的對帳單也跟著變。本課實跑：餘額從 10501 變成 10500。

</details>

**Q3. 手續費原本用 switch 判斷帳戶類型。照開放封閉原則，新增「VIP 戶」最理想的做法是？**

- (A) 在 switch 裡多加一個 case
- (B) 複製一份計算手續費的類別再改
- (C) 在呼叫端加 if 判斷是不是 VIP 戶
- (D) 新增實作 FeePolicy 的類別

<details><summary>看答案</summary>

**答案：(D)** 依賴 FeePolicy 這個抽象之後，新增類型只要加類別，既有的 TransferService 不用改。加 case 或 if 都是在改舊程式。

</details>

**Q4. 里氏替換原則的原始定義用什麼判斷 S 是不是 T 的子型別？**

- (A) S 的類別宣告有寫 extends T
- (B) S 的方法名稱與參數都跟 T 一樣
- (C) S 的欄位數量比 T 還多
- (D) 換成 S 之後程式行為不變

<details><summary>看答案</summary>

**答案：(D)** 定義的重點是：所有以 T 定義的程式，把物件換成 S 的之後行為不變。子類別只是語法概念，子型別才是語意關係。

</details>

**Q5. 定存繼承一般帳戶，覆寫 withdraw 改成「沒到期一律丟例外」。問題在哪？**

- (A) 方法名稱跟父類別不一樣
- (B) 存取權限比父類別更開放
- (C) 前置條件變強
- (D) 後置條件變強，提供得比父類別多

<details><summary>看答案</summary>

**答案：(C)** 父類別只要求金額不超過餘額，定存多要求已到期。子類別要求不能更多，提供不能更少。

</details>

**Q6. 稽核入口被一個大介面逼著實作 withdraw、approveLoan，只能丟 UnsupportedOperationException。最合適的修法是？**

- (A) 在每個方法裡改成什麼都不做
- (B) 把整個介面改成抽象類別
- (C) 照使用端把大介面拆小
- (D) 讓稽核入口改繼承 ATM 的類別

<details><summary>看答案</summary>

**答案：(C)** 介面隔離原則：替每一種使用端建立專屬的介面。改成空方法會讓錯誤更難發現；換成抽象類別一樣把所有方法塞在一起。

</details>

**Q7. 「依賴反轉」與「依賴注入」的關係，哪一句正確？**

- (A) 前者是原則，後者是技巧
- (B) 依賴反轉是 Spring 才有的功能
- (C) 兩個詞指的是同一件事
- (D) 用了依賴注入就一定符合依賴反轉

<details><summary>看答案</summary>

**答案：(A)** 依賴反轉講相依該指向抽象；依賴注入講相依從外面交進來。注入一個具體類別，一樣沒有依賴抽象。

</details>

**Q8. 關於貧血模型，下面哪一句最符合這課的說法？**

- (A) 資料導向主張把規則全塞進實體
- (B) 兩派各有道理，都反對 setter 亂改
- (C) Fowler 認為它是最好的設計
- (D) 所有專家都同意它一定是錯的

<details><summary>看答案</summary>

**答案：(B)** Fowler 認為貧血模型違背資料與處理放在一起；Goetz 的資料導向主張不可變資料加分開的邏輯。兩派都反對可以用 setter 繞過規則的物件。

</details>

**Q9. 只有一種利息算法，卻先寫好介面、工廠與唯一的實作。這是哪一種反模式？該怎麼處理？**

- (A) 上帝類別；把類別拆成更多個小類別
- (B) 過早抽象；重複比錯的抽象便宜
- (C) 吞掉例外；把例外重新丟出去
- (D) 貧血模型；把規則放回實體裡

<details><summary>看答案</summary>

**答案：(B)** 為還沒出現的需求先蓋擴充點就是過早抽象。重複比錯誤的抽象便宜得多，抽象錯了就先拆回去。

</details>

**Q10. catch 區塊什麼都不做，轉帳方法照常回傳「轉帳成功」。比較好的寫法是？**

- (A) 補上情境、帶著原因重新丟出
- (B) 改成接 Throwable 再忽略
- (C) 在 catch 裡印一行日誌就好
- (D) 把 catch 區塊整個換成 finally

<details><summary>看答案</summary>

**答案：(A)** 吞掉例外會把失敗藏起來。照〈例外機制〉的做法：補上哪個帳戶、多少錢，並把原本的例外當 cause 傳下去；讓下層例外直接往外傳本來就是不好的設計。

</details>
