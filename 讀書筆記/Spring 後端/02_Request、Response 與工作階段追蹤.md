# 02. Request、Response 與工作階段追蹤

> 來源：[筆記平台 · Spring 後端](https://hhtim.github.io/notes-platform/spring/#/lesson/request-response-session)　第 2 課 / 共 23 課 · 約 13 分鐘

**讀取請求、建立回應、比較轉送與重新導向，再用 Cookie、Session、JDBC 與連線池完成有狀態的資料流程。**

### 讀完這課你會

*   用 HttpServletRequest 讀請求、用 HttpServletResponse 設定回應
*   分辨請求轉送與重新導向，知道什麼時候該用哪一個
*   選擇 Cookie 或 Session 保存狀態，並知道各自的風險
*   說明 JDBC 與連線池各自負責什麼

*【HTTP 文字進入 Java 世界】*

## Request 與 Response 物件

瀏覽器送來的是一串 HTTP 文字。Tomcat 解析完，把內容裝進 `HttpServletRequest`，像把散落的寄件資訊整理成一張表格；Servlet 再透過 `HttpServletResponse` 設定狀態碼、標頭與本體，最後由 Tomcat 組成 HTTP 回應送回去。

這兩個都是介面，實際物件由容器提供。程式只依賴介面，所以不必自己拆解原始的 HTTP 封包。

| 部分 | Request 常見操作 | Response 常見操作 |
| --- | --- | --- |
| 起始列 | `getMethod()`、`getRequestURI()` | `setStatus()` |
| 標頭 | `getHeader(name)` | `setHeader(name, value)` |
| 本體 | `getReader()`、`getInputStream()` | `getWriter()`、`getOutputStream()` |

*【讀懂使用者送來的資料】*

## 取得路徑、參數與請求本體

`getContextPath()` 取得應用程式的情境路徑，避免把部署名稱寫死；`getRequestURI()` 取得請求目標的路徑部分；`getQueryString()` 取得還沒拆開的查詢字串。

處理一般表單時，直接用參數 API 就好，容器會依請求格式把資料整理好：

*   `getParameter("username")`：取得單一參數值。
*   `getParameterValues("hobby")`：取得同名參數的多個值，回傳字串陣列。
*   `getParameterMap()`：取得全部參數及其值陣列。

同名參數是以字串陣列保存的，不是把值串成一個字串。規格裡 `getParameterMap()` 的宣告就是 `Map<String, String[]> getParameterMap()`，而 `getParameterValues(String name)` 回傳一個 `String` 陣列，裝著這個請求參數的所有值[出處](https://jakarta.ee/specifications/servlet/6.0/apidocs/jakarta.servlet/jakarta/servlet/servletrequest)。要取同名參數的多個值，方法名是 `getParameterValues(...)`，不是 `getParameter(...)`。

> 📝 查證更正：原筆記寫 getParameterMap() 時說「可以看到同樣的key(hobby)，會將值放在一起做字串相加(hobby: 1 2)」，查證後更正：getParameterMap() 的值型別是 String[]，同名參數是陣列裡的多個元素，不是把字串接在一起；畫面上看起來像接在一起，只是把陣列印出來的樣子。原筆記在同一段還把「取多個值」的方法名寫成 String[] req.getParameter(...)，正確的方法名是 getParameterValues(...)

要讀純文字本體用 `getReader()`；圖片、壓縮檔這類二進位資料用 `getInputStream()`。兩者讀的是同一個請求本體，通常不能混用，也不能重複讀。

字元編碼要在讀參數或本體之前設定；回應的內容型態與編碼也要在取得 Writer、送出回應之前確定。

```
request.setCharacterEncoding("UTF-8");

String username = request.getParameter("username");

response.setContentType("text/html;charset=UTF-8");
response.getWriter().println("你好，" + username);
```

把使用者輸入直接串進 HTML 會產生跨網站指令碼攻擊（Cross-Site Scripting，XSS）。正式系統要依輸出情境做編碼，並同時做輸入驗證。

*【站內交棒，或請瀏覽器重走一次】*

## 請求轉送與重新導向

請求轉送（Forward）像餐廳內部把同一張點菜單交給另一位廚師：瀏覽器沒有再送一次請求，所以網址通常不變，後續資源也讀得到同一個 request 範圍的資料。

```
request.setAttribute("result", data);
request.getRequestDispatcher("/result.jsp")
       .forward(request, response);
```

重新導向（Redirect）則像櫃台請客人換個地址重排一次：伺服器先回一個重新導向回應，瀏覽器再發出第二次請求。所以網址會變，原本 request 範圍的資料也不會自動留著。

```
response.sendRedirect(
    request.getContextPath() + "/products"
);
```

| 比較 | 轉送 | 重新導向 |
| --- | --- | --- |
| 請求次數 | 一次 | 通常兩次 |
| 瀏覽器網址 | 通常不變 | 會改變 |
| request 屬性 | 可共用 | 不會自動保留 |
| 目標 | 目前應用程式內的伺服器端資源 | 站內或其他可存取的網址都行 |

要不要加情境路徑，判斷的方法不是看有沒有斜線，而是看「下一個請求是誰發出的」：由瀏覽器發出的站內路徑要加情境路徑；容器內部的 `RequestDispatcher` 路徑照 Servlet API 的路徑規則解析，不用加。

*【讓無狀態的 HTTP 記得上下文】*

## Cookie：由瀏覽器保管的小紙條

Cookie 是伺服器請瀏覽器保存的一小段名稱與值。伺服器用 `Set-Cookie` 回應標頭設定，之後瀏覽器在符合網域、路徑、安全與期限等條件時，用 `Cookie` 請求標頭帶回來。

```
Cookie cookie = new Cookie("theme", "dark");
cookie.setMaxAge(7 * 24 * 60 * 60);
cookie.setHttpOnly(true);
cookie.setSecure(true);
response.addCookie(cookie);
```

`setMaxAge()` 設正數是保存秒數，設零表示要求刪除，負數（預設值）表示不指定持久期限、瀏覽器關掉就沒了。刪除時還要用與原本相符的 Path、Domain 等屬性，瀏覽器才找得到正確的那一筆。

一般用途的使用者代理程式（例如瀏覽器）每個 Cookie 應至少支援 4096 位元組，以 Cookie 名稱、值與屬性的長度總和計算（RFC 6265 第 6.1 節）。3KB 不是規格數字，而且計法也不只算值[出處](https://www.rfc-editor.org/rfc/rfc6265#section-6.1)。

> 📝 查證更正：原筆記寫「Cookie最大3KB」，查證後更正：RFC 6265 要求一般用途的瀏覽器每個 Cookie 至少支援 4096 位元組，而且這個長度是名稱、值與所有屬性加起來算的；3KB 不是規格數字

Cookie 不能直接存中文，要先做 URL 編碼。這不是 Java 的限制。RFC 6265 的 `Set-Cookie` 語法把 `cookie-octet` 限定為 US-ASCII 字元，而且排除控制字元、空白、雙引號、逗號、分號與反斜線，中文本來就不在合法字元裡，所以任何語言都得先編碼[出處](https://www.rfc-editor.org/rfc/rfc6265#section-4.1.1)。

Cookie 存在使用者那端，使用者看得到、改得動、刪得掉，所以不能把它當成可信的資料來源。敏感資訊不應該明文放進去；識別資訊也要搭配 HTTPS、`Secure`、`HttpOnly` 與合適的 `SameSite` 設定。

*【資料留在伺服器，瀏覽器只帶識別證】*

## Session：伺服器端的工作階段空間

`HttpSession` 讓同一次工作階段的多次請求之間共用伺服器端的資料。它像寄物櫃：東西放在伺服器，瀏覽器只帶一把工作階段識別碼當鑰匙，容器再用這把鑰匙找到對應的 Session。

```
HttpSession session = request.getSession();
session.setAttribute("username", "Tim");

String username =
    (String) session.getAttribute("username");

// 登出時讓整個 Session 失效
session.invalidate();
```

Cookie 與 Session 的比較裡常見一句「Cookie 不安全，Session 較安全」。這個相對比較沒有錯，但容易讓人放心過頭：工作階段識別碼一樣要在網路上來回傳，被偷到就能冒用整個工作階段。OWASP（Open Worldwide Application Security Project，整理網站安全做法的開放組織）的工作階段管理建議是登入後更換識別碼、使用安全的 Cookie 屬性、整個工作階段都走 HTTPS，並設定閒置逾時[出處](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)。登入資訊該放 Cookie、Session 還是權杖、各自要防什麼攻擊，見〈網站安全三題：CORS、CSRF、密碼學〉。

常聽到「Session 預設 30 分鐘」，那是 Tomcat 在自己的 `conf/web.xml` 裡設的 `<session-timeout>30</session-timeout>`。Servlet 規格把工作階段的預設逾時交給 Servlet 容器決定，本身不訂數字，換容器或改設定就不是這個數[出處](https://jakarta.ee/specifications/servlet/6.1/jakarta-servlet-spec-6.1.html)[Tomcat 預設值](https://github.com/apache/tomcat/blob/main/conf/web.xml)。

「鈍化、活化」（伺服器正常關閉時把 Session 寫進磁碟、重啟時讀回來）是 Tomcat 預設管理員的行為，但那是容器層的實作與設定，不是規格保證。所以程式不該假設重啟後 Session 一定還在，也不該把大型物件塞進去。

*【從 Java 通往關聯式資料庫】*

## JDBC：統一的資料庫操作介面

JDBC（Java Database Connectivity，Java 資料庫連線）是一套標準 API。Java 程式只依賴 JDBC 這組介面，各家資料庫廠商提供驅動程式（Driver）處理自家的通訊細節。就像統一插座規格：應用程式用共同介面，驅動程式負責轉接。

教學裡常見先寫一行 `Class.forName("com.mysql.cj.jdbc.Driver")` 註冊驅動程式。這一行到今天仍然跑得動，但已經不必要：`DriverManager` 初始化時就會自己去找驅動程式，管道之一是用服務提供者載入機制載入 `java.sql.Driver`，現代的驅動程式只要在 classpath 上就會被找到[出處](https://docs.oracle.com/en/java/javase/21/docs/api/java.sql/java/sql/DriverManager.html)。

把 `useSSL=false` 寫進連線網址是關掉傳輸加密，屬於安全性降級，不是效能調校。而且 `useSSL` 已經標為棄用（DEPRECATED），現在該用的是 `sslMode`（預設值 `PREFERRED`），正式環境應該維持加密連線[出處](https://dev.mysql.com/doc/connector-j/en/connector-j-connp-props-security.html)。

> 📝 查證更正：原筆記寫「在url資料庫後面加上?useSSL=false可以提高效能」，查證後更正：useSSL=false 是關掉傳輸加密，屬於安全性降級而不是效能調校；MySQL Connector/J 8 已改用 sslMode 參數，正式環境應維持加密連線

典型流程是取得 `Connection`、建立 `PreparedStatement`、設定參數、執行 SQL、處理 `ResultSet`，最後關閉資源。

```
String sql =
    "SELECT id, username FROM member WHERE email = ?";

try (Connection conn = dataSource.getConnection();
     PreparedStatement stmt = conn.prepareStatement(sql)) {

    stmt.setString(1, email);

    try (ResultSet rs = stmt.executeQuery()) {
        while (rs.next()) {
            long id = rs.getLong("id");
            String username = rs.getString("username");
        }
    }
}
```

`PreparedStatement` 把 SQL 結構與參數值分開處理，可以降低 SQL 注入（SQL Injection）的風險，也方便重複套用不同參數。它取代不了權限控管與輸入驗證，但一定比自己拼字串安全。

`ResultSet` 用來逐列讀查詢結果；要知道欄位數量、名稱或型別這類結構資訊時，才用 `ResultSetMetaData`。更新資料則是取得受影響的列數，不一定有 `ResultSet`。

多個 SQL 必須一起成功或一起失敗時就要用交易（Transaction）：關掉自動提交，成功後 `commit()`，失敗時 `rollback()`。

*【別為每位客人現挖一口井】*

## 資料庫連線池：重複利用昂貴的連線

建立一條資料庫連線要網路交握、驗證與配置資源，每次請求都重開成本很高。連線池會先準備或按需維護一批連線；程式借出來用，用完歸還，下一個請求就能接著用。

`DataSource` 是 JDBC 的標準介面，連線池的實作通常透過它供應 `Connection`。對使用端來說，呼叫 `close()` 通常代表把連線還回池子，而不是關掉底層那條實體連線。

*   省掉頻繁建立連線的成本，縮短等待時間。
*   限制同時使用的連線數，避免資料庫被大量請求壓垮。
*   用逾時、健康檢查與洩漏偵測管理連線。
*   還是要確實關閉 Connection、Statement 與 ResultSet，不然池子會被借光。

連線池不是越大越快。池子大小要配合資料庫的容量、SQL 的執行時間與應用程式的並行量調整。

### 重點整理

*   Request 用來讀請求，Response 用來設定狀態碼、標頭與回應內容。
*   轉送沿用同一次請求；重新導向會要瀏覽器再送一次請求。
*   Cookie 存在瀏覽器端，不可信任；Session 資料在伺服器端，靠 Cookie 裡的識別碼串起多次請求。
*   Session 一樣要防識別碼被偷，不能因為資料在伺服器就當成絕對安全。
*   每個 Cookie 至少支援 4096 位元組，計的是名稱、值與屬性的總長度。
*   JDBC 提供共同介面，驅動程式負責實際通訊；SQL 參數要用 PreparedStatement。
*   連線池重複利用連線，但借出來的資源仍然必須確實關閉歸還。

## 隨堂測驗

**Q1. Tomcat 把收到的 HTTP 請求包成 HttpServletRequest，主要好處是什麼？**

- (A) Servlet 可以用 Java API 讀方法、標頭、路徑與參數，不必自己解析原始 HTTP
- (B) 請求會因此自動取得資料庫管理員權限
- (C) 瀏覽器可以直接操作 Java 物件
- (D) 所有請求都會自動變成同一個 Session

<details><summary>看答案</summary>

**答案：(A)** 容器負責協定解析，應用程式只要照 HttpServletRequest 介面取資料。

</details>

**Q2. 一組核取方塊以相同名稱送出多個值時，最適合用哪個方法取得？**

- (A) getParameterValues(name)
- (B) getParameter(name)
- (C) getHeader(name)
- (D) getContextPath()

<details><summary>看答案</summary>

**答案：(A)** getParameterValues() 以字串陣列回傳同名參數的多個值；getParameter() 只會拿到其中一個。

</details>

**Q3. Servlet 把資料設成 request 屬性後，要交給 JSP 顯示、而且要留在同一次請求裡，該用什麼方式？**

- (A) 用 RequestDispatcher 做請求轉送
- (B) 用 sendRedirect() 重新導向
- (C) 建立新的 Cookie 等下一次請求
- (D) 讓 JDBC 驅動程式直接開啟 JSP

<details><summary>看答案</summary>

**答案：(A)** 轉送沿用同一個 request，所以 JSP 讀得到先前設定的屬性。

</details>

**Q4. 重新導向之後，原本的 request 屬性通常讀不到了，原因是什麼？**

- (A) 瀏覽器會依重新導向的位置送出一個新的 HTTP 請求
- (B) 重新導向會把 request 自動轉成 Cookie
- (C) sendRedirect() 會關掉整個 Tomcat
- (D) 重新導向只允許存取資料庫資源

<details><summary>看答案</summary>

**答案：(A)** 重新導向包含伺服器回應與瀏覽器的新請求，因此產生新的 request 範圍。

</details>

**Q5. 單一個 Cookie 的大小是怎麼規定的？**

- (A) 瀏覽器至少要支援 4096 位元組，且計的是名稱、值與屬性的總長度
- (B) 固定上限是 3KB，只算值的長度
- (C) 沒有任何建議，各家瀏覽器完全自由
- (D) 每個 Cookie 最多只能放 256 個字元

<details><summary>看答案</summary>

**答案：(A)** 一般用途的瀏覽器每個 Cookie 至少要支援 4096 位元組，含名稱、值與所有屬性。

</details>

**Q6. 關於 Cookie 與 Session 的關係，哪一項正確？**

- (A) Session 資料通常在伺服器端，瀏覽器用 Cookie 帶著工作階段識別碼
- (B) Session 內容一定完整存在 Cookie 裡
- (C) Cookie 只能由 JDBC 建立
- (D) 工作階段識別碼外流也不會被冒用

<details><summary>看答案</summary>

**答案：(A)** 瀏覽器通常只保存識別碼，伺服器再用它找到對應的 Session 資料。

</details>

**Q7. 「Session 的預設逾時是 30 分鐘」這句話，比較精確的說法是什麼？**

- (A) Servlet 規格沒有規定預設值，30 分鐘是 Tomcat 自己設的
- (B) 那是 HTTP 協定規定的固定值
- (C) 那是 JDBC 連線池的預設逾時
- (D) 所有 Java Web 容器都被規格要求設成 30 分鐘

<details><summary>看答案</summary>

**答案：(A)** 預設逾時由容器決定，換容器或改設定就不是這個數字。

</details>

**Q8. PreparedStatement 相較於自己拼接 SQL 字串，最重要的優點是什麼？**

- (A) 把 SQL 結構與參數值分開處理，可降低 SQL 注入風險
- (B) 保證所有 SQL 都不需要交易
- (C) 讓 ResultSet 永遠只有一列
- (D) 讓資料庫不再需要帳號與權限

<details><summary>看答案</summary>

**答案：(A)** 參數化查詢不會把參數值當成 SQL 結構的一部分，但仍要搭配權限與輸入驗證。

</details>

**Q9. 從 DataSource 取得池化的 Connection 後，呼叫 close() 通常代表什麼？**

- (A) 把連線還回連線池，讓後續請求重複使用
- (B) 永久關閉整個資料庫伺服器
- (C) 提交所有還沒完成的交易
- (D) 刪除連線池裡的全部連線

<details><summary>看答案</summary>

**答案：(A)** 連線池通常會代理 Connection，close() 是歸還資源，不是關掉資料庫。

</details>
