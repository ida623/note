# 08. Spring 資料存取

> 🏠 **生活化版本**：每個段落開頭的「生活比喻」先用日常情境帶你抓到感覺，接著再看原本的技術說明與程式碼；篇末有「比喻對照表」可以快速複習。

> 來源：[筆記平台 · Spring 後端](https://hhtim.github.io/notes-platform/spring/#/lesson/spring-data)　第 8 課 / 共 23 課 · 約 12 分鐘

**比較 Spring JDBC、JPA 與 Hibernate 的整合方式，依查詢需求選擇適合的資料存取工具。**

### 讀完這課你會

*   用 NamedParameterJdbcTemplate 做新增、修改、刪除與查詢，並用 RowMapper 把資料列轉成 Java 物件
*   說清楚 JPA、Hibernate 與 Spring Data JPA 三者的關係
*   用 Repository、方法名稱衍生查詢與 @Query 表達資料操作
*   依查詢需求在 Spring JDBC 與 Spring Data JPA 之間選擇

*【Spring JDBC 幫你收掉重複的流程】*

## 還是寫 SQL，但不用處理樣板程式碼

> 🏠 **生活比喻**
>
> `JdbcTemplate` 像**自動洗碗機**：你只要放碗（寫 SQL），開連線、關連線、處理錯誤這些**洗碗瑣事**它都幫你做。

原生 JDBC 要一直重複取得連線、建立敘述、綁參數、走訪結果、釋放資源。Spring JDBC 把 SQL 的控制權留給你，只替你處理這些固定流程。

`DataSource` 提供資料庫連線；`JdbcTemplate` 或 `NamedParameterJdbcTemplate` 用它執行 SQL。後者以名稱綁定參數，比一排問號好讀很多。

```
String sql = """
    update student
       set name = :name
     where id = :id
    """;

MapSqlParameterSource params = new MapSqlParameterSource()
    .addValue("name", student.name())
    .addValue("id", student.id());

int affected = jdbcTemplate.update(sql, params);
```

命名參數不是把字串接進 SQL，而是交給範本物件做參數綁定，所以不會有自己串接輸入值造成的注入風險與格式問題。

*【修改與查詢走不同流程】*

## update、batchUpdate 與 query

> 🏠 **生活比喻**
>
> - `update`＝**一次寄一封信**
> - `batchUpdate`＝**一次把一疊信全部寄出**，省很多跑郵局的時間
> - `query`＝**去郵局領信**

| 方法 | 用途 | 常見結果 |
| --- | --- | --- |
| `update` | 執行 INSERT、UPDATE、DELETE | 受影響的資料筆數 |
| `batchUpdate` | 批次執行多組修改參數 | 各批次受影響的筆數 |
| `query` | 查詢多筆資料 | 由 RowMapper 轉出來的物件集合 |
| `queryForObject` | 預期剛好一筆結果 | 單一值或單一物件 |

主鍵由資料庫產生時，可以搭配 `KeyHolder` 取得新增後的鍵值。批次處理適合「同一段 SQL、每次參數不同」而且量很大的情境。

*【資料列需要一位翻譯】*

## 用 RowMapper 建立領域物件

> 🏠 **生活比喻**
>
> `RowMapper` 像**拆箱員**：倉庫送來一箱一箱（每一列資料），他照說明把每箱拆開、組成一個 Java 物件。

```
public class StudentRowMapper implements RowMapper<Student> {
    @Override
    public Student mapRow(ResultSet rs, int rowNum) throws SQLException {
        return new Student(
            rs.getLong("id"),
            rs.getString("name"),
            rs.getInt("age")
        );
    }
}
```

`ResultSet` 是查詢結果；`RowMapper` 定義每一列怎麼變成 Java 物件。欄位名稱、SQL 型別與 Java 型別要合理對應，資料庫的 `NULL` 也要明確處理。

查詢本來就可能沒有結果時，不要把「查無資料」和真正的資料庫故障混為一談。資料存取層應該把底層狀況轉成上層看得懂的結果或例外。

*【從資料列走向物件關聯】*

## ORM、JPA、Hibernate 與 Spring Data JPA

> 🏠 **生活比喻**
>
> - ORM＝**物件和資料表互相翻譯的概念**
> - JPA＝**翻譯的國際規範**
> - Hibernate＝**照規範做的翻譯社**
> - Spring Data JPA＝**再幫你包好的「一鍵翻譯」服務**

*   **JPA**：持久化的規格，定義實體、關聯與 EntityManager 等 API；已改名 Jakarta Persistence。
*   **Hibernate**：最常見的 JPA 實作，同時也提供自己的 Session API。
*   **Spring Data JPA**：站在 JPA 之上的 Spring Data 模組，用 Repository 把常見的資料操作抽象化。

所以三者不是同一層的替代品，而是疊起來的：JPA 定規格，Hibernate 負責實作，Spring Data JPA 再幫你把 Repository 的重複程式碼省掉。簡單記法是：JPA 負責定義，Hibernate 負責實作。

*【用 Repository 表達資料操作】*

## 基本操作與方法名稱衍生查詢

> 🏠 **生活比喻**
>
> Spring Data JPA 像**會讀名字的管家**：你寫 `findByNameAndAge`，他就**照方法名稱自動組出查詢**，不用寫 SQL。

```
public interface StudentRepository
        extends JpaRepository<Student, Long> {

    List<Student> findByNameContainingAndAgeGreaterThan(
        String keyword,
        int age
    );
}
```

常用操作有 `save`、`findById`、`findAll` 與 `deleteById`。`findById` 回傳 `Optional<T>`，提醒呼叫端資料可能不存在。

方法名的大小寫要完全一致：刪除是 `deleteById(ID id)`，寫成 `deleteByID` 就找不到方法。

`save` 常被說成「集 insert 與 update 於一身」。新增與更新兩種它確實都做得到，但它不是每次都跑兩段。`save` 會先判斷這個實體有沒有被持久化過：還沒有就呼叫 `persist`，已經有就呼叫 `merge`。實際發出什麼 SQL 還會受實體狀態影響[出處](https://docs.spring.io/spring-data/jpa/reference/jpa/entity-persistence.html)。

方法名稱衍生查詢適合簡單條件。名稱長到看不懂，或需求變複雜時，就該換一種比較清楚的查詢寫法。

*【複雜查詢要講清楚用哪種語言】*

## @Query 預設不是原生 SQL

> 🏠 **生活比喻**
>
> `@Query` 預設寫的是 **JPQL（用物件名稱的說法）**；要寫倉庫原本的 SQL 要加 `nativeQuery = true`，像**特別註明「這段用倉庫方言」**。

```
@Query("""
    select s
      from Student s
     where s.active = true
       and s.age >= :minAge
    """)
List<Student> findActiveAdults(@Param("minAge") int minAge);
```

`@Query` 預設使用 JPQL，查的是實體與它的屬性，不是資料表與欄位名。`value` 是要執行的 JPA 查詢，`nativeQuery` 設定這個查詢是不是原生查詢，預設為 false[出處](https://docs.spring.io/spring-data/jpa/docs/current/api/org/springframework/data/jpa/repository/Query.html)。這是很容易踩到的一個坑：把資料表名當成實體名寫進去，執行時就會直接失敗。

> 📝 查證更正：原筆記寫 @Query 的用途是「在Spring Data JPA中，執行原生的SQL語法」，查證後更正：@Query 預設使用 JPQL，查的是實體與屬性；要用資料庫原生 SQL 必須明確寫 nativeQuery = true

原生 SQL 能用到特定資料庫的功能，但換資料庫的成本比較高；JPQL 與衍生查詢則比較貼近實體模型。選哪一種要看查詢複雜度、效能、可讀性，以及你願意跟資料庫綁多緊。

*【同一個容器管理資料基礎設施】*

## DataSource、EntityManagerFactory 與交易

> 🏠 **生活比喻**
>
> - DataSource＝**計程車排班站**（連線來源）
> - EntityManagerFactory＝**管家公司**
> - 交易管理員＝**監督整單作業的主管**；用 JDBC 和 JPA 要配不同的主管

走 JDBC 這條路時，Spring 管的是 `DataSource` 與 JDBC 範本；走 JPA 這條路時，管的是 `EntityManagerFactory`、Repository 與交易管理器。直接整合 Hibernate 時，也可以由 Spring 建立並注入 `SessionFactory`，這樣就不必再自己寫一個 `HibernateUtil`。

Web 容器提供的 JNDI DataSource 也可以交給 Spring 查找並註冊成 Bean，服務就不必自己到全域目錄找連線來源，改用注入取得。

把 Spring 裝進傳統 JavaWeb 專案時，控制器是 Tomcat 建立的 Servlet，Tomcat 不認得 Spring 的 Bean，控制器只能自己用 DL（Dependency Lookup，依賴查找）的方式去取得 Service 物件。改用 Spring MVC 之後就不必了：`@Controller` 是 `@Component` 的特化，會被掃描並註冊成 Spring 管理的 Bean，直接用建構子注入拿 Service 就好。

資料存取技術與交易管理必須配套。多步驟的寫入流程要由服務層建立清楚的交易邊界，而不是讓每個 Repository 各自提交。

早期的做法是用 `web.xml` 加 `ContextLoaderListener` 載入 Spring 組態，那是 Spring Boot 普及之前的常態。現在的專案多半靠自動組態與註解掃描，不會再寫這份部署描述檔。

*【工具沒有高下，只有合不合適】*

## Spring JDBC 與 Spring Data JPA 怎麼選？

> 🏠 **生活比喻**
>
> - Spring JDBC＝**自己開車**，路線完全自己控制，適合複雜報表
> - Spring Data JPA＝**搭計程車**，一般的增刪改查省事很多

| 考量 | Spring JDBC | Spring Data JPA |
| --- | --- | --- |
| SQL 控制 | SQL 明白寫在程式裡，控制最直接 | 透過實體操作、JPQL 或原生 SQL 間接控制 |
| 物件關聯 | 要自己組裝 | 可以宣告關聯與載入策略 |
| 簡單的增刪改查 | 還是要寫 SQL 與對映 | Repository 能省掉大量樣板程式碼 |
| 複雜報表 | 通常能直接精準寫出 SQL | 用 JPQL、原生查詢，或另外搭 JDBC |
| 學習重點 | SQL、參數與 RowMapper | 實體狀態、關聯、交易與查詢策略 |

同一個系統也可以兩者並用：一般實體的增刪改查用 Spring Data JPA，複雜報表用 Spring JDBC。關鍵是交易與分層的邊界要清楚。

### 🗺️ 比喻對照表

| 技術名詞 | 生活比喻 |
| --- | --- |
| JdbcTemplate | 自動洗碗機 |
| batchUpdate | 一次寄一疊信 |
| RowMapper | 拆箱員 |
| JPA / Hibernate | 翻譯規範 / 翻譯社 |
| 衍生查詢 | 會讀方法名稱的管家 |
| JDBC vs JPA | 自己開車 vs 搭計程車 |

### 重點整理

*   Spring JDBC 保留 SQL 的控制力，並省掉連線與資源釋放的樣板程式碼。
*   `update` 處理資料異動，`query` 搭配 `RowMapper` 處理查詢對映。
*   JPA 是規格，Hibernate 是實作，Spring Data JPA 提供 Repository 抽象。
*   `save` 依實體是不是新的決定走 persist 還是 merge，不是固定的 insert 加 update。
*   `@Query` 預設是 JPQL；要原生 SQL 得寫 `nativeQuery = true`。
*   JDBC 與 JPA 可以並用，選擇依據是 SQL 控制、物件關聯、查詢複雜度與維護成本。

## 隨堂測驗

**Q1. NamedParameterJdbcTemplate 相較於位置參數，主要的可讀性優勢是什麼？**

- (A) SQL 可以用有意義的名稱綁定參數
- (B) 不需要任何 DataSource
- (C) 會自動建立所有資料表
- (D) 所有查詢都不必寫 SQL

<details><summary>看答案</summary>

**答案：(A)** 像 :studentId 這樣的命名參數，比一排問號更容易看出用途。

</details>

**Q2. 要執行 INSERT、UPDATE 或 DELETE，通常用哪個方法？**

- (A) update
- (B) query
- (C) mapRow
- (D) findById

<details><summary>看答案</summary>

**答案：(A)** update 回傳受影響的筆數；query 是查詢用的。

</details>

**Q3. RowMapper 的主要責任是什麼？**

- (A) 把 ResultSet 的一列轉成 Java 物件
- (B) 建立資料庫連線池
- (C) 決定 HTTP 回應狀態碼
- (D) 註冊 Spring MVC 攔截器

<details><summary>看答案</summary>

**答案：(A)** RowMapper 把欄位讀取與物件建立的邏輯包在一起。

</details>

**Q4. 關於 JPA 與 Hibernate 的關係，哪一項正確？**

- (A) JPA 是規格，Hibernate 是常見的實作
- (B) Hibernate 是規格，JPA 只是一張資料表
- (C) 兩者都是 HTTP 伺服器
- (D) JPA 是一種 JDBC 驅動程式

<details><summary>看答案</summary>

**答案：(A)** JPA 定義 API 與行為，Hibernate 提供實作，Spring Data JPA 再疊一層抽象。

</details>

**Q5. Spring Data JPA 的 findById 回傳 Optional，主要想表達什麼？**

- (A) 指定識別碼的資料可能不存在
- (B) 每次查詢一定會找到兩筆資料
- (C) 查詢必須在瀏覽器執行
- (D) 實體不能使用主鍵

<details><summary>看答案</summary>

**答案：(A)** Optional 逼呼叫端明確處理「有值」與「沒有值」兩種結果。

</details>

**Q6. Spring Data JPA 的 @Query 預設使用哪一種查詢語言？**

- (A) JPQL
- (B) 資料庫原生 SQL
- (C) SpEL 專用語法
- (D) HTTP 查詢字串

<details><summary>看答案</summary>

**答案：(A)** 預設查的是實體與屬性；要原生 SQL 必須明確寫 nativeQuery = true。

</details>

**Q7. 對一個識別值為 null 的新實體呼叫 save()，通常會發生什麼？**

- (A) 被判斷為新實體，走 persist
- (B) 一定先 insert 再 update 一次
- (C) 一定會拋出例外
- (D) 會直接刪除同主鍵的資料

<details><summary>看答案</summary>

**答案：(A)** save 先判斷實體是不是新的，再決定走 persist 或 merge。

</details>

**Q8. 哪一種需求通常比較適合優先考慮 Spring JDBC？**

- (A) 需要精準控制複雜報表的 SQL
- (B) 需要完全避免接觸關聯式資料庫
- (C) 要把 HTTP 路徑對應到 Controller
- (D) 要管理瀏覽器的畫面元件

<details><summary>看答案</summary>

**答案：(A)** Spring JDBC 適合需要直接掌握 SQL 與結果對映的查詢。

</details>

**Q9. 同一件商業操作要透過兩個 Repository 改資料，交易邊界通常該放在哪裡？**

- (A) 協調這兩個 Repository 的服務層方法
- (B) 每個實體的 getter 方法
- (C) RowMapper 的 mapRow 方法
- (D) application.properties 的某一個設定值

<details><summary>看答案</summary>

**答案：(A)** 服務層掌握完整的工作單位，能確保多個資料操作一起提交或一起還原。

</details>
