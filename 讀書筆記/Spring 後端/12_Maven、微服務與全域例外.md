# 12. Maven、微服務與全域例外

> 來源：[筆記平台 · Spring 後端](https://hhtim.github.io/notes-platform/spring/#/lesson/maven-microservices)　第 12 課 / 共 23 課 · 約 13 分鐘

**從 Maven 的建置與相依管理，延伸到微服務的取捨，以及 Spring Web 請求的統一錯誤處理。**

### 讀完這課你會

*   看懂 Maven 的 POM、座標、相依範圍與生命週期
*   比較單體式架構與微服務，知道各自付出什麼代價
*   認出請求在 Filter、DispatcherServlet 與 Controller 之間怎麼流動
*   分別處理 Controller 層與 Filter 層丟出的例外

*【專案建置】*

## Maven 解決什麼問題？

Maven 是 Java 專案的建置與管理工具。它像一份標準化的施工圖：用 POM（Project Object Model，專案物件模型）描述專案資訊、相依套件與建置規則，讓不同開發工具與自動化環境都能用同一套方式處理專案。

*   提供標準目錄，正式程式、測試程式與資源各有固定位置。
*   提供編譯、測試、打包與安裝等建置流程。
*   用座標宣告第三方程式庫，並自動解析它們的相依套件。

| 目錄 | 用途 |
| --- | --- |
| `src/main/java` | 正式的 Java 原始碼 |
| `src/main/resources` | 正式環境的資源與組態 |
| `src/test/java` | 測試的 Java 原始碼 |
| `src/test/resources` | 測試需要的資源 |

不同開發工具各自產生的目錄結構不一樣，專案很難互通，這正是這套標準目錄要解決的事：只要都走 Maven，結構就一致，同一個專案換工具打開也沒問題。

*【套件的身分證】*

## Maven 座標與相依範圍

Maven 座標像套件的收件地址，用來唯一辨識你要用的成品。

*   **groupId**：所屬的組織或命名空間。
*   **artifactId**：專案或模組名稱。
*   **version**：成品版本。

```
<dependency>
  <groupId>com.example</groupId>
  <artifactId>order-client</artifactId>
  <version>1.2.0</version>
  <scope>test</scope>
</dependency>
```

相依範圍（scope）決定套件在哪些階段可用。沒寫的時候預設是 `compile`；`test` 只在測試的編譯與執行時可用；`runtime` 表示執行時需要、但正式原始碼編譯時不直接依賴它的 API；`provided` 表示編譯時需要，執行環境會提供——〈Servlet 與 JavaWeb 基礎〉講的 Servlet API 就是這一類。

*【建置流程】*

## 生命週期與階段

Maven 主要有 clean、default 與 site 三套生命週期。常用的 `compile`、`test`、`package`、`install` 是 default 生命週期裡的階段；執行比較後面的階段時，同一套生命週期裡排在前面的階段會依序先跑。

| 指令 | 主要效果 |
| --- | --- |
| `mvn clean` | 執行 clean 生命週期，清掉先前的建置產出。 |
| `mvn compile` | 編譯正式程式碼。 |
| `mvn test` | 先完成必要的前置階段，再執行測試。 |
| `mvn package` | 測試後產生 JAR 或 WAR 等成品。 |
| `mvn install` | 把成品裝進本機的 Maven 儲存庫，供其他本機專案引用。 |

> 💡 執行 `mvn package` 是不是只做打包？

不是。它會照 default 生命週期的順序先完成前置階段，例如編譯與測試，才進到 package。

*【架構選擇】*

## 單體式系統與微服務

單體式系統把會員、商品、付款與報表都部署在同一個應用程式裡；微服務則依業務能力拆成可以各自部署的服務。重點是切出清楚的業務邊界，不是把每個類別都變成一個服務。

| 面向 | 單體式架構 | 微服務架構 |
| --- | --- | --- |
| 部署 | 整包一起部署 | 各服務可以獨立部署 |
| 擴充 | 通常擴充整個應用程式 | 可以只針對高流量的服務擴充 |
| 開發協調 | 程式集中，起步比較直接 | 團隊自主性高，但介面協調變多 |
| 失敗影響 | 共用同一個行程，故障容易擴大 | 可以隔離部分故障，但要設計逾時與降級 |
| 資料一致性 | 本機交易好處理 | 跨服務的一致性複雜得多 |
| 維運成本 | 服務數少，初期較低 | 需要監控、追蹤、部署與服務治理的能力 |

拆開不等於自動隔離。把功能做成服務之後，應用程式必須被設計成能夠容忍服務的失敗——會需要這樣設計，正是因為一個服務掛掉會影響呼叫它的人。要真的隔離，得另外做逾時、重試上限、斷路器與降級[出處](https://martinfowler.com/articles/microservices.html)。

> 📝 查證更正：原筆記把微服務的好處寫成「壓力分散：各功能獨立運行，某個模組出問題不會影響其他模組」，查證後更正：Martin Fowler 的微服務一文明講「把功能做成服務的後果之一，是應用程式必須被設計成能夠容忍服務的失敗」；會需要這樣設計就代表故障不會自己隔離，要隔離得另外做逾時、重試上限、斷路器與降級

*   **逾時（timeout）**：等下游回覆等到一個時間就放棄，不要無限等下去，把自己也拖垮。
*   **斷路器（circuit breaker）**：像家裡的無熔絲開關：發現某個下游一直失敗，就先直接擋掉對它的呼叫、不要再一直試，等一段時間再放行探一次。
*   **降級（fallback）**：下游叫不到的時候，改給一個堪用的替代結果，例如回傳快取的舊資料或一份預設清單，讓畫面還是出得來。

*【拆分的思維】*

## 微服務不是免費的效能按鈕

可以這樣比喻：全聯的收銀台本來收銀員要結帳又要裝袋，後來改成只負責結帳，裝袋交給顧客。微服務也用類似方式讓團隊與元件各自負責清楚的業務能力。差別在於軟體服務之間還多了網路延遲、失敗重試與資料一致性的問題。

微服務可能帶來的好處包括獨立部署、個別擴充、技術選擇的彈性，以及把單次變更的範圍縮小。但這些好處要成立，前提是邊界劃得合理、介面穩定，而且有足夠的自動化測試與維運能力。

主要的挑戰包括：

*   切得太細，網路呼叫與跨團隊溝通的成本反而變高。
*   API 或訊息格式一改，就要處理版本相容與團隊協調。
*   跨服務的交易、追蹤、日誌彙整與故障排查都更難。
*   某個服務故障，仍可能透過同步依賴連鎖影響其他服務。

> 短期的活動網站、小型團隊，或業務還在快速變動的時候，模組化的單體通常比太早拆成微服務更好維護。Martin Fowler 的講法是「不該用微服務開始一個新專案，即使你確定這個應用程式會大到值得這麼做」[出處](https://martinfowler.com/bliki/MonolithFirst.html)。

*【一次 Web 請求的完整路徑】*

## Filter 為什麼比 Controller 更早看到請求？

瀏覽器送出的請求先進 Servlet 容器，再通過 Filter 鏈，之後才到 Spring MVC 的 `DispatcherServlet`。DispatcherServlet 找到對應的 Controller，完成參數解析與方法呼叫，回應再反向穿過 Filter 鏈出去。

```
用戶端
  ↓
Servlet 容器
  ↓
Filter 鏈（可能包含 Spring Security）
  ↓
DispatcherServlet
  ↓
HandlerMapping／Interceptor
  ↓
Controller
  ↓
回應反向通過 Filter 鏈
  ↓
用戶端
```

這三種東西沒辦法排成一條線。Spring Security 的 Servlet 支援包含在 `FilterChainProxy` 之內，`FilterChainProxy` 是 Spring Security 提供的一個特殊 `Filter`；因為它是一個 Bean，通常會被包在 `DelegatingFilterProxy` 裡，再用容器自己的標準機制註冊。也就是說，「Spring Security Filter」在容器眼中只是那條鏈上的其中一格，安全 Filter 彼此的順序是那一格內部的事，不能跟容器那條鏈上的 Filter 放在同一條順序上比大小[出處](https://docs.spring.io/spring-security/reference/servlet/architecture.html)。

> 📝 查證更正：原筆記在「主要區別」寫「執行順序：Servlet Filter 最先執行，然後是 Spring Security Filter，最後是 Spring 內建 Filter」，查證後更正：官方文件寫明「Spring Security 的 Servlet 支援包含在 FilterChainProxy 之內」，而 FilterChainProxy 本身只是容器 Filter 鏈上的一格（通常包在 DelegatingFilterProxy 裡註冊）。安全 Filter 彼此的先後是那一格內部的事，跟容器那條鏈上的 Filter 不在同一個層級，沒辦法排成一條線

*【MVC 範圍內的錯誤】*

## 用全域例外處理器統一 Controller 的回應

`@RestControllerAdvice` 可以集中處理 Spring MVC 方法執行期間傳出的例外，把它們轉成一致的 HTTP 狀態與回應格式。

```
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<ApiError> handleBusiness(
            BusinessException ex) {
        ApiError body = new ApiError(
            ex.getCode(),
            ex.getMessage()
        );
        return ResponseEntity
            .status(HttpStatus.BAD_REQUEST)
            .body(body);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiError> handleUnexpected(
            Exception ex) {
        ApiError body = new ApiError(
            "INTERNAL_ERROR",
            "系統暫時無法處理請求"
        );
        return ResponseEntity
            .status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(body);
    }
}
```

對外的回應不要直接吐出堆疊追蹤、資料庫語法、權杖或內部主機資訊。詳細例外記進受控的日誌，回應只給穩定的錯誤碼與使用者看得懂的訊息。

*【MVC 範圍外的錯誤】*

## Filter 丟的例外為什麼常常抓不到？

`@ControllerAdvice` 只參與 DispatcherServlet 內部的例外解析。Filter 跑在 DispatcherServlet 外圍，所以它在呼叫下游之前或期間丟出的例外，不會自然進到 MVC 的全域例外處理器。

常見的處理策略有三種：

*   在 Filter 裡自己接住例外，直接設定 HTTP 狀態、內容型態與 JSON 回應。
*   把可共用的錯誤轉換邏輯抽成一個獨立服務，讓 Filter 與全域例外處理器共用。
*   把例外交給適當的例外解析器或容器的錯誤處理流程，但要避免重複寫入已經送出的回應。

```
try {
    filterChain.doFilter(request, response);
} catch (BusinessException ex) {
    response.setStatus(HttpServletResponse.SC_BAD_REQUEST);
    response.setContentType("application/json;charset=UTF-8");
    response.getWriter().write(
        errorJson(ex.getCode(), ex.getMessage())
    );
}
```

有一種說法是用 `ServletRequestListener` 在請求開始與結束時捕捉例外，這條路行不通。它只宣告兩個方法，兩個都只吃一個 `ServletRequestEvent` 參數，沒有任何例外物件；`requestDestroyed` 是在 ServletRequest 即將離開這個 Web 應用程式的範圍時通知，那時候回應多半也已經送出、改不動了[出處](https://jakarta.ee/specifications/servlet/6.0/apidocs/jakarta.servlet/jakarta/servlet/servletrequestlistener)。

> 📝 查證更正：原筆記把「使用 ServletRequestListener：這可以在請求開始和結束時執行代碼,你可以在這裡捕獲異常」列為四種處理方式之一，查證後更正：ServletRequestListener 的 requestDestroyed 只收到一個 ServletRequestEvent，裡面沒有例外物件，而且此時回應多半已經送出、改不動了，所以拿它捕捉並改寫錯誤回應行不通

如果是 Spring Security 的認證或授權錯誤，應該用安全框架自己提供的認證進入點與拒絕存取處理器，而不是把所有錯誤都包成一般的 Controller 例外。

*【錯誤端點】*

## 用 /error 之前要理解它的轉送條件

容器或 Spring Boot 可以把未處理的錯誤分派到 `/error`，再由錯誤控制器建立回應。但這不是「Filter 一丟例外就一定會呼叫你的自訂方法」：會不會進到錯誤分派、能拿到哪些請求屬性、回應是不是已經送出，都會影響結果。

採用自訂錯誤控制器時，至少要檢查狀態碼、例外物件、原始路徑與回應是否已送出，並且不要把未知例外的內部訊息直接丟給用戶端。

> Controller 例外 → MVC 例外解析；Filter 例外 → Filter、安全框架或容器的錯誤流程

*【串起來看】*

## 建置、架構與錯誤格式其實互相牽動

Maven 讓每個服務都能用一致的方式編譯、測試與打包；微服務讓服務可以各自部署；全域例外處理讓 API 的錯誤格式保持一致。如果各服務各自回傳不同的錯誤結構，即使部署已經拆開，用戶端整合起來還是很痛苦。

所以可以把錯誤碼規則、追蹤識別碼與共用回應模型講定成一份明確的約定。共用程式庫可以透過 Maven 發布，但要控制相容性，別讓所有服務被迫同時升級。

### 重點整理

*   Maven 用 POM 管理座標、相依套件與標準化的建置流程。
*   執行生命週期後段的階段時，同一套生命週期的前置階段會先跑。
*   微服務能獨立部署與擴充，但網路、資料一致性與維運成本都會增加。
*   同步依賴會讓故障連鎖，隔離要靠逾時、斷路器與降級自己設計。
*   Spring Security 的整組安全 Filter 在容器眼中只是鏈上的一格，容器 Filter 與安全 Filter 不能排成同一條順序。
*   `@RestControllerAdvice` 只管得到 Spring MVC 範圍內的例外。
*   錯誤回應要穩定且不洩漏內部資訊，細節留在受控日誌。

## 隨堂測驗

**Q1. Maven 的 POM 主要扮演什麼角色？**

- (A) 描述專案資訊、相依套件與建置設定
- (B) 取代 JVM 執行 Java 位元碼
- (C) 直接管理資料庫交易
- (D) 攔截所有 HTTP Filter 例外

<details><summary>看答案</summary>

**答案：(A)** POM 是 Maven 用來管理整個專案的那份描述檔。

</details>

**Q2. Maven 座標裡的 artifactId 通常表示什麼？**

- (A) 專案或模組的名稱
- (B) 套件所屬的組織或命名空間
- (C) 執行 Java 的 JDK 路徑
- (D) 相依套件可用的生命週期

<details><summary>看答案</summary>

**答案：(A)** groupId 是組織，artifactId 是專案或模組，version 是版本。

</details>

**Q3. 執行 mvn package 時，哪一項敘述正確？**

- (A) 會先執行 default 生命週期裡排在 package 前面的必要階段
- (B) 只會壓縮檔案，不會編譯或測試
- (C) 一定會把成品發布到遠端儲存庫
- (D) 會自動刪掉所有 Maven 相依套件

<details><summary>看答案</summary>

**答案：(A)** 同一套生命週期裡，跑後面的階段會先把前面的階段跑完。

</details>

**Q4. 相依範圍寫成 provided 的意思是什麼？**

- (A) 編譯時需要，執行環境會提供
- (B) 只在測試時可用
- (C) 執行時需要，但編譯時用不到
- (D) 發布到遠端儲存庫時才需要

<details><summary>看答案</summary>

**答案：(A)** Servlet API 就是典型的 provided，執行時由 Servlet 容器提供。

</details>

**Q5. 哪一項最能說明微服務與單體式架構的差異？**

- (A) 微服務依業務邊界拆成可獨立部署的服務，單體通常整包一起部署
- (B) 微服務不必處理網路失敗，單體才要
- (C) 微服務一定只能用一種程式語言
- (D) 單體式系統無法建立任何內部模組

<details><summary>看答案</summary>

**答案：(A)** 差別在部署與邊界，不在於誰不用處理網路問題。

</details>

**Q6. 為什麼微服務的故障不一定能完全隔離？**

- (A) 同步的服務依賴可能讓逾時或失敗形成連鎖影響
- (B) 所有微服務一定共用同一個 JVM 行程
- (C) mvn package 會合併所有服務的資料庫
- (D) 每個服務都必須使用相同的連接埠

<details><summary>看答案</summary>

**答案：(A)** 要真的隔離，得另外設計逾時、斷路器與降級。

</details>

**Q7. @RestControllerAdvice 最適合處理哪一類例外？**

- (A) Spring MVC 處理流程中由 Controller 等元件傳出的例外
- (B) 作業系統啟動 JVM 前發生的錯誤
- (C) Maven 下載相依套件時的網路中斷
- (D) Servlet 容器外部設備的硬體故障

<details><summary>看答案</summary>

**答案：(A)** 它參與的是 DispatcherServlet 內部的例外解析。

</details>

**Q8. Filter 直接丟出的例外，為什麼常常不會被 MVC 全域例外處理器接到？**

- (A) Filter 跑在 DispatcherServlet 外圍，例外沒有進到 MVC 的例外解析流程
- (B) Filter 只能走成功路徑，Java 不允許它丟例外
- (C) ControllerAdvice 只能處理資料庫主鍵衝突
- (D) DispatcherServlet 一定比所有 Filter 更早執行

<details><summary>看答案</summary>

**答案：(A)** 位置決定了誰看得到這個例外。

</details>

**Q9. 要對外回傳一個非預期的系統例外，哪種設計比較安全？**

- (A) 回傳穩定的錯誤碼與一般訊息，詳細堆疊記進受控日誌
- (B) 把完整堆疊、SQL 與權杖全部放進 JSON
- (C) 不論什麼錯誤都回 HTTP 200 且不給錯誤碼
- (D) 把例外訊息當成 Maven 版本號回傳

<details><summary>看答案</summary>

**答案：(A)** 對外回應不該洩漏內部資訊，細節留在日誌裡。

</details>
