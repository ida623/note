# 03. Hibernate 入門與環境

> 🏠 **生活化版本**：每個段落開頭的「生活比喻」先用日常情境帶你抓到感覺，接著再看原本的技術說明與程式碼；篇末有「比喻對照表」可以快速複習。

> 來源：[筆記平台 · Spring 後端](https://hhtim.github.io/notes-platform/spring/#/lesson/hibernate-intro)　第 3 課 / 共 23 課 · 約 12 分鐘

**從物件關聯對映、實體的四種狀態與環境設定開始，掌握 Hibernate 的交易與基本新增、刪除、修改、查詢。**

### 讀完這課你會

*   說清楚物件關聯對映、Hibernate、JPA 與 JDBC 各自站在哪一層
*   認得實體物件的臨時、永續、分離、移除四種狀態
*   設定 Hibernate 的相依套件、資料庫連線與實體對映
*   用 Session 與 Transaction 完成基本的新增、刪除、修改、查詢

*【觀念起點】*

## 為什麼需要 Hibernate？

> 🏠 **生活比喻**
>
> 直接用 JDBC 像**每次都要手寫提貨單、自己把貨拆箱分類**；Hibernate 像**有一位管家**，你說「我要 3 號會員」，他自己去倉庫把資料整理成 Java 物件交給你。

直接用 JDBC 時，你得自己取得連線、寫 SQL、設定參數，再把 `ResultSet` 的每個欄位一個一個塞回 Java 物件。資料表欄位越多，這些重複程式碼就越長。

物件關聯對映（Object-Relational Mapping，ORM）像一位翻譯：程式這端講的是物件與屬性，資料庫那端講的是資料表與欄位，ORM 負責建立兩邊的對應。

| 物件世界 | 資料庫世界 |
| --- | --- |
| 實體類別 | 資料表 |
| 一個物件 | 一筆資料列 |
| 屬性 | 欄位 |
| 物件識別屬性 | 主鍵 |
| 物件之間的參照 | 外來鍵關聯 |

Hibernate 是 ORM 框架，JPA 則是持久層的標準規格。應用程式可以透過 JPA 規格操作由 Hibernate 提供的實作，而 Hibernate 底層還是透過 JDBC 跟資料庫溝通。

> 應用程式 → JPA／Hibernate → JDBC → 關聯式資料庫

JPA 早年的正式名稱是「Java Persistence API」。這套規格後來改名為 Jakarta Persistence，套件也從 `javax.persistence` 改成 `jakarta.persistence`[出處](https://jakarta.ee/specifications/persistence/3.1/)。現在的文件與程式碼看到的多半是新名字。

> 📝 查證更正：這是版本差異不是原筆記寫錯：原筆記寫「JPA(Java Persistence API)」，那是它寫成當時的正式名稱。規格隨 Java EE 移交 Eclipse 基金會後改名 Jakarta Persistence，套件也從 javax.persistence 改成 jakarta.persistence

常聽到「JPA 是 Java 官方委託 Gavin King 所寫」，這句話並不精確。Gavin King 是 Hibernate 的作者沒錯，但規格不是委託一個人寫的，而是 JSR 338 專家小組共同完成，規格書第 1.1 節列出二十一位成員與所屬單位[出處](https://jakarta.ee/specifications/persistence/3.1/jakarta-persistence-spec-3.1.html)。

MyBatis 也能把查詢結果對映成物件，但它的設計取向和完整的 ORM 不太一樣；Spring Data JPA 則是站在 JPA 之上，再提供一層儲存庫抽象。這三者的關係〈Spring 資料存取〉會再談。

*【三個核心角色】*

## SessionFactory、Session 與 Transaction

> 🏠 **生活比喻**
>
> - SessionFactory＝**管家公司**，整個程式只開一間，很貴
> - Session＝**派來你家的一位管家**，用完就走
> - Transaction＝**一張工作單**：上面的事要嘛全做完，要嘛全取消

`SessionFactory` 是很重的工廠物件，通常在應用程式啟動時建立一次，之後整個程式共用。

`Session` 代表一段工作範圍（工作單元，Unit of Work），負責追蹤實體狀態並提供資料存取操作。它通常不是執行緒安全的物件，不能讓多個同時執行的請求共用。

`Transaction` 把多個操作包成不可分割的一組。即使只是查詢，也建議把交易邊界劃清楚，否則連線與一致性的行為會變得難以預測。

```
SessionFactory sessionFactory = HibernateUtil.getSessionFactory();

try (Session session = sessionFactory.openSession()) {
    Transaction tx = session.beginTransaction();
    try {
        // 在這裡做資料存取
        tx.commit();
    } catch (RuntimeException ex) {
        if (tx.isActive()) {
            tx.rollback();
        }
        throw ex;
    }
}
```

`openSession()` 每次都建立新的 Session；`getCurrentSession()` 則看目前的綁定設定，例如綁在執行緒上，或交給框架管理的交易。用 Hibernate 內建的連線供應者時，它預設會把 JDBC 連線的自動提交關掉；連線改由 DataSource（連線池或 JNDI）提供時 Hibernate 不動這個設定。不論哪一種，新增、刪除、修改都要在交易裡完成[出處](https://docs.hibernate.org/orm/6.6/javadocs/org/hibernate/cfg/JdbcSettings.html)。

*【物件的四種狀態】*

## 實體生命週期

> 🏠 **生活比喻**
>
> 物件在 Hibernate 眼中有四種身分：
> - Transient＝**路人**，管家不認識
> - Persistent＝**管家正在照顧的人**，改了什麼管家會自動記下來
> - Detached＝**管家下班後留下的人**，改了也沒人記
> - Removed＝**被標記要送走的人**

Hibernate 不只是幫你送 SQL，它還會追蹤一個物件現在是不是由 Session 管理中。可以把 Session 想成代管櫃台：物件交給櫃台之後，屬性一改動，提交交易時才可能同步回資料庫。

| 狀態 | 意思 | 常見的轉換方式 |
| --- | --- | --- |
| 臨時（Transient） | 剛用 `new` 建出來，還沒被 Session 管理。 | `new Member()` |
| 永續（Persistent） | 正被 Session 追蹤，提交交易時會做髒資料檢查。 | `persist()`、依識別值載入 |
| 分離（Detached） | 曾經被管理，但已離開原本的 Session。 | `detach()`、`clear()`、關閉 Session |
| 移除（Removed） | 已標記要刪除，通常在提交或 flush 時反映到資料庫。 | `remove()` |

物件有識別值，不代表它現在一定是永續狀態。Session 關掉之後，物件仍然留著主鍵值，但已經變成分離物件。

`flush()` 是把記憶體裡排好的變更同步成 SQL；`commit()` 是把交易完成掉。兩件事相關，但不是同一件。

*【實體對映】*

## 用註解把 Java 類別接上資料表

> 🏠 **生活比喻**
>
> `@Entity`、`@Table`、`@Column` 像**貼在家具上的標籤**：「這張桌子對應倉庫的 A 櫃、桌腳對應第 3 格」，管家照標籤收放。

一般 Java 物件常被叫做 POJO（Plain Old Java Object，普通 Java 物件）。加上實體對映之後，它就能變成 Hibernate 管理的實體類別。每個實體都必須有識別屬性，用 `@Id` 對應主鍵。

```
@Entity
@Table(name = "member")
public class Member {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "username", nullable = false)
    private String username;

    @Column(name = "status", insertable = false)
    private String status;

    protected Member() {
    }

    // getter、setter
}
```

常有人建議別用 `AUTO`。原因在 `AUTO` 的定義：由持久層提供者依該資料庫挑一個適合的策略，所以換資料庫時產生識別值的方式可能跟著換。要讓行為可預期，明確指定 `IDENTITY` 或 `SEQUENCE` 就好[出處](https://jakarta.ee/specifications/persistence/3.1/apidocs/jakarta.persistence/jakarta/persistence/generationtype)。

`insertable = false` 表示產生 INSERT 時不寫這個欄位，常用來讓資料庫的預設值接手；它不等於這個 Java 屬性永遠不能改。

*【環境建置】*

## 相依套件、組態與連線來源

> 🏠 **生活比喻**
>
> 組態像**給管家的工作手冊**：倉庫在哪（連線網址）、鑰匙（帳號密碼）、倉庫品牌（方言）。

典型的 Maven 專案把 Java 程式放 `src/main/java`，把 `hibernate.cfg.xml` 這類資源放 `src/main/resources`。環境設定可以拆成三件事：

*   加入 Hibernate ORM 與 JDBC 驅動程式等 Maven 相依套件。
*   設定資料庫連線、SQL 方言與 SessionFactory 的行為。
*   註冊或掃描帶有對映註解的實體類別。

```
<hibernate-configuration>
  <session-factory>
    <property name="hibernate.connection.url">
      jdbc:mysql://localhost:3306/app_db
    </property>
    <property name="hibernate.connection.username">app_user</property>
    <property name="hibernate.connection.password">請由安全設定注入</property>
    <mapping class="com.example.Member"/>
  </session-factory>
</hibernate-configuration>
```

別把正式環境的密碼提交進版本控制。實務上會改用環境變數、祕密管理服務，或由容器提供的 DataSource。

用 JNDI（Java 命名與目錄介面）時，DataSource 通常由 Servlet 容器註冊；直接跑一般的 `main` 方法時，除非另外建立相容的命名環境，否則不能假設容器提供的 JNDI 資源存在——用一般的 `main` 方法啟動時 Tomcat 根本沒跑起來，JNDI 也就不會啟動。

*【基本操作】*

## 新增、查詢、修改與刪除

> 🏠 **生活比喻**
>
> - `persist`＝**把新家具交給管家登記入庫**
> - `find`＝**請管家拿某號家具**
> - 修改＝**直接改家具，管家下班前會自動同步**（髒檢查）
> - `remove`＝**請管家送走**
>
> 改資料的事都要在**工作單**（交易）裡做。

所有會改資料的操作都要放在明確的交易裡。對永續物件來說，改完屬性通常不必再呼叫一個叫 `update` 的方法；Hibernate 會在 flush 時做髒資料檢查（Dirty Checking），自己看出哪些欄位變了。

```
// 新增
Member member = new Member();
member.setUsername("mei");
session.persist(member);

// 依主鍵查詢
Member found = session.find(Member.class, memberId);

// 修改：found 必須仍由目前的 Session 管理
found.setUsername("mei.lin");

// 刪除
session.remove(found);
```

把 `save()`、`delete()`、`saveOrUpdate()` 當成「已棄用但還能用」，是 Hibernate 6 的狀態。Hibernate 7 把 `Session#save`、`Session#update`、`Session#saveOrUpdate` 的所有形式都移除了，`Session#delete` 也移除、改用 `Session#remove`。新增、併回、刪除現在用 `persist()`、`merge()`、`remove()`，舊寫法在 Hibernate 7 連編譯都不會過[出處](https://docs.hibernate.org/orm/7.0/migration-guide/)。

> 📝 查證更正：這是版本差異不是原筆記寫錯：原筆記把 save()、delete()、saveOrUpdate() 標成「已廢棄」，那是 Hibernate 6 的狀態；Hibernate 7.0 已經把 Session#save、Session#update、Session#saveOrUpdate、Session#delete 整批移除，改用 persist()、merge()、remove()，舊呼叫在 Hibernate 7 連編譯都過不了

依主鍵查詢用 JPA 標準的 `find()`。Hibernate 自己的 `get()` 在 7.0 標成棄用（deprecated），要改用 JPA 標準的 `Session#find`[出處](https://docs.hibernate.org/orm/7.0/migration-guide/)。

物件已經是分離狀態時，用 `merge()` 把資料併回目前 Session 管理的實體。要注意：之後要繼續操作的是 `merge()` 回傳的那個物件，不是你傳進去的舊物件。

```
Member managed = session.merge(detachedMember);
managed.setUsername("new-name");
```

*【Web 應用程式的注意事項】*

## 延遲載入與交易邊界

> 🏠 **生活比喻**
>
> 延遲載入像**管家先只拿目錄給你，等你翻到那頁才去倉庫拿實物**。如果管家已經下班（Session 關了）你才翻頁，就會拿不到（`LazyInitializationException`）。

延遲載入（Lazy Loading）會先放一個代理物件或還沒初始化的集合，等程式真的去讀關聯資料時才查詢。它能避免一次載入太多資料，但如果 Session 已經關了才去讀還沒載入的關聯，就會失敗。

有一種常見的解法是把連線與交易控制搬到 Filter 上，讓 Session 活到畫面畫完。這個做法有個名字叫 Open Session in View，在 Spring Boot 對應的是 `spring.jpa.open-in-view` 這個設定（預設開著）。它的代價是查詢時機變得難以掌握，也容易在畫面渲染階段冒出一大堆額外查詢。Spring Boot 啟動時若沒有明確設定這個屬性，會印一行警告：「`spring.jpa.open-in-view` 預設是開著的，因此畫面渲染期間可能會執行資料庫查詢」——所以不要在不知情下依賴它[出處](https://github.com/spring-projects/spring-boot/blob/main/module/spring-boot-jpa/src/main/java/org/springframework/boot/jpa/autoconfigure/JpaBaseConfiguration.java)。

比較穩的做法是在服務層的交易裡把回應需要的資料查齊，或直接投影成 DTO（Data Transfer Object，資料傳輸物件）。

> 先定義這個使用情境需要哪些資料，再決定要立即載入、查詢時 JOIN FETCH，還是投影成 DTO；不要把延遲載入當成自動解決效能問題的開關。

### 🗺️ 比喻對照表

| 技術名詞 | 生活比喻 |
| --- | --- |
| Hibernate | 幫你整理倉庫的管家 |
| SessionFactory / Session | 管家公司 / 派來的管家 |
| Persistent / Detached | 管家照顧中 / 管家下班後 |
| @Entity | 家具上的對照標籤 |
| 髒檢查 | 管家下班前自動同步 |
| 延遲載入 | 翻到那頁才去拿 |

### 重點整理

*   ORM 把實體、屬性與關聯對映到資料表、欄位與外來鍵，底層仍然走 JDBC。
*   JPA 是規格且已改名 Jakarta Persistence，Hibernate 是它的實作之一。
*   SessionFactory 通常共用；Session 代表一段工作範圍，不能跨執行緒共用。
*   永續物件由 Session 追蹤；有識別值不代表還被管理。
*   Hibernate 7 移除了舊的 `save()` 系列，新增、併回、刪除改用 `persist()`、`merge()`、`remove()`；依主鍵查詢用 `find()`。
*   交易失敗要 rollback，資源用完要關閉。
*   延遲載入必須跟交易邊界、查詢需求一起設計，別靠 Open Session in View 撐場。

## 隨堂測驗

**Q1. Hibernate 的物件關聯對映主要在解決哪一種差異？**

- (A) Java 物件模型與關聯式資料庫模型之間的差異
- (B) Java 原始碼與 JVM 位元碼之間的差異
- (C) HTTP 請求與 DNS 查詢之間的差異
- (D) CSS 版面與瀏覽器 DOM 之間的差異

<details><summary>看答案</summary>

**答案：(A)** ORM 負責把實體、屬性、關聯翻譯成資料表、欄位與外來鍵。

</details>

**Q2. 某個 Member 物件曾被 Session 管理，Session 已關閉，物件仍留著主鍵值。它最可能是哪一種狀態？**

- (A) 分離狀態
- (B) 臨時狀態
- (C) 永續狀態
- (D) 移除狀態

<details><summary>看答案</summary>

**答案：(A)** 離開原本的 Session 之後就是分離狀態；主鍵還在不代表還被追蹤。

</details>

**Q3. 關於 SessionFactory 與 Session，哪一項正確？**

- (A) SessionFactory 通常長期共用，Session 對應一段工作範圍
- (B) Session 通常由所有請求與執行緒永久共用
- (C) 每執行一次查詢就要重建 SessionFactory
- (D) SessionFactory 只負責產生 JavaBean，跟持久層設定無關

<details><summary>看答案</summary>

**答案：(A)** SessionFactory 很重，建一次共用；Session 輕，不能跨執行緒共用。

</details>

**Q4. 在交易裡查到受管理的 Member，只想改 username，最合適的基本做法是什麼？**

- (A) 呼叫 setter 改屬性，再提交交易
- (B) 關閉 Session 之後再改，等 Hibernate 自己發現
- (C) 建立一個同主鍵的新物件直接 persist
- (D) 先 clear，再期待原物件維持永續狀態

<details><summary>看答案</summary>

**答案：(A)** 永續物件靠髒資料檢查同步變更，不需要另外呼叫更新方法。

</details>

**Q5. 對分離物件呼叫 merge() 之後，接下來應該操作哪一個物件？**

- (A) merge() 回傳的那個受管理物件
- (B) 原本傳進去的分離物件
- (C) SessionFactory 本身
- (D) Transaction 的代理物件

<details><summary>看答案</summary>

**答案：(A)** merge() 會回傳一個新的受管理物件，傳進去的舊物件不會因此被管理。

</details>

**Q6. 在 Hibernate 7 想新增一個全新的實體，應該呼叫哪個方法？**

- (A) persist()
- (B) save()
- (C) saveOrUpdate()
- (D) update()

<details><summary>看答案</summary>

**答案：(A)** save 系列方法在 Hibernate 6 被標示棄用、7.0 整批移除，新增一律用 persist()。

</details>

**Q7. 實體類別上的 @Id 主要表示什麼？**

- (A) 指定實體的識別屬性，通常對應資料表主鍵
- (B) 指定所有查詢都必須排序的欄位
- (C) 指定這個欄位只能存整數
- (D) 指定這個類別不必加入對映

<details><summary>看答案</summary>

**答案：(A)** 每個實體都要有識別屬性，Hibernate 靠它辨認物件對應哪一筆資料。

</details>

**Q8. 為什麼延遲載入的關聯在 Session 關閉後可能讀不到？**

- (A) 該關聯還沒初始化，而且已經沒有可以執行查詢的工作階段
- (B) 主鍵在 Session 關閉時一定會被清空
- (C) 資料表會在提交交易後自動刪除
- (D) JDBC 規定集合只能讀取一次

<details><summary>看答案</summary>

**答案：(A)** 延遲載入要等到真的存取時才查詢，Session 沒了就查不了。

</details>

**Q9. 交易中發生執行期例外時，比較完整的處理方式是什麼？**

- (A) 交易仍有效就 rollback，接著把例外傳出去或妥善處理
- (B) 照樣 commit，免得浪費已經執行的 SQL
- (C) 只關閉 SessionFactory，不處理交易
- (D) 再呼叫一次 beginTransaction 覆蓋原本的交易

<details><summary>看答案</summary>

**答案：(A)** 部分成功的交易必須還原，否則資料會停在半完成的狀態。

</details>
