# 20. 容器不等於 Docker

> 🏠 **生活化版本**：每個段落開頭的「生活比喻」先用日常情境帶你抓到感覺，接著再看原本的技術說明與程式碼；篇末有「比喻對照表」可以快速複習。

> 來源：[筆記平台 · 容器與 Kubernetes](https://hhtim.github.io/notes-platform/k8s/#/lesson/container-standards)　第 20 課 / 共 23 課 · 約 10 分鐘

**namespace、cgroup、OCI、runc——那些名字各站在哪一層。**

### 讀完這課你會

*   說出〈容器〉那兩個機制的正式名字
*   說出 OCI 標準化了什麼
*   把 dockerd、containerd、runc 放到正確的層
*   說明容器不是 Docker 發明的

*【實作篇・收尾】*

## 容器是一種技術，Docker 只是其中一個實作品

> 🏠 **生活比喻**
>
> 容器之於 Docker，就像**「保溫瓶」之於某個知名保溫瓶品牌**：大家常用品牌名稱叫整個東西，但其實還有很多牌子。

> Docker 是「容器化技術最成功、使用最廣泛的一個實作品」  
> 不是「容器」本身

*【補上名字】*

## 〈容器〉那兩個開關，其實有名字

> 🏠 **生活比喻**
>
> - **namespace**＝**隔間的牆**：讓你只看得到自己房間
> - **cgroups**＝**電表和水表限額**：限制你能用多少資源

〈容器〉說過：「Linux 本來就內建兩個機制，一個讓每個容器只看得到屬於自己的東西，一個限制它最多能吃多少 CPU 和記憶體。容器就是把這兩個開關打開而已。」這裡給它們正式名字：

*   **Namespace（命名空間）**：管「看得到什麼」。每個容器有自己的一套視野——看不到別的容器的程序、檔案、網路介面。負責的是**隔離**。
*   **Cgroup（控制群組）**：管「能用多少」。一組程序最多吃多少 CPU、多少記憶體，優先權多高。負責的是**資源管理與限制**。

〈K8s 上手：Minikube 與上雲〉你寫的 `requests` 和 `limits`，最後落到節點上就是變成 cgroup 的設定；〈Docker 上手〉用 `docker container top` 在主機上看得到容器裡的程序，也是因為它們本來就是同一台機器上的程序，只是被關進不同的 namespace。

Linux Container（LXC）是一種作業系統層的虛擬化技術，直接建在核心本來就有的那些隔離能力上。它是 Linux 核心隔離功能的使用者空間介面，用到的核心能力裡有 Kernel namespaces 和 CGroups（control groups）——和〈容器〉「容器就是把兩個開關打開」講的是同一件事。[出處](https://linuxcontainers.org/lxc/introduction/)

*【來歷】*

## 一條時間軸：容器是慢慢拼出來的

> 🏠 **生活比喻**
>
> 容器像**樂高**：chroot、namespace、cgroups 是一塊塊零件，花了幾十年才湊齊，Docker 是第一個把它們**組成好玩的成品**的人。

容器不是某天被發明出來的，是好幾樣 Linux 能力一塊一塊補齊之後，才有人把它們包成好用的東西。

```
限制看得到哪些檔案            chroot
        ↓
隔離程序、網路、掛載點等視野    namespace
        ↓
計量與限制 CPU、記憶體         cgroup
        ↓
包成好用的管理工具與映像檔分發   LXC、Docker……
```

| 時間 | 發生什麼 |
| --- | --- |
| 1979 | chroot 出現在第七版 Unix，可以限制一支程式看得到哪一段檔案系統。1982 年加進 BSD。 |
| 2000 年代初 | Linux-VServer 出現，在 Linux 上做出接近容器的隔離。 |
| 2005 | SWsoft 把 Virtuozzo 的核心以 GPL 開源，成立 OpenVZ 專案。[出處](https://wiki.openvz.org/History) |
| 2006 | Google 內部做出 Process Containers，後來改名 Control Groups（cgroups）。[出處](https://en.wikipedia.org/wiki/Cgroups) |
| 2008 年 1 月 | cgroups 併進 Linux 核心 2.6.24。[出處](https://en.wikipedia.org/wiki/Cgroups) 同年 8 月 LXC 首度發佈，把 namespace 和 cgroup 包成一整套容器管理工具。[出處](https://en.wikipedia.org/wiki/LXC) |
| 2013 | Docker 第一個公開版本 v0.1.0 發佈（2013 年 3 月）。[出處](https://github.com/moby/moby/releases/tag/v0.1.0) 最初底層就是用 LXC，後來才換成自己的執行元件。 |
| 2015 | OCI 成立，把容器的格式和啟動方式寫成標準。 |

chroot 的起點：1979 年隨第七版 Unix（Version 7）開發時出現，1982 年加進 BSD。[出處](https://www.linuxfoundation.org/blog/blog/a-brief-look-at-the-roots-of-linux-containers)

LXC 常被說成「第一個完整的容器管理實作」，這個說法要綁在 **Linux 上**才成立：在 Linux 上它是第一個把隔離、資源管理和生命週期工具湊齊的一套；別的作業系統更早就有同類的東西：

*   2000 年，FreeBSD 把 chroot 擴充成 FreeBSD Jails
*   2000 年代初，Solaris 推出 zones，把作業系統的服務虛擬化 [出處](https://www.linuxfoundation.org/blog/blog/a-brief-look-at-the-roots-of-linux-containers)

Docker 真正改變局面的地方，其實不在隔離本身——那些能力 2008 年就在核心裡了。它做的是**分層映像檔、一個指令就能建、一個倉庫就能分發、一套所有人都看得懂的操作介面**。把已經存在的底層能力，整理成做得出來、送得出去、跑得起來的東西。

*【標準】*

## OCI：讓容器換得掉的那份文件

> 🏠 **生活比喻**
>
> OCI 像**貨櫃的國際標準尺寸**：只要符合規格，哪家船公司、哪個港口的吊車都能搬。

2015 年，容器圈把格式寫成了公開標準。OCI（Open Container Initiative，開放容器倡議）在 2015 年 6 月 22 日由 Docker、CoreOS 等業界成員發起，掛在 Linux 基金會（Linux Foundation）底下。[出處](https://opencontainers.org/about/overview/)

| 規格 | 規定什麼 |
| --- | --- |
| Runtime Spec | 怎麼把一包解開的檔案真的啟動成一個容器——基本操作規範。 |
| Image Spec | 映像檔長什麼樣：清單、分層、設定。 |
| Distribution Spec | 怎麼把映像檔推上去、拉下來（registry 的那套 API）。2021 年 5 月發佈 v1.0.0。[出處](https://github.com/opencontainers/distribution-spec/releases/tag/v1.0.0) |

規格現在有三份：除了 Runtime Spec 和 Image Spec，第三份 Distribution Spec 管的就是你〈映像檔與 Dockerfile〉在做的 push 和 pull。[出處](https://opencontainers.org/about/overview/)

*【名字對照】*

## 那幾個名字各站在哪一層

> 🏠 **生活比喻**
>
> 像一間餐廳的分工：**點餐系統**（docker / kubectl）→ **廚房經理**（dockerd / kubelet）→ **領班**（containerd / CRI-O）→ **真正下廚的**（runc）。

把〈Docker Desktop 與 Colima〉那四棒和標準疊在一起看，整張圖就完整了：

| 層 | 例子 | 可不可以換掉 |
| --- | --- | --- |
| 你打的指令 | `docker`、`podman`、`nerdctl` | 可以 |
| 引擎／總管 | Docker Engine（`dockerd`） | 可以，K8s 預設就不經過它了 |
| 容器執行環境 | containerd、CRI-O | 可以 |
| 真的去啟動的那支 | runc（照 OCI Runtime Spec 做的） | 可以，只要照同一份規格 |
| 映像檔的格式 | OCI Image Spec | 這一層就是不能換的共識 |

> 💡 這張表也回答了〈Pod 與 Node〉提過的那件事：**Kubernetes 從 v1.24 起，kubelet 不再內建接 Docker Engine 的那段轉接程式（dockershim），改成一律透過 CRI 這個共同介面接容器執行環境——containerd、CRI-O 都可以，不是只有 containerd；要繼續用 Docker Engine 也能裝 cri-dockerd 接上去。而你用 Docker 建出來的映像檔照樣能跑**，在所有 CRI 實作上都能跑。[出處](https://kubernetes.io/blog/2022/02/17/dockershim-faq/) 原因就在最後一列——上面幾層都可以換，映像檔的格式是共同遵守的規格。你手上那些 Dockerfile 和映像檔，不綁在 Docker 這個產品上。

所以〈要不要用 K8s〉那句「同一個映像檔在 `docker run`／託管服務／K8s 都能跑」，底下撐著它的就是這份標準。

### 🗺️ 比喻對照表

| 技術名詞 | 生活比喻 |
| --- | --- |
| 容器 vs Docker | 保溫瓶 vs 某品牌 |
| namespace / cgroups | 隔間牆 / 水電表限額 |
| OCI | 貨櫃的國際標準尺寸 |
| runc | 真正下廚的人 |

### 重點整理

*   容器是技術，Docker 是最成功的實作品之一——兩個詞不是同義詞。
*   〈容器〉那兩個機制的名字：namespace 管「看得到什麼」，cgroup 管「能用多少」。
*   容器是拼出來的：chroot（1979）→ namespace 與 cgroup（cgroup 的前身 2006 年在 Google 做出來，2008 年併進核心）→ LXC（2008）→ Docker（2013）。
*   Docker 的貢獻在分層映像檔、建置流程、倉庫分發和好用的介面，不在隔離本身。
*   OCI 從 2015 年起把容器寫成標準，現在有三份：Runtime、Image、Distribution。
*   指令、引擎、執行環境都能換掉，映像檔格式是不換的那一層——這就是 K8s 拿掉 Docker 也不影響你的原因。

## 隨堂測驗

**Q1. Linux 的 namespace 在容器技術裡負責什麼？**

- (A) 隔離——決定這個容器看得到哪些程序、檔案、網路介面
- (B) 限制這個容器最多能用多少 CPU 和記憶體
- (C) 提供映像檔的公開下載網站
- (D) 把單體程式自動拆成多個服務

<details><summary>看答案</summary>

**答案：(A)** namespace 管「看得到什麼」，配額那件事是 cgroup 在管。

</details>

**Q2. cgroup 解決的是哪一類問題？**

- (A) 計量與限制 CPU、記憶體這些資源
- (B) 替 HTTP 請求挑選網域名稱
- (C) 定義 Dockerfile 的分層語法
- (D) 管理應用程式的資料庫結構

<details><summary>看答案</summary>

**答案：(A)** 你在 Kubernetes 寫的 requests 和 limits，落到節點上就是變成 cgroup 的設定。

</details>

**Q3. Docker 對容器普及最重要的貢獻是什麼？**

- (A) 把分層映像檔、建置流程、倉庫分發和好用的介面整合成一套
- (B) 發明了作業系統層級的所有隔離機制
- (C) 讓每個容器可以執行在自己獨立的硬體上
- (D) 取消了容器對核心相容性的要求

<details><summary>看答案</summary>

**答案：(A)** 隔離的底層能力 2008 年就在核心裡了；Docker 做的是把它們變成做得出來、送得出去的東西。

</details>

**Q4. cgroups 是什麼時候併進 Linux 核心的？**

- (A) 2008 年 1 月，核心 2.6.24——它的前身是 Google 2006 年的 Process Containers
- (B) 1979 年，隨第七版 Unix 一起發布
- (C) 2013 年，隨 Docker 第一版一起發布
- (D) 2015 年，OCI 成立的時候

<details><summary>看答案</summary>

**答案：(A)** 1979 年那個是 chroot；2013 年是 Docker 出現；2015 年是 OCI 成立。

</details>

**Q5. OCI 這個組織在做什麼？**

- (A) 把容器的映像檔格式、啟動方式和分發方式寫成公開標準
- (B) 販售商用的容器執行環境授權
- (C) 維護 Docker Hub 上所有官方映像檔
- (D) 決定 Kubernetes 每一版要加哪些功能

<details><summary>看答案</summary>

**答案：(A)** 它是 2015 年成立、掛在 Linux 基金會底下的專案，目前有 Runtime、Image、Distribution 三份規格。

</details>

**Q6. Kubernetes 從 v1.24 起，kubelet 不再內建接 Docker Engine 的那段轉接程式，為什麼你用 Docker 建的映像檔還是能跑？**

- (A) 映像檔的格式是 OCI 的共同規格，換掉上面那幾層不影響它
- (B) 因為 Kubernetes 會自動把映像檔轉檔
- (C) 因為 Docker 額外提供了一套相容程式要你安裝
- (D) 因為 Docker 建出來的映像檔只是純文字檔

<details><summary>看答案</summary>

**答案：(A)** 指令、引擎、執行環境都可以換（containerd、CRI-O 都行，裝了 cri-dockerd 連 Docker Engine 都還能接），不能換的是大家共同遵守的映像檔格式，所以 docker build 出來的映像檔在所有 CRI 實作上都能跑。

</details>

**Q7. 在〈Docker Desktop 與 Colima〉那幾棒裡，runc 站在哪一層？**

- (A) 最底下——照 OCI 的規格，真的把那支被隔離的程式啟動起來
- (B) 最上面——使用者輸入指令的介面
- (C) 負責在 registry 上存放映像檔
- (D) 負責替 Service 分配叢集內的位址

<details><summary>看答案</summary>

**答案：(A)** 順序是 docker CLI → dockerd → containerd → runc；runc 是最後真的動手的那一棒。

</details>

**Q8. FreeBSD Jails、Solaris Zones 和 LXC 三者的關係是什麼？**

- (A) Jails 和 Zones 在別的作業系統上更早做出同一類的隔離，LXC 是 Linux 上把這些能力湊齊的那一套
- (B) 三者是同一套程式在不同作業系統上的移植版本
- (C) Jails 和 Zones 是 LXC 推出之後才出現的仿製品
- (D) 三者都只是 chroot 的別名，功能完全相同

<details><summary>看答案</summary>

**答案：(A)** Jails 是 2000 年 FreeBSD 把 chroot 擴充出來的，Solaris 的 zones 在 2000 年代初把作業系統服務虛擬化；LXC 則是 2008 年在 Linux 上把 namespace 和 cgroup 包成一整套。所以「LXC 是第一個完整的容器管理實作」這句話，要綁在 Linux 上才站得住。

</details>
