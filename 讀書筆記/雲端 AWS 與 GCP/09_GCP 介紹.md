# 09. GCP 介紹

> 來源：[筆記平台 · 雲端 AWS 與 GCP](https://hhtim.github.io/notes-platform/cloud/#/lesson/gcp-intro)　第 9 課 / 共 18 課 · 約 18 分鐘

**從資源階層、地理範圍與 Compute Engine，建立不會搞混 Project、Region、Zone、VPC 和 VM 的基礎觀念，並看懂權限怎麼一路往下累加。**

### 讀完這課你會

*   分清 GCP 的管理階層與地理位置
*   說出 Global、Regional、Zonal 三種範圍
*   說出 Compute Engine、GKE、Cloud Run 的定位
*   說出權限怎麼往下累加、角色與服務帳戶

*【平台全貌】*

## Google Cloud 是一組透過網路使用的雲端服務

Google Cloud Platform（GCP）是 Google 提供的雲端運算平台。不必先自己建好所有實體伺服器，就能用到運算、儲存、網路、資料庫、資料分析、容器與人工智慧等能力。

| 需求 | 代表服務 | 用途 |
| --- | --- | --- |
| 虛擬機 | Compute Engine | 建立並執行 VM。 |
| 物件儲存 | Cloud Storage | 存放圖片、影片、備份與其他物件。 |
| 虛擬網路 | Virtual Private Cloud | 管理 Subnet、路由與防火牆規則等網路設定。 |
| 關聯式資料庫 | Cloud SQL | 使用代管的關聯式資料庫。 |
| Kubernetes | Google Kubernetes Engine | 執行與管理容器化的工作負載。 |
| 身分與權限 | Identity and Access Management | 控制誰能對哪些資源做哪些操作。 |

*【管理階層】*

## Project 是管理資源的基本單位，不是地理位置

```
Organization（組織，可選）
└── Folder（資料夾，可選）
    └── Project（專案）
        ├── Compute Engine VM
        ├── VPC Network
        ├── Cloud Storage Bucket
        └── 其他服務資源
```

Organization 通常代表一間公司或機構；Folder 可以依部門、系統或環境整理 Project；Project 則承載 API、IAM、計費關聯、配額與各種服務資源。

可以想成公司的文件櫃：Organization 是整間公司，Folder 是部門抽屜，Project 是實際辦某件事的資料夾。這是管理關係，不是機房地圖，所以 Project 本身不是 Region 也不是 Zone。

政策可以套在不同管理層級，並影響底下的資源。設計權限時要看完整階層，不能只看資源旁邊那一條設定。

更精確地說，權限是**往下累加**的：一個資源實際生效的允許政策，是設定在它自己身上的允許政策，加上從父項繼承下來的允許政策，兩者的聯集。[出處](https://docs.cloud.google.com/iam/docs/resource-hierarchy-access-control)（聯集＝把兩邊的權限全部合起來算，重複的只算一次。）

> 💡 這句話的實務後果是：你在 Project 上「少給」某個人權限，並不會把他在 Organization 或 Folder 那一層已經拿到的權限收回來。往下看只會越看越多，不會越看越少。

所以查一個人為什麼碰得到某個資源，要從 Organization 一路看到資源本身，不能只看資源旁邊那一格。真的要在低層擋掉上層給出去的東西，得另外用拒絕政策（deny policy），那是一套跟允許政策分開的機制。

*【地理位置】*

## Region 是地理區域，Zone 是裡面的部署與故障隔離位置

Region 是 Google Cloud 的獨立地理區域；Zone 是 Region 內的部署位置，也是故障隔離單位。一般的 Compute Engine VM 屬於 Zonal Resource，所以建立時要選 Zone。

一個 Region 有幾個 Zone？一個 Region 由三個或以上的 Zone 組成[出處](https://docs.cloud.google.com/docs/geography-and-regions)。通則是這些 Zone 分布在三座以上的實體資料中心，但有例外：斯德哥爾摩、墨西哥、大阪、蒙特婁這四個 Region，三個 Zone 只落在一或兩座實體資料中心。所以「一個 Zone 對應一棟資料中心」不能當定律，別把 Zone 記成固定的實體資料中心階層。

常被引用的「同一 Region 內的 Zone 之間小於 5 毫秒」「Zone 內小於 1 毫秒」不是 Google 的承諾：同一 Region 內 Zone 之間的連線規格是高頻寬、低延遲[出處](https://docs.cloud.google.com/compute/docs/regions-zones)，沒有寫成毫秒數。

這不代表實測跑不出那種數字。估算法則是每 100 公里約 1 毫秒來回延遲；網路不會走理想路徑，實際距離通常是地圖直線距離的 1.5 到 2 倍，估的時候要把這個倍數算進去[出處](https://docs.cloud.google.com/solutions/best-practices-compute-engine-region-selection)。同一 Region 的 Zone 通常只隔幾公里到幾十公里，所以實際延遲很低是合理的。

差別在於：那是估算，不是可以拿來當設計保證的規格。要規劃對延遲敏感的架構，就實測自己那組 Region 與 Zone——Google 的 Network Intelligence Center 也有區域配對的實測延遲可看——別把記憶中的數字當承諾。

選位置時通常要一起考慮使用者延遲、資料落地、災難復原、那裡有沒有你要的服務或硬體，以及資料傳輸成本。把 VM 分散到不同 Zone 能降低單一 Zone 故障的影響，但要自動導流還是得搭配負載平衡、健康檢查或其他故障切換設計。

*【資源範圍】*

## Global、Regional、Zonal 是資源的適用範圍，不是一條路徑

| 範圍 | 意義 | 常見例子 |
| --- | --- | --- |
| Global | 不隸屬單一 Region 或 Zone | VPC Network |
| Regional | 隸屬一個 Region，但不綁定單一 Zone | Subnet |
| Zonal | 隸屬一個 Zone | 一般的 Compute Engine VM |

```
同一台 VM 可以同時這樣描述：
管理上：屬於某個 Project
地理上：建立在某個 Zone
網路上：網路介面連到同一 Region 的 Subnet
```

> 💡 不要背成「Project → VPC → Region → Zone → Subnet → VM」。Region 與 Zone 是地理位置，不是建立在 VPC 裡面的子資源。

上面三種講的是「資源屬於哪個範圍」。另外還有一個很容易跟 Regional 搞混的詞叫 **Multi-Region（多重區域）**，它是存資料時可以挑的地理範圍，而且比一個 Region 更大。Cloud Storage 的位置有四種選項：

| 選項 | 範圍 | 例子 |
| --- | --- | --- |
| zone | 一個區域裡的特定範圍；只有 Rapid Bucket（高效能的區域級 bucket）能用，一般的 bucket 選不到 | `US-CENTRAL1-A` |
| region | 一個特定的地理位置 | 愛荷華（`US-CENTRAL1`） |
| dual-region | 一組特定的區域配對 | 東京與大阪（`ASIA1`） |
| multi-region | 一個大型地理區域，包含兩個或更多的地理區域 | 美國（`US`） |

所以一般 bucket 實際在挑的是後面三種[出處](https://docs.cloud.google.com/storage/docs/locations)。

Global 和 Multi-Region 是兩件事，別混用。Global（例如 VPC Network）的意思是「這個資源不綁任何地點」；Multi-Region 的意思是「這份資料實際被放在一整片涵蓋多個區域的範圍裡」——你還是選了地點，只是選了一大片。這樣選的用意：這類跨區域的服務，設計上能在單一區域失效之後繼續運作[出處](https://docs.cloud.google.com/docs/geography-and-regions)。會挑 Multi-Region 的多半是存資料的服務，例如 Cloud Storage 的 bucket；前面提過，一般的 Compute Engine VM 是 Zonal，建立時挑的是 Zone。

*【虛擬網路】*

## VPC 像跨城市的私人道路網，Subnet 像各城市的地址區

Google Cloud 的 VPC Network 是 Global Resource，可以包含位於不同 Region 的 Subnet；每個 Subnet 只屬於一個 Region，而不屬於單一 Zone。

```
Project：shopping-project
├── VPC：shopping-vpc（Global）
│   ├── taiwan-subnet（Regional）
│   └── tokyo-subnet（Regional）
└── Compute Engine VM（Zonal）
    └── 網路介面 → 與 VM 同一 Region 的 Subnet
```

所以同一 Region 不同 Zone 的 VM 可以連到同一個 Subnet；但 VM 的網路介面不能直接連到另一個 Region 的 Subnet。

*【Compute Engine】*

## GCE 像向 Google 租一台可以遠端管理的虛擬電腦

Google Compute Engine（GCE）是基礎設施即服務（Infrastructure as a Service，IaaS）。Google 維護底層實體硬體，使用者選 VM 規格、作業系統、磁碟與網路，並負責作業系統更新、應用程式，以及多數 VM 內部的安全設定。

GCE 適合需要控制作業系統、安裝特定軟體、跑傳統應用程式，或工作負載還不適合容器化的情況。它給你較高的控制度，也代表要承擔較多維運責任。

GCE 常被提到的兩個計費特色是「以秒計費」與「持續使用折扣」（sustained-use discount，同一個月裡跑得夠久就自動打折）。兩項都存在，但各有一個條件。以秒計費是每分鐘起跳：所有 vCPU、GPU 與記憶體最少收一分鐘，跑 30 秒也按一分鐘算，滿一分鐘之後才改以一秒為單位計費[出處](https://cloud.google.com/compute/vm-instance-pricing)。持續使用折扣則只適用於部分機器系列（例如 N1、N2、N2D、C2、M1、M2），較新的機型不在其中[出處](https://docs.cloud.google.com/compute/docs/sustained-use-discounts)。實際計價一律以當下的官方定價與帳務文件為準。

*【抽象層級】*

## 從 VM 到函式，管理責任一層層交給平台

| 服務 | 主要部署單位 | 適合情境 |
| --- | --- | --- |
| Compute Engine | VM | 需要作業系統與基礎設施的控制權。 |
| Google Kubernetes Engine | 容器化工作負載 | 需要 Kubernetes 編排能力，又希望平台代管部分叢集工作。 |
| Cloud Run | 容器 | 想執行容器，但不想直接管伺服器或叢集。 |
| App Engine | 應用程式 | 希望由平台處理較多執行環境與擴展工作。 |
| Cloud Functions | 事件驅動的函式 | 用事件觸發較小的程式單元。 |

選服務不是單純追求「越自動越好」。需要特殊作業系統設定時，GCE 可能比較合適；已經在用 Kubernetes 且需要編排控制時，可以考慮 GKE；想直接跑容器又不想管基礎設施時，Cloud Run 通常更貼近需求。什麼時候該從 Docker 走到託管容器服務或 Kubernetes，見〈要不要用 K8s〉。

*【角色的三種來源】*

## 基本、預先定義、自訂——由粗到細

在 Google Cloud，權限不是一條一條直接給人，而是包成「角色」（role）再授予。角色依來源分三種：

| 角色種類 | 誰決定內容 | 顆粒度 | 什麼時候用 |
| --- | --- | --- | --- |
| 基本角色（basic） | Google 內建，範圍很寬 | 最粗 | 個人實驗、沙盒環境 |
| 預先定義角色（predefined） | Google 依服務維護 | 中等，對準單一服務 | 日常授權的首選 |
| 自訂角色（custom） | 你自己挑權限組出來 | 最細 | 預先定義的都不剛好時 |

三種角色：

*   基本角色：權限非常寬鬆，給予對 Google Cloud 資源的廣泛存取
*   預先定義角色：基本角色之外另外提供的，對特定的 Google Cloud 資源給予細緻的存取
*   自訂角色：你自己建立的 IAM 角色[出處](https://docs.cloud.google.com/iam/docs/roles-overview)

基本角色包含跨所有 Google Cloud 服務的數千項權限，正式環境除非別無選擇，不要授予基本角色。配合前面講的權限聯集，在高層級隨手給一個基本角色，底下所有專案都會跟著吃到。

角色名稱換過（以下是 2026 年 9 月的狀態）：

*   Owner、Editor、Viewer 這三個老面孔現在歸類為**舊版基本角色**（legacy basic roles）。它們在 IAM 推出之前就已存在，原本叫 *primitive roles*（原始角色）
*   另外還有一組較新的基本角色 Admin、Writer、Reader，但這組在 2026 年 9 月仍掛著預覽版（Preview）標示、受「Pre-GA 條款」規範：預覽版功能照現狀提供，支援可能有限
*   而且 Reader、Writer、Admin 還不能從主控台授予，要改用 API 或 gcloud CLI[出處](https://docs.cloud.google.com/iam/docs/roles-overview)

所以「Primitive／Predefined／Custom 三種角色」的分法照樣成立，Primitive 是基本角色的舊名；Owner、Editor、Viewer 本身還在，照樣能用。

*【給程式用的帳號】*

## 服務帳戶既是「誰」，也是「一個可以被授權的東西」

服務帳戶（Service Account）是給程式用的帳號：一種特殊的帳戶，通常由應用程式或運算工作負載使用（例如一個 Compute Engine 執行個體），而不是由人使用。[出處](https://docs.cloud.google.com/iam/docs/service-account-overview)這跟〈AWS 全域架構與 IAM〉講的 AWS 用 Role 取代長期金鑰是同一個思路：讓程式帶著一個有身分的帳號去做事，而不是把密碼寫進程式碼。

它有個一開始容易卡住的雙重身分：

*   服務帳戶是**主體**（principal）：你可以授予它存取 Google Cloud 資源的權限
*   服務帳戶同時也是**資源**：你可以讓其他主體取得存取這個服務帳戶的權限[出處](https://docs.cloud.google.com/iam/docs/service-account-overview)

> 「這個服務帳戶能做什麼」和「誰可以使用這個服務帳戶」是兩件要分開設定的事。

程式要拿到這個身分，用**服務帳戶金鑰**（service account key，一個下載下來的憑證檔）確實做得到，也還能用，但建議盡可能避免使用服務帳戶金鑰。理由有三個：

*   金鑰是誰拿去用的查不出來（稽核紀錄只看得到服務帳戶動過資源，看不出是誰用了那把金鑰）
*   有建立金鑰權限的人可以藉此取得比自己更大的權限
*   任何持有服務帳戶金鑰的人都能使用它

建議的替代做法是把服務帳戶直接附加到資源上（VM、GKE 的 Pod）、用身分模擬，或對外部工作負載用 Workload Identity 聯合[出處](https://docs.cloud.google.com/iam/docs/best-practices-service-accounts)。

跨專案有兩件不同的事。**第一件：把 A 專案的服務帳戶授權去存取 B 專案的資源**（例如讓它讀 B 專案的 Cloud SQL），只要在 B 專案那邊把角色授予這個服務帳戶就成立，預設就能做。**第二件：把 A 專案的服務帳戶「附加」到 B 專案的一台 VM 上**，讓那台機器直接以這個身分執行，才是下面要過兩關的那件事。前者是給權限，後者是把身分綁到別的專案的機器上。

跨專案的第二件事就卡在後面那一半。把 A 專案建立的服務帳戶，掛到 B 專案的一台 VM 上，並不是預設就能做的事，要先過兩關。第一關是放行一條機構政策的限制條件（機構政策＝organization policy，一套可以套用在組織、資料夾或專案上的規則）：那條限制條件叫 `iam.disableCrossProjectServiceAccountUsage`，只有開和關兩種值，要確保它*未被強制執行*。這一條要注意設定的位置：它預設就是強制執行的，而且只能設定在專案層級，不能設在資料夾或組織層級，所以去組織那一層找會找不到。第二關是要讓目標服務的服務代理（service agent，Google 代表某個服務去做事的內建帳號），在那個服務帳戶上取得「服務帳戶權杖建立者」角色（`roles/iam.serviceAccountTokenCreator`）——權杖（token）就是那張有時效的臨時通行證，有了這個角色才能替那個服務帳戶簽發通行證[出處](https://docs.cloud.google.com/iam/docs/attach-service-accounts)。

開通之後會多一個副作用：IAM 會自動替放服務帳戶的那個專案加上一道「專案鎖」（project lien），用途是防止該專案被刪除，來源標記是 `iam.googleapis.com/cross-project-service-accounts`。所以那個專案之後想刪會刪不掉，要先處理這道鎖[出處](https://docs.cloud.google.com/iam/docs/attach-service-accounts)。

*【責任不會消失】*

## 用了代管服務，還是要管權限、資料與應用程式

Google 負責維護底層基礎設施，但客戶還是要正確設定 IAM、保護資料、限制網路存取，並維護自己控制的作業系統與程式。用的服務抽象程度越高，Google 負責的底層工作越多；客戶對自己資料與存取決策的責任並不會因此消失。

> 先問「我需要控制到哪一層」，再選服務；不要先挑流行的工具，再勉強把工作負載塞進去。

### 重點整理

*   Organization、Folder、Project 是管理階層；Region、Zone 是地理位置，兩條線不要混在一起。
*   VPC 是 Global，Subnet 是 Regional，一般的 Compute Engine VM 是 Zonal——VM 建立在 Zone，透過網路介面連到同一 Region 的 Subnet。
*   GCE 控制度高、要管的系統層工作也多；GKE、Cloud Run、App Engine、Cloud Functions 提供不同程度的代管與抽象。
*   有效權限是「自己身上的」加上「從父項繼承的」的聯集，所以往下只會越加越多，低層擋不掉高層給出去的權限。
*   角色分基本、預先定義、自訂三種；Owner／Editor／Viewer 是舊版基本角色，舊名叫 primitive roles，正式環境別隨手給。
*   服務帳戶既是可以被授權的主體，也是別人可以被授權去用的資源；跨專案使用要先放行機構政策，而且會多一道防誤刪的專案鎖。
*   Multi-Region 是比 Region 更大的資料存放範圍，跟「不綁地點」的 Global 不是同一回事。

## 隨堂測驗

**Q1. Google Cloud 的 Project 最適合被理解成什麼？**

- (A) 管理 API、IAM、計費關聯與服務資源的基本單位
- (B) 固定對應到一座實體資料中心
- (C) 只用來存放 Compute Engine 的映像檔
- (D) 等同於一個 Region

<details><summary>看答案</summary>

**答案：(A)** Project 是管理與治理單位，跟資源放在哪個地理位置是兩件事。

</details>

**Q2. 一般的 Compute Engine VM、Subnet 與 VPC Network，資源範圍依序是什麼？**

- (A) Zonal、Regional、Global
- (B) Regional、Global、Zonal
- (C) Global、Zonal、Regional
- (D) Zonal、Global、Regional

<details><summary>看答案</summary>

**答案：(A)** VM 落在 Zone，Subnet 屬於一個 Region，VPC Network 則是全球性資源。

</details>

**Q3. VM 位於某個 Zone 時，它的網路介面應該連到哪個 Subnet？**

- (A) 與該 Zone 同一個 Region 的 Subnet
- (B) 任意其他 Region 的 Subnet
- (C) 只屬於該單一 Zone 的專屬 Subnet
- (D) 不屬於任何 VPC 的獨立 Subnet

<details><summary>看答案</summary>

**答案：(A)** Subnet 是 Regional 資源，所以網路介面要連同一 Region 的 Subnet，但不限同一個 Zone。

</details>

**Q4. 哪個說法正確描述 Google Cloud 的 VPC Network？**

- (A) 它是 Global Resource，可以包含不同 Region 的 Subnet
- (B) 它只能存在於一個 Zone 之內
- (C) 它其實就是 Organization 的另一個名稱
- (D) 它會讓所有跨 Region 流量自動加密並免費

<details><summary>看答案</summary>

**答案：(A)** VPC 是全球性的虛擬網路，但它底下的每個 Subnet 仍各屬於一個 Region。

</details>

**Q5. 團隊需要自己選作業系統、安裝特殊軟體並控制 VM 設定，該先考慮哪項服務？**

- (A) Compute Engine
- (B) Cloud Functions
- (C) Cloud Run
- (D) App Engine

<details><summary>看答案</summary>

**答案：(A)** 要控制到作業系統這一層，就要選 IaaS 的 Compute Engine；另外三個抽象程度都更高。

</details>

**Q6. 團隊已經有容器映像檔，想把它跑起來但不想管 VM 或 Kubernetes 叢集，哪項服務較貼近需求？**

- (A) Cloud Run
- (B) Compute Engine
- (C) Google Kubernetes Engine
- (D) Cloud Storage

<details><summary>看答案</summary>

**答案：(A)** Cloud Run 是代管的容器執行平台；GKE 仍然要面對叢集，GCE 還要管到作業系統。

</details>

**Q7. 把兩台 VM 放到同一 Region 的不同 Zone 之後，哪個敘述最正確？**

- (A) 故障隔離變好，但要自動導流仍需健康檢查與負載平衡等設計
- (B) 所有流量一定會自動避開故障的那台 VM
- (C) 這兩台 VM 會因此變成 Global Resource
- (D) 這兩台 VM 必須分屬不同 VPC 才能運作

<details><summary>看答案</summary>

**答案：(A)** 跨 Zone 只是把高可用的地基打好，自動切換要另外設計。

</details>

**Q8. 關於同一 Region 內 Zone 之間的網路延遲，哪個說法正確？**

- (A) 是高頻寬、低延遲的連線，但沒有固定毫秒數的承諾
- (B) 保證一律小於 5 毫秒
- (C) 保證一律小於 1 毫秒
- (D) 跟跨 Region 的延遲相同

<details><summary>看答案</summary>

**答案：(A)** 「小於 5 毫秒」「小於 1 毫秒」這類數字不是承諾；要對延遲敏感的設計，得自己實測那組 Region 與 Zone。

</details>

**Q9. 某人在 Folder 這一層被授予了可以讀取底下所有專案的角色。你在其中一個 Project 上只給他一個範圍很小的角色，他在那個 Project 的實際權限是什麼？**

- (A) 兩者的聯集，Folder 那一層給的讀取權限仍然有效
- (B) 只剩 Project 上給的那個小角色，低層的設定會覆蓋高層
- (C) 兩者的交集，只剩兩邊都有的那些權限
- (D) 兩份設定互相衝突，系統會先擋下所有存取等管理員處理

<details><summary>看答案</summary>

**答案：(A)** 有效允許政策是資源本身的政策與繼承自父項的政策的聯集，往下只會累加，低層擋不掉高層給出去的權限。

</details>

**Q10. 正式環境裡要授權一個程式，它只需要讀取某一個 Cloud Storage bucket。最合適的做法是什麼？**

- (A) 挑一個對準該服務的預先定義角色，都不剛好時再自訂一個角色
- (B) 先給 Owner，等程式跑順了再回頭收掉多餘的權限
- (C) 給 Editor，因為它的範圍比 Owner 小
- (D) 給 Viewer，反正只要讀取權限就夠用了

<details><summary>看答案</summary>

**答案：(A)** Owner、Editor、Viewer 都是基本角色，跨所有服務、包含數千項權限；正式環境除非別無選擇，否則不要用。

</details>
