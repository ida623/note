# 09. Spring Security 認證與授權

> 🏠 **生活化版本**：每個段落開頭的「生活比喻」先用日常情境帶你抓到感覺，接著再看原本的技術說明與程式碼；篇末有「比喻對照表」可以快速複習。

> 來源：[筆記平台 · Spring 後端](https://hhtim.github.io/notes-platform/spring/#/lesson/spring-security)　第 9 課 / 共 23 課 · 約 11 分鐘

**從登入身分、角色權限、Filter 鏈到 Cookie 與 Session，建立 Spring Security 的整體心智模型。**

### 讀完這課你會

*   分辨認證與授權，並知道它們各自在哪裡失敗
*   看懂請求怎麼通過 Spring Security 的 Filter 鏈
*   用路徑規則與方法層級規則限制存取
*   說明 Cookie、Session 與權杖式認證的差別

*【先確認身分，再判斷權限】*

## 認證與授權是兩道不同的門

> 🏠 **生活比喻**
>
> - 認證＝**大樓門口刷卡**：你是誰？
> - 授權＝**進電梯後能按哪幾樓**：你能做什麼？
>
> 401 是**卡刷不過**，403 是**卡沒問題但你不能去那層樓**。

Spring Security 是 Spring 生態系的安全框架，處理登入、權限控制、密碼驗證、工作階段與常見的網站攻擊防護。它像大樓的門禁系統：先在櫃檯確認「你是誰」（認證，Authentication），再判斷這張門禁卡能不能開某個房間（授權，Authorization）。

| 概念 | 要回答的問題 | 失敗時的狀況 |
| --- | --- | --- |
| 認證 | 你是誰？提供的憑證有效嗎？ | 帳號或密碼錯、權杖失效，通常要求重新登入 |
| 授權 | 已登入的你可以做什麼？ | 身分有效，但角色或權限不足 |

舉個例子：一般會員看免費影片，VIP 會員看付費影片。還沒登入就要看影片是認證問題；已登入的一般會員要看 VIP 影片是授權問題。

公開資源不需要先認證。標成 `permitAll` 的路徑不需要授權判斷，而且根本不會去工作階段裡取出身分[出處](https://docs.spring.io/spring-security/reference/servlet/authorization/authorize-http-requests.html)。所以「先認證再授權」是理解一般流程的好方法，但不是所有請求都這樣走。

> 📝 查證更正：原筆記寫「所有網站，一定都是「先認證、再授權」」，查證後更正：公開資源不需要先認證。Spring Security 官方文件說明 permitAll 的路徑「requires no authorization and is a public endpoint」，而且在這種情況下根本不會去工作階段裡取出 Authentication

*【把登入資料包成框架看得懂的物件】*

## Spring Security 的認證流程

> 🏠 **生活比喻**
>
> 登入像**櫃台核對身分證**：Filter 收下帳密 → AuthenticationManager（**櫃台主管**）找 UserDetailsService（**員工名冊**）查人 → PasswordEncoder（**指紋比對機**）核對密碼 → 通過就發一張識別證放進 SecurityContext（**你身上的識別證**）。

帳號密碼登入時，請求先由負責認證的 Filter 接住，再把憑證交給認證管理元件。它透過使用者資料服務查出帳號，用密碼編碼器比對密碼。成功之後，已認證的身分會放進安全內容保存區。

*   **Authentication**：代表目前的身分與憑證，也可以帶著角色或權限。
*   **AuthenticationManager**：接收認證要求，協調整個認證流程。
*   **UserDetailsService**：依使用者名稱載入帳號資料。
*   **UserDetails**：描述帳號、密碼雜湊值與權限的介面。
*   **SecurityContextHolder**：讓目前這次請求取得已認證身分的入口。

帳號可以先放在記憶體裡方便示範或測試（`InMemoryUserDetailsManager` 就是這個用途），正式系統通常改從資料庫、LDAP（Lightweight Directory Access Protocol，查詢公司帳號目錄用的協定）或其他身分服務載入。密碼不應該存明文，要存適合密碼用途的單向雜湊結果，這點〈網站安全三題：CORS、CSRF、密碼學〉會細談。

*【每個請求都先走檢查站】*

## Filter 鏈怎麼保護 API

> 🏠 **生活比喻**
>
> Filter 鏈像**機場的一連串安檢關卡**：證件檢查、行李 X 光、隨身物品檢查，**每一關都過了才能登機**（進到 Controller）。

Servlet Filter（過濾器）像機場一連串的檢查站，能在請求進 Controller 之前檢查或補資料。Spring Security 會建立自己的安全 Filter 鏈，依序處理安全內容、登入、例外轉換與授權判斷。

*   讀 Session、Basic 憑證或權杖，試著建立使用者身分。
*   把認證結果放進安全內容保存區。
*   判斷目標資源允不允許目前這個身分存取。
*   把未登入或權限不足的錯誤轉成適當的 HTTP 回應。

自訂 Filter 可以直接實作 `Filter`，也可以繼承 `OncePerRequestFilter`。後者的重點是：一次請求的分派流程裡，同一個 Filter 不會重複執行。

把 Filter 加進安全鏈時是指定相對位置，例如放在某個既有 Filter 前面或後面，而不是指定「第五個位置」。這裡有個很實際的坑：同一個 Filter 如果既被 `@Component` 掃描自動註冊進 Servlet 容器，又被手動 `addFilterBefore()` 加進 Spring Security 鏈，它就會對同一次請求執行兩次。

負責權限檢查的過濾器在 Spring Security 5 是 `FilterSecurityInterceptor`。後來由 `AuthorizationFilter` 取代，但為了向後相容，`FilterSecurityInterceptor` 仍是預設；切換的條件是寫法：用 `authorizeHttpRequests` 而不是 `authorizeRequests` 時，才改用 `AuthorizationFilter`。到 Spring Security 7，舊的 `authorizeRequests` 已經從 `HttpSecurity` 拿掉，只剩 `authorizeHttpRequests` 這條路，也就只剩 `AuthorizationFilter`[出處](https://docs.spring.io/spring-security/reference/servlet/authorization/authorize-http-requests.html)[HttpSecurity](https://docs.spring.io/spring-security/site/docs/current/api/org/springframework/security/config/annotation/web/builders/HttpSecurity.html)。

> 📝 查證更正：這是版本差異不是原筆記寫錯：原筆記在「SpringSecurity完整流程」寫「FilterSecurityInterceptor: 負責權限校驗的過濾器」，那是 Spring Security 5 的元件。官方文件寫 AuthorizationFilter 取代（supersedes）了它，同一段也說「為了向後相容，FilterSecurityInterceptor 仍是預設」，並說明「當使用 authorizeHttpRequests 而非 authorizeRequests 時，會改用 AuthorizationFilter」；而 7.x 的 HttpSecurity javadoc 已無 authorizeRequests，所以現在只走得到 AuthorizationFilter

*【把路徑規則寫成看得懂的門禁表】*

## 用 HttpSecurity 設定路徑授權

> 🏠 **生活比喻**
>
> `HttpSecurity` 像**寫大樓的門禁規則表**：「大廳誰都能進、辦公區要員工證、機房只有管理員」。規則**由上往下比對，先符合的算數**。

`HttpSecurity` 可以設定路徑授權、表單登入、HTTP Basic、CSRF、CORS、Session 與 OAuth（讓使用者授權第三方應用程式代替自己存取資料的授權標準）相關功能。授權規則由「比對哪些請求」加上「採取什麼限制」兩部分組成。

```
@Bean
SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
    http.authorizeHttpRequests(auth -> auth
        .requestMatchers("/welcome", "/register").permitAll()
        .requestMatchers("/admin/**").hasRole("ADMIN")
        .requestMatchers("/member/**").hasAnyRole("USER", "ADMIN")
        .anyRequest().authenticated()
    );
    return http.build();
}
```

| 規則 | 意義 |
| --- | --- |
| `permitAll()` | 所有人都能存取，包含還沒登入的人 |
| `denyAll()` | 所有人都不能存取 |
| `authenticated()` | 必須完成認證 |
| `hasRole("ADMIN")` | 必須具備指定角色 |
| `hasAnyRole("USER", "ADMIN")` | 具備其中一個角色就行 |

規則照宣告順序比對，所以比較明確的路徑要放前面，最後再用 `anyRequest()` 收尾。

上面是現行寫法。跟 Spring Security 5 相比，換過這幾處：`WebSecurityConfigurerAdapter` 在 5.7 標成棄用（deprecated）、6.0 移除，改用 `SecurityFilterChain` Bean 來設定 `HttpSecurity`[出處](https://docs.spring.io/spring-security/site/docs/5.7.x/api/org/springframework/security/config/annotation/web/configuration/WebSecurityConfigurerAdapter.html)[移除紀錄](https://github.com/spring-projects/spring-security/issues/10902)；`authorizeRequests()` 換成 `authorizeHttpRequests()`，7.x 的 `HttpSecurity` 已經沒有前者[出處](https://docs.spring.io/spring-security/site/docs/current/api/org/springframework/security/config/annotation/web/builders/HttpSecurity.html)；`antMatchers()`、`mvcMatchers()` 換成 `requestMatchers()`，5.8 起這些方法都標為棄用[出處](https://docs.spring.io/spring-security/site/docs/5.8.x/api/org/springframework/security/config/annotation/web/AbstractRequestMatcherRegistry.html)；`@EnableGlobalMethodSecurity` 換成 `@EnableMethodSecurity`[出處](https://docs.spring.io/spring-security/reference/servlet/authorization/method-security.html)。

*【角色像職稱，權限像可以做的動作】*

## RBAC 與方法層級授權

> 🏠 **生活比喻**
>
> - RBAC＝**依職位給鑰匙**：經理拿經理的鑰匙組，不用一個個人設定
> - `@PreAuthorize`＝**在某個抽屜上再加一把鎖**，進了房間還要再檢查一次

角色存取控制（Role-Based Access Control，RBAC）不是逐一把權限發給每個使用者，而是先把一組權限指派給角色，再讓使用者擁有角色。例如 ADMIN 可以管理會員，USER 只能讀自己的資料。

路徑授權守在 HTTP 入口；方法層級授權則直接守住 Service 或 Controller 的方法。後者適合保護那些可能被多個入口呼叫的核心操作。

```
@PreAuthorize("hasRole('ADMIN')")
public void deleteMember(long memberId) {
    // 只有符合授權條件的身分才能執行
}
```

不要只靠前端把按鈕藏起來做權限控制。使用者還是可以自己呼叫 API，真正的授權判斷必須在後端執行。

*【瀏覽器拿號碼牌，伺服器保管登入狀態】*

## Cookie、Session 與權杖

> 🏠 **生活比喻**
>
> - Session＝**寄物櫃號碼牌**：伺服器記得你，你只拿號碼
> - Token（JWT）＝**蓋了防偽章的通行證**：伺服器不用記，看通行證上的章是真的就放行

Cookie 是瀏覽器保存、依規則附在請求上的一小段資料，格式像 `名稱=值`。Session（工作階段）是伺服器端維護的狀態；瀏覽器通常只保存一個識別碼，例如 `JSESSIONID`。

```
登入成功
  → 伺服器建立 Session
  → 回應用 Cookie 交付 JSESSIONID
  → 瀏覽器後續請求都帶著 JSESSIONID
  → 伺服器用它找到 Session 與登入身分
  → 登出或逾時後讓 Session 失效
```

Session 本身是 Servlet 容器提供的 `HttpSession`，Spring Security 沒有自己實作一套。`HttpSessionSecurityContextRepository` 把 `SecurityContext` 關聯到 `HttpSession`，它負責的是安全內容要放在哪裡，而放的地方就是容器的工作階段；換成 Redis（把資料放在記憶體裡的鍵值資料庫）這類外部儲存也是換掉這個儲存庫，不是換掉 Session 本身[出處](https://docs.spring.io/spring-security/reference/servlet/authentication/persistence.html)。Redis 適合放登入資訊、卻不適合直接當分散式鎖的理由，見〈分散式鎖與 Redis〉。

> 📝 查證更正：原筆記寫「Session 是後端程式的一種數據儲存方式，實作方式不限，Spring Security 預設是使用 Java 的 map 變數來實作」，查證後更正：Session 本身是 Servlet 容器（例如 Tomcat）提供的 HttpSession，Spring Security 並沒有自己實作一套 Session；它預設做的是把安全內容存進 HttpSession，這件事由 HttpSessionSecurityContextRepository 負責，也可以換成 Redis 等外部儲存

Cookie 不只用來登入，也可以保存個人化設定、購物車識別資訊或表單進度。但敏感內容不該直接明文放進去。

另一種架構是登入後發出權杖（token），之後由自訂 Filter 解析權杖並建立安全內容。最常見的權杖格式是 JWT（JSON Web Token）：伺服器把「你是誰、有哪些權限、什麼時候過期」寫成一段字串，再用自己的金鑰簽章；之後收到這段字串時驗一下簽章，就知道內容沒被人動過手腳，不必回頭查資料庫。要不要再把使用者狀態放進 Redis 是架構選擇，不是 JWT 的必要條件。權杖放在瀏覽器哪裡、CSRF 與 XSS 各要怎麼防，見〈網站安全三題：CORS、CSRF、密碼學〉；面試怎麼答 JWT 與 OAuth 2.0 的分工，見面試集〈後端與雲端面試題庫〉。

### 🗺️ 比喻對照表

| 技術名詞 | 生活比喻 |
| --- | --- |
| 認證 / 授權 | 門口刷卡 / 能按哪幾樓 |
| 401 / 403 | 卡刷不過 / 不能去那層 |
| Filter 鏈 | 機場一連串安檢 |
| UserDetailsService | 員工名冊 |
| RBAC | 依職位給鑰匙 |
| Session / JWT | 寄物櫃號碼牌 / 防偽通行證 |

### 重點整理

*   認證確認身分，授權判斷這個身分能不能做某件事；公開資源兩者都不需要。
*   Spring Security 透過 Filter 鏈在請求到達 Controller 前做安全檢查。
*   授權判斷現在由 `AuthorizationFilter` 負責，搭配 `authorizeHttpRequests` 設定。
*   路徑規則與方法層級規則互補，但後端才是權限判斷的最後防線。
*   RBAC 用角色承接一組權限，省掉逐一管理使用者權限的成本。
*   Session 由 Servlet 容器維護，Spring Security 只是把安全內容存進去。

## 隨堂測驗

**Q1. 已登入的一般會員想開只限 VIP 的影片，這主要是哪一類失敗？**

- (A) 授權失敗
- (B) 認證失敗
- (C) 密碼雜湊失敗
- (D) Session 建立失敗

<details><summary>看答案</summary>

**答案：(A)** 身分已經確認了，是權限不足，所以屬於授權失敗。

</details>

**Q2. 「所有請求都一定先認證再授權」這句話的問題在哪？**

- (A) 標成 permitAll 的公開路徑不需要認證，也不會去取出身分
- (B) 授權一定發生在認證之前
- (C) 認證與授權其實是同一件事
- (D) Spring Security 不做授權判斷

<details><summary>看答案</summary>

**答案：(A)** 公開端點不需要授權判斷，框架連工作階段裡的身分都不會去拿。

</details>

**Q3. Spring Security Filter 鏈的主要作用是什麼？**

- (A) 在請求進入 Controller 前依序執行認證與授權等安全處理
- (B) 只負責把 Java 物件轉成 JSON
- (C) 只負責建立資料庫交易
- (D) 只負責解析 Controller 的路由參數

<details><summary>看答案</summary>

**答案：(A)** 安全檢查發生在請求進入應用程式核心之前。

</details>

**Q4. 哪一個元件負責依使用者名稱載入帳號資料？**

- (A) UserDetailsService
- (B) SecurityContextHolder
- (C) ExceptionTranslationFilter
- (D) PasswordEncoder

<details><summary>看答案</summary>

**答案：(A)** UserDetailsService 定義的就是依名稱載入 UserDetails 這件事。

</details>

**Q5. .requestMatchers(​"/admin/\*\*").​hasRole(​"ADMIN") 的意義是什麼？**

- (A) 符合這個路徑的請求必須由具備 ADMIN 角色的身分存取
- (B) 所有請求都會自動取得 ADMIN 角色
- (C) 只有未登入者可以存取這個路徑
- (D) 這個路徑不再經過任何安全 Filter

<details><summary>看答案</summary>

**答案：(A)** requestMatchers 選出請求，hasRole 要求目前身分具備指定角色。

</details>

**Q6. RBAC 的核心做法是什麼？**

- (A) 把權限組合成角色，再把角色指派給使用者
- (B) 把每個網址都轉成一組密碼
- (C) 把使用者資料全部存進 Cookie
- (D) 讓所有已登入者共用相同權限

<details><summary>看答案</summary>

**答案：(A)** 角色是使用者與權限之間的一層管理介面。

</details>

**Q7. 在典型的 Session 登入架構裡，Session 本身是誰維護的？**

- (A) Servlet 容器提供的 HttpSession，Spring Security 只是把安全內容存進去
- (B) Spring Security 自己用一個 Java Map 實作
- (C) 瀏覽器的 localStorage
- (D) 資料庫的交易日誌

<details><summary>看答案</summary>

**答案：(A)** Spring Security 沒有自己實作 Session，它負責的是安全內容要存在哪裡。

</details>

**Q8. 自訂 Filter 同時被元件掃描自動註冊，又被手動加進安全鏈，最可能發生什麼？**

- (A) 同一個 Filter 對一次請求執行兩次
- (B) 所有 Filter 都會自動停用
- (C) Controller 會繞過 Filter 鏈
- (D) Session 一定會改成無狀態模式

<details><summary>看答案</summary>

**答案：(A)** Servlet 容器與 Spring Security 各註冊一次，就會重複執行。

</details>

**Q9. 為什麼不能只靠前端隱藏「刪除會員」按鈕來做授權？**

- (A) 使用者仍然可以直接呼叫 API，後端必須再檢查一次權限
- (B) 隱藏按鈕會讓密碼無法雜湊
- (C) 前端收不到任何 HTTP 狀態碼
- (D) 隱藏按鈕會讓 Session 立刻失效

<details><summary>看答案</summary>

**答案：(A)** 前端介面繞得過去，真正的存取控制只能由後端執行。

</details>
