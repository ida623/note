# 02. AWS 全域架構與 IAM

> 來源：[筆記平台 · 雲端 AWS 與 GCP](https://hhtim.github.io/notes-platform/cloud/#/lesson/aws-iam)　第 2 課 / 共 18 課 · 約 14 分鐘

**認識 Region、Availability Zone 與 Edge Location，學會用 IAM 的身分、角色與政策落實最小權限，並知道 IAM 為什麼是全球服務。**

### 讀完這課你會

*   分清 Region、Availability Zone 與 Edge Location
*   說出 User、Group、Role、Policy 怎麼組成授權
*   判斷一個請求會被放行還是被擋下
*   知道 IAM 為什麼不屬於 Region、怎麼檢查政策

*【全球基礎設施】*

## Region 是地理區域，Availability Zone 是故障隔離位置

AWS Region 是 AWS 在某個地理範圍提供服務的區域。很多 AWS 資源會建立在你選的 Region 裡；切到另一個 Region 時，不要預期原本那個 Region 的區域性資源會自動跟著出現。

一個 Region 裡面有多個可用區（Availability Zone，AZ）。AZ 之間用低延遲網路互連，同時保有故障隔離能力。把工作負載分散到多個 AZ，可以降低單一位置壞掉就整個服務中斷的風險。

一個 Region 不會只有一兩個 AZ：每個 Region 至少由三個彼此隔離、實體分開的 AZ 組成[出處](https://aws.amazon.com/about-aws/global-infrastructure/regions_az/)。為什麼要這樣切：同一 Region 內的 AZ 最遠相距約 100 公里，遠到不會一起遭災，又近到延遲夠低、可以用同步複寫[出處](https://docs.aws.amazon.com/whitepapers/latest/aws-fault-isolation-boundaries/availability-zones.html)。

要注意的是：跨 AZ 擺放資源只是把隔離的地基打好；要讓流量自動轉向，還是得搭配健康檢查、負載平衡和資料備援設計。

*【靠近使用者】*

## Edge Location 用來加速內容，不等於 Region

邊緣站點（Edge Location）設在靠近使用者的位置，常拿來快取與傳送內容。可以想成在各地設超商取貨點：常用的東西先放到離客戶近的地方，不必每次都跑回主倉庫。

選 Region 時要一起看：法規與資料落地要求、使用者延遲、那個 Region 有沒有提供你要的服務，以及成本。Edge Location 能改善內容傳遞，但不能拿來取代「工作負載要放在哪個 Region」這個決定。

*【責任邊界】*

## AWS 保護雲端本身，客戶保護放進雲端的東西

AWS 共享責任模型可以想成租辦公大樓：房東負責建築結構、公共設施與大樓的底層安全；租戶還是要管自己的門禁名單、室內資料和自己那些設備的設定。

*   **AWS**：負責底層機房、硬體、網路與代管服務的基礎設施安全。
*   **客戶**：依服務模式管理資料、身分權限、加密選項、網路規則、作業系統與應用程式。

用 IaaS 時，客戶要管的層數比較多；用全託管服務時供應商管得多，但客戶對自己的資料與存取權限還是跑不掉。

*【IAM 骨架】*

## 先回答三件事：誰、對哪個資源、做什麼

AWS Identity and Access Management（IAM）管兩件事：身分驗證（authentication）確認「你是誰」，授權（authorization）決定「你能做什麼」。

IAM 是**全球服務**：你建立的 User、Group、Role 與 Policy 不隸屬於任何一個 Region，切到哪個 Region 看到的都是同一份。這跟這一課開頭講的「區域性資源不會自動跟著你換 Region」正好相反。資源不屬於特定 Region 的服務，通常就叫全球（global）服務。[出處](https://docs.aws.amazon.com/whitepapers/latest/aws-fault-isolation-boundaries/global-services.html)

「全球」講的是資源的適用範圍，不是說整個 IAM 跑在同一個地方。IAM 分成兩半：

*   控制平面（control plane）：負責「改設定」，也就是建立與修改使用者、角色、政策那些操作。在 aws 分區只設在 us-east-1 一個 Region
*   資料平面（data plane）：負責「每次請求都判斷准不准」，在該分區的每個 Region 各有一套隔離的

（分區＝partition，AWS 把全球切成幾塊彼此獨立的大區塊，一般商用 Region 都在名為 aws 的那一塊。）這個差別在災難演練時會咬人：復原路徑不要依賴分區型服務的控制平面，也就是別等到故障切換的當下才去建角色、改政策[出處](https://docs.aws.amazon.com/whitepapers/latest/aws-fault-isolation-boundaries/global-services.html)。

*   **IAM User**：長期存在於 AWS 帳號中的身分，可以搭配主控台密碼或程式用的憑證。
*   **User Group**：IAM User 的集合，方便把共同權限集中管理；群組本身不是一個可以登入的身分。
*   **IAM Role**：可以被人員、應用程式或 AWS 服務「承接」的身分，通常搭配短期憑證。
*   **Policy**：一份政策文件，寫清楚允許或拒絕哪些動作、作用在哪些資源、有什麼條件。

Role 搭配的短期憑證由 AWS Security Token Service（STS）發出。15 分鐘是可以要求的最短效期，不是「每 15 分鐘就失效」[出處](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_manage-assume.html)。承接角色時可以要求 15 分鐘到該角色「最長工作階段時間」之間的任一長度（這個設定可以調 1 到 12 小時），沒指定的話預設 1 小時。拿一組角色憑證再去承接另一個角色（角色串接）時，上限固定是 1 小時，而且不管個別角色設定多長都一樣[出處](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html#id_roles_terms-and-concepts)。

> 📝 查證更正：原筆記寫「STS (Security Token Service) 每 15 分鐘有效，配合 IAM role，分發給 IAM user、AWS service」，查證後更正：15 分鐘是可以要求的最短效期下限，不是固定效期。承接角色時可要求的範圍是 15 分鐘到該角色的「最長工作階段時間」設定（可設 1 到 12 小時），沒特別指定的預設是 1 小時；另外用一組角色憑證再去承接另一個角色（角色串接）時，上限固定為 1 小時

這個範圍只適用於承接角色，STS 其他取得方式的效期範圍不一樣——例如 IAM 使用者呼叫 GetSessionToken 取得的臨時憑證，範圍是 15 分鐘到 36 小時、預設 12 小時；同一支 API 若是用根使用者的憑證呼叫，上限就只有 1 小時[出處](https://docs.aws.amazon.com/STS/latest/APIReference/API_GetSessionToken.html)。這幾種方式共通的只有「15 分鐘是下限」這一點。

日常管理不該長期使用 AWS 帳號的根使用者（root user）。根使用者權限極高，應該設強密碼、開啟多重要素驗證（Multi-Factor Authentication，MFA），而且只在真的需要根權限的工作才動用。

*【Policy 結構】*

## Effect、Action、Resource 與 Condition 組成一句授權

把政策陳述（Statement）想成一條法規：「允許或拒絕誰，在什麼條件下，對哪個資源執行哪些動作。」

| 欄位 | 用途 |
| --- | --- |
| Effect | 指定 Allow 或 Deny。 |
| Action | 指定可以執行或被拒絕的 AWS API 動作。 |
| Resource | 指定動作作用在哪些 AWS 資源，通常寫成 ARN（Amazon Resource Name，AWS 資源的完整地址）。 |
| Condition | 限制政策何時生效，例如來源位址、標籤或請求情境。 |
| Principal | 指出誰是被授權或被限制的主體，常見於資源型政策與信任政策。 |

> 授權判斷 ≈ 主體（Principal）＋動作（Action）＋資源（Resource）＋條件（Condition）＋效果（Effect）

身分型政策是附加在既有的 User、Group 或 Role 上，所以政策內容通常不另外寫 Principal；資源型政策則要指出誰能存取這個資源。

*【兩種政策】*

## 身分型說「這個身分能做什麼」，資源型說「誰能碰我」

| 比較 | 身分型政策 | 資源型政策 |
| --- | --- | --- |
| 附加位置 | IAM User、User Group 或 Role | 支援這類政策的 AWS 資源 |
| 思考方向 | 這個身分可以做什麼 | 哪些主體可以存取這項資源 |
| Principal | 通常不寫在政策裡 | 通常要指定 |
| 常見用途 | 授權角色讀取特定 Bucket（儲存貯體） | Bucket Policy、Lambda 函式的呼叫權限 |

例如 EC2 上的應用程式要讀 S3，做法是把適當的 Role 指派給這個工作負載，讓程式拿到短期憑證，而不是把長期存取金鑰寫死在程式碼裡。〈AI Agent 實作：AWS 基礎建設〉用「掛角色前後跑同一條指令」把這件事做了一遍，可以當實作範例。

*【誰呼叫誰】*

## S3 觸發 Lambda 時，授權要放在被呼叫的 Lambda 上

```
使用者上傳物件
        ↓
S3 收到事件
        ↓ 呼叫 Lambda
Lambda 的資源型政策
        ↓ 檢查 Principal、Action 與來源條件
允許後才執行函式
```

這個情境裡呼叫的人是 S3 服務，被呼叫的資源是 Lambda 函式。所以要在 Lambda 的資源型政策中允許 S3 執行呼叫動作，並用條件限制只能由預期的那個 Bucket 觸發。

「任兩個 AWS 服務互相串接都要透過 Role」這句話不成立[出處](https://docs.aws.amazon.com/lambda/latest/dg/access-control-resource-based.html)：這一頁的 S3 觸發 Lambda 就是反例。要用哪一種，看方向——工作負載主動去呼叫別的服務（例如 EC2 上的程式讀 S3）用 Role；別的服務來呼叫你（例如 S3 來觸發 Lambda）則是在被呼叫的資源上寫資源型政策。

> 📝 查證更正：原筆記寫「任兩個 AWS 服務要互相串接也要透過 Role」，查證後更正：這不是通則。S3 事件觸發 Lambda 就是反例——S3 沒有可附加身分型政策的身分，授權是寫在 Lambda 的資源型政策裡，不是靠 Role。Role 適用的是「工作負載自己去呼叫別的服務」那一種方向

Lambda 的執行角色回答的是另一個問題：「函式開始跑之後，可以存取哪些資源」。它不回答「誰可以呼叫這個函式」。這兩個方向不能混在一起。

*【安全判斷】*

## 沒被允許就是不行，明確 Deny 會蓋過 Allow

AWS 的權限判斷不是挑一份看起來權限最大的政策來用。一般觀念是：沒有任何適用的 Allow，請求會被隱含拒絕；只要出現適用的明確 Deny，就算別的政策有 Allow，請求還是會被拒絕。

所以授權要照最小權限原則（principle of least privilege）：只給完成工作需要的動作與資源範圍，能加條件就加。權限需求變了之後，也要定期檢查、把不再使用的授權拿掉。

> 💡 ARN（Amazon Resource Name）像 AWS 資源的完整地址。政策應該盡量指向真正需要的那些資源，沒有充分理由就不要把 Resource 寫成涵蓋全部的萬用字元。

*【先驗再上】*

## 兩個內建工具：上線前先模擬，上線後持續盤點

政策寫完最怕兩種失誤：以為擋住了其實沒擋住，以及給過頭了卻沒人發現。IAM 對這兩件事各給了一個工具，一個事前用、一個事後用。

*   **IAM 政策模擬器（IAM policy simulator）**：事前用的。挑一個現有身分，或貼一份還沒套上去的政策，再指定要測的動作與資源，它會回答這個請求會被允許還是拒絕，並指出是哪一條政策造成這個結果。它只模擬 AWS 會怎麼依那些政策評估請求，不會真的向任何 AWS 服務送出請求[出處](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_testing-policies.html)，所以拿刪除類的危險動作去試也不會真的動到東西。
*   **IAM Access Analyzer（存取分析器）**：事後用的。它持續掃你的資源與身分，把問題寫成一則則「發現項目」（finding）。它能做的事：
*   找出組織與帳號裡分享給外部對象的資源 找出沒在用的權限 依政策語法與 AWS 最佳做法檢查政策 依 CloudTrail（AWS 記錄誰在什麼時候呼叫了哪個 API 的稽核服務）的實際使用紀錄，反推出一份剛好夠用的政策[出處](https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html)

> 模擬器回答「這樣寫會不會通」；Access Analyzer 回答「現在到底開了哪些沒人注意的門」。

模擬器的結果可能與實際 AWS 環境不同，測完之後要再對照實際環境檢查政策，確認得到想要的結果。遇到比較複雜的設定（例如角色串接），模擬結果也可能與實際行為不同[出處](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_testing-policies.html)。

Access Analyzer 有一個很容易漏掉的範圍限制：外部存取的分析只看啟用它的那個 Region 裡的資源，所以想看完帳號裡所有資源，得在每個有資源的 Region 各建一個外部存取分析器；未使用權限那一種分析則不受 Region 影響，不必每個 Region 各建一個[出處](https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html)。另外 Access Analyzer 有一部分是要收費的：

*   未使用權限分析：依分析的 IAM 角色與使用者數量計費
*   內部存取分析：依監控的資源數量計費
*   自訂政策檢查：依 API 請求次數計費
*   「在多個 Region 各建一個就各收一份錢」只適用於未使用權限分析器，不是所有分析器[出處](https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html)

2026 年 7 月起，政策模擬器搬進了 IAM 主控台，並加上模擬服務控制政策的能力，不再是獨立的模擬器網站（服務控制政策＝Service Control Policy，SCP，在 AWS Organizations 裡替整個組織或某一群帳號畫出的權限天花板，個別帳號的政策再怎麼給也不會超過它）[出處](https://aws.amazon.com/about-aws/whats-new/2026/07/iam-policy-simulator-iam-console/)。

### 重點整理

*   Region 是地理區域；AZ 是 Region 內的故障隔離位置；Edge Location 著重把內容送到離使用者近的地方。
*   IAM User 與 Group 管既有身分；Role 適合可被承接的權限與短期憑證。
*   身分型政策附加在身分上；資源型政策附加在資源上並要寫出 Principal。
*   預設是隱含拒絕，適用的明確 Deny 會蓋過 Allow。
*   優先採用最小權限、MFA 與短期憑證，不要在程式裡放長期金鑰。
*   IAM 是全球服務，身分與政策不隸屬某個 Region；但改設定的控制平面只在單一 Region，復原路徑別依賴它。
*   上線前用政策模擬器試，上線後用 Access Analyzer 盤點外部存取與沒在用的權限。

## 隨堂測驗

**Q1. 某服務要能承受單一機房位置故障，最基本的方向是什麼？**

- (A) 把工作負載分散到同一 Region 的多個 Availability Zone，並設計故障切換
- (B) 把所有執行個體集中放在同一個 Availability Zone
- (C) 只把靜態內容放到 Edge Location 快取
- (D) 把資源全部改建在另一個 Region，原 Region 不留

<details><summary>看答案</summary>

**答案：(A)** 多 AZ 能降低單一故障隔離位置失效的衝擊，但仍要搭配流量與資料備援才會自動切換。

</details>

**Q2. 選擇 AWS Region 時，哪一組因素最值得一起評估？**

- (A) 法規與資料落地、使用者延遲、該 Region 有沒有提供需要的服務，以及成本
- (B) 該 Region 的 AZ 命名規則與主控台語言設定
- (C) 帳號裡 IAM User 的數量與群組命名慣例
- (D) Edge Location 的數量，其他都不必看

<details><summary>看答案</summary>

**答案：(A)** Region 的選擇通常同時牽涉合規、距離、服務可用性與成本；Edge Location 只影響內容傳遞。

</details>

**Q3. EC2 上的應用程式需要讀取 S3，哪種做法比較符合安全實務？**

- (A) 指派一個只有必要權限的 IAM Role，讓工作負載取得短期憑證
- (B) 把根使用者的存取金鑰寫進程式碼
- (C) 把整個 S3 Bucket 設為公開讀取
- (D) 在 EC2 上放一份所有團隊共用的長期存取金鑰檔

<details><summary>看答案</summary>

**答案：(A)** Role 讓工作負載拿到短期憑證，避免在機器或程式裡保存長期金鑰。

</details>

**Q4. 下列哪一項最正確地描述 IAM User Group？**

- (A) 它是 IAM User 的集合，方便集中指派共同權限
- (B) 它是一個可以直接登入主控台的共用帳號
- (C) 它是多個 AWS 帳號組成的組織單位
- (D) 它只能放 IAM Role，不能放 IAM User

<details><summary>看答案</summary>

**答案：(A)** User Group 用來整理 IAM User 與共同權限，本身不是登入身分。

</details>

**Q5. 資源型政策通常需要哪個欄位，才能指出授權對象是誰？**

- (A) Principal
- (B) Effect
- (C) Condition
- (D) Resource

<details><summary>看答案</summary>

**答案：(A)** Principal 指定哪些帳號、身分或服務是這份政策適用的主體；身分型政策通常不寫這一欄。

</details>

**Q6. 某身分型政策允許讀取某個 Bucket，但該 Bucket 的適用政策明確 Deny 這個請求，結果通常如何？**

- (A) 請求被拒絕，因為適用的明確 Deny 優先
- (B) 請求被允許，因為身分型政策永遠優先
- (C) 以較晚建立的那份政策為準
- (D) 兩份政策互相抵銷，改由預設值決定

<details><summary>看答案</summary>

**答案：(A)** 在 IAM 的評估規則中，適用的明確 Deny 會蓋過任何 Allow。

</details>

**Q7. S3 事件要觸發 Lambda 時，Lambda 的資源型政策主要回答哪個問題？**

- (A) S3 是否被允許呼叫這個 Lambda 函式
- (B) Lambda 執行之後可以讀取哪些資料庫
- (C) 使用者能不能登入 AWS 主控台
- (D) Lambda 應該部署在哪一個 Availability Zone

<details><summary>看答案</summary>

**答案：(A)** 資源型政策控制「誰能呼叫我」；函式跑起來之後的權限是由執行角色決定的。

</details>

**Q8. 哪一項最符合最小權限原則？**

- (A) 只允許工作真正需要的動作、資源與條件，並定期移除不再使用的權限
- (B) 所有開發者一律先給完整管理權限，出事再收回
- (C) 把 Resource 都寫成萬用字元，以免部署時缺權限失敗
- (D) 替每個程式都配一組相同的長期存取金鑰方便管理

<details><summary>看答案</summary>

**答案：(A)** 最小權限要求授權範圍與實際工作需求相符，而且會隨需求改變而調整。

</details>

**Q9. 在東京 Region 的主控台建立了一個 IAM Role，接著把主控台切到法蘭克福 Region，會看到什麼？**

- (A) 那個 Role 還在，因為 IAM 的身分與政策不隸屬於任何一個 Region
- (B) 那個 Role 不見了，要在法蘭克福 Region 再建一次一模一樣的
- (C) 那個 Role 還在，但它的權限只在東京 Region 生效
- (D) 那個 Role 還在，但要先在法蘭克福 Region 啟用它才承接得了

<details><summary>看答案</summary>

**答案：(A)** IAM 的資源不屬於特定 Region，這正是它被稱為全球服務的原因；切 Region 看到的是同一份。

</details>

**Q10. 一份政策還沒套到任何身分上，想先確認它會不會放行某個危險動作，最合適的做法是什麼？**

- (A) 用 IAM 政策模擬器評估，它會算出允許或拒絕，但不會真的向 AWS 服務送出請求
- (B) 先套到一個測試用的 IAM User 上，實際執行那個動作看看會不會成功
- (C) 查 CloudTrail 的歷史紀錄，看過去有沒有人成功做過這個動作
- (D) 用 IAM Access Analyzer 的未使用權限分析，看這個動作有沒有被用過

<details><summary>看答案</summary>

**答案：(A)** 模擬器是事前工具，不送出真實請求；另外三個看到的都只是已經發生過的事。

</details>
