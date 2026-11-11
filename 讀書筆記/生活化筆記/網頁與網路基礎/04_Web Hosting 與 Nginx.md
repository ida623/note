# 04. Web Hosting 與 Nginx

> 🏠 **生活化版本**：每個段落開頭的「生活比喻」先用日常情境帶你抓到感覺，接著再看原本的技術說明與程式碼；篇末有「比喻對照表」可以快速複習。

> 來源：[筆記平台 · 網頁與網路基礎](https://hhtim.github.io/notes-platform/web/#/lesson/hosting-nginx)　第 4 課 / 共 15 課 · 約 9 分鐘

**比較網站託管方案，並從真實除錯案例理解 Nginx 的反向代理、DNS 解析與路徑改寫。**

### 讀完這課你會

*   依成本、控制權與維運能力選擇託管方式
*   理解 Nginx 作為 Web 伺服器與反向代理的角色
*   分辨 `$request_uri` 與 `$uri`
*   從真實案例找出 DNS 解析與代理路徑問題

*【讓網站被找得到】*

## Web Hosting 是替網站準備營業場所

> 🏠 **生活比喻**
>
> Web Hosting 像**替店家找店面**：要有空間（儲存）、水電（運算）、門口的路（網路），網站才能開門營業。

Web Hosting（網站託管）是提供運算、儲存與網路環境，讓網站檔案或應用程式能持續接受網際網路請求。它不只「存放檔案」，還可能包含執行環境、TLS、監控、備份、擴充及資料庫服務。

典型架構可能包含硬體或雲端資源、作業系統、Web 伺服器、應用程式執行環境及資料層；代管平台則可能把其中多層藏起來，由供應商維護。

*【選住處】*

## 常見託管方式怎麼選？

> 🏠 **生活比喻**
>
> - 共享主機＝**跟別人合租店面**，便宜但互相影響
> - VPS＝**商場裡的獨立櫃位**
> - 雲端主機＝**按需求隨時換大小的店面**
> - 無伺服器＝**美食街攤位**，商場幫你顧水電，你只管賣

| 方式 | 特色 | 適合情境 | 主要代價 |
| --- | --- | --- | --- |
| 共享主機 | 多個租戶共享環境，管理簡單 | 小型網站、內容網站 | 控制權與資源彈性較低 |
| VPS | 取得隔離的虛擬主機資源 | 需要自訂環境的中小型服務 | 需自行管理系統與安全更新 |
| 專用伺服器 | 獨占實體主機 | 特殊硬體、隔離或合規需求 | 成本與維運負擔高 |
| 雲端託管 | 資源可彈性配置與擴縮 | 流量波動或高可用服務 | 架構及計費較複雜 |
| 容器平台 | 以映像封裝應用與相依性 | 多服務、可攜部署 | 需要容器與編排能力 |
| Serverless | 供應商管理底層資源，依事件執行 | API、事件處理、間歇工作 | 執行限制、平台相依與成本模型 |

「無伺服器」不是沒有伺服器，而是使用者通常不必直接配置或維護底層主機。選型時要一起考量預算、流量、延遲、合規、團隊維運能力、可攜性與擴充需求。

*【入口接待員】*

## Nginx 可以直接回檔案，也可以轉送請求

> 🏠 **生活比喻**
>
> Nginx 像**大樓的櫃台**：
> - 訪客要拿傳單（靜態檔）→ **櫃台直接給**
> - 訪客要找某公司（API）→ **櫃台幫你轉接到樓上**（反向代理）

Nginx 常扮演 Web 伺服器、反向代理、TLS 終止點或負載平衡器。直接提供 HTML、CSS、JavaScript 時，它像倉庫出貨員；把請求轉給後端服務時，則像櫃台替訪客找到正確部門。

```
upstream application_backend {
    server 127.0.0.1:9000;
}

server {
    listen 8080;
    root /usr/share/nginx/html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://application_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

`try_files` 常用於單頁應用程式：若實體檔案不存在，就回傳 `index.html`，再由前端路由處理網址。這也表示真正不存在的靜態資源可能被回成 HTML，設定時要配合資源路徑與錯誤處理。

`proxy_pass http://application_backend` 裡的名稱要先用 `upstream` 區塊定義——它替一組後端伺服器取名字，裡面可以列多台、設權重[出處](https://nginx.org/en/docs/http/ngx_http_upstream_module.html#upstream)。

若沒有這個區塊，Nginx 會把 `application_backend` 當成一般主機名稱、在載入設定時就去查 DNS；查不到就整份設定載入失敗，錯誤訊息是 `host not found in upstream`[出處](https://www.f5.com/company/blog/nginx/dns-service-discovery-nginx-plus)[原始碼](https://github.com/nginx/nginx/blob/master/src/core/ngx_inet.c)。

*【名稱要去哪裡查】*

## Nginx 的上游 DNS 解析時機

> 🏠 **生活比喻**
>
> `proxy_pass` 寫死主機名稱，像**櫃台上班時抄一次樓上公司的分機號碼就不再更新**；公司換了分機，櫃台還是撥舊號碼。用變數加 `resolver` 才會定期重查。

`proxy_pass` 寫死主機名稱時，Nginx 在啟動或重載設定時解析一次——解析失敗一般情況下會使啟動或重載失敗，成功後也不會照 DNS TTL 重新解析；`proxy_pass` 含變數時則改在處理請求時解析，此時必須用 `resolver` 指定 DNS 伺服器，並會依 TTL 更新[出處](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_pass)[resolver](https://nginx.org/en/docs/http/ngx_http_core_module.html#resolver)[F5 部落格](https://www.f5.com/company/blog/nginx/dns-service-discovery-nginx-plus)。

> 📝 查證更正：原筆記寫「Nginx DNS 解析步驟：1. 先使用 DNS 解析，再使用 Nginx resolver 指定的 DNS 解析 2. 後者的 DNS 解析結果會覆蓋前者」、所有形式「都會在啟動時被解析」，並稱解析失敗時「Nginx 會完全崩潰並停止所有 Web 請求」，查證後更正：固定名稱與含變數的名稱解析時機不同、不是兩階段互相覆蓋；解析失敗的後果是設定載入不成功（啟動或重載失敗），不是執行中崩潰。依據：nginx 文件 proxy_pass「Parameter value can contain variables. In this case, if an address is specified as a domain name, the name is searched among the described server groups, and, if not found, is determined using a resolver.」；resolver「By default, nginx caches answers using the TTL value of a response.」；F5（nginx 母公司）部落格「If the domain name can’t be resolved, NGINX fails to start or reload its configuration.」「NGINX caches the DNS records until the next restart or configuration reload, ignoring the records’ TTL values.」「When you use a variable to specify the domain name in the proxy_pass directive, NGINX re‑resolves the domain name when its TTL expires.」

```
location /telemetry/ {
    resolver 10.0.0.53 valid=30s;
    set $monitor_backend https://monitor.example.internal;
    proxy_pass $monitor_backend$request_uri;
}
```

`resolver` 放在 `http`、`server` 或 `location` 會形成不同作用範圍。全域設定較集中，局部設定則能隔離不同環境；DNS 位址應由部署環境提供，不應把內部位址硬寫成通用範例。

*【一個真實案例】*

## 同一路徑，要依環境代理到不同監控服務

> 🏠 **生活比喻**
>
> 像**同一個收件地址，依地區送到不同倉庫**：測試環境送測試倉、正式環境送正式倉，客人寫的地址不用改。

某個前端單頁應用程式需要載入監控腳本，並將資料送到監控服務。瀏覽器一律請求站內的 `/telemetry/`，避免前端直接知道各環境的內部服務位址；Nginx 再依目前站台環境轉送到對應上游。

```
瀏覽器
  → GET /telemetry/agent.js
  → Nginx 判斷目前環境
  → 測試環境或正式環境的監控服務
  → 回傳 agent.js
```

第一次設定把所有上游名稱直接寫進靜態 `proxy_pass`。結果容器啟動時，其中一個只有另一環境才能解析的名稱失敗，連目前可用的網站也無法正常啟動。

團隊後來把每個環境的解析器與上游放進各自的代理區塊，並以變數延後到真正收到該路徑的請求時才解析。這解決了啟動時跨環境 DNS 不可達的問題，也讓環境邊界更清楚。

*【第二個坑】*

## Rewrite 之後，到底該轉送哪一條路徑？

> 🏠 **生活比喻**
>
> rewrite 像**櫃台幫訪客把地址改寫成內部代號**，再依新代號決定送到哪；改寫完要確認**轉送的是改寫後還是原本的地址**。

入口規則先把公開路徑改寫成內部路徑，以便重新選擇 `location`：

```
location /telemetry/ {
    rewrite ^/telemetry/(.*)$ /telemetry_stage/$1 last;
}
```

`last` 會以改寫後的 URI 重新執行 location 比對。這時必須分清：

*   **$request_uri**：用戶端送來的原始 URI，通常包含查詢字串，rewrite 後仍不變。
*   **$uri**：目前正處理的正規化 URI，可被 rewrite 改變，通常不含查詢字串。

若上游仍期待原始的 `/telemetry/agent.js`，可明確傳遞原始 URI：

```
location /telemetry_stage/ {
    resolver 10.0.0.53;
    set $stage_backend https://monitor-stage.example.internal;
    proxy_pass $stage_backend$request_uri;
}
```

若上游期待改寫後的路徑，就應明確使用目前 URI 或組合出目標路徑。重點不是背一個斜線口訣，而是先寫下「用戶端 URI、目前 URI、上游 URI」三者的預期值，再測試含路徑與查詢字串的案例。

*【從錯誤訊息回推】*

## 「no host in upstream」不應只怪雙斜線

> 🏠 **生活比喻**
>
> 這個錯誤像**櫃台拿到一個空白的轉接號碼**：變數展開後沒有主機名稱，跟多一個斜線不一定有關，要看變數到底有沒有值。

`no host in upstream` 的意思是：Nginx 把變數展開、組出上游網址之後，發現 `://` 後面的主機名稱那一段是空的。「雙斜線」要分兩種看。路徑中間多一個斜線（`https://host//a/b`）只影響路徑語意，主機還在，不會產生這個錯誤；但 `://` 後面直接接 `/`（`https:///agent.js`，例如放主機名稱的變數展開後只剩協定字首）就等於主機名稱是空的，正是這個錯誤的成因之一。變數整個是空的則會走到另一個訊息 `invalid URL prefix`，因為連 `http://` 都沒有。

Nginx 的判斷流程：`ngx_http_proxy_eval()` 先確認網址以 `http://` 或 `https://` 開頭（不是就記 invalid URL prefix），再交給 `ngx_parse_url()`，主機那段長度為 0 時記下 `no host`，印出來就是「no host in upstream」[proxy 模組](https://github.com/nginx/nginx/blob/master/src/http/modules/ngx_http_proxy_module.c)[ngx_inet.c](https://github.com/nginx/nginx/blob/master/src/core/ngx_inet.c)。主機為空只是成因之一——只要組出來的結果主機那段是空的——不論是順序錯還是變數沒值——都是這個訊息，所以照下面的順序一項一項排除。

較可靠的除錯順序是：

1.  以設定測試確認語法有效。
2.  記錄或檢查變數展開後的上游主機與 URI。
3.  在相同執行環境驗證 DNS 能否解析。
4.  確認 TLS 名稱、Host 標頭與上游憑證是否相符。
5.  測試原始路徑、改寫路徑、查詢字串與尾端斜線。

*【安全與快取】*

## 能代理成功，還不等於適合上線

> 🏠 **生活比喻**
>
> 轉接成功只是第一步，還要想：**等多久算超時、包裹太大要不要收、轉接失敗要不要重試、敏感資訊別外流**。

反向代理設定還要考量逾時、請求大小、重試、上游 TLS 驗證、存取控制與敏感標頭。若要停用快取，應理解 `Cache-Control` 標頭裡 `no-store` 與 `no-cache` 兩個指令的差異，以及另一個標頭 `Expires` 的角色（有 `Cache-Control: max-age` 時 `Expires` 會被忽略）[出處](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Expires)，而不是重複加入彼此矛盾的標頭。

設定檔也不應包含 API 金鑰、私密金鑰或可識別內部環境的資訊。機密值應透過適合的秘密管理機制注入，日誌則要避免記錄權杖與個資。

### 🗺️ 比喻對照表

| 技術名詞 | 生活比喻 |
| --- | --- |
| Web Hosting | 替網站找店面 |
| 無伺服器 | 美食街攤位 |
| Nginx | 大樓櫃台 |
| 反向代理 | 櫃台幫你轉接到樓上 |
| 上游 DNS 快取 | 櫃台只抄一次分機號碼 |

### 重點整理

*   Hosting 選型是在成本、控制權、擴充性與維運負擔之間取捨。
*   Nginx 可提供靜態檔案，也可依主機、路徑或規則把請求代理到上游。
*   含變數的 proxy_pass、resolver、rewrite 與 URI 組合必須一起驗證。

## 隨堂測驗

**Q1. Web Hosting 的核心用途是什麼？**

- (A) 提供網站可持續對外服務所需的運算、儲存與網路環境
- (B) 替網站申請並管理網域名稱
- (C) 把網站程式碼編譯成瀏覽器可執行的格式
- (D) 代替瀏覽器渲染網頁後回傳畫面

<details><summary>看答案</summary>

**答案：(A)** 託管服務讓網站檔案或應用程式能在網路上接受請求；網域註冊與渲染是別的服務或角色。

</details>

**Q2. 團隊不想管理主機，工作量又隨事件大幅波動，哪種方案通常值得優先評估？**

- (A) Serverless 或代管平台
- (B) 專用實體伺服器且全部自行維運
- (C) 只購買網域名稱
- (D) 在每位使用者電腦上部署資料庫

<details><summary>看答案</summary>

**答案：(A)** Serverless 將底層資源管理交給供應商，適合事件驅動與波動負載，但仍要評估限制。

</details>

**Q3. Nginx 作為反向代理時在做什麼？**

- (A) 接收用戶端請求並轉送到適當上游
- (B) 代替用戶端向外部網站發出請求（正向代理）
- (C) 直接執行後端應用程式的商業邏輯
- (D) 把靜態檔案編譯成動態內容

<details><summary>看答案</summary>

**答案：(A)** 反向代理位於用戶端與後端服務之間，負責轉送與相關入口功能；替用戶端連外的是正向代理。

</details>

**Q4. 單頁應用程式中的 try_files 常把未知前端路由導向哪裡？**

- (A) index.html
- (B) 404 錯誤頁
- (C) 上游應用程式的 /api/ 路徑
- (D) 最接近的 CDN 節點

<details><summary>看答案</summary>

**答案：(A)** 回傳 index.html 後，可由前端路由器解讀目前路徑；直接回 404 反而會讓前端路由失效。

</details>

**Q5. proxy_pass 使用含主機名稱的變數時，為何常需要 resolver？**

- (A) 名稱要在請求處理期間由 Nginx 解析
- (B) 變數會停用作業系統的 hosts 檔案
- (C) resolver 負責快取上游回應內容
- (D) 沒有 resolver 時 Nginx 會改用預設上游

<details><summary>看答案</summary>

**答案：(A)** 變數上游通常在執行期決定，Nginx 需要指定 DNS 解析器；其餘選項不是 resolver 的作用。

</details>

**Q6. rewrite 執行後，哪個變數通常仍保存原始 URI 與查詢字串？**

- (A) $request_uri
- (B) $uri
- (C) $host
- (D) $remote_addr

<details><summary>看答案</summary>

**答案：(A)** $request_uri 保留原始請求；$uri 則可能被正規化或改寫。

</details>

**Q7. 看到 no host in upstream 時，最優先檢查什麼？**

- (A) proxy_pass 展開後是否真的包含有效主機
- (B) 上游伺服器的憑證是否過期
- (C) location 區塊的比對順序
- (D) add_header 是否重複設定

<details><summary>看答案</summary>

**答案：(A)** 此錯誤直接指向上游 URL 的主機部分，常見原因是空變數或錯誤組合；其餘項目是別種症狀的檢查點。

</details>

**Q8. 把 resolver 分別放在不同 location 的主要好處是什麼？**

- (A) 可讓不同代理路徑使用各自適用的 DNS 設定
- (B) 可以省略 proxy_pass 的主機名稱
- (C) 讓所有 location 共用同一份 DNS 快取
- (D) 避免設定檔需要重載

<details><summary>看答案</summary>

**答案：(A)** 局部 resolver 可隔離不同環境或服務的名稱解析策略；共用設定反而是放 http 區塊的效果。

</details>
