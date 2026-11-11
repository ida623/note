# 15. SageMaker

> 來源：[筆記平台 · 雲端 AWS 與 GCP](https://hhtim.github.io/notes-platform/cloud/#/lesson/sagemaker)　第 15 課 / 共 18 課 · 約 9 分鐘

**掌握 SageMaker 從資料準備、訓練與推論，到可解釋性、監控與治理的完整生命週期。**

### 讀完這課你會

*   把機器學習流程對應到 SageMaker 功能
*   依延遲與流量型態選對推論模式
*   說出 Clarify、Model Monitor、Model Cards 各管什麼

*【平台總覽】*

## SageMaker 是一條從頭到尾的機器學習工作平台

Amazon SageMaker 協助開發者與資料科學家準備資料、建立與訓練模型、調整超參數、部署推論服務與監控模型。AWS 管底層資源的配置，團隊仍然要負責問題定義、資料品質、模型選擇與治理。

名字有變過：AWS 在 2024 年 12 月把原本的 Amazon SageMaker 更名為 Amazon SageMaker AI，「Amazon SageMaker」這個名字則改指涵蓋資料、分析與 AI 的新一代整合平台[出處](https://docs.aws.amazon.com/sagemaker/latest/dg/whatis.html)。這次更名沒有改動任何既有功能的名稱，所以本課講的 Data Wrangler、Feature Store、Clarify 這些都還是同一個東西；現在的文件標題用的是 SageMaker AI。

```
資料 → 清理與特徵工程 → 訓練與調參
→ 評估 → 部署 → 推論 → 監控 → 更新
```

SageMaker 可以用內建演算法，也能搭配常見的機器學習框架與自訂容器。Studio 提供整合式的開發介面；Canvas 則面向希望少寫程式或不寫程式就建模型的使用者。

*【資料準備】*

## Data Wrangler 整理資料，Feature Store 管理特徵

SageMaker Data Wrangler 用來選取、探索、清理、視覺化與轉換表格或影像資料，也能協助切分訓練、驗證與測試資料。做好的資料流程可以接到其他 SageMaker 工作流程。

SageMaker Feature Store 是集中管理特徵的地方，讓訓練和推論重複使用同一份定義，降低「訓練時算一套、上線時算另一套」造成的偏差。

| 儲存型態 | 目的 | 資料特性 |
| --- | --- | --- |
| 線上儲存 | 低延遲取得最新特徵，支援即時推論 | 依識別鍵快速查目前的值 |
| 離線儲存 | 模型訓練、批次分析與歷史回測 | 保留歷史資料並支援分析查詢 |

*【標註與預建資源】*

## Ground Truth 建標籤，JumpStart 幫你起步

SageMaker Ground Truth 是資料標註服務，可以把人工工作團隊與自動化流程整合起來，建立影像、文字等訓練資料。它也能支援蒐集或評估人類回饋，例如讓評審比較不同模型的回答。

**服務近況（2026 年 9 月）**：SageMaker Ground Truth 已經不再開放新客戶，既有客戶可以照常使用，AWS 不再替它開發新功能[出處](https://docs.aws.amazon.com/sagemaker/latest/dg/sms.html)。AIF-C01 考試指南 v1.4 沒有單獨點名 Ground Truth，但 SageMaker 整體在考試範圍內[出處](https://d1.awsstatic.com/training-and-certification/docs-ai-practitioner/AWS-Certified-AI-Practitioner_Exam-Guide.pdf)；實務上開新專案已經選不到它。

SageMaker JumpStart 提供可以瀏覽、試用、客製化與部署的預訓練模型，以及針對常見商業問題的預建解決方案。模型中心偏向挑單一模型元件；解決方案範本則把多個元件組成比較完整的使用案例。

*【訓練】*

## 參數與超參數不要混為一談

模型參數是訓練過程從資料裡學到的值；超參數（Hyperparameter）則是訓練前就要設好的選項，例如學習率、樹的深度或批次大小。Automatic Model Tuning 會試不同的組合，依你指定的指標找出表現較好的設定。

常見的任務與演算法包括：

*   線性方法：做迴歸或分類。
*   K-近鄰：依鄰近的樣本做預測。
*   K-means：在未標註資料中找群組。
*   主成分分析（PCA）：降低特徵維度。
*   異常偵測、文字與影像演算法：處理對應的資料型態。

*【部署選型】*

## 四種推論模式，看延遲、流量與單次工作大小

| 模式 | 適合情境 | 主要取捨 |
| --- | --- | --- |
| Real-time Inference | 持續流量、需要低延遲互動 | 端點持續運行，要管容量與擴展 |
| Serverless Inference | 間歇或不可預測的互動流量 | 依使用情況啟動，但可能遇到冷啟動 |
| Asynchronous Inference | 單次請求處理很久或內容很大 | 先排進佇列，完成後再取結果或收通知 |
| Batch Transform | 整批離線資料的預測 | 不必維持即時端點，但不適合互動式回應 |

三個常考的數字：非同步推論適合最大 1GB 的內容、最長一小時的處理時間，而且沒有請求時可以把執行個體數量自動縮到零[出處](https://docs.aws.amazon.com/sagemaker/latest/dg/async-inference.html)；即時端點的單次請求內容上限則是 6,291,456 位元組，也就是 6 MB[出處](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_runtime_InvokeEndpoint.html)。

比較表常列「即時推論延遲最低、小於 100 毫秒」，這不是規格：即時推論的定位是有互動、需要低延遲的工作負載，沒有 100 毫秒的承諾[出處](https://docs.aws.amazon.com/sagemaker/latest/dg/realtime-endpoints.html)；實際延遲取決於模型、執行個體規格與內容大小。真正有規定的是另一個數字：模型容器必須在 60 秒內回應[出處](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_runtime_InvokeEndpoint.html)。

選擇順序可以簡化成：需要立即互動時比較 Real-time 與 Serverless；單筆工作很久或內容很大時考慮 Asynchronous；整批離線處理就選 Batch Transform。實際的限制與支援區域仍應查最新規格。

*【可解釋性與公平】*

## Clarify 回答「模型為什麼這樣判斷」

先分清楚兩個很像的詞：**可解讀性**（interpretability）講的是「看得懂模型內部怎麼把輸入變成輸出」，線性迴歸這種結構簡單的模型天生就比較好解讀；**可解釋性**（explainability）講的是「能不能把某個預測的原因，講成利害關係人聽得懂的說法」，就算模型內部很複雜，也可以用事後的說明技術補上。這裡講的都是後者。

SageMaker Clarify 協助偵測資料與模型的偏差，並解釋特徵怎麼影響預測。部署前可以檢查訓練資料是不是對特定群體不平衡；訓練後可以檢查模型結果有沒有出現不公平的差異。

全域解釋說明模型整體比較依賴哪些特徵；局部解釋則說明某一次預測是被哪些特徵推動的。SHAP 值（SHapley Additive exPlanations，一種把預測結果拆分成「每個特徵各推了多少」的計算方法）是常見的特徵歸因方法，但「知道模型依賴什麼」不等於「證明模型公平或因果正確」。

**服務近況（2026 年 9 月）**：SageMaker Clarify 已經不再開放新客戶，既有客戶可以照常使用，AWS 不再替它開發新功能，並建議改用 Clarify 內部本來就在用的 SHAP 開源套件搭配自建流程[出處](https://docs.aws.amazon.com/sagemaker/latest/dg/clarify-availability-change.html)。AIF-C01 考試指南 v1.4 的 Task 4.1 仍點名 SageMaker Clarify[出處](https://d1.awsstatic.com/training-and-certification/docs-ai-practitioner/AWS-Certified-AI-Practitioner_Exam-Guide.pdf)，所以考題照舊會出現；實務上開新專案已經選不到它。

*【治理與監控】*

## 文件、總覽、監控與權限各有工具

| 工具 | 用途 |
| --- | --- |
| Model Cards | 記錄模型用途、限制、風險、訓練與評估資訊 |
| Model Dashboard | 集中檢視模型狀態、風險與監控資訊 |
| Model Monitor<br>（不再開放新客戶） | 監控資料品質、模型品質、偏差或特徵歸因的漂移 |
| Role Manager<br>（不再開放新客戶） | 依工作角色建立符合最小權限原則的存取設定 |
| MLflow | 追蹤實驗、參數、指標與模型版本 |

**服務近況（2026 年 9 月）**：表中的 Model Monitor[出處](https://docs.aws.amazon.com/sagemaker/latest/dg/model-monitor.html)與 Role Manager[出處](https://docs.aws.amazon.com/sagemaker/latest/dg/role-manager.html)都已經不再開放新客戶，既有客戶可以照常使用，AWS 不再替它們開發新功能；Model Monitor 的替代路徑是三者組合：開源的 Amazon SageMaker AI 監控方案、Amazon QuickSight 治理儀表板、Amazon CloudWatch[出處](https://docs.aws.amazon.com/sagemaker/latest/dg/model-monitor-availability-change.html)。AIF-C01 考試指南 v1.4 的 Task 1.3 與 Task 4.1 都仍點名 SageMaker Model Monitor[出處](https://d1.awsstatic.com/training-and-certification/docs-ai-practitioner/AWS-Certified-AI-Practitioner_Exam-Guide.pdf)，所以考題照舊會出現；實務上開新專案已經選不到它們。

治理不是模型部署完才補文件，而是從資料來源、實驗、核准、部署到退役，都要留下責任歸屬與稽核線索。

*【負責任 AI】*

## 好模型不只要準，也要值得被使用

*   **公平性**：避免對特定群體造成不合理的差別待遇。
*   **可解釋性**：理解模型怎麼形成結果。
*   **隱私與安全**：保護資料並限制未授權的存取。
*   **透明度**：清楚說明用途、能力與限制。
*   **真實性與穩健性**：在一般與意外情況下都維持可靠表現。
*   **治理**：建立政策、流程、稽核與責任制度。
*   **安全性**：降低對個人與社會造成傷害的可能。
*   **可控性**：保留人類監督、介入與停止系統的能力。

### 重點整理

*   Data Wrangler 準備資料、Feature Store 管特徵、Ground Truth 做標註、JumpStart 提供預建模型。
*   Clarify 檢查偏差並解釋預測；Model Monitor 盯上線後的變化；Model Cards 留治理文件。
*   Ground Truth、Clarify、Model Monitor、Role Manager 都已不再開放新客戶，考試仍會考，新專案選不到。
*   即時推論單次內容上限 6 MB；非同步推論可到 1 GB、最長一小時，而且可以縮到零。
*   即時推論沒有毫秒數的承諾，但規定模型容器要在 60 秒內回應。
*   原本的 SageMaker 現在叫 Amazon SageMaker AI。

## 隨堂測驗

**Q1. 團隊要用視覺化方式清理、轉換並探索訓練資料，該用哪個 SageMaker 功能？**

- (A) Data Wrangler
- (B) Model Cards
- (C) Model Monitor
- (D) Role Manager

<details><summary>看答案</summary>

**答案：(A)** Data Wrangler 專門處理資料探索、清理、轉換與特徵工程；另外三個分別管文件、監控與權限。

</details>

**Q2. 訓練與即時推論必須重複使用同一份客戶特徵定義，哪個功能最合適？**

- (A) Feature Store
- (B) Data Wrangler
- (C) Ground Truth
- (D) JumpStart

<details><summary>看答案</summary>

**答案：(A)** Data Wrangler 可以做出特徵，但集中儲存與共享、確保訓練與推論一致的是 Feature Store。

</details>

**Q3. 網站流量間歇出現，而且可以容忍冷啟動，應該優先評估哪種推論模式？**

- (A) Serverless Inference
- (B) 持續運行的 Real-time Inference
- (C) Batch Transform
- (D) Asynchronous Inference

<details><summary>看答案</summary>

**答案：(A)** Serverless 適合間歇或不可預測的互動流量，代價是可能遇到冷啟動。

</details>

**Q4. 每晚要對整份 S3 資料集做離線預測，不需要即時端點，該選什麼？**

- (A) Batch Transform
- (B) Real-time Inference
- (C) Serverless Inference
- (D) Asynchronous Inference

<details><summary>看答案</summary>

**答案：(A)** 整批離線資料一次跑完最適合 Batch Transform；非同步推論處理的仍然是一筆一筆的請求。

</details>

**Q5. 單次請求的內容大約 200 MB，處理要花二十分鐘，呼叫端不必在線上等。哪種模式最合適？**

- (A) Asynchronous Inference
- (B) Real-time Inference
- (C) Serverless Inference
- (D) Batch Transform

<details><summary>看答案</summary>

**答案：(A)** 即時端點單次請求的內容上限是 6 MB，200 MB 送不進去；非同步推論可到 1 GB、最長一小時，而且呼叫端不必在線上等。

</details>

**Q6. 要解釋單一筆貸款申請為什麼被模型判為高風險，該用哪個功能？**

- (A) SageMaker Clarify 的局部解釋
- (B) SageMaker Clarify 的全域解釋
- (C) SageMaker Model Monitor 的漂移報告
- (D) SageMaker Model Cards 的風險欄位

<details><summary>看答案</summary>

**答案：(A)** 全域解釋講的是模型整體依賴哪些特徵；要分析某一次預測，要看局部解釋。

</details>

**Q7. Automatic Model Tuning 主要在調什麼？**

- (A) 訓練前指定的超參數組合
- (B) 模型訓練後學到的權重值
- (C) 訓練資料的人工標籤
- (D) 模型卡片裡的風險敘述

<details><summary>看答案</summary>

**答案：(A)** 權重是訓練時學出來的參數；自動調參試的是學習率、批次大小這類事前設定。

</details>

**Q8. 上線模型的輸入資料分布改變了，需要持續偵測漂移，該用哪個功能？**

- (A) SageMaker Model Monitor
- (B) SageMaker Clarify
- (C) SageMaker Ground Truth
- (D) SageMaker Feature Store

<details><summary>看答案</summary>

**答案：(A)** Model Monitor 專門追蹤上線後的資料品質、模型品質與相關漂移。

</details>
