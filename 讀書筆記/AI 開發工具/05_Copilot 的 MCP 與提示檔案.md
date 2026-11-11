# 05. Copilot 的 MCP 與提示檔案

> 來源：[筆記平台 · AI 開發工具](https://hhtim.github.io/notes-platform/ai-tools/#/lesson/copilot-mcp-prompts)　第 5 課 / 共 8 課 · 約 23 分鐘

**用 MCP 接上外部工具，再用指示檔、提示檔、工具組與自訂代理人把成功的對話變成可以重跑的流程。**

### 讀完這課你會

*   說明 MCP 負責什麼、不負責什麼
*   分清指示檔、提示檔、自訂代理人與工具組
*   把工作區外的儲存庫、網頁指給它看
*   把外部內容當成不可信的資料，避開提示注入

*【先講 MCP】*

## 替 AI 工具準備一個通用插座

MCP（Model Context Protocol，模型上下文協定）是一套讓應用程式用標準方式連接外部資料與工具的協定。可以把它比喻成 AI 世界的 USB-C，主機不必為每個模型、每項服務都另外做一套接頭。

它是 Anthropic 在 2024 年 11 月 25 日正式公開的開放標準，訊息格式用 JSON-RPC 2.0，官方提供多種語言的 SDK。

它解決的是「多對多整合」的重複工：以前 M 種模型要接 N 種工具，就得做 M×N 套接頭。但「用同一種插頭」不等於「插上去就安全」。伺服器仍可能碰到本機檔案、公司系統或外部服務，認證、授權、輸入驗證與稽核都得另外處理。

MCP 的角色分工與三種能力（工具、資源、提示範本）見〈Claude Code 的擴充：MCP 與 Hooks〉。

*【三個角色】*

## 主機、用戶端、伺服器各司其職

| 角色 | 白話比喻 | 責任 |
| --- | --- | --- |
| 主機（Host） | 你在用的那張工作台 | 承載聊天或代理人介面，管互動與權限 |
| 用戶端（Client） | 專線接頭 | 代表主機跟某一台伺服器建立協定連線 |
| 伺服器（Server） | 工具箱或資料櫃 | 對外公開可呼叫的能力或可取得的內容 |

本機的伺服器可能讀檔案或操作本機程式；遠端的可能連到工單系統、設計檔、雲端或公司資料。不管跑在哪裡，先把資料流畫出來：送出了什麼、交給誰、保存多久、回傳的內容會不會被其他工具再用一次。

*【傳輸與能力】*

## 工具只是 MCP 的其中一塊

現行規格的兩種標準傳輸是標準輸入輸出（stdio）與 Streamable HTTP；原本單獨列的 HTTP 加 SSE 那一種已經由 Streamable HTTP 取代[出處](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports)。標準輸入輸出用在主機自己啟動的本機程序；走網路的那種適合遠端服務，但需要更完整的身分驗證、加密與授權設計。

> 📝 查證更正：原筆記寫「傳輸層：Stdio 適用於本地程序；HTTP (SSE) Server-Sent Events 適用於遠端通訊」，查證後更正

| 能力 | 用途 | 主要風險 |
| --- | --- | --- |
| 工具（Tools） | 讓模型要求執行查詢或動作 | 越權修改、危險參數、外部副作用 |
| 資源（Resources） | 提供可讀取的資料或內容 | 敏感資料外洩、過期內容被誤用 |
| 提示範本（Prompts） | 提供可重複使用的互動範本 | 範本夾帶不當指示或已不符現況 |
| 取樣（Sampling） | 讓伺服器反過來請主機用模型生成內容 | 互相呼叫、成本、資料邊界不清 |

這四項現行 VS Code 都支援了。其中取樣是讓伺服器用你設定的模型發出請求，第一次呼叫時會跳出授權提示[出處](https://code.visualstudio.com/api/extension-guides/ai/mcp)；要控管哪些模型開放給伺服器取樣，用的是 `chat.mcp.serverSampling` 這個設定。[出處](https://code.visualstudio.com/docs/agents/reference/ai-settings)

> 📝 查證更正：原筆記寫「目前 GitHub Copilot 的 Agent Mode 只能用「工具」這項！」，並把 Resources、Prompts、Sampling 列為當時尚未支援，查證後更正

取樣則要再多看一步。它跟 Roots 已經準備退場：MCP 規格在 2026-07-28 版把這兩項標為棄用（deprecated），最快會在 2027-07-28 之後的版本被移除，並給了替代做法——取樣改成直接串模型供應商的介面，Roots 改用工具參數、資源網址或伺服器設定來傳路徑。[出處](https://modelcontextprotocol.io/specification/2026-07-28/deprecated)所以取樣現在是編輯器還支援、規格已經不建議：舊的實作還會動，但新的流程不要再建立在它上面。

用戶端這邊還有 Elicitation（伺服器中途向使用者要一項補充資訊）。VS Code 也支援這項。[出處](https://code.visualstudio.com/api/extension-guides/ai/mcp)不過通則要記得：「協定有這項能力」推論不出「手上這套產品一定支援」，兩者是不同層次，實際還是看該產品自己的文件。

*【設定 MCP】*

## 接之前先看清楚它要什麼權限

新增伺服器前，先檢查來源、維護者、啟動指令、相依套件、會連到哪些網路位址、環境變數與可存取的路徑。專案設定如果會進版本控制，就不能直接放金鑰。

```
{
  "servers": {
    "example": {
      "command": "example-server",
      "args": ["--read-only"],
      "env": { "EXAMPLE_TOKEN": "${input:exampleToken}" }
    }
  }
}
```

專案設定檔放在 `.vscode/mcp.json`，命令列也有 `--add-mcp` 參數可以加；現在正式版的 VS Code 就支援，不必再裝預覽版[出處](https://code.visualstudio.com/docs/agent-customization/mcp-servers)。管理指令有 `MCP: Add Server`、`MCP: List Servers`、`MCP: Reset Cached Tools`、`MCP: Open User Configuration`、`MCP: Open Workspace Folder MCP Configuration`、`MCP: Browse Resources`、`MCP: Reset Trust`、`MCP: Show Installed Servers`。[出處](https://code.visualstudio.com/docs/agents/reference/mcp-configuration)

> 📝 查證更正：原筆記寫「安裝擴充套件：使用 code-insiders 安裝 GitHub Copilot Pre-release 版本」「指令：code-insiders --add-mcp」，查證後更正

`.vscode/mcp.json` 有個前提要先知道。VS Code 把 AI 代理跑在一個獨立的程序裡，叫 Agent Host。[出處](https://code.visualstudio.com/docs/agents/concepts/agent-host)

*   跑在 Agent Host 上的工作階段不會自己去讀 `.vscode/mcp.json`，是 VS Code 把設定轉過去的。
*   需要你當場輸入值的伺服器（像上面範例那樣用 `${input:…}` 的）不在轉送之列。
*   要讓設定在 Agent Host 與其他 Copilot 工具之間都通用，改用工作區的 `.mcp.json` 或使用者的 `~/.copilot/mcp-config.json`，這兩個 Agent Host 會直接讀。[出處](https://code.visualstudio.com/docs/agent-customization/mcp-servers)

*   優先用唯讀帳號、測試環境與範圍受限的權杖。
*   寫入、刪除、付款、部署、對外發訊這類動作，保留人工確認。
*   固定或審查套件版本，不要每次啟動都抓一份沒檢查過的新程式。
*   留下工具呼叫、參數、結果與核准人的稽核紀錄。
*   定期把不用的伺服器、權杖與權限清掉。

現成的伺服器很多（瀏覽器操作、雲端服務查詢、設計稿轉程式碼、聯網搜尋、抓網頁、查時間都有人做），有些還搭配自己的付費方案與額度。這類清單與價格變動很快，挑伺服器該從任務與風險出發，不要只因為「熱門推薦」就裝上去。

*【除錯】*

## 連線、能力、權限、業務邏輯分開查

官方有一支檢查工具（MCP Inspector），可以觀察伺服器啟不啟得起來、宣告了哪些能力、呼叫的輸入輸出長什麼樣。啟動方式是用 npx 執行官方套件，再開瀏覽器連本機的埠號；版本與埠號會變，用之前先確認套件來源。出問題時照這四層往下查：

*   連線層：程序有沒有啟動、傳輸方式與環境變數對不對。
*   協定層：初始化成不成功、宣告的能力與參數結構對不對得上。
*   權限層：這個帳號到底准不准存取目標資源。
*   業務層：工具跑成功了，結果是不是真的符合需求。

*【四種客製化元件】*

## 規則、任務、角色、工具不要混在一起

| 元件 | 像什麼 | 適合放什麼 | 檔案形式 |
| --- | --- | --- | --- |
| 指示檔 | 常設規章 | 團隊風格、架構界線、安全與測試政策 | `.github/copilot-instructions.md`、`.github/instructions/*.instructions.md` |
| 提示檔 | 可以重跑的工作單 | 建介面、審弱點、產遷移計畫等任務流程 | `.github/prompts/*.prompt.md` |
| 自訂代理人 | 角色與工作環境 | 規劃者、文件編輯、唯讀審查等模式與工具限制 | 已改名為 `*.agent.md`，工作區放在 `.github/agents`；自訂代理人的前身就是聊天模式，舊的 `.chatmode.md` 要改名搬過去[出處](https://code.visualstudio.com/docs/agent-customization/custom-agents) |
| 工具 | 可以操作的器材 | 讀檔、搜尋、查資料庫、呼叫外部服務、執行指令 | 內建或由 MCP 伺服器提供 |

> 📝 查證更正：原筆記寫這類檔案是 .chatmode.md（聊天模式），查證後更正

提示檔可以要求遵循指示檔，也可以建議用哪些工具，但它本身不是工具。就像工作單可以寫「用扳手鎖緊」，工作單不會變成扳手。

*【工具組】*

## 工具一多，就替常用的那幾把綁一個名字

接上兩三台 MCP 伺服器之後，可以選的工具很快就是幾十個，每次要手動勾選很煩。**工具組**（Tool Sets）就是為這件事存在的：把一組相關的代理工具包成一個名字，之後當成一個整體、用這個名字整組叫出來。[出處](https://code.visualstudio.com/docs/agent-customization/tool-sets)

建立方式是在命令面板（VS Code 上方那個打指令的搜尋框）跑 `Chat: Configure Tool Sets`，選 `Create new tool sets file`，在開出來的 `.jsonc` 檔（可以寫註解的 JSON）裡定義：

```
{
  "reader": {
    "tools": ["search/changes", "search/codebase", "read/problems", "search/usages"],
    "description": "Tools for reading and gathering context",
    "icon": "book"
  }
}
```

之後在對話裡打 `#reader`，這一整組就一起帶進去。三個欄位：

*   `tools`：工具名稱的陣列，可以放內建工具、MCP 工具或擴充功能提供的工具。
*   `description`：在工具選單裡顯示的說明。
*   `icon`：圖示。

VS Code 自己也內建了幾組，每組把相關的工具包在一起：`#read`（讀工作區的檔案與執行輸出）、`#search`（搜工作區）、`#edit`（改工作區的檔案與 Notebook，也就是可以邊寫程式邊看執行結果的那種檔案）、`#execute`（執行指令、任務與 Notebook 的儲存格）、`#web`（取用網頁內容）、`#browser`（用瀏覽器工具瀏覽、檢查與操作頁面）、`#agent`（把工作分派給子代理人）。[出處](https://code.visualstudio.com/docs/agents/reference/tools-reference)

*【自訂代理人】*

## 同一套工具，換個角色用

自訂代理人把指示、工具跟一個選填的模型組成一份可重複使用的設定，對應某一個角色，例如規劃或程式碼審查。[出處](https://code.visualstudio.com/docs/agent-customization/custom-agents)

例如一個「Plan」角色只出實作計畫、不動程式碼，就不會在你還在想的時候改到東西。

| 要設的東西 | 寫在哪 |
| --- | --- |
| 檔案本身 | 一個 `.agent.md` 的 Markdown 檔 |
| 工作區共用 | `.github/agents` 資料夾（Claude 格式則放 `.claude/agents`） |
| 只給自己、跨專案用 | `~/.copilot/agents` 或 `~/.claude/agents` |
| 檔頭設定（YAML 前置區，檔案開頭用三個減號框起來的設定段） | `description`（說明）、`name`（名稱，不寫就用檔名）、`tools`（准用哪些工具或工具組）、`model`（指定用哪個模型）等 |

建立用命令面板的 `Chat: New Custom Agent`，要用的時候在對話視窗的代理人下拉選單裡切換。

這個功能的名稱換過：自訂代理人以前叫自訂聊天模式，功能一樣，只是改了名字，更貼近「為特定工作調整 AI 行為」的用途。舊的 `.chatmode.md` 要改名搬過去。[出處](https://code.visualstudio.com/docs/agent-customization/custom-agents)

*【提示檔】*

## 把成功的對話變成可以維護的資產

提示檔適合那種會重複出現、輸入可以替換、輸出可以驗收的任務。放在專案的 `.github/prompts/` 就能跟同事共用、進版本控制，在對話裡打 `/` 加名稱就叫得出來；放在個人設定裡則是自己跨專案用。內容支援 `${selection}`（目前選取內容）、`${input:變數名}`（執行時問你要填什麼）這類變數。要指某個檔案給它看，有兩種寫法：Markdown 連結或 `#file:`，工作區裡的檔案用相對於這份提示檔的路徑；把流程拆成好幾份小的、彼此用連結串起來也是同一招。[出處](https://code.visualstudio.com/docs/agent-customization/prompt-files)

```
---
description: 審查指定介面的授權風險
---

目標：
檢查 ${input:routeName} 的身分驗證與授權流程。

參考：
- #file:../../src/middleware/auth.ts
- [專案安全規範](../instructions/security.instructions.md)

限制：
- 只分析，不改檔案、不執行外部指令。
- 不顯示權杖、Cookie 或個資內容。

輸出：
1. 依嚴重度排序的發現
2. 每項發現對應的程式碼依據
3. 建議修正與待確認的假設
```

不要把整段聊天原封不動存起來；刪掉當時才有的偶然資訊，留下用途、必要輸入、允許範圍、禁止事項、輸出格式與完成條件。流程長的話拆成幾份小提示、明確傳遞中間產物，比做一份越長越大的提示好維護。

提示檔沒有 `chat.promptFiles` 這個開關要打開。管提示檔的設定名稱是 `chat.promptFilesLocations`，列出去哪些資料夾找提示檔；這個設定現在已標為棄用（Deprecated），它與本機代理未來都會移除[出處](https://code.visualstudio.com/updates/v1_100)[出處](https://code.visualstudio.com/docs/agents/reference/ai-settings)。提示檔在 Agent Host 工作階段也已棄用、不會被載入，只有本機代理還讀得到；下一步是用提示檔轉換功能，把既有的提示檔轉成 agent skills（技能檔，一份 `SKILL.md`，檔頭寫名稱與用途、內文寫指示）。[出處](https://code.visualstudio.com/docs/agent-customization/prompt-files)[出處](https://code.visualstudio.com/docs/agent-customization/agent-skills)所以這套做法的觀念可以學，但長期別把流程全押在這個檔案格式上。另外，把對話存成提示檔、或匯出成一份檔案給別人匯入這類功能，分享前要先把祕密、個資、內部路徑與客戶資料清掉——可重用不等於可公開。

> 📝 查證更正：原筆記寫「啟用設定："chat.promptFiles": true」，查證後更正

*【對話管理】*

## 換一個乾淨的開始，或把這段留下來

對話越長，舊的資訊越容易干擾新的問題。要處理的需求有三種：清空上下文、把這次的對話存成之後可以重跑的檔案、把整串對話留底或給別人。對應的做法如下。

| 你想做的事 | 現行做法 |
| --- | --- |
| 不要讓舊對話影響新問題 | `/clear`：開一個新對話，並把目前這個封存或標記為完成 |
| 對話太長、超出模型能看的範圍 | `/compact`（同類的還有 `/fork`）：壓縮上下文，或是連同歷史把對話分岔成另一串；要繼續同一串的是 `/compact` |
| 把這次的做法變成下次可以重跑的檔案 | `/create-prompt`（同類的還有 `/create-agent`、`/create-instructions`、`/create-skill`、`/create-hook`）：在本機代理的工作階段裡產生一份自訂設定 |
| 整串留底或給別人 | 命令面板的 `Chat: Export Chat...`，存成一個 JSON 檔 |

匯出對話會產生一個 JSON 檔，這次工作階段**全部**的提示與回覆都在裡面。[出處](https://code.visualstudio.com/docs/agents/run/sessions/manage-sessions)另外也可以按右鍵複製成 Markdown，有三種：`Copy`（單則）、`Copy All`（整串）、`Copy Final Response`（只要最後那段結論）。既然是整串照抄，分享前一樣要先清祕密與個資。

要把對話變成可重複執行的檔案，用的是 `/create-prompt`。能用哪些指令，要看聊天介面、執行環境、角色與開了哪些功能，實際以你手上那個版本打 `/` 跳出來的清單為準。[出處](https://code.visualstudio.com/docs/agents/reference/ai-features-cheat-sheet)提示檔這個格式在部分工作階段已經標為棄用，所以別把長期流程全押在它身上。

*【再多三種材料】*

## 專案以外的東西，怎麼指給它看

選取的程式碼、問題清單、版本控制的差異、整個工作區怎麼指給它看，見〈GitHub Copilot 基礎〉。下面三種材料來自**工作區以外**。

| 想給的材料 | 現行寫法 | 用途 |
| --- | --- | --- |
| GitHub 上某個儲存庫的原始碼 | `#githubRepo`，後面接 `owner/repo`（GitHub 上「帳號／儲存庫名稱」的寫法） | 對 GitHub 儲存庫做**語意搜尋**（照意思找相關的段落，不是只比對字面），儲存庫寫成 `owner/repo` |
| 同上，但要照關鍵字精確找 | `#githubTextSearch` | 在 GitHub 儲存庫或組織裡找文字或程式碼樣式 |
| 某一頁網頁的內容 | `#web/fetch` | 抓一頁網頁 |

抓網頁的工具寫成 `#web/fetch`，歸在 `#web` 這組底下，跟〈GitHub Copilot 基礎〉的 `#search/codebase` 是同一種「工具組／工具」的寫法；`#fetch` 是不帶前綴的舊短名，現在還能不能打，以手上那個版本輸入 `#` 跳出來的清單為準。[出處](https://code.visualstudio.com/docs/agents/reference/tools-reference)

早期用 `#openSimpleBrowser`（在編輯器裡開一個簡易瀏覽器，讓 AI 看得到網頁結構）做這件事，現在改由**內建瀏覽器那一組工具**做，讓代理在做網頁時看得到畫面、也能操作頁面，工具包括 `openBrowserPage`、`navigatePage`、`readPage`、`screenshotPage`、`clickElement` 等，用 `workbench.browser.enableChatTools` 這個設定開關，預設是開的。[出處](https://code.visualstudio.com/docs/agents/run/browser-tools)

這三種材料都來自你的工作區以外，所以下一段那條規矩對它們特別重要。

*【上下文與信任邊界】*

## 資料要剛好，而且要分得出哪些不可信

選取內容、問題清單、版本控制差異、專案搜尋與外部網頁各自回答不同的問題。先問「完成這件事最低限度需要哪些證據」，再附上對應的資料。

外部內容尤其要當成不可信的輸入。網頁、工單、文件或工具回傳的結果，可能夾帶提示注入（prompt injection，把惡意指令藏在資料裡，騙模型當成命令執行），例如叫它忽略原本的規則、去讀祕密、或執行某個指令。這些文字只能當資料，不能自動升格成命令。

> 信任層級要固定：使用者與專案政策決定目標；外部資料只提供事實，不能自己改寫權限與任務。

*【串成可重複的流程】*

## 用契約把提示、工具與驗收接起來

> 可靠流程 ＝ 固定規範 ＋ 任務範本 ＋ 最小工具權限 ＋ 看得到的證據 ＋ 人工驗收

1.  用指示檔宣告長期規則。
2.  用提示檔定義單次任務的輸入、步驟與輸出。
3.  只給相關的上下文，並標明哪些是不可信的外部資料。
4.  只開必要的工具，對有副作用的呼叫設核准點。
5.  用差異、測試、日誌或查詢結果驗收，不用模型的自述驗收。
6.  規格或工具改了，同步更新範本並重新測一次。

### 重點整理

*   MCP 讓 AI 與外部工具、資料的連接方式標準化，但不會自動解決安全問題。
*   協定有哪些能力，跟某套產品實際支援哪些，是兩件要分開確認的事。
*   指示檔管長期規則，提示檔管可重複的任務，自訂代理人管角色與工具邊界，工具組只是把常用工具綁一個名字。
*   工作區以外的材料各有寫法：別人的儲存庫用 `#githubRepo`，某一頁網頁用 `#web/fetch`，要看實際畫面則用內建瀏覽器那組工具。
*   想換個乾淨的開始用 `/clear`，對話太長用 `/compact`；匯出會把整串提示與回覆寫成一個 JSON 檔，分享前先清乾淨。
*   外部內容可能夾帶提示注入，一律當成資料而不是命令。
*   有副作用的工具呼叫都照最小權限給、留紀錄、設人工核准點。

## 隨堂測驗

**Q1. 把 MCP 比喻成「AI 世界的 USB-C」，主要是在講什麼？**

- (A) 它提供比較標準化的方式，讓應用程式連接不同的資料與工具
- (B) 所有 MCP 伺服器都由同一家公司營運
- (C) 接上 MCP 之後就不必做認證與授權
- (D) MCP 只負責替電腦供電

<details><summary>看答案</summary>

**答案：(A)** 這個比喻強調的是介面標準化，不是說所有服務都一樣，也不是說接上就安全。

</details>

**Q2. 主機（Host）在 MCP 架構裡的主要角色是什麼？**

- (A) 承載 AI 互動，並協調用戶端連線、權限與工具使用
- (B) 永久保存公司所有資料
- (C) 取代每一台 MCP 伺服器
- (D) 只負責產生 JSON

<details><summary>看答案</summary>

**答案：(A)** 主機是使用者實際操作的那支應用程式，負責協調模型與外部能力。

</details>

**Q3. 下列哪一項最能區分 MCP 的工具與資源？**

- (A) 工具偏向執行查詢或動作，資源偏向提供可讀取的內容
- (B) 工具只能在雲端，資源只能在本機
- (C) 資源可以任意部署，工具永遠唯讀
- (D) 兩者完全相同，只是名稱不同

<details><summary>看答案</summary>

**答案：(A)** 工具代表可以呼叫的操作，資源代表可以取得的內容；實際支援還是看各產品的實作。

</details>

**Q4. 要接一台新的 MCP 伺服器，最重要的檢查組合是什麼？**

- (A) 來源、啟動指令、相依套件、會連到哪裡、權限與資料範圍
- (B) 圖示好不好看、名稱夠不夠短
- (C) 有沒有要求最高的系統權限
- (D) 能不能把稽核紀錄全部關掉

<details><summary>看答案</summary>

**答案：(A)** 伺服器可能碰到敏感資料或執行操作，得先弄懂它的來源與權限風險。

</details>

**Q5. 哪一種內容最適合做成提示檔？**

- (A) 會重複執行、輸入可替換、限制固定、輸出可驗收的審查流程
- (B) 正式環境的永久密碼
- (C) 只有今天有效、也沒有驗收方式的臨時閒聊
- (D) 把所有團隊規範跟所有任務混成一大段文字

<details><summary>看答案</summary>

**答案：(A)** 提示檔適合封裝可重複、可帶參數而且驗得出結果的任務。

</details>

**Q6. 指示檔跟提示檔最核心的差別是什麼？**

- (A) 指示檔是持續套用的規範，提示檔是可以重複執行的任務範本
- (B) 指示檔只能放密碼，提示檔只能放圖片
- (C) 指示檔一定會執行指令，提示檔永遠不能引用工具
- (D) 兩者都只是程式碼格式化工具

<details><summary>看答案</summary>

**答案：(A)** 前者定義長期的行為邊界，後者封裝具體的工作流程。

</details>

**Q7. 把外部網頁的內容交給代理人時，為什麼要防提示注入？**

- (A) 外部文字可能夾帶「忽略原本規則」「去讀祕密」之類的惡意指令
- (B) 所有網頁模型都看不懂
- (C) 提示注入只會改變字型
- (D) 只要用 HTTPS 就不會出現提示注入

<details><summary>看答案</summary>

**答案：(A)** 傳輸加密保證不了內容可信；外部內容只能當資料，不能當高權限的命令。

</details>

**Q8. 要驗收一個由提示檔搭配 MCP 工具跑完的流程，該看什麼？**

- (A) 工具呼叫紀錄、實際差異、測試或查詢證據，以及還沒解掉的風險
- (B) 只看它有沒有說「已完成」
- (C) 只看回應夠不夠長
- (D) 只要工具沒報錯就直接上正式環境

<details><summary>看答案</summary>

**答案：(A)** 可靠的驗收靠的是看得到的證據，不是模型對自己結果的宣告。

</details>

**Q9. 「把一組相關的工具綁成一個名字，之後在對話裡用一個名字整組叫出來」講的是哪一個？**

- (A) 工具組（Tool Sets）
- (B) 自訂代理人
- (C) 提示檔
- (D) 指示檔

<details><summary>看答案</summary>

**答案：(A)** 四者分工不同：工具組只管把工具打包成一個名字，自訂代理人管角色與可用工具的邊界，提示檔是可重跑的任務範本，指示檔是長期規範。

</details>

**Q10. 要 AI 參考 GitHub 上某個儲存庫的寫法，現行的引用方式是哪一個？**

- (A) #githubRepo，後面接 owner/repo
- (B) #web/fetch，後面接網址
- (C) #search/codebase
- (D) #browser

<details><summary>看答案</summary>

**答案：(A)** #githubRepo 是對某個儲存庫做語意搜尋；#web/fetch 抓的是某一頁網頁，#search/codebase 搜的是你目前這個工作區，#browser 是操作內建瀏覽器。

</details>
