# 01. Servlet 與 JavaWeb 基礎

> 來源：[筆記平台 · Spring 後端](https://hhtim.github.io/notes-platform/spring/#/lesson/servlet-javaweb)　第 1 課 / 共 23 課 · 約 12 分鐘

**從 HTTP、Tomcat 與 Servlet 生命週期，建立 JavaWeb、JSP、MVC 與三層式架構的整體觀念。**

### 讀完這課你會

*   說明瀏覽器、Web 伺服器與 Servlet 三者怎麼合作完成一次請求
*   看懂 Servlet 的生命週期，以及路徑是怎麼對應到程式的
*   知道 JSP、EL、JSTL 各自負責什麼
*   分辨 MVC 與三層式架構在解決哪兩件不同的事

*【先看全貌】*

## JavaWeb 是什麼？

JavaWeb 是「用 Java 寫、透過瀏覽器使用」的那一整套技術。使用者這端只需要瀏覽器，畫面、商業規則與資料的主要處理都在伺服器上，所以這類系統常被稱為瀏覽器／伺服器架構（Browser/Server，簡稱 B/S）。

可以把網站想成餐廳：瀏覽器是顧客，HTTP 請求是點菜單，伺服器是餐廳，HTTP 回應是送上桌的餐點。Servlet 就是接單並安排後續流程的那個人，必要時還會去資料庫拿料。

| 角色 | 主要工作 | 常見內容 |
| --- | --- | --- |
| 瀏覽器 | 送出請求並把結果畫出來 | HTML、CSS、JavaScript |
| Web 伺服器／Servlet 容器 | 收 HTTP、找資源、管理 Servlet | Tomcat |
| Servlet | 處理請求、控制應用程式流程 | Java 類別 |
| 資料庫 | 保存與查詢長期資料 | MySQL、Oracle Database |

Java 分成三種版本：Java SE（標準版）、Java EE（企業版）、Java ME（手持裝置版）。本課只談企業版這條線。

*【兩端的共同語言】*

## HTTP 的請求與回應

HTTP（Hypertext Transfer Protocol，超文字傳輸協定）規範瀏覽器與伺服器怎麼交換資料。它採一問一答的請求—回應模型，而且協定本身不會自動記住上一次互動，這個性質叫無狀態（Stateless）。

HTTP 本身不提供加密，它送在 TCP 上，或送在一條受 TLS 加密的 TCP 連線上——TLS（Transport Layer Security，傳輸層安全協定，專門替連線加密）是外加的那一層，加在 HTTP 底下就是 HTTPS；而且 HTTP/2 以前的版本跑在 TCP 上，HTTP/3 改用以 UDP 為基礎的 QUIC[出處](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Overview)[HTTP/3](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Evolution_of_HTTP)。

> 📝 查證更正：原筆記寫「HTTP協議是基於TCP協議，面向連接、安全」，查證後更正：HTTP 本身不提供任何加密或身分驗證，安全來自外加的 TLS；而且 HTTP/3 已改跑在以 UDP 為基礎的 QUIC 上，不再是「一定基於 TCP」。原筆記另在「HTTP ?」這個標題底下直接把 HTTP 解釋成 HTTPS，兩者是不同層的東西

HTTP 與 HTTPS 常被當成同一件事，但它們是不同層的東西。HTTP/3 與 QUIC 的細節見〈HTTP 與 HTTPS〉。

| 訊息 | 組成 | 用途 |
| --- | --- | --- |
| HTTP 請求 | 請求列、請求標頭、可有可無的訊息本體 | 說明方法、目標路徑與送出的資料 |
| HTTP 回應 | 狀態列、回應標頭、可有可無的訊息本體 | 說明處理結果與傳回的內容 |

GET 通常用來取得資源，參數放在網址的查詢字串；POST 通常用來提交資料，資料多半放在請求本體。但 HTTP 方法描述的是語意，不代表 GET 天生安全或 POST 會自動加密。

常聽到的說法是「POST 優於 GET，因為 GET 能帶的參數有限制」。就實務結果來說，網址確實有長度天花板，但那個限制不是 HTTP 協定訂的。RFC 9110 只建議所有發送端與接收端至少支援 8000 位元組長度的網址，真正卡住你的是各家瀏覽器與伺服器自己的實作上限[出處](https://www.rfc-editor.org/rfc/rfc9110#name-uri-references)。

> 瀏覽器 → HTTP 請求 → Web 伺服器／Servlet 容器 → Servlet → HTTP 回應 → 瀏覽器

狀態碼看首位數字就能分類：2xx 成功、3xx 重新導向、4xx 用戶端的請求有問題、5xx 伺服器處理失敗。200 是成功、404 是找不到資源、500 是伺服器內部錯誤。

*【把通訊細節交給容器】*

## Tomcat 與 Servlet 的分工

Servlet 是在 Servlet 容器裡執行的伺服器端 Java 元件。它不像一般 Java 程式靠自己的 `main()` 啟動，而是由容器建立物件、呼叫方法，並把請求與回應物件傳進來。

Tomcat 同時提供 HTTP 連線處理與 Servlet 容器功能。它把收到的 HTTP 文字解析成 `HttpServletRequest`，再建立 `HttpServletResponse` 讓程式設定；處理完成後，容器再把回應物件轉回 HTTP 送給瀏覽器。

*   **通訊支援**：處理連線與 HTTP 訊息解析。
*   **生命週期管理**：載入、建立、初始化、銷毀 Servlet。
*   **並行處理**：讓多個請求可能同時進入同一個 Servlet 實例。
*   **設定與安全管理**：依部署設定套用路徑、權限與其他規則。
*   **JSP 支援**：把 JSP 轉換並編譯成 Servlet。

容器只負責分配與管理執行緒，不會替你把同步問題解決掉。容器可能把並行的請求送進同一個 `service` 方法，開發者必須自己為多執行緒的並行處理做好準備（規格第 2.3.3.1 節）[出處](https://jakarta.ee/specifications/servlet/6.1/jakarta-servlet-spec-6.1.html)。同一個 Servlet 通常只有一個實例服務所有請求，所以不要把每位使用者的請求資料存進可變的實例欄位，否則兩個請求會互相覆寫。執行緒池怎麼運作、競爭條件與 `synchronized` 擋得住什麼，見〈執行緒與並行〉。

> 📝 查證更正：原筆記寫容器的「多執行緒支援: 每一個Servlet都會執行Java的執行緒(Thread)，而Container也負責建立及管理多的執行緒問題，已解決Synchronization(同步)的問題」，查證後更正：容器只負責分配執行緒，執行緒安全仍是應用程式自己的責任，Servlet 規格要求開發者自行處理共享資源的同步

ServletContext 是規格裡的一個具體 API 物件，定義了一組讓 Servlet 跟它的 Servlet 容器溝通的方法；每個 Web 應用程式在每個 Java 虛擬機裡各有一個 context。它是應用程式用來對容器說話的那個物件，不是容器本身，更不是 Web 伺服器的同義詞[出處](https://jakarta.ee/specifications/servlet/6.0/apidocs/jakarta.servlet/jakarta/servlet/servletcontext)。

> 📝 查證更正：原筆記寫「Web服務器 = Servlet Container = Sevlet Context = Servlet環境」，查證後更正：ServletContext 是規格裡的一個 API 物件，代表一個 Web 應用程式在容器中的執行環境，和「Web 伺服器」「Servlet 容器」不是同義詞

*【套件名換過一次】*

## javax.servlet 已經改叫 jakarta.servlet

Servlet 屬於 Java EE（Java Enterprise Edition）這一整套規範，同一套底下還有 JDBC、JSP 等。這個歸屬到今天沒變，但名字與套件名後來整批換過。

名稱與套件整批換過一次：Java EE 移交 Eclipse 基金會後因為商標問題改名為 Jakarta EE，Jakarta EE 9 把所有 `javax.*` 套件改成 `jakarta.*`。Tomcat 9 與 10 之間因此有一個重大的不相容變更：規格 API 的 Java 套件從 `javax...` 改成 `jakarta...`，Web 應用程式必須用新的 API 重新編譯；從 Tomcat 9 以前搬到 Tomcat 10 以後，幾乎一定要修改程式碼[出處](https://tomcat.apache.org/migration-10.html)[下載頁](https://tomcat.apache.org/download-10.cgi)。

> 📝 查證更正：這是版本差異不是原筆記寫錯：原筆記寫「Servlet 屬於J2EE的架構」「JavaEE: Java Enterprise Edition (Java企業版)」，在它寫成的年代是正確的名稱。後來 Java EE 移交 Eclipse 基金會、因商標問題改名 Jakarta EE，Jakarta EE 9 把所有 javax.* 套件改成 jakarta.*，Tomcat 10 起只認 jakarta.servlet

```
// Tomcat 9 以前
import javax.servlet.http.HttpServlet;

// Tomcat 10 之後
import jakarta.servlet.http.HttpServlet;
```

套件名用錯世代時，編譯錯誤是「找不到類別」，而不是「套件名不對」，所以常被誤判成相依套件沒加好。

*【容器掌管程式的一生】*

## Servlet 生命週期

Servlet 的一生像店員上班：先報到一次（初始化），接著反覆接待客人（處理請求），最後下班收尾（銷毀）。

1.  **載入與建立**：容器載入 Servlet 類別並建立實例。預設在第一次收到對應請求時發生，也可以設定成啟動時就載入。
2.  **初始化**：容器呼叫 `init()`，只呼叫一次，適合讀設定或準備共用資源。
3.  **服務請求**：每次請求都進 `service()`；對 `HttpServlet` 來說，再依 HTTP 方法分派到 `doGet()`、`doPost()` 等方法。
4.  **結束服務**：應用程式停止、重新部署或容器關閉時，容器呼叫 `destroy()`，讓程式釋放自己持有的資源。

```
@WebServlet("/hello")
public class HelloServlet extends HttpServlet {
    @Override
    protected void doGet(HttpServletRequest request,
                         HttpServletResponse response)
            throws IOException {
        response.setContentType("text/html;charset=UTF-8");
        response.getWriter().println("<h1>你好，Servlet！</h1>");
    }
}
```

`@WebServlet("/hello")` 是容器找到這個 Servlet 的門牌（URL Pattern，路徑樣式）。使用者實際打的網址還會包含主機、連接埠，以及應用程式的情境路徑（Context Path）。

只要有一個 Servlet 重新載入，同一個 Web 應用程式裡的所有 Servlet 都會跟著一起重新載入，原因是每次重新載入都會換掉一個類別載入器（Class Loader）。部署到同一個 Tomcat 實例的每一個 Web 應用程式，各自有一個類別載入器，`WEB-INF/classes` 與 `WEB-INF/lib` 的類別只對這個應用程式可見。換掉這個載入器，整個應用程式的類別就一起換掉，但不會波及同一台 Tomcat 上的其他應用程式[出處](https://tomcat.apache.org/tomcat-10.1-doc/class-loader-howto.html)。

*【相依套件與部署】*

## Web 應用程式怎麼交給 Tomcat

傳統 JavaWeb 應用程式會打包成 WAR 檔部署。編譯後的類別放在 `WEB-INF/classes`，應用程式專用的 JAR 放在 `WEB-INF/lib`，部署描述檔是 `WEB-INF/web.xml`。改用註解設定路徑時，就不一定要在 `web.xml` 裡逐一登記 Servlet。

建置工具裡的 Servlet API 相依套件通常設成 `provided`：編譯時需要這組介面，執行時由 Tomcat 提供。如果又把另一份不相容的 API 打包進應用程式，就可能發生類別衝突。

現在的 Spring Boot 專案多半改成內嵌伺服器、打包成可執行的 JAR，不再手動丟 WAR 到 Tomcat 的 webapps 資料夾。WAR 這條路仍然可用，但已不是預設做法。

*【動態畫面的傳統做法】*

## JSP、EL 與 JSTL

JSP（JavaServer Pages）讓你在以 HTML 為主的頁面裡產生動態內容。它第一次被使用時，容器會把 JSP 轉成 Servlet 原始碼再編譯，所以 JSP 骨子裡還是靠 Servlet 機制執行。

早期 JSP 可以用腳本元素直接塞 Java 程式碼進去，但那會讓畫面與邏輯糾纏在一起。比較清楚的做法是：Servlet 把資料準備好，JSP 再用 EL（Expression Language，運算式語言）與 JSTL（JSP Standard Tag Library，JSP 標準標籤函式庫）把資料顯示與迭代出來。

*   **${brands}**：從範圍物件裡找名稱叫 brands 的資料。
*   **page 範圍**：只在目前這一頁有效。
*   **request 範圍**：只在目前這次請求中有效，適合 Servlet 轉送給 JSP 的資料。
*   **session 範圍**：在同一次工作階段的多次請求之間有效。
*   **application 範圍**：整個 Web 應用程式共用。

同名屬性可能同時存在不同範圍。沒有明確指定範圍時，EL 會依序往上找，所以大型專案要避免意義不清的同名資料。

*【別讓程式擠成一團】*

## MVC 與三層式架構

MVC 像餐廳前場的分工：控制器接單（Controller）、模型處理規則與資料（Model）、視圖負責擺盤呈現（View）。在傳統 Servlet／JSP 應用程式裡，Servlet 常當控制器，JSP 當視圖，Java 物件與服務構成模型。

| 觀點 | 組成 | 在回答什麼問題 |
| --- | --- | --- |
| MVC | Model、View、Controller | 一次 Web 互動怎麼接收、處理與呈現 |
| 三層式架構 | 展示層、商業邏輯層、資料存取層 | 整個應用程式的責任怎麼分層 |

兩者不是二選一。Servlet 與 JSP 位在展示層；控制器呼叫商業邏輯層的 Service；Service 再呼叫資料存取層的 DAO（Data Access Object，資料存取物件）。這樣做可以降低類別之間的綁定程度，讓測試、分工與抽換實作都容易一些。

> 瀏覽器 → Controller（Servlet）→ Service → DAO → 資料庫  
> 瀏覽器 ← View（JSP）← Controller

### 重點整理

*   HTTP 是瀏覽器與伺服器的溝通規則；加密來自外掛的 TLS，協定本身不保證安全。
*   Tomcat 解析 HTTP、管理 Servlet，把請求與回應包成 Java 物件交給程式。
*   Servlet 由容器建立，依序經歷初始化、反覆服務請求、銷毀。
*   同一個 Servlet 實例可能同時處理多個請求，容器不會替你處理同步，別用實例欄位存單次請求的狀態。
*   Jakarta EE 9 起套件名從 `javax.*` 改成 `jakarta.*`，Tomcat 10 之後只認新的。
*   JSP 負責呈現畫面，EL 與 JSTL 讓頁面少寫 Java 程式碼。
*   MVC 描述互動角色，三層式架構描述應用程式責任，兩者可以一起用。

## 隨堂測驗

**Q1. Tomcat 收到 HTTP 請求後，最核心的工作是什麼？**

- (A) 解析請求、建立請求與回應物件，再呼叫對應的 Servlet
- (B) 把 Java 原始碼傳給瀏覽器執行
- (C) 把每個 HTTP 請求永久保存到 Session
- (D) 直接用 JDBC 把每個請求寫進資料庫

<details><summary>看答案</summary>

**答案：(A)** 容器負責 HTTP 與 Servlet 之間的轉換，以及 Servlet 的生命週期管理。

</details>

**Q2. Servlet 為什麼通常不需要自己的 main() 方法？**

- (A) 它由容器建立，生命週期與請求處理方法也由容器呼叫
- (B) 它會由瀏覽器直接建立
- (C) JSP 會替每個 Servlet 產生 main()
- (D) JDBC 驅動程式負責啟動 Servlet

<details><summary>看答案</summary>

**答案：(A)** Servlet 是受容器管理的元件，進入點與方法呼叫都由 Servlet 容器掌控。

</details>

**Q3. 同一個 HttpServlet 實例可能同時收到多個請求，設計時要注意什麼？**

- (A) 別用可變的實例欄位保存單一使用者的請求資料
- (B) 把每次請求都放進 ServletConfig
- (C) 讓 doGet() 一次只接待一位使用者
- (D) 把所有區域變數改成 static 欄位

<details><summary>看答案</summary>

**答案：(A)** 容器可能以多個執行緒共用同一個實例，共享的可變欄位會互相覆寫；容器不會替你處理同步。

</details>

**Q4. Servlet 的 init() 最適合做哪一類工作？**

- (A) 一次性的初始化，例如讀設定或準備共用資源
- (B) 處理每一筆 GET 查詢參數
- (C) 替瀏覽器畫出 HTML 畫面
- (D) 在每次 SQL 查詢後關閉連線

<details><summary>看答案</summary>

**答案：(A)** init() 在 Servlet 建立後只呼叫一次；每次請求的工作應該放在服務方法裡。

</details>

**Q5. 一份 Tomcat 9 年代的 Servlet 程式搬到 Tomcat 10，最先會遇到什麼問題？**

- (A) import 的套件要從 javax.servlet 改成 jakarta.servlet
- (B) HTTP 方法從 GET 改成 POST 才會生效
- (C) web.xml 必須改寫成 JSON 格式
- (D) 所有 JSP 都要改寫成 HTML

<details><summary>看答案</summary>

**答案：(A)** Jakarta EE 9 把 javax.\* 整批改成 jakarta.\*，Tomcat 10 只認新的套件名。

</details>

**Q6. 關於 JSP，哪一項正確？**

- (A) 容器會把 JSP 轉換並編譯成 Servlet 再提供服務
- (B) JSP 是只能由瀏覽器執行的 JavaScript 檔案
- (C) JSP 裡不可以包含任何 HTML
- (D) JSP 會取代 HTTP 協定

<details><summary>看答案</summary>

**答案：(A)** JSP 是伺服器端的頁面技術，執行基礎仍然是 Servlet。

</details>

**Q7. 在傳統 Servlet／JSP 的 MVC 做法中，哪一種分工最合理？**

- (A) Servlet 接收請求並協調流程，JSP 呈現結果
- (B) JSP 負責所有資料庫交易，Servlet 只保存圖片
- (C) Servlet 只負責 CSS，JSP 負責建立 TCP 連線
- (D) DAO 顯示頁面，瀏覽器直接呼叫資料庫

<details><summary>看答案</summary>

**答案：(A)** Servlet 常當 Controller，JSP 當 View，資料存取交給模型或 DAO。

</details>

**Q8. MVC 與三層式架構的關係，哪一項最恰當？**

- (A) 兩者可以搭配使用，分別描述互動角色與應用程式的責任分層
- (B) 用了 MVC 之後就不能建立資料存取層
- (C) 三層式架構要求 View 直接連線資料庫
- (D) 兩者只是 Servlet 生命週期的不同叫法

<details><summary>看答案</summary>

**答案：(A)** 兩者關注的切面不同，實務上常同時採用。

</details>

**Q9. Servlet API 的相依套件常設成 provided，主要原因是什麼？**

- (A) 編譯時需要這組介面，部署後由 Servlet 容器提供
- (B) Servlet API 只允許在單元測試中使用
- (C) 這樣瀏覽器才會下載 Servlet API
- (D) 這樣資料庫才會自動建立資料表

<details><summary>看答案</summary>

**答案：(A)** provided 表示建置時可用、執行環境會提供，可降低重複或版本衝突的風險。

</details>
