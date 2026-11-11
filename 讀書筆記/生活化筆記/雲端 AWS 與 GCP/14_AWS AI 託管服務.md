# 14. AWS AI 託管服務

> 🏠 **生活化版本**：每個段落開頭的「生活比喻」先用日常情境帶你抓到感覺，接著再看原本的技術說明與程式碼；篇末有「比喻對照表」可以快速複習。

> 來源：[筆記平台 · 雲端 AWS 與 GCP](https://hhtim.github.io/notes-platform/cloud/#/lesson/aws-ai-services)　第 14 課 / 共 18 課 · 約 7 分鐘

**依文字、文件、影像、語音、搜尋、推薦與人工審核的需求，選對 AWS 託管服務。**

### 讀完這課你會

*   依輸入類型挑對 AWS 託管服務
*   分清 Mechanical Turk、Ground Truth 與 A2I
*   判斷該用託管服務還是自己管運算資源

*【選型原則】*

## 先問要處理什麼，再選服務

> 🏠 **生活比喻**
>
> AWS AI 託管服務像**一排專科診所**：先確定是眼睛還是牙齒的問題（文字、影像、語音），再掛對應的科。

AWS 的 AI 託管服務提供事先訓練好的能力，讓團隊不必自己蒐集資料、訓練模型、管理推論基礎設施。適合需求明確、想快速整合標準 AI 功能的情境。

選型時先確認四件事：輸入是文字、文件、影像還是語音？輸出要分析、轉換還是互動？需不需要客製模型？有沒有延遲、隱私、合規與人工審核的要求？

*【文字與文件】*

## Comprehend、Translate、Textract 與 Kendra 各司其職

> 🏠 **生活比喻**
>
> - Comprehend＝**讀心術**：看懂文字的情緒、重點
> - Translate＝**翻譯員**
> - Textract＝**掃描器加打字員**：把紙本表格變成資料
> - Kendra＝**公司內部的搜尋引擎**

| 服務 | 輸入與輸出 | 典型用途 |
| --- | --- | --- |
| Amazon Comprehend | 文字 → 語言、實體、關鍵詞、情緒或主題 | 評論分析、文件分類 |
| Amazon Translate | 來源語言文字 → 目標語言文字 | 即時或批次翻譯 |
| Amazon Textract | 掃描文件或圖片 → 文字、表格與表單欄位 | 發票、申請表、身分文件處理 |
| Amazon Kendra<br>（不再開放新客戶） | 自然語言問題 → 排序後的企業搜尋結果 | 跨多個企業資料來源搜尋 |

Comprehend 的重點是「理解文字」；Textract 的重點是「從文件版面把內容取出來」；Kendra 則是「找到正確的文件」。它們可以串在一起用，不是互相取代。

**服務近況（2026 年 9 月）**：Amazon Kendra 自 2026 年 7 月 30 日起不再開放新客戶，既有客戶可以照常使用，AWS 建議新的搜尋應用改用 Amazon Bedrock 的知識庫[出處](https://docs.aws.amazon.com/kendra/latest/dg/kendra-availability-change.html)。AIF-C01 考試指南 v1.4 仍把 Kendra 列在考試範圍[出處](https://d1.awsstatic.com/training-and-certification/docs-ai-practitioner/AWS-Certified-AI-Practitioner_Exam-Guide.pdf)，所以考題照舊會出現；實務上開新專案已經選不到它。

Comprehend 則是關掉其中幾項功能，不是整個服務：主題建模（topic modeling，從一堆文件裡自動歸納出共同主題）、事件偵測與提示安全分類這三項不再開放新客戶，過去 12 個月內用過的帳號不受影響[出處](https://docs.aws.amazon.com/comprehend/latest/dg/topic-modeling.html)。上表寫的「主題」指的就是這一項；語言、實體、關鍵詞與情緒那幾項照常可用。

*【影像與推薦】*

## Rekognition 看影像，Personalize 排內容

> 🏠 **生活比喻**
>
> - Rekognition＝**會認人認物的眼睛**
> - Personalize＝**很懂你的店員**，推薦你可能喜歡的東西

Amazon Rekognition 用來分析影像與影片，可以做物件、場景、人臉、文字與不當內容偵測；要辨識企業自己特有的物件時，可以評估自訂標籤功能。

Rekognition 同樣是關掉其中兩項功能：串流影片與大量影像分析自 2026 年 4 月 30 日起不再開放新客戶，過去 12 個月內用過的帳號不受影響，Rekognition 其他功能照常供應[出處](https://docs.aws.amazon.com/rekognition/latest/dg/rekognition-availability-changes.html)。所以上面講的影像分析定位仍然成立，存在 S3 的影片也照樣分析得了，只是「接即時影像串流做偵測」這條路新客戶走不了。

Amazon Personalize 用來建立個人化推薦與排序。它利用使用者、項目與互動資料，對不同使用者呈現不同的商品、內容或行銷結果。

> 💡 快速判斷：想知道「圖片裡有什麼」選 Rekognition；想知道「這位使用者下一個可能喜歡什麼」選 Personalize。

*【語音與對話】*

## Transcribe、Polly、Lex 與 Connect 的分工

> 🏠 **生活比喻**
>
> 電話客服的分工：
> - Transcribe＝**速記員**（語音→文字）
> - Polly＝**播音員**（文字→語音）
> - Lex＝**接線生的大腦**（聽懂意圖）
> - Connect＝**整個客服中心**

| 服務 | 核心工作 |
| --- | --- |
| Amazon Transcribe | 語音轉文字（Speech-to-Text） |
| Amazon Polly | 文字轉語音（Text-to-Speech） |
| Amazon Lex | 辨識對話意圖與必要欄位，建立聊天或語音機器人 |
| Amazon Connect | 建立雲端聯絡中心與來電流程 |

典型的電話客服流程長這樣：

```
客戶來電
→ Connect 接聽並執行聯絡流程
→ Lex 理解意圖
→ Lambda 或後端系統處理業務邏輯
→ Polly 把文字結果轉成語音
→ Connect 播放給客戶
```

只要會議逐字稿，用 Transcribe 就夠了；要聽懂「我要取消訂單」代表的意圖，才需要 Lex。

*【人力介入】*

## MTurk、Ground Truth 與 A2I 出現的時間點不同

> 🏠 **生活比喻**
>
> - MTurk＝**打工平台**，找人做小任務
> - Ground Truth＝**教材編輯部**，在訓練前幫資料標答案
> - A2I＝**品管員**，上線後 AI 沒把握的案子交給人複核

| 服務 | 定位 | 典型時間點 |
| --- | --- | --- |
| Amazon Mechanical Turk | 一般的群眾外包人力市場 | 任何可以拆分的人工任務 |
| SageMaker Ground Truth<br>（不再開放新客戶） | 建立高品質的訓練標籤 | 模型訓練前的資料準備階段 |
| Amazon Augmented AI（A2I）<br>（不再開放新客戶） | 把特定的模型預測交給真人審核 | 模型推論或生產流程當中 |

Ground Truth 像教材編輯部，負責在考試前整理好有答案的題庫；A2I 像上線後的品管站，遇到低信心或高風險的結果就轉交真人。

**服務近況（2026 年 9 月）**：SageMaker Ground Truth[出處](https://docs.aws.amazon.com/sagemaker/latest/dg/sms.html)與 Amazon A2I[出處](https://docs.aws.amazon.com/sagemaker/latest/dg/a2i-use-augmented-ai-a2i-human-review-loops.html)都已經不再開放新客戶，既有客戶可以照常使用，AWS 不再替它們開發新功能。AIF-C01 考試指南 v1.4 仍把 A2I 列在考試範圍[出處](https://d1.awsstatic.com/training-and-certification/docs-ai-practitioner/AWS-Certified-AI-Practitioner_Exam-Guide.pdf)，所以考題照舊會出現；實務上開新專案已經選不到它們。Mechanical Turk 不在這個名單裡，仍然開放。

```
輸入 → AI 或自訂模型
          ├─ 符合自動處理條件 → 回傳結果
          └─ 需要人工判斷 → A2I 審核 → 最終結果
```

*【基礎設施】*

## 託管 AI 服務與自己管運算資源

> 🏠 **生活比喻**
>
> - 託管服務＝**叫外送**，直接吃
> - EC2 自己跑模型＝**自己租廚房做菜**，彈性大但什麼都要顧

Amazon EC2 提供虛擬伺服器；EBS 是可以掛到 EC2 上的區塊儲存。自己在 EC2 上訓練或部署模型時，要選執行個體、裝框架、設定擴展並維護系統。

訓練通常需要大量平行運算，可以選 GPU 或 AWS Trainium；推論工作則可依模型需求考慮 GPU 或 AWS Inferentia。硬體名稱只提供方向，實際效能與成本還是要靠自己的模型做基準測試。

Trn1 執行個體最多搭載 16 顆 Trainium 晶片[出處](https://aws.amazon.com/ec2/instance-types/trn1/)，最大的規格正好是 16 顆。AWS 宣稱它相較同類執行個體最多可省下五成的訓練成本，這是供應商自己的比較基準，實際省多少要看你的模型。

> 📝 查證更正：原筆記寫「例如 Trn1 Instance 擁有超過 16 Trainium 加速器」，查證後更正：AWS 官方寫的是 Trn1 執行個體「最多」搭載 16 顆 Trainium 晶片，最大的 trn1.32xlarge 正好是 16 顆，不是超過 16 顆

Inferentia 的兩個數字其實來自不同世代[出處](https://aws.amazon.com/ai/machine-learning/inferentia/)：第一代 Inferentia 宣稱吞吐量最高提升 2.3 倍、每次推論成本最多降低 70%；「四倍吞吐量」則是第二代 Inferentia2 相對於第一代的比較，不能把兩句併成同一句。

> 📝 查證更正：原筆記在 AWS Inferentia 底下寫「吞吐量提升四倍，成本降低 70%」，查證後更正：這兩個數字來自不同世代——第一代 Inferentia 宣稱吞吐量最高提升 2.3 倍、每次推論成本最多降低 70%；四倍吞吐量是第二代 Inferentia2 相對於第一代 Inferentia 的比較

> 託管服務適合直接取得某項特定能力；EC2 或 SageMaker 適合需要自訂模型、框架與運算環境的工作。

### 🗺️ 比喻對照表

| 技術名詞 | 生活比喻 |
| --- | --- |
| Comprehend | 讀懂文字的讀心術 |
| Textract | 掃描器加打字員 |
| Transcribe / Polly | 速記員 / 播音員 |
| Lex | 接線生的大腦 |
| Ground Truth / A2I | 教材編輯部 / 上線後品管員 |

### 重點整理

*   文字洞察找 Comprehend，文件擷取找 Textract；企業搜尋對應的是 Kendra，但它已不再開放新客戶。
*   影像分析找 Rekognition，推薦排序找 Personalize。
*   語音轉文字找 Transcribe，文字轉語音找 Polly，聽懂意圖找 Lex。
*   訓練前做標註對應 Ground Truth、上線後人工審核對應 A2I，兩者都已不再開放新客戶。
*   硬體的效能與省錢數字都是供應商的比較基準，要用自己的模型實測。

## 隨堂測驗

**Q1. 公司要從掃描進來的發票擷取文字、表格與欄位，應該優先用哪個服務？**

- (A) Amazon Textract
- (B) Amazon Comprehend
- (C) Amazon Kendra
- (D) Amazon Rekognition

<details><summary>看答案</summary>

**答案：(A)** Textract 專門從文件影像擷取文字、表格與表單資料；Comprehend 處理的是已經是文字的內容。

</details>

**Q2. 要判斷大量產品評論是正面還是負面，最適合哪個服務？**

- (A) Amazon Comprehend
- (B) Amazon Transcribe
- (C) Amazon Translate
- (D) Amazon Personalize

<details><summary>看答案</summary>

**答案：(A)** 情緒、實體與主題這類文字分析是 Comprehend 的工作；Translate 只做語言轉換。

</details>

**Q3. 哪個服務負責把會議錄音轉成逐字稿？**

- (A) Amazon Transcribe
- (B) Amazon Polly
- (C) Amazon Lex
- (D) Amazon Connect

<details><summary>看答案</summary>

**答案：(A)** Transcribe 是語音轉文字；Polly 方向相反，Lex 負責理解意圖。

</details>

**Q4. 電話客服必須聽懂來電者「要查詢帳戶餘額」這個意圖，哪個服務負責意圖辨識？**

- (A) Amazon Lex
- (B) Amazon Transcribe
- (C) Amazon Polly
- (D) Amazon Connect

<details><summary>看答案</summary>

**答案：(A)** Lex 是對話式 AI，負責自然語言理解與意圖辨識；Connect 管的是接聽與流程。

</details>

**Q5. 模型已經部署，低信心的貸款判斷必須交由員工確認，應該用哪個服務？**

- (A) Amazon Augmented AI（A2I）
- (B) SageMaker Ground Truth
- (C) Amazon Mechanical Turk
- (D) Amazon Comprehend

<details><summary>看答案</summary>

**答案：(A)** A2I 是生產推論流程中的人工審核；Ground Truth 著重的是訓練前的資料標註。

</details>

**Q6. 公司要替大量訓練圖片建立物件邊界框標籤，應該優先用哪個服務？**

- (A) SageMaker Ground Truth
- (B) Amazon Augmented AI（A2I）
- (C) Amazon Rekognition 的自訂標籤
- (D) Amazon Personalize

<details><summary>看答案</summary>

**答案：(A)** Ground Truth 是建立與管理訓練標籤的服務；A2I 處理的是上線後的預測審核。

</details>

**Q7. 購物網站希望依每位使用者的互動紀錄排序商品，該選哪個服務？**

- (A) Amazon Personalize
- (B) Amazon Rekognition
- (C) Amazon Kendra
- (D) Amazon Textract

<details><summary>看答案</summary>

**答案：(A)** Personalize 用使用者、項目與互動資料做個人化推薦與排序。

</details>

**Q8. 哪一項最能說明託管 AI 服務的優勢？**

- (A) 可以直接用現成的預訓練能力，減少自行建模與維運的工作
- (B) 一定比任何自訂模型更準確
- (C) 完全不必再處理權限與隱私問題
- (D) 價格固定，不會隨用量或區域改變

<details><summary>看答案</summary>

**答案：(A)** 託管服務降低的是建模與基礎設施負擔，品質、安全、成本與合規還是要自己評估。

</details>
