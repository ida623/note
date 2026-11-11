# 04. Hibernate 查詢與關聯

> 來源：[筆記平台 · Spring 後端](https://hhtim.github.io/notes-platform/spring/#/lesson/hibernate-query)　第 4 課 / 共 23 課 · 約 12 分鐘

**用 HQL、Criteria API、原生 SQL 與實體關聯，表達不同層次的資料查詢需求。**

### 讀完這課你會

*   分辨 HQL 與 SQL 分別在查什麼
*   用具名參數、投影與分頁寫出常見的 HQL 查詢
*   依需求在 HQL、Criteria API 與原生 SQL 之間選擇
*   設定一對一、一對多、多對一與雙向關聯，並知道兩端都要維護

*【物件導向的查詢語言】*

## HQL 查的是實體，不是資料表

HQL（Hibernate Query Language）長得很像 SQL，但操作的是實體類別與它的屬性。Hibernate 再依資料庫方言把它翻成對應的 SQL，所以換資料庫時查詢字串通常不用改。

| 比較項目 | HQL | SQL |
| --- | --- | --- |
| 資料來源 | 實體類別，例如 `Member` | 資料表，例如 `member` |
| 欄位表示 | 實體屬性，例如 `username` | 資料表欄位，例如 `user_name` |
| 關聯導覽 | 可沿著對映屬性 JOIN | 依欄位與外來鍵條件 JOIN |
| 跨資料庫 | 由 Hibernate 翻譯方言 | 語法差異要自己處理 |

```
FROM Member m
WHERE m.username = :username
ORDER BY m.id DESC
```

HQL 的 `SELECT` 可以省略，省略時回傳 `FROM` 指定的完整實體。實體類別名與屬性名要正確對應 Java 這邊的對映，不能拿資料表或欄位名代替。

HQL 的大小寫規則分成兩半，兩句話要一起看：關鍵字（SELECT、FROM、WHERE）不分大小寫，類別名與屬性名分大小寫。把關鍵字寫成大寫只是閱讀習慣，不影響查詢意義。

*【安全傳值】*

## 用參數，不要把使用者輸入拼進去

具名參數像預留座位：HQL 先用 `:username` 標出位置，再由 API 把真正的值放進去。這樣比串字串清楚，查詢引擎也能正確處理值的型別與跳脫。

```
List<Member> members = session
    .createQuery(
        "FROM Member m WHERE m.username = :username",
        Member.class
    )
    .setParameter("username", input)
    .getResultList();
```

> 💡 如果 input 是外部輸入，能不能寫成 `"... = '" + input + "'"`？

不行。字串拼接會抬高注入攻擊與語法錯誤的風險。不論用 HQL、Criteria 還是原生 SQL，值都應該透過參數綁定傳進去。

*【回傳什麼形狀】*

## 投影與 DTO

查完整實體會把所有對映屬性都載入；如果畫面只要姓名與狀態，可以用投影（Projection）限制回傳內容。

```
SELECT new com.example.MemberSummary(m.username, m.status)
FROM Member m
WHERE m.status = :status
```

建構子投影需要目標類別提供參數型別與順序相符的建構子。如果只挑了多個零散屬性又沒指定 DTO，預設回傳的是 `List<Object[]>`：每一列是一個陣列，用起來很容易寫錯索引。

> 完整實體：後續需要實體行為與關聯時用；DTO 投影：唯讀畫面與固定欄位時用

*【資料很多的時候】*

## 分頁交給查詢 API 控制

各家資料庫的分頁語法不一樣（MySQL 用 `LIMIT`，Oracle 與 SQL Server 用 `OFFSET … FETCH` 這類寫法[SQL Server](https://learn.microsoft.com/sql/t-sql/queries/select-order-by-clause-transact-sql)[Oracle](https://docs.oracle.com/en/database/oracle/oracle-database/23/sqlrf/SELECT.html)）。HQL 不把這些寫進字串，而是透過查詢 API 指定起點與筆數，差異由 Hibernate 在底層轉換。

```
List<Member> page = session
    .createQuery("FROM Member m ORDER BY m.id", Member.class)
    .setFirstResult(20)
    .setMaxResults(10)
    .getResultList();
```

這段的意思是略過前 20 筆，再取最多 10 筆。正式的分頁要搭配穩定的排序條件，否則資料一有異動，各頁內容就可能重複或漏掉。

*【新增、修改、刪除也能用 HQL】*

## 批次敘述與它的邊界

HQL 的 `insert` 有版本差異：Hibernate 5.6 的文法是 `insert_statement ::= insert_clause select_statement`，insert 只能接一個 select 當來源；後來的版本補上 `values` 子句，例如 `insert Person (id, name) values (100L, 'Jane Doe'), (200L, 'John Roe')`，給多組值就插入多列[現行](https://docs.hibernate.org/orm/6.6/querylanguage/html_single/Hibernate_Query_Language.html)[舊版](https://docs.hibernate.org/orm/5.6/userguide/html_single/Hibernate_User_Guide.html)。

要留意的是：這類批次敘述直接對資料庫動手，不會走實體的狀態追蹤。執行完之後，Session 裡既有的實體可能還留著舊值，必要時要重新整理或清掉受影響的實體。

*【條件會變的查詢】*

## Criteria API：用物件組出查詢

Criteria API 適合條件數量隨使用者輸入改變的查詢。它把查詢拆成建構器、查詢定義、資料來源與條件物件，不必手動接一堆 HQL 片段。

```
CriteriaBuilder cb = session.getCriteriaBuilder();
CriteriaQuery<Member> cq = cb.createQuery(Member.class);
Root<Member> member = cq.from(Member.class);

cq.select(member)
  .where(cb.equal(member.get("status"), "ACTIVE"))
  .orderBy(cb.asc(member.get("username")));

List<Member> result = session.createQuery(cq).getResultList();
```

Criteria 也能做更新與刪除。規格裡就有 `CriteriaUpdate`，用 Criteria API 執行批次更新；刪除則有對應的 `CriteriaDelete`[出處](https://jakarta.ee/specifications/persistence/3.1/apidocs/jakarta.persistence/jakarta/persistence/criteria/criteriaupdate)。

> 📝 查證更正：原筆記寫 Criteria「只支援查詢動作，不支援新刪修動作」，查證後更正：JPA 2.1（2013 年）就加入了 CriteriaUpdate 與 CriteriaDelete，可以用 Criteria 的方式表達批次更新與刪除

「Criteria 只能查詢」這個印象有來源：Hibernate 早年另有一套自己的 `org.hibernate.Criteria`，那一套確實只能查詢。現在寫 Criteria 用到的 `Root`、`CriteriaQuery` 這些名字屬於 JPA 這一套，兩套不要混在一起看。

Criteria 常被說成「type-safe（型別安全，編譯器會檢查）」。這個說法不能算錯，但成立的前提是搭配靜態中繼模型（Static Metamodel，例如 `Member_.status`）。像上面範例那樣用字串 `get("status")` 指定屬性時就沒有這個保護：規格裡 `Path.get(String)` 是在執行時才因為找不到屬性丟 `IllegalArgumentException`，屬性改名編譯器不會提醒你[出處](https://jakarta.ee/specifications/persistence/3.1/apidocs/jakarta.persistence/jakarta/persistence/criteria/path)。

Criteria 本身也不是防注入的魔法。查詢的值仍然要以參數或 API 的值節點傳入，不要把不可信的內容拿去當欄位名或 SQL 片段。

*【資料庫專屬的能力】*

## 原生 SQL：直接對資料表說話

原生 SQL 適合用資料庫專屬函式、複雜報表、既有 SQL，或 HQL 不好表達的查詢。代價是和資料庫結構與方言綁得更緊。

```
List<Member> members = session
    .createNativeQuery(
        "SELECT * FROM member WHERE status = :status",
        Member.class
    )
    .setParameter("status", "ACTIVE")
    .getResultList();
```

| 工具 | 適合情境 | 主要代價 |
| --- | --- | --- |
| HQL | 以實體為中心的一般查詢 | 要熟悉對映與 HQL 語法 |
| Criteria API | 條件高度動態、需要用程式組出來 | 程式碼較長，可讀性要自己顧 |
| 原生 SQL | 資料庫專屬功能或複雜的既有 SQL | 換資料庫困難，要自己留意快取一致性 |

*【模型之間的關聯】*

## Relationship 與 Association

資料庫用外來鍵描述資料表之間的關係（Relationship）；Java 實體用物件參照描述關聯（Association）。概念相通，但對映時還是要明確指定哪一方持有外來鍵。

*   **一對一**：一本書對應一筆商品明細，兩端最多各一筆。
*   **多對一**：多名員工屬於同一個部門；員工這端持有一個 Department 屬性。
*   **一對多**：一個部門有多名員工；部門這端持有員工集合。
*   **多對多**：多名學生修多門課，通常由中介資料表保存兩端的外來鍵。

```
@Entity
public class Employee {
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "department_id")
    private Department department;
}

@Entity
public class Department {
    @OneToMany(mappedBy = "department")
    private List<Employee> employees = new ArrayList<>();
}
```

`mappedBy = "department"` 表示 `Employee.department` 才是維護這段關聯的那一側。它指的是 Java 屬性名，不是資料庫欄位名。

關聯可以從兩個角度分類：數量性（1 對 1、1 對 N、N 對 1、N 對 N）與方向性（單向只有一方找得到對方，雙向兩方都找得到）。這兩個分法直接對應到上面的註解設定。

*【雙向關聯的陷阱】*

## 資料庫一致，不代表記憶體兩端也一致

雙向關聯讓兩個實體都找得到對方，但兩邊的物件參照要自己同時維護。可以在 Department 提供一個輔助方法，避免只更新其中一側。

```
public void addEmployee(Employee employee) {
    employees.add(employee);
    employee.setDepartment(this);
}
```

關聯的數量性與載入策略是兩件事：`@OneToMany` 說的是一對多，`LAZY` 或 `EAGER` 說的才是什麼時候載入。級聯操作（Cascade）也要依生命週期需求設定，不要把「刪除部門」誤設成無條件刪掉所有員工。

把雙向關聯直接序列化成 JSON 時，兩端互相參照會造成無限遞迴。API 回應通常該用 DTO，不要直接把完整的實體圖丟出去。

### 重點整理

*   HQL 用的是實體類別名與 Java 屬性名，不是資料表與欄位名。
*   外部輸入一律參數化，不要拼接到 HQL 或 SQL 裡。
*   DTO 投影能限制回傳欄位；分頁要搭配穩定的排序。
*   現行 HQL 支援 `insert ... values`；Criteria 也支援批次更新與刪除。
*   Criteria 要搭配靜態中繼模型才有完整型別檢查，用字串指定屬性沒有。
*   原生 SQL 適合資料庫專屬需求，但換資料庫的成本比較高。
*   雙向關聯的兩端都要維護，`mappedBy` 指向持有關聯的 Java 屬性。

## 隨堂測驗

**Q1. HQL 的 FROM Member m 裡，Member 通常代表什麼？**

- (A) 對映後的實體類別名稱
- (B) 資料庫連線池名稱
- (C) 實體所屬的 Maven artifactId
- (D) JDBC 驅動程式類別名稱

<details><summary>看答案</summary>

**答案：(A)** HQL 操作的是實體與屬性，不是資料表與欄位。

</details>

**Q2. 為什麼查詢條件要用 :username 這類具名參數？**

- (A) 能清楚綁定值與型別，並降低字串拼接造成的注入風險
- (B) 能讓所有查詢自動略過交易
- (C) 能強制 Hibernate 永遠用同一張資料表
- (D) 能讓延遲載入自動改成立即載入

<details><summary>看答案</summary>

**答案：(A)** 參數綁定不會讓外部輸入變成 SQL 結構的一部分。

</details>

**Q3. 清單畫面只需要 username 與 status，哪種做法比較貼近需求？**

- (A) 用 DTO 建構子投影，只挑需要的屬性
- (B) 載入完整實體與所有關聯後再丟掉用不到的資料
- (C) 改用 DELETE 查詢排除其他欄位
- (D) 把這兩個屬性改成實體主鍵

<details><summary>看答案</summary>

**答案：(A)** 投影能限制回傳欄位，避免多載入不需要的資料與關聯。

</details>

**Q4. setFirstResult(20) 搭配 setMaxResults(10) 是什麼意思？**

- (A) 略過前 20 筆，最多再取接下來的 10 筆
- (B) 只查主鍵介於 20 到 10 之間的資料
- (C) 先取 20 筆，再刪掉其中 10 筆
- (D) 建立 20 個 Session，每個查 10 筆

<details><summary>看答案</summary>

**答案：(A)** 這是查詢 API 層級的分頁，各家資料庫的語法差異由 Hibernate 轉換。

</details>

**Q5. 關於現行 HQL 的 insert 敘述，哪一項正確？**

- (A) 支援 values 子句，而且給多組值可以一次插入多列
- (B) 完全不支援 insert，只能用原生 SQL
- (C) 只能搭配 select 來源，不能直接給值
- (D) insert 一定會繞過資料庫，只改記憶體

<details><summary>看答案</summary>

**答案：(A)** 舊版本不支援 values，現行版本支援。

</details>

**Q6. 想用 Criteria API 表達一次批次更新，正確的認知是什麼？**

- (A) JPA 2.1 起提供 CriteriaUpdate，可以用 Criteria 表達更新
- (B) Criteria 永遠只能查詢，更新一定要改用原生 SQL
- (C) Criteria 的更新必須先關閉交易
- (D) CriteriaUpdate 只能用在 NoSQL 資料庫

<details><summary>看答案</summary>

**答案：(A)** CriteriaUpdate 與 CriteriaDelete 自 JPA 2.1 就存在。

</details>

**Q7. Criteria API 常被說成型別安全，比較精確的說法是什麼？**

- (A) 用字串指定屬性時編譯器抓不到錯，要搭配靜態中繼模型才有完整檢查
- (B) 它在任何寫法下都有完整的編譯期檢查
- (C) 它完全沒有型別檢查
- (D) 型別檢查只在執行原生 SQL 時才有效

<details><summary>看答案</summary>

**答案：(A)** get("status") 這種字串寫法改名時不會編譯失敗，Metamodel 才補得上這一塊。

</details>

**Q8. Department 的 @OneToMany(mappedBy = "department") 中，department 指的是什麼？**

- (A) Employee 實體裡持有關聯的那個 Java 屬性名稱
- (B) Department 資料表的主鍵名稱
- (C) Hibernate 組態檔的檔名
- (D) 資料庫使用者名稱

<details><summary>看答案</summary>

**答案：(A)** mappedBy 指向對側的 Java 屬性，宣告關聯由那一端維護。

</details>

**Q9. 在雙向一對多關聯中新增員工時，記憶體裡比較穩妥的做法是什麼？**

- (A) 把員工加進部門集合，同時把員工的 department 設成該部門
- (B) 只改資料庫外來鍵，不更新任何物件參照
- (C) 只建立一個新的 SessionFactory
- (D) 把一對多拆成兩個互不相干的一對一

<details><summary>看答案</summary>

**答案：(A)** 資料庫一致不代表記憶體兩端一致，兩邊都要維護才不會讀到半邊的狀態。

</details>
