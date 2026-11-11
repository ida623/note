# 18. K8s 上手：Minikube 與上雲

> 來源：[筆記平台 · 容器與 Kubernetes](https://hhtim.github.io/notes-platform/k8s/#/lesson/k8s-hands-on)　第 18 課 / 共 23 課 · 約 15 分鐘

**把第 5〜10 課的觀念寫成 YAML，順便把資源單位讀懂。**

### 讀完這課你會

*   把 K8s 的觀念寫成一份能套用的 YAML
*   看懂 500m、256Mi 這些資源單位
*   用 Minikube 在自己電腦開叢集
*   知道 YAML 搬上雲端時哪些要重想

*【動手之前】*

## 一份部署計畫要回答三件事

〈為什麼需要 Kubernetes〉講過 K8s 的核心迴圈：你交一張單子，它一直比對現況。要準備的東西可以拆成三個問題：

*   **要部署什麼**：一個容器化的應用程式。也就是先有映像檔（〈映像檔與 Dockerfile〉）。
*   **要怎麼部署、給多少資源**：幾份、每份多少 CPU 和記憶體、怎麼換版本、對外怎麼進來。
*   **要部署到哪裡**：本機的練習叢集，還是雲端的正式叢集。

〈為什麼需要 Kubernetes〉那個迴圈的英文術語：你寫的單子叫**期望狀態（desired state）**，叢集目前的樣子叫**現況（current state）**，「只講結果不講步驟」的寫法叫**宣告式（declarative）**，控制器一直把現況往期望狀態拉的那個動作叫**調和（reconciliation）**。

*【本機練習場】*

## Minikube：在自己電腦上開一個叢集

Minikube 是本機版的 Kubernetes，目的是讓學習和開發容易一點。[出處](https://minikube.sigs.k8s.io/docs/start/)

```
minikube start
kubectl cluster-info
kubectl get nodes
```

> 💡 `minikube start` 開出來的是**單節點**叢集——那一台同時是大腦（master）也是工人（worker）。這跟〈叢集與大腦〉講的正式架構不一樣：正式環境裡大腦那幾台是分開的、而且要奇數台（〈壞掉的時候〉）。[出處](https://kubernetes.io/docs/tutorials/hello-minikube/) 所以 Minikube 練得起來，不等於正式環境也會這樣。

電腦上同時有好幾個叢集的話，先確認 `kubectl` 現在指著哪一個，免得把東西套到錯的環境去：

```
kubectl config current-context
kubectl config get-contexts
```

*【第一份單子】*

## Deployment 管幾份，Service 給一個不變的名字

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: demo-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: demo-app          # ← 要對上下面 template 的 labels
  template:
    metadata:
      labels:
        app: demo-app        # ← 這裡
    spec:
      containers:
        - name: app
          image: example/demo-app:1.0
          ports:
            - containerPort: 8080
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 256Mi
---
apiVersion: v1
kind: Service
metadata:
  name: demo-app
spec:
  selector:
    app: demo-app            # ← 也要對上同一組
  ports:
    - port: 80
      targetPort: 8080
  type: ClusterIP
```

> 💡 三個地方要對上同一組標籤（label）：Deployment 的 `selector`、Pod 範本的 `labels`、Service 的 `selector`。**這三處像三本要互相核對的地址簿，任何一處拼錯，服務就找不到後端。**

`port` 和 `targetPort` 也常搞混：`port: 80` 是**這個 Service 對外掛牌的號碼**（叢集內其他服務打 80），`targetPort: 8080` 是**容器裡程式真正在聽的號碼**。`type: ClusterIP` 是預設值，意思是只在叢集內部找得到它（〈Service：找路〉講的那個「永遠不變的名字」）。

```
kubectl apply -f app.yaml
kubectl get deployment,pods,service
kubectl rollout status deployment/demo-app
kubectl port-forward service/demo-app 8080:80    # 從你的電腦直接打進去試
```

*【單位】*

## 500m 和 256Mi 分別是多少

requests（保留量）和 limits（上限）的意思見〈Deployment：下單〉。

| 寫法 | 是多少 | 怎麼記 |
| --- | --- | --- |
| `1` | 一顆 CPU | 實體機上是一個實體核心，虛擬機上是一個虛擬核心 |
| `500m` | 半顆 CPU | m 是千分之一，1000m ＝ 1 顆 |
| `100m` | 十分之一顆 | 比 1m 更細的寫法不准 |
| `128Mi` | 128 × 1,048,576 位元組（約 134 MB） | Mi 是 2 的 20 次方，不是一百萬 |
| `128M` | 128,000,000 位元組 | 沒有 i 的才是十進位的一百萬 |

> 💡 寫 `memory: 16Mi` 的時候，「**兆**」這個字要特別小心，因為兩岸用法剛好差了六個數量級：

| 寫法／講法 | 是多少位元組 |
| --- | --- |
| `Mi`（mebibyte） | 2 的 20 次方 ＝ 1,048,576——`16Mi` 約 16.8 MB |
| `M`（megabyte） | 10 的 6 次方 ＝ 1,000,000 |
| 台灣講的「兆」 | 10 的 12 次方，也就是 tera（T、Ti 那個量級） |
| 簡體資料裡的「兆字节」 | 多半指 MB，不是 10 的 12 次方 |

所以簡體技術文件寫的「16 兆位元組」，多半是 16 MB 的意思，跟 `16Mi`（約 16.8 MB）同一個量級；但在台灣的說法裡「兆」是 10 的 12 次方，照字面讀就差了一百萬倍。Kubernetes 只定義 `Mi` 和 `M` 這兩個後綴，不用「兆」這種口語單位——**寫 YAML 就照後綴寫，不要在腦袋裡換成「兆」**。[出處](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)

CPU 那邊的單位是 millicore（毫核心）：1000m ＝ 1 個核心，所以 `20m` 是單一核心的 2%。至於「一個核心」是什麼：**節點是實體機就是一個實體核心，節點是虛擬機就是一個虛擬核心**。[出處](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)

> 💡 **requests 和 limits 填一樣時，這個 Pod 的服務品質等級（QoS class）是 Guaranteed**——意思是**節點資源不夠、要趕 Pod 走的時候，Guaranteed 是最後才被趕的那一批**（先趕 BestEffort，再趕 Burstable）。注意這不是排班順序：決定「先排誰」的是另一套機制（PriorityClass，Pod 的排班優先權）。[出處](https://kubernetes.io/docs/concepts/workloads/pods/pod-qos/) 填得不一樣（requests 小於 limits）則是可以超用、但要有餘力才超得到。

這個順序還有一個前提：**因資源壓力而驅逐時，只有「用量已經超過自己 requests」的 Pod 才進候選名單**。所以一個 requests 填得實在、也沒超用的 BestEffort 以外的 Pod，不會因為等級低就先被趕；等級決定的是候選名單裡的先後。[出處](https://kubernetes.io/docs/concepts/workloads/pods/pod-qos/)

CPU 和記憶體超過上限的後果不同（〈Deployment：下單〉講過）：CPU 超過上限是被**節流**（跑慢一點），記憶體超過上限則**可能**被殺掉，而且**要等核心真的偵測到記憶體吃緊才會動手**，超過上限不等於立刻被砍。[出處](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)

*【自動長大縮小】*

## HPA：流量大就多開幾份

水平 Pod 自動擴縮器（Horizontal Pod Autoscaler，簡稱 HPA）會依指標調整副本數。它不是魔法，有三個前提：指標拿得到、容器有設合理的 requests、應用程式本身多開幾份也沒問題。

```
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: demo-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: demo-app
  minReplicas: 3
  maxReplicas: 35
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 80
```

> 💡 一個容易踩到的互動：**Deployment 寫 `replicas: 2`、HPA 寫 `minReplicas: 3`，最後會變成 3 份**。HPA 接手之後，Deployment 那個數字就不是最終答案了。

指標可以是幾種：`Resource`（CPU、記憶體這種現成的）、`Pods`（每個 Pod 的自訂指標，例如每秒封包數）、`Object`（某個物件上的指標，例如 Ingress 的每秒請求數）、`External`（叢集外面來的）。後面三種都要另外有一條指標管線把數字送進來，不是寫下去就會動。

同理，滾動更新（〈Deployment：下單〉）能不能真的不斷線，也有前提：副本要夠、就緒檢查（readiness probe）要設對、而且新舊版本要能同時存在一陣子。策略只是機制，容量和程式設計不對一樣會斷。

*【設定與密碼】*

## ConfigMap 放一般設定，Secret 放敏感的

把設定從程式碼裡拉出來，換設定就不用重建映像檔。一般設定放 **ConfigMap**，密碼、金鑰、憑證放 **Secret**。兩個在 YAML 裡的用法幾乎一樣，〈OpenShift 部署實戰〉會實際接上去。

Secret 這個名字很容易讓人以為資料已經被保護好了。Secret **預設是沒有加密**存在 etcd 裡的，任何有 API 存取權、或摸得到 etcd 的人都讀得出來；甚至只要有權在某個命名空間建 Pod，就等於能讀那個命名空間的 Secret[出處](https://kubernetes.io/docs/concepts/configuration/secret/)。base64 是編碼不是加密。要真的安全，得另外做：

> 📝 查證更正：原筆記寫「Secrets 在 K8S 中安全地儲存了敏感資料，例如 API Keys、密碼或是認證……但是用 base64 編碼以及是專門為安全敏感性配置所設計」，查證後更正：Kubernetes 官方文件的警語寫 Secret 預設是「stored unencrypted in the API server's underlying data store (etcd)」，任何有 API 存取權或 etcd 存取權的人都讀得到；base64 只是編碼不是加密

*   開啟靜態加密
*   用角色存取控制（RBAC：先把權限包成角色，再把角色給人或程式，規定誰可以對哪些東西做什麼）把權限縮到最小
*   或改用外部的金鑰管理服務

RBAC 這套想法在 Spring 裡怎麼落地，見〈Spring Security 認證與授權〉。

*【從本機到雲端】*

## YAML 帶得走，基礎設施帶不走

Kubernetes 把應用程式和特定主機解開了，但不會自動抹平各家雲端的差異。同一份 YAML 搬上去，下面這些還是要重新想過。

| 面向 | Minikube | 雲端叢集 |
| --- | --- | --- |
| 用途 | 學習、本機驗證 | 測試、預備或正式的工作負載 |
| 節點 | 通常就一台 | 多台，還可以跨多個可用區 |
| 對外入口 | 多半用 `port-forward` 或本機外掛 | 接雲端的負載平衡器和網域名稱 |
| 持久儲存 | 本機的儲存供應器 | 雲端磁碟、檔案或物件儲存服務 |
| 誰負責顧 | 你自己的電腦 | 雲端商和你的團隊分攤（〈要不要用 K8s〉那張表） |

搬之前先把環境差異抽出來：一般設定放 ConfigMap、敏感設定走 Secret 加外部金鑰管理、儲存用 PVC（一張「我要一塊儲存空間」的申請單）申請（〈OpenShift 部署實戰〉）、對外入口依平台選 Ingress 或負載平衡服務（〈對外入口〉）。

「為什麼建議上雲」講的也是同一件事的反面：自己在機房做，主機互連、負載平衡、擴縮、權限控管、買硬碟，每一樣都得自己來。

*【壞掉的時候】*

## 先看狀態，再看事件，最後才看紀錄

```
kubectl get pods
kubectl describe pod POD名稱
kubectl logs POD名稱
kubectl get events --sort-by=.metadata.creationTimestamp
kubectl rollout status deployment/demo-app
```

Pod 起不來，先分清楚是哪一種：**排不進去**（沒有節點裝得下）、**映像檔拉不到**（名字打錯或沒權限）、**程式自己崩潰**、還是**健康檢查沒過**。這四種的處理方向完全不一樣，`describe` 最下面那段事件通常直接告訴你是哪一種。

Service 連不到，先核對標籤有沒有對上、`targetPort` 對不對、Pod 是不是真的 Ready——不要一上來就砍掉重建整個叢集。

看「這個 Service 到底有沒有後端」，以前用 `kubectl get endpoints`。Kubernetes 從 v1.33 起把 Endpoints 這個 API 標為過時，改用 EndpointSlice，讀寫舊的會收到警告。[出處](https://kubernetes.io/blog/2025/04/24/endpoints-deprecation/) 現在請改打 `kubectl get endpointslices`——EndpointSlice 就是「這個 Service 目前實際指到哪幾個 Pod」的那份清單。

### 重點整理

*   部署計畫回答三件事：部署什麼、怎麼部署給多少資源、部署到哪裡。
*   Minikube 開的是單節點叢集（大腦和工人同一台），適合練，不代表正式架構。
*   Deployment 的 selector、Pod 範本的 labels、Service 的 selector，三處標籤要一致。
*   `1000m` ＝ 一顆 CPU（實體機上是一個實體核心，虛擬機上是一個虛擬核心）；`Mi` 是 2 的 20 次方位元組、`M` 是 10 的 6 次方——台灣講的「兆」是 10 的 12 次方，簡體資料裡的「兆字节」多半是 MB，看到「兆」要先確認是哪一種。
*   requests 等於 limits 時 QoS 是 Guaranteed——節點資源不夠要趕人時最後才輪到它；而且因資源壓力驅逐時，只有用量超過自己 requests 的 Pod 才是候選。這跟排班順序是兩回事。
*   HPA 的 `minReplicas` 會蓋過 Deployment 的 `replicas`；自訂指標要另外有管線送數字。
*   Secret 預設沒有加密，只是 base64；要安全得另外開靜態加密、用角色存取控制（RBAC）把權限縮到最小，或改用外部金鑰服務。
*   YAML 搬得走，但網路、儲存、權限、成本上雲之後都要重看一遍。

## 隨堂測驗

**Q1. minikube start 開出來的叢集，跟〈叢集與大腦〉講的正式架構最大的差別是什麼？**

- (A) 它是單節點，同一台既是大腦也是工人
- (B) 它沒有辦法套用任何 YAML
- (C) 它不需要映像檔就能跑容器
- (D) 它的 Pod 不會被控制器補位

<details><summary>看答案</summary>

**答案：(A)** 正式環境的大腦是分開的、而且要奇數台；Minikube 是拿來學和驗證用的。

</details>

**Q2. Service 找不到 Deployment 建出來的 Pod，最先該核對什麼？**

- (A) Deployment 的 selector、Pod 範本的 labels、Service 的 selector 這三處標籤是不是一致
- (B) Dockerfile 的 ENTRYPOINT 有沒有寫成陣列
- (C) etcd 有沒有把映像檔的每一層存起來
- (D) HPA 的最大副本數是不是偶數

<details><summary>看答案</summary>

**答案：(A)** Service 靠標籤挑 Pod，三本地址簿其中一本拼錯就對不上。

</details>

**Q3. Service 寫 port: 80、targetPort: 8080，意思是什麼？**

- (A) 叢集內別人打這個 Service 的 80，流量會被送到容器裡聽 8080 的程式
- (B) 容器對外掛牌 80，主機聽 8080
- (C) Service 限制流量最多 80 個連線、8080 個請求
- (D) 80 是 Pod 數量上限，8080 是記憶體上限

<details><summary>看答案</summary>

**答案：(A)** port 是 Service 掛牌的號碼，targetPort 是容器裡程式真正在聽的號碼。

</details>

**Q4. resources 裡寫 memory: 128Mi，這是多少？**

- (A) 128 × 1,048,576 位元組，大約 134 MB
- (B) 128 × 1,000,000 位元組（那是沒有 i 的 128M）
- (C) 128,000 位元組
- (D) 主機記憶體的 128 分之一

<details><summary>看答案</summary>

**答案：(A)** Mi 是二進位的 mebibyte（2 的 20 次方位元組）；沒有 i 的 M 才是十進位的一百萬。簡體資料寫的「兆字节」多半指 MB，不是台灣講的 10 的 12 次方，讀到「兆」要先確認是哪一種。

</details>

**Q5. cpu: 500m 代表什麼？**

- (A) 半顆 CPU——m 是千分之一，1000m 等於一顆
- (B) 500 顆 CPU
- (C) 500 MB 的 CPU 快取
- (D) CPU 使用率上限 500%

<details><summary>看答案</summary>

**答案：(A)** 節點若是實體機，1 個 cpu 等於一個實體核心；節點若是虛擬機，就是一個虛擬核心。m 是它的千分之一。

</details>

**Q6. requests 和 limits 填成一樣的數字，會得到什麼？**

- (A) 這個 Pod 的服務品質等級是 Guaranteed，節點資源不夠要趕 Pod 走的時候最後才輪到它
- (B) Pod 會被禁止排到任何節點上
- (C) Kubernetes 會自動把它改成 Deployment
- (D) 容器就不會再被健康檢查監看

<details><summary>看答案</summary>

**答案：(A)** QoS 決定的是節點資源不夠時的驅逐順序（先趕 BestEffort、再 Burstable、最後 Guaranteed），不是排班順序——排班先後是另一套機制（PriorityClass，Pod 的排班優先權）在管。還有一個前提：因資源壓力驅逐時，只有用量超過自己 requests 的 Pod 才是候選。填得不一樣（requests 小於 limits）則是可以超用，但要有餘力才超得到。

</details>

**Q7. Deployment 寫 replicas: 2，HPA 寫 minReplicas: 3，最後會跑幾份？**

- (A) 3 份——HPA 接手之後，Deployment 那個數字不是最終答案
- (B) 2 份——Deployment 的設定優先
- (C) 5 份——兩個數字會相加
- (D) 會直接出錯，兩者不能並存

<details><summary>看答案</summary>

**答案：(A)** minReplicas 是 HPA 維持的下限，會蓋過 Deployment 原本寫的數字。

</details>

**Q8. 關於 Kubernetes 的 Secret，哪一句才對？**

- (A) 預設沒有加密，只是 base64 存在 etcd 裡，要另外開靜態加密並縮緊 RBAC 權限
- (B) 存進去就會自動以強加密保護，不需要額外設定
- (C) 只有叢集管理員讀得到，一般使用者完全看不到
- (D) 它跟 ConfigMap 唯一的差別是容量上限比較大

<details><summary>看答案</summary>

**答案：(A)** Secret 預設沒加密：有 API 或 etcd 存取權的人都讀得到，base64 是編碼不是加密。

</details>

**Q9. CPU 和記憶體超過 limits 的後果，差在哪？**

- (A) CPU 超過會被節流（跑慢），記憶體超過則可能被殺掉——核心偵測到記憶體吃緊時才動手
- (B) 兩者都會讓 Pod 立刻被刪除
- (C) CPU 超過會被殺掉，記憶體超過只會被節流
- (D) 兩者都只會記一筆事件，不影響執行

<details><summary>看答案</summary>

**答案：(A)** 記憶體沒辦法「用慢一點」，所以核心的處理方式是終止容器；但只是「可能」終止，而且只在核心偵測到記憶體壓力時才發生——超過上限不等於立刻被砍。

</details>

**Q10. 想看某個 Service 到底有沒有可用的後端，現在該用哪一個指令？**

- (A) kubectl get endpointslices——Endpoints 這個 API 從 v1.33 起已標為過時
- (B) kubectl get endpoints——EndpointSlice 還沒穩定
- (C) kubectl get secrets
- (D) kubectl config get-contexts

<details><summary>看答案</summary>

**答案：(A)** Endpoints 這個 API 從 v1.33 起標為過時，讀寫它會收到警告；看後端改用 EndpointSlice。

</details>
