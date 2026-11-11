# 03. VPC 網路架構

> 🏠 **生活化版本**：每個段落開頭的「生活比喻」先用日常情境帶你抓到感覺，接著再看原本的技術說明與程式碼；篇末有「比喻對照表」可以快速複習。

> 來源：[筆記平台 · 雲端 AWS 與 GCP](https://hhtim.github.io/notes-platform/cloud/#/lesson/vpc)　第 3 課 / 共 18 課 · 約 12 分鐘

**看懂 VPC、子網路、路由表與兩種安全規則如何一起引導並保護流量，並分清楚兩種閘道各自怎麼轉換位址。**

### 讀完這課你會

*   分清區域、可用區、VPC 與子網路的包含關係
*   判斷子網路算公開還是私有
*   分清 Security Group 與 Network ACL
*   說出 Internet Gateway 與 NAT Gateway 的差別

*【先建立空間感】*

## 從地理區域一路縮小到子網路

> 🏠 **生活比喻**
>
> AWS 網路像一座城市：Region 是城市、AZ 是行政區、**VPC 是你圍起來的社區**、**Subnet 是社區裡的一條條巷子**。

可以把 AWS 的網路想成一座城市：Region（區域）是城市所在的地理範圍，Availability Zone（可用區，AZ）是彼此隔離的基礎設施區域，VPC（虛擬私有雲）是你在城市裡圈出來的私人園區，Subnet（子網路）則是園區裡的分區。

| 層級 | 白話比喻 | 重點 |
| --- | --- | --- |
| Region | 一座城市所在的地理範圍 | AWS 資源所屬的區域 |
| Availability Zone | 彼此隔離的基礎設施區域 | 一個 Region 內有多個 AZ（至少三個） |
| VPC | 私人園區 | 由你自己規劃的虛擬網路邊界 |
| Subnet | 園區內的分區 | 每個 Subnet 只屬於單一 AZ |

高可用（High Availability，HA）的常見做法，是把同一套服務分散部署到不同 AZ。這樣單一 AZ 出事時，其他 AZ 還有機會繼續提供服務。

*【道路決定去向】*

## Route Table 與公開、私有子網路

> 🏠 **生活比喻**
>
> Route Table 是**路標**，只告訴你往哪走，不管准不准過。
> - 公開子網路＝巷口路標寫「往**大門**（Internet Gateway）」
> - 私有子網路＝巷子沒有直通大門的路標

Route Table（路由表）像路標：它不負責准不准過，只決定封包下一站往哪走。每個 Subnet 都會關聯一張路由表，多個 Subnet 也可以共用同一張。

同一個 VPC 內通常有一條本地路由（local route），所以不同 Subnet 的資源可以透過 VPC 的路由功能互通；但流量還是要通過相關的安全規則才算過關。

*   **公開子網路（Public Subnet）**：它的路由表有一條通往 Internet Gateway 的路由。EC2 要直接跟網際網路來往，通常還需要公有 IPv4 位址或 Elastic IP（你先向 AWS 要下來、可以搬到別台機器上的固定公有位址），以及放行的安全規則。
*   **私有子網路（Private Subnet）**：沒有讓執行個體直接經由 Internet Gateway 對外通訊的路由。需要主動連外時，可以把預設路由指向放在公開子網路裡的 NAT Gateway（NAT＝Network Address Translation，網路位址轉換：出去的時候把來源換成公有位址，回來的時候再換回私有位址）。

> 公開子網路 ≠ 裡面的資源自動公開；路由、公有位址與安全規則，三個缺一不可。

*【三條常見流量路徑】*

## 封包實際上怎麼走

> 🏠 **生活比喻**
>
> 封包像**送信**：先看路標決定下一站，經過每一道門都要檢查，最後才到收件人手上。

下面三張圖裡會一直出現 ENI（Elastic Network Interface，彈性網路介面），它就是掛在 EC2 上的虛擬網卡。

> 💡 情境一：同一個 VPC 內，兩個私有子網路怎麼互通？

```
來源 EC2
→ 來源 ENI 的 Security Group 出站檢查
→ 來源 Subnet 的 Network ACL 出站檢查
→ 路由表的 local 路由
→ VPC 路由功能
→ 目的 Subnet 的 Network ACL 入站檢查
→ 目的 ENI 的 Security Group 入站檢查
→ 目的 EC2
```

> 💡 情境二：公開子網路中的 EC2 怎麼連到網際網路？

```
有公有位址的 EC2
→ ENI
→ Security Group 與 Network ACL
→ 路由表：預設路由指向 Internet Gateway
→ Internet Gateway
→ 網際網路
```

> 💡 情境三：私有子網路中的 EC2 怎麼主動連外？

```
私有 EC2
→ 私有 Subnet 的安全檢查與路由表
→ NAT Gateway（位於公開 Subnet）
→ 公開 Subnet 的路由表
→ Internet Gateway
→ 網際網路
```

NAT Gateway 會把來源的私有位址換成它對外使用的位址（來源網路位址轉換，SNAT），並記住連線狀態。它是讓私有資源「主動連出去」用的，不等於允許網際網路任意主動連進來。

*【兩種位址轉換】*

## Internet Gateway 做的也是 NAT，只是一對一

> 🏠 **生活比喻**
>
> Internet Gateway 像**社區大門的門牌對照**：對外寫「XX 路 100 號」（公有 IP），進門再轉成「社區 3 號房」（私有 IP），一戶對一個門牌。

情境二有個地方值得停下來想：EC2 的作業系統裡其實看不到自己的公有 IP。你登進去查它的網路設定（Linux 上就是 `ip addr` 這個指令），看到的只會是 VPC 配給它的私有位址。那外面的人是怎麼連到它的？答案是 Internet Gateway 一路在替它換位址。

Internet Gateway 在邏輯上替你的執行個體做一對一的 NAT：

*   出去：流量離開 VPC 子網路前往網際網路時，回覆位址欄位被設成該執行個體的公有 IPv4 位址或 Elastic IP 位址，而不是它的私有 IP 位址
*   進來：送往那個公有位址的流量，會先被轉換成執行個體的私有 IPv4 位址，才被送進 VPC[出處](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Internet_Gateway.html)

「一對一」是指一個私有位址固定配一個公有位址，兩邊像門牌與郵政信箱一樣一對一掛勾。NAT Gateway 就不是這樣，它是多對一：一整批私有 EC2 共用它那一個對外位址出去。這個差別直接決定了「外面連不連得進來」。

| 比較項目 | Internet Gateway | NAT Gateway |
| --- | --- | --- |
| 位址對應 | 一對一：一個私有位址對一個公有位址 | 多對一：多台私有 EC2 共用對外位址 |
| EC2 自己要有公有位址嗎 | 要，公有 IPv4 或 Elastic IP | 不用 |
| 連線方向 | 內對外、外對內都可以 | 只能由內主動往外 |
| 擺在哪裡 | 掛在 VPC 上 | 建在公開子網路裡 |

這段講的是 IPv4。IPv6 沒有這回事：IPv6 位址是全球唯一的，所以預設就是公有的。要對外通訊是讓 VPC 與子網路關聯一段 IPv6 位址範圍（CIDR 區塊，用「起始位址／斜線數字」寫成的一段連續位址）、並指派 IPv6 位址給執行個體，不經過這種位址轉換[出處](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Internet_Gateway.html)。

*【網卡才是網路身分】*

## ENI、EC2 與 Security Group 的關係

> 🏠 **生活比喻**
>
> ENI 是房子的**門**，EC2 是**房子**，Security Group 是**裝在門上的門禁**；門禁跟著門走，不是跟著房子。

ENI（Elastic Network Interface，彈性網路介面）就是虛擬網卡。EC2 是運算資源，它透過掛上 ENI 才取得私有 IP、所屬 Subnet 這些網路身分。

Security Group（安全群組）是 VPC 層級的資源，關聯的對象是 ENI，不是「住在某個 Subnet 裡」[出處](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html)。規則是跟著網卡走的，Security groups 本身就是網路介面的屬性之一[出處](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-eni.html)。

> 📝 查證更正：原筆記的條列寫「EC2 外面包了 SG」「SG 在某一個 Subnet 裡面」，查證後更正：Security Group 是 VPC 層級的資源，關聯的對象是 ENI，不隸屬於某個 Subnet。原筆記下一段其實自己就補了「SG 其實是跟著 ENI 走的」，但那條錯的條列沒有收回，所以這裡講清楚

在條件允許時，ENI 可以從一台 EC2 卸下來，再掛到另一台 EC2。這樣就能保留部分網路設定，只換掉背後的運算資源。

*【兩道不同的門禁】*

## Security Group 與 Network ACL

> 🏠 **生活比喻**
>
> - Security Group＝**住戶自家門禁**，有記憶：讓你出去了，你回來就自動放行（有狀態）
> - Network ACL＝**巷口警衛**，沒記憶：進來出去都要各查一次（無狀態）

| 比較項目 | Security Group | Network ACL |
| --- | --- | --- |
| 保護範圍 | ENI（資源層級） | Subnet 邊界 |
| 規則種類 | 只有允許規則 | 允許與拒絕規則都有 |
| 狀態 | 有狀態（Stateful） | 無狀態（Stateless） |
| 回程流量 | 已允許連線的回應可自動通過 | 入站、出站都要分別允許 |
| 評估方式 | 綜合所有適用的規則 | 依規則編號由小到大比對 |

Network ACL 是無狀態的，所以跨 Subnet 邊界時，要分別想來源端的出站規則與目的端的入站規則，回程流量也必須有對應規則才通得過。

Network ACL 的預設值也要分兩種，而且方向剛好相反。VPC 附的那個預設 Network ACL 是進出全放；**你自己新建**的 Network ACL 則是什麼都不通：

*   每個 Network ACL 都有一條預設入站規則與一條預設出站規則，規則編號是星號（`*`），封包不符合其他任何規則就會被拒絕
*   規則編號為星號的規則刪不掉[出處](https://docs.aws.amazon.com/vpc/latest/userguide/custom-network-acl.html)

所以自訂一個之後要自己把該放的流量一條條加回去，判讀現有環境時直接去看實際規則，不要靠印象。

Security Group 的預設值則可以記成一句話：**進來全拒、出去全放**。剛建立的安全群組：

*   沒有任何入站規則，所以在你加入入站規則之前，不允許任何入站流量
*   有一條出站規則，允許該資源所有出站流量[出處](https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html)

這解釋了一個常見現象：剛開好的 EC2 從外面連不進去（沒有入站規則），但機器自己連得出去、抓得到系統更新（出站全放）。要收緊出站也做得到：安全群組沒有出站規則時，就不允許任何出站流量。

「進來全拒」這句要綁在**自己新建的**安全群組上。每個 VPC 都附一個名叫 default 的預設安全群組，它不一樣：它預設就帶一條入站規則，來源寫的是這個安全群組自己，效果是「掛著同一個安全群組的資源彼此可以互通」；出站則是全放的 IPv4 一條；只有在 VPC 有關聯 IPv6 CIDR 區塊時，才會再多一條 IPv6 的。建議別用它，改為特定資源或資源群組自己建安全群組[出處](https://docs.aws.amazon.com/vpc/latest/userguide/default-security-group.html)。

*【建置順序】*

## 建立一個可以直接連外的基本網路

> 🏠 **生活比喻**
>
> 像**蓋一個小社區**：圈地（VPC）→ 劃巷子（Subnet）→ 裝大門（IGW）→ 立路標（Route Table）→ 裝門禁（SG）→ 蓋房子（EC2）。

1.  建立 VPC，並規劃 CIDR（位址範圍。這個斜線寫法怎麼讀、一段範圍能切出幾個位址、每個子網路又會先被拿走幾個，見〈GCP 網路位址與子網路〉）。

2.  在指定的 AZ 建立 Subnet。

3.  建立 Internet Gateway，掛載到 VPC——掛載對象是 VPC，不是 Subnet[出處](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Internet_Gateway.html)；而且一個 VPC 同時只能掛一個[出處](https://docs.aws.amazon.com/vpc/latest/userguide/amazon-vpc-limits.html)。

    > 📝 查證更正：原筆記的建置步驟寫「創建 IGW，並且將它 Attach to VPC(剛剛創立的 Public Subnet)」——前半句對、括號裡寫成 Subnet，前後矛盾。查證後更正：Internet Gateway 是掛載到 VPC，一個 VPC 只能掛一個；Subnet 是靠路由表指向它才連得出去，不是掛載對象

4.  在公開 Subnet 關聯的路由表中，加一條指向 Internet Gateway 的預設路由。

5.  建立 EC2 放進該 Subnet，配置需要的公有位址與安全規則。

> 一個 Subnet 算不算公開，主要看它關聯的路由表能不能把網際網路流量送到 Internet Gateway。

### 🗺️ 比喻對照表

| 技術名詞 | 生活比喻 |
| --- | --- |
| VPC / Subnet | 社區 / 巷子 |
| Route Table | 路標 |
| Internet Gateway | 社區大門 |
| ENI | 房子的門 |
| Security Group | 自家門禁（有記憶） |
| Network ACL | 巷口警衛（沒記憶） |

### 重點整理

*   Subnet 只位於單一 AZ；跨 AZ 部署是提高可用性的常見做法。
*   Route Table 決定下一站怎麼走，Security Group 與 Network ACL 決定流量過不過得去。
*   Internet Gateway 讓公開資源連外；NAT Gateway 讓私有資源主動連外。
*   Security Group 有狀態、只有允許規則；Network ACL 無狀態，而且可以明確拒絕。
*   Security Group 關聯在 ENI 上，EC2 是透過 ENI 取得網路身分的。
*   新建的 Security Group 預設進來全拒、出去全放；VPC 附的那個 default 安全群組則多一條「同群組互通」的入站規則。
*   Internet Gateway 做的是一對一的位址轉換，NAT Gateway 是多對一——所以只有前者外面連得進來。

## 隨堂測驗

**Q1. 某個 Subnet 要成為公開子網路，最關鍵的路由條件是什麼？**

- (A) 它關聯的路由表有一條指向 Internet Gateway 的預設路由
- (B) Subnet 裡至少放了一台 EC2
- (C) Subnet 關聯了一個 Security Group
- (D) Subnet 與另一個私有 Subnet 共用同一張路由表

<details><summary>看答案</summary>

**答案：(A)** 公不公開由路由決定；有沒有 EC2、掛哪個安全群組都不影響這個判斷。

</details>

**Q2. 私有子網路的 EC2 只需要主動下載更新，不希望被網際網路直接連進來，適合走哪條路？**

- (A) 經 NAT Gateway 再通過 Internet Gateway 連外
- (B) 把私有 IP 直接交給 Internet Gateway 對外
- (C) 只加 Security Group 的出站規則，不動路由表
- (D) 把該 Subnet 的 Network ACL 全部改成允許

<details><summary>看答案</summary>

**答案：(A)** NAT Gateway 做來源位址轉換並記住連線狀態，讓私有資源能出去、外面進不來。

</details>

**Q3. 為什麼 Network ACL 的回程流量也需要規則？**

- (A) 因為 Network ACL 是無狀態的，入站與出站要分開評估
- (B) 因為 Network ACL 只能設定拒絕規則
- (C) 因為 Network ACL 只作用在 Internet Gateway 上
- (D) 因為 Network ACL 會忽略來源 Subnet 的設定

<details><summary>看答案</summary>

**答案：(A)** 無狀態表示它不記得去程連線，所以回來的流量要另外有規則放行。

</details>

**Q4. 關於 Security Group 與 ENI，哪個敘述最精確？**

- (A) Security Group 關聯到 ENI，EC2 透過 ENI 取得網路身分
- (B) Security Group 是建立在單一 Subnet 裡面的資源
- (C) ENI 只負責掛載儲存空間，與網路位址無關
- (D) 一個 VPC 裡只能存在一個 ENI

<details><summary>看答案</summary>

**答案：(A)** 規則是跟著網卡走的；把它想成貼在 EC2 上只是方便理解的說法。

</details>

**Q5. 同一個 VPC 中，不同 Subnet 的資源要互通，路由表通常靠哪一類路由？**

- (A) VPC 的 local 路由
- (B) 指向 Internet Gateway 的預設路由
- (C) 指向 NAT Gateway 的預設路由
- (D) 指向 VPC 端點的路由

<details><summary>看答案</summary>

**答案：(A)** 同一個 VPC 內部互通靠的是 local 路由；另外三種都是為了連到 VPC 以外的目的地。

</details>

**Q6. 哪個情境最符合跨 AZ 高可用的概念？**

- (A) 把同一套服務部署在不同 AZ，避免單一 AZ 故障就全面中斷
- (B) 把所有執行個體集中放進同一個 Subnet，以縮短路由
- (C) 替同一台 EC2 掛上多個 Security Group
- (D) 讓所有 Subnet 共用同一個 Network ACL

<details><summary>看答案</summary>

**答案：(A)** 高可用的關鍵是把服務分散到不同的故障隔離位置，而不是調整安全規則。

</details>

**Q7. Security Group 被稱為「有狀態」，代表什麼？**

- (A) 允許建立連線之後，對應的回應流量可以自動通過
- (B) 規則依編號由小到大比對，只採用第一筆符合的
- (C) 它會記錄並長期保存經過的應用程式資料
- (D) 它可以加入明確的拒絕規則

<details><summary>看答案</summary>

**答案：(A)** 有狀態是指它記得已建立的連線；依編號比對和可拒絕是 Network ACL 的特性。

</details>

**Q8. 建立公開子網路時，Internet Gateway 應該掛載在哪裡？**

- (A) VPC
- (B) 某一個 Subnet
- (C) 某一台 EC2 的 ENI
- (D) 該 Subnet 的路由表

<details><summary>看答案</summary>

**答案：(A)** Internet Gateway 掛在 VPC 上；Subnet 是透過路由表指向它才連得出去。

</details>

**Q9. 公開子網路裡的一台 EC2，登進作業系統卻查不到自己的公有 IP，為什麼外面還是連得到它？**

- (A) Internet Gateway 替它做一對一的位址轉換，兩個方向都會換掉位址
- (B) 公有 IP 其實記在 Security Group 的規則裡，作業系統看不到是正常的
- (C) 路由表會在封包離開時把私有位址改寫成 Elastic IP，跟 Internet Gateway 無關
- (D) 公開子網路裡的 EC2 是靠 NAT Gateway 做位址轉換的

<details><summary>看答案</summary>

**答案：(A)** EC2 從頭到尾只知道私有位址；出去時來源被換成公有位址、進來時目的被換回私有位址，都是 Internet Gateway 做的。

</details>

**Q10. 新建一個 Security Group，一條規則都還沒加就掛到 EC2 上，預設行為是什麼？**

- (A) 外面連不進來，但這台機器可以主動連出去
- (B) 進出都被擋住，兩個方向都要加規則才會通
- (C) 進出都放行，要加規則才擋得住
- (D) 外面連得進來，但這台機器不能主動連出去

<details><summary>看答案</summary>

**答案：(A)** 新建的安全群組沒有任何入站規則，卻帶一條允許全部出站的規則，所以是進來全拒、出去全放。

</details>
