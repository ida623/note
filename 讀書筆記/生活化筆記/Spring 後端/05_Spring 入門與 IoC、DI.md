# 05. Spring 入門與 IoC、DI

> 🏠 **生活化版本**：每個段落開頭的「生活比喻」先用日常情境帶你抓到感覺，接著再看原本的技術說明與程式碼；篇末有「比喻對照表」可以快速複習。

> 來源：[筆記平台 · Spring 後端](https://hhtim.github.io/notes-platform/spring/#/lesson/spring-ioc)　第 5 課 / 共 23 課 · 約 11 分鐘

**理解 Spring 如何集中管理物件，並以依賴注入把類別之間的綁定程度降下來。**

### 讀完這課你會

*   看出「在類別裡直接 new 相依物件」會造成什麼問題
*   說明控制反轉與依賴注入的關係
*   用元件掃描或 Java 組態建立 Bean，並在有多個候選者時指定要哪一個
*   讀取設定檔的值，並分辨 `${...}` 與 `#{...}`

*【先從綁太緊講起】*

## 為什麼不該到處直接 new？

> 🏠 **生活比喻**
>
> 到處 `new` 像**每家餐廳都自己養雞、種菜**：想換供應商就要拆掉雞舍。讓別人供貨，換供應商只要換一通電話。

假設 `MemberService` 在類別裡直接寫 `new MemberDaoImpl()`。這就像店長把某一家供應商的電話焊死在櫃檯上：想換供應商時，不只換供應端，連店長的流程也得改。

```
public class MemberService {
    private MemberDao memberDao = new MemberDaoImpl();
}
```

此時 `MemberService` 同時負責商業邏輯與相依物件的建立，而且直接知道具體的實作類別。要換另一種 DAO、要在測試裡放替身，或要調整建構方式，使用端都得跟著改。

改善方向是讓使用端依賴介面這類抽象型別，再由外部決定實際要給哪一個物件。這種降低類別之間綁定程度的設計叫鬆耦合（loose coupling）。

*【把建立物件的責任交出去】*

## IoC、DI 與 Spring 容器

> 🏠 **生活比喻**
>
> - IoC 控制反轉＝**不是你自己去買食材，而是供應商送到你門口**
> - DI 依賴注入＝**送貨這個動作**
> - Spring 容器＝**中央廚房兼物流中心**，負責準備所有物件（Bean）並送到需要的地方

控制反轉（Inversion of Control，IoC）是把物件的建立、組裝與生命週期的控制權，從應用程式交給容器。過去由類別自己 `new`；改用 IoC 之後，由 Spring 的 IoC 容器把物件準備好。

由 Spring 容器管理的物件叫 Bean。容器負責它的實例化、相依關係組裝、初始化，以及容器關閉時的銷毀處理。

依賴注入（Dependency Injection，DI）是實作 IoC 最常見的方式：容器把某個物件需要的相依物件送進去，像中央廚房把備好的食材送到各工作站。

| 名詞 | 重點 |
| --- | --- |
| IoC | 一種設計原則：把物件控制權交給外部容器。 |
| DI | 一種實作方式：由外部注入物件需要的相依項目。 |
| Bean | 由 Spring 容器建立與管理的物件。 |
| ApplicationContext | 常用的 Spring 容器介面，除了管理 Bean 還提供其他應用功能。 |

IoC 的實作方式不只 DI，還有 DL（Dependency Lookup，依賴查找）與 Service Locator；Java EE Web 容器提供的 JNDI 就是 DL 的一種實作。Spring 主要走的是 DI 這條路。

*【讓相依關係看得見】*

## 必要的相依優先用建構子注入

> 🏠 **生活比喻**
>
> 建構子注入像**開店前就要求所有必備設備到位**：沒有爐子就不准開店，避免開店後才發現少東西；也方便測試時換成假的設備。

相依物件可以透過建構子、setter 或欄位注入。對「非有不可」的相依來說，建構子注入通常最清楚：物件一建立就必須拿到完整相依，也方便在單元測試裡直接把替身傳進去。

```
public interface MemberDao {
    Member findById(long id);
}

@Repository
public class JdbcMemberDao implements MemberDao {
    // 資料存取實作
}

@Service
public class MemberService {
    private final MemberDao memberDao;

    public MemberService(MemberDao memberDao) {
        this.memberDao = memberDao;
    }
}
```

`@Component` 以及語意更明確的 `@Service`、`@Repository`、`@Controller`，可以讓類別在元件掃描時變成 Bean。只有落在掃描範圍內的類別才會被找到。

`@Autowired` 常見的寫法是加在實體變數上，這種欄位注入到現在也還能用。只是 Spring 一般建議用建構子注入：元件可以寫成不可變物件，必要的相依也不會是 `null`[出處](https://docs.spring.io/spring-framework/reference/core/beans/dependencies/factory-collaborators.html)。目標 Bean 只有一個建構子時，那個建構子上不需要再加 `@Autowired`[出處](https://docs.spring.io/spring-framework/reference/core/beans/annotation-config/autowired.html)。

*【同一個介面有好幾個候選者】*

## 用 @Qualifier 講清楚要哪一個

> 🏠 **生活比喻**
>
> 容器裡有兩種「付款方式」（信用卡、Line Pay），你只說「我要付款方式」，物流中心不知道送哪個。`@Qualifier` 就是**指名道姓「我要信用卡那個」**。

如果容器裡有兩個以上的 Bean 都實作 `Printer`，只照型別注入就會出現歧義。這時可以用 `@Qualifier` 指定 Bean 名稱，或用 `@Primary` 標出預設的那一個。

```
@Service
public class ReportService {
    private final Printer printer;

    public ReportService(@Qualifier("hpPrinter") Printer printer) {
        this.printer = printer;
    }
}
```

`@Qualifier` 適合表達「這裡明確就是要某一種實作」；`@Primary` 適合表達「整個應用程式通常用這一個」。

元件掃描產生的 Bean 名稱預設是把類別名的第一個字母改小寫，所以 `HpPrinter` 會變成 `hpPrinter`，上面範例裡那個名稱就是這樣來的。

*【三種設定風格】*

## 元件掃描、Java 組態與 XML

> 🏠 **生活比喻**
>
> - 元件掃描＝**物流中心自動巡貨架，看到貼 `@Component` 標籤的就登記**
> - Java 組態 `@Bean`＝**手寫一張訂貨單**
> - XML＝**舊式紙本訂貨單**

Spring 可以用註解元件掃描、Java 組態或 XML 設定 Bean。實務上會混用，但要避免同一項相依關係散在太多地方。

```
@Configuration
public class PrinterConfig {
    @Bean
    public Printer hpPrinter() {
        return new HpPrinter();
    }
}
```

`@Configuration` 表示這是組態類別；`@Bean` 表示這個方法回傳的物件要交給容器管理。它特別適合你改不到原始碼的第三方類別，也適合需要明確建構流程的物件。

常看到有人把 `@Bean`、`<bean/>` 與 `@Component` 三個畫上等號。就「三者都會讓容器管到這個物件」這個意思來說沒有錯，但等號容易讓人以為可以互換：`@Component` 加在類別上、靠元件掃描發現，`@Bean` 只能加在組態類別的方法上、由那個方法自己負責建構物件。

XML 的 `<bean>` 也能達成一樣的目的，而且不必改目標類別；不過 Java 組態通常比較容易得到型別檢查與程式碼導覽。早期的教學多半以 XML 組態為主，那是 Spring Boot 普及之前的常態。

*【Bean 從出生到離開容器】*

## 初始化、銷毀與相依順序

> 🏠 **生活比喻**
>
> 容器會**先準備好你需要的供應商，再準備你**；`@PostConstruct` 是**開店後的第一件事**，`@PreDestroy` 是**打烊前的收拾**。

容器會先建立 Bean、完成相依注入，再呼叫初始化回呼。應用程式正常關閉時，容器會執行銷毀回呼。如果 A 依賴 B，容器必須先把 B 準備好，才能完成 A。

```
@Component
public class CacheClient {
    @PostConstruct
    void connect() {
        // 相依注入完成後執行
    }

    @PreDestroy
    void close() {
        // 容器關閉時釋放資源
    }
}
```

這個註解可以標在 public、protected、套件私有或 private 的方法上，不必是 public；沒有參數、沒有回傳值這兩點則成立[出處](https://jakarta.ee/specifications/annotations/3.0/apidocs/jakarta.annotation/jakarta/annotation/postconstruct)。

> 📝 查證更正：原筆記寫「@PostConsturct 1. 方法必須為public 2. 沒有返回值(void) 3. 方法不能有參數」，查證後更正：Jakarta Annotations 規格明講這個註解可以標在 public、protected、套件私有或 private 的方法上，不要求 public；沒有參數、沒有回傳值這兩點則成立。另外原筆記把註解名打成「@PostConsturct」，正確拼法是 @PostConstruct

另外這個註解現在住在 `jakarta.annotation`：`javax.annotation` 整包在 JDK 9 從核心模組分出去、JDK 11 移除，Jakarta EE 9 起改到新套件[出處](https://docs.spring.io/spring-framework/reference/core/beans/annotation-config/postconstruct-and-predestroy-annotations.html)。

初始化方法不是用來遮掩循環依賴的。如果 A 需要 B、B 又需要 A，通常代表責任切得不清楚，應該先重新設計，而不是想辦法讓容器勉強把它們建出來。

*【把環境值移出程式碼】*

## properties、@Value 與 SpEL

> 🏠 **生活比喻**
>
> - `application.properties`＝**店裡的設定公告欄**（營業時間、折扣）
> - `@Value`＝**從公告欄抄一個值過來**
> - SpEL＝**公告欄上可以寫簡單算式**（「原價 × 0.8」）

`application.properties` 可以保存連線網址、功能開關這類設定。用預留位置（placeholder）語法 `${key}` 讀取屬性，冒號後面可以放預設值。

```
printer.max-pages=100

@Value("${printer.max-pages:50}")
private int maxPages;
```

外部設定有 `printer.max-pages` 時就用外部的值，找不到才用 `50`：設定檔裡的值優先，冒號後面那個只是找不到時的備援。

Spring 表達式語言（Spring Expression Language，SpEL）用的是 `#{...}`，可以存取 Bean 或做運算，跟單純讀設定值的 `${...}` 用途不同。

### 🗺️ 比喻對照表

| 技術名詞 | 生活比喻 |
| --- | --- |
| IoC | 供應商送到門口 |
| DI | 送貨這個動作 |
| Spring 容器 | 中央廚房兼物流中心 |
| 建構子注入 | 開店前設備全到位 |
| @Qualifier | 指名要哪一家 |
| @Value | 從公告欄抄值 |

### 重點整理

*   IoC 把物件的建立與管理交給容器；DI 把相依物件注入使用端。
*   依賴介面這類抽象型別，可以縮小換實作時要改的範圍。
*   必要的相依優先用建構子注入；多個候選 Bean 用 `@Qualifier` 或 `@Primary` 處理。
*   Bean 可以由元件掃描、Java 組態或 XML 建立，但 `@Bean` 與 `@Component` 不是同一個東西。
*   `@PostConstruct` 不要求 public，套件名在 Spring 6 起改成 `jakarta.annotation`。
*   `${...}` 讀屬性，`#{...}` 執行 SpEL 運算式。

## 隨堂測驗

**Q1. MemberService 在類別內直接 new MemberDaoImpl，主要造成什麼問題？**

- (A) 服務類別與具體 DAO 實作綁得太緊
- (B) Spring 無法處理 HTTP 請求
- (C) 資料庫無法建立交易
- (D) JSON 無法轉換成 Java 物件

<details><summary>看答案</summary>

**答案：(A)** 使用端直接建立具體實作，換實作或放測試替身時都得改使用端。

</details>

**Q2. 控制反轉的核心概念是什麼？**

- (A) 把物件的建立與組裝控制權交給外部容器
- (B) 把所有方法改成靜態方法
- (C) 由資料庫決定 HTTP 狀態碼
- (D) 把 Java 物件全部轉成 JSON

<details><summary>看答案</summary>

**答案：(A)** 原本由應用程式自己負責的物件管理工作，改由容器負責。

</details>

**Q3. 在 Spring 裡，Bean 指的是什麼？**

- (A) 由 Spring 容器建立或管理的物件
- (B) 只能存放資料表欄位的實體類別
- (C) 一段固定格式的 SQL
- (D) 瀏覽器送出的 Cookie

<details><summary>看答案</summary>

**答案：(A)** Bean 就是納入 IoC 容器管理的物件，不限於某一層或某一種用途。

</details>

**Q4. 為什麼必要的相依適合用建構子注入？**

- (A) 物件一建立就能保證必要相依已經到位，也方便直接傳入測試替身
- (B) 可以省掉所有介面設計
- (C) 能讓每個 Bean 自動變成單例
- (D) 會自動替方法加上交易

<details><summary>看答案</summary>

**答案：(A)** 建構子會把必要相依明白列出來，欄位也能宣告成 final。

</details>

**Q5. 容器裡有兩個 Printer 實作，某個注入點只要 hpPrinter，適合怎麼做？**

- (A) 在注入點用 @Qualifier("hpPrinter")
- (B) 在方法上用 @RequestBody
- (C) 在類別上用 @ControllerAdvice
- (D) 在欄位上用 @PathVariable

<details><summary>看答案</summary>

**答案：(A)** @Qualifier 在同型別有多個候選 Bean 時指定要哪一個名稱。

</details>

**Q6. 哪一種情境特別適合用 @Bean 建立物件？**

- (A) 要管理一個你改不到原始碼、加不上 @Component 的第三方類別
- (B) 要從網址取得查詢參數
- (C) 要把查詢結果逐列轉成物件
- (D) 要攔截 Controller 的路徑

<details><summary>看答案</summary>

**答案：(A)** @Bean 在組態類別裡自己負責建構物件，不必修改目標類別。

</details>

**Q7. 關於 @PostConstruct 方法的存取層級，正確的是什麼？**

- (A) 不要求 public，任何存取層級都可以
- (B) 一定要 public，否則不會被呼叫
- (C) 一定要 private
- (D) 必須跟類別同名

<details><summary>看答案</summary>

**答案：(A)** Spring 對這個註解的方法沒有存取層級要求，常寫成套件私有。

</details>

**Q8. Bean 的初始化回呼通常在什麼時候執行？**

- (A) 物件建立而且相依注入完成之後
- (B) 每次 SQL 提交之後
- (C) HTTP 回應送出之後
- (D) 相依還沒注入、序列化成 JSON 之前

<details><summary>看答案</summary>

**答案：(A)** 初始化回呼用來處理相依就緒後的準備工作。

</details>

**Q9. ${printer.max-pages:50} 裡的 50 代表什麼？**

- (A) 找不到這個屬性時採用的預設值
- (B) Bean 的固定存活秒數
- (C) HTTP 回應狀態碼
- (D) 容器最多能建立的 Bean 數量

<details><summary>看答案</summary>

**答案：(A)** 冒號後面是屬性不存在時的預設值；設定檔裡有值時以設定檔為準。

</details>
