# 17. AIF 模擬考精選與觀念 I

> 🏠 **生活化版本**：每個段落開頭的「生活比喻」先用日常情境帶你抓到感覺，接著再看原本的技術說明與程式碼；篇末有「比喻對照表」可以快速複習。

> 來源：[筆記平台 · 雲端 AWS 與 GCP](https://hhtim.github.io/notes-platform/cloud/#/lesson/aif-exam-notes-1)　第 17 課 / 共 18 課 · 約 18 分鐘

**用七組主題統整生成參數、RAG、資料切分、SageMaker 工具、負責任 AI 與 AWS 治理的判題方式。**

### 讀完這課你會

*   看題目先抓出它在問哪一類問題
*   分清生成參數、資料切分與治理服務的職責
*   排除「功能存在但不適用」的選項

*【主題一｜生成式 AI 的模型與推論】*

## 從「模型怎麼學」到「回答怎麼產生」

> 🏠 **生活比喻**
>
> 基礎模型像**讀過整座圖書館的通才**，回答時是**一個字一個字接龍**，每次挑最可能的下一個字。

**觀念整理**

基礎模型（Foundation Model，FM）通常先用大量未標記資料做自我監督學習。做法像是把教材中的一部分遮起來，讓模型自己猜回來；答案直接從原始資料產生，不必逐筆請人標。

模型參數（model parameters）是訓練時從資料學到的內部數值，例如神經網路的權重與偏置；超參數（hyperparameters）則是控制訓練方式的外部設定，例如學習率、批次大小與訓練輪數。前者像學生腦中裝進去的知識，後者像課程安排與讀書方法。

模型是一個 token 一個 token 往下生成的（token 是模型切字的最小單位，大約是一個字或半個字）。生成下一個 token 時，Temperature 調整機率分布的平坦程度，所以常用來控制隨機性；Top K 只保留固定數量的高機率候選；Top P 保留累積機率達到門檻的候選集合，所以候選數量是浮動的；Stop sequences 則是遇到指定內容就停止生成。

| 題目裡的線索 | 對應概念 | 辨識重點 |
| --- | --- | --- |
| 回答更穩定或更有創意 | Temperature | 調的是隨機性，不是候選數量 |
| 固定保留幾個候選 token | Top K | K 就是那個固定數量 |
| 依累積機率形成候選池 | Top P | 候選數會隨機率分布浮動 |
| 遇到特定字串就結束 | Stop sequences | 控制停止條件，不控制創意 |

> 💡 代表題：客服模型的回答太制式，公司希望增加文字變化，但不需要指定停在哪裡，應該優先調哪個設定？

**正解**：Temperature。它直接影響取樣的隨機程度，調高之後輸出通常更多樣。

**為什麼**：題幹問的是「創意與變化」，不是候選池大小，也不是輸出要在哪裡結束。

**常見誘答**：Top P 也會影響多樣性，但題目直接用「創造力、隨機性」描述時，一般以 Temperature 最貼切；Stop sequences 只負責停止生成。

> 💡 代表題：系統要依候選 token 的累積機率門檻來決定取樣範圍，該用什麼？

**正解**：Top P，也叫核心取樣（nucleus sampling）。

**為什麼**：Top P 從高機率的 token 開始累加，加到門檻為止，所以候選池大小不是固定的。

**常見誘答**：Top K 固定的是候選數量；Temperature 改的是分布形狀，不等於直接建立累積機率候選池。

*【主題二｜補充私有知識與多模態理解】*

## 先分清楚 RAG、微調與嵌入

> 🏠 **生活比喻**
>
> - RAG＝**考試帶小抄**，資料常更新也沒問題
> - 微調＝**職前訓練**，改變它做事的方式
> - 嵌入＝**把文字變成地圖座標**，意思相近的放得近

**觀念整理**

企業希望模型依照經常更新的內部文件回答問題時，可以用檢索增強生成（Retrieval Augmented Generation，RAG）。流程是先找出相關的文件片段，再連同問題交給模型作答，像開卷考先翻到相關那一頁，而不是重新訓練整個模型。

Amazon Bedrock Knowledge Bases（題庫與較舊的資料常沿用舊名 Knowledge Bases for Amazon Bedrock）可以協助建立 RAG 流程。微調（fine-tuning）比較適合調整模型的行為、語氣或特定任務模式；來自人類回饋的強化學習（Reinforcement Learning from Human Feedback，RLHF）則是用人類偏好資料改善模型行為。這兩者都不等同於即時檢索企業文件。

嵌入模型（embedding model）會把文字、影像等內容轉成可以互相比較的向量。多模態嵌入把不同資料型態放進同一個語意空間，適合跨文字與影像的搜尋、配對、推薦或分類；如果任務還要求直接理解複雜輸入並產生完整回答，那就要評估多模態生成模型，或用嵌入檢索搭配生成模型。

> 企業文件 → 分段與嵌入 → 相似度檢索 → 把相關內容放進提示 → 基礎模型生成回答

> 💡 代表題：保險公司的商品條款經常更新，希望聊天機器人依最新版的內部文件回答，又不想每次更新都重新訓練模型，該怎麼做？

**正解**：用 Amazon Bedrock Knowledge Bases 建立 RAG。

**為什麼**：知識留在外部資料來源，更新後重新同步或重建索引就好，不必把每次變更都訓練進模型參數。

**常見誘答**：微調不是企業知識查詢的預設解法；RLHF 的重點是學人類偏好，不是檢索最新文件。

> 💡 代表題：電商要用商品照片與文字描述，找出語意相近的商品，重點是跨模態搜尋而不是產生新影像，哪一類模型比較切題？

**正解**：多模態嵌入模型。

**為什麼**：它能讓相關的文字與影像在同一個向量空間中彼此靠近，方便搜尋與配對。

**常見誘答**：純文字模型沒辦法直接表示影像；卷積神經網路側重影像處理，未必能完成文字與影像的語意對齊；多模態生成模型功能更廣，但只需要檢索時未必是最精簡的方案。

*【主題三｜模型是不是真的學會了】*

## 偏差、變異、資料切分與過度擬合

> 🏠 **生活比喻**
>
> - 高偏差＝**箭都射偏同一邊**
> - 高變異＝**箭四散**
> - 過度擬合＝**只會背考古題，換題就不會**

**觀念整理**

高偏差（high bias）表示模型的假設過度簡化，連訓練資料的重要規律都抓不到，常造成擬合不足（underfitting）。高變異（high variance）表示模型對訓練資料的小變動很敏感，容易把雜訊也記住，常造成過度擬合（overfitting）。

訓練集用來學模型參數；驗證集用來比較模型與調整超參數，也可以用交叉驗證取代獨立的驗證集；測試集要留到最後，評估選定的模型對未見資料的泛化能力。如果反覆依測試結果修改模型，測試集也會被間接「學進去」。

降低過度擬合的方法包括交叉驗證、正規化（regularization）、決策樹剪枝（pruning）、增加多樣化的資料，以及神經網路的 Dropout（訓練時隨機關掉一部分神經元，逼模型不要只靠固定那幾條路徑作答）。核心精神都是不讓模型只記住訓練樣本裡的偶然細節。

題目常把「取得並準備高品質的資料」當成機器學習專案的瓶頸。特徵工程（feature engineering）則是把原始資料選擇、轉換或組合成更有意義的模型輸入，例如從交易時間建立「是不是週末」這個特徵。

> 💡 代表題：模型在訓練資料上幾乎完美，換到新資料表現卻大幅下降。這是哪種問題，該怎麼處理？

**正解**：高變異造成的過度擬合；可以用交叉驗證、正規化、剪枝或增加多樣化的資料。

**為什麼**：訓練好、未見資料差，是模型記住訓練細節而沒能泛化的典型訊號。

**常見誘答**：增加模型複雜度通常讓過度擬合更嚴重；縮小訓練資料也會讓模型更容易把少量樣本背起來。

> 💡 代表題：團隊已經選好模型與超參數，要拿到比較公正的最終泛化評估，該用哪一份資料？

**正解**：從頭到尾沒參與訓練與調整的測試集。

**為什麼**：驗證集已經被拿去選模型或調超參數了，測試集才是最後的獨立評量。

**常見誘答**：訓練集只反映模型對已見資料的擬合；把測試集拿來調參會造成評估洩漏。

*【主題四｜學習方式與人類參與】*

## 標籤、互動回饋與人工審核，角色各不相同

> 🏠 **生活比喻**
>
> - 監督式學習＝**對答案學**
> - RLHF＝**老師給每次回答打分數**，學會人喜歡的回答方式
> - 人工審核＝**最後由真人把關**

**觀念整理**

監督式學習（supervised learning）從已標記的輸入與答案學出預測關係。強化學習（reinforcement learning）則讓代理人（agent）在環境中採取行動，依獎勵或懲罰學出能提高長期累積報酬的策略。

Amazon SageMaker Ground Truth 是機器學習的資料標記工作流程；Amazon Mechanical Turk 是可以承接各種人類智慧任務的眾包市場。Ground Truth 可以使用不同的人力來源，也能支援蒐集人類對模型回應的比較、排序等偏好資料，作為 RLHF 流程的一部分。

Amazon Augmented AI（Amazon A2I）用來建立預測結果的人工審核流程，例如把低信心或高風險的個案交給人工確認。它處理的是推論流程中的人工監督，不等同於建立一般的訓練標籤資料集。

**服務近況（2026 年 9 月）**：SageMaker Ground Truth[出處](https://docs.aws.amazon.com/sagemaker/latest/dg/sms.html)、Amazon A2I[出處](https://docs.aws.amazon.com/sagemaker/latest/dg/a2i-use-augmented-ai-a2i-human-review-loops.html)與 SageMaker Model Monitor[出處](https://docs.aws.amazon.com/sagemaker/latest/dg/model-monitor.html)都已經不再開放新客戶，既有客戶可以照常使用，AWS 不再替它們開發新功能。AIF-C01 考試指南 v1.4 仍把 A2I 列在考試範圍、Task 1.3 與 Task 4.1 也仍點名 Model Monitor[出處](https://d1.awsstatic.com/training-and-certification/docs-ai-practitioner/AWS-Certified-AI-Practitioner_Exam-Guide.pdf)，所以考題照舊會出現；實務上開新專案已經選不到它們。Mechanical Turk 不在這個名單裡，仍然開放。

> 💡 代表題：詐欺偵測模型需要持續監控，而且低信心的交易必須交給分析師覆核，該搭配哪些服務？

**正解**：Amazon SageMaker Model Monitor 搭配 Amazon A2I。

**為什麼**：Model Monitor 負責觀察上線模型與資料的狀況；A2I 負責把符合規則的預測送進人工審核。

**常見誘答**：Ground Truth 側重資料標記；Feature Store 管理特徵；Data Wrangler 處理資料準備，三個都取代不了「生產監控加人工覆核」這個組合。

> 💡 代表題：團隊要蒐集標註員對兩個聊天機器人回答的偏好排序，作為訓練獎勵模型的資料，可以用什麼？

**正解**：Amazon SageMaker Ground Truth。

**為什麼**：Ground Truth 能組織人工標記工作，產出比較與排序這類高品質的標記資料。

**常見誘答**：把 Ground Truth 說成「會自動取代人類回饋」或「即時決策引擎」都不對，它做的就是把人力標記流程組織起來。

*【主題五｜SageMaker 工具怎麼分工】*

## 從資料準備、建模到治理的關鍵字配對

> 🏠 **生活比喻**
>
> SageMaker 各工具像**廚房分區**：Canvas 是**給不會寫程式的人用的點餐機**，Data Wrangler 是洗切區，Model Monitor 是品管。

**觀念整理**

SageMaker Canvas 面向想用視覺化介面建立預測流程的使用者；Data Wrangler 聚焦資料的選擇、清理、轉換、探索與視覺化。看到「不寫程式建立模型」偏 Canvas；看到「用單一視覺介面準備資料」偏 Data Wrangler。

Feature Store 是集中儲存、共享與管理模型特徵的地方，可以降低訓練與推論的特徵計算方式不一致造成的落差（training-serving skew）。Model Dashboard 提供跨模型的集中檢視入口；Model Monitor 則持續檢查已部署模型的資料與品質問題。

SageMaker Clarify 著重偏見偵測與模型說明；Ground Truth 著重資料標記；Model Dashboard 著重跨模型的集中治理。考題常把這些真實存在的功能混在一起，所以要先圈出題目的動詞：準備、儲存、標記、解釋、監控，還是集中查看。

| 需求動詞 | 優先聯想到的工具 |
| --- | --- |
| 用視覺化方式建立模型並產生預測 | SageMaker Canvas |
| 清理、探索、轉換與視覺化資料 | SageMaker Data Wrangler |
| 集中儲存與重複使用特徵 | SageMaker Feature Store |
| 建立標記資料集 | SageMaker Ground Truth<br>（不再開放新客戶） |
| 偵測偏見、說明預測 | SageMaker Clarify<br>（不再開放新客戶） |
| 持續觀察已部署的模型 | SageMaker Model Monitor<br>（不再開放新客戶） |
| 集中查看與治理多個模型 | SageMaker Model Dashboard |

**服務近況（2026 年 9 月）**：表中標註的三個——Ground Truth、Clarify[出處](https://docs.aws.amazon.com/sagemaker/latest/dg/clarify-availability-change.html)與 Model Monitor——都已經不再開放新客戶，既有客戶可以照常使用。AIF-C01 考試指南 v1.4 的 Task 4.1 仍點名 Clarify 與 Model Monitor[出處](https://d1.awsstatic.com/training-and-certification/docs-ai-practitioner/AWS-Certified-AI-Practitioner_Exam-Guide.pdf)，所以這張配對表對考試仍然有效；實務上開新專案已經選不到這三個。

> 💡 代表題：業務分析師希望用點選的方式匯入資料、建立模型並產生預測，不想寫太多程式，該選哪個工具？

**正解**：Amazon SageMaker Canvas。

**為什麼**：題目涵蓋的是從資料到建模再到預測的完整視覺化流程，不只是資料清理。

**常見誘答**：Data Wrangler 主要解決資料準備；Clarify 解決偏見與說明；Model Dashboard 解決集中治理。

> 💡 代表題：多個團隊必須共用顧客特徵，還要確保訓練與線上推論用的是一致的特徵定義，該選哪個服務？

**正解**：Amazon SageMaker Feature Store。

**為什麼**：它把特徵集中管理，方便發現、重用，並維持訓練與推論的一致性。

**常見誘答**：Data Wrangler 可以做出特徵，但它不是特徵的中央儲存與共享層；Ground Truth 管的是標記工作。

*【主題六｜負責任 AI、文件與內容安全】*

## 透明、公平、監控與防護不是同一件事

> 🏠 **生活比喻**
>
> - 透明＝**說得出為什麼**
> - 公平＝**不偏心**
> - 監控＝**上線後持續巡檢**
> - 防護＝**擋下不該發生的事**

**觀念整理**

可解讀性（interpretability）偏向理解模型內部如何由輸入形成輸出；可解釋性（explainability）偏向把預測的原因轉成利害關係人聽得懂的說法。簡單的模型可能天生比較好解讀，複雜的模型則可以用事後說明技術提高可解釋性。

SageMaker Clarify 可以檢查偏見並說明模型預測；Model Monitor 負責觀察上線後資料或模型品質的變化。前者回答「模型為什麼這樣判斷、對群體公不公平」，後者回答「模型上線後有沒有逐漸偏離預期」。

SageMaker Model Cards 是組織為自己某個特定模型建立的治理文件，可以記錄預期用途、風險、訓練與評估資訊；AWS AI Service Cards 則是由 AWS 說明它自己那些 AI 服務的用途、限制與潛在影響。兩者都是透明度工具，但建立者與描述的對象不同。

公開的生成式 AI 應用如果需要比較不同基礎模型，可以用 Amazon Bedrock 的模型評估功能；如果要限制有害內容、敏感資訊或禁止的主題，則用 Amazon Bedrock Guardrails（舊名 Guardrails for Amazon Bedrock）。模型評估處理「選哪一個」，Guardrails 處理「哪些內容不能通過」。

> 💡 代表題：團隊既要比較多個基礎模型的回答品質，也要擋住公開應用輸出有害內容，該用哪兩項能力？

**正解**：Amazon Bedrock 的模型評估功能，加上 Amazon Bedrock Guardrails。

**為什麼**：前者支援模型之間的比較，後者對輸入與輸出套用安全政策。

**常見誘答**：SageMaker Clarify 偏向偏見與說明；Model Monitor 偏向生產監控；Amazon Comprehend 是文字分析服務，不是 Bedrock 生成內容的主要護欄。

> 💡 代表題：公司要記錄自建信用模型的預期用途、風險評等、訓練指標與評估觀察，該用哪一種文件？

**正解**：SageMaker Model Cards。

**為什麼**：文件描述的是公司自己的那個特定模型，以及它的治理資訊。

**常見誘答**：AI Service Cards 說明的是 AWS 提供的 AI 服務的用途與限制，不是替客戶保存每個自建模型的生命週期紀錄。

*【主題七｜安全、合規與私有連線】*

## 先辨認是在找漏洞、蒐證，還是查報告

> 🏠 **生活比喻**
>
> - Inspector＝**驗屋師**，找漏洞
> - CloudTrail＝**監視器**，記誰做了什麼
> - Artifact＝**合規文件櫃**，拿認證報告
> - Config＝**設定變更紀錄**

**觀念整理**

Amazon Inspector 著重自動化的漏洞管理，以及非預期的網路暴露偵測；AWS Audit Manager 著重持續稽核、證據蒐集與合規評估；AWS Artifact 提供 AWS 自己的合規文件；AWS Config 則記錄與評估 AWS 資源的組態。

AWS CloudTrail 記錄 API 與帳戶活動，可以當稽核證據的來源，但它本身不等於一套完整的自動化稽核管理流程。AWS Trusted Advisor 提供最佳實務建議，也不是專門用來建立合規證據與評估報告的。

VPC 裡沒有網際網路連線的工作負載，如果要私下存取 Amazon S3，可以用適用於 S3 的 VPC 端點。NAT 閘道與網際網路閘道都是在提供網際網路路徑，不符合「不得經由公用網際網路」這個核心限制。

**快速口訣**：掃漏洞找 Inspector；蒐證稽核找 Audit Manager；下載 AWS 合規文件找 Artifact；檢查資源組態找 Config。

**服務近況（2026 年 9 月）**：AWS Audit Manager 正在轉為維護模式，2026 年 4 月 30 日起無法在新帳戶啟用，既有客戶可以在原帳戶與區域照常使用，AWS 建議新的合規需求改用 AWS Config 的 Conformance Pack[出處](https://docs.aws.amazon.com/audit-manager/latest/userguide/audit-manager-availability-change.html)。AIF-C01 考試指南 v1.4 仍把 AWS Audit Manager 列在考試範圍[出處](https://d1.awsstatic.com/training-and-certification/docs-ai-practitioner/AWS-Certified-AI-Practitioner_Exam-Guide.pdf)，所以上面那句口訣對考試仍然成立；實務上新帳戶已經開不了它。

> 💡 代表題：法遵團隊想持續稽核 AWS 的使用情況、自動蒐集證據，並依框架整理風險評估，該用什麼？

**正解**：AWS Audit Manager。

**為什麼**：題幹的核心動詞是「稽核、蒐證、依框架評估」。

**常見誘答**：Artifact 提供的是 AWS 自己的合規報告；CloudTrail 提供活動紀錄；Inspector 掃的是工作負載漏洞，三個都只是其中一塊。

> 💡 代表題：位在沒有網際網路的 VPC 裡的 SageMaker 工作負載要讀 S3，而且流量不能走公用網路，該怎麼設計？

**正解**：建立適用於 Amazon S3 的 VPC 端點，並搭配適當的路由與存取政策。

**為什麼**：VPC 端點讓工作負載透過 AWS 內部網路私下存取支援的服務。

**常見誘答**：NAT 閘道與網際網路閘道都是在建立網際網路路徑；SageMaker 的推論端點是提供模型推論，不是 S3 的私有連線方案。

### 🗺️ 比喻對照表

| 技術名詞 | 生活比喻 |
| --- | --- |
| RAG / 微調 / 嵌入 | 小抄 / 職前訓練 / 地圖座標 |
| 過度擬合 | 只會背考古題 |
| RLHF | 老師給回答打分數 |
| Inspector / CloudTrail | 驗屋師 / 監視器 |

### 重點整理

*   創意與隨機性看 Temperature；固定候選數看 Top K；累積機率候選池看 Top P。
*   要最新的私有知識先想 RAG；要調行為與語氣才評估微調。
*   高偏差常是擬合不足；高變異常是過度擬合。
*   驗證資料用來選模型與調參；測試資料留到最後評估泛化。
*   Canvas 建模、Data Wrangler 備料、Feature Store 管特徵、Ground Truth 做標記；Clarify 看偏見與說明、Model Monitor 看上線後的變化、Model Dashboard 看集中治理。
*   Model Cards 描述自己的模型，AI Service Cards 描述 AWS 的 AI 服務；Inspector 掃漏洞、Audit Manager 做稽核蒐證、S3 的私有存取用 VPC 端點。
*   Ground Truth、A2I、Clarify、Model Monitor、Audit Manager 都已不再開放新客戶，考試仍會考，新專案選不到。

## 隨堂測驗

**Q1. 法規摘要系統要盡量每次都挑高機率的詞，減少回答之間的差異。最該先調低哪個推論參數？**

- (A) Temperature
- (B) Stop sequences 的數量
- (C) 最大輸出長度
- (D) 上下文視窗大小

<details><summary>看答案</summary>

**答案：(A)** Temperature 調的就是取樣的隨機程度，調低會讓輸出更穩定；停止序列與長度只決定在哪裡收尾。

</details>

**Q2. 某模型的候選池大小會隨著每一步的機率分布而變動，這是哪個參數造成的？**

- (A) Top P
- (B) Top K
- (C) Temperature
- (D) 停止序列

<details><summary>看答案</summary>

**答案：(A)** Top P 是累加到機率門檻為止，所以候選數量浮動；Top K 固定的就是那個數量。

</details>

**Q3. 醫院的內部規範每季改版，想讓助理依最新版本回答，而且不希望每次改版都重新訓練。最合適的做法是什麼？**

- (A) 建立知識庫並用 RAG，在回答前檢索最新版規範
- (B) 每次改版都重新做一次完整的預訓練
- (C) 對模型做一次微調，把規範寫進參數裡
- (D) 用 RLHF 蒐集員工對舊版回答的偏好排序

<details><summary>看答案</summary>

**答案：(A)** 知識放在外部資料來源，改版後重新同步索引即可；另外三種都要動到模型本身。

</details>

**Q4. 某模型換一批驗證樣本，結果就劇烈變動，但在訓練資料上誤差很低。這最可能代表什麼？**

- (A) 模型有高變異，可能過度擬合
- (B) 模型有高偏差，屬於擬合不足
- (C) 訓練資料一定完全沒有雜訊
- (D) 測試集正在被用來更新模型權重

<details><summary>看答案</summary>

**答案：(A)** 對資料變動非常敏感是高變異的典型現象，通常伴隨過度擬合。

</details>

**Q5. 兩個團隊各自算出的「近三十天消費金額」對不上，導致線上推論與訓練時的輸入不一致。最適合導入什麼？**

- (A) Amazon SageMaker Feature Store
- (B) Amazon SageMaker Ground Truth
- (C) Amazon SageMaker Clarify
- (D) Amazon SageMaker Model Dashboard

<details><summary>看答案</summary>

**答案：(A)** 把特徵定義集中管理、讓訓練與推論共用同一份，正是 Feature Store 要解決的落差。

</details>

**Q6. 影像判讀模型已上線，需要偵測輸入資料分布的變化，而且信心不足的個案要交給醫師確認。哪個組合最符合？**

- (A) SageMaker Model Monitor 搭配 Amazon A2I
- (B) SageMaker Canvas 搭配 AWS Artifact
- (C) SageMaker Data Wrangler 搭配 Amazon Inspector
- (D) SageMaker Feature Store 搭配 AWS Config

<details><summary>看答案</summary>

**答案：(A)** 監控上線後的資料與模型狀況靠 Model Monitor；把預測送去人工審核靠 A2I。

</details>

**Q7. 稽核人員要求公司自動蒐集 AWS 環境的控制證據，並依合規框架整理成評估報告，而不是只下載 AWS 自己的合規文件。該選哪個服務？**

- (A) AWS Audit Manager
- (B) AWS Artifact
- (C) Amazon Inspector
- (D) AWS CloudTrail

<details><summary>看答案</summary>

**答案：(A)** Artifact 給的是 AWS 自己的報告，CloudTrail 給的是活動紀錄，Inspector 掃的是漏洞；做稽核蒐證與框架評估的是 Audit Manager。

</details>

**Q8. 公開的生成式 AI 應用已經選定模型，現在要攔下禁止主題、敏感資訊與不當內容。最直接的能力是什麼？**

- (A) Amazon Bedrock Guardrails
- (B) Amazon Bedrock 的模型評估功能
- (C) SageMaker Clarify 的偏見檢測
- (D) Amazon Bedrock 的模型呼叫日誌

<details><summary>看答案</summary>

**答案：(A)** 模型評估是拿來選模型的，呼叫日誌是事後留紀錄的；即時攔截內容要靠 Guardrails。

</details>
