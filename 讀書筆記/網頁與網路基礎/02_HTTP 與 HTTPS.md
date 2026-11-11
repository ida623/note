# 02. HTTP 與 HTTPS

> 來源：[筆記平台 · 網頁與網路基礎](https://hhtim.github.io/notes-platform/web/#/lesson/http-https)　第 2 課 / 共 15 課 · 約 7 分鐘

**看懂 Web 的請求回應規則，以及 TLS 如何替 HTTP 加上身分驗證、加密與完整性保護。**

### 讀完這課你會

*   看懂 HTTP 請求與回應的基本結構
*   依用途選擇常見 HTTP 方法
*   從狀態碼判斷處理結果
*   解釋 HTTPS 與 TLS 提供的保護及限制

*【Web 的共同語言】*

## HTTP 是請求與回應的規則

HTTP（Hypertext Transfer Protocol，超文字傳輸協定）是應用層協定。瀏覽器等用戶端送出請求，伺服器回傳回應；傳送內容不只 HTML，也可能是 JSON、圖片、影音或其他資料。

HTTP 是無狀態協定（Stateless Protocol）：每個請求在協定語意上可以獨立處理。若網站需要記住登入狀態或購物車，通常會搭配 Cookie、Session 或權杖（Token）。這三種各放在哪裡、各要防什麼攻擊，見〈網站安全三題：CORS、CSRF、密碼學〉。

*【寄出需求單】*

## HTTP Request 有哪些部分？

```
GET /products/42 HTTP/1.1
Host: shop.example.com
Accept: application/json
Authorization: Bearer <token>
```

*   **方法（Method）**：想對資源做什麼。
*   **目標**：路徑與查詢參數，例如 `/products/42`。
*   **標頭（Headers）**：主機、可接受格式、認證、快取條件等附加資訊。
*   **訊息本體（Body）**：要傳送的資料；並非每個請求都有。

| 方法 | 常見語意 | 提醒 |
| --- | --- | --- |
| GET | 讀取資源 | 應避免造成資源狀態改變 |
| POST | 提交資料或建立資源 | 重送可能重複產生效果 |
| PUT | 以請求附上的資源內容（表示，representation）建立或取代目標資源 | 具冪等性 |
| PATCH | 局部修改資源 | 不保證具冪等性 |
| DELETE | 刪除資源 | 具冪等性 |

冪等性（idempotent）：同一個請求重複送多次，結果和送一次相同。HTTP 規格（RFC 9110）把 PUT、DELETE 與安全方法（safe method，只讀不改的方法，例如 GET、HEAD）都列為冪等[出處](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.2)；PATCH 不保證冪等（RFC 5789），POST 通常也沒有。

*【伺服器回單】*

## Response 與狀態碼

```
HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: max-age=60

{"id":42,"name":"網路入門"}
```

回應包含狀態行、標頭與可選的訊息本體。三位數狀態碼先以第一位數分類：

*   **1xx**：資訊性回應，表示處理仍在進行。
*   **2xx**：成功，例如 200 OK、201 Created。
*   **3xx**：重新導向或快取相關，例如 301、304。
*   **4xx**：伺服器認為問題出在請求這一端：格式不對、沒有權限、或找不到目標，例如 400、401、403、404。
*   **5xx**：伺服器處理失敗，例如 500、503。

「4xx 是前端寫錯、5xx 是後端寫錯」太武斷；狀態碼描述 HTTP 結果分類，不足以單獨判定是哪個團隊造成問題。

*【明信片與密封信】*

## HTTP 與 HTTPS 的差別

一般 HTTP 沒有替應用資料提供 TLS 保護，沿途能觀察流量的一方可能讀取或竄改內容。HTTPS 則是透過 TLS 保護 HTTP 通訊，不是另一套取代 HTTP 語意的應用協定。

> HTTPS = HTTP + TLS

HTTP 的常見預設連接埠是 80，HTTPS 是 443；但服務也能設定其他連接埠。連接埠本身不會產生加密，真正提供保護的是 TLS。

*【先驗身分再談秘密】*

## TLS 交握做了什麼？

TLS 交握的目的，是協商版本與加密參數、驗證伺服器憑證，並建立後續通訊使用的工作階段金鑰。現代 TLS 通常使用非對稱密碼技術進行身分驗證與金鑰協商，再以效率較高的對稱式加密保護大量資料。

現行的 TLS 1.3 已移除「用伺服器公鑰加密預主金鑰（pre-master secret）」這種靜態 RSA 金鑰交換，一律使用具前向保密性（forward secrecy）的暫時性金鑰交換——就算私鑰日後外洩，過去的通訊也解不開[出處](https://www.rfc-editor.org/rfc/rfc8446)。

> 📝 查證更正：原筆記把交握寫成「客戶端生成預主密鑰（Pre-Master Secret），使用服務器公鑰加密後發送」，查證後更正：那是舊式 RSA 金鑰交換；TLS 1.3 已移除靜態 RSA 與靜態 Diffie-Hellman，全部改用有前向保密性的金鑰交換

1.  用戶端送出支援的 TLS 版本、加密選項及交握資料。
2.  伺服器選擇參數並送出憑證等交握資料。
3.  瀏覽器檢查憑證鏈、有效期限及名稱是否符合。
4.  雙方完成金鑰交換並推導工作階段金鑰。
5.  後續 HTTP 訊息在受保護的連線中傳輸。

憑證通常由受信任的憑證機構（Certificate Authority，CA）簽發，也可能使用組織自建 CA。它把網站名稱與公開金鑰等資料綁在一起；私密金鑰則必須由伺服器端妥善保管。

*【三種核心保護】*

## HTTPS 能保護什麼？

*   **機密性**：降低通訊內容遭沿途偷看的風險。
*   **完整性**：讓雙方能偵測資料是否在傳輸途中遭竄改。
*   **身分驗證**：透過憑證確認連線對象控制相符的網域與私密金鑰。

HTTPS 不代表網站內容一定可信，也無法單獨阻擋釣魚、惡意程式、應用程式漏洞或 DDoS。它保護的是傳輸通道，不是替整個網站品質背書。

*【效能與實務】*

## HTTPS 的成本沒有想像中那麼單純

TLS 會增加交握與加解密工作，但現代硬體、連線重用及 HTTP/2、HTTP/3 等技術可降低影響。憑證不一定要花錢買——Let's Encrypt 這類免費憑證機構可以自動簽發與更新 TLS 憑證[出處](https://letsencrypt.org/)，因此不應把「一定很慢、一定要付費買憑證」當成 HTTPS 的固定缺點。

> 📝 查證更正：原筆記寫「使用 SSL 加密須購買 SSL 憑證，造成開發端增加額外的開發成本」，查證後更正：已有免費憑證機構；原筆記後段的搬遷步驟其實也提到 Let's Encrypt 免費方案，前後矛盾

網站遷移到 HTTPS 時，常見工作包括取得並自動更新憑證、將 HTTP 重新導向 HTTPS、修正混合內容、更新 canonical URL 與分析工具設定，最後測試憑證鏈、重新導向及所有資源。

*【版本差異】*

## HTTP 不一定都跑在同一種傳輸上

HTTP/1.1 與 HTTP/2 通常使用 TCP；HTTP/3 則運行在以 UDP 為基礎的 QUIC 上，並整合 TLS 1.3[出處](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Evolution_of_HTTP)[RFC 9001](https://www.rfc-editor.org/rfc/rfc9001.html)。因此「HTTP 一定透過 TCP」只適用於部分版本。

> 📝 查證更正：原筆記寫 HTTP「實際上是藉由 TCP 作為資料的傳輸方式」，查證後補充：這只適用於 HTTP/1.1 與 HTTP/2；HTTP/3 改用以 UDP 為基礎的 QUIC，並整合 TLS 1.3。QUIC 與 TLS 1.3 的關係見 RFC 9001：「This document describes how QUIC [QUIC-TRANSPORT] is secured using TLS [TLS13].」

### 重點整理

*   HTTP 定義請求、回應、方法、標頭與狀態碼的語意。
*   HTTPS 是受 TLS 保護的 HTTP，提供機密性、完整性與身分驗證。
*   HTTPS 不會自動消除網站漏洞、釣魚或 DDoS 等其他風險。

## 隨堂測驗

**Q1. HTTP 的「無狀態」代表什麼？**

- (A) 每個請求在協定語意上可獨立處理
- (B) 伺服器永遠不能保存任何資料
- (C) HTTP 回應不能包含 Body
- (D) 瀏覽器每次都必須更換 IP

<details><summary>看答案</summary>

**答案：(A)** 需要跨請求保存狀態時，可另搭配 Cookie、Session 或權杖。

</details>

**Q2. 只想讀取一項資源時，最常使用哪個方法？**

- (A) GET
- (B) POST
- (C) PATCH
- (D) DELETE

<details><summary>看答案</summary>

**答案：(A)** GET 的常見語意是取得資源，而且應避免造成資源狀態改變。

</details>

**Q3. HTTP 404 最直接表示什麼？**

- (A) 找不到所請求的資源
- (B) TLS 憑證一定過期
- (C) 伺服器已永久關機
- (D) 請求已成功建立資源

<details><summary>看答案</summary>

**答案：(A)** 404 屬於 4xx，表示伺服器找不到請求目標。

</details>

**Q4. HTTPS 的核心關係為何？**

- (A) HTTP 通訊受到 TLS 保護
- (B) HTTP 被 DNS 完全取代
- (C) TCP 自動變成網域名稱
- (D) 只要使用 443 就一定安全

<details><summary>看答案</summary>

**答案：(A)** HTTPS 保留 HTTP 語意，並以 TLS 保護傳輸。

</details>

**Q5. TLS 為何通常不以非對稱加密處理全部應用資料？**

- (A) 對稱式加密更適合高效率處理大量資料
- (B) 公開金鑰不能參與任何交握
- (C) HTTP 不允許使用公開金鑰
- (D) 憑證已包含所有網頁內容

<details><summary>看答案</summary>

**答案：(A)** 非對稱技術主要用於驗證與金鑰協商，後續資料通常以對稱式金鑰保護。

</details>

**Q6. 瀏覽器驗證伺服器憑證時，哪項檢查最合理？**

- (A) 名稱、有效期限與信任鏈是否有效
- (B) 網站的所有內容是否真實
- (C) 伺服器永遠不會遭 DDoS
- (D) 網頁是否沒有 JavaScript

<details><summary>看答案</summary>

**答案：(A)** 憑證驗證連線身分，不替網站內容與應用安全全面背書。

</details>

**Q7. 下列哪項不是 HTTPS 單獨就能保證的？**

- (A) 網站沒有應用程式漏洞
- (B) 傳輸內容較不易遭竊聽
- (C) 傳輸途中遭竄改可被偵測
- (D) 連線對象可透過憑證驗證

<details><summary>看答案</summary>

**答案：(A)** HTTPS 保護通訊通道，仍須另外處理程式漏洞、權限與營運安全。

</details>

**Q8. 關於 HTTP 底層傳輸，哪項正確？**

- (A) HTTP/3 使用以 UDP 為基礎的 QUIC
- (B) 所有 HTTP 版本都只能使用 TCP
- (C) HTTPS 完全不需要傳輸層
- (D) HTTP/1.1 必須使用 QUIC

<details><summary>看答案</summary>

**答案：(A)** HTTP/1.1、HTTP/2 通常跑在 TCP 上，HTTP/3 則使用 QUIC。

</details>
