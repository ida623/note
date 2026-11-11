# 15. 映像檔與 Dockerfile

> 🏠 **生活化版本**：每個段落開頭的「生活比喻」先用日常情境帶你抓到感覺，接著再看原本的技術說明與程式碼；篇末有「比喻對照表」可以快速複習。

> 來源：[筆記平台 · 容器與 Kubernetes](https://hhtim.github.io/notes-platform/k8s/#/lesson/docker-images)　第 15 課 / 共 23 課 · 約 13 分鐘

**把環境寫成一個檔案：指令分工、快取順序、多階段建置。**

### 讀完這課你會

*   用三種方式拿到映像檔，知道為什麼刪不掉
*   看懂 Dockerfile 指令，分清 CMD 與 ENTRYPOINT
*   用指令順序與 .dockerignore 讓重建變快
*   用多階段建置不讓編譯工具跟著出貨

*【拿到映像檔】*

## 三條路：下載、自己做、離線搬

> 🏠 **生活比喻**
>
> 拿到料理包有三種方式：**去超市買**（pull）、**自己照食譜做**（build）、**朋友用保冷袋帶過來**（save / load）。
> 刪不掉料理包，通常是因為**還有盤子在用它**（容器還存在）。

映像檔和容器的關係見〈Docker〉（食譜、成品、跑起來的那一份）。

| 方式 | 什麼時候用 | 指令 |
| --- | --- | --- |
| 從 registry 下載 | 拿現成的（公開或公司內部的） | `docker image pull nginx:1.27` |
| 用 Dockerfile 做 | 把自己的程式包成映像檔 | `docker image build -t myapp:1.0 .` |
| 從檔案匯入 | 連不上 registry，只能請別人給你一包 | `docker image load -i nginx.tar` |

```
docker image ls                    # 看目前有哪些
docker image inspect nginx:1.27    # 看細節：CPU 架構、基於哪個系統
docker image rm nginx:1.27         # 刪掉
```

> 💡 刪不掉的時候先看有沒有容器在用它。**容器只是停掉還不夠**——只要那個容器還存在，它跟映像檔的關係就還在，得先把容器 `rm` 掉，映像檔才刪得動。

*【離線搬運】*

## save 和 load 要成對

> 🏠 **生活比喻**
>
> save＝**打包進保冷袋**，load＝**到另一邊拆開放進冰箱**；沒網路的地方就靠這招手提過去。

```
# 匯出成一個檔
docker image save nginx:1.27 -o nginx.tar

# 在另一台匯入
docker image load -i nginx.tar
```

`save` 把映像檔的每一層和它的設定打包起來，`load` 在另一邊還原。網路連不到 registry 的環境就靠這一招。

另外還有一招是 `docker container commit`：進到容器裡改東西，再把當下的狀態存成新的映像檔。**能用，但別當常態**。這樣做出來的映像檔沒有配方，別人看不出你改了什麼，下次也重現不出來。正式的做法是把每個步驟寫進 Dockerfile。

*【第一份配方】*

## Dockerfile 就是一張純文字的施工單

> 🏠 **生活比喻**
>
> `-t` 是**貼標籤**寫上名字和版本；最後那個 `.` 是**告訴廚師食材放在哪個籃子**（build context），只有籃子裡的東西拿得到。

```
FROM nginx:1.27-alpine
COPY index.html /usr/share/nginx/html/index.html
```

```
docker image build -t my-nginx:1.0 .
docker container run -d --name my-nginx -p 8080:80 my-nginx:1.0
```

`-t my-nginx:1.0` 是給成品取名字加標籤；最後那個 `.` 是**建置內容（build context）**——你告訴 Docker「這個資料夾裡的檔案我建的時候要用得到」，`COPY` 就是從這裡面撈。

> 💡 同一個 `-t`，在不同指令裡是不同意思：`docker build -t` 的 t 是 tag（標籤），`docker run -t` 的 t 是 tty（配一個偽終端機給容器）。[出處](https://docs.docker.com/reference/cli/docker/container/run/)

*【指令各管什麼】*

## 九個常用指令的分工

> 🏠 **生活比喻**
>
> - FROM＝選**基底高湯**
> - RUN＝**備料步驟**
> - COPY＝**把食材放進鍋**
> - CMD / ENTRYPOINT＝**上桌時要做的動作**
> - EXPOSE＝**標示出餐口位置**
>
> 用 `latest` 像跟店家說「給我最新的」，每次拿到的可能不一樣。

| 指令 | 做什麼 | 要注意 |
| --- | --- | --- |
| `FROM` | 從哪個映像檔開始疊 | 官方的優先，而且要指定版本，別用 latest |
| `WORKDIR` | 設定後面指令的工作目錄 | 目錄不存在會自己建 |
| `COPY` | 把建置內容裡的檔案複製進去 | 一般複製都用它 |
| `ADD` | 複製，而且會自動解開壓縮檔 | 真的需要那個「自動」時才用 |
| `RUN` | 建的時候執行指令（裝套件之類） | 每一行 RUN 都疊一層，能合併就合併 |
| `ENV` | 設環境變數 | 會留在映像檔裡，容器跑起來還讀得到 |
| `ARG` | 設建置參數 | 建完就沒了，容器裡看不到 |
| `CMD` | 容器啟動時的預設指令或預設參數 | 會被 `docker run` 後面接的指令蓋掉 |
| `ENTRYPOINT` | 固定要執行的那支主程式 | 常跟 CMD 搭配，一個當工具一個當參數 |

挑基礎映像檔的通則是：官方映像優先、固定版本不要用 `latest`、盡量挑體積小的。再進一步：標籤是會被發佈者改掉的（mutable），要保證每次拿到完全一樣的東西，最保險的做法是釘內容摘要（digest）而不是標籤。[出處](https://docs.docker.com/build/building/best-practices/)

另外有一個順序上的坑：**ARG 是唯一可以寫在 FROM 前面的指令**，ENV 不行[出處](https://docs.docker.com/reference/dockerfile/)。而且寫在 FROM 前面的 ARG 只能用在 FROM 那一行，要在後面用得再宣告一次。

> 📝 查證更正：原筆記第四章的 Spring Boot 範例把三行 ARG 和三行 ENV 寫在 FROM 之前，查證後更正：Docker 官方文件明寫「ARG is the only instruction that may precede FROM in the Dockerfile」，ENV 不能放在 FROM 前面

*【最容易搞混的兩組】*

## ARG 對 ENV：差在活多久

> 🏠 **生活比喻**
>
> - ARG＝**做菜時才用的便條**，料理包封好就丟掉
> - ENV＝**印在料理包上的說明**，加熱時還看得到

兩個都是設變數，差別在**作用時間**，不是型別。做個實驗就看得很清楚：兩份 Dockerfile 分別用 ARG 和 ENV 設同一個版本號，build 出來的映像檔跑起來版本都對；但進到容器裡打 `env`，只有 ENV 那個看得到變數，ARG 那個找不到。

```
# 建的時候用，建完就消失
ARG VERSION=2.0.1
RUN wget https://example.com/tool-${VERSION}.tar.gz

# 建的時候和跑的時候都在，會留在映像檔裡
ENV TZ=Asia/Taipei
```

不改 Dockerfile 也能換 ARG 的值：

```
docker image build -t myapp:2.0.0 --build-arg VERSION=2.0.0 .
```

正因為 ENV 會跟著映像檔留下來，密碼、權杖這種東西不要用 ENV 寫死在 Dockerfile 裡——拿到映像檔的人就讀得到。敏感資料交給專門的機密管理機制處理。

#### CMD 對 ENTRYPOINT：一個會被蓋掉，一個不會

CMD 設的是**預設**指令：`docker run` 後面如果你接了別的指令，CMD 就被忽略。ENTRYPOINT 設的則是那支**主程式**：`docker run` 後面接的東西會變成它的參數，蓋不掉它。真要整個換掉得另外加 `--entrypoint`，它會蓋掉映像檔預設的 ENTRYPOINT。[出處](https://docs.docker.com/reference/cli/docker/container/run/)

```
FROM alpine:3.20
ENTRYPOINT ["echo"]
CMD ["hello"]
```

直接跑，印出 `hello`；後面接 `world`，CMD 的預設參數被換掉，變成印 `world`。把 ENTRYPOINT 想成固定的工具、CMD 想成工具預設帶的參數，這組搭配就通了。

Dockerfile 裡只能有一個 CMD 生效：列了多個 CMD，只有最後一個算數。[出處](https://docs.docker.com/reference/dockerfile/) 還有一個狀況要知道：什麼 CMD 都沒寫時，容器啟動會沿用基礎映像檔（`FROM` 那個）自己帶的預設指令。

*【建快一點】*

## 常改的放後面，不該送的別送

> 🏠 **生活比喻**
>
> 像**疊千層蛋糕**：改了某一層，它上面的每一層都得重做。所以不常變的（裝套件）放下面，常改的（程式碼）放最上面。
> `.dockerignore`＝**不要把垃圾桶也一起放進籃子**。

映像檔是一層一層疊的，**某一層的快取失效，它後面每一層都要重建**。所以把變動少的步驟放前面、常改的程式碼放最後：

```
FROM python:3.12-slim
WORKDIR /app

# 變動少：先裝相依套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 變動多：最後才複製程式碼
COPY app.py .
CMD ["python", "app.py"]
```

這樣改 `app.py` 的時候，裝套件那一層的快取還留得住。反過來把 `COPY app.py` 放在裝套件前面，每改一次程式碼，連裝套件都要重跑一次。

另一個省時間的地方是建置內容。`.` 代表「整個目前目錄打包送給 Docker」，但你的 Dockerfile 可能只 COPY 一個檔。用 `.dockerignore` 把不用送的排掉：

```
.git/
.venv/
__pycache__/
*.log
```

另外兩條建置建議：`apt-get update` 要和 `apt-get install` 寫在同一個 RUN 裡（避免用到過期的套件清單），以及用 `.dockerignore` 排掉跟建置無關的檔案。[出處](https://docs.docker.com/build/building/best-practices/)

*【縮小成品】*

## 多階段建置：鷹架不要跟著交屋

> 🏠 **生活比喻**
>
> 蓋房子要**鷹架**（編譯器），但交屋時要拆掉。多階段建置就是第一段蓋房、第二段只把房子搬給屋主。

編譯器就像蓋房子的鷹架——蓋的時候要，住進去不需要。多階段建置的做法是：第一段用有編譯器的映像檔編出成品，第二段換一個精簡的映像檔，只把成品搬過去。

```
FROM gcc:14 AS builder
WORKDIR /src
COPY hello.c .
RUN gcc --static -o hello hello.c

FROM alpine:3.20
COPY --from=builder /src/hello /usr/local/bin/hello
ENTRYPOINT ["/usr/local/bin/hello"]
```

最終的映像檔只有最後那一段，加上你明確搬進去的東西。拿同一份 C 程式對照就很明顯：直接用 gcc 映像檔出貨的成品很肥，改成兩段之後小非常多。

換基礎映像檔的時候記得確認 CPU 架構和系統函式庫對得上——用 `docker image inspect` 看 `Architecture` 和 `Os` 兩個欄位。

*【分享出去】*

## 重新標記，再推上 registry

> 🏠 **生活比喻**
>
> 推上 Docker Hub 像**寄包裹**：要寫上**收件人帳號**（`帳號/名稱:版本`），沒寫的話郵局以為你要寄給官方，當然被退件。

```
docker image tag myapp:1.0 你的帳號/myapp:1.0
docker login
docker image push 你的帳號/myapp:1.0
```

這裡很容易卡一次：直接 `docker image push hello:1.0` 會失敗。Docker Hub 的命名規則是——**沒有帳號前綴的名字（像 `nginx:latest`）是保留給官方映像檔的**，你自己的要寫成 `帳號/名稱:標籤`。

`tag` 不會複製一整份，它只是給同一包內容再掛一個名字。推之前確認 registry 位址和登入權限；登入憑證不要寫進 Dockerfile。

### 🗺️ 比喻對照表

| 技術名詞 | 生活比喻 |
| --- | --- |
| pull / build / load | 超市買 / 自己做 / 保冷袋帶來 |
| build context | 廚師拿得到的食材籃 |
| Layer 快取 | 千層蛋糕，改下層上面全重做 |
| 多階段建置 | 交屋前拆鷹架 |
| ARG / ENV | 做菜便條 / 包裝上的說明 |
| registry push | 寄包裹要寫收件人 |

### 重點整理

*   映像檔三條來路：從 registry 下載、用 Dockerfile 建、從封存檔匯入；容器還在（就算停掉）就刪不掉它用的映像檔。
*   commit 出來的映像檔沒有配方，正式專案要把步驟寫進 Dockerfile。
*   ARG 建完就消失、ENV 會留在映像檔裡；只有 ARG 能寫在 FROM 前面。
*   CMD 會被 docker run 後面的指令蓋掉，ENTRYPOINT 不會（真要換得加 `--entrypoint`）；兩個搭配＝固定工具＋預設參數。
*   某一層快取失效，後面全部重建——所以常改的程式碼放最後；`.dockerignore` 減少送進去的檔案。
*   多階段建置：編譯器留在第一段，最終成品只帶走編好的東西。

## 隨堂測驗

**Q1. 映像檔刪不掉，錯誤訊息說有容器在用它。你已經把那個容器 stop 了，為什麼還是刪不掉？**

- (A) 容器只是停掉、還存在，跟映像檔的關係就還在，要先把容器 rm 掉
- (B) 停掉的容器會把映像檔鎖成唯讀，要重開機才解得開
- (C) 要先把映像檔推上 registry 才刪得掉
- (D) 映像檔一旦被 pull 下來就不能刪除

<details><summary>看答案</summary>

**答案：(A)** stop 只是結束程式；容器本身還在，參照就還在。

</details>

**Q2. 要把映像檔帶到連不上 registry 的環境，該用哪一組？**

- (A) docker image save 匯出，再用 docker image load 匯入
- (B) docker image push 匯出，再用 docker container start 匯入
- (C) docker container export 匯出，再用 docker image pull 匯入
- (D) docker image inspect 匯出，再用 docker image tag 匯入

<details><summary>看答案</summary>

**答案：(A)** save 把每一層和設定打包成一個檔，load 在另一邊還原。

</details>

**Q3. docker image build -t myapp:1.0 . 最後那個句點代表什麼？**

- (A) 把目前這個目錄當成建置內容，COPY 就從這裡面撈檔案
- (B) 表示用匿名標籤，不指定名稱
- (C) 表示從目前正在跑的容器建出映像檔
- (D) 表示建完直接推到預設的 registry

<details><summary>看答案</summary>

**答案：(A)** 句點指的是 build context 的位置，不是 Dockerfile 的檔名。

</details>

**Q4. ARG 和 ENV 最主要的差別是什麼？**

- (A) ARG 只在建置期間有效、建完就消失；ENV 會留在映像檔裡，容器跑起來還讀得到
- (B) ARG 只能放數字，ENV 只能放文字
- (C) ARG 用來掛載目錄，ENV 用來對應連接埠
- (D) ARG 會自動加密，ENV 只做雜湊

<details><summary>看答案</summary>

**答案：(A)** 進到容器裡打 env，看得到的是 ENV 設的那些，ARG 的找不到。

</details>

**Q5. 在 Dockerfile 裡，哪一個指令可以寫在 FROM 前面？**

- (A) 只有 ARG
- (B) ARG 和 ENV 都可以
- (C) 只有 ENV
- (D) RUN、ARG、ENV 都可以

<details><summary>看答案</summary>

**答案：(A)** ARG 是唯一能出現在 FROM 之前的指令，而且它只能用在 FROM 那一行。

</details>

**Q6. ENTRYPOINT ["echo"] 搭配 CMD ["hello"]，執行時在後面接了 world，結果會印出什麼？**

- (A) world——CMD 的預設參數被換掉了，ENTRYPOINT 照樣執行
- (B) hello——ENTRYPOINT 會擋掉所有後面接的參數
- (C) hello world——兩者會串在一起
- (D) 什麼都不印，因為兩個指令衝突

<details><summary>看答案</summary>

**答案：(A)** ENTRYPOINT 是固定要跑的工具，CMD 是它預設帶的參數，而參數可以被換掉。

</details>

**Q7. 為什麼建議先 COPY requirements.txt 裝套件、最後才 COPY 程式碼？**

- (A) 某一層快取失效後面全部要重建，把常改的放最後才留得住裝套件那層的快取
- (B) Dockerfile 規定 Python 檔案一定要最後複製
- (C) requirements.txt 必須成為容器的主程式
- (D) 這樣程式碼才會自動變成環境變數

<details><summary>看答案</summary>

**答案：(A)** 相依套件變動少、程式碼變動多，順序反過來會每次都重裝一次。

</details>

**Q8. .dockerignore 的用途是什麼？**

- (A) 把不需要送進建置內容的檔案和目錄排掉
- (B) 禁止容器讀取所有環境變數
- (C) 忽略登入 registry 時的失敗
- (D) 讓 Docker 跳過所有 RUN 指令

<details><summary>看答案</summary>

**答案：(A)** 建置內容是整包送給 Docker 的，排掉不相關的東西可以變快、也避免不小心被 COPY 進去。

</details>

**Q9. 多階段建置能把最終映像檔縮小，關鍵是什麼？**

- (A) 最後那一段只收你明確搬過去的成品，不必把整套編譯工具一起打包
- (B) 它會把所有檔案改存到主機的記憶體檔案系統
- (C) 它會自動刪掉應用程式執行時需要的相依套件
- (D) 它會把多個標籤合併成同一個

<details><summary>看答案</summary>

**答案：(A)** 編譯器留在第一段，第二段換精簡的基礎映像檔，只 COPY --from 搬編好的東西。

</details>

**Q10. docker image push hello:1.0 推到 Docker Hub 失敗，最可能的原因是什麼？**

- (A) 沒有帳號前綴的名字是保留給官方映像檔的，自己的要寫成「帳號/名稱:標籤」
- (B) 標籤裡不能出現小數點
- (C) 映像檔一定要先 save 成檔案才能 push
- (D) 只有多階段建置出來的映像檔才准 push

<details><summary>看答案</summary>

**答案：(A)** 先用 docker image tag 重新掛一個帶帳號前綴的名字，再 push。

</details>
