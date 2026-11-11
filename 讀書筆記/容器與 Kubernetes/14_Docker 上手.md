# 14. Docker 上手

> 來源：[筆記平台 · 容器與 Kubernetes](https://hhtim.github.io/notes-platform/k8s/#/lesson/docker-basics)　第 14 課 / 共 23 課 · 約 12 分鐘

**裝在哪、跑起來、看得到、收乾淨——第一輪手指頭練習。**

### 讀完這課你會

*   知道 Docker 在 Mac、Windows、Linux 上的差別
*   跑起第一個容器，看懂每個參數
*   分清前景、背景、互動三種跑法與 exec
*   把容器停掉、刪掉、看紀錄

*【實作篇・開場】*

## Docker 的三個零件

Dockerfile 是食譜、映像檔（image）是成品、容器是跑起來的那一份（見〈Docker〉）。

**容器是一種技術，Docker 只是這個技術的其中一個實作品**。常常把兩個字當同義詞用，是因為 Docker 是最成功、用得最廣的那一個。這件事背後有一整套標準在撐著，那是〈容器不等於 Docker〉的內容。

*   **Docker Engine**：真正在做事的那一支程式（正式名稱：容器引擎）。它負責建映像檔、開容器、管網路。
*   **Docker CLI**：你在終端機打 `docker` 時用的那個介面。它自己不做事，只把你的要求送給 Engine。
*   **Registry**：映像檔倉庫，大家共用的架子（〈Docker〉提過）。預設是 Docker Hub。

*【裝之前】*

## Linux 容器要的是 Linux 核心，所以 Mac 和 Windows 得墊一層

容器靠的是 Linux 核心內建的兩個機制（〈容器〉說過：一個讓你只看得到自己的東西，一個限制你能吃多少資源）。在 Linux 上這兩個機制本來就在，Docker Engine 直接用就好；在 macOS 和 Windows 上沒有 Linux 核心，所以得先有一個 Linux 環境，容器再跑在那裡面。

要分清楚的是「誰需要 Linux」：需要 Linux 核心的是 **Linux 容器**，不是 Docker Engine 這支程式本身。Docker Engine 透過 Docker Desktop 在 Windows、macOS、Linux 上都取得到，而且 Windows 上還有另一條跑 Windows 容器的路線[出處](https://docs.docker.com/engine/install/)。對 Mac 和 Windows 上要跑 Linux 容器的人來說，結論一樣：中間會有一層 Linux，只是你通常感覺不到。那一層長什麼樣，〈Docker Desktop 與 Colima〉拆開來看。

> 📝 查證更正：原筆記寫「Docker Engine 只能 run 在 Linux 環境!!」（連寫三次），查證後更正：Docker 官方文件寫 Docker Engine 透過 Docker Desktop 也能在 Windows 與 macOS 上取得；Windows 另有跑 Windows 容器的路線。「需要 Linux 核心」講的是 Linux 容器，不等於 Docker Engine 只存在於 Linux

| 你的電腦 | 常見裝法 | 中間那層 Linux |
| --- | --- | --- |
| Linux | 直接裝 Docker Engine | 不需要 |
| Windows | Docker Desktop | WSL 2（Windows 內建的 Linux 子系統） |
| macOS | Docker Desktop | 它自己開的虛擬機 |
| macOS | Colima ＋ Docker CLI | Colima 開的虛擬機 |

安裝步驟會隨版本改，以你選的那套工具的官方安裝文件為準。

*【裝完第一件事】*

## 兩行指令確認「打得到」

```
docker version
docker info
```

`docker version` 會分兩段印出來：上面是 Client（你的 CLI），下面是 Server（Docker Engine）。**只看到 Client 那一段，就是 Engine 還沒起來**——在 Mac 和 Windows 上通常是那層 Linux 還沒開。`docker info` 則列出現在有幾個容器、幾個映像檔、資料存在哪裡。

> docker ＋ 你要管的東西 ＋ 要做的動作 ＋ 選項

```
docker image ls           # 管的是映像檔，動作是列出來
docker container ls       # 管的是容器，動作是列出來
docker container stop web # 管的是容器，動作是停掉名叫 web 的那個
```

很多寫法有簡寫，例如 `docker container ls` 可以寫成 `docker ps`。`docker container ps` 也會動——`docker container ls`、`docker container list`、`docker container ps`、`docker ps` 是同一個指令。[出處](https://docs.docker.com/reference/cli/docker/container/ls/) 剛學的時候建議打完整寫法，一眼看得出你在動哪一類東西。

*【第一個容器】*

## 一行指令，跑起一個網頁伺服器

```
docker container run --name web -d -p 8080:80 nginx
```

| 這一段 | 在做什麼 |
| --- | --- |
| `--name web` | 幫這個容器取名叫 web。不取的話 Docker 會亂配一個（像 `xenodochial_clarke` 這種）。 |
| `-d` | 丟到背景跑，終端機馬上還你。 |
| `-p 8080:80` | 把**你這台機器的 8080 埠**接到**容器裡的 80 埠**。順序是「主機：容器」，不要反。 |
| `nginx` | 要用哪個映像檔。沒寫版本就是 `latest`。 |

跑起來之後開瀏覽器連 `http://127.0.0.1:8080` 就看得到 nginx 的預設首頁。

這一行按下去，Docker 依序做了這些事：

*   先在本機找有沒有 `nginx` 這個映像檔。
*   沒有就去 registry（預設 Docker Hub）下載。
*   用映像檔開一個新容器，並且給它一層自己的可寫空間。
*   配一個容器內部用的位址，把 8080 對到容器的 80。
*   執行映像檔裡設定好的那個開機指令（nginx 這個映像檔是跑一支叫 `docker-entrypoint.sh` 的腳本）。

`latest` 不是「永遠是最新版」的保證，它只是「沒指定版本時預設拿的那個標籤」，而它指到的內容會變。正式環境要指定測過的版本——這件事〈映像檔與 Dockerfile〉再細講。

*【三種跑法】*

## 前景、背景、互動

##### 背景（加 `-d`）

*   終端機立刻還你，可以繼續打別的指令。
*   關掉終端機，容器照跑。
*   看不到即時輸出，要靠 `logs` 去撈。
*   跑網站、資料庫這種長命的服務就用這個。

##### 前景（不加 `-d`）

*   輸出直接印在畫面上，適合邊跑邊看。
*   終端機被佔住，不能做別的。
*   **按 Ctrl + C 會把 SIGINT 這個訊號送進容器**，多數情況下容器就停了。
*   想脫離但不停掉：Ctrl + P 接 Ctrl + Q——**這一招要容器是用 `-i` 加 `-t` 跑起來的才有效**。

第三種是**互動**——你要在容器裡面打指令：

```
# 開一個新容器，直接進到它的 shell
docker container run -it --rm ubuntu sh

# 進到一個已經在跑的容器裡
docker container exec -it web sh
```

`-i` 是保持標準輸入（STDIN，也就是「你打的字送得進去」）開著；`-t` 是配一個偽終端機（TTY，讓你有提示符號、能按 Tab 補字、能按 Ctrl + C）。兩個一起用才有像在本機終端機操作的感覺。只給 `-i` 會沒有提示符號，只給 `-t` 則可能打不進字。

> 💡 run 和 exec 差在哪？**run 是開一個新容器；exec 是在已經在跑的容器裡再起一支程式**。所以從 exec 開出來的 shell 打 `exit` 離開，容器還是 Up；但如果你離開的是容器的主程式，容器就跟著結束。

不是每個映像檔裡都有 `bash`。精簡的映像檔（例如 Alpine 那一類）通常只有 `sh`，所以 `sh` 是比較保險的第一次嘗試。

這兩個鍵有前提：`--sig-proxy` 預設開著時，Ctrl + C 會把 SIGINT 送進容器；而 Ctrl + P 接 Ctrl + Q 這個脫離鍵，只有容器是用 `-i` 和 `-t` 啟動時才有用。[出處](https://docs.docker.com/reference/cli/docker/container/attach/) 而且**訊號送進去不保證停得掉**：容器裡的主程式是編號 1 的程序，Linux 對它有特殊待遇：預設動作的訊號一律忽略。所以**除非那支程式自己有寫處理，否則它會直接忽略 SIGINT 和 SIGTERM**。停不掉的時候用 `docker container stop`（逾時後會改送 SIGKILL）。[出處](https://docs.docker.com/reference/cli/docker/container/run/)

*【容器是什麼東西】*

## 它不是縮小版的虛擬機，它就是一支程式

除了〈容器〉講的「共用作業系統」，從外面也看得到證據：**在主機上用 `ps` 看，容器裡的程式就實實在在出現在主機的程序清單裡**，只是被關進自己的房間、被限制了能吃多少 CPU 和記憶體。程式、行程（程序）、執行緒三者的關係見〈執行緒與並行〉。

```
docker container top web    # 看這個容器裡有哪些程序
```

所以會有這個後果：**主程式停了，容器就退出了**。容器沒有「開機、待機、關機」那一套，它的命跟那支主程式綁在一起。

*【收尾】*

## 看得到、停得掉、刪得乾淨

```
# 只列還在跑的
docker container ls

# 連停掉的一起列（-a 就是 all）
docker container ls -a

# 看紀錄，-f 是持續跟著跑
docker container logs web
docker container logs -f web

# 停止、重開、刪除
docker container stop web
docker container start web
docker container rm web
```

**停止（stop）不等於刪除（rm）**。停掉的容器還在，連同它那層可寫空間裡的檔案；只有刪掉容器，那層才跟著消失。跑一次性的工作可以加 `--rm`，跑完自動刪掉，就不會累積一堆 Exited 的殘骸。

要一次處理很多個，用括號把清單餵進去：

```
docker container stop $(docker container ls -aq)   # -q 只印 ID
```

> `docker system prune` 這類指令一次會清掉多種「目前沒在用」的東西——停掉的容器、沒人掛的網路、以及**懸空的映像檔**（dangling image：沒有任何標籤指著它的那些，通常是重建之後被頂掉的舊層）。**映像檔那一項預設只清懸空的**；加上 `-a` 才會連「有標籤但目前沒有容器在用」的映像檔一起刪（`-a` 就是刪掉所有沒在用的映像檔，不只懸空的）。[出處](https://docs.docker.com/reference/cli/docker/system/prune/) 在還不確定它會掃到什麼之前，先用 `ls` 把要刪的列出來看過，再動手。

### 重點整理

*   容器是技術，Docker 是實作品之一；在 Mac 和 Windows 上跑 **Linux 容器**，中間一定墊了一層 Linux（Windows 另有跑 Windows 容器的路線）。
*   `docker version` 只印出 Client 那一段，就是 Engine 沒起來。
*   `-p` 的順序是「主機埠：容器埠」；`-d` 丟背景；`-a` 是列出全部（含停掉的）。
*   run 開新容器，exec 在既有容器裡再起一支程式；離開 exec 的 shell 不會停掉容器。
*   容器就是一支被隔離、被限制資源的程式——主程式停了，容器就退出。
*   停止只是停程式，刪除才會連那層可寫空間一起帶走。

## 隨堂測驗

**Q1. 「容器」和「Docker」的關係，哪一句最準確？**

- (A) 容器是一種技術，Docker 是實作這個技術的其中一套工具
- (B) 容器只能由 Docker 建立，兩個詞完全同義
- (C) Docker 是一種硬體虛擬化規格，容器是它的圖形介面
- (D) Docker 就是 Linux 核心裡的命名空間功能本身

<details><summary>看答案</summary>

**答案：(A)** Docker 是用得最廣的實作品，所以常被拿來當容器的代稱，但兩者不是同一件事。

</details>

**Q2. 為什麼在 macOS 上跑 Linux 容器，中間一定會有一層 Linux？**

- (A) Linux 容器靠的是 Linux 核心提供的隔離與資源限制，macOS 沒有 Linux 核心
- (B) 因為映像檔只能存在 ext4 檔案系統上
- (C) 因為 Docker CLI 只看得懂 Linux 的終端機
- (D) 因為 Docker Hub 只允許 Linux 主機下載映像檔

<details><summary>看答案</summary>

**答案：(A)** 少了 Linux 核心就沒有那兩個機制，所以得先有一個 Linux 環境，容器再跑在裡面。

</details>

**Q3. 打了 docker version，只看到 Client 那一段、沒有 Server 那一段，最可能是什麼狀況？**

- (A) Docker Engine 還沒啟動（Mac、Windows 上通常是那層 Linux 還沒開）
- (B) 映像檔下載到一半失敗了
- (C) 容器的主程式已經結束
- (D) 主機的 8080 埠被別的程式佔走了

<details><summary>看答案</summary>

**答案：(A)** CLI 自己不做事，Client 那段印得出來只代表指令存在；Server 那段才代表連得到 Engine。

</details>

**Q4. docker container run --name web -d -p 8080:80 nginx 裡面的 8080:80，意思是什麼？**

- (A) 把主機的 8080 埠接到容器裡的 80 埠
- (B) 把容器的 8080 埠接到主機的 80 埠
- (C) 限制這個容器最多用 8080 MB 記憶體、80% CPU
- (D) 指定容器編號是 8080、映像檔標籤是 80

<details><summary>看答案</summary>

**答案：(A)** 順序固定是「主機埠：容器埠」，寫反了就連不到。

</details>

**Q5. 想看到包含已經停掉的所有容器，該用哪一個？**

- (A) docker container ls -a
- (B) docker container ls
- (C) docker image ls -a
- (D) docker container top

<details><summary>看答案</summary>

**答案：(A)** -a 就是 all；不加 -a 只會列出還在跑的那些。

</details>

**Q6. 從 docker container exec -it web sh 開出來的 shell 打 exit 離開，為什麼 web 通常還是 Up？**

- (A) exec 是在既有容器裡另外起一支程式，離開它不等於結束容器的主程式
- (B) 因為 -t 會把容器鎖在執行狀態，任何指令都停不掉
- (C) 因為 sh 會自動把容器轉成虛擬機
- (D) 因為背景容器一律不接受任何停止訊號

<details><summary>看答案</summary>

**答案：(A)** 容器的命綁在主程式上；exec 起的是額外的程式，不是主程式。

</details>

**Q7. -i 和 -t 一起用，得到的是什麼？**

- (A) 輸入送得進去，而且有提示符號、能按 Tab 和 Ctrl + C——像在本機終端機操作
- (B) 自動下載缺少的映像檔並建立索引
- (C) 把容器的資料同步回 registry
- (D) 替容器配一組固定的對外位址

<details><summary>看答案</summary>

**答案：(A)** -i 保持標準輸入開著，-t 配偽終端機；只給其中一個，操作起來都會怪怪的。

</details>

**Q8. 容器的主程式結束之後，通常會怎樣？**

- (A) 容器跟著進入停止狀態
- (B) 容器自動變成一個新的映像檔
- (C) Docker 會自動另外起一支主程式頂替
- (D) 容器繼續跑，直到映像檔被刪除為止

<details><summary>看答案</summary>

**答案：(A)** 容器不是一台會待機的機器，它的生命週期跟那支主程式綁在一起。

</details>

**Q9. 停止容器和刪除容器，差別在哪？**

- (A) 停止只是結束程式，容器和它那層可寫空間都還在；刪除才會一起帶走
- (B) 停止會刪掉映像檔，刪除只清掉執行紀錄
- (C) 兩個完全一樣，只是指令名稱不同
- (D) 刪除容器一定會連它用的映像檔一起刪掉

<details><summary>看答案</summary>

**答案：(A)** 所以停掉之後再 start 回來，裡面寫過的檔案還在；rm 之後就沒了。

</details>
