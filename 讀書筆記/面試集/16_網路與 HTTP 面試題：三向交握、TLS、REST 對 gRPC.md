# 16. 網路與 HTTP 面試題：三向交握、TLS、REST 對 gRPC

> 來源：[筆記平台 · 面試集](https://hhtim.github.io/notes-platform/interview/#/lesson/network-http-qa)　第 16 課 / 共 23 課 · 約 20 分鐘

**OSI 對四層、三向交握與 TIME_WAIT、TLS 1.3 握手與 0-RTT、HTTP/1.1 到 HTTP/3、常考狀態碼、冪等與快取、REST 對 gRPC 對 GraphQL、Cookie 與 CORS——十五題的面試答法，每句附 RFC 章節出處。**

### 讀完這課你會

*   對照 OSI 七層與 TCP/IP 四層
*   答出三向交握與四向揮手的細節
*   講出 TLS 1.3 握手與 HTTPS 怎麼加密
*   比較 HTTP 各版本與幾種 API 風格

*【分層與 TCP】*

## 從七層講到三向交握

握手的逐步拆解與實跑見〈TCP、UDP 與 TLS 握手〉。

答題公式：先一句話定義，再講差別與取捨，最後補一句實務或版本註記。

> 💡 面試官：OSI 七層與 TCP/IP 四層怎麼對應？HTTP、TCP、IP 各在哪層？

**一句話定義**：OSI 是 1978 年起草、1984 年成為 ISO 7498 標準的七層參考模型[出處](https://en.wikipedia.org/wiki/OSI_model)，把網路通訊拆成一疊協定層，每層有一組固定功能，對上層提供服務、隱藏實作細節[出處](https://learn.microsoft.com/en-us/windows-hardware/drivers/network/windows-network-architecture-and-the-osi-model)。

TCP/IP 四層是網際網路實際使用的分層，由上到下是應用層、傳輸層、網際網路層、鏈結層（〈網路是怎麼運作的〉稱網路存取層）[RFC 1122 第 1.1.3 節](https://www.rfc-editor.org/rfc/rfc1122.html#page-8)。

| OSI 七層（由上到下） | TCP/IP 四層 | 面試要能點名的協定 |
| --- | --- | --- |
| 應用層、表現層、會議層[出處](https://en.wikipedia.org/wiki/OSI_model#Comparison_with_TCP/IP_model)（RFC 1122 自己只算表現＋應用兩層[RFC 1122 第 1.1.3 節](https://www.rfc-editor.org/rfc/rfc1122.html#page-9)） | 應用層 | HTTP、DNS、SMTP |
| 傳輸層 | 傳輸層 | TCP、UDP |
| 網路層 | 網際網路層 | IP、ICMP（回報錯誤與探測用的控制訊息協定，ping 就是用它） |
| 資料鏈結層、實體層 | 鏈結層 | Ethernet、Wi-Fi |

**怎麼答才不掉進背誦**：面試官要的不是七個名字，是「你知道每個協定在解決什麼問題」。

抓三句：IP 負責跨網路把封包送到目的主機，但不保證端到端送達，封包可能損毀、重複、亂序或根本沒到[RFC 1122 第 1.1.3 節](https://www.rfc-editor.org/rfc/rfc1122.html#page-9)；TCP 在它上面補上可靠性；HTTP 再在 TCP 上面定義請求與回應的語意。

TLS 放哪一層是常見追問：它同時有傳輸層與表現層的性質，塞不進七層任何一格[出處](https://en.wikipedia.org/wiki/OSI_model#Layer_4:_Transport_layer)。答「介於傳輸層與應用層之間、替應用層資料加密」即可。四層分工的白話版與每層例子見〈網路是怎麼運作的〉。

> 💡 面試官：TCP 三向交握每一步在做什麼？為什麼是三次不是兩次？

**一句話定義**：三向交握（three-way handshake）是 TCP 建立連線的程序[RFC 9293 第 3.5 節](https://www.rfc-editor.org/rfc/rfc9293.html#section-3.5)，目的是讓兩端各自告訴對方「我的起始序號是幾號」並得到確認。旗標（flag，TCP 標頭裡一個位元一個開關）：SYN 是同步序號，ACK 是確認欄位有效，FIN 是送方沒有資料了[RFC 9293 第 3.1 節](https://www.rfc-editor.org/rfc/rfc9293.html#section-3.1)。

| 步驟 | 誰送 | 旗標 | 序號與確認號（照 RFC 9293 圖 6 的數字） | 送完後的狀態 |
| --- | --- | --- | --- | --- |
| 1 | 用戶端 | SYN | SEQ=100 | 用戶端 SYN-SENT，伺服器收到後 SYN-RECEIVED |
| 2 | 伺服器 | SYN＋ACK | SEQ=300、ACK=101（「你的 100 我收到了，下一個給我 101」） | 用戶端收到後 ESTABLISHED |
| 3 | 用戶端 | ACK | SEQ=101、ACK=301 | 伺服器收到後 ESTABLISHED；這一段可以直接帶資料 |

**為什麼是三次：**

*   每一端都要送出自己的起始序號、收到對方的確認；也要收到對方的起始序號並回確認。寫開來是四步：A 送 SYN、B 回 ACK、B 送 SYN、A 回 ACK。
*   第 2、3 步可以合成一個訊息，所以叫三向（或三訊息）交握。[RFC 9293 第 3.5 節](https://www.rfc-editor.org/rfc/rfc9293.html#section-3.5)
*   兩次不夠：第二步只確認了用戶端的序號，伺服器自己的序號還沒被確認。
*   追問「三次到底防什麼」：主要是防止舊的重複連線請求造成混亂。序號不綁全球時鐘，網路裡遲到的舊 SYN 若只靠兩步就會被當成新連線。[RFC 9293 第 3.5 節](https://www.rfc-editor.org/rfc/rfc9293.html#section-3.5)

> 三次＝雙方各一次 SYN 加各一次 ACK，中間那兩個合成一包；第三步的 ACK 是在替伺服器的序號蓋章

> 💡 面試官：四向揮手怎麼走？TIME_WAIT 是什麼、為什麼伺服器上會很多？

**一句話定義**：關閉連線是雙方各自送 FIN、各自被 ACK 的四段過程。正常關閉的順序：[RFC 9293 第 3.6 節](https://www.rfc-editor.org/rfc/rfc9293.html#section-3.6)

*   主動關閉的一方送 FIN（帶 ACK），進 FIN-WAIT-1。
*   對方回 ACK 進 CLOSE-WAIT，主動方進 FIN-WAIT-2。
*   對方應用程式也關閉後，送出自己的 FIN，進 LAST-ACK。
*   主動方回最後一個 ACK 進 TIME_WAIT，等 2 MSL 後才 CLOSED。（RFC 寫成 TIME-WAIT，netstat／ss 指令的輸出寫成 TIME_WAIT。）

**為什麼是四段不是三段**：因為 TCP 的關閉是單向的：收到 FIN 的一端先回 ACK，要等自己的使用者也 CLOSE 之後才送自己的 FIN[RFC 9293 第 3.6 節](https://www.rfc-editor.org/rfc/rfc9293.html#section-3.6)，中間那段對方可能還有資料要送完，所以 ACK 與 FIN 通常分開。

**TIME_WAIT 在等什麼**：等夠久，確定對方收到了對它關閉請求的確認，並避免新連線被前一條連線延遲到達的區段影響。[RFC 9293 第 3.3.2 節](https://www.rfc-editor.org/rfc/rfc9293.html#section-3.3.2)

等多久是硬性規定（MUST）：主動關閉的連線要在 TIME-WAIT 停留 2 倍 MSL[RFC 9293 第 3.6 節](https://www.rfc-editor.org/rfc/rfc9293.html#section-3.6)；MSL（Maximum Segment Lifetime，一個區段在網路上最多能活多久）取 2 分鐘，這是工程上的選擇[RFC 9293 第 3.4.1 節](https://www.rfc-editor.org/rfc/rfc9293.html#section-3.4.1)。

為什麼要 2 倍：最後那個 ACK 可能丟，對方會重送 FIN，一來一回各一個 MSL。

**為什麼伺服器上會很多**：TIME_WAIT 落在「主動關閉」的那一端。伺服器若在每次回應後主動關連線（例如短連線的 HTTP 服務），每條連線關掉後都會在伺服器上留一個 TIME_WAIT 記錄，照 RFC 是 4 分鐘（2 倍 MSL），Linux 實作是 60 秒[Linux tcp.h 的 TCP_TIMEWAIT_LEN](https://github.com/torvalds/linux/blob/master/include/net/tcp.h)；流量一大就累積成千上萬個，吃的是記憶體與連線表。應用伺服器對後端資料庫或快取每次新開連線再主動關掉時，它自己是用戶端，堆的 TIME_WAIT 還會把暫時埠（用戶端每條連線臨時借用的埠號）用光。解法是連線重用（HTTP 持久連線、資料庫連線池），少關就少等。

> 💡 面試官：TCP 對 UDP 差在哪？什麼場景選 UDP？

**一句話定義**：TCP 提供可靠、有序的位元組串流，可靠性來自用序號偵測封包遺失、用每段的檢查碼偵測錯誤，再靠重傳修正[RFC 9293 第 2.2 節](https://www.rfc-editor.org/rfc/rfc9293.html#section-2.2)；UDP 則用最少的協定機制讓應用程式互送訊息，以交易為導向，不保證送達也不保證不重複[RFC 768](https://www.rfc-editor.org/rfc/rfc768.html)。

|   | TCP | UDP |
| --- | --- | --- |
| 連線 | 先三向交握，有狀態 | 沒有連線，直接送 |
| 可靠與順序 | 序號、確認、重傳，保證到且有序 | 都不保證，應用程式自己補 |
| 壅塞控制 | 必須（MUST）實作慢啟動（一開始少送，每收到確認就加速）、壅塞避免（接近網路容量後改成慢慢加）與重傳逾時的指數退避（每重傳一次，等待時間翻倍）[RFC 9293 第 3.8.2 節](https://www.rfc-editor.org/rfc/rfc9293.html#section-3.8.2) | 沒有，塞不塞網路由應用程式負責 |
| 資料單位 | 位元組串流，邊界由應用層自己切 | 一則訊息一個資料包，邊界天然存在 |

**什麼時候選 UDP**：兩類。

*   一問一答、寧可重問也不想等握手：DNS 就是代表。UDP 不適合區域轉送，但是網際網路上標準查詢的建議方式。[RFC 1035 第 4.2.1 節](https://www.rfc-editor.org/rfc/rfc1035.html#section-4.2.1)
*   要自己掌控可靠性與延遲：即時語音影像丟一格畫面比等重傳好；HTTP/3 用的 QUIC 更是直接把可靠性與 TLS 都做在 UDP 上面。UDP 被擋而連不上 QUIC 時，用戶端應該（SHOULD）改試 TCP 版的 HTTP。[RFC 9114 第 3.1 節](https://www.rfc-editor.org/rfc/rfc9114.html#section-3.1)

答題時補一句「UDP 不是不可靠的代名詞，是把可靠性的決定權交給應用層」，會比背「TCP 可靠、UDP 快」高一個層次。TCP 對 UDP 的比喻版見〈網路是怎麼運作的〉。

*【TLS 與 HTTPS】*

## 握手、版本差異與憑證鏈

> 💡 面試官：TLS 1.3 握手怎麼走？跟 TLS 1.2 少了什麼？憑證鏈怎麼驗？

**一句話定義**：TLS 握手是在傳資料之前驗證對方身分、協商加密參數、建立共用金鑰的協定[RFC 8446 第 1 節](https://www.rfc-editor.org/rfc/rfc8446.html#section-1)。完整握手分成三個階段：金鑰交換（Key Exchange）、伺服器參數（Server Parameters）、身分驗證（Authentication）；金鑰交換階段之後的一切都是加密的[RFC 8446 第 2 節](https://www.rfc-editor.org/rfc/rfc8446.html#section-2)。

*   **第一趟（用戶端→伺服器）**：ClientHello，帶自己支援的加密套件與 key_share（Diffie-Hellman 金鑰交換用的公開值——雙方各丟一個公開值，就能各自算出同一把秘密）。
*   **第二趟（伺服器→用戶端）**：ServerHello 帶伺服器的 key_share——到這裡雙方已經算得出共用金鑰；接著的 EncryptedExtensions、Certificate、CertificateVerify、Finished 全部已經加密。
*   **第三趟（用戶端→伺服器）**：用戶端送 Finished，然後就可以送應用資料。這種正常握手叫 1-RTT 握手[RFC 8446 第 2.3 節](https://www.rfc-editor.org/rfc/rfc8446.html#section-2.3)（RTT，round-trip time，來回一趟的時間）。

**跟 TLS 1.2 差在哪**：先講趟數：TLS 1.2 的完整握手是 ClientHello、ServerHello 到 ServerHelloDone、ClientKeyExchange 與用戶端 Finished、伺服器 Finished，之後才有應用資料，數起來是兩趟來回[RFC 5246 第 7.3 節](https://www.rfc-editor.org/rfc/rfc5246.html#section-7.3)，TLS 1.3 少一趟。

再講 TLS 1.3 的重大差異：

*   **靜態 RSA 與靜態 Diffie-Hellman** 加密套件被拿掉，所有公開金鑰交換機制都提供前向保密（forward secrecy，長期私鑰日後洩漏也解不開過去的流量）。
*   **ServerHello 之後的所有握手訊息都加密**。
*   **對稱加密演算法清單**清掉舊的，只剩 AEAD（帶完整性驗證的加密模式）。
*   **新增 0-RTT 模式**。
*   **工作階段恢復改成 PSK**（預先共用金鑰）機制。
*   **ChangeCipherSpec 這類多餘訊息移除**[RFC 8446 第 1.2 節](https://www.rfc-editor.org/rfc/rfc8446.html#section-1.2)。

**0-RTT 的風險（必被追問）**：0-RTT 是用上次的 PSK 在第一趟就夾帶應用資料，安全性較弱：[RFC 8446 第 2.3 節](https://www.rfc-editor.org/rfc/rfc8446.html#section-2.3)

*   不是前向保密的，因為只用 PSK 推導的金鑰加密。
*   不保證跨連線不會被重放。

面試答法：0-RTT 只放冪等的請求——冪等就是同一個請求送幾次結果都一樣，例如 GET；扣款這類請求不能走 0-RTT，因為攔截者可以把同一包重送一次。

**憑證鏈怎麼驗**：伺服器在 Certificate 訊息裡送一串憑證：送方自己的憑證必須（MUST）放第一個，後面每一張應該（SHOULD）直接簽發前一張；信任錨（trust anchor，用戶端本來就信的根憑證）可以省略不送[RFC 8446 第 4.4.2 節](https://www.rfc-editor.org/rfc/rfc8446.html#section-4.4.2)。

用戶端做路徑驗證：確認第一張由信任錨簽發、每一張的主體是下一張的簽發者、最後一張是要驗的目標，且每一張在當下都有效[RFC 5280 第 6.1 節](https://www.rfc-editor.org/rfc/rfc5280.html#section-6.1)。

伺服器另外用 CertificateVerify 拿憑證裡那把公鑰對應的私鑰，對整段握手紀錄做數位簽章，證明「我不只拿得出這張憑證，我還握有它的私鑰」。[RFC 8446 第 4.4.3 節](https://www.rfc-editor.org/rfc/rfc8446.html#section-4.4.3)

> 💡 面試官：HTTPS 是對稱還是非對稱加密？各用在哪個階段？

**一句話定義**：兩種都用，分工在 TLS 的兩個組件上：握手協定驗證通訊雙方、協商加密模式與參數、建立共用金鑰；紀錄協定用握手建立的參數保護流量[RFC 8446 第 1 節](https://www.rfc-editor.org/rfc/rfc8446.html#section-1)。

*   **非對稱，用在握手**：兩件事。金鑰交換用 (EC)DHE（TLS 1.3 支援的三種模式是 (EC)DHE、PSK-only、PSK 搭 (EC)DHE）[RFC 8446 第 2 節](https://www.rfc-editor.org/rfc/rfc8446.html#section-2)；身分驗證用憑證加 CertificateVerify 的數位簽章[RFC 8446 第 4.4.3 節](https://www.rfc-editor.org/rfc/rfc8446.html#section-4.4.3)。注意 TLS 1.3 不再拿伺服器的 RSA 公鑰直接加密金鑰送過去（那是被移除的靜態 RSA），公鑰只用來簽章。
*   **對稱，用在資料**：紀錄協定用 AEAD 演算法加密每一筆紀錄，輸入是一把金鑰、一個 nonce（只用一次的數字，讓同樣的明文每次加密結果都不同）、明文與附加資料；那把金鑰就是握手算出來的共用金鑰。[RFC 8446 第 5.2 節](https://www.rfc-editor.org/rfc/rfc8446.html#section-5.2)

> 非對稱慢但能在陌生人之間建立信任與共用秘密，只在握手用一次；對稱快，之後每一個位元組都靠它

HTTPS 提供的三種保護（機密性、完整性、身分驗證）與「HTTPS 不等於網站沒有漏洞」見〈HTTP 與 HTTPS〉。

*【HTTP 版本】*

## 1.1 的持久連線、2 的多工、3 的 QUIC

> 💡 面試官：HTTP/1.1 的 Keep-Alive 與隊頭阻塞是什麼？HTTP/2 的多工解決了什麼？HTTP/3 為什麼改用 QUIC？

**HTTP/1.1——連線預設不關**：收到的協定是 HTTP/1.1（或更新）時，連線在這次回應後繼續保持；HTTP/1.0 則要看有沒有帶 keep-alive 連線選項[RFC 9112 第 9.3 節](https://www.rfc-editor.org/rfc/rfc9112.html#section-9.3)。所以 `Connection: keep-alive` 是 HTTP/1.0 時代的用法，1.1 不寫也持久，要關才寫 `Connection: close`。別跟 TCP 自己的 keep-alive 混在一起：那是送探測區段確認閒置連線是否還活著、預設關閉的機制[RFC 9293 第 3.8.4 節](https://www.rfc-editor.org/rfc/rfc9293.html#section-3.8.4)，跟 HTTP 的持久連線是兩回事。

**隊頭阻塞（head-of-line blocking，排在前面那個沒回，後面全部得等）：**[RFC 9113 第 1 節](https://www.rfc-editor.org/rfc/rfc9113.html#section-1)

*   HTTP/1.0 在一條 TCP 連線上一次只允許一個未完成的請求。
*   HTTP/1.1 加了管線化（pipelining，不等回應就連續送請求），只解決了一部分併發問題，仍然有應用層隊頭阻塞：管線化的回應必須照請求順序回，第一個慢就全部慢。
*   所以 HTTP/1.0 與 1.1 的用戶端靠對同一台伺服器開多條連線來併發。

**HTTP/2——一條連線多個串流**：同一條連線上可以交錯傳送訊息，HTTP 欄位用高效的編碼處理，請求也可以設定優先權[RFC 9113 第 1 節](https://www.rfc-editor.org/rfc/rfc9113.html#section-1)。

做法是把訊息切成二進位的訊框（frame），每個請求回應一個串流（stream）；一條 HTTP/2 連線可以同時開著多個串流，任一端都可以交錯送出多個串流的訊框[RFC 9113 第 5 節](https://www.rfc-editor.org/rfc/rfc9113.html#section-5)。

請求行也不見了，方法、協定、主機、路徑改成 `:method`、`:scheme`、`:authority`、`:path` 四個偽標頭（pseudo-header，以冒號開頭、協定自己用的標頭欄位）；有 `:authority` 時，收方不得（MUST NOT）用 Host 標頭判斷目標[RFC 9113 第 8.3.1 節](https://www.rfc-editor.org/rfc/rfc9113.html#section-8.3.1)。走 TLS 的 HTTP/2 要求 TLS 1.2 以上[RFC 9113 第 9.2 節](https://www.rfc-editor.org/rfc/rfc9113.html#section-9.2)。

**但 HTTP/2 沒解決 TCP 那一層的阻塞**：HTTP/2 本身就沒處理 TCP 的隊頭阻塞。[RFC 9113 第 1 節](https://www.rfc-editor.org/rfc/rfc9113.html#section-1) 多工是 HTTP 層做的，TCP 的遺失復原機制看不到這些平行的串流，只看到一條位元組串流；一個遺失或亂序的封包會讓所有進行中的交易停擺，不管那筆交易有沒有真的受到影響。[RFC 9114 第 1 節](https://www.rfc-editor.org/rfc/rfc9114.html#section-1)

**HTTP/3——把多工交給 QUIC**：QUIC 內建串流多工與每串流的流量控制，可靠性做在串流層級、壅塞控制做在整條連線層級。[RFC 9114 第 1.2 節](https://www.rfc-editor.org/rfc/rfc9114.html#section-1.2)

*   避免跨串流的隊頭阻塞：封包遺失時，只有該封包裡有資料的串流要等重傳，其他串流可以繼續。[RFC 9000 第 13 節](https://www.rfc-editor.org/rfc/rfc9000.html#section-13)
*   握手合併：QUIC 的握手同時協商加密與傳輸參數，整合了 TLS 握手，不用先 TCP 三向交握再 TLS 握手。[RFC 9000 第 1 節](https://www.rfc-editor.org/rfc/rfc9000.html#section-1)

|   | HTTP/1.1 | HTTP/2 | HTTP/3 |
| --- | --- | --- | --- |
| 傳輸 | TCP | TCP（實務上幾乎都走 TLS） | QUIC（UDP 之上、內建 TLS 1.3） |
| 訊息格式 | 文字，一行一欄位 | 二進位訊框、HPACK 壓縮標頭（重複出現的標頭用索引編號代替，省流量） | 二進位訊框、QPACK 壓縮標頭（HPACK 改成能容忍 QUIC 封包亂序到達的版本） |
| 併發 | 管線化少有瀏覽器開，實務上一連線一個未完成請求，靠多開連線 | 一連線多串流 | 一連線多串流，且串流各自獨立重傳 |
| 隊頭阻塞 | 應用層有 | 應用層解了，TCP 層還在 | 兩層都解 |

「HTTP 不一定跑在 TCP 上」與各版本的連線流程見〈HTTP 與 HTTPS〉、〈從輸入網址到看到網頁〉。

*【HTTP 語意】*

## 狀態碼、方法、快取

狀態碼與快取的 curl 實跑見〈HTTP 進階：狀態碼、快取、Keep-Alive 與版本演進〉。

> 💡 面試官：常見狀態碼各代表什麼？401 與 403 差在哪？

狀態碼定義在 RFC 9110 第 15 節。答題時先講類別（2xx 成功、3xx 轉向、4xx 用戶端錯、5xx 伺服器錯），再挑幾組容易混的講差別。

| 狀態碼 | 定義 | 面試補一句 |
| --- | --- | --- |
| 200 OK | 請求成功[§15.3.1](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.3.1) | 內容隨方法而不同，GET 回資源表述 |
| 201 Created | 請求已完成並建立了一個或多個新資源，主要資源由 Location 標頭或目標 URI 指出[§15.3.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.3.2) | POST 建資源成功回 201 不是 200 |
| 204 No Content | 成功完成，但沒有額外內容要回[§15.3.5](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.3.5) | DELETE 或 PUT 成功常用 |
| 301 Moved Permanently | 目標資源已有新的永久 URI[§15.4.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.4.2) | 可被快取；歷史原因，用戶端可能把 POST 改成 GET |
| 302 Found | 目標資源暫時在另一個 URI，之後仍應用原 URI[§15.4.3](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.4.3) | 同樣可能被改成 GET；要保留方法用 307（暫時）[§15.4.8](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.4.8)或 308（永久）[§15.4.9](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.4.9) |
| 304 Not Modified | 收到條件式 GET 或 HEAD，要不是條件判定為假，本來會回 200；用戶端手上的版本仍有效，不必再傳[§15.4.5](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.4.5) | 快取驗證的核心，見下面快取那題 |
| 400 Bad Request | 伺服器認為是用戶端錯誤而無法或不願處理（語法錯、訊息框架錯等）[§15.5.1](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.5.1) | 語法層面的錯 |
| 401 Unauthorized | 請求缺少對目標資源有效的身分驗證憑據；伺服器必須（MUST）回 WWW-Authenticate 標頭[§15.5.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.5.2) | 名字叫 Unauthorized，意思其實是「未驗證身分」 |
| 403 Forbidden | 伺服器理解請求但拒絕執行；若帶了憑據，代表憑據不足以取得存取；也可能因為與憑據無關的理由被禁止[§15.5.4](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.5.4) | 知道你是誰，但你沒權限 |
| 404 Not Found | 找不到目標資源目前的表述，或不願透露它存在[§15.5.5](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.5.5) | 不想洩漏資源存在時，403 可以改回 404 |
| 409 Conflict | 請求與目標資源目前的狀態衝突，使用者可能解決衝突後重送[§15.5.10](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.5.10) | 版本衝突、重複建立同一筆 |
| 422 Unprocessable Content | 內容型別懂、語法也對，但無法處理其中的指令（例如格式正確但語意錯的欄位）[§15.5.21](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.5.21) | 驗證失敗常用；400 是看不懂，422 是看懂但不合理 |
| 429 Too Many Requests | 使用者在一段時間內送了太多請求（限流）；可帶 Retry-After[RFC 6585 §4](https://www.rfc-editor.org/rfc/rfc6585.html#section-4) | 定義在 RFC 6585，不在 9110 |
| 500 Internal Server Error | 伺服器遇到未預期的狀況而無法完成請求[§15.6.1](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.6.1) | 程式例外沒接住的預設結果 |
| 502 Bad Gateway | 伺服器作為閘道或代理時，從上游收到無效回應[§15.6.3](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.6.3) | Nginx 後面的應用程式掛了、回了看不懂的東西 |
| 503 Service Unavailable | 暫時過載或排定維護而無法處理，可帶 Retry-After[§15.6.4](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.6.4) | 「等一下再來」，斷路器（circuit breaker，下游連續失敗就先不打過去、直接回錯的保護開關）打開時常回這個 |
| 504 Gateway Timeout | 作為閘道或代理時，沒有及時收到上游回應[§15.6.5](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.6.5) | 上游太慢；502 是回了但壞掉，504 是根本沒回 |

> 401 是「你是誰？」，403 是「我知道你是誰，不行」；502 是上游回了壞東西，504 是上游沒在時限內回

> 💡 面試官：GET／POST／PUT／PATCH／DELETE 的語意？哪些冪等、哪些安全？

**一句話定義：**「安全」是方法的語意本質上唯讀、不會改伺服器狀態；「冪等」是同一個請求送一次跟送多次，對伺服器的預期效果一樣。GET、HEAD、OPTIONS、TRACE 是安全方法[RFC 9110 第 9.2.1 節](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.1)；PUT、DELETE 與所有安全方法是冪等的[RFC 9110 第 9.2.2 節](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.2)。

| 方法 | 語意 | 安全 | 冪等 |
| --- | --- | --- | --- |
| GET | 要求傳回目標資源目前的表述[§9.3.1](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.3.1) | 是 | 是 |
| HEAD | 跟 GET 一樣但伺服器不得（MUST NOT）送內容[§9.3.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.3.2) | 是 | 是 |
| POST | 要求目標資源依它自己的語意處理請求裡的表述——例如送表單、建立尚未有識別的新資源[§9.3.3](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.3.3) | 否 | 否 |
| PUT | 要求目標資源的狀態被建立，或整個換成請求裡的表述[§9.3.4](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.3.4) | 否 | 是 |
| PATCH | 部分修改；PATCH 既不安全也不冪等，但可以設計成冪等[RFC 5789 §2](https://www.rfc-editor.org/rfc/rfc5789.html#section-2) | 否 | 不保證 |
| DELETE | 要求原始伺服器移除目標資源與它目前功能的關聯[§9.3.5](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.3.5) | 否 | 是 |

**為什麼面試愛問冪等**：因為它決定「能不能自動重試」：冪等方法在連線失敗、回應還沒收到時，可以自動重送請求[RFC 9110 第 9.2.2 節](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.2)；管線化時，非冪等方法之後也不應該（SHOULD NOT）接著管線化其他請求[RFC 9112 第 9.3.2 節](https://www.rfc-editor.org/rfc/rfc9112.html#section-9.3.2)。

兩個常見追問：

*   「DELETE 第二次回 404 還算冪等嗎」：算，冪等看的是伺服器狀態（資源都不在了），不是回應碼要一樣。
*   「POST 怎麼做到冪等」：用冪等鍵（idempotency key，用戶端替每次操作產生的唯一編號，伺服器看過就不重做），這是應用層加上去的，不是 POST 本身的性質。

REST API 設計的 Spring 實作見〈Spring MVC 與 RESTful API〉。

> 💡 面試官：HTTP 快取的 Cache-Control、ETag、Last-Modified 與 304 怎麼配合？

**一句話定義**：快取分兩件事——「新鮮度」決定能不能不問伺服器直接用，「驗證」決定過期後能不能只問一句「有沒有變」就繼續用。回應新鮮時可以不經驗證直接重用；不新鮮時，若驗證能讓它重新變新鮮，仍可重用[RFC 9111 第 1 節](https://www.rfc-editor.org/rfc/rfc9111.html#section-1)。

*   **Cache-Control 管新鮮度：**`max-age=N`：回應的年齡超過 N 秒後視為過期[RFC 9111 §5.2.2.1](https://www.rfc-editor.org/rfc/rfc9111.html#section-5.2.2.1)；`no-cache`：未經驗證並取得成功回應前，不得（MUST NOT）用它滿足其他請求[RFC 9111 §5.2.2.4](https://www.rfc-editor.org/rfc/rfc9111.html#section-5.2.2.4)——可以存，但每次都要問；`no-store` 才是不得儲存請求或回應的任何部分[RFC 9111 §5.2.2.5](https://www.rfc-editor.org/rfc/rfc9111.html#section-5.2.2.5)；`private` 限單一使用者的快取（瀏覽器）存[RFC 9111 §5.2.2.7](https://www.rfc-editor.org/rfc/rfc9111.html#section-5.2.2.7)、`public` 允許共用快取（CDN、代理）存[RFC 9111 §5.2.2.9](https://www.rfc-editor.org/rfc/rfc9111.html#section-5.2.2.9)。
*   **ETag 與 Last-Modified 是驗證器**：ETag 是所選表述目前的實體標籤，一個不透明的版本識別[RFC 9110 §8.8.3](https://www.rfc-editor.org/rfc/rfc9110.html#section-8.8.3)；Last-Modified 是原始伺服器認為所選表述最後修改的日期時間[RFC 9110 §8.8.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-8.8.2)。
*   **304 是驗證成功的回答**：用戶端把 ETag 放進 `If-None-Match`[RFC 9110 §13.1.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-13.1.2)、把日期放進 `If-Modified-Since`[RFC 9110 §13.1.3](https://www.rfc-editor.org/rfc/rfc9110.html#section-13.1.3) 送條件式請求；沒變就回 304，快取更新並重用已儲存的回應[RFC 9111 §4.3.4](https://www.rfc-editor.org/rfc/rfc9111.html#section-4.3.4)，省掉整個內容的傳輸。

> no-cache 不是「不要快取」，是「每次用之前先問」；真的不准存是 no-store

*【API 風格】*

## REST 的約束，以及對 gRPC、GraphQL、SOAP 的取捨

> 💡 面試官：RESTful 的約束是什麼？

**一句話定義**：REST 是 Fielding 博士論文第 5 章定義的一組架構約束，不是「用 JSON 走 HTTP」的同義詞。六個約束：

*   **用戶端—伺服器分離**[§5.1.2](https://ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm#sec_5_1_2)。
*   **無狀態**：每個請求必須包含理解它所需的全部資訊，不能利用伺服器上儲存的任何脈絡，工作階段狀態因此完全放在用戶端[§5.1.3](https://ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm#sec_5_1_3)。
*   **可快取**[§5.1.4](https://ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm#sec_5_1_4)。
*   **統一介面**：由資源的識別、透過表述操作資源、自我描述的訊息、以超媒體作為應用狀態的引擎四個介面約束組成[§5.1.5](https://ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm#sec_5_1_5)。
*   **分層系統**：每個元件看不到它直接互動那一層以外的東西[§5.1.6](https://ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm#sec_5_1_6)。
*   **按需程式碼（選用）**：允許下載程式碼擴充用戶端[§5.1.7](https://ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm#sec_5_1_7)。

**面試怎麼答**：講「無狀態」時把它跟前面的冪等、安全方法、快取接起來——正因為每個請求自帶全部資訊，才能被任何一台伺服器處理、才能被中間的快取與代理理解（分層系統），這就是 REST 撐得起水平擴充的原因。追問「你們的 API 真的 RESTful 嗎」時誠實答：多數 API 做到資源、方法語意與無狀態，最後一個「超媒體作為應用狀態的引擎」（回應裡帶可用操作的連結）多半沒做。

> 💡 面試官：REST 對 gRPC 差在哪？什麼時候選 gRPC？

**一句話定義**：gRPC 是遠端程序呼叫框架：用戶端可以直接呼叫另一台機器上伺服器應用程式的方法，就像呼叫本地物件；protocol buffers 可以同時當介面定義語言（IDL）與訊息交換格式[gRPC 官方介紹](https://grpc.io/docs/what-is-grpc/introduction/#overview)。

|   | REST（HTTP＋JSON） | gRPC |
| --- | --- | --- |
| 契約 | URI＋方法＋文件（可用 OpenAPI 補上，那是描述 API 有哪些路徑、參數與回應的標準格式） | `.proto` 檔先定義服務與訊息，再產生各語言的程式碼 |
| 序列化 | 文字 JSON，人看得懂、除錯用瀏覽器就行 | protocol buffers 二進位，要工具才看得懂 |
| 傳輸 | HTTP 任一版本 | HTTP/2：一次 RPC 就是一條 HTTP/2 串流，訊息以 HTTP/2 資料訊框送出[gRPC 部落格](https://grpc.io/blog/grpc-on-http2/) |
| 串流 | 一問一答；要推送得另想辦法 | 四種方法：單次、伺服器串流、用戶端串流、雙向串流[gRPC 核心概念](https://grpc.io/docs/what-is-grpc/core-concepts/#rpc-life-cycle) |
| 逾時 | 各家自己約定 | 內建 deadline，超過回 DEADLINE_EXCEEDED[gRPC 核心概念](https://grpc.io/docs/what-is-grpc/core-concepts/#rpc-life-cycle) |
| 瀏覽器 | 原生支援 | 目前無法在瀏覽器實作 HTTP/2 版的 gRPC 規格，要靠 gRPC-Web 加一個必要的代理轉譯[gRPC 部落格](https://grpc.io/blog/state-of-grpc-web/) |

**什麼時候選 gRPC**：內部服務之間、呼叫量大或延遲敏感、需要串流（例如持續推送行情）、多語言團隊要一份契約產出所有語言的程式碼。對外給第三方或給瀏覽器直接用的 API 仍以 REST 為主，因為工具、快取與除錯體驗都是圍著 HTTP＋JSON 建的。

> 💡 面試官：REST 對 GraphQL？REST 對 SOAP？

**GraphQL**：給 API 用的查詢語言，加上一個用你定義的型別系統執行查詢的伺服器端執行環境[GraphQL 官方入門](https://graphql.org/learn/introduction/)。三個賣點：用型別系統描述 API、查你需要的剛剛好的資料（一次請求拿到期望形狀的資料，不必管背後是哪些資料來源）、不必版本化就能演進[GraphQL 官方入門](https://graphql.org/learn/introduction/#query-exactly-what-you-need)。

代價在 HTTP 那一層：GraphQL API 只有單一端點，請求用 POST 送出，查詢操作也可以用 GET。[GraphQL 官方文件](https://graphql.org/learn/serving-over-http/#api-endpoint) 預設都走同一個 URI 的 POST 時，前面講的 HTTP 快取（照 URI 存、用 304 驗證）用不上，查詢改用 GET 才能用[GraphQL 官方文件](https://graphql.org/learn/serving-over-http/#methods)；狀態碼也無法像 REST 那樣直接表達每筆資源的結果。

適合前端畫面多變、一頁要拼很多來源的場景；不適合把它當「REST 的升級版」。

**SOAP**：以 XML 為基礎的訊息格式，用來在去中心化的分散式環境裡，於對等節點之間交換結構化且有型別的資訊[SOAP 1.2 入門第 1.1 節](https://www.w3.org/TR/soap12-part0/#L1153)，訊息是一個 `Envelope` 包著 `Header` 與 `Body`[SOAP 1.2 入門第 2.1 節](https://www.w3.org/TR/soap12-part0/#L1165)。

跟 REST 的差別：SOAP 是一套訊息協定，操作寫在 XML 內文裡，HTTP 只是運送工具（所以全部 POST、全部 200 也不奇怪）；REST 是架構風格，操作靠 HTTP 方法與狀態碼表達。

面試答法不是「SOAP 過時」，而是「契約嚴格、有 WS-\*（WS-Security 這類在 SOAP 上加安全、交易等功能的一組規格）擴充，整合既有系統時會遇到；新做的服務用 REST 或 gRPC」。

*【瀏覽器這一端】*

## 從輸入網址到看到網頁、Cookie 與 CORS

> 💡 面試官：從輸入網址到看到網頁，中間發生什麼？

**怎麼答**：這題是串珠子，面試官在看你能不能把前面每一題按順序接起來，每一站講一句「在解決什麼問題」就好。骨架如下，每一站的細節見〈從輸入網址到看到網頁〉：

*   **解析 URL**：拆出協定、主機、埠、路徑；決定要不要加密。
*   **DNS 查詢**：把主機名換成 IP，先查瀏覽器與作業系統的快取，沒有才問遞迴解析器（替你一路問到權威伺服器的 DNS 伺服器，通常是網路業者或 8.8.8.8 這類公用服務）[MDN](https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/How_browsers_work#dns_lookup)。
*   **建立連線**：HTTP/1.1 與 HTTP/2 是 TCP 三向交握[MDN](https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/How_browsers_work#tcp_handshake)再 TLS 握手[MDN](https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/How_browsers_work#tls_negotiation)；HTTP/3 走 QUIC，一次握手把兩件事做完（見上面 HTTP 版本那題）。
*   **送請求、伺服器處理、回回應**：中間可能經過 CDN、反向代理（Nginx）、應用程式、資料庫；回應帶狀態碼與快取標頭。
*   **解析與渲染**：關鍵渲染路徑分成五步：把 HTML 解析成 DOM 樹、把 CSS 解析成 CSSOM 樹（CSS Object Model，樣式規則的樹狀物件）[MDN](https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/How_browsers_work#parsing)，兩棵樹合成渲染樹，算版面（layout），最後繪製（paint），有時再合成圖層[MDN](https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/How_browsers_work#render)。過程中遇到的圖片、腳本、樣式表再各自重跑一次上面的請求流程。

> 💡 面試官：Cookie 的 HttpOnly、Secure、SameSite 各擋什麼？

**一句話定義**：三個屬性分別管「誰能讀」「走什麼線送」「跨站時送不送」。

| 屬性 | 定義 | 擋的是什麼攻擊 |
| --- | --- | --- |
| HttpOnly | 禁止 JavaScript 存取這個 Cookie，例如透過 `Document.cookie`；但 Cookie 仍會隨 JavaScript 發起的請求（fetch、XMLHttpRequest）送出[MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie#httponly) | 減輕 XSS（跨站腳本）偷走工作階段 Cookie 的傷害——腳本讀不到，但擋不住腳本代替使用者送請求 |
| Secure | 只在請求使用 https: 協定時送給伺服器（localhost 例外）[MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie#secure) | 中間人在明文 HTTP 上攔截 Cookie |
| SameSite=Strict | 只在來自設定該 Cookie 的同一個網站的請求送出[MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie#samesitesamesite-value) | CSRF（跨站請求偽造）——別的網站發起的請求不帶你的 Cookie |
| SameSite=Lax | 同站送；跨站只在「頂層導覽」（網址列會變的那種）且「方法安全」（排除 POST、PUT、DELETE）時送；部分瀏覽器在沒指定 SameSite 時預設用 Lax[MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie#samesitesamesite-value) | 同上，但允許從別站點連結進來時仍保持登入 |
| SameSite=None | 同站跨站都送；用這個值時必須同時設定 Secure[MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie#samesitesamesite-value) | 不擋，給嵌在別站的第三方內容用 |

**追問：CORS 是誰在擋**？是瀏覽器。出於安全理由，瀏覽器限制腳本發起的跨來源 HTTP 請求：fetch 與 XMLHttpRequest 遵守同源政策，除非其他來源的回應帶了正確的 CORS 標頭[MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS)。

所以伺服器不是在「擋」，是在用 `Access-Control-Allow-Origin` 這類標頭「放行」；用 curl 或後端程式呼叫同一個 API 完全不受 CORS 影響，因為那裡沒有瀏覽器。

不符合「簡單請求」條件的跨來源請求（方法不是 GET／HEAD／POST、帶了 Authorization 這類安全清單以外的標頭，或 Content-Type 不是三種表單型別），瀏覽器會先送一個 OPTIONS「預檢」（preflight）請求，帶上實際請求會用的方法與標頭，確認伺服器允許[MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS#preflighted_requests)；判準是條件、不是會不會改狀態，所以帶 Authorization 的 GET 也會預檢，表單編碼的 POST 反而不會[MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS#simple_requests)。

Cookie 與 Session 的機制見〈Request、Response 與工作階段追蹤〉；CORS 在 Spring 怎麼設、CSRF 怎麼防見〈網站安全三題：CORS、CSRF、密碼學〉。

> HttpOnly 擋腳本讀、Secure 擋明文送、SameSite 擋跨站帶；CORS 是瀏覽器在擋、伺服器在放行

### 重點整理

*   分層題答「每層解決什麼問題」（IP 不保證送達、TCP 補可靠、HTTP 定語意）；三向交握是 SYN → SYN＋ACK → ACK，中間兩步合併成一包，主要理由是防舊的重複連線請求；關閉是四段 FIN／ACK，主動關閉方進 TIME_WAIT 等 2 倍 MSL（等最後的 ACK 有機會重送、讓舊區段死光；照 RFC 是 4 分鐘、Linux 是 60 秒），哪端主動關哪端就堆。
*   TLS 1.3 是 1-RTT 握手，ServerHello 之後全加密，拿掉靜態 RSA 換前向保密；0-RTT 不防重放、只放冪等請求；握手用非對稱（DH 換金鑰、憑證簽章驗身分），資料用對稱 AEAD。
*   HTTP/1.1 預設持久連線但有隊頭阻塞；HTTP/2 一連線多串流、偽標頭取代請求行，但 TCP 層阻塞沒解；HTTP/3 把多工交給 QUIC，串流各自重傳、握手合併。
*   401 缺身分驗證、403 有身分沒權限；301／302 可能被改成 GET，要保方法用 308／307；502 上游回壞東西、504 上游沒及時回；429 在 RFC 6585。
*   安全方法 GET／HEAD／OPTIONS／TRACE，冪等再加 PUT／DELETE；PATCH 不保證冪等；冪等的價值是能安全重試。Cookie 的 HttpOnly 擋腳本讀、Secure 只走 HTTPS、SameSite 管跨站帶不帶（None 必須配 Secure）；CORS 是瀏覽器擋、伺服器用標頭放行，不符合簡單請求條件才預檢，curl 不受影響。
*   no-cache 是先問再用，no-store 才是不准存；private 只給瀏覽器存、public 給 CDN 這類共用快取存；ETag／Last-Modified 配 If-None-Match／If-Modified-Since 換 304。
*   REST 六約束（無狀態、統一介面等）不等於 JSON over HTTP；gRPC 走 HTTP/2、protobuf、四種串流、瀏覽器要 gRPC-Web 代理；GraphQL 單一端點預設走 POST 時 HTTP 快取用不上，查詢改 GET 才能用；SOAP 是 XML 訊息協定。

## 隨堂測驗

**Q1. 面試官問「TCP 為什麼要三次交握，兩次不行嗎？」最準確的回答是？**

- (A) 雙方各要送一次自己的起始序號、各要收到一次確認，寫開是四步，第 2、3 步合併成 SYN＋ACK 才變三步；兩次的話伺服器的序號沒被確認，舊的重複 SYN 也會被誤當新連線
- (B) 第三次是用來傳送第一筆應用資料，沒有它連線就沒有內容
- (C) 兩次就夠了，第三次只是為了對稱好看，實作上可以省略
- (D) 三次是為了讓伺服器有時間分配記憶體，跟序號無關

<details><summary>看答案</summary>

**答案：(A)** 第 2、3 步可以合成一個訊息，所以叫三向交握；主要理由是防止舊的重複連線請求造成混亂。

</details>

**Q2. 一台伺服器上出現大量 TIME_WAIT 狀態的連線，下列哪個解讀是對的？**

- (A) 這台伺服器在主動關閉連線；每條要停 2 倍 MSL 等最後的 ACK 有機會重送、也讓舊區段死光，短連線一多就堆起來
- (B) 這是對方主動關閉留下的，伺服器自己沒辦法影響
- (C) TIME_WAIT 代表連線還在傳資料，只是暫時卡住
- (D) 這是三向交握失敗的殘留，重啟服務就會清掉

<details><summary>看答案</summary>

**答案：(A)** 主動關閉的一方必須在 TIME_WAIT 停留 2 倍 MSL；哪一端主動關、哪一端就堆 TIME_WAIT，解法是連線重用（持久連線、連線池）。

</details>

**Q3. 「DNS 標準查詢走 UDP、HTTP/3 走 QUIC 而 QUIC 跑在 UDP 上」，這兩個例子共同說明了什麼？**

- (A) UDP 不是不可靠的代名詞，而是把可靠性與延遲的決定權交給應用層自己補
- (B) UDP 其實也有三向交握，只是比 TCP 快
- (C) 任何協定只要夠新都會改用 UDP，TCP 正在被淘汰
- (D) UDP 保證順序但不保證送達，所以剛好適合查詢

<details><summary>看答案</summary>

**答案：(A)** UDP 不保證送達、也不保證不重複；DNS 自己做重傳、QUIC 自己做可靠性與壅塞控制，都是應用層決定要什麼程度的可靠。

</details>

**Q4. 關於 TLS 1.3 的 0-RTT 模式，面試時哪個說法是正確的？**

- (A) 0-RTT 資料不具前向保密、也不保證不被重放，所以只適合放冪等請求，扣款這類請求不能走 0-RTT
- (B) 0-RTT 跟一般握手安全性完全相同，只是省一趟來回
- (C) 0-RTT 是 TLS 1.2 就有的功能，1.3 只是改名
- (D) 0-RTT 靠伺服器的憑證加密，所以比 1-RTT 更安全

<details><summary>看答案</summary>

**答案：(A)** 0-RTT 資料不是前向保密的，也不保證跨連線不會被重放。

</details>

**Q5. HTTPS 的加密怎麼分工？**

- (A) 握手階段用非對稱（Diffie-Hellman 交換金鑰、憑證與簽章驗身分），之後的資料用握手算出的對稱金鑰以 AEAD 加密
- (B) 全程都用非對稱加密，因為對稱加密不夠安全
- (C) 全程都用對稱加密，憑證只是用來顯示網址列的鎖頭
- (D) 握手用對稱加密協商，之後改用 RSA 公鑰逐筆加密資料

<details><summary>看答案</summary>

**答案：(A)** TLS 分成握手協定與紀錄協定：握手建立共用金鑰與驗身分，紀錄協定用 AEAD 保護每一筆資料。

</details>

**Q6. HTTP/2 已經在一條連線上多工，為什麼還需要 HTTP/3？**

- (A) HTTP/2 的多工對 TCP 不可見，任何一個封包遺失都會讓整條連線的所有串流停擺；HTTP/3 改走 QUIC，串流各自重傳、互不阻塞
- (B) HTTP/2 不支援 TLS，HTTP/3 才把加密加進來
- (C) HTTP/2 只能同時處理一個請求，HTTP/3 才有多工
- (D) HTTP/3 改回文字格式，比較好除錯

<details><summary>看答案</summary>

**答案：(A)** HTTP/2 沒處理 TCP 的隊頭阻塞，一個遺失封包會讓所有交易停擺；QUIC 避免跨串流的隊頭阻塞。

</details>

**Q7. 使用者帶著有效的登入權杖呼叫一個他沒有權限的 API，伺服器應該回哪個狀態碼？**

- (A) 403 Forbidden——伺服器理解請求、知道他是誰，但拒絕執行
- (B) 401 Unauthorized——只要被拒絕就是 401
- (C) 404 Not Found——找不到他有權限的資源
- (D) 400 Bad Request——請求本身有問題

<details><summary>看答案</summary>

**答案：(A)** 401 是缺少有效的身分驗證憑據；403 是伺服器理解請求但拒絕執行，帶了憑據代表憑據不足以取得存取。

</details>

**Q8. 下列關於 HTTP 方法安全與冪等的敘述，哪個正確？**

- (A) PUT 與 DELETE 是冪等但不安全；GET、HEAD、OPTIONS、TRACE 既安全又冪等；POST 兩者皆非
- (B) POST 是冪等的，因為同一筆資料送兩次伺服器會自動去重
- (C) DELETE 第二次回 404，所以 DELETE 不是冪等的
- (D) PATCH 一定是冪等的，因為它只改部分欄位

<details><summary>看答案</summary>

**答案：(A)** 安全方法是 GET、HEAD、OPTIONS、TRACE，冪等再加 PUT、DELETE；冪等看的是伺服器狀態不是回應碼；PATCH 不保證冪等。

</details>

**Q9. 回應標頭寫 Cache-Control: no-cache，快取應該怎麼做？**

- (A) 可以儲存，但每次要用之前必須先向伺服器驗證（例如帶 If-None-Match 拿 304）才能用
- (B) 完全不能儲存請求或回應的任何部分
- (C) 可以直接重用到 max-age 到期
- (D) 只有瀏覽器能存，CDN 不能存

<details><summary>看答案</summary>

**答案：(A)** no-cache 是未經驗證不得用它滿足其他請求；真正不准儲存的是 no-store。

</details>

**Q10. 前端用 fetch 呼叫另一個網域的 API 被擋，後端同事用 curl 卻正常，為什麼？**

- (A) CORS 是瀏覽器在執行同源政策，伺服器只是用 Access-Control-Allow-Origin 放行；curl 沒有瀏覽器，不受 CORS 限制
- (B) 伺服器針對瀏覽器的 User-Agent 做了封鎖
- (C) curl 會自動帶上 CORS 標頭，所以能通過
- (D) fetch 預設走 HTTP/3，該 API 只支援 HTTP/1.1

<details><summary>看答案</summary>

**答案：(A)** 瀏覽器限制腳本發起的跨來源 HTTP 請求，除非回應帶了正確的 CORS 標頭；擋的一方是瀏覽器，不是伺服器。

</details>
