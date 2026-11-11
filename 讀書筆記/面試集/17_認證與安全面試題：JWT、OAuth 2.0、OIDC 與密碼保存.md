# 17. 認證與安全面試題：JWT、OAuth 2.0、OIDC 與密碼保存

> 來源：[筆記平台 · 面試集](https://hhtim.github.io/notes-platform/interview/#/lesson/auth-security-qa)　第 17 課 / 共 23 課 · 約 14 分鐘

**認證對授權、JWT 簽章與撤銷、OAuth 2.0 授權碼加 PKCE、OIDC 與 SAML、慢雜湊怎麼選、Spring Security 資源伺服器、OWASP Top 10:2025——十五題的面試答法，每句附 RFC 或官方出處。**

### 讀完這課你會

*   分清認證與授權、Session 與 Token
*   講出 JWT 怎麼驗、常見的驗證漏洞
*   講出 OAuth 2.0 授權碼流程
*   答出密碼怎麼存、常見攻擊怎麼防

*【認證基礎】*

## 誰、能做什麼、憑證怎麼帶

Filter 鏈與登入流程見〈Spring Security 認證與授權〉。

答題公式：先一句話定義，再講差別與取捨，最後補協定編號或版本。以下以 Spring Security 7.1、OWASP Top 10 2025 版為準。

> 💡 面試官：認證與授權差在哪？Session 對 Token 各自的優缺點？

**一句話定義**：認證（authentication）回答「你是誰」，授權（authorization）回答「你能做什麼」。網銀輸入帳號密碼加簡訊驗證碼是認證；登入後能不能查別人的帳戶是授權。

**差別與取捨：**

*   Session 是「伺服器記得你」：狀態存伺服器，瀏覽器只拿識別碼放 Cookie。登出、強制下線立刻生效，成本是多台伺服器要共用狀態。
*   Token 是「你自己帶著證明」：伺服器簽發一段字串，每次請求帶上，驗簽章就知道你是誰。無狀態、跨服務好傳遞，代價是簽出去就難以即時作廢；一做拒絕清單（伺服器記下已作廢的權杖，收到就擋），工作階段就不再完全無狀態。[出處](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_Cheat_Sheet.html)
*   網銀網頁走 Session 就夠，行動銀行 App 與多個後端服務之間走 Token。

> 💡 面試官：Basic 認證與 Bearer 認證的格式與風險？

**一句話定義**：Basic 是把「帳號:密碼」用 Base64 編碼後放進 Authorization 標頭（RFC 7617 第 2 節）[出處](https://www.rfc-editor.org/rfc/rfc7617#section-2)；Bearer 是把一段權杖（token）放進同一個標頭，格式 `Authorization: Bearer mF_9.B5f-4.1JqM`（RFC 6750 第 2.1 節）。[出處](https://www.rfc-editor.org/rfc/rfc6750#section-2.1)

**風險：**

*   Basic 的帳密等於明文傳送（Base64 是編碼不是加密），沒搭配 TLS 這類外部安全機制就不算安全的認證方法。[出處](https://www.rfc-editor.org/rfc/rfc7617#section-1)
*   Bearer 權杖是誰拿著誰就能用，所以防護全繞著「別外洩」：一律走 TLS、簽發短效（一小時以內）的權杖、放進 Cookie 就必須防範跨站請求偽造。[出處](https://www.rfc-editor.org/rfc/rfc6750#section-5.3)
*   JWT 是格式、Bearer 是帶法，兩者可各自替換。

*【JWT】*

## 三段、簽章、過期與撤銷

> 💡 面試官：JWT 三段是什麼？簽章怎麼驗？

**一句話定義**：JWT（JSON Web Token）是一種精簡、可放進網址的格式，用來表示要在兩方之間傳遞的聲明；聲明（claim）就是一句「關於誰的什麼陳述」。[出處](https://www.rfc-editor.org/rfc/rfc7519#abstract)

**三段與驗法**：JWT 是用句點分隔的幾段字串，每段都是 base64url 編碼：標頭（如 `{"typ":"JWT","alg":"HS256"}`）、聲明集合、簽章。[出處](https://www.rfc-editor.org/rfc/rfc7519#section-3) 常用聲明登記了七個：iss、sub、aud、exp、nbf、iat、jti。[出處](https://www.rfc-editor.org/rfc/rfc7519#section-4.1)

驗證分兩步：[出處](https://www.rfc-editor.org/rfc/rfc7519#section-7.2)

*   驗格式與簽章：HS256 用同一把共享金鑰重算 HMAC 再比對，RS256 用簽發者的公鑰驗證第三段的簽章；任何一步失敗，JWT 就必須被拒絕。
*   再檢查 aud 與 exp 等聲明。

簽章只保證沒被改、不保證沒被看：有簽章的 JWT 提供完整性與真實性，但不提供機密性。[出處](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_Cheat_Sheet.html)

> 💡 面試官：alg 改成 none 與演算法混淆攻擊是什麼？怎麼防？

**成因**：標頭的 alg 是「送來的人」宣告的，驗證方照單全收，就等於讓攻擊者決定怎麼驗。兩種攻擊：[出處](https://www.rfc-editor.org/rfc/rfc8725#section-2.1)

*   alg 改成 `none`：某些函式庫相信這個值，不檢查任何簽章就「驗證」通過。
*   RS256 改成 HS256：某些函式庫會把 RSA 公鑰當成 HMAC 的共享祕密。公鑰本來就公開，拿它當金鑰就能簽出通得過的權杖。

**防法**：演算法由驗證端寫死，不從權杖讀。

*   函式庫必須讓呼叫者指定一組支援的演算法，且不得使用其他演算法；每把金鑰只搭配一種演算法。[出處](https://www.rfc-editor.org/rfc/rfc8725#section-3.1)
*   還要驗 iss 與 aud：發給多個服務的權杖必須包含 aud，收到方必須驗證。[出處](https://www.rfc-editor.org/rfc/rfc8725#section-3.9)

> 💡 面試官：JWT 怎麼過期、怎麼撤銷？Refresh Token 的角色？Token 放 Cookie 還是 localStorage？

**過期與撤銷**：過期靠 exp；撤銷是弱項，因為簽出去就不會回頭問伺服器。做法是拒絕清單（通常以 jti 與 iss 為鍵，代價是又有狀態）；權杖被重複使用的風險，可以靠短過期時間緩解。[出處](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_Cheat_Sheet.html)

**Refresh Token：**

*   Refresh token 是用來取得 access token 的憑證，只送給授權伺服器，絕不送往資源伺服器。[出處](https://www.rfc-editor.org/rfc/rfc6749#section-1.5)
*   所以存取權杖短效、更新權杖長效，撤銷就撤更新權杖。
*   再加上更新權杖輪替：每次換發給新的、舊的作廢，外洩的那把一被重複使用，授權伺服器就會發現。[出處](https://www.rfc-editor.org/rfc/rfc9700#section-4.14)

**放哪裡**：localStorage 對頁面上任何 JavaScript 開放，被 XSS（跨網站指令碼，把惡意程式塞進網頁執行）打中就整包被讀走。認證權杖、JWT、更新權杖或任何憑證都不要存在 localStorage 或 sessionStorage，改用 `HttpOnly`、`Secure`、`SameSite=Strict` 的 Cookie。[出處](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html) Cookie 會被瀏覽器自動帶，所以要另外防 CSRF（〈網站安全三題：CORS、CSRF、密碼學〉）。

> 簽章只保證沒被改；演算法由驗證方寫死；存取權杖短效、更新權杖輪替；憑證放 HttpOnly Cookie 再防 CSRF

*【OAuth 2.0 與 OIDC】*

## 授權框架、身分層與企業單一登入

> 💡 面試官：OAuth 2.0 的四個角色與授權碼流程？為什麼不建議 Implicit 流程？

**一句話定義**：OAuth 2.0（RFC 6749）是授權框架，解決「讓第三方應用程式在不拿到你密碼的情況下，代替你存取你的資料」。四個角色，用「記帳 App 讀你的銀行交易明細」對照：[出處](https://www.rfc-editor.org/rfc/rfc6749#section-1.1)

| 角色 | 做什麼 | 例子 |
| --- | --- | --- |
| 資源擁有者（resource owner） | 資料的主人 | 你 |
| 用戶端（client） | 想代替你存取資料的應用程式 | 記帳 App |
| 授權伺服器（authorization server） | 認證資源擁有者並取得授權後，簽發 access token | 銀行的登入授權頁 |
| 資源伺服器（resource server） | 收到 access token 就回應請求 | 銀行開放 API |

**授權碼與 Implicit**：授權碼流程是用戶端把資源擁有者導向授權伺服器，授權伺服器認證並取得同意後，帶著授權碼導回用戶端，用戶端再拿授權碼換權杖；好處是資源擁有者的憑證絕不會交給用戶端。[出處](https://www.rfc-editor.org/rfc/rfc6749#section-1.3.1)

Implicit（隱含）流程是簡化版：略過授權碼，直接把 access token 簽發給瀏覽器，權杖可能暴露給其他能存取瀏覽器的應用程式。[出處](https://www.rfc-editor.org/rfc/rfc6749#section-1.3.2)

2025 年 1 月發佈的 RFC 9700 起，用戶端不應（SHOULD NOT）使用隱含流程。[出處](https://www.rfc-editor.org/rfc/rfc9700#section-2.1.2) 現在單頁應用程式也走「授權碼加 PKCE」。

> 💡 面試官：PKCE 解決什麼？

**一句話定義**：PKCE（Proof Key for Code Exchange，RFC 7636，念作 pixy）解決「授權碼被攔截後被別人拿去換權杖」。公開用戶端容易受到授權碼攔截攻擊：攻擊者在未受 TLS 保護的路徑上攔截授權碼，例如同一支手機上的另一個 App。[出處](https://www.rfc-editor.org/rfc/rfc7636#section-1) 行動銀行 App 就是公開用戶端：裝在使用者手機上，藏不住任何密鑰。

**機制：**[出處](https://www.rfc-editor.org/rfc/rfc7636#section-4)

*   用戶端每次先產生隨機的 `code_verifier`，用 S256 方法算出 `code_challenge`（`code_verifier` 的 SHA-256 再 base64url），隨授權請求送出。做得到 S256 就必須用 S256，plain 只是相容用。
*   換權杖時送出原本的 verifier，授權伺服器在回傳權杖前驗證 `code_verifier`。
*   攔到授權碼的人沒有 verifier，換不到權杖。
*   公開用戶端必須（MUST）使用 PKCE，機密用戶端建議使用。[出處](https://www.rfc-editor.org/rfc/rfc9700#section-2.1.1)

> 💡 面試官：OAuth 2.0 與 OIDC 差在哪？ID Token 對 Access Token？

**一句話定義**：OAuth 2.0 管授權，沒有定義「這個人是誰」；OIDC（OpenID Connect）補上這層：OpenID Connect 1.0 是架在 OAuth 2.0 協定之上的簡單身分層，讓用戶端能驗證終端使用者的身分。[出處](https://openid.net/specs/openid-connect-core-1_0.html#Introduction)

|   | Access Token | ID Token |
| --- | --- | --- |
| 回答的問題 | 「拿著它能存取什麼」，給資源伺服器看 | 「這個人是誰、何時認證的」，給用戶端看 |
| 格式 | OAuth 2.0 沒規定，不透明字串或 JWT 都行[出處](https://www.rfc-editor.org/rfc/rfc6749#section-1.4) | 一定是 JWT[出處](https://openid.net/specs/openid-connect-core-1_0.html#IDToken) |
| 誰驗 | 資源伺服器（API） | 用戶端：iss 必須完全符合、aud 必須包含自己的 client_id[出處](https://openid.net/specs/openid-connect-core-1_0.html#IDTokenValidation) |

> 💡 面試官：SAML 是什麼、跟 OIDC 差在哪？企業單一登入為什麼還在用 SAML？

**一句話定義**：SAML（Security Assertion Markup Language）是以 XML 為基礎、在線上商業夥伴之間交換安全資訊的框架。最重要的使用情境是跨網域的網頁單一登入：身分提供者（負責登入的一方）向服務提供者（你要用的系統）斷言「這個使用者已在它那裡認證」。[出處](https://docs.oasis-open.org/security/saml/Post2.0/sstc-saml-tech-overview-2.0.html)

**差別與取捨**：做的事一樣，差在格式與年代：

*   SAML 用 XML 斷言、靠瀏覽器表單 POST 傳遞，2.0 版 2005 年定稿。
*   OIDC 用 JSON 與 JWT、走 OAuth 2.0 的導向與 REST 呼叫，2014 年定稿，天生適合行動 App。
*   企業內部還在用 SAML，是因為帳號目錄、人資與內部系統多在 OIDC 普及前就接了 SAML，換掉要動每一個服務提供者；Spring Security 也因此有完整的 SAML 2 支援。[出處](https://docs.spring.io/spring-security/reference/servlet/saml2/index.html)

*【密碼保存】*

## 慢雜湊、參數，以及 Spring Security 怎麼包

> 💡 面試官：密碼怎麼存？為什麼 MD5／SHA-256 加鹽也不夠？bcrypt、scrypt、Argon2、PBKDF2 怎麼選？

**一句話定義**：只存「專為密碼設計的慢雜湊」結果，不存明文、不加密、不用一般雜湊。SHA-256 這類快速雜湊演算法不適合保存密碼，因為攻擊者能用它快速進行大量猜測。[出處](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)

**為什麼加鹽還不夠**：鹽（salt，每筆密碼各不相同的隨機值）擋的是「事先算好一張表、一次比對所有人」，但不會讓「猜一次」變慢；MD5、SHA-1 設計上就是要快，密碼專用演算法則應該慢，而且可以改工作因子調整有多慢（工作因子：決定要算多少輪的參數，越大越慢）。[出處](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) 一句話：鹽讓攻擊者不能一次破所有人，慢雜湊讓破一個人也很貴。

| 演算法 | 建議的最低參數 | 什麼時候選 |
| --- | --- | --- |
| Argon2id | 記憶體 19 MiB、迭代 2 次、平行度 1 | 首選；2015 年密碼雜湊競賽的優勝者 |
| scrypt | 成本參數 2 的 17 次方、區塊大小 8、平行參數 1 | Argon2id 不可用時 |
| bcrypt | 工作因子 10 以上，密碼長度上限 72 位元組 | 舊系統沿用；超長會被截斷 |
| PBKDF2 | 600,000 次以上，內部雜湊 HMAC-SHA-256 | 需要符合 FIPS-140 時（美國政府的密碼模組認證） |

出處：[OWASP 密碼保存速查表](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)

**密碼規則也要答對**（NIST SP 800-63B-4 對單因子密碼的要求）：[出處](https://pages.nist.gov/800-63-4/sp800-63b.html)

*   至少 15 個字元。
*   不得強加其他組成規則（例如規定要含符號）。
*   不得要求定期更換密碼。
*   建立時必須與含常見或已外洩密碼的封鎖清單比對。

「每 90 天改密碼、必須含符號」已不是最佳實務。

> 💡 面試官：Spring Security 的 DelegatingPasswordEncoder 做了什麼？

**一句話定義**：帶前綴的分派器：儲存格式是 `{id}encodedPassword`，編碼時用現行建議的演算法並標上 id，比對時看前綴決定交給哪個 PasswordEncoder，新舊格式可以共存。

**為什麼要有它**：直接把預設換成 bcrypt 會撞到兩個問題：很多應用程式用的是無法輕易遷移的舊編碼，而且最佳實務還會再變。DelegatingPasswordEncoder 讓新密碼一律用現行建議的演算法編碼，同時舊格式的密碼照樣能驗證。[出處](https://docs.spring.io/spring-security/reference/features/authentication/password-storage.html)

```
PasswordEncoder encoder = PasswordEncoderFactories.createDelegatingPasswordEncoder();
String stored = encoder.encode("password");
// {bcrypt}$2a$10$dXJ3SW6G7P50lGmMkkmwe.20cQQubK3.HZWzG3YB1tlRy.fqvM/BG
encoder.matches("password", stored);   // 照前綴 {bcrypt} 交給 BCryptPasswordEncoder 比對
```

**追問時要補的：**[出處](https://docs.spring.io/spring-security/reference/features/authentication/password-storage.html)

*   把演算法寫在前面不是問題，因為密碼的保存不依賴演算法保密。
*   `BCryptPasswordEncoder` 預設強度 10，建議調到驗證一組密碼大約花 1 秒。
*   也因為每次驗證都貴，建議把長期憑證（帳密）換成短期憑證（權杖），呼應本課第一題。

*【Spring Security 資源伺服器】*

## API 怎麼驗別人簽的 JWT

JWT 驗簽與授權碼流程的實跑見〈JWT 與 OAuth 2.0 在 Spring Security 裡怎麼接〉。

> 💡 面試官：Spring Security 當 OAuth 2.0 資源伺服器怎麼驗 JWT？

**一句話定義**：資源伺服器就是「收 Bearer token 的 API」。Spring Boot 之下兩步：加 `spring-security-oauth2-resource-server` 與 `spring-security-oauth2-jose` 兩個相依，再告訴它授權伺服器在哪：

```
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: https://idp.example.com/issuer
```

`issuer-uri` 是 JWT 裡 iss 聲明的值，資源伺服器用它自動設定、找到授權伺服器的公鑰，接著驗證進來的 JWT。[出處](https://docs.spring.io/spring-security/reference/servlet/oauth2/resource-server/jwt.html) 對應的預設 SecurityFilterChain：

```
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http
        .authorizeHttpRequests((authorize) -> authorize
            .anyRequest().authenticated()
        )
        .oauth2ResourceServer((oauth2) -> oauth2.jwt(Customizer.withDefaults()));
    return http.build();
}
```

**它實際做了什麼**：收到 JWT 時做三件事，金鑰換新時會自動輪替：[出處](https://docs.spring.io/spring-security/reference/servlet/oauth2/resource-server/jwt.html)

*   從 jwks_url 端點（授權伺服器公開它公鑰的網址）取得與 JWT 相符的公鑰，驗證簽章。
*   驗證 exp 與 nbf 時間戳記，以及 iss 聲明。
*   把每個 scope（權杖被允許的操作範圍）對應成前綴 `SCOPE_` 的權限。

aud 預設不驗，多個 API 共用同一個授權伺服器時，要在設定加 `spring.security.oauth2.resourceserver.jwt.audiences` 屬性（或自訂驗證器）。[出處](https://docs.spring.io/spring-security/reference/servlet/oauth2/resource-server/jwt.html)〈後端與雲端面試題庫〉講的「Gateway 驗完、內部服務仍要重新授權」，在 Spring 裡就是每個資源伺服器各自掛這段。

*【OWASP 與常見漏洞】*

## 十大風險、四種攻擊的防法、CSP 與機密

> 💡 面試官：OWASP 十大風險現行版有哪幾項？各給一個例子與防法

**一句話定義**：OWASP Top 10 是 OWASP 基金會定期整理的「網頁應用程式最嚴重的十類風險」，現行是 2025 年版。[出處](https://top10.owasp.org/2025/) 跟 2021 年版的差別：SSRF 已併入存取控制失效，「軟體供應鏈失效」與「例外狀況處理不當」是新面孔。[出處](https://top10.owasp.org/2025/0x00_2025-Introduction)

| 編號 | 名稱 | 銀行情境的例子 → 防法 |
| --- | --- | --- |
| A01 | 存取控制失效 | 改網址上的帳號編號就看到別人的對帳單 → 除公開資源外預設拒絕，只在伺服器端檢查[出處](https://top10.owasp.org/2025/A01_2025-Broken_Access_Control) |
| A02 | 安全設定錯誤 | 正式環境開著除錯頁 → 各環境同一套強化設定 |
| A03 | 軟體供應鏈失效 | 引進被植入惡意程式的套件 → 追蹤相依、鎖定版本 |
| A04 | 密碼學失效 | 密碼用 MD5 存 → 本課密碼保存那節 |
| A05 | 注入 | 轉帳備註被拼進 SQL → 參數化查詢 |
| A06 | 不安全的設計 | 忘記密碼只問「母親的姓名」 → 設計期做威脅建模（先列出誰會怎麼攻擊） |
| A07 | 認證失效 | 放任帳密填充這類自動化攻擊（帳密填充：拿別處外洩的帳號密碼整批試登入）[出處](https://top10.owasp.org/2025/A07_2025-Authentication_Failures) → 多因子認證、限制嘗試次數 |
| A08 | 軟體或資料完整性失效 | 反序列化（把外部送來的位元組還原成程式物件）不受信任的資料 → 只收受信任來源 |
| A09 | 安全記錄與告警失效 | 外洩帳密被拿來整批試登入，三天沒人知道 → 登入失敗要記錄並告警 |
| A10 | 例外狀況處理不當 | 驗證服務逾時就當作通過 → 失效時關閉 |

> 💡 面試官：SQL 注入、XSS、CSRF、SSRF 各怎麼防？

*   **SQL 注入**：成因：使用者輸入被拼進 SQL 字串，輸入就能改變查詢結構。防法：首選是預備語句（參數化查詢），Java 對應 `PreparedStatement`；靠跳脫所有使用者輸入來防，強烈不建議。[出處](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)
*   **XSS**：成因：使用者輸入原樣放進 HTML，瀏覽器把它當程式執行。防法：框架的安全保護、輸出編碼與 HTML 淨化是最好的保護；CSP 只是額外的一層防禦。[出處](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
*   **CSRF**：成因：瀏覽器自動帶 Cookie，惡意網站借你的登入狀態送請求。防法：先用框架內建的 CSRF 防護；有狀態的軟體用同步權杖模式，無狀態的用雙重提交 Cookie；SameSite 屬性可加，但任何能用 GET 改狀態的操作，`SameSite=Lax` 都擋不住。[出處](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html) Spring Security 的權杖怎麼帶見〈網站安全三題：CORS、CSRF、密碼學〉。
*   **SSRF**：SSRF（Server-Side Request Forgery，伺服器端請求偽造）成因：應用程式拿使用者給的網址去發請求（下載頭像、呼叫 webhook），攻擊者就能讓伺服器替他連內網或雲端中繼資料服務。防法：目標只會是已識別、受信任的應用程式時用允許清單；封鎖清單容易被繞過，能用允許清單就用；真的躲不掉時至少封鎖內網、本機與雲端中繼資料位址，再加上網路層隔離。[出處](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)

> 💡 面試官：CSP 標頭在擋什麼？跟 XSS 的關係？

**一句話定義**：CSP（Content Security Policy，內容安全政策）是伺服器用回應標頭告訴瀏覽器「這個頁面允許從哪裡載入什麼」，讓網頁開發者控制特定頁面可以取得或執行哪些資源[出處](https://www.w3.org/TR/CSP3/)，主要用來防禦跨網站指令碼攻擊。[出處](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP)

```
Content-Security-Policy: default-src 'self'; img-src 'self' example.com
```

對 XSS 真正有用的是限制指令碼，建議做法是 nonce：[出處](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP)

*   伺服器每次回應產生一個隨機值，放進 `script-src`，也放進頁面每個 script 標籤的 `nonce` 屬性。
*   就算攻擊者能把 JavaScript 插進頁面，他不知道這次的 nonce，瀏覽器就拒絕執行。
*   導入時先用 report-only 模式，只回報不擋。

結論：CSP 是 XSS 發生後讓注入的程式跑不起來的第二道牆，第一道永遠是輸出編碼。

> 💡 面試官：機密（API 金鑰、資料庫密碼）該放哪？

**一句話定義**：不進程式碼、不進 git、不進映像檔；正式環境從集中式的機密管理服務取得，並能輪替與稽核。常見的反面教材：機密以明文寫死在原始碼裡，散落在設定檔與組態管理工具中。[出處](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)

**三個層次：**[出處](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)

*   寫死在程式碼：不行。
*   環境變數：及格線，比寫死好，但通常對所有行程可見、可能被寫進日誌，除非其他方法不可行，否則不建議。
*   集中式的機密管理服務：正解，例子有 HashiCorp Vault、CyberArk Conjur，雲端平台也各有自己的；存取權要限縮。

銀行情境：資料庫密碼要能定期輪替而不重新部署。

> 程式碼裡不該出現任何一把鑰匙；環境變數是及格線，機密管理服務加輪替與稽核才是正解

### 重點整理

*   認證是「你是誰」、授權是「你能做什麼」；Session 能立刻撤銷但要存狀態，Token 無狀態但難撤銷；Basic 必須配 TLS，Bearer 誰拿著誰能用、要短效。
*   JWT 三段是 base64url 的標頭、聲明、簽章；簽章保證沒被改、不保證沒被看；演算法由驗證方寫死（RFC 8725 第 3.1 節），否則 alg 改 none 與 RS256 換 HS256 都能偽造權杖。
*   撤銷靠短效存取權杖加更新權杖輪替；憑證不放 localStorage，放 HttpOnly、Secure、SameSite 的 Cookie 再防 CSRF。
*   OAuth 2.0 走授權碼流程，隱含流程「不應使用」，公開用戶端「必須」用 PKCE；OIDC 是 OAuth 2.0 上的身分層，ID Token 給用戶端、Access Token 給 API；SAML 用 XML 做同一件事。
*   密碼存慢雜湊：Argon2id 首選、scrypt 次之、bcrypt 工作因子 10 以上且限 72 位元組、PBKDF2 留給 FIPS；NIST 現行版要求至少 15 字元、不強制組成規則、不定期換密碼。
*   DelegatingPasswordEncoder 用 {id} 前綴讓新舊格式共存；資源伺服器給 issuer-uri 加 jwt() 就會驗簽章、exp、nbf、iss，aud 要自己加。
*   OWASP Top 10:2025：SSRF 併入存取控制失效、供應鏈失效與例外狀況處理不當是新面孔；注入用參數化查詢、XSS 用輸出編碼加 CSP、CSRF 用框架權杖、SSRF 用允許清單；機密進機密管理服務。

## 隨堂測驗

**Q1. 一個已登入網銀的一般會員，嘗試查另一個客戶的帳戶明細被拒。這是哪一道門擋下的？**

- (A) 授權——身分有效，但這個身分不能做這件事
- (B) 認證——伺服器判定憑證無效
- (C) CSRF 防護——請求缺少防偽權杖
- (D) CORS——瀏覽器擋下跨來源回應

<details><summary>看答案</summary>

**答案：(A)** 認證回答「你是誰」、授權回答「你能做什麼」；帳號密碼都對但權限不足，是授權失敗。

</details>

**Q2. API 收到的 JWT 標頭寫著 alg 為 HS256，但這個 API 平常只用 RS256 公鑰驗簽章。最正確的處理是？**

- (A) 直接拒絕——可接受的演算法由驗證端寫死，每把金鑰只搭配一種演算法
- (B) 改用 HMAC-SHA256 並拿 RS256 的公鑰當共享祕密驗簽章
- (C) 只要簽章驗得過就接受，演算法由簽發者決定
- (D) 先解出聲明，確認 exp 沒過期就放行

<details><summary>看答案</summary>

**答案：(A)** 函式庫只能用呼叫者指定的演算法；讓權杖自己宣告演算法，正是 RS256 換 HS256 混淆攻擊能成立的原因。

</details>

**Q3. 用 JWT 做工作階段時，為什麼存取權杖要短效並搭配更新權杖，而不是發一個長效存取權杖就好？**

- (A) JWT 簽出去就難以即時撤銷，短效讓外洩的權杖很快失效，撤銷改在更新權杖上做
- (B) 短效權杖的簽章比較短，傳輸比較省
- (C) 更新權杖會送到資源伺服器，資源伺服器才能檢查它有沒有被撤銷
- (D) 長效權杖會超過 base64url 的長度上限

<details><summary>看答案</summary>

**答案：(A)** 簽章式權杖不會回頭問伺服器，權杖被重複使用的風險靠短過期時間緩解；更新權杖只送給授權伺服器、絕不送往資源伺服器。

</details>

**Q4. 前端工程師提議把登入後的 JWT 存進 localStorage，方便各頁面讀取。主要風險是什麼？**

- (A) 同來源任何 JavaScript 都讀得到，一個 XSS 漏洞就洩漏所有權杖；建議改放 HttpOnly、Secure、SameSite 的 Cookie
- (B) localStorage 會隨瀏覽器關閉而清空，使用者每次都要重新登入
- (C) localStorage 會被瀏覽器自動附在跨站請求上，造成 CSRF
- (D) localStorage 容量太小放不下 JWT

<details><summary>看答案</summary>

**答案：(A)** JWT、更新權杖或任何憑證都不要放 localStorage 或 sessionStorage；會被瀏覽器自動附帶的是 Cookie，不是 localStorage。

</details>

**Q5. 一家銀行的行動 App 要接第三方登入。這種公開用戶端該用哪個 OAuth 2.0 流程？**

- (A) 授權碼流程加 PKCE——公開用戶端必須用 PKCE，隱含流程不應使用
- (B) 隱含流程——App 沒有後端，直接拿存取權杖最省事
- (C) 授權碼流程加用戶端密鑰——把密鑰編進 App 裡
- (D) 任何流程都可以，只要走 TLS

<details><summary>看答案</summary>

**答案：(A)** 公開用戶端必須（MUST）用 PKCE，用戶端不應（SHOULD NOT）用隱含流程；App 裝在使用者手機上藏不住密鑰，所以不能靠用戶端密鑰。

</details>

**Q6. PKCE 的 code_verifier 與 code_challenge 之所以能擋住授權碼攔截，關鍵在哪？**

- (A) 攻擊者就算攔到授權碼，換權杖時交不出當初產生 challenge 的那個 verifier
- (B) challenge 是用授權伺服器的私鑰簽的，攻擊者無法偽造
- (C) verifier 取代了授權碼，所以授權碼不再出現在導回網址裡
- (D) PKCE 強制授權碼只能走 TLS 傳送

<details><summary>看答案</summary>

**答案：(A)** 用戶端先送 challenge，換權杖時再送 verifier，授權伺服器比對兩者；攔到授權碼的人手上沒有 verifier。

</details>

**Q7. 團隊把 OIDC 拿回來的 ID Token 直接當成 Bearer 去呼叫另一個 API。這個做法錯在哪？**

- (A) ID Token 是給用戶端驗證使用者身分用的，受眾是用戶端的 client_id，不是 API；呼叫 API 要用 Access Token
- (B) ID Token 沒有簽章，API 無法驗證
- (C) ID Token 不是 JWT 格式，API 解不開
- (D) 只要 iss 相同就可以互換，這個做法沒有錯

<details><summary>看答案</summary>

**答案：(A)** ID Token 是含有使用者認證相關聲明的安全權杖，用戶端要驗 aud 含自己的 client_id；它是身分證明，不是 API 的存取憑證。

</details>

**Q8. 系統目前用「SHA-256 加每人不同的隨機鹽」存密碼。資料庫外洩後，為什麼攻擊者仍能大量破解？**

- (A) 鹽只擋預先算好的對照表與一次比對所有人，SHA-256 本身算得極快，逐一猜測仍然便宜；要換成 Argon2id 這類慢雜湊
- (B) 鹽存在同一張表裡，等於沒加鹽
- (C) SHA-256 已被數學上破解，可以直接反推原文
- (D) 隨機鹽讓相同密碼產生相同雜湊，攻擊者一破全破

<details><summary>看答案</summary>

**答案：(A)** 快速雜湊讓攻擊者能快速進行大量猜測，鹽解決的是預先算好的對照表（彩虹表）與批次比對，不解決單筆猜測的速度。

</details>

**Q9. Spring Security 資料庫裡的密碼欄位長這樣：{bcrypt}$2a$10$…。有人擔心前綴把演算法洩漏給攻擊者。正確的理解是？**

- (A) 前綴是 DelegatingPasswordEncoder 用來決定交給哪個編碼器比對的 id；這不算洩漏，密碼保存的安全不依賴演算法保密
- (B) 應該把前綴拿掉，改成統一的雜湊值以免被辨識
- (C) 前綴表示這筆密碼還沒編碼，登入時會被拒絕
- (D) 前綴只是註解，比對時會被忽略，實際用的是預設的 SHA-256

<details><summary>看答案</summary>

**答案：(A)** id 必須在密碼開頭、以 { } 包住，比對時依 id 分派；bcrypt 的結果本來就以 $2a$ 開頭，藏前綴沒有意義。

</details>

**Q10. OWASP Top 10:2025 跟 2021 年版相比，下列哪一項變化是正確的？**

- (A) SSRF 不再獨立成項，併入存取控制失效；新增軟體供應鏈失效與例外狀況處理不當
- (B) 注入從第 1 名掉出前十
- (C) 新增了 CSRF 這一項獨立風險
- (D) 清單完全沒變，只更新了年份

<details><summary>看答案</summary>

**答案：(A)** 2025 年版把 SSRF 併入存取控制失效，軟體供應鏈失效是舊「易受攻擊與過時的元件」的擴大版，例外狀況處理不當是 2025 年的新類別。

</details>
