# 06. Spring AOP 與交易控制

> 🏠 **生活化版本**：每個段落開頭的「生活比喻」先用日常情境帶你抓到感覺，接著再看原本的技術說明與程式碼；篇末有「比喻對照表」可以快速複習。

> 來源：[筆記平台 · Spring 後端](https://hhtim.github.io/notes-platform/spring/#/lesson/spring-aop-tx)　第 6 課 / 共 23 課 · 約 11 分鐘

**用切面集中處理橫跨多個功能的共同邏輯，並建立可靠的宣告式交易邊界。**

### 讀完這課你會

*   分辨商業邏輯與橫切關注點
*   看懂切面、切入點、通知與代理物件各自負責什麼
*   依時機選擇 Before、After、Around 等通知
*   用宣告式交易劃出正確的交易邊界，並知道代理機制的限制

*【共同功能不該散在各處】*

## AOP 解決的是橫切問題

> 🏠 **生活比喻**
>
> 日誌、權限、交易這些事**每個功能都要做**，像**每間店都要有監視器和保全**。AOP 就是**統一由保全公司處理**，不用每家店自己請。

會員註冊、下單、修改資料屬於商業邏輯；日誌、執行時間、權限檢查與交易控制則會同時出現在很多功能裡。後者像一條橫跨各個房間的消防管線，所以叫橫切關注點（cross-cutting concern）。

如果每個方法都自己複製一份計時或日誌程式碼，不只難讀，規則一改還很容易漏改。舉個例子：本來 `print()` 只要印出訊息，為了記錄執行時間塞進一堆計時程式碼；換一台印表機，同樣的計時程式碼又要再複製一次。

切面導向程式設計（Aspect-Oriented Programming，AOP）把這些共同邏輯抽出來，再套用到符合條件的方法上。

> AOP 是用來補充物件導向設計的，不是把所有商業邏輯都搬進切面。

*【先認識幾個角色】*

## 切面、連接點、切入點、通知與代理

> 🏠 **生活比喻**
>
> - 切面（Aspect）＝**保全公司**
> - 連接點＝**可以派保全站崗的地方**（每個方法呼叫）
> - 切入點＝**實際決定要站崗的地點清單**
> - 通知（Advice）＝**保全要做的事**（檢查證件、記錄進出）
> - 代理＝**站在門口的保全本人**，客人其實是先碰到他

*   **切面（Aspect）**：集中放共同功能的模組，例如計時切面。
*   **連接點（Join Point）**：程式執行中可以套用額外行為的位置；Spring AOP 主要處理方法執行。
*   **切入點（Pointcut）**：描述哪些連接點要被選中。
*   **通知（Advice）**：在選中的位置，什麼時候、怎麼執行共同邏輯。
*   **代理（Proxy）**：包在目標物件外層的替身，先攔下呼叫，再安排通知與目標方法。

代理可以想成大樓櫃檯：訪客以為自己直接在找住戶，但會先經過櫃檯登記與檢查，再由櫃檯放行。

*【讓切面在對的時機介入】*

## 常見的通知類型

> 🏠 **生活比喻**
>
> - `@Before`＝**進門前檢查**
> - `@After`＝**離開時登記**
> - `@AfterReturning`＝**順利辦完事才登記**
> - `@AfterThrowing`＝**出事時通報**
> - `@Around`＝**全程陪同**，連要不要讓你進去都能決定

| 通知 | 執行時機 | 適合做什麼 |
| --- | --- | --- |
| `@Before` | 目標方法執行前 | 前置檢查、記錄輸入摘要 |
| `@After` | 目標方法結束後，不論正常或丟出例外 | 一定要做的收尾紀錄 |
| `@AfterReturning` | 目標方法正常回傳後 | 記錄成功結果 |
| `@AfterThrowing` | 目標方法丟出例外後 | 失敗稽核、例外紀錄 |
| `@Around` | 包住整次方法呼叫 | 計時、重試，或需要決定要不要繼續執行的情況 |

`@Around` 的權限最大，也最容易用錯。它必須呼叫 `ProceedingJoinPoint.proceed()` 才會繼續執行目標方法，而且要正確回傳結果或把例外傳出去。

`@After` 常被說成「在切入點的方法被呼叫後執行」。更精確的說法是：它像 `finally`，方法丟出例外時一樣會執行。

*【動手做一個計時切面】*

## 切入點要精準，切面本身也得是 Bean

> 🏠 **生活比喻**
>
> 切入點寫太廣像**派保全到每個房間包括廁所**，浪費又干擾；切面類別本身也要**登記在物流中心**（是 Bean），不然保全公司根本沒開工。

```
@Aspect
@Component
public class TimingAspect {
    @Around("execution(* com.example.service..*(..))")
    public Object measure(ProceedingJoinPoint joinPoint) throws Throwable {
        long start = System.nanoTime();
        try {
            return joinPoint.proceed();
        } finally {
            long elapsed = System.nanoTime() - start;
            log.info("{} 花了 {} 奈秒", joinPoint.getSignature(), elapsed);
        }
    }
}
```

`@Aspect` 宣告這個類別是切面，`@Component` 讓 Spring 管理它——兩個註解要一起加，因為切面本身不是 Bean 就不會生效。範例的切入點表示選取 `com.example.service` 套件及其子套件裡的方法，其中的 `*` 是任意回傳型別。

切入範圍太寬會攔到不該被影響的方法，太窄又會漏掉目標。切入點應該搭配套件、類別、方法或自訂註解把意圖講清楚。

*【代理機制帶來的邊界】*

## 寫了註解不一定會被攔截

> 🏠 **生活比喻**
>
> 保全站在**大門**（代理）。如果是**店內員工自己走到隔壁房間**（同一個類別內部呼叫自己的方法），沒經過大門，保全就攔不到。

Spring AOP 建代理有兩條路，JDK 動態代理或 CGLIB：

*   目標物件有實作介面：用 JDK 動態代理（Java SE 的 Reflection/Proxy API）
*   沒有實作任何介面：建立 CGLIB 代理，也就是在執行期產生目標型別的子類別。CGLIB 是一個在執行期直接產生子類別位元組碼的函式庫，Spring 已把它打包進 spring-core

不過「有介面就用 JDK 動態代理」這條規則只在 `spring.aop.proxy-target-class` 是 `false` 時成立。Spring Boot 2.0 起把它預設成 `true`，AOP 也預設用 CGLIB 代理，所以 Spring Boot 專案不論有沒有介面都走 CGLIB[出處](https://docs.spring.io/spring-framework/reference/core/aop/proxying.html)[預設值](https://docs.spring.io/spring-boot/appendix/application-properties/index.html)[2.0 起](https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-2.0-Migration-Guide)。

不論哪一種代理，攔截的都是「從外部進入 Bean」的呼叫。如果同一個物件裡的 A 方法直接呼叫自己的 B 方法，這次呼叫沒有經過代理，B 上的 AOP 行為就不會生效。這個狀況叫自我呼叫（self-invocation）。

常見的改善方式是重新切分 Bean，讓呼叫真的跨過代理邊界。不要為了繞過設計問題，到處自己去拿代理物件。

*【交易是一組不能拆散的操作】*

## 提交、還原與 ACID

> 🏠 **生活比喻**
>
> 交易像**轉帳**：扣款和入帳要嘛都成功（commit），要嘛都取消（rollback），不能只做一半。

交易（transaction）把多個資料庫操作當成一個工作單位。轉帳要先扣款再入帳：兩步都成功才提交（commit），中途失敗就還原（rollback），避免只做一半。

| ACID 特性 | 意義 |
| --- | --- |
| 原子性（Atomicity） | 整組操作全部完成，否則全部不算。 |
| 一致性（Consistency） | 交易前後都符合資料規則。 |
| 隔離性（Isolation） | 並行交易之間互相影響的程度受控制。 |
| 持久性（Durability） | 提交之後的結果能持續保存。 |

ACID 與交易控制語法（COMMIT、ROLLBACK、SAVEPOINT）的完整說明見〈SQL 三種子語言：DDL、DML、DQL〉。

隔離層級用來在一致性與並行效能之間取捨。等級放得越寬，下面這三種「讀到怪東西」的情況就越可能發生：

*   **髒讀（dirty read）**：讀到另一筆交易改了、但還沒提交的資料。那筆交易如果後來還原，你讀到的就是一個從來沒存在過的值。
*   **不可重複讀（non-repeatable read）**：同一筆交易裡對同一列讀兩次，結果不一樣——中間被另一筆交易改掉並提交了。
*   **幻讀（phantom read）**：同一個查詢條件跑兩次，第二次多出或少掉幾列——中間有人新增或刪除了符合條件的資料。

*【交給 Spring 管理交易邊界】*

## 用 @Transactional 宣告交易

> 🏠 **生活比喻**
>
> `@Transactional` 像**在工作單上蓋「整單作業」的章**，保全（代理）看到章就自動幫你開始和結束交易，不用自己寫開始、提交、還原。

程式化交易是在程式碼裡手動開始、提交與還原；宣告式交易則是描述哪些方法需要交易，再由 Spring 透過 AOP 與交易管理器處理。

程式化交易到現在仍是官方正式支援的做法，有兩種方式：命令式流程一般建議用 `TransactionTemplate`，反應式程式碼用 `TransactionalOperator`。它不是被淘汰，只是一般服務在多數情境下會先選宣告式交易[出處](https://docs.spring.io/spring-framework/reference/data-access/transaction/programmatic.html)。

> 📝 查證更正：原筆記寫程式化交易是「較舊的使用方式,現今Spring已不使用」，查證後更正：程式化交易到現在仍是 Spring 官方正式支援的做法，官方文件為它保留專章，並提供 TransactionTemplate 與反應式的 TransactionalOperator；只是一般服務在多數情境下會先選宣告式交易

```
@Service
public class TransferService {
    @Transactional
    public void transfer(long fromId, long toId, BigDecimal amount) {
        accountDao.withdraw(fromId, amount);
        accountDao.deposit(toId, amount);
    }
}
```

`@Transactional` 可以放在類別或方法上。交易邊界通常放在服務層，因為一件商業操作往往要協調好幾個 DAO。如果只在各個 DAO 方法上各開一個交易，整件商業操作就被切成好幾段，失去「一起成功或一起失敗」的意義。

`@Transactional` 預設只在 `RuntimeException` 或 `Error` 時還原，受檢的 `Exception` 不會觸發還原；要讓受檢例外也還原，得自己設 `rollbackFor`[出處](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html)。所以不要只憑「有丟例外」就假設一定還原。

> 📝 查證更正：原筆記寫「發生例外、邏輯不合理 => Rollback」，等於說任何例外都還原；查證後更正：Spring 的宣告式交易預設只對 RuntimeException 與 Error 還原，受檢例外（checked exception）預設不還原，照原筆記的假設去寫會漏還原，要還原得自己設定 rollbackFor

*【交易也受代理限制】*

## 避免 @Transactional 看得到卻攔不到

> 🏠 **生活比喻**
>
> 蓋了章卻沒效的常見原因：**方法是 private**（保全看不到）、**同類別自己呼叫自己**（沒經過大門）、**例外被你吞掉**（保全不知道出事）。

宣告式交易同樣靠代理，所以要從外部呼叫受管理 Bean 的交易方法，才會經過交易攔截器。自我呼叫、自己手動 `new` 出服務物件，或把交易邊界放錯層，都會讓設定失效。

> 💡 想一下：如果 `checkout()` 先寫入訂單，再呼叫庫存 DAO，而扣庫存失敗了，哪一層最適合包住整個交易？

答案通常是協調「建單加扣庫存」的那個服務方法，因為只有它掌握完整的商業工作單位。

### 🗺️ 比喻對照表

| 技術名詞 | 生活比喻 |
| --- | --- |
| AOP | 統一請保全公司 |
| Aspect / Advice | 保全公司 / 保全要做的事 |
| Pointcut | 站崗地點清單 |
| 代理 | 站在門口的保全 |
| @Around | 全程陪同 |
| 自我呼叫失效 | 店內走動沒經過大門 |
| @Transactional | 蓋「整單作業」章 |

### 重點整理

*   AOP 把日誌、計時、交易這類橫切關注點集中管理。
*   切入點決定套用位置，通知決定執行時機，代理負責攔截呼叫。
*   Spring AOP 有 JDK 動態代理與 CGLIB 兩種，Spring Boot 預設走 CGLIB。
*   `@Around` 必須呼叫 `proceed()`，並處理好回傳值與例外。
*   宣告式交易預設只對執行期例外還原，受檢例外要自己設 `rollbackFor`。
*   交易邊界放在能涵蓋完整商業操作的服務層，並要留意自我呼叫會繞過代理。

## 隨堂測驗

**Q1. 下列哪一項最符合橫切關注點？**

- (A) 很多服務都需要的執行時間紀錄
- (B) 會員註冊時建立會員資料
- (C) 計算購物車商品總價
- (D) 依訂單內容扣除庫存

<details><summary>看答案</summary>

**答案：(A)** 執行時間紀錄會橫跨多個商業功能，適合抽成切面。

</details>

**Q2. AOP 裡的切入點負責什麼？**

- (A) 描述哪些方法執行的位置要套用通知
- (B) 保存資料庫交易的實際資料
- (C) 建立 HTTP 回應本體
- (D) 把查詢結果對映成實體

<details><summary>看答案</summary>

**答案：(A)** 切入點負責從所有連接點裡挑出要被攔截的那些。

</details>

**Q3. 只想在目標方法正常完成後記錄成功結果，適合用哪種通知？**

- (A) @AfterReturning
- (B) @After
- (C) @Before
- (D) @AfterThrowing

<details><summary>看答案</summary>

**答案：(A)** @AfterReturning 只在正常回傳後執行；@After 不論成功失敗都會執行。

</details>

**Q4. @Around 通知如果沒有呼叫 ProceedingJoinPoint.proceed()，通常會發生什麼事？**

- (A) 目標方法不會被執行
- (B) 目標方法會自動執行兩次
- (C) 交易會立即提交
- (D) 切面會自動變成 @Before

<details><summary>看答案</summary>

**答案：(A)** Around 包住整次呼叫，要主動 proceed() 才會往下走。

</details>

**Q5. 關於 Spring AOP 的代理機制，哪一項正確？**

- (A) 有 JDK 動態代理與 CGLIB 兩種，Spring Boot 預設用 CGLIB
- (B) 只有 JDK 動態代理一種，所以目標類別一定要有介面
- (C) 代理是在編譯期把程式碼織進位元組碼
- (D) 代理只能用在資料庫連線物件上

<details><summary>看答案</summary>

**答案：(A)** 有沒有介面會影響代理型態，Spring Boot 自 2.0 起預設把 proxyTargetClass 設為 true。

</details>

**Q6. 為什麼同一個 Bean 內部的方法自我呼叫可能不會觸發 Spring AOP？**

- (A) 這個呼叫沒有經過 Spring 建立的代理物件
- (B) Java 不允許同類別的方法互相呼叫
- (C) @Aspect 只能套用在資料庫連線
- (D) 自我呼叫會被編譯器改成靜態方法

<details><summary>看答案</summary>

**答案：(A)** 代理只攔得到從外部進入 Bean 的呼叫，物件內部的直接呼叫繞過它。

</details>

**Q7. 轉帳的扣款成功但入帳失敗，交易通常應該怎麼處理？**

- (A) 還原整筆交易，不要只完成扣款
- (B) 提交扣款並忽略入帳
- (C) 只重新序列化回應
- (D) 改回傳較低的 HTTP 狀態碼

<details><summary>看答案</summary>

**答案：(A)** 轉帳是一個不可拆分的工作單位，任一步失敗都應該還原。

</details>

**Q8. 為什麼 @Transactional 常放在服務層方法上？**

- (A) 服務層能涵蓋一件商業操作涉及的多個資料存取步驟
- (B) 服務層會自動把所有例外轉成 JSON
- (C) DAO 無法參與任何資料庫交易
- (D) Controller 不能呼叫服務層

<details><summary>看答案</summary>

**答案：(A)** 交易邊界要包住完整的商業操作，而協調多個 DAO 的正是服務層。

</details>

**Q9. 某個加了 @Transactional 的方法丟出一個受檢例外，預設會發生什麼事？**

- (A) 交易不會還原，除非另外設定 rollbackFor
- (B) 交易一定會還原
- (C) 交易會被重試三次
- (D) Spring 會自動把它轉成 RuntimeException

<details><summary>看答案</summary>

**答案：(A)** Spring 宣告式交易預設只對 RuntimeException 與 Error 還原。

</details>
