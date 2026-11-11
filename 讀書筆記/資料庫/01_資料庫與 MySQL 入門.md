# 01. 資料庫與 MySQL 入門

> 來源：[筆記平台 · 資料庫](https://hhtim.github.io/notes-platform/database/#/lesson/db-mysql-intro)　第 1 課 / 共 9 課 · 約 10 分鐘

**從電腦怎麼保存資料開始，認識資料庫、DBMS、關聯式資料表與 MySQL 基礎。**

### 讀完這課你會

*   分辨記憶體、硬碟、資料庫與資料庫管理系統的角色
*   看懂關聯式資料庫中的資料庫、資料表、欄位與資料列
*   了解 MySQL、SQL、資料型態與基本操作之間的關係

*【先從電腦怎麼放資料開始】*

## 記憶體像工作桌，硬碟像檔案櫃

程式執行時，資料會在不同儲存位置之間移動。中央處理器（Central Processing Unit，CPU）負責運算；主記憶體（Random Access Memory，RAM）暫放正在執行的程式與資料；硬碟或固態硬碟則負責長期保存。

| 位置 | 白話比喻 | 特性 |
| --- | --- | --- |
| CPU 暫存器與快取 | 手上正在看的便條紙 | 速度最快、容量很小 |
| 主記憶體 | 工作桌 | 方便快速取用，但斷電後內容會消失 |
| 硬碟或固態硬碟 | 檔案櫃 | 速度較慢，但可長期保存大量資料 |

例如開啟通訊軟體時，程式會從硬碟載入主記憶體，再由 CPU 執行。尚未存檔的圖片先放在記憶體；按下儲存後，才會寫入硬碟長期保存。

> 由快到慢：CPU 暫存器與快取 → 主記憶體 → 硬碟等長期儲存裝置。

*【有資料，還要有人管理】*

## 資料庫不等於資料庫管理系統

資料庫（Database，DB）是有組織的資料集合；資料庫管理系統（Database Management System，DBMS）則是負責建立、讀取、修改、保護與備份資料庫的軟體。

可以把資料庫想成倉庫裡的貨物與貨架，把 DBMS 想成倉儲管理中心。應用程式通常不會自行翻動硬碟上的資料，而是向 DBMS 提出要求，再由 DBMS 處理權限、並行操作與資料一致性。

*   **DB**：有組織地保存資料的集合。
*   **DBMS**：管理資料庫的軟體，例如 MySQL、PostgreSQL。
*   **SQL**：操作關聯式資料庫的語言。
*   **資料庫伺服器**：執行 DBMS、接受用戶端連線的主機或服務環境。

「一台電腦裝上並開啟 DBMS 就是資料庫伺服器」是最常見的情況，但資料庫伺服器不一定獨占一台實體電腦，也可能是虛擬機、容器或雲端代管服務。

*【把資料排成有規則的表格】*

## 關聯式資料庫的核心物件

關聯式資料庫（Relational Database）以資料表表達資料與關係。MySQL、PostgreSQL、Oracle Database 與 Microsoft SQL Server 都屬於常見的關聯式資料庫管理系統（RDBMS）。

| 物件 | 用途 | 例子 |
| --- | --- | --- |
| 資料庫／綱要 | 組織一組相關物件 | 商店系統 |
| 資料表（Table） | 保存同類型的資料 | customers |
| 欄位（Column） | 定義每項資料的名稱與型態 | customer_name |
| 資料列（Row） | 代表一筆紀錄 | 某一位顧客 |
| 值（Value） | 某筆紀錄在某欄位的內容 | 「阿寶」 |
| 檢視表（View） | 以查詢定義的虛擬資料表 | active_customers |
| 索引（Index） | 以額外空間換取特定查詢速度 | email 索引 |

在 MySQL 中，`SCHEMA` 與 `DATABASE` 是同義詞；其他資料庫產品（例如 PostgreSQL、SQL Server）則把綱要（Schema）設計成資料庫之下的一層命名空間（namespace，同名物件靠它分隔、不打架）。

同義到什麼程度？MySQL 連 SCHEMA 關鍵字都有，CREATE SCHEMA 就是 CREATE DATABASE 的同義詞[出處](https://dev.mysql.com/doc/refman/8.4/en/create-database.html)。

> 💡 一張資料表像試算表，但不只是格子：欄位有型態、資料可受約束，而且資料表之間能建立關聯。

*【資料型態是資料的使用說明】*

## 為欄位選擇合適的資料型態

電腦底層以位元（bit）表示 0 或 1，8 個位元合起來是 1 個位元組（byte）。資料型態則告訴 DBMS：這串位元應被當成整數、文字、日期，還是其他內容。

| 類型 | 常見 MySQL 型態 | 適用資料 |
| --- | --- | --- |
| 整數 | INT、BIGINT | 數量、流水號 |
| 精確小數 | DECIMAL | 金額、需精確計算的比例 |
| 浮點數 | FLOAT、DOUBLE | 允許近似值的科學量測 |
| 文字 | CHAR、VARCHAR、TEXT | 代碼、姓名、文章內容 |
| 日期時間 | DATE、DATETIME、TIMESTAMP | 生日、訂單時間 |
| 真假值 | BOOLEAN | 啟用狀態；在 MySQL 中是 TINYINT(1) 的別名 |

`CHAR(n)` 適合長度固定的內容，例如固定格式代碼；`VARCHAR(n)` 適合長度不固定的文字。實際占用空間由欄位的字元集決定：MySQL 建議的 `utf8mb4` 每個字元占 1〜4 個位元組（英文字母 1 個、常用中文字 3 個），不能用「英文 1 個位元組、非英文 2 個位元組」概括[出處](https://dev.mysql.com/doc/refman/8.4/en/charset-unicode.html)。

> 📝 查證更正：原筆記寫「每個英文字符的儲存空間只需要 1 Byte，非英文字符則需要 2 Bytes」，那是 SQL Server 舊字元集的規則；查證後更正：MySQL 的空間由欄位字元集決定，utf8mb4 每字元 1〜4 個位元組

那套「n 開頭型態存 Unicode」的分類是 SQL Server 的規則。MySQL 雖然也接受 `NCHAR`、`NVARCHAR` 寫法，但會被當成已棄用（deprecated）的 utf8mb3 字元集並發出警告；官方建議直接用 `CHAR`／`VARCHAR` 搭配 `utf8mb4`，即可完整保存中文與各國文字[出處](https://dev.mysql.com/doc/refman/8.4/en/charset-national.html)。

> 📝 查證更正：原筆記用 SQL Server 的 char、varchar、nchar、nvarchar、text、ntext 六種文字型態說明，並註記 nchar、nvarchar「MySQL沒有」；查證後更正：MySQL 其實接受 NCHAR、NVARCHAR 寫法，但會被當成已棄用的 utf8mb3 字元集並發出警告，官方建議直接用 CHAR/VARCHAR 搭配 utf8mb4

> 金額用 DECIMAL；不要用 FLOAT 或 DOUBLE 承擔必須精確到分的帳務計算。

*【MySQL 是系統，SQL 是溝通語言】*

## 認識 MySQL 與 SQL

MySQL 是一套 RDBMS（現由 Oracle 開發維護）；結構化查詢語言（Structured Query Language，SQL）才是用來操作關聯式資料庫的語言，自 1986 年起有 ANSI/ISO 標準[出處](https://dev.mysql.com/doc/refman/8.4/en/what-is-mysql.html)。SQL 有共同標準，但不同資料庫產品仍有語法與功能差異。

> 📝 查證更正：原筆記在「MySQL 簡介」下寫「Structured Query Language 1970年由IBM開發」，把 MySQL 與 SQL 混為一談；查證後更正：MySQL 是 Oracle 開發維護的 RDBMS，SQL 才是語言，且自 1986 年起有 ANSI/ISO 標準

| 子語言 | 工作 | 常見指令 |
| --- | --- | --- |
| DDL | 定義結構 | CREATE、ALTER、DROP |
| DML | 新增、修改、刪除資料 | INSERT、UPDATE、DELETE |
| DQL | 查詢資料 | SELECT |
| DCL | 控制權限 | GRANT、REVOKE |
| TCL | 控制交易 | COMMIT、ROLLBACK、SAVEPOINT |

不同教材可能把 `SELECT` 歸入廣義 DML，而不是獨立列為 DQL；分類方式不同，不影響 SQL 的實際用途。〈SQL 三種子語言：DDL、DML、DQL〉會把 DDL、DML、DQL 逐一展開。

*【先會觀察，再開始改資料】*

## 第一組 MySQL 指令

```
SHOW DATABASES;

USE shop;

SHOW TABLES;

SELECT customer_id, customer_name
FROM customers;
```

`SHOW DATABASES` 列出目前帳號可看見的資料庫；`USE` 選擇預設資料庫；`SHOW TABLES` 列出資料表；`SELECT` 則取得指定欄位。

MySQL 安裝後會看到幾個系統資料庫：`information_schema`（記錄有哪些資料庫、資料表等描述性資訊）、`mysql`（帳號與權限）、`performance_schema` 與 `sys`（效能觀測）。它們是 MySQL 自己要用的，不要當成一般業務資料庫隨意修改。

> 💡 看到 `SELECT *` 時，星號代表所有欄位。練習時很方便，但正式程式通常應明列需要的欄位，以降低不必要的資料傳輸與結構變動風險。

### 重點整理

*   資料庫保存有組織的資料，DBMS 負責管理它，SQL 則是操作關聯式資料庫的語言。
*   關聯式資料表由欄位與資料列組成，索引用額外空間協助特定查詢。
*   MySQL 是 RDBMS，不是 SQL 語言本身；在 MySQL 裡 SCHEMA 與 DATABASE 是同義詞。
*   資料型態會影響可存內容、驗證方式、空間與計算結果；金額用 DECIMAL。
*   文字欄位搭配 utf8mb4 字元集，即可保存中文與各國文字，不需要 SQL Server 式的 n 開頭型態。

## 隨堂測驗

**Q1. 應用程式要長期保存使用者資料時，最合理的做法是什麼？**

- (A) 透過 DBMS 將資料寫入長期儲存裝置
- (B) 只把資料留在 CPU 暫存器
- (C) 只把資料留在主記憶體
- (D) 把所有資料轉成畫面截圖

<details><summary>看答案</summary>

**答案：(A)** 主記憶體斷電即失，DBMS 可管理並持久保存資料。

</details>

**Q2. 資料庫與 DBMS 的關係，哪個比喻最貼切？**

- (A) 資料庫像貨物與貨架，DBMS 像倉儲管理中心
- (B) 資料庫像管理員，DBMS 像一筆訂單
- (C) 資料庫與 DBMS 完全是同一概念
- (D) DBMS 只是一種欄位名稱

<details><summary>看答案</summary>

**答案：(A)** 資料庫是資料集合，DBMS 是管理資料庫的軟體。

</details>

**Q3. 在關聯式資料表中，一位顧客的一筆完整紀錄通常對應什麼？**

- (A) 一個資料列
- (B) 一個索引
- (C) 一個資料庫伺服器
- (D) 一個資料型態

<details><summary>看答案</summary>

**答案：(A)** 資料列代表一筆紀錄，欄位則描述該紀錄的各項屬性。

</details>

**Q4. 在 MySQL 中，SCHEMA 與 DATABASE 的關係是什麼？**

- (A) 兩者是同義詞，CREATE SCHEMA 等於 CREATE DATABASE
- (B) MySQL 完全沒有 SCHEMA 這個詞
- (C) SCHEMA 是 DATABASE 底下的一層
- (D) SCHEMA 只能放檢視表

<details><summary>看答案</summary>

**答案：(A)** 在 MySQL 裡 CREATE SCHEMA 是 CREATE DATABASE 的同義詞；把綱要當資料庫下一層的是其他產品。

</details>

**Q5. 儲存精確金額時，通常較適合哪種 MySQL 型態？**

- (A) DECIMAL
- (B) FLOAT
- (C) TEXT
- (D) DATE

<details><summary>看答案</summary>

**答案：(A)** DECIMAL 適合需要固定精度的金額，浮點數可能產生近似誤差。

</details>

**Q6. MySQL 與 SQL 的關係為何？**

- (A) MySQL 是資料庫管理系統，SQL 是操作關聯式資料庫的語言
- (B) MySQL 是欄位，SQL 是資料列
- (C) 兩者都是硬碟格式
- (D) SQL 只能用於 MySQL

<details><summary>看答案</summary>

**答案：(A)** SQL 可用於多種關聯式資料庫，MySQL 是其中一種 RDBMS。

</details>

**Q7. 用 utf8mb4 字元集時，「中文固定 2 個位元組」的說法哪裡不對？**

- (A) utf8mb4 每字元占 1〜4 個位元組，常用中文字多為 3 個
- (B) 中文其實固定 4 個位元組
- (C) 中文不能存進 MySQL
- (D) utf8mb4 只能存英文

<details><summary>看答案</summary>

**答案：(A)** utf8mb4 是變長編碼：英文字母 1 個位元組、常用中文字 3 個、少數擴充字元 4 個。

</details>

**Q8. 索引最主要的用途是什麼？**

- (A) 以額外空間與維護成本換取特定查詢效率
- (B) 自動替所有資料加密
- (C) 取代資料表保存全部資料
- (D) 保證任何查詢都在固定時間完成

<details><summary>看答案</summary>

**答案：(A)** 索引可加速符合其結構的查詢，但也會占空間並增加寫入成本。

</details>

**Q9. 正式應用程式較少直接使用 SELECT \* 的主要原因是什麼？**

- (A) 可能讀取不需要的欄位，並增加對資料表結構的依賴
- (B) 星號只能查到第一個欄位
- (C) SELECT \* 會永久刪除資料
- (D) MySQL 完全不支援星號

<details><summary>看答案</summary>

**答案：(A)** 明列欄位能讓資料需求更清楚，也能減少不必要的傳輸。

</details>
