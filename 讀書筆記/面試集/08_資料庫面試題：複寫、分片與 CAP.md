# 08. 資料庫面試題：複寫、分片與 CAP

> 來源：[筆記平台 · 面試集](https://hhtim.github.io/notes-platform/interview/#/lesson/db-replication-sharding-cap)　第 8 課 / 共 23 課 · 約 14 分鐘

**主從複寫與半同步、讀寫分離的延遲、分片鍵與一致性雜湊、CAP 與 PACELC、BASE、連線池大小與資料庫四種壞法、冷熱分離與何時用 NoSQL——十一題以 MySQL 8.4 為準。**

### 讀完這課你會

*   講清 MySQL 複寫與複寫延遲
*   分清分割與分片、三種分片方式
*   把 CAP 講對
*   估連線池大小並排查常見故障

*【複寫】*

## binlog、三條執行緒與半同步

答題公式：一句話定義、取捨、版本註記。

> 💡 面試官：MySQL 主從複寫怎麼運作？非同步跟半同步差在哪？

**一句話定義**：複寫（replication）是把一台 MySQL（手冊叫 source，本課稱主庫）的資料變更，複製到一台或多台其他 MySQL（replica，本課稱複本）[出處](https://dev.mysql.com/doc/refman/8.4/en/replication.html)。主庫把每筆提交的變更記進二進位日誌（binary log，簡稱 binlog），複本拿去重放；8.4 預設用列格式（row-based），記「哪一列改成什麼」而不是 SQL 原句[出處](https://dev.mysql.com/doc/refman/8.4/en/replication-formats.html)。

**三條執行緒**：複本連上來時，主庫開一條 `Binlog Dump` 執行緒送 binlog；複本的接收執行緒（I/O receiver thread）把收到的內容寫進本機的中繼日誌（relay log，複本先抄下來、稍後再執行的那份日誌），套用執行緒（SQL applier thread）再讀中繼日誌、執行裡面的交易[出處](https://dev.mysql.com/doc/refman/8.4/en/replication-threads.html)。8.4 的套用端預設多執行緒：`replica_parallel_workers` 預設 4，由一條協調執行緒派工[出處](https://dev.mysql.com/doc/refman/8.4/en/replication-options-replica.html#sysvar_replica_parallel_workers)。

| 模式 | 主庫的提交何時回覆用戶端 | 代價 |
| --- | --- | --- |
| 非同步（預設） | 寫進自己的 binlog 就回覆；主庫不知道複本何時、甚至有沒有拿到這筆交易[出處](https://dev.mysql.com/doc/refman/8.4/en/replication-semisync.html) | 主庫當機時，還沒送出去的交易會丟 |
| 半同步 | 等到至少一台複本收到並寫進日誌才提交；只要求收到，不要求複本已執行完[出處](https://dev.mysql.com/doc/refman/8.4/en/replication-semisync.html) | 每筆提交多一趟網路來回 |

半同步是外掛，主庫裝 `rpl_semi_sync_source`、複本裝 `rpl_semi_sync_replica`，各自把 `_enabled` 設成 1[出處](https://dev.mysql.com/doc/refman/8.4/en/replication-semisync-installation.html)。

三個細節：

*   **逾時：**`rpl_semi_sync_source_timeout`（預設 10000 毫秒）內沒有複本回覆，主庫會**退回非同步**。
*   **等待點預設 `AFTER_SYNC`**：binlog 寫進磁碟後、提交進儲存引擎前就等複本。主庫上已提交的交易都已寫進複本的中繼日誌，所以主庫意外當機、由複本接手時不會丟交易。
*   **另一個值 `AFTER_COMMIT`**：先提交、再等複本回覆，代價有兩個。第一，提交之後、複本回覆之前，其他用戶端可能比發出提交的那個用戶端更早看到這筆交易。第二，複本若沒處理到這筆交易，主庫又意外當機而容錯移轉，用戶端可能發現資料比在主庫上看到的少。[出處](https://dev.mysql.com/doc/refman/8.4/en/replication-options-source.html#sysvar_rpl_semi_sync_source_wait_point)

```
-- 主庫（8.4.11 實跑）
INSTALL PLUGIN rpl_semi_sync_source SONAME 'semisync_source.so';
SHOW VARIABLES LIKE 'rpl_semi_sync%';
-- rpl_semi_sync_source_enabled                 OFF      ← 還要 SET GLOBAL ... = 1
-- rpl_semi_sync_source_timeout                 10000
-- rpl_semi_sync_source_wait_for_replica_count  1
-- rpl_semi_sync_source_wait_point              AFTER_SYNC
```

> 💡 面試官：複寫延遲會造成什麼問題？怎麼量？

**兩個問題：**

*   **讀到舊資料**：走複本的查詢看到的是幾秒前的世界。
*   **容錯移轉（failover，主庫壞了由複本接手）時丟交易**：複本還沒收到的交易就丟了。非同步下，主庫不知道複本何時、甚至有沒有拿到並處理這些交易，也不保證任何事件一定會到達任何一台複本。[出處](https://dev.mysql.com/doc/refman/8.4/en/replication-semisync.html) 已經寫進中繼日誌、只是還沒套用的交易，複本接手後仍會套用完。

**怎麼量**：在複本跑 `SHOW REPLICA STATUS`，看 `Seconds_Behind_Source`：複本正在套用的事件，其原始時間戳與複本現在時間的差。它量的其實是接收執行緒與套用執行緒之間的落差；網路慢時接收端本身就落後，這欄卻常顯示 0，所以只在快速網路上有用[出處](https://dev.mysql.com/doc/refman/8.4/en/show-replica-status.html)。

傳統複寫要複本記住讀到主庫哪個 binlog 檔的哪個位置；GTID（global transaction identifier，全域交易識別碼）給每筆交易一個 `server_uuid:序號` 的編號[出處](https://dev.mysql.com/doc/refman/8.4/en/replication-gtids-concepts.html)，換主庫或新增複本不必再對檔名與位置；同一個 GTID 在同一台伺服器上最多套用一次，重送不會重做[出處](https://dev.mysql.com/doc/refman/8.4/en/replication-gtids.html)。

*【讀寫分離】*

## 剛寫完讀不到，三種解法

> 💡 面試官：讀寫分離之後，使用者剛轉完帳、刷新頁面卻看不到那筆交易，怎麼處理？

**一句話定義**：讀寫分離是把寫入送主庫、讀取分散到複本。MySQL 不替你分流，要應用程式自己把所有寫入送到主庫、讀取送到主庫或複本[出處](https://dev.mysql.com/doc/refman/8.4/en/replication-solutions-scaleout.html)。預設非同步，寫完立刻去複本讀可能讀到舊狀態。三種解法由簡到繁：

*   **關鍵讀走主庫**：必須看到自己剛寫的結果的查詢（餘額、交易明細）固定送主庫，能忍受延遲的（月報表、歷史查詢）才走複本。最簡單，但主庫讀壓力減不掉多少。
*   **讀自己的寫**：寫入成功後幾秒內，同一位使用者的讀取都導回主庫，過了再放回複本。常見做法而非官方規範，門檻值用實測的複寫延遲來定。
*   **GTID 等待**：寫入後拿到主庫的 GTID 集合，到複本上呼叫 `WAIT_FOR_EXECUTED_GTID_SET(gtid_set, timeout)`：它等到複本套用完該集合內的所有交易才回傳 0，逾時回傳 1[出處](https://dev.mysql.com/doc/refman/8.4/en/gtid-functions.html)。等到了就在這台複本讀；逾時改走主庫。

```
-- 主庫：寫完後取得已執行的 GTID 集合（實跑）
SELECT @@gtid_executed;      -- b9e303eb-...:1-8
-- 複本：最多等 1 秒
SELECT WAIT_FOR_EXECUTED_GTID_SET('b9e303eb-bbd6-11f1-b1c4-dae0644808c0:1-8', 1);   -- 0
```

AWS 那邊：Aurora 的複本共用同一個叢集磁碟區，複寫延遲通常遠低於 100 毫秒，寫入量大時會拉長[出處](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.Replication.html)；RDS 的 Standby 對 Read Replica 見〈RDS 資料庫資源〉。

*【分片】*

## 垂直對水平、分片鍵、跨分片的三個難題

> 💡 面試官：垂直分割對水平分割？什麼時候該分片？

**一句話定義**：垂直分割（vertical partitioning）是把一張表的不同欄位拆開存；水平分割（horizontal partitioning）是把不同的列分到不同的實體分區。MySQL 的分割是水平分割，不支援垂直分割，目前也沒有引入的計畫[出處](https://dev.mysql.com/doc/refman/8.4/en/partitioning-overview.html)。分片（sharding）是把水平分割做到跨伺服器：同一張邏輯表的列散在多台獨立的資料庫上。

**什麼時候該分**：複寫只複製「同一份」資料，解決的是讀取量與可用性；單一主庫的**寫入**吞吐或**儲存容量**到頂時，複本再多也沒用，才輪到分片。代價見〈NoSQL 與資料庫設計〉那張表：分片鍵怎麼選、跨片查詢、重新平衡。順序是先索引、讀寫分離、冷資料歸檔（很少用的舊資料搬去便宜的地方存），最後才分片——這是常見做法而非官方規範。

> 💡 面試官：分片鍵怎麼選？範圍、雜湊、一致性雜湊各適合什麼？

| 分法 | 怎麼分 | 好處 | 壞處 |
| --- | --- | --- | --- |
| 按範圍 | 帳號 1〜100 萬第 1 片、100〜200 萬第 2 片；或按月份 | 範圍查詢只掃少數片 | 熱點：新帳號、本月交易全擠在最後一片 |
| 按雜湊 | 對鍵算雜湊值，取餘數決定放哪片 | 分布均勻 | 範圍查詢要掃全部片；加減機器時餘數全變，幾乎所有資料要搬 |
| 一致性雜湊 | 雜湊值空間當成一個環，節點與鍵都落在環上，鍵順時針找到第一個節點 | 加減節點只影響它在環上的鄰居，其他節點不受影響[出處](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf) | 節點在環上的位置隨機，資料與負載會不均，也不管機器效能有差 |

Dynamo 論文第 4.2 節對後兩個缺點的解法是**虛擬節點**（virtual nodes）：一台實體機器在環上佔多個位置，機器掛掉時它的負載平均散到剩下的機器，容量大的機器多佔幾個位置[出處](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf)。DynamoDB 也是按雜湊分割：把分割鍵（partition key）的值丟進內部雜湊函式，輸出決定項目存在哪個分割；加上排序鍵（sort key）後，同一個分割鍵的項目存在一起、按排序鍵排好[出處](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.CoreComponents.html)。

> 選分片鍵的第一原則：最常一起查的資料要落在同一片——帳務系統通常拿客戶編號，不拿交易編號

> 💡 面試官：跨分片的 JOIN、交易、全域唯一 ID 怎麼辦？

*   **JOIN**：資料庫做不了跨機器的 JOIN，只能靠設計避開，三個常見做法（非官方規範）——用同一個分片鍵讓客戶的帳戶與交易落在同一片；小而少變的表（幣別、分行代號）每片各放一份；真的要跨片就分兩次查、在應用程式裡合併。
*   **交易**：跨片沒有共同的 ACID 交易。能改設計就讓一筆業務只碰一片；改不了的走 Saga 加交易式 Outbox 加對帳，見面試集〈系統設計：訊息佇列與最終一致性〉。
*   **全域唯一 ID**：自動遞增在每片各自數，會撞號。三條路：號段模式（發號服務每次批發一段號碼，見面試集〈系統設計：短網址的高併發〉）；UUID（不撞，但插進叢集索引會亂跳，補救寫法見〈資料庫面試題：索引、交易隔離與鎖〉）；時間戳加機器編號加序號拼成 64 位元整數，大致遞增、不需中心發號（各家實作不同，沒有標準文件）。

*【CAP】*

## 分割是前提不是選項，平時取捨的是延遲

> 💡 面試官：CAP 定理到底說什麼？為什麼「三選二」是誤解？

**先講證明版**：Gilbert 與 Lynch 2002 年的證明把三個詞定義死：

*   **一致（atomic consistency）**：每個操作看起來像在某個瞬間一次完成，所有操作排成一個全序。
*   **可用（availability）**：每個沒故障的節點收到的每個請求，都必須得到回應。
*   **分割容忍（partition tolerance）**：允許網路丟掉任意多的訊息。[出處](https://users.ece.cmu.edu/~adrian/731-sp04/readings/GL-cap.pdf)

定理：在非同步網路模型中，不可能做出一個讀寫資料物件，在所有公平執行（包含訊息丟失的執行）中同時保證可用性與原子一致性[出處](https://users.ece.cmu.edu/~adrian/731-sp04/readings/GL-cap.pdf)。

證明骨架：網路斷成兩半，寫入落在一半、讀取落在另一半，要回應就只能回舊值，要回新值就只能不回應。

**再講為什麼三選二是誤解**：三選二過度簡化了三個性質之間的張力，CAP 的提出者 Brewer 2012 年也承認這個講法一直有誤導[出處](https://www.infoq.com/articles/cap-twelve-years-later-how-the-rules-have-changed/)。三點：

*   **P 不是選項**。你只能決定分割*發生時*保 C 還是保 A。分割很少發生，大多數時間 C 與 A 可以都完整，分割出現時才需要偵測並處理它的策略[出處](https://www.infoq.com/articles/cap-twelve-years-later-how-the-rules-have-changed/)。
*   **不是整個系統選一次**。C 與 A 之間的選擇可以在同一個系統裡做很多次、切得很細：子系統可以選不一樣，還可以依操作、甚至依特定資料或使用者而不同[出處](https://www.infoq.com/articles/cap-twelve-years-later-how-the-rules-have-changed/)。帳務餘額保 C、瀏覽紀錄保 A，就是兩個選擇。
*   **分割其實是延遲問題**。實務上，分割就是通訊等待的時間上限：等不到回覆時，要嘛取消操作（少了 A），要嘛硬做下去（賭 C）[出處](https://www.infoq.com/articles/cap-twelve-years-later-how-the-rules-have-changed/)。處理分割分三步：偵測分割開始、進入可能限制部分操作的分割模式、通訊恢復後啟動分割復原[出處](https://www.infoq.com/articles/cap-twelve-years-later-how-the-rules-have-changed/)。

**PACELC**：Abadi 2012 年提出的補完，把取捨分成兩種時候：

*   **發生分割（P）**：在可用性與一致性之間取捨（A 與 C）。
*   **否則（E），正常運作時**：在延遲（L）與一致性（C）之間取捨。[出處](https://www.cs.umd.edu/~abadi/papers/abadi-pacelc.pdf)

平時同步複寫多等一趟網路，就是用延遲換一致——CAP 沒講這一半。

分類：

*   **PA/EL**（分割時保可用、平時保低延遲）：Dynamo、Cassandra、Riak 的預設。
*   **PC/EC**：VoltDB、Megastore 這類完整 ACID 系統，不放棄一致性，願意付出可用性與延遲的代價。[出處](https://www.cs.umd.edu/~abadi/papers/abadi-pacelc.pdf)

半同步複寫的 MySQL 較接近 PA/EC：平時每筆提交多等一趟網路，換的是容錯移轉不丟交易，這是耐久性（durability，寫進去的資料不會因當機消失），不是 CAP 定義的一致性；逾時退回非同步、主庫照常提交，則是分割時選可用。PACELC 論文沒有點名 MySQL，這是常見的歸類，套的是論文對 MongoDB 的判準：MongoDB 屬 PA/EC，平時保證讀寫一致；主節點故障或與其餘部分斷開時，其餘節點另選新主節點繼續提供讀寫，舊主與新主的狀態於是不一致[出處](https://www.cs.umd.edu/~abadi/papers/abadi-pacelc.pdf)。

> 答 CAP 的順序：先講 P 是前提、再講分割時的 C 對 A、最後補一句平時是 L 對 C——三句話把三選二的版本蓋掉

> 💡 面試官：什麼是 BASE？

**一句話定義**：BASE 是基本可用（Basically Available）、軟狀態（Soft state）、最終一致（Eventually consistent）的縮寫：ACID 以一致性為重、是資料庫的傳統路線，BASE 是以高可用為重的設計取向[出處](https://www.infoq.com/articles/cap-twelve-years-later-how-the-rules-have-changed/)。

白話：一部分壞掉時其他部分照常服務；各副本某一刻可以不一樣；停止寫入後過一段時間會變成同一個值。

Dynamo 是課本例子：為了永遠可寫，在某些故障情境下犧牲一致性[出處](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf)。業務上怎麼解釋「暫時看不到」、哪些帳務不能最終一致，見面試集〈系統設計：訊息佇列與最終一致性〉。

*【連線池】*

## 為什麼要池、大小怎麼估

> 💡 面試官：資料庫連線池為什麼重要？大小怎麼估？

**一句話定義**：連線池（connection pool）是一塊快取區，讓資料庫連線在同一個應用程式內或跨應用程式重複使用，不必每次操作都新建再拆掉一條連線[出處](https://dev.mysql.com/doc/refman/8.4/en/glossary.html#glos_connection_pool)。

建連線要 TCP 交握、認證、配置執行緒，是毫秒級的固定成本；而且資料庫端連線數有上限——`max_connections` 預設 151[出處](https://dev.mysql.com/doc/refman/8.4/en/server-system-variables.html#sysvar_max_connections)，滿了之後新連線收到 `Too many connections`[出處](https://dev.mysql.com/doc/refman/8.4/en/too-many-connections.html)。

**大小**：HikariCP 給的起點公式是 `連線數 = 核心數 × 2 + 有效磁碟軸數`（磁碟軸 spindle，大致就是幾顆會轉的傳統硬碟），出自 PostgreSQL 專案，4 核心、一顆硬碟的機器大約 10 條[出處](https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing)。

核心數與磁碟數是**資料庫伺服器**的，不是應用程式的。前提：公式假設瓶頸是 CPU 與磁碟尋道，執行緒多過核心數只是增加切換成本；換成 SSD 沒有尋道與轉動延遲、阻塞更少，執行緒該*更少*（接近核心數）而不是更多[出處](https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing)。

公式還有兩個前提：

*   活躍資料集全部被快取住時，有效磁碟軸數是零；快取命中率越低，才越接近實際軸數。
*   這條公式在 SSD 上表現如何，目前還沒有人分析過。[出處](https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing)

核心觀念：池子要小，讓等待連線的執行緒排隊，而不是開一大堆連線[出處](https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing)。

**Spring Boot**：有 HikariCP 就用它（`spring-boot-starter-jdbc` 或 `data-jpa` 自帶），沒有才退到 Tomcat 池、Commons DBCP2、Oracle UCP；參數用 `spring.datasource.hikari.*` 前綴[出處](https://docs.spring.io/spring-boot/reference/data/sql.html)。

```
spring.datasource.hikari.maximum-pool-size=10
spring.datasource.hikari.connection-timeout=3000   # 等不到連線 3 秒就丟例外，不無限排隊
```

推理題：帳務服務 20 個執行個體（instance，同一個服務跑起來的一份程式）、每個池 10 條＝200 條長連線，超過預設的 151；調大 `max_connections` 或縮小池，都要算過再選。

*【壞法與冷資料】*

## 四種壞法怎麼發現、冷熱分離、什麼時候用 NoSQL

> 💡 面試官：資料庫常見的壞法——連線耗盡、鎖等待、磁碟滿、複寫斷掉，各怎麼發現？

| 壞法 | 症狀 | 去哪裡看 |
| --- | --- | --- |
| 連線耗盡 | 應用程式取不到連線、逾時；資料庫回 `Too many connections` | 狀態變數 `Max_used_connections`（啟動以來同時在用的最高數）與 `Connection_errors_max_connections`（因達上限被拒的次數）[出處](https://dev.mysql.com/doc/refman/8.4/en/server-status-variables.html#statvar_Max_used_connections)。伺服器另留一條給有 `CONNECTION_ADMIN` 權限的帳號，滿載時仍能連進去下 `SHOW PROCESSLIST`[出處](https://dev.mysql.com/doc/refman/8.4/en/too-many-connections.html) |
| 鎖等待 | 語句卡住，`innodb_lock_wait_timeout`（預設 50 秒）後報 `Lock wait timeout exceeded`[出處](https://dev.mysql.com/doc/refman/8.4/en/innodb-parameters.html#sysvar_innodb_lock_wait_timeout) | `sys.innodb_lock_waits` 檢視表：誰在等、等多久（`wait_age`）、被誰擋（`blocking_pid`），連 `KILL` 語句都拼好了[出處](https://dev.mysql.com/doc/refman/8.4/en/sys-innodb-lock-waits.html)；底層資料來自 `performance_schema.data_lock_waits`[出處](https://dev.mysql.com/doc/refman/8.4/en/performance-schema-data-lock-waits-table.html) |
| 磁碟滿 | binlog 寫滿時像卡住而不是報錯：MySQL 每分鐘檢查一次有沒有空間寫下一個事件，有了就繼續；每 10 分鐘往錯誤日誌寫一筆警告（手冊這段只講 MyISAM 表與 binlog）[出處](https://dev.mysql.com/doc/refman/8.4/en/full-disk.html)。InnoDB 表的資料檔寫滿則是另一種錯誤 `The table is full`，會直接報錯[出處](https://dev.mysql.com/doc/refman/8.4/en/table-size-limit.html) | 作業系統的磁碟監控；等資料庫報錯已太晚 |
| 複寫斷掉 | 複本資料停在某個時間點；`Seconds_Behind_Source` 變成 `NULL`（套用執行緒沒在跑）[出處](https://dev.mysql.com/doc/refman/8.4/en/show-replica-status.html) | `SHOW REPLICA STATUS` 的 `Replica_IO_Running` 與 `Replica_SQL_Running` 正常都該是 `Yes`[出處](https://dev.mysql.com/doc/refman/8.4/en/replication-administration-status.html)；停掉的原因在 `Last_IO_Error`／`Last_SQL_Error`[出處](https://dev.mysql.com/doc/refman/8.4/en/show-replica-status.html) |

> 四種壞法的共同答法：先講症狀，再講哪個指標要提前告警

> 💡 面試官：冷熱資料分離、歸檔怎麼做？

**一句話定義**：熱資料常被讀寫（近三個月的交易），冷資料很少碰但依法要留（幾年前的明細）；分離是熱的留在小而快的表、冷的搬去便宜的地方。MySQL 內建的工具是分割表，好處有兩個：失去用處的資料通常可以直接丟掉裝它的那個分區；以及分區修剪（partition pruning）——WHERE 條件只落在某些分區時，其他分區自動不掃[出處](https://dev.mysql.com/doc/refman/8.4/en/partitioning-overview.html)。

```
CREATE TABLE tx_log (id BIGINT NOT NULL, booked_on DATE NOT NULL, amount DECIMAL(15,2),
  PRIMARY KEY (id, booked_on))
PARTITION BY RANGE (YEAR(booked_on)) (
  PARTITION p2023 VALUES LESS THAN (2024), PARTITION p2024 VALUES LESS THAN (2025),
  PARTITION p2025 VALUES LESS THAN (2026), PARTITION pmax VALUES LESS THAN MAXVALUE);
EXPLAIN SELECT * FROM tx_log WHERE booked_on >= '2025-01-01' AND booked_on < '2026-01-01'\G
-- partitions: p2025            ← 只掃一個分區（實跑）
ALTER TABLE tx_log DROP PARTITION p2023;   -- 整年一次移除，不必逐列 DELETE
```

注意：丟掉分區的同時，也刪掉了那個分區裡的所有資料[出處](https://dev.mysql.com/doc/refman/8.4/en/partitioning-management-range-list.html)。所以先把該分區匯出到歸檔庫或物件儲存、核對筆數、才 DROP；報表與稽核查詢走歸檔庫或複本、不碰帳務主庫（常見安排，非官方規範）。DynamoDB 的對應物是存活時間（TTL）：替每個項目設到期時間戳，到期後 DynamoDB 會在幾天內自動刪除，不消耗寫入吞吐量[出處](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html)。

> 💡 面試官：什麼時候該用 NoSQL？

**一句話定義**：存取模式固定、以鍵查值為主、資料量與寫入量大到要橫向擴充，且不需要跨表 JOIN 與交易時，鍵值或文件型資料庫比關聯式划算；查詢多變、要複雜關聯與強一致交易的帳務核心，還是關聯式。完整判準見〈NoSQL 與資料庫設計〉。以 DynamoDB 為例，兩個要點：

*   **只有鍵有綱要**。除了主鍵之外，表沒有綱要；主鍵是分割鍵，或分割鍵加排序鍵[出處](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.CoreComponents.html)。所以先想清楚怎麼查再決定鍵，跟關聯式先建模、後想查詢的順序相反。
*   **預設最終一致讀**。讀取可能不反映剛完成的寫入；要最新資料就把 `ConsistentRead` 設成 true，但強一致讀只支援表與本地次要索引（local secondary index，跟表用同一個分割鍵、只換排序鍵的索引），全域次要索引（global secondary index，可以用另一組分割鍵與排序鍵）與串流只能最終一致；最終一致讀的價格是強一致讀的一半[出處](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadConsistency.html)——PACELC 的 L 對 C 變成每次讀都能選。

### 重點整理

*   MySQL 複寫靠 binlog 加三條執行緒（主庫 Binlog Dump、複本接收與套用），預設非同步、列格式、4 條套用工作執行緒。半同步等至少一台複本「收到並寫進日誌」，逾時退回非同步，等待點預設 AFTER_SYNC。
*   複寫延遲看 `Seconds_Behind_Source`，只在快速網路上準。「剛寫完讀不到」三招：關鍵讀走主庫、寫後一段時間讀主庫、複本上 `WAIT_FOR_EXECUTED_GTID_SET` 等到再讀。
*   複寫解讀取量與可用性，分片解寫入量與容量；MySQL 只有水平分割。範圍分法有熱點、雜湊分法怕加機器、一致性雜湊加虛擬節點。跨片 JOIN 靠同片設計，交易走 Saga，全域 ID 用號段、UUID 或時間戳拼接。
*   CAP：P 是前提，分割時才在 C 與 A 之間逐操作選；平時是 L 對 C（PACELC）。BASE 是基本可用、軟狀態、最終一致。
*   連線池起點是資料庫核心數 × 2 加磁碟軸數，前提是瓶頸在 CPU 與磁碟，SSD 要更少。總連線數＝執行個體數 × 池大小，對著 `max_connections`（預設 151）算。
*   四種壞法各有指標：`Connection_errors_max_connections`、`sys.innodb_lock_waits`、磁碟監控、`Replica_IO_Running`／`Replica_SQL_Running`。冷資料用 DROP PARTITION 或 DynamoDB TTL，先歸檔再刪。

## 隨堂測驗

**Q1. MySQL 8.4 預設的半同步複寫，主庫的提交要等到什麼條件才回覆用戶端？**

- (A) 至少一台複本回報「已收到並寫進日誌」，不要求複本已執行完那筆交易
- (B) 所有複本都執行完並提交該筆交易
- (C) 主庫把 binlog 寫到磁碟就回覆，不等任何複本
- (D) 至少一台複本執行完該筆交易並回報結果

<details><summary>看答案</summary>

**答案：(A)** 半同步只要求「收到並記錄」，不要求「執行完」；等所有複本提交是全同步，只等自己寫 binlog 是非同步。

</details>

**Q2. 帳務服務把餘額查詢送到複本，某位使用者轉帳成功後立刻刷新卻看不到扣款。哪個做法能「保證」這次讀到自己剛寫的結果？**

- (A) 在複本上先呼叫 WAIT_FOR_EXECUTED_GTID_SET 等到寫入的 GTID 已套用，再查；逾時就改走主庫
- (B) 查詢前先 sleep 一秒再讀複本，因為 Seconds_Behind_Source 通常小於一秒
- (C) 把複本的 replica_parallel_workers 調大，讓套用追上主庫
- (D) 在複本上執行 SHOW REPLICA STATUS 確認 Replica_SQL_Running 是 Yes 再查

<details><summary>看答案</summary>

**答案：(A)** 只有等到指定 GTID 集合套用完才讀，才是保證；固定等一秒是賭延遲，調工作執行緒與確認執行緒在跑都不保證那筆交易已到。

</details>

**Q3. Seconds_Behind_Source 只在快速網路上有用，原因是什麼？**

- (A) 它量的是複本內接收執行緒與套用執行緒的落差；網路慢時接收端本身落後，欄位卻常顯示 0
- (B) 它需要主庫與複本時鐘完全同步，跨機房時鐘差會讓值失準
- (C) 它只在單執行緒套用時有意義，多執行緒複本一律顯示 NULL
- (D) 慢速網路下主庫不會送出事件的時間戳，複本無法計算

<details><summary>看答案</summary>

**答案：(A)** 接收執行緒落後時，套用執行緒常常追上它，欄位就顯示 0，掩蓋了真正的落後。

</details>

**Q4. 某銀行系統把讀取全部分流到三台複本後，主庫的磁碟仍在半年內寫滿、寫入延遲持續升高。下一步最合理的是？**

- (A) 考慮分片：複寫只複製同一份資料，解決不了單一主庫的寫入量與容量上限
- (B) 再加三台複本，把讀取分得更散
- (C) 把非同步複寫改成半同步，降低主庫的寫入壓力
- (D) 在複本上建更多索引，加快查詢

<details><summary>看答案</summary>

**答案：(A)** 複本再多，每一筆寫入還是要在主庫落地一次；寫入吞吐與儲存到頂是分片才解得了的問題。

</details>

**Q5. 以「交易發生月份」當範圍分片鍵，最可能遇到什麼問題？**

- (A) 熱點：本月的所有新交易全落在同一片，其他片幾乎閒著
- (B) 加減機器時幾乎所有資料都要搬移
- (C) 無法做任何範圍查詢，因為月份沒有順序
- (D) 同一位客戶的交易被打散到每一片，無法一起查

<details><summary>看答案</summary>

**答案：(A)** 範圍分法的通病是新資料集中在最後一段；「加機器全搬」是取餘數雜湊分法的問題，同一客戶被打散則是拿交易編號做雜湊分法才會有的代價。

</details>

**Q6. 面試官問「CAP 是三選二，你們選哪兩個？」最準確的回答是？**

- (A) 分割不是選項而是前提；分割發生時才在一致與可用之間取捨，而且可以逐操作選；平時取捨的是延遲對一致
- (B) 選 CP，因為銀行系統一致性最重要，可用性可以犧牲
- (C) 選 CA，因為機房內網路很穩，不會發生分割
- (D) 選 AP，因為現代系統都用最終一致

<details><summary>看答案</summary>

**答案：(A)** 三選二的講法有誤導，CAP 提出者 Brewer 自己也承認：P 一定要面對，C 對 A 只在分割時發生且粒度很細，平時是 PACELC 裡的 L 對 C。

</details>

**Q7. 半同步複寫的 MySQL 平時等至少一台複本收到才提交，逾時則退回非同步、主庫照常提交。依 PACELC 分類，它最接近哪一類？為什麼？**

- (A) PA/EC：逾時退回非同步、主庫照常提交，是分割時選可用；平時每筆提交多等複本回覆，是拿延遲換一致
- (B) PC/EC：半同步在等不到複本時會停止提交以保住一致，和 VoltDB、Megastore 同一類
- (C) PA/EL：半同步預設不等複本，平時走的是低延遲
- (D) PC/EL：分割時停止提交保一致，平時不等複本走低延遲

<details><summary>看答案</summary>

**答案：(A)** 逾時退回非同步代表分割時主庫仍可寫（PA）；平時每筆提交多等複本回覆是拿延遲換一致（EC）。真正 PC/EC 的是 VoltDB、Megastore 這類等不到就不提交的系統；論文沒點名 MySQL，這是套它對 MongoDB 的判準。

</details>

**Q8. 資料庫伺服器 8 核心、一顆 SSD，帳務服務跑 20 個執行個體。照 HikariCP 的連線池公式與前提，下面哪個判斷正確？**

- (A) 公式起點約 17 條是給整台資料庫的，20 個執行個體各開 17 條會變成 340 條，遠超過 max_connections 預設的 151，要縮池或算過再調上限
- (B) 每個執行個體都應設 17 條，因為公式算的是每個應用程式該開幾條
- (C) SSD 很快，所以每個執行個體可以開到 50 條以上
- (D) 公式只適用於 PostgreSQL，MySQL 應改用一個使用者一條連線

<details><summary>看答案</summary>

**答案：(A)** 核心數與磁碟數都是資料庫端的，總連線數是執行個體數乘池大小；SSD 該用更少執行緒，公式出自 PostgreSQL 專案但適用於多數資料庫。

</details>

**Q9. 凌晨收到告警：複本上的報表資料停在昨晚十一點，SHOW REPLICA STATUS 的 Seconds_Behind_Source 顯示 NULL。最直接該看哪裡？**

- (A) Replica_IO_Running 與 Replica_SQL_Running 是否為 Yes，以及 Last_IO_Error／Last_SQL_Error 的錯誤訊息
- (B) 主庫的 max_connections 是否被用滿
- (C) performance_schema.data_lock_waits 有沒有鎖等待
- (D) 磁碟是否已滿，因為 NULL 代表磁碟滿

<details><summary>看答案</summary>

**答案：(A)** NULL 表示套用執行緒沒在跑（或中繼日誌耗盡且接收執行緒沒在跑），先看兩條執行緒狀態與最後一次錯誤；磁碟滿、鎖等待、連線滿各有自己的指標。

</details>
