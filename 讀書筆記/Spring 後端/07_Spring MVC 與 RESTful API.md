# 07. Spring MVC 與 RESTful API

> 來源：[筆記平台 · Spring 後端](https://hhtim.github.io/notes-platform/spring/#/lesson/spring-mvc-rest)　第 7 課 / 共 23 課 · 約 13 分鐘

**從一次 HTTP 往返出發，設計分層清楚、輸入有驗證、錯誤回得正確的 RESTful API。**

### 讀完這課你會

*   把路徑、HTTP 方法與參數對應到 Spring MVC 的 Controller
*   知道資料可能藏在路徑、查詢字串、標頭或本體，各自用哪個註解取得
*   依 REST 風格設計資源網址與狀態碼
*   在進入商業邏輯前擋掉不合法的輸入，並統一處理例外

*【一次 Web 溝通的基本單位】*

## HTTP 請求與回應

用戶端先送出 HTTP 請求，伺服器處理後傳回 HTTP 回應。請求包含方法、網址、標頭與可能存在的本體；回應包含狀態碼、標頭與可能存在的本體。HTTP 的版本演進、狀態碼與 HTTPS 見〈HTTP 與 HTTPS〉。

```
POST /api/students HTTP/1.1
Content-Type: application/json

{"name":"小安","age":20}
```

```
HTTP/1.1 201 Created
Location: /api/students/42
Content-Type: application/json

{"id":42,"name":"小安","age":20}
```

回應裡那個 `Location` 不是裝飾。201 建立出來的主要資源由回應中的 `Location` 標頭指出；沒有 `Location` 標頭，就以目標網址為準。而這次的目標網址是 `/api/students` 這個集合，不是剛建好的那一筆。所以用 POST 對集合新增時，要自己把新資源的網址放進 `Location`，用戶端才知道去哪裡拿它[出處](https://www.rfc-editor.org/rfc/rfc9110#name-201-created)。

POST 的請求本體一樣是明文傳送。HTTP 訊息設計上就是人看得懂的，它送在 TCP 上，或送在一條受 TLS 加密的 TCP 連線上——加密來自 TLS 而不是方法。POST 跟 GET 的差別只在資料不會出現在網址、瀏覽紀錄與伺服器存取紀錄裡[出處](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Overview)。機密資料要不要安全，取決於 HTTPS、權限控管與資料處理方式；GET 也不該帶密碼或權杖。

> 📝 查證更正：原筆記把 GET 比喻成明信片、POST 比喻成信封，寫「POST 傳遞的參數不會被別人看見，安全性較高」，查證後更正：POST 的請求本體一樣是明文，沒有 TLS 保護時整段都看得到；POST 的差別只在資料不會出現在網址、瀏覽紀錄與伺服器存取紀錄裡，不等於加密

*【把請求送到正確的方法】*

## Controller 與路徑對應

`@RestController` 讓類別成為 Web 控制器，而且方法的回傳值預設會直接寫進回應本體。可以把它看成 `@Controller` 加 `@ResponseBody` 的便利組合。

```
@RestController
@RequestMapping("/api/students")
public class StudentController {
    @GetMapping("/{id}")
    public StudentResponse find(@PathVariable long id) {
        return studentService.find(id);
    }
}
```

`@RequestMapping` 可以同時設定路徑與方法；`@GetMapping`、`@PostMapping`、`@PutMapping`、`@DeleteMapping` 則是語意更清楚的快捷寫法。

*【資料可能藏在四個地方】*

## 路徑、查詢字串、標頭與本體

| 請求裡的位置 | Spring 註解 | 適合放什麼 |
| --- | --- | --- |
| 路徑 `/students/42` | `@PathVariable` | 特定資源的識別碼 |
| 查詢字串 `?page=2` | `@RequestParam` | 篩選、排序、分頁等條件 |
| 請求標頭 | `@RequestHeader` | 媒體格式、驗證資訊、追蹤資訊 |
| 請求本體 | `@RequestBody` | 新增或更新所需的結構化資料 |

請求本體不是 POST 專屬。PUT 的語意就是用請求訊息裡附上的內容，去建立或取代目標資源的狀態，本體是它的必要組成，PATCH 同理，`@RequestBody` 在這些方法上都用得上[出處](https://www.rfc-editor.org/rfc/rfc9110#name-put)。PUT 的典型寫法就是兩個註解一起用：`@PathVariable` 指出要換掉哪一筆，`@RequestBody` 帶進新的內容。

> 📝 查證更正：原筆記寫「request body => POST方法限定」，查證後更正：PUT 與 PATCH 同樣常帶請求本體，@RequestBody 也可以用在這些方法上；原筆記自己在「設計RESTful API」那篇也寫了 PUT 要同時用 @PathVariable 與 @RequestBody，前後其實互相矛盾

缺少必填的 `@RequestParam` 通常會直接變成用戶端錯誤（400），要讓它非必填就加 `required=false` 或 `defaultValue`。JSON 少了欄位時能不能接受，則應該由型別與驗證規則明確決定，不要依賴 Java 欄位自動變成 `null`：前端少送一個該有的屬性時，後端預設不會報錯，只會拿到 `null`，這就是沒有加驗證時的行為。

*【網址描述資源，方法表達動作】*

## RESTful API 的基本設計

REST 是一種架構風格。常見做法是用名詞式網址表示資源，再用 HTTP 方法表達操作，避免把動作名稱重複塞進網址。

| 需求 | 方法與路徑 | 常見的成功狀態 |
| --- | --- | --- |
| 取得學生清單 | `GET /api/students` | `200 OK` |
| 取得單一學生 | `GET /api/students/{id}` | `200 OK` |
| 新增學生 | `POST /api/students` | `201 Created` |
| 完整更新學生 | `PUT /api/students/{id}` | `200 OK` 或 `204 No Content` |
| 刪除學生 | `DELETE /api/students/{id}` | `204 No Content` |

資源有階層關係時可以設計成 `/students/{studentId}/courses`。層級不宜無限加深；子資源本身如果可以獨立識別，也可以提供比較扁平的網址。

*【JSON 的值不只四種】*

## 輸入與輸出的資料結構

JSON 的值可以是物件、陣列、數字、字串，以及 `true`、`false`、`null` 這三個字面值。常見的「整數、浮點數、字串、布林」這種四種說法漏掉了物件、陣列與 `null`，而且 JSON 的數字並不分整數與浮點數兩型[出處](https://www.rfc-editor.org/rfc/rfc8259#section-3)。

> 📝 查證更正：原筆記寫 JSON 的「Value四種類型: 整數、浮點數、字串、Boolean」，查證後更正：RFC 8259 定義 JSON 的值可以是物件、陣列、數字、字串，以及 true、false、null 這三個字面值；原筆記漏掉了物件、陣列與 null，而且數字在 JSON 裡不分整數與浮點數兩型

```
{
  "id": 42,
  "name": "小安",
  "active": true,
  "tags": ["java", "spring"],
  "address": {
    "city": "臺北市"
  }
}
```

Spring MVC 會透過訊息轉換器在 JSON 與 Java 物件之間轉換。API 的輸入輸出建議用專用的 DTO（Data Transfer Object，資料傳輸物件），不要直接把資料庫實體的所有欄位暴露出去，驗證與版本調整也會比較清楚。

*【不合法的資料在入口就擋下】*

## Bean Validation 與 @Valid

Bean Validation 是 Jakarta 的驗證規格：用註解宣告欄位要符合什麼條件（不可為空、數值下限之類），再由框架在進入方法前檢查。Spring MVC 在標了 `@Valid` 的參數上執行這些檢查。

```
public record CreateStudentRequest(
    @NotBlank String name,
    @Min(0) int age
) {}

@PostMapping
public ResponseEntity<StudentResponse> create(
        @Valid @RequestBody CreateStudentRequest request) {
    StudentResponse created = studentService.create(request);
    return ResponseEntity
            .created(URI.create("/api/students/" + created.id()))
            .body(created);
}
```

`ResponseEntity.created(...)` 會一次把狀態碼設成 201 並填好 `Location`，比自己寫 `status(HttpStatus.CREATED)` 再補標頭不容易漏。

*   **@NotNull**：不可以是 null，但空字串會過。
*   **@NotEmpty**：字串、集合或陣列不可以是空的。
*   **@NotBlank**：字串去掉前後空白後還要有內容，最適合姓名這類欄位。
*   **@Min**：數值的下限。

驗證註解的套件名也跟著 Jakarta 改過：Spring Boot 2 以前是 `javax.validation`，Spring Boot 3 起是 `jakarta.validation`。

*【成功與失敗都要說清楚】*

## ResponseEntity 與統一的例外處理

`ResponseEntity` 可以明確指定狀態碼、標頭與本體。找不到資源要回適當的 4xx，不要把所有情況都包成 `200 OK`。

```
@RestControllerAdvice
public class ApiExceptionHandler {
    @ExceptionHandler(StudentNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleNotFound(
            StudentNotFoundException ex) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
                .body(new ErrorResponse("STUDENT_NOT_FOUND", ex.getMessage()));
    }
}
```

`@ControllerAdvice` 搭配 `@ExceptionHandler` 可以集中處理多個 Controller 的例外；純 API 的專案常直接用 `@RestControllerAdvice`。處理器可以針對具體的例外給精準回應，再留一個比較一般的例外處理當最後防線。

例外處理會沿著繼承關係往上找：找不到處理 `IllegalArgumentException` 的方法時，會往上找 `RuntimeException`，一路到 `Exception`。所以最後防線寫到 `Exception` 就夠了。

*【每一層只做好自己的事】*

## Controller、Service、Repository 與攔截器

| 元件 | 主要責任 |
| --- | --- |
| Controller | 接收 HTTP 請求、轉換輸入、建立 HTTP 回應。 |
| Service | 執行商業規則、協調資料操作與交易。 |
| DAO／Repository | 把資料存取細節包起來。 |
| Interceptor（攔截器） | 在 Controller 前後執行 Web 層的共同處理。 |

Spring MVC 的攔截器實作 `HandlerInterceptor`，再透過 `WebMvcConfigurer.addInterceptors` 註冊。`preHandle()` 回傳 `true` 代表繼續往下走，回傳 `false` 就停在這裡、不送到 Controller。

攔截器適合請求追蹤、地區判斷這類 MVC 流程的需求。完整的身分驗證與授權應該用專門的安全框架，不要在一般攔截器裡自己拼一套安全規則——〈Spring Security 認證與授權〉會談這件事。

### 重點整理

*   路徑識別資源，HTTP 方法表達操作；POST 本身不代表資料已加密。
*   `@PathVariable`、`@RequestParam`、`@RequestHeader`、`@RequestBody` 分別取請求裡不同位置的資料。
*   請求本體不是 POST 專屬，PUT 與 PATCH 也常帶。
*   JSON 的值有物件、陣列、數字、字串、true、false、null 七種。
*   用 DTO 搭配 `@Valid` 與驗證註解，在進入商業邏輯前就檢查輸入。
*   Controller 處理 HTTP，Service 處理商業規則，Repository 處理資料存取。

## 隨堂測驗

**Q1. HTTP 回應中，哪個部分最直接表示處理結果是成功還是錯誤？**

- (A) 狀態碼
- (B) 請求路徑
- (C) Controller 類別名稱
- (D) Java 套件名稱

<details><summary>看答案</summary>

**答案：(A)** 狀態碼用標準化的方式表示成功、用戶端錯誤或伺服器錯誤。

</details>

**Q2. @RestController 的主要效果是什麼？**

- (A) 讓類別成為控制器，而且方法回傳值預設寫進回應本體
- (B) 讓類別中每個方法自動開啟資料庫交易
- (C) 把所有方法改成非同步執行
- (D) 自動把每個網址參數存進資料庫

<details><summary>看答案</summary>

**答案：(A)** 它等於 @Controller 加上 @ResponseBody。

</details>

**Q3. 要取得 /api/students/42 裡的 42，最適合用哪個註解？**

- (A) @PathVariable
- (B) @RequestParam
- (C) @RequestHeader
- (D) @RequestBody

<details><summary>看答案</summary>

**答案：(A)** 42 是網址路徑樣式裡的資源識別值。

</details>

**Q4. GET /api/students?page=2 裡的 page，最適合怎麼取得？**

- (A) 用 @RequestParam
- (B) 用 @PathVariable
- (C) 用 @ExceptionHandler
- (D) 用 @Transactional

<details><summary>看答案</summary>

**答案：(A)** page 位在查詢字串，這是 @RequestParam 的工作。

</details>

**Q5. 關於 @RequestBody 與 HTTP 方法的關係，哪一項正確？**

- (A) 不限於 POST，PUT 與 PATCH 同樣常帶請求本體
- (B) 只有 POST 能帶請求本體
- (C) 只有 GET 能帶請求本體
- (D) 請求本體必須放在網址的查詢字串

<details><summary>看答案</summary>

**答案：(A)** 能不能帶本體由 API 的設計約定與方法語意決定，不是 POST 專屬。

</details>

**Q6. 下列哪個 REST API 設計最適合新增學生？**

- (A) POST /api/students
- (B) GET /api/createStudent
- (C) DELETE /api/students
- (D) PUT /api/findStudent

<details><summary>看答案</summary>

**答案：(A)** 對集合資源用 POST 通常表示建立一個新的子資源，動作不該寫進網址。

</details>

**Q7. 關於 JSON 的值，哪一項正確？**

- (A) 可以是物件、陣列、數字、字串，以及 true、false、null
- (B) 只有整數、浮點數、字串、布林值四種
- (C) 只能是字串
- (D) 一定要是陣列

<details><summary>看答案</summary>

**答案：(A)** JSON 的值包含物件與陣列，也包含 null 這個字面值。

</details>

**Q8. 姓名不可以是 null、空字串或只有空白，最適合用哪個驗證註解？**

- (A) @NotBlank
- (B) @NotNull
- (C) @Min
- (D) @PathVariable

<details><summary>看答案</summary>

**答案：(A)** @NotNull 擋不掉空字串，@NotBlank 才要求去掉空白後仍有內容。

</details>

**Q9. 一項操作要同時建立訂單並扣除庫存，哪一層最適合協調這兩步？**

- (A) Service
- (B) Controller
- (C) Interceptor
- (D) Repository

<details><summary>看答案</summary>

**答案：(A)** Service 負責商業流程，能協調多個資料存取操作與它們的交易邊界。

</details>
