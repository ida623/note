# 06. RDS 資料庫資源

> 🏠 **生活化版本**：每個段落開頭的「生活比喻」先用日常情境帶你抓到感覺，接著再看原本的技術說明與程式碼；篇末有「比喻對照表」可以快速複習。

> 來源：[筆記平台 · 雲端 AWS 與 GCP](https://hhtim.github.io/notes-platform/cloud/#/lesson/rds)　第 6 課 / 共 18 課 · 約 9 分鐘

**理解託管式關聯資料庫的備份、高可用、容錯移轉與讀取擴充架構。**

### 讀完這課你會

*   說出自己架資料庫和用 RDS 的責任差別
*   分清 Primary、Standby 與 Read Replica
*   知道 Multi-AZ 不等於備份、誤刪怎麼救

*【先決定自己要管多少】*

## EC2 自建資料庫與 RDS

> 🏠 **生活比喻**
>
> - EC2 自建＝**租空屋自己裝潢、自己修水電**
> - RDS＝**住飯店式公寓**，打掃、維修、備份都有人幫你做

在 EC2 上自己裝資料庫，像租下一間空屋後自己維護所有設備：AWS 提供底層運算資源，但作業系統修補、資料庫安裝與修補、備份、複寫和容錯移轉，多半得自己規劃。

RDS（Relational Database Service，關聯式資料庫服務）則像請物業代管重要設備。AWS 幫忙處理比較多例行工作，例如基礎設施維護、備份功能、資料庫軟體的維護選項，以及 Multi-AZ 容錯機制；使用者還是要負責資料模型、帳號權限、網路安全、參數設定、容量選擇與成本控管。

| 工作 | EC2 自建資料庫 | RDS |
| --- | --- | --- |
| 資料庫安裝與例行修補 | 自己處理 | 由服務提供管理機制 |
| 備份功能 | 自己設計與驗證 | 提供自動備份與 Snapshot |
| 高可用與容錯移轉 | 自己建置 | 可以使用 Multi-AZ 部署 |
| 資料與查詢設計 | 自己負責 | 仍由使用者負責 |
| 網路與存取權限 | 自己負責 | 仍由使用者負責 |

*【同樣是副本，任務不一樣】*

## Primary、Standby 與 Read Replica

> 🏠 **生活比喻**
>
> - Primary＝**主廚**，接所有點單
> - Standby＝**待命的副主廚**，平常不出菜，主廚倒下立刻接手
> - Read Replica＝**負責回答菜單問題的服務生**，分擔查詢

*   **Primary**：主要的資料庫執行個體，承接一般應用程式的讀寫流量。
*   **Standby**：Multi-AZ 架構中的備援副本，目的是高可用與容錯移轉，通常不拿來承接一般查詢。
*   **Read Replica**：用來分擔讀取流量的副本，通常透過非同步複寫取得資料，所以可能有複寫延遲。

> Standby 解決「主資料庫壞了怎麼辦」；Read Replica 解決「讀取流量太大怎麼辦」。

Read Replica 不該被當成完全即時的資料來源。應用程式寫入 Primary 之後馬上查 Read Replica，可能暫時看不到最新資料；需要「寫完立刻讀得到」的流程要謹慎選擇查詢端點。

*【跨可用區準備接班人】*

## Multi-AZ 與 Failover

> 🏠 **生活比喻**
>
> Multi-AZ 像**主廚和副主廚在不同分店待命**：一家停電，另一家的副主廚馬上接手（Failover），客人只需要重新撥號。

典型的 Multi-AZ 部署會把主要資料庫與備援資源放在不同 AZ。複寫方式依部署型態而不同，這兩個字是考點：**執行個體部署**（Multi-AZ DB instance）是**同步複寫**到另一個 AZ 的待命副本[出處](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZSingleStandby.html)；**叢集部署**（Multi-AZ DB cluster）則是**半同步複寫**，一筆變更只要至少一個讀取副本確認就算提交[出處](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/multi-az-db-clusters-concepts.html)。主要端故障或進行特定維護時，RDS 可以執行 Failover（容錯移轉），由備援端接手。

應用程式要用 RDS 給的 Endpoint（端點 DNS 名稱），不要把底層主機 IP 寫死。容錯移轉之後 AWS 會更新 DNS 指向新的主要端；應用程式仍然要能重新解析 DNS、重試連線，並處理短暫中斷。

```
平常：
應用程式 → RDS Endpoint → Primary
                         ↔ Standby（高可用複寫）

故障後：
應用程式 → 同一個 Endpoint → 新的 Primary
```

Multi-AZ 提升的是可用性，不等於備份。使用者誤刪資料時，這個錯誤也可能被複寫到備援端，所以備份與復原策略還是省不掉。

*【資料庫通常躲在內網】*

## Subnet Group 與 Security Group

> 🏠 **生活比喻**
>
> 資料庫放私有子網路，像**金庫放在大樓最裡面**；Security Group 是金庫門口的名單，只讓應用程式伺服器進來。

資料庫通常部署在私有子網路，避免直接暴露在網際網路上。DB Subnet Group 告訴 RDS 可以在哪些 Subnet 裡配置資料庫資源。

AWS 對 DB Subnet Group 的要求是：必須在同一 Region 的至少兩個可用區各有一個 Subnet，而且建議每個可用區都放一個[出處](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.WorkingWithRDSInstanceinaVPC.html)。重點不是「兩個 Subnet」這個數字，而是這些 Subnet 要分布在兩個以上的可用區，RDS 才有地方建新的備援端。

Security Group 只該放行真的需要連線的來源。例如讓應用程式 EC2 所屬的 Security Group 連到資料庫連接埠，就比開放給所有 IPv4 位址安全得多。

> 不要因為「先測通再說」就把資料庫連接埠開給 0.0.0.0/0；那等於把門對整個網際網路打開。

```
管理者
→ 經受控方式登入應用程式或管理主機
→ 使用資料庫用戶端
→ RDS Endpoint
→ RDS 的 Security Group 驗證來源
→ Primary Database
```

*【備份有兩種時間尺度】*

## 自動備份、時間點復原與 Snapshot

> 🏠 **生活比喻**
>
> - 自動備份＋時間點復原＝**行車紀錄器**，可以倒轉到某一秒
> - Snapshot＝**手動拍的紀念照**，你刪掉前都會留著

RDS 的自動備份會搭配儲存磁碟快照與資料庫交易日誌（Transaction Log），支援在保留期間內做時間點復原（Point-in-Time Recovery）。復原時通常不是把原資料庫直接倒轉，而是建立一個新的資料庫執行個體。

手動 DB Snapshot 是由使用者主動建立的復原點。從 Snapshot 復原時，同樣會產生新的資料庫執行個體，再由你去檢查資料、網路與參數設定。

| 方式 | 適用需求 | 復原結果 |
| --- | --- | --- |
| 時間點復原 | 回到保留期間內比較精確的某個時間 | 建立新的資料庫執行個體 |
| 手動 Snapshot | 保留明確的里程碑或長期復原點 | 由 Snapshot 建立新的資料庫執行個體 |
| Multi-AZ Standby | 主要端故障時快速接手 | 執行容錯移轉，救不回誤刪的資料 |

自動備份跑的是兩個不同的時間尺度。快照是一天一次：RDS 會在你指定的備份時段，自動對資料做一次完整的每日快照[出處](https://aws.amazon.com/rds/faqs/)。交易日誌則細得多，RDS 每五分鐘把交易日誌上傳到 S3 一次[出處](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PIT.html)。這也是為什麼時間點復原能回到的最近時間，通常落在最近五分鐘之內，而不是退回到昨天的快照。能回到多久以前則看保留期間；確切的最近可復原時間，在主控台的「自動備份」頁看得到。

*【讀取壓力大，就把讀分出去】*

## Read Replica 怎麼用

> 🏠 **生活比喻**
>
> 讀取量太大時，多請幾位**服務生回答問題**（Read Replica），主廚專心出菜；但服務生的資訊可能**慢一點點**（複寫延遲）。

工作負載主要卡在讀取時，可以建立 Read Replica，讓報表、查詢或其他能接受短暫延遲的流量走副本端點。寫入仍然要送往可寫的主要資料庫。

```
寫入請求 ───────────────→ Primary
                         │
                         └─ 非同步複寫 → Read Replica
讀取請求（可接受延遲）────────────────→ Read Replica
```

建了副本不會讓應用程式自動把查詢分流。應用程式、資料存取層或中介服務還是要知道哪些查詢可以走副本，並處理複寫延遲與副本暫時不可用的情況。

*【從 EC2 驗證資料庫連線】*

## 基本操作流程

> 🏠 **生活比喻**
>
> 像**開一家餐廳的步驟**：選店址（VPC、子網路）→ 設門禁 → 請主廚（建 RDS）→ 讓外場連得到廚房（應用程式連線）→ 定期備份。

1.  建立 VPC、私有子網路，以及符合部署需求的 DB Subnet Group。
2.  建立 RDS，把 Security Group 限制成只允許應用程式或管理來源。
3.  在能安全連到 RDS 的主機上，安裝相容的資料庫用戶端。
4.  用 RDS Endpoint、資料庫帳號與密碼連線。
5.  建立測試資料，再驗證 Snapshot、時間點復原與 Read Replica 的行為。

```
# 套件名稱依作業系統版本與套件庫而異
sudo dnf install -y mariadb105

# 連接 MySQL 相容的 RDS
mysql -u admin -p -h <rds-endpoint>

SHOW DATABASES;
```

不要把資料庫密碼直接寫進指令稿、AMI 或版本庫；正式環境要用適當的祕密管理方式保存。

### 🗺️ 比喻對照表

| 技術名詞 | 生活比喻 |
| --- | --- |
| 自建 vs RDS | 自己修水電 vs 飯店式公寓 |
| Primary / Standby | 主廚 / 待命副主廚 |
| Read Replica | 回答問題的服務生 |
| Failover | 副主廚接手 |
| 時間點復原 | 行車紀錄器倒轉 |

### 重點整理

*   RDS 減少基礎設施維護工作，但資料、權限與網路安全仍由使用者負責。
*   Standby 是為了高可用；Read Replica 是為了分擔讀取。
*   Read Replica 通常有複寫延遲，不能假設寫完立刻讀得到。
*   應用程式要連 RDS Endpoint，並具備重新連線與重試的能力。
*   Multi-AZ 不是備份；誤刪要靠自動備份或 Snapshot 救回來。

## 隨堂測驗

**Q1. 改用 RDS 之後，哪一項通常仍然是使用者的責任？**

- (A) 設計資料表、帳號權限與網路存取規則
- (B) 更換承載服務的實體伺服器
- (C) 修補底層虛擬化平台的作業系統
- (D) 維護 AWS 資料中心的電力與冷卻

<details><summary>看答案</summary>

**答案：(A)** RDS 接手的是基礎設施與例行維運，資料模型與存取控制還是使用者自己的事。

</details>

**Q2. 資料庫主要端故障時，希望另一個可用區的資源接手服務，應該優先考慮什麼？**

- (A) Multi-AZ 部署與 Standby 容錯移轉
- (B) 只建立 Read Replica，假設它會自動接管寫入
- (C) 把最近的 Snapshot 設為公開共享
- (D) 把 DB Subnet Group 縮成單一 Subnet

<details><summary>看答案</summary>

**答案：(A)** Read Replica 是分擔讀取用的，接手寫入服務靠的是 Multi-AZ 的容錯移轉。

</details>

**Q3. 查詢流量過大，而且部分查詢可以接受短暫的資料延遲，哪個功能最適合分擔？**

- (A) Read Replica
- (B) Multi-AZ Standby
- (C) 手動 DB Snapshot
- (D) 時間點復原

<details><summary>看答案</summary>

**答案：(A)** Standby 平常不承接查詢；Snapshot 與時間點復原是備份手段，不解決流量問題。

</details>

**Q4. 為什麼寫入之後立刻查詢 Read Replica，可能看不到最新資料？**

- (A) Primary 到 Read Replica 通常是非同步複寫，可能有延遲
- (B) Read Replica 本身沒有任何儲存空間
- (C) Read Replica 每天只同步一次
- (D) RDS Endpoint 會把查詢隨機丟給任一副本

<details><summary>看答案</summary>

**答案：(A)** 非同步複寫表示主端寫完就回應，副本稍後才追上，所以會有一小段落差。

</details>

**Q5. 應用程式連線 RDS 時，為什麼應該用 Endpoint 而不是寫死底層主機 IP？**

- (A) 容錯移轉後 DNS 可以指向新的主要端，應用程式不必改設定
- (B) Endpoint 可以省掉資料庫帳號密碼驗證
- (C) Endpoint 會自動把所有查詢改寫成唯讀
- (D) Endpoint 可以取代 Security Group 的來源限制

<details><summary>看答案</summary>

**答案：(A)** Endpoint 是一層 DNS 名稱，讓底層主機換人時應用程式不用跟著改。

</details>

**Q6. 團隊誤刪一批資料，Multi-AZ Standby 也同步收到了刪除，最合理的復原方式是什麼？**

- (A) 用時間點復原或合適的 Snapshot 建立新的資料庫
- (B) 等 Standby 自動把刪除動作取消掉
- (C) 把 Read Replica 提升為主要端就能救回
- (D) 重新執行一次容錯移轉

<details><summary>看答案</summary>

**答案：(A)** 複寫會忠實地把誤刪帶過去，能回到刪除前的只有備份類機制。

</details>

**Q7. 資料庫 Security Group 的來源設定，哪個做法比較安全？**

- (A) 只允許應用程式的 Security Group 或受控管理來源連線
- (B) 為了方便，長期允許所有 IPv4 位址連入
- (C) 改用預設的 Network ACL 放行所有流量
- (D) 把資料庫改放到公開子網路並開啟公有存取

<details><summary>看答案</summary>

**答案：(A)** 把來源限制在真正需要連線的對象，是資料庫最基本的防線。

</details>

**Q8. 從 RDS Snapshot 執行復原時，通常會得到什麼？**

- (A) 一個由 Snapshot 建立出來的新資料庫執行個體
- (B) 原資料庫在原地被直接倒轉回去
- (C) 一顆可以直接掛到 EC2 上的 EBS Volume
- (D) 一份自動套用到 Read Replica 的設定

<details><summary>看答案</summary>

**答案：(A)** RDS 的還原是「開一台新的」，所以還原後要自行檢查資料、網路與參數設定。

</details>
