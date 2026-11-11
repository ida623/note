# 17. Docker Desktop 與 Colima

> 來源：[筆記平台 · 容器與 Kubernetes](https://hhtim.github.io/notes-platform/k8s/#/lesson/docker-desktop-colima)　第 17 課 / 共 23 課 · 約 11 分鐘

**Mac 和 Windows 上那層 Linux 是誰開的，以及四棒怎麼傳。**

### 讀完這課你會

*   說出 docker 指令到容器跑起來經過哪幾棒
*   說出 Windows、macOS 上那層 Linux 是誰開的
*   把 Spring Boot 的 JAR 包成映像檔跑起來
*   知道換工具後映像檔「不見」是怎麼回事

*【先把棒次排好】*

## 一行 docker 指令，背後有四棒

〈Docker 上手〉說過 CLI 自己不做事。完整的傳球是這樣：

| 誰 | 白話角色 | 正式名稱 |
| --- | --- | --- |
| `docker` 指令 | 接單櫃台，把你的要求送出去 | Docker CLI |
| `dockerd` | 總管，決定要做什麼、管網路和映像檔 | Docker Engine（容器引擎） |
| containerd | 工頭，管映像檔和容器的一生 | 容器執行環境（〈Pod 與 Node〉出現過） |
| runc | 工人，真的去把那支被隔離的程式啟動起來 | 低階執行工具 |

〈Docker 上手〉提過：Linux 容器要的是 Linux 核心。在 Mac 和 Windows 上，**只有第一棒（你打的 `docker` 指令）留在自己的作業系統上，後面三棒都在那台 Linux 裡面**——包括 `dockerd`。所以問題不是「Docker 裝不起來」，是「要先生出一個 Linux 給後面三棒站」。

*【Windows 路線】*

## Docker Desktop 借 WSL 2 那層 Linux

Docker Desktop 是**一站式**的裝法：圖形介面、Docker CLI、容器引擎、Compose、網路轉送、檔案共享，一次包給你。在 Windows 上它用 WSL 2（Windows 內建的 Linux 子系統）當地基。

```
Windows 終端機
  ↓ docker 指令
Docker Desktop
  ↓
WSL 2 的 Linux 環境
  ↓ dockerd → containerd → runc
Linux 容器
```

這一層很容易被誤會成你自己在 Windows 上裝的那個 Linux 發行版。實際上 Docker Desktop 跑在**它自己的 `docker-desktop` 發行版**裡，和你裝的其他 WSL 發行版互相隔離。[出處](https://docs.docker.com/desktop/features/wsl/) 所以就算你在 Windows 上裝了 Ubuntu，Docker 也不是跑在那個裡面。

你打 `-p 8080:8080` 的時候，Docker Desktop 幫你把 Windows 的 8080 轉到 WSL 2、再轉到容器。使用者連 `localhost:8080`，流量是這樣一路過去的。

*【macOS 路線】*

## Docker Desktop 或 Colima，差在誰管那台虛擬機

macOS 本身不是 Linux，也沒有 WSL 這種東西，所以要跑 Linux 容器就一定得開一台 Linux 虛擬機。兩條路：

##### Docker Desktop：一站式

*   圖形介面、CLI、引擎、Compose 全包。
*   虛擬機由它自己開、自己管，你不太需要知道。
*   裝好就能用，適合不想研究底下那層的人。

##### Colima：模組化

*   Colima 只負責管那台 Linux 虛擬機。
*   Docker CLI、Compose 自己另外裝。
*   沒有圖形介面，全部在終端機。
*   裝法：`brew install colima docker docker-compose`

```
macOS 終端機
  ↓ docker 指令
Docker context / socket
  ↓
Colima 管的那台 Linux 虛擬機
  ↓ dockerd → containerd → runc
Linux 容器
```

Colima 自己不開虛擬機，它叫 **Lima**（一個在 macOS 上開 Linux 虛擬機的工具）去開。啟動時可以指定要給多少資源：

```
colima start --cpu 4 --memory 8
```

數字照你電腦的容量調，不要把資源全部塞給虛擬機。

#### 三個容易記錯的細節

*   Docker Desktop for Mac 的虛擬機管理器現在有兩個選項：Docker 自己做的 **Docker VMM**，和 Apple 的 **Virtualization framework**。Docker VMM 的切換步驟在 Mac 這邊只有 **Apple Silicon** 有（Intel Mac 沒有這一項；Windows 另有自己的分頁），而舊的 HyperKit 只剩 Intel Mac 能用、已被標為棄用（deprecated），建議改用 Apple 的 Virtualization framework。[出處](https://docs.docker.com/desktop/features/vmm/)

*   Colima 從 v0.6.0 起，底下用的是 Ubuntu 映像[出處](https://colima.run/docs/faq/)。v0.5.6 以前，Ubuntu 只是**可以另外開啟的一層**。

    > 📝 查證更正：原筆記寫「Colima 建立 Alpine Linux VM (更輕量)」以及「Lima 下載 Alpine 或 Ubuntu Linux 映像檔」，查證後更正：Colima 官方常見問答寫「From v0.6.0 onward, Colima uses Ubuntu as the underlying image」，且 v0.5.6 以前 Ubuntu 只是可選的一層

*   Lima 不是只會用 QEMU。Lima 支援多種虛擬化方式，而且預設變過——Lima v1.0 之前預設是 QEMU（一套開源的虛擬機軟體），v1.0 起在 macOS 13.5 以上的新機器預設改用 Apple 的 VZ（Virtualization framework）。[出處](https://lima-vm.io/docs/config/vmtype/) 所以「Colima 一定用 QEMU」這句現在不成立。

*【動手】*

## 把一個 Spring Boot 的 JAR 變成容器

先用 Maven 或 Gradle 把 JAR 建出來，再寫 Dockerfile（寫法見〈映像檔與 Dockerfile〉）：

```
FROM eclipse-temurin:21-jre
WORKDIR /app
COPY target/my-app.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

上面基礎映像檔選 `eclipse-temurin` 而不是 `openjdk`，是有原因的：Docker Hub 上的 `openjdk` 官方映像頁面已經掛著停止維護的公告，Java 的基礎映像檔要改用 `eclipse-temurin`、`amazoncorretto` 這幾個替代品[出處](https://hub.docker.com/_/openjdk)。

> 📝 查證更正：原筆記的 Dockerfile 用 openjdk:17-jre-alpine，查證後更正：Docker Hub 上的 openjdk 官方映像頁面寫「This image is officially deprecated and all users are recommended to find and use suitable replacements ASAP」，建議改用 eclipse-temurin、amazoncorretto、ibm-semeru-runtimes、ibmjava、sapmachine

```
docker build -t my-spring-app:1.0 .
docker run -d --name my-spring-app -p 8080:8080 my-spring-app:1.0

docker ps
curl http://localhost:8080
```

這幾行按下去，實際發生的事是：CLI 把建置內容和指令送給引擎 → 引擎在那台 Linux 虛擬機裡拉基礎映像檔、跑 Dockerfile 的每一步、疊出分層映像檔 → 啟動時由 containerd 和 runc 準備檔案系統、隔離房間、資源上限，最後把 Java 程序起起來。**你的 Java 程式從頭到尾都是在那台 Linux 虛擬機裡面跑的**，只是連線被一路轉回你的 `localhost`。

*【最常見的疑惑】*

## 「我的映像檔不見了」

從 Docker Desktop 換成 Colima（或反過來）之後，`docker image ls` 突然空了。資料通常沒有不見——**是你的 CLI 指到另一間工廠了**。每個引擎有自己的映像檔和容器，Docker CLI 靠 context（連線設定）決定要跟哪一個講話：

```
docker context ls      # 有哪些連線設定，哪個是現在用的
docker context show    # 現在指著哪一個
docker info            # 連上去之後看到的是哪一套
```

| 面向 | Docker Desktop | Colima |
| --- | --- | --- |
| 平台 | Windows、macOS | macOS（也支援其他環境） |
| 操作方式 | 圖形介面加命令列 | 命令列為主 |
| 那層 Linux | 產品自己開、自己管 | 透過 Lima 開和管 |
| Docker CLI | 通常隨產品一起裝 | 要自己另外裝 |
| 映像檔放哪 | 在它自己的 Linux 後端裡 | 在 Colima 那台虛擬機裡 |
| Dockerfile 要不要改 | 不用——同一份 Dockerfile 兩邊都能建 |   |

兩邊的 Dockerfile 通用，但效能、檔案掛載和網路行為仍然可能不一樣，換工具之後值得重跑一次自己的流程。

### 重點整理

*   四棒：docker CLI → dockerd → containerd → runc；需要 Linux 核心的是後面兩棒。
*   Windows 上 Docker Desktop 跑在它自己的 `docker-desktop` WSL 發行版裡，不是你裝的那個 Ubuntu。
*   macOS 上跑 Linux 容器一定要一台 Linux 虛擬機：Docker Desktop 自己開自己管，Colima 則是叫 Lima 去開。
*   Colima 從 v0.6.0 起用的是 Ubuntu 映像；Lima 的預設虛擬化方式也變過——v1.0 起，在 macOS 13.5 以上**新建**的機器預設改用 Apple 的 VZ（設定不相容時仍退回 QEMU）。
*   Java 的基礎映像檔別再用 `openjdk`，它已經停止維護。
*   換工具之後映像檔「不見了」，先看 `docker context`——多半只是指到另一個引擎。

## 隨堂測驗

**Q1. 從你打 docker run 到容器跑起來，四棒的順序是什麼？**

- (A) docker CLI → dockerd → containerd → runc
- (B) runc → containerd → dockerd → docker CLI
- (C) docker CLI → runc → dockerd → containerd
- (D) containerd → docker CLI → runc → dockerd

<details><summary>看答案</summary>

**答案：(A)** CLI 只接單，真正建立隔離環境、啟動程式的是最後那兩棒。

</details>

**Q2. 在 Windows 上用 Docker Desktop，Docker 實際跑在哪裡？**

- (A) 它自己的 docker-desktop WSL 發行版裡，和你另外裝的發行版是隔離的
- (B) 直接跑在 Windows 核心上，不需要任何 Linux
- (C) 跑在你自己安裝的那個 Ubuntu 發行版裡面
- (D) 跑在遠端的 Docker Hub 伺服器上

<details><summary>看答案</summary>

**答案：(A)** Docker Desktop 跑在自己的 docker-desktop 發行版裡。

</details>

**Q3. 在 Colima 的架構裡，Lima 的角色是什麼？**

- (A) 負責開出並管理那台 Linux 虛擬機
- (B) 把 Java 原始碼編譯成 JAR
- (C) 取代 Dockerfile 來描述映像檔
- (D) 替 Kubernetes 建立 Ingress 規則

<details><summary>看答案</summary>

**答案：(A)** Colima 管容器執行環境，虛擬機那一層是交給 Lima。

</details>

**Q4. Colima 從 v0.6.0 起，底下那台虛擬機用的是哪個 Linux 映像？**

- (A) Ubuntu
- (B) Alpine
- (C) CentOS
- (D) Debian 8

<details><summary>看答案</summary>

**答案：(A)** Colima 從 v0.6.0 起用 Ubuntu；v0.5.6 以前，Ubuntu 只是一層可以自己開啟的選項。

</details>

**Q5. Dockerfile 裡的基礎映像檔為什麼不該再用 openjdk？**

- (A) Docker Hub 上的 openjdk 官方映像已公告停止維護，建議改用 eclipse-temurin 等替代品
- (B) openjdk 只能用在 Windows 容器
- (C) openjdk 不支援多階段建置
- (D) openjdk 的映像檔沒有辦法加標籤

<details><summary>看答案</summary>

**答案：(A)** openjdk 官方映像已停止維護，Java 的基礎映像改用 eclipse-temurin、amazoncorretto 這類替代品。

</details>

**Q6. 在 macOS 上把 Spring Boot 容器跑起來之後，那個 Java 程序實際在哪裡執行？**

- (A) 在那台 Linux 虛擬機裡的容器中，只是連線被轉回你的 localhost
- (B) 直接在 macOS 上，以原生程序的方式執行
- (C) 在 Docker Hub 的雲端主機上
- (D) 在瀏覽器的 JavaScript 引擎裡

<details><summary>看答案</summary>

**答案：(A)** Linux 容器要 Linux 核心；macOS 沒有，所以一定跑在中間那層 Linux 裡。

</details>

**Q7. 換了容器工具之後 docker image ls 變空的，最合理的解釋是什麼？**

- (A) CLI 指到另一個引擎了，用 docker context 看目前連的是哪一個
- (B) Dockerfile 被自動刪除了
- (C) 所有容器都被轉成映像檔了
- (D) 主機的連接埠被作業系統保留了

<details><summary>看答案</summary>

**答案：(A)** 每個引擎有自己的映像檔與容器清單；換 context 就等於換一間工廠。

</details>

**Q8. Docker Desktop 和 Colima 最重要的共同點是什麼？**

- (A) 兩者都替本機的 Docker 工作流程準備好 Linux 容器的執行環境，同一份 Dockerfile 兩邊都能建
- (B) 兩者一定使用同一套虛擬化技術
- (C) 兩者都附帶一模一樣的圖形介面
- (D) 兩者都把映像檔存在 macOS 的主機目錄裡

<details><summary>看答案</summary>

**答案：(A)** 產品體驗差很多，但對你的 Dockerfile 來說兩邊是一樣的。

</details>
