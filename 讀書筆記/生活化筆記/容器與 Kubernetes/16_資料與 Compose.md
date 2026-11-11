# 16. 資料與 Compose

> 🏠 **生活化版本**：每個段落開頭的「生活比喻」先用日常情境帶你抓到感覺，接著再看原本的技術說明與程式碼；篇末有「比喻對照表」可以快速複習。

> 來源：[筆記平台 · 容器與 Kubernetes](https://hhtim.github.io/notes-platform/k8s/#/lesson/docker-compose)　第 16 課 / 共 23 課 · 約 12 分鐘

**容器可以砍掉重來，資料不行——三種掛法，加一份 Compose 檔。**

### 讀完這課你會

*   說出容器裡的檔案什麼時候會消失
*   在具名 Volume、Bind Mount、tmpfs 間選對
*   用 Compose 檔取代一長串 docker run
*   說出 down 之後資料在不在、depends_on 的限制

*【先搞清楚資料住在哪】*

## 容器可以砍掉重來，資料不行

> 🏠 **生活比喻**
>
> 容器像**飯店房間**：住客退房（容器刪掉）時，房間會被打掃乾淨，你留在桌上的東西全部消失。

映像檔的每一層都是唯讀的範本。容器跑起來之後新增、修改、刪除的檔案，全部落在**它自己那一層可寫空間**（正式名稱：容器層，container layer）。這一層的命運很單純：

##### 容器只是停掉

*   資料還在。容器本身沒被刪，那一層就還在。
*   `start` 回來，之前寫的檔案原封不動。

##### 容器被刪掉

*   那一層跟著消失，資料沒了。
*   而且這一層綁在單一容器上，別的容器接不過去。

所以資料庫的檔案、使用者上傳的東西、要留著查的紀錄，都不該只放在容器層。把容器想成可以隨時換的旅館房間：日用品放房裡沒差，重要行李要放進另外保管的置物櫃（正式名稱：持久化儲存）。

*【三種掛法】*

## 看資料要活多久，決定用哪一種

> 🏠 **生活比喻**
>
> 要保存的東西要放到**房間外面**：
> - 具名 Volume＝**飯店的寄物櫃**，飯店幫你管
> - Bind Mount＝**直接借用你自己家的抽屜**
> - tmpfs＝**便條紙**，關燈就沒了

| 方式 | 資料放哪、活多久 | 典型用途 |
| --- | --- | --- |
| 具名 Volume | Docker 自己管；容器刪了它還在 | 資料庫檔案、要跨容器接手的資料 |
| Bind Mount | 直接對到你主機上的某個路徑 | 開發中的程式碼、要在主機上編輯的設定檔 |
| tmpfs | 放在記憶體；容器停了就沒 | 不需要留下來的暫存資料 |

```
# 具名 Volume
docker container run -v app-data:/app/data myapp:1.0

# Bind Mount
docker container run -v /主機上的絕對路徑:/app/config myapp:1.0

# tmpfs
docker container run --tmpfs /app/cache myapp:1.0
```

具名 Volume 是保存資料的首選機制。[出處](https://docs.docker.com/engine/storage/volumes/)

*【具名 Volume】*

## 讓新容器接回同一份資料

> 🏠 **生活比喻**
>
> 換房間（新容器）時，只要**拿回同一個寄物櫃號碼**（掛同一個 Volume），東西都還在。

```
docker volume create app-data
docker volume ls
docker volume inspect app-data     # 看 Mountpoint 在哪

docker container run --name app-a -v app-data:/app/data myapp:1.0
docker container rm -f app-a
docker container run --name app-b -v app-data:/app/data myapp:1.0   # 資料還在
```

只要沒把 `app-data` 刪掉，第二個容器掛上去就接回同一份資料。這就是「容器可以換、資料自己活」的做法。

> 💡 一個容易中的坑：Dockerfile 裡寫了 `VOLUME ["/app"]`，但 `docker run` 的時候沒指定名字，Docker 每開一次容器就幫你生一個**隨機名字的 Volume**（正式名稱：匿名 Volume）。[出處](https://docs.docker.com/engine/storage/volumes/) 這樣很容易累積出一堆看不出用途的 Volume。解法是每次都用 `-v 名字:路徑` 明確命名。

`docker volume inspect` 印出來的 Mountpoint（通常長得像 `/var/lib/docker/volumes/app-data/_data`）是**那層 Linux 裡面的路徑**。在 Windows 和 macOS 上你用檔案總管或 Finder 找不到它，因為它在 Docker 那層 Linux 裡面。那一層是誰開的、長什麼樣，〈Docker Desktop 與 Colima〉會拆開。

> Volume 有自己的生命週期，但**它不是備份**。誤刪、磁碟壞掉、資料本身損毀，Volume 一樣救不了你。重要資料另外規畫備份和還原。

*【Bind Mount】*

## 把主機的資料夾直接借給容器

> 🏠 **生活比喻**
>
> Bind Mount 像**把自家書桌搬到飯店房間**：你在家改，房間裡馬上看到；房間裡改，家裡也跟著變。

舉個例子：本機沒裝 C 語言的編譯環境，但又想編一支 `hello.c`。做法是把目前目錄掛進一個裝好 gcc 的容器裡：

```
docker container run -it -v "$PWD":/root gcc:14 sh
# 在容器裡：gcc -o hello hello.c
# exit 之後，編好的 hello 就出現在你自己的資料夾裡
```

這一招的重點是**雙向**：主機改檔案，容器馬上看到；容器在掛載目錄裡產出的檔案，主機也看得到。開發流程很吃這個——程式碼留在主機上，編譯器和執行環境由容器提供。

> 💡 一個容易踩到的狀況：用 `-d` 跑 gcc 容器，容器立刻退出了。原因是〈Docker 上手〉那條規則——容器的命綁在主程式上，gcc 映像檔的預設指令跑完就結束了。要停在裡面操作就得用 `-it`。

Bind Mount 的代價是綁死主機：路徑要存在、權限要對，而且 Windows 和 macOS、Linux 的路徑寫法不一樣。只是要保存應用程式資料的話，具名 Volume 比較好搬。另外，掛載會**蓋住**容器裡那個路徑原本的內容——拿空資料夾掛到本來有檔案的目錄，看起來像檔案不見了，其實只是被蓋住。

*【Compose】*

## 一長串參數，改成一份看得懂的檔案

> 🏠 **生活比喻**
>
> Compose 像一張**整桌宴席的菜單**：網站、資料庫、快取各一道，每道的做法都寫好，一聲令下整桌一起上。

一個應用程式常常不只一個容器：網站一個、資料庫一個、快取一個，每個都有自己的環境變數、埠號和掛載設定。全部用 `docker run` 打，遲早漏參數。Compose 讓你把這些寫進一份 YAML：

```
services:
  web:
    image: myapp:1.0
    ports:
      - "8080:8080"
    environment:
      DB_HOST: db
    depends_on:
      - db

  db:
    image: mysql:8.4
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
    volumes:
      - db-data:/var/lib/mysql

volumes:
  db-data:
```

`services` 底下的 `web` 和 `db` 是服務名稱。**同一個 Compose 專案裡的服務可以直接用服務名稱找到對方**，所以應用程式的資料庫主機就填 `db`。最下面的 `volumes` 宣告一個叫 `db-data` 的具名 Volume，再由資料庫服務掛上去。

密碼那行用 `${MYSQL_ROOT_PASSWORD}` 代進來，不要把真的密碼寫死在 Compose 檔裡，含密碼的檔案也不要進版控。

*【Compose 操作】*

## 起、看、收

> 🏠 **生活比喻**
>
> `up`＝開席、`ps / logs`＝看看每道菜狀況、`down`＝收桌。
> `docker-compose`（中間有連字號）是**舊版菜單格式**，`docker compose` 是新版。

```
docker compose config    # 先把設定解析出來看一遍
docker compose up -d     # 背景把整組起起來
docker compose ps        # 看狀態
docker compose logs -f   # 跟著看紀錄
docker compose down      # 收掉這個專案的容器和網路
```

你會看到兩種寫法：`docker-compose up`（中間有連字號）和 `docker compose up`。它們是兩代東西：Compose v1 用 Python 寫、指令是 `docker-compose`；v2 用 Go 重寫、變成 `docker` 的子指令 `docker compose`。[出處](https://docs.docker.com/compose/intro/history/) 現在用的是後者，打指令時用有空格的那個寫法。

`docker compose down` 會收掉容器和網路，**但預設不會刪具名 Volume**，要加 `--volumes`（`-v`）這個旗標才刪。[出處](https://docs.docker.com/reference/cli/docker/compose/down/) 所以重新 `up` 通常接得回原本的資料；反過來說，手滑加了 `-v`，資料就可能救不回來。

> 💡 `depends_on` 保證不了「資料庫已經可以接查詢了」。啟動時 Compose 不會等到容器「就緒」，只等到它「在跑」。[出處](https://docs.docker.com/compose/how-tos/startup-order/) 要真的等，得搭配健康檢查（`healthcheck`）加上 `condition: service_healthy`；就算這樣，應用程式自己也該會重試。

*【跨機器】*

## 本機那一套，多台機器就不夠用了

> 🏠 **生活比喻**
>
> 寄物櫃只在這間飯店有效。開了分館要共用同一批東西，就要改用**中央倉庫**（網路儲存）。

具名 Volume 和 Bind Mount 都在**同一台主機上**。一旦有第二台機器也要讀同一份資料，就得換成別的 Volume 驅動程式（volume driver，決定 Volume 實際存在哪裡的外掛），例如透過 SSH 掛遠端檔案系統，或用雲端的儲存服務。

換上去之後要重新評估的東西不少：一致性、效能、權限、備份。再往下就換一個層次了——那是 Kubernetes 的 PVC（一張「我要一塊儲存空間」的申請單）在處理的事，〈OpenShift 部署實戰〉會碰到。

| 需求 | 選哪個 | 為什麼 |
| --- | --- | --- |
| 資料庫檔案要跨容器保存 | 具名 Volume | 生命週期不綁單一容器 |
| 本機改程式碼、容器負責跑 | Bind Mount | 主機和容器共用同一個目錄 |
| 只在執行期間用的暫存 | tmpfs | 停掉就丟，也不用寫進硬碟 |
| 多個服務要一起起來 | Compose | 把服務關係和參數集中成一份檔案 |
| 多台主機共用同一份資料 | 本機 Volume 不夠 | 要換 volume driver 或外部儲存服務 |

### 🗺️ 比喻對照表

| 技術名詞 | 生活比喻 |
| --- | --- |
| 容器層 | 飯店房間，退房就清空 |
| Volume | 飯店寄物櫃 |
| Bind Mount | 把自家書桌搬進房間 |
| Compose | 整桌宴席菜單 |
| up / down | 開席 / 收桌 |

### 重點整理

*   容器停掉，那層可寫空間還在；容器刪掉，它才跟著消失。
*   具名 Volume 放要留的資料、Bind Mount 借主機目錄給容器、tmpfs 放丟得掉的暫存。
*   Dockerfile 寫了 VOLUME 但 run 的時候沒取名字，會一直生出匿名 Volume。
*   Volume 和容器的生命週期分開，但 Volume 不是備份。
*   `docker compose down` 預設不刪具名 Volume；加 `-v` 才刪。
*   `depends_on` 只等到「在跑」，不等到「可以用」——要就緒保證得配健康檢查，應用程式也該會重試。

## 隨堂測驗

**Q1. 容器被 stop 但沒有 rm，它那層可寫空間裡的檔案會怎樣？**

- (A) 還在，因為容器本身還沒被刪掉
- (B) 立刻被搬到 registry 保存
- (C) 自動轉存成一個具名 Volume
- (D) 在停止的當下就消失

<details><summary>看答案</summary>

**答案：(A)** stop 只結束程式；那層跟著容器走，容器還在就還在。

</details>

**Q2. 資料庫的檔案要能在舊容器刪掉之後交給新容器繼續用，最適合哪一種？**

- (A) 具名 Volume
- (B) 容器自己那層可寫空間
- (C) tmpfs
- (D) 建置快取

<details><summary>看答案</summary>

**答案：(A)** 具名 Volume 的生命週期跟容器分開，換容器掛回同一個名字就接得回來。

</details>

**Q3. 開發時想「在主機上改程式碼，容器裡馬上看到同一份檔案」，該用哪一種掛法？**

- (A) Bind Mount
- (B) 具名 Volume
- (C) tmpfs
- (D) 多階段建置

<details><summary>看答案</summary>

**答案：(A)** Bind Mount 直接把主機上指定的路徑掛進容器，兩邊看到的是同一份。

</details>

**Q4. Dockerfile 裡寫了 VOLUME ["/app"]，但每次 docker run 都沒指定名字，會發生什麼？**

- (A) 每開一個容器就多一個隨機名字的匿名 Volume，久了看不出哪個是哪個
- (B) Docker 會拒絕啟動容器
- (C) 所有容器自動共用同一個叫 app 的 Volume
- (D) 資料會直接寫進映像檔的唯讀層

<details><summary>看答案</summary>

**答案：(A)** 沒給名字系統就隨機配一個；要重複接回同一份資料就得用 -v 名字:路徑。

</details>

**Q5. 為什麼「有 Volume」不等於「有備份」？**

- (A) Volume 一樣會被誤刪、可能隨磁碟故障或資料損毀而遺失
- (B) Volume 在容器停止時一定會自動清空
- (C) Volume 只存得下設定檔，存不了資料庫檔案
- (D) Volume 每次掛載都會被映像檔的內容覆寫

<details><summary>看答案</summary>

**答案：(A)** 獨立的生命週期只解決「換容器」這件事，不解決「東西壞掉或刪錯」。

</details>

**Q6. Compose 檔最下面那個頂層的 volumes: db-data: 在做什麼？**

- (A) 宣告一個具名 Volume，讓下面的服務可以掛載它
- (B) 建立一個叫 db-data 的容器
- (C) 把資料庫映像檔推上 registry
- (D) 限制所有服務只能用記憶體檔案系統

<details><summary>看答案</summary>

**答案：(A)** 頂層 volumes 負責宣告，服務再在自己的設定裡掛上去。

</details>

**Q7. 執行 docker compose down 之後，具名 Volume 裡的資料預設會怎樣？**

- (A) 留著——要加 --volumes（-v）才會一起刪掉
- (B) 一定會被刪掉，沒有辦法保留
- (C) 會被自動匯出成 tar 檔
- (D) 會被移到另一個 Compose 專案底下

<details><summary>看答案</summary>

**答案：(A)** down 預設收的是容器和網路；刪 Volume 是另外那個旗標的事。

</details>

**Q8. 關於 Compose 的 depends_on，哪一句是對的？**

- (A) 它只等到相依的容器「在跑」，不等到「可以用」，應用程式仍需要重試或搭配健康檢查
- (B) 它保證資料庫已經完成初始化並能接受任何查詢
- (C) 它會把兩個服務合併成同一個容器
- (D) 它會自動替相依的服務建立備份

<details><summary>看答案</summary>

**答案：(A)** Compose 不會等到容器 ready，只等到它 running。

</details>

**Q9. docker-compose 和 docker compose（中間沒有連字號）差在哪？**

- (A) 前者是用 Python 寫的 Compose v1，後者是用 Go 重寫、變成 docker 子指令的 v2
- (B) 前者用來啟動、後者用來停止
- (C) 前者給 Linux 用、後者給 macOS 用
- (D) 兩者完全一樣，只是打法不同沒有任何區別

<details><summary>看答案</summary>

**答案：(A)** 現在用的是 v2 的 docker compose（中間是空格）。

</details>

**Q10. 多台主機上的容器要共用同一份資料，本機的具名 Volume 為什麼不夠？**

- (A) 具名 Volume 存在單一主機上，跨機器要換 volume driver 或外部儲存服務
- (B) 具名 Volume 一次只能被一個容器掛載
- (C) 具名 Volume 的容量上限固定是 1 GB
- (D) 具名 Volume 不支援資料庫類型的檔案

<details><summary>看答案</summary>

**答案：(A)** 跨機器之後還得重新評估一致性、效能、權限和備份——這已經是另一個層次的問題。

</details>
