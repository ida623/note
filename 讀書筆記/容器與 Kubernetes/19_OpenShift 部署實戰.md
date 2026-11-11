# 19. OpenShift 部署實戰

> 來源：[筆記平台 · 容器與 Kubernetes](https://hhtim.github.io/notes-platform/k8s/#/lesson/k8s-openshift)　第 19 課 / 共 23 課 · 約 15 分鐘

**設定、儲存、工作負載、服務、對外入口，一層一層接起來。**

### 讀完這課你會

*   說出 OpenShift 跟 Kubernetes 的關係與 Route
*   依相依關係一層一層接起整套服務
*   知道任意使用者身分會讓哪些映像檔掛掉
*   照由內往外的順序排錯

*【先看全景】*

## OpenShift 是 Kubernetes 加上一層平台

Red Hat OpenShift Container Platform（常縮寫成 OCP）核心就是 Kubernetes，上面再補開發、路由、安全和維運的整合。所以 Pod、Deployment、Service 這些物件幾乎全部通用，指令從 `kubectl` 換成 `oc`（`oc` 也吃大部分 `kubectl` 的用法）。

最明顯的多出來的東西是 **Route**：OpenShift 自己的對外 HTTP／HTTPS 入口。〈對外入口〉講的 Ingress 在 OpenShift 上一樣能用，而 Red Hat 自己的文件與範例用的是 Route。

例子是一個部落格網站（WordPress）＋一個資料庫（MySQL）＋一個快取（Redis）。

```
外部使用者
    ↓ HTTPS
Route
    ↓
網站的 Service
    ↓
網站的 Pod
   ↙         ↘
資料庫 Service   快取 Service
    ↓             ↓
資料庫 Pod      快取 Pod
    ↓             ↓
   PVC           PVC
```

Deployment、Service、ConfigMap、Secret 的基本觀念見〈Deployment：下單〉〈Service：找路〉〈對外入口〉與〈K8s 上手：Minikube 與上雲〉。

*【先畫相依，再套用】*

## 建立順序，跟「能不能用」是兩件事

照這個順序做，少踩坑：

*   先確認你在哪個專案（OpenShift 的 project 就是 Kubernetes 的命名空間）、配額還剩多少、有哪些儲存類別可用。
*   建 ConfigMap、Secret、PVC——後面的東西會引用它們。
*   建工作負載：快取 → 資料庫 → 網站。
*   等 Pod 通過就緒檢查。
*   建 Service，再建 Route。
*   由內往外測：Pod → Service → Route。

```
oc project            # 現在在哪個專案
oc get resourcequota  # 這個專案還剩多少額度
oc get storageclass   # 有哪些儲存類別可以用
```

> 💡 **套用 YAML 的先後順序，不等於應用程式的啟動順序**。Kubernetes 是非同步調和的（〈為什麼需要 Kubernetes〉那個迴圈），你先建資料庫不代表網站起來時資料庫已經能接查詢。真正的保證來自就緒檢查（readiness probe）和應用程式自己的重試——這和〈資料與 Compose〉講的 Compose `depends_on` 是同一個道理。

*【設定與密碼】*

## 引用的時候，名字和鍵值都要一模一樣

```
apiVersion: v1
kind: ConfigMap
metadata:
  name: blog-config
data:
  DB_NAME: blog
  DB_USER: blog_user
  CACHE_HOST: cache
---
apiVersion: v1
kind: Secret
metadata:
  name: blog-secret
type: Opaque
stringData:
  DB_PASSWORD: 換成你自己的強密碼
  ADMIN_PASSWORD: 換成你自己的強密碼
```

工作負載用 `configMapKeyRef` 或 `secretKeyRef` 把單一欄位取出來當環境變數。**引用時的 `name`（哪個 ConfigMap／Secret）和 `key`（裡面哪一個欄位）要和上面完全一致**，錯一個字 Pod 就起不來。

Secret 預設沒有加密這件事〈K8s 上手：Minikube 與上雲〉講過，在 OpenShift 上一樣成立。密碼請用佔位字串進版控、實際值另外注入；教學範例常見的 `rootpass`、`wppass` 這種明碼寫法是為了講解方便，不是可以照抄的做法。

還有一個寫法會讓人踩空：用 `cat << 'EOF' | oc apply -f -` 送 YAML，裡面寫 `namespace: $PROJECT_NAME` 想代入專案名稱。但 here-document 的結束字（這裡是 `EOF`）**只要加了引號，裡面的內容就不會做變數展開**，那一行會原封不動送出去。[出處](https://www.gnu.org/software/bash/manual/bash.html#Here-Documents) 比較單純的做法是 YAML 裡乾脆不寫 `namespace`，先用 `oc project` 切到對的專案再套用。

*【儲存】*

## PVC 是「我要一塊空間」的申請單

```
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: database-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
```

這又是〈單子與執行者〉那個模式：PVC 是單子，平台負責去生出真的儲存空間來滿足它。資料庫和網站內容各開一張，快取要不要開則看情況——它只是重建得回來的快取，還是裡面有不能掉的資料？**不要因為「這是有狀態的服務」就一律給它一張。**

> 💡 PVC 一直卡在 Pending，優先查四件事：儲存類別（StorageClass）存不存在、存取模式（accessModes）平台支不支援、容量夠不夠、專案配額還有沒有。第一種特別容易中——抄來的範例寫了某個雲端專屬的儲存類別，但你這個環境沒有。

YAML 裡省略 `storageClassName` 時，會不會自動用預設的儲存類別，取決於叢集有沒有設預設值。省略之前先用 `oc get storageclass` 看一眼。

*【工作負載】*

## 把資料庫的位置注入網站

**下面這份 YAML 的環境變數名稱（`WORDPRESS_DATABASE_*`）和 8080 這個埠，是照 Bitnami 版 WordPress 映像的規格寫的**。換成 Docker Hub 上的官方 `wordpress` 映像就不通——它吃的是 `WORDPRESS_DB_HOST`、`WORDPRESS_DB_USER`、`WORDPRESS_DB_PASSWORD`、`WORDPRESS_DB_NAME`，而且它聽的是 **80**（官方範例寫 `-p 8080:80`）。[出處](https://hub.docker.com/_/wordpress) 80 落在 1024 以下的特權埠，正好踩到下一段講的那一條，在 OpenShift 上起不來。**換映像檔就要去讀那個映像檔自己的文件，把變數名和埠號對過一遍。**

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: blog
spec:
  replicas: 1
  selector:
    matchLabels:
      app: blog
  template:
    metadata:
      labels:
        app: blog
    spec:
      containers:
        - name: blog
          image: 你的registry/wordpress:釘死的版本
          ports:
            - name: http
              containerPort: 8080
          env:
            - name: WORDPRESS_DATABASE_HOST
              value: database          # ← 就是 Service 的名字
            - name: WORDPRESS_DATABASE_NAME
              valueFrom:
                configMapKeyRef:
                  name: blog-config
                  key: DB_NAME
            - name: WORDPRESS_DATABASE_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: blog-secret
                  key: DB_PASSWORD
          readinessProbe:
            httpGet:
              path: /
              port: http
            initialDelaySeconds: 15
            periodSeconds: 5
          resources:
            requests:
              cpu: 100m
              memory: 256Mi
            limits:
              cpu: 500m
              memory: 512Mi
```

注意 `WORDPRESS_DATABASE_HOST` 填的是 `database`——那是**資料庫 Service 的名字**，不是任何一個 Pod 的位址。這正是〈Service：找路〉講的「永遠不變的名字」實際用起來的樣子。

> 💡 就緒檢查（readinessProbe）和存活檢查（livenessProbe）的分工不要搞混：**就緒檢查決定要不要把流量送進來，存活檢查決定要不要把它砍掉重開**。路徑、等待時間、逾時都要照那個映像檔真正的啟動行為調，抄別人的數字常常不合用。

#### 映像檔的三個坑

第一個坑是映像檔搬家了。Bitnami 已經公告從 2025 年 8 月 28 日起，把 `docker.io/bitnami` 底下的既有映像（含各版本標籤）搬到 `docker.io/bitnamilegacy`，那邊不再更新也不再支援，只給你暫時遷移用[出處](https://github.com/bitnami/containers/issues/83267)。所以 `bitnami/wordpress`、`bitnami/mysql`、`bitnami/redis` 這類舊名稱照抄下去，現在可能拉不下來。要沿用的話請先確認目前還提供哪些映像與標籤。

> 📝 查證更正：原筆記用 bitnami/wordpress:latest、bitnami/mysql:5.7、bitnami/redis:7.0 這幾個映像檔，查證後更正：Bitnami 官方公告自 2025 年 8 月 28 日起，把 docker.io/bitnami 底下既有的容器映像（含各版本標籤）搬到 docker.io/bitnamilegacy，該處不再更新也不再支援，只供暫時遷移使用

第二個坑是身分：**OpenShift 會用一個隨機指定的、非 root 的使用者編號來跑你的容器**。所以映像檔要這樣做：容器裡會被寫入的目錄和檔案，要屬於 root 群組且該群組可讀寫，映像檔的 `USER` 也該寫數字而不是名字。[出處](https://docs.redhat.com/en/documentation/openshift_container_platform/4.20/html/images/creating-images) 這也解釋了一個常見疑問：**為什麼這類映像檔聽的是 8080 而不是 80**：容器裡的程序不是以特權使用者的身分在跑，不能聽特權埠（1024 以下的埠）。假設自己一定是 root、或假設某個目錄一定寫得進去的映像檔，在 OpenShift 上就會起不來。

第三個坑是標籤會變：正式環境不要用 `latest`。標籤是可以被發佈者改掉的，同一個名字下次拉到的可能是不同內容，稽核和重現都會出問題。[出處](https://docs.docker.com/build/building/best-practices/)

*【內部連線】*

## Service 的名字就是叢集內的地址

```
apiVersion: v1
kind: Service
metadata:
  name: blog
spec:
  selector:
    app: blog
  ports:
    - name: http
      port: 80
      targetPort: http
---
apiVersion: v1
kind: Service
metadata:
  name: database
spec:
  selector:
    app: database
  ports:
    - name: mysql
      port: 3306
      targetPort: 3306
```

網站連 `database:3306`，實際上是靠叢集內的名稱解析找到資料庫的 Pod。`targetPort` 除了寫數字，也可以寫容器那個埠的**名字**（上面 Deployment 裡的 `name: http`），改埠號時比較不會漏改。

```
oc get pods
oc get services
oc get endpointslices     # 這個 Service 到底有沒有後端
oc describe service blog
```

Service 沒有後端時，一樣先比對 selector 和 Pod 的 labels，再確認 Pod 真的 Ready——沒 Ready 的 Pod 不會被算進去。以前用 `oc get endpoints` 看後端；Kubernetes 從 v1.33 起把 Endpoints 標為過時，改用 EndpointSlice。[出處](https://kubernetes.io/blog/2025/04/24/endpoints-deprecation/)

*【對外發布】*

## Route：加密要在哪一段結束

```
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: blog
spec:
  to:
    kind: Service
    name: blog
  port:
    targetPort: http
  tls:
    termination: edge
```

Route 的後端是 **Service**（不是 Pod）——又是〈單子與執行者〉那個模式：Route 是單子，真正在轉發的是 OpenShift 的路由器。`termination` 這個欄位在決定「加密在哪一段結束」，只有三個值：

| 寫法 | 加密到哪裡 | 什麼時候用 |
| --- | --- | --- |
| `edge` | 在路由器就解密，之後是明文送到 Pod | 一般情況；憑證放在路由器那一層 |
| `reencrypt` | 路由器解密後，再開一條新的加密連線到 Pod | 叢集內部也要求加密 |
| `passthrough` | 完全不解密，直接原封不動送給 Pod | 要由應用程式自己處理憑證 |

三種寫法的憑證需求各不相同。[出處](https://docs.redhat.com/en/documentation/openshift_container_platform/4.20/html/ingress_and_load_balancing/routes) **寫了 `tls` 區塊就一定要填 `termination`**，而且只吃 edge、reencrypt、passthrough 三個值（API 欄位的說明把 edge 註記為預設）；但 **整個 `tls` 區塊不寫的 Route，走的是純 HTTP，不是 edge**。[出處](https://github.com/openshift/api/blob/master/route/v1/types.go) 組織要求「一路加密到 Pod」時，`edge` 就不夠。

```
oc apply -f manifests/
oc rollout status deployment/database
oc rollout status deployment/blog
oc get route blog
```

*【壞掉的時候】*

## 由內往外縮小範圍，不要同時改十個檔案

| 看到的症狀 | 先查 | 通常是 |
| --- | --- | --- |
| Pod 卡在 Pending | `describe pod`、PVC、配額 | 排不進去，或儲存還沒綁上 |
| ImagePullBackOff | 映像檔名稱、標籤、拉取憑證 | 名字打錯、標籤不存在、沒權限 |
| CrashLoopBackOff | 這次和上一次的紀錄 | 設定漏了、權限不足、程式自己崩潰 |
| Service 沒有後端 | selector、labels、就緒檢查 | 標籤沒對上，或 Pod 還沒 Ready |
| Route 回錯誤 | Route、Service、後端、目標埠 | 這條鏈其中一層不通 |

```
oc describe pod POD名稱
oc logs POD名稱
oc logs POD名稱 --previous       # 上一次崩潰前留下的紀錄
oc get events --sort-by=.metadata.creationTimestamp
oc port-forward service/blog 8080:80
```

> 先用 port-forward 確認內部通不通  
> 內部通、外面不通 → 問題就只剩 Route 那一段

這個順序的價值在於**每一步都把範圍砍一半**。反過來同時調 Route、改 Service、重建 PVC，就算會了也不知道是哪一個修好的。

### 重點整理

*   OpenShift 核心就是 Kubernetes，物件幾乎通用；多出來最常用的是 Route 這個對外入口。
*   套用順序幫助操作，但就緒保證來自 readiness probe 和應用程式的重試，不是 YAML 的先後。
*   `configMapKeyRef`／`secretKeyRef` 的 name 和 key 要完全一致，錯一個字 Pod 起不來。
*   OpenShift 用隨機的非 root 使用者編號跑容器——假設自己是 root 的映像檔會掛；非 root 不能聽 1024 以下的埠，這就是這類映像檔聽 8080 不聽 80 的原因。
*   `docker.io/bitnami` 底下的既有映像已搬到 legacy 倉庫、不再更新，照舊名稱拉可能拉不下來；正式環境本來就不該用 `latest`。
*   Route 的 `termination` 只有 edge、reencrypt、passthrough 三種，決定加密在哪一段結束。
*   排錯由內往外：Pod → Service（先 port-forward 試）→ Route。

## 隨堂測驗

**Q1. OpenShift 的 Route，後端接的是什麼？**

- (A) Service——再由 Service 挑出可用的 Pod
- (B) 直接指定某一個 Pod 的位址
- (C) PVC
- (D) Secret

<details><summary>看答案</summary>

**答案：(A)** 又是「單子與執行者」那個模式：Route 是單子，真正在轉發的是 OpenShift 的路由器。

</details>

**Q2. 為什麼「先套用資料庫的 YAML、再套用網站的」保證不了網站啟動時資料庫已經能用？**

- (A) Kubernetes 是非同步調和資源的，建立順序不等於應用程式的就緒順序
- (B) Deployment 只會照字母順序啟動
- (C) Service 會延後建立所有 Pod
- (D) PVC 綁定後會暫停 API Server

<details><summary>看答案</summary>

**答案：(A)** 真正的保證來自 readiness probe 和應用程式自己的重試，跟 Compose 的 depends_on 同一個道理。

</details>

**Q3. Deployment 裡 WORDPRESS_DATABASE_HOST 填 database，這個 database 指的是什麼？**

- (A) 資料庫那個 Service 的名字
- (B) 資料庫 Pod 當下的位址
- (C) 資料庫容器的映像檔名稱
- (D) PVC 的名稱

<details><summary>看答案</summary>

**答案：(A)** Pod 的位址一直在變，所以呼叫方只認 Service 的名字。注意變數名本身是跟著映像檔走的：WORDPRESS_DATABASE_\* 是 Bitnami 版的寫法，Docker Hub 官方的 wordpress 映像吃的是 WORDPRESS_DB_\*，而且聽 80 不是 8080——換映像檔要把變數名和埠號一起對過。

</details>

**Q4. PVC 長時間卡在 Pending，該先查什麼？**

- (A) 儲存類別存不存在、存取模式支不支援、容量夠不夠、專案配額還有沒有
- (B) Route 的 TLS termination 設成哪一種
- (C) Service 的 sessionAffinity
- (D) ConfigMap 有沒有設成不可變更

<details><summary>看答案</summary>

**答案：(A)** 第一種特別容易中：抄來的範例寫了某個雲端專屬的儲存類別，但你這個環境沒有。

</details>

**Q5. OpenShift 上挑容器映像檔，為什麼要特別注意非 root 相容性？**

- (A) 平台會用隨機指定的、非 root 的使用者編號來跑容器，假設自己是 root 的映像檔會失敗
- (B) Route 只允許 root 程序接受 HTTPS
- (C) ConfigMap 只有 root 掛載得起來
- (D) StatefulSet 一律固定使用編號 0 的使用者

<details><summary>看答案</summary>

**答案：(A)** 可寫的目錄要屬於 root 群組且該群組可寫；容器裡的程序不可以聽 1024 以下的特權埠，因為它們不是以特權使用者的身分在跑——這就是這類映像檔聽 8080 不聽 80 的原因。

</details>

**Q6. 正式環境用 latest 當映像檔標籤，最大的風險是什麼？**

- (A) 同一個標籤可能被發佈者改成指向不同內容，部署到底是什麼版本變得無法重現
- (B) 它會讓所有健康檢查失效
- (C) 它只能搭配 ClusterIP 型態的 Service
- (D) 它會讓 PVC 自動變成唯讀

<details><summary>看答案</summary>

**答案：(A)** 標籤是可變的，要硬保證同一份內容就得釘內容摘要（digest）。

</details>

**Q7. Route 的 termination 設成 edge，代表什麼？**

- (A) 加密在路由器那一層就結束，之後是明文送到 Pod
- (B) 完全不解密，原封不動交給 Pod 自己處理
- (C) 路由器解密後再開一條新的加密連線到 Pod
- (D) 整條路徑都不加密

<details><summary>看答案</summary>

**答案：(A)** 要求一路加密到 Pod 的話，要改用 reencrypt 或 passthrough。

</details>

**Q8. port-forward 進去看得到網站，但用公開網址打不開。下一步該集中查哪一層？**

- (A) Route、憑證設定、路由器，以及 Route 指到的目標埠
- (B) 把所有 PVC 重建一次
- (C) 把資料庫的 Secret 刪掉重來
- (D) 把快取改成 DaemonSet

<details><summary>看答案</summary>

**答案：(A)** 內部已經通，範圍就只剩對外那一段——每一步砍一半，才知道是哪裡修好的。

</details>

**Q9. Shell 裡用 cat << 'EOF' 送 YAML，裡面寫的 $PROJECT_NAME 會發生什麼事？**

- (A) 不會被展開，會原封不動當成字串送出去
- (B) 會被展開成目前的專案名稱
- (C) 會讓 oc apply 直接噴語法錯誤
- (D) 會被展開成空字串並印出警告

<details><summary>看答案</summary>

**答案：(A)** here-document 的結束字加了引號，裡面就不做變數展開；比較單純的做法是不要在 YAML 裡寫 namespace。

</details>
