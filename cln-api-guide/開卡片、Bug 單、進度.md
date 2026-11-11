# 開卡片、Bug 單、進度

## 日常作業：開卡片、改 Bug 單、更新進度

寫程式以外的例行流程。拿到新交易先開卡片，改 Bug 照 Bug 單流程走，完成後記得回填 Excel 進度。

### 新交易開卡片

| 項目 | 規則 |
| --- | --- |
| Original Estimate | SA 預估時數 × 1.5 + CR 時數 |
| CR 時數 | 易以下 2、中 4、難 8 |
| 前端／後端／報表 | 開三張卡片：新交易、測試、CR |
| 批次 | 開兩張卡片：新交易、CR |

### 改 Bug 單

Bug 單位置：[TFS-UT 工作項目](https://dialm01.cathdevelop.intra.uwccb/tfs/DefaultCollection/LONLXLIP01-LIP-UT/_workitems/mentioned/)。依 Severity 決定優先順序，下面是最晚期限，越快解越好，但不要影響排定的交易完成時間。

| Severity | 收到後完成期限 |
| --- | --- |
| 1 - Critical | 2～3 個工作天 |
| 2 - High | 5 個工作天 |
| 3 - Medium | 7～10 個工作天 |

### 找到自己的 Bug 單

Azure DevOps Boards → 工作項目，Assigned To 篩選「@我」，點開要處理的單。

### 狀態改 Developing

開始修改前，把 State 從 New 改成 Developing 並儲存，再動手改程式。

### 手動執行 CI

Pipelines → 管線，找到這次改的 Pipeline（如 lip-web-cln）→ 右上角「執行管線」→ 確認服務正確、Branch 是這次用的分支（如 dev）→ 執行。

### 確認 CI/CD 成功

CI Build 沒有失敗後，到 Pipelines → 版本（Releases）找最新一筆 Release，確認 CD／UT 部署階段都成功。失敗就先查原因排除。

### 到 UT 測試

照 Bug 單的測試案例／Repro Steps 重做一次，確認問題修好、相關功能沒被影響。還有問題就重複「改程式 → CI → 確認 CD → UT 測試」。

### 更新 Bug 單

State 改 Testing、Resolved Reason 設 Fixed（Bug fixed），重新指派給對應的測試人員並儲存。

### 更新 Excel 開發進度

檔案：`【有擔貸款專案】開發功能清單暨時程_20250606.xlsx`。有負責的新交易或異動都要同步更新。

**新交易**

找到自己負責的功能／交易，更新開發狀態、開發人員、預計開始／完成時間、實際開始／完成時間。

**異動**

切到「規格文件更新紀錄」頁籤，用功能項目、功能代號、文件名稱或 Bug 單號找到自己的那筆，更新調整狀態、調整人員、調整完成日。
