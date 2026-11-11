# 10. 網站安全三題：CORS、CSRF、密碼學

> 🏠 **生活化版本**：每個段落開頭的「生活比喻」先用日常情境帶你抓到感覺，接著再看原本的技術說明與程式碼；篇末有「比喻對照表」可以快速複習。

> 來源：[筆記平台 · Spring 後端](https://hhtim.github.io/notes-platform/spring/#/lesson/web-security)　第 10 課 / 共 23 課 · 約 11 分鐘

**釐清跨來源存取、偽造請求與資料保護這三個常被混在一起的網站安全問題。**

### 讀完這課你會

*   判斷兩個網址是不是同源，並說明預檢請求在做什麼
*   說明 Cookie 為什麼讓網站可能遭遇 CSRF，以及防線怎麼設
*   分辨編碼、加密與雜湊各自的用途
*   選對保存密碼的方式

*【先分清楚「來源」】*

## CORS 與瀏覽器的同源政策

> 🏠 **生活比喻**
>
> 同源政策像**瀏覽器規定：A 網站的程式不能隨便讀 B 網站的回覆**。CORS 是 **B 網站主動說「我允許 A 來讀」**，像**住戶在警衛室留訪客名單**。

同源政策（Same-Origin Policy）是瀏覽器的安全機制。兩個網址要通訊協定、主機名稱與連接埠三者都一樣才算同源，只要其中一項不同就是跨來源。

| 網址 A | 網址 B | 結果 | 原因 |
| --- | --- | --- | --- |
| `https://api.example.com/a` | `https://api.example.com/b` | 同源 | 只有路徑不同 |
| `https://example.com` | `http://example.com` | 跨來源 | 通訊協定不同 |
| `https://example.com` | `https://api.example.com` | 跨來源 | 主機名稱不同 |
| `https://example.com:443` | `https://example.com:8443` | 跨來源 | 連接埠不同 |

CORS（Cross-Origin Resource Sharing，跨來源資源共用）讓伺服器用回應標頭告訴瀏覽器：哪些來源、方法與標頭可以跨來源使用。它約束的是瀏覽器要不要把回應交給前端程式，不是伺服器對伺服器請求的通用防火牆。

整個跨來源請求的過程裡，控制瀏覽器行為的其實是後端程式：規則由伺服器用回應標頭發出，真正執行這些規則的是瀏覽器。

*【先問能不能送，再送真的請求】*

## 簡單請求與預檢請求

> 🏠 **生活比喻**
>
> - 簡單請求＝**直接送信過去**
> - 預檢請求（OPTIONS）＝**送重要包裹前先打電話問「我可以寄這種包裹給你嗎？」**，對方說可以才真的寄

符合特定方法、標頭與內容型態條件的跨來源請求可以直接送出，叫簡單請求（Simple Request）。方法限 `GET`、`HEAD`、`POST`，內容型態限 `application/x-www-form-urlencoded`、`multipart/form-data`、`text/plain` 這三個安全清單上的值。

條件有一項不符合，瀏覽器就會先送一個 `OPTIONS` 預檢請求（Preflight Request），問伺服器允不允許接下來要用的方法與標頭。預檢過了才送實際請求。

```
瀏覽器
  → OPTIONS /orders
     Origin: https://shop.example
     Access-Control-Request-Method: PUT
  ← Access-Control-Allow-Origin: https://shop.example
     Access-Control-Allow-Methods: PUT
  → PUT /orders
  ← 實際回應
```

*   **Access-Control-Allow-Origin**：允許讀取這個回應的來源。
*   **Access-Control-Allow-Methods**：允許使用的 HTTP 方法。
*   **Access-Control-Allow-Headers**：允許送出的請求標頭。
*   **Access-Control-Allow-Credentials**：允不允許帶 Cookie 這類憑證。
*   **Access-Control-Max-Age**：瀏覽器可以把預檢結果快取多久。

要允許瀏覽器帶 Cookie，前端與後端都得配合設定，而且回應的允許來源不能寫萬用字元 `*`，必須列出明確的來源。

兩者可以一起用。只要在 Spring Security 啟用 `cors` 支援、又沒有另外給 `CorsConfigurationSource`，它就會沿用提供給 Spring MVC 的 CORS 設定，`@CrossOrigin` 就屬於這一套。真正的關鍵是順序：預檢請求不帶 Cookie，Spring Security 若先跑就會判定未認證而擋掉，所以 CORS 必須排在它前面處理[出處](https://docs.spring.io/spring-security/reference/servlet/integrations/cors.html)。

> 📝 查證更正：原筆記寫「@CrossOrigin 不能和 Spring Security 同時使用」，查證後更正：官方文件說明兩者可以一起用，做法是在 Spring Security 啟用 cors 支援、不另外給 CorsConfigurationSource，它就會「使用提供給 Spring MVC 的 CORS 設定」（頁面上沒有點名 @CrossOrigin，它屬於 Spring MVC 的 CORS 設定是推論）；真正的關鍵是「CORS must be processed before Spring Security, because the pre-flight request does not contain any cookies」——預檢請求不帶 Cookie，如果 Spring Security 先跑就會判定未認證而擋掉

CORS 可以設在 Spring MVC、Spring Security 或反向代理層。挑一個地方統一管，不要讓不同層回傳互相矛盾的標頭；也可以統一交給反向代理（reverse proxy，站在應用程式前面代收請求的伺服器，例如 Nginx）處理。

*【瀏覽器自動帶 Cookie，攻擊者就借得到登入狀態】*

## CSRF 的攻擊原理

> 🏠 **生活比喻**
>
> CSRF 像**壞人寄一張「幫我轉帳」的單子給你，騙你在銀行櫃台旁邊簽名**：因為你身上帶著銀行會員卡（Cookie），銀行以為是你本人要轉帳。

跨站請求偽造（Cross-Site Request Forgery，CSRF）像有人趁你還戴著銀行的識別手環，誘導你的瀏覽器替他送出一張轉帳表單。攻擊者通常讀不到你的 Cookie，也不需要讀到；只要瀏覽器在符合條件時自動附上 Cookie，伺服器就可能以為請求是你本人發的。

```
1. 使用者登入 example.com，瀏覽器拿到 Session Cookie
2. 使用者還沒登出，就開了惡意網站
3. 惡意網站誘使瀏覽器向 example.com 送出會改資料的請求
4. 瀏覽器自動附上 example.com 的 Cookie
5. 伺服器沒有額外驗證的話，這個操作就被當成合法請求
```

CSRF 防護主要針對會改變狀態的操作。Spring Security 預設不檢查 `GET` 這類唯讀方法的防偽權杖，前提是你的 `GET` 真的唯讀；如果系統讓 GET 也能改資料，那就自己開了一個洞。

*【除了登入憑證，再要一張攻擊者拿不到的票】*

## CSRF 權杖與其他防線

> 🏠 **生活比喻**
>
> CSRF 權杖像**每次填單都要附上櫃台剛剛發給你的一次性密碼**，壞人拿不到這組密碼，偽造的單子就會被擋下；SameSite Cookie 是**會員卡只在銀行自己的網站才拿出來**。

常見做法是產生一個無法預測的 CSRF 權杖，要求前端把它放進表單欄位或自訂的請求標頭。伺服器確認權杖與目前工作階段相符，才接受會改資料的請求。

```
Cookie: JSESSIONID=...
X-XSRF-TOKEN: 這個工作階段對應的防偽權杖
```

上面用的標頭名 `X-XSRF-TOKEN` 與表單參數名 `_csrf`，對應的是把權杖放進 Cookie 的那種設定；如果改把權杖存在工作階段裡，預設標頭名會是 `X-CSRF-TOKEN`，所以標頭名要跟自己用的儲存庫對上[出處](https://docs.spring.io/spring-security/reference/servlet/exploits/csrf.html)。

如果前端走的是「Cookie 裡放一份讀得到的權杖，再複製到自訂標頭」這個模式，惡意網站因為同源政策讀不到那個 Cookie 的值，也就設不出正確的標頭，伺服器就分辨得出偽造請求。

*   Session Cookie 可以加 `SameSite` 屬性，降低跨站時被自動附帶的機會。
*   會改資料的 API 要用符合語意的方法，並檢查 CSRF 權杖。
*   登入、登出與公開 API 要不要略過檢查，得看實際的威脅模型決定。
*   CORS 與 CSRF 解決的是不同問題，開了 CORS 不等於防住了 CSRF。

關鍵不在憑證叫什麼名字，而在它會不會被瀏覽器自動附帶。瀏覽器的請求會自動帶上所有 Cookie，包含工作階段 Cookie，所以除非另外做好授權，這種攻擊就會成立；JWT 放在 Cookie 裡，一樣算在「所有 Cookie」裡面[出處](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)。

> 📝 查證更正：原筆記在 CSRF 總結寫「其實 CSRF 攻擊是基於 Cookie → 如果不是使用 Session & Cookie 認證，就不會有 CSRF 攻擊」，查證後更正：關鍵不在憑證叫什麼名字，而在它會不會被瀏覽器自動附帶。OWASP 的原話是瀏覽器的請求會自動帶上所有 Cookie，包含工作階段 Cookie；放在 Cookie 裡的 JWT 也在這個「所有 Cookie」的範圍內，所以一樣有 CSRF 風險——後半句是依那句原話往下推的，OWASP 本身沒有討論 JWT

權杖如果只由程式主動放進 `Authorization` 標頭，傳統的 CSRF 風險確實比較低；但還是要處理跨網站指令碼（XSS）、權杖外洩等其他威脅。

*【能不能還原，決定了工具的用途】*

## 編碼、加密與雜湊

> 🏠 **生活比喻**
>
> - 編碼（Base64）＝**換一種字體寫**，誰都能讀回來，不是保密
> - 加密＝**鎖進保險箱**，有鑰匙才能打開
> - 雜湊＝**打成果汁**，無法變回水果，但同樣的水果一定打出同樣的果汁

| 方式 | 能否還原 | 要不要金鑰 | 主要用途 |
| --- | --- | --- | --- |
| 編碼（Encoding） | 照規則就能解碼 | 不用 | 格式轉換與傳輸相容，例如 Base64 |
| 對稱式加密 | 可以解密 | 加解密用同一把祕密金鑰 | 有效率地保護大量資料 |
| 非對稱式加密 | 依演算法與金鑰操作 | 公鑰與私鑰各一把 | 金鑰交換、加密或數位簽章 |
| 雜湊（Hashing） | 設計上不可逆 | 通常不用 | 完整性檢查、密碼驗證的一部分 |

編碼不是安全措施：把資料轉成 Base64，就像把中文換成另一種可逆的寫法，誰知道規則誰就讀得到。加密像把資料鎖進箱子，有對的金鑰才打得開。雜湊像資料的指紋，用來比對，不是用來還原。

非對稱密碼學不只是「公鑰加密、私鑰解密」。在數位簽章的情境裡方向是反過來的：私鑰用來簽署，公鑰用來驗證。

*【密碼不能只做一次快速雜湊】*

## 安全保存密碼

> 🏠 **生活比喻**
>
> 存密碼要用**加鹽的慢雜湊**（bcrypt）：
> - 加鹽＝**每個人的果汁都加一點獨特配料**，相同密碼也會打出不同果汁
> - 慢＝**故意讓果汁機很慢**，壞人要猜幾十億次就變得不可能

一般雜湊雖然不可逆，攻擊者還是可以大量猜測候選密碼再比對雜湊結果。彩虹表（Rainbow Table）就是預先算好結果的一種攻擊方式；鹽值（Salt）則是替每一筆密碼加入不同的隨機值，讓相同的密碼不會產生相同的儲存結果。

「同一個字串，每次算出來的雜湊值一定一模一樣」——單講雜湊函式本身，這句話沒錯。但下一步要接上：一旦加了每筆不同的隨機鹽值，同一組密碼存進資料庫的結果就不會一樣了。不同的鹽值讓相同的密碼算出不同的雜湊值，不破解雜湊就看不出兩個使用者是不是用同一組密碼。所以驗證密碼不能自己把輸入雜湊一次再比字串，要交給專門的驗證方法[出處](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)。

密碼要用專門的 `PasswordEncoder` 與成本可調整的密碼雜湊演算法，而不是 MD5 這類為速度設計的一般雜湊。註冊時存編碼結果；登入時用驗證方法比對輸入的原始密碼與已存的結果，不需要也不應該把密碼「解密」出來。

> 註冊：原始密碼 → PasswordEncoder → 存下密碼雜湊結果

> 登入：輸入密碼 ＋ 已存結果 → PasswordEncoder.matches(...) → 相不相符

### 🗺️ 比喻對照表

| 技術名詞 | 生活比喻 |
| --- | --- |
| CORS | 住戶留的訪客名單 |
| 預檢請求 | 寄前先打電話問 |
| CSRF | 騙你在櫃台旁簽名 |
| CSRF 權杖 | 每張單附一次性密碼 |
| 編碼 / 加密 / 雜湊 | 換字體 / 鎖保險箱 / 打成果汁 |
| 加鹽 | 每人加獨特配料 |

### 重點整理

*   同源看的是通訊協定、主機名稱與連接埠三項，路徑不同不算跨來源。
*   不符合簡單請求條件的跨來源請求，會先用 OPTIONS 做預檢。
*   CORS 必須排在 Spring Security 之前處理，因為預檢請求不帶 Cookie。
*   CSRF 利用的是「瀏覽器會自動附帶憑證」這個行為，憑證叫不叫 JWT 不是重點。
*   CORS、CSRF 與 XSS 是三個不同的問題，不能用其中一項設定取代另外兩項。
*   編碼只換格式，加密可用金鑰還原，雜湊設計成單向。
*   密碼要用成本可調的專用雜湊加隨機鹽值，驗證時用 matches 而不是比對字串。

## 隨堂測驗

**Q1. 判斷兩個網址是不是同源時，要比較哪些部分？**

- (A) 通訊協定、主機名稱與連接埠
- (B) HTTP 方法、路徑與查詢參數
- (C) Cookie 名稱、Session ID 與回應內容
- (D) Controller、Service 與 Repository

<details><summary>看答案</summary>

**答案：(A)** 來源由這三項組成，只有路徑不同不會變成跨來源。

</details>

**Q2. 瀏覽器送出 CORS 預檢請求時，用的是哪個 HTTP 方法？**

- (A) OPTIONS
- (B) HEAD
- (C) TRACE
- (D) PATCH

<details><summary>看答案</summary>

**答案：(A)** 預檢用 OPTIONS 詢問伺服器允不允許接下來的方法與標頭。

</details>

**Q3. 要讓跨來源請求帶 Cookie，後端的 CORS 設定要注意什麼？**

- (A) 允許憑證時必須回傳明確的來源，不能用萬用字元
- (B) 只要允許 GET 就會自動允許所有 Cookie
- (C) 必須把 Session ID 放進網址
- (D) 應該停用所有 OPTIONS 請求

<details><summary>看答案</summary>

**答案：(A)** 帶憑證的 CORS 前後端都要配合，允許來源不能寫 \*。

</details>

**Q4. 在 Spring 專案裡同時使用 CORS 與 Spring Security，最關鍵的是什麼？**

- (A) CORS 要排在 Spring Security 之前處理，因為預檢請求不帶 Cookie
- (B) 兩者不能同時使用，必須擇一
- (C) 必須把所有 API 改成 GET
- (D) Spring Security 會自動把預檢請求視為已登入

<details><summary>看答案</summary>

**答案：(A)** 預檢不帶 Cookie，Security 若先跑就會判定未認證而擋掉。

</details>

**Q5. CSRF 攻擊利用的是瀏覽器的哪一項行為？**

- (A) 符合條件時會自動在請求裡附上 Cookie
- (B) 會自動把密碼寫進回應本體
- (C) 會自動替每個請求建立管理員角色
- (D) 會自動允許所有跨來源回應

<details><summary>看答案</summary>

**答案：(A)** 攻擊者靠的是自動附帶的登入憑證，讓偽造請求看起來像合法工作階段。

</details>

**Q6. 為什麼把 CSRF 權杖放進自訂請求標頭有助於防禦？**

- (A) 惡意網站取不到正確的權杖，也就設不出相符的標頭
- (B) 自訂標頭會自動加密所有資料庫欄位
- (C) 自訂標頭可以取代使用者認證
- (D) 自訂標頭會讓 Cookie 永遠不再傳送

<details><summary>看答案</summary>

**答案：(A)** 伺服器要求一份 Cookie 以外、無法預測的資訊，就能分辨合法前端與偽造請求。

</details>

**Q7. 下列哪一項最適合描述 Base64？**

- (A) 可逆的資料編碼，不是加密
- (B) 要私鑰才能還原的非對稱式加密
- (C) 專門保存密碼的慢速雜湊
- (D) 阻擋瀏覽器跨來源讀取的授權協定

<details><summary>看答案</summary>

**答案：(A)** Base64 用來讓資料在傳輸時相容，知道規則的人都能解碼。

</details>

**Q8. 鹽值對保存密碼的主要幫助是什麼？**

- (A) 讓相同密碼的儲存結果也不一樣，降低預先計算攻擊的效果
- (B) 讓伺服器可以直接把所有密碼解密回來
- (C) 讓密碼不必經過任何雜湊
- (D) 讓 CORS 預檢結果永久有效

<details><summary>看答案</summary>

**答案：(A)** 每筆不同的隨機鹽值會改變雜湊輸入，相同密碼就不再對應同一個儲存值。

</details>

**Q9. 用了 JWT 之後，什麼情況仍然可能有 CSRF 風險？**

- (A) JWT 放在瀏覽器會自動附帶的 Cookie 裡
- (B) JWT 只由程式加進 Authorization 標頭，沒有存在 Cookie
- (C) JWT 只存在伺服器的測試資料中
- (D) JWT 已過期且伺服器確實拒絕它

<details><summary>看答案</summary>

**答案：(A)** 風險的關鍵是憑證會不會被瀏覽器自動附帶，不是它叫什麼名字。

</details>
