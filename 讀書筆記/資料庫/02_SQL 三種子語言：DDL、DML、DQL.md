# 02. SQL 三種子語言：DDL、DML、DQL

> 來源：[筆記平台 · 資料庫](https://hhtim.github.io/notes-platform/database/#/lesson/sql-languages)　第 2 課 / 共 9 課 · 約 16 分鐘

**用一套商店範例學會定義資料表、異動資料、撰寫查詢，並以約束與交易守住一致性。**

### 讀完這課你會

*   使用 DDL 建立與修改資料表，並設定常見約束
*   使用 DML 安全地新增、修改與刪除資料
*   使用 DQL 篩選、排序、分組、連接與分頁查詢

*【先分清楚你正在改什麼】*

## DDL、DML、DQL 的分工

| 類別 | 操作對象 | 常見指令 |
| --- | --- | --- |
| DDL（資料定義語言） | 資料庫物件與結構 | CREATE、ALTER、DROP、TRUNCATE |
| DML（資料操作語言） | 資料表裡的紀錄 | INSERT、UPDATE、DELETE |
| DQL（資料查詢語言） | 想讀取的資料 | SELECT |

白話說，DDL 像裝潢店面，DML 像搬入或調整商品，DQL 像向店員提出查詢條件。實際資料庫產品在分類名稱、交易行為與語法細節上可能略有差異。

*【先蓋好容器】*

## 用 DDL 建立與維護資料表

```
CREATE DATABASE shop
  CHARACTER SET utf8mb4;

USE shop;

CREATE TABLE departments (
    department_id INT PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL,
    UNIQUE (department_name)
);

CREATE TABLE employees (
    employee_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    employee_name VARCHAR(100) NOT NULL,
    salary DECIMAL(10, 2) NOT NULL,
    hired_on DATE,
    department_id INT,
    CONSTRAINT fk_employee_department
        FOREIGN KEY (department_id)
        REFERENCES departments(department_id)
);
```

`CREATE` 建立物件；`ALTER` 修改既有結構；`DROP` 移除物件本身；`TRUNCATE` 快速清空資料表內的資料，但保留資料表結構。

```
ALTER TABLE employees
    ADD COLUMN email VARCHAR(255);

ALTER TABLE employees
    ADD CONSTRAINT uk_employee_email UNIQUE (email);

DROP TABLE old_employees;
```

> 💡 `DROP TABLE` 會連資料表結構一起移除（這裡示範刪掉一張不再用的舊表 old_employees），風險遠高於一般查詢。執行前應確認環境、物件名稱、備份與復原方案。

`TRUNCATE` 在 MySQL 中歸類為 DDL 而非 DML：它會隱含提交（執行的當下就等於自動 COMMIT），所以不能像還沒提交的 DML 那樣用 `ROLLBACK` 反悔。

*【把錯誤擋在入口】*

## 約束是資料表的守門員

| 約束 | 作用 | 例子 |
| --- | --- | --- |
| PRIMARY KEY | 唯一識別每筆紀錄，且不可為 NULL | employee_id |
| UNIQUE | 限制一欄或一組欄位不可出現重複值 | email |
| FOREIGN KEY | 要求值能對應到另一張表的識別值 | department_id |
| NOT NULL | 禁止缺值 | employee_name |
| CHECK | 要求資料符合條件 | salary >= 0 |
| DEFAULT | 未提供值時給予預設值 | status 預設 active |

嚴格說 `DEFAULT` 是欄位屬性（替欄位指定預設值），不是約束，只是常和約束一起設定[出處](https://dev.mysql.com/doc/refman/8.4/en/create-table.html)。

主鍵可以由一個欄位或多個欄位組成；多欄組合稱為複合主鍵（Composite Primary Key）。

```
CREATE TABLE enrollments (
    student_id BIGINT,
    course_id BIGINT,
    score DECIMAL(5, 2),
    PRIMARY KEY (student_id, course_id)
);
```

MySQL 的 `UNIQUE` 欄位可以是 NULL，而且允許多筆資料同時是 NULL——不可為 NULL 的是主鍵[出處](https://dev.mysql.com/doc/refman/8.4/en/create-index.html)。若業務要求該欄一定有值，要另外加上 `NOT NULL`。

> 📝 查證更正：原筆記寫唯一鍵（UK）「值不可為NULL」，查證後更正：MySQL 官方文件明訂 UNIQUE 索引允許可為 NULL 的欄位存放多個 NULL 值

外鍵要用資料表層級的 `FOREIGN KEY ... REFERENCES ...` 子句宣告才會生效：把 `REFERENCES` 直接寫在欄位定義那一行，MySQL 會解析但直接忽略，不會建立外鍵，也不會報錯——這是很容易踩到的無聲陷阱[出處](https://dev.mysql.com/doc/refman/8.4/en/create-table.html)。

*【新增時把欄位寫清楚】*

## INSERT：加入資料

```
INSERT INTO departments
    (department_id, department_name)
VALUES
    (10, '工程部'),
    (20, '業務部');

INSERT INTO employees
    (employee_name, salary, hired_on, department_id)
VALUES
    ('阿寶', 52000.00, '2026-09-01', 10);
```

即使要填入全部欄位，也建議明列欄位名稱。如此一來，SQL 比較容易閱讀，也不會過度依賴資料表當下的欄位順序。

`employee_id` 設為 `AUTO_INCREMENT` 後，新增時通常省略它，交由 MySQL 產生。自動編號的重點是提供識別值，不代表號碼必然連續。

*【修改與刪除前，先確認範圍】*

## UPDATE 與 DELETE

```
UPDATE employees
SET salary = salary + 500
WHERE department_id = 20;

DELETE FROM employees
WHERE employee_id = 105;
```

`WHERE` 決定哪些資料列會被異動。少了它，`UPDATE` 或 `DELETE` 會影響整張表。

安全做法是先用相同條件執行 `SELECT`，確認目標資料列，再於交易中執行異動。

```
SELECT employee_id, employee_name, salary
FROM employees
WHERE department_id = 20;
```

> 先 SELECT 看範圍，再 UPDATE 或 DELETE；條件與筆數都要符合預期。

*【查詢像組裝一條資料處理管線】*

## SELECT、WHERE 與 ORDER BY

```
SELECT
    employee_id,
    employee_name,
    salary
FROM employees
WHERE salary >= 50000
  AND department_id IN (10, 20)
ORDER BY salary DESC, employee_id ASC
LIMIT 10;
```

*   `SELECT`：指定輸出的欄位或運算結果。
*   `FROM`：指定資料來源。
*   `WHERE`：在分組前篩選資料列。
*   `ORDER BY`：排序；`ASC` 為遞增，`DESC` 為遞減。
*   `LIMIT`：限制回傳筆數。

常見條件還有 `BETWEEN`、`IN`、`LIKE` 與 `IS NULL`。NULL 表示未知或缺值，因此不能用 `= NULL` 判斷。

```
SELECT employee_name
FROM employees
WHERE email IS NULL;

SELECT employee_name
FROM employees
WHERE employee_name LIKE '阿%';
```

*【先分組，再回答群體問題】*

## 聚合函式、GROUP BY 與 HAVING

聚合函式（Aggregate Function，把多筆資料整理成一個摘要值）有 `COUNT`、`SUM`、`AVG`、`MIN` 與 `MAX`。

```
SELECT
    department_id,
    COUNT(*) AS employee_count,
    AVG(salary) AS average_salary
FROM employees
WHERE hired_on >= '2026-01-01'
GROUP BY department_id
HAVING COUNT(*) >= 3
ORDER BY average_salary DESC;
```

`WHERE` 在分組前排除個別資料列；`HAVING` 在分組後篩選群組，因此可以用聚合結果作條件。`COUNT(*)` 這類條件不能寫在 `WHERE`，要寫在 `HAVING`。

> 概念處理順序：FROM／JOIN → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT。

資料庫實際的執行計畫可能與這個順序不同；這裡說的是理解查詢結果時的邏輯順序。

*【資料拆開保存，查詢時再接回來】*

## JOIN 多表查詢

```
SELECT
    e.employee_name,
    d.department_name
FROM employees AS e
JOIN departments AS d
    ON e.department_id = d.department_id;
```

| 連接方式 | 結果 |
| --- | --- |
| INNER JOIN | 只保留兩邊能配對的資料列 |
| LEFT JOIN | 保留左表全部資料；右表配不到時補 NULL |
| RIGHT JOIN | 保留右表全部資料；左表配不到時補 NULL |

```
SELECT
    d.department_name,
    COUNT(e.employee_id) AS employee_count
FROM departments AS d
LEFT JOIN employees AS e
    ON e.department_id = d.department_id
GROUP BY d.department_id, d.department_name;
```

這裡使用 `LEFT JOIN`，即使某部門還沒有員工，也能出現在結果中。

*【查詢裡還能放查詢】*

## 子查詢、函數與分頁

```
SELECT employee_name, salary
FROM employees
WHERE salary > (
    SELECT AVG(salary)
    FROM employees
);
```

子查詢（Subquery，包在另一個查詢裡的查詢）先算出一個值或一組資料，再供外層查詢使用。簡單需求可以直接用；複雜查詢則要留意可讀性與效能。

```
SELECT
    UPPER(employee_name) AS display_name,
    ROUND(salary, 0) AS rounded_salary,
    CURRENT_DATE AS queried_on
FROM employees
ORDER BY employee_id
LIMIT 20 OFFSET 40;
```

這段查詢跳過前 40 筆，再取 20 筆——這就是分頁查詢的基本寫法。翻到很後面的頁面時，資料庫仍得掃過前面所有資料，大資料量下要留意效能。

*【一組動作要一起成功】*

## TCL、交易與 ACID

交易（Transaction）是一組視為整體的資料操作。例如轉帳必須同時扣除甲帳戶與增加乙帳戶，不能只完成一半。

```
START TRANSACTION;

UPDATE accounts
SET balance = balance - 1000
WHERE account_id = 1;

SAVEPOINT after_debit;

UPDATE accounts
SET balance = balance + 1000
WHERE account_id = 2;

COMMIT;
```

`COMMIT` 確認提交交易；`ROLLBACK` 取消尚未提交的變更；`ROLLBACK TO SAVEPOINT` 則退回某個保存點。

| 特性 | 意思 |
| --- | --- |
| 原子性（Atomicity） | 整組操作全成或全敗 |
| 一致性（Consistency） | 交易前後都遵守資料規則 |
| 隔離性（Isolation） | 並行交易之間看不看得到彼此的中間狀態，由隔離層級控制 |
| 持久性（Durability） | 已提交的結果在斷電、當機後仍保留 |

持久性保證的是「已提交」的交易：一旦 `COMMIT` 成功，結果就不怕斷電或當機。`ROLLBACK` 則相反——它把尚未提交的變更整個取消，不會對資料庫留下永久改變[出處](https://dev.mysql.com/doc/refman/8.4/en/glossary.html#glos_acid)。

> 📝 查證更正：原筆記寫持久性是「操作一旦提交或是還原，對資料庫中的改變就是永久的」，查證後更正：持久性只保證「已提交」的交易；還原（ROLLBACK）是取消尚未提交的變更，不會形成永久改變

交易能力也和儲存引擎有關：一般 MySQL Server 裡，預設的 InnoDB 引擎支援交易，MyISAM、MEMORY 這類引擎不支援[出處](https://dev.mysql.com/doc/refman/8.4/en/storage-engines.html)；另外 DDL（例如 TRUNCATE）會隱含提交，會把當下未提交的交易一併提交掉。

### 重點整理

*   DDL 管結構、DML 管資料異動、DQL 管查詢。
*   主鍵負責識別且不可為 NULL；UNIQUE 擋重複但允許多個 NULL；外鍵要用資料表層級語法宣告才生效。
*   執行 UPDATE 或 DELETE 前，先以相同 WHERE 條件 SELECT 確認影響範圍。
*   WHERE 篩資料列，HAVING 篩分組後的結果；聚合條件寫在 HAVING。
*   交易以 COMMIT、ROLLBACK 與 SAVEPOINT 控制；持久性保證的是已提交的結果。

## 隨堂測驗

**Q1. 要替既有 employees 資料表新增 email 欄位，應優先使用哪類指令？**

- (A) DDL 的 ALTER TABLE
- (B) DML 的 INSERT
- (C) DQL 的 SELECT
- (D) TCL 的 COMMIT

<details><summary>看答案</summary>

**答案：(A)** 修改資料表結構屬於 DDL，通常使用 ALTER TABLE。

</details>

**Q2. 為什麼 INSERT 時建議明列欄位名稱？**

- (A) 可清楚對應值與欄位，並降低對欄位順序的依賴
- (B) 可保證自動編號永遠連續
- (C) 可讓所有約束自動失效
- (D) 可省略 VALUES 關鍵字

<details><summary>看答案</summary>

**答案：(A)** 明列欄位可提升可讀性，也能降低結構調整造成的錯置風險。

</details>

**Q3. 某欄位必須有值且不能重複，應採用什麼設計？**

- (A) 同時設定 NOT NULL 與 UNIQUE
- (B) 只設定 DEFAULT
- (C) 只建立一般索引
- (D) 只使用 VARCHAR

<details><summary>看答案</summary>

**答案：(A)** UNIQUE 控制重複但允許 NULL，NOT NULL 才禁止缺值，兩者解決不同問題。

</details>

**Q4. 在 MySQL 中，UNIQUE 約束的欄位可以存 NULL 嗎？**

- (A) 可以，而且允許多筆資料同時是 NULL
- (B) 完全不行，跟主鍵一樣
- (C) 只能有一筆 NULL
- (D) 只有文字欄位可以

<details><summary>看答案</summary>

**答案：(A)** MySQL 的 UNIQUE 索引允許可為 NULL 的欄位存放多個 NULL；不可為 NULL 的是主鍵。

</details>

**Q5. 把 REFERENCES 直接寫在欄位定義那一行（欄位層級），MySQL 會怎麼處理？**

- (A) 解析後直接忽略，不會建立外鍵也不報錯
- (B) 正常建立外鍵
- (C) 回報語法錯誤
- (D) 自動改成主鍵

<details><summary>看答案</summary>

**答案：(A)** MySQL 只接受資料表層級的 FOREIGN KEY 子句；行內 REFERENCES 會被無聲忽略，是常見陷阱。

</details>

**Q6. 執行 UPDATE 前最實用的安全檢查是什麼？**

- (A) 先用相同 WHERE 條件執行 SELECT
- (B) 先移除主鍵
- (C) 先清空整張表
- (D) 省略 WHERE 以避免條件寫錯

<details><summary>看答案</summary>

**答案：(A)** 先查出預計影響的資料列，可確認條件與筆數是否合理。

</details>

**Q7. 要篩選「員工數至少三人的部門」，條件最適合放在哪裡？**

- (A) HAVING COUNT(\*) >= 3
- (B) WHERE COUNT(\*) >= 3
- (C) ORDER BY COUNT(\*) >= 3
- (D) LIMIT COUNT(\*) >= 3

<details><summary>看答案</summary>

**答案：(A)** COUNT 是分組後的聚合結果，因此應由 HAVING 篩選。

</details>

**Q8. 想列出所有部門，包括目前沒有員工的部門，應如何連接？**

- (A) 以 departments 為左表使用 LEFT JOIN employees
- (B) 使用 INNER JOIN 並刪除 ON
- (C) 以 employees 為唯一資料來源
- (D) 只使用 CROSS JOIN

<details><summary>看答案</summary>

**答案：(A)** LEFT JOIN 會保留左表所有部門，沒有員工時右側欄位為 NULL。

</details>

**Q9. 轉帳時扣款成功、入帳失敗，最後兩者都不生效，主要體現哪項交易特性？**

- (A) 原子性
- (B) 持久性
- (C) 隔離性
- (D) 一致性

<details><summary>看答案</summary>

**答案：(A)** 原子性要求一組交易操作全部成功，否則全部撤銷。

</details>

**Q10. TRUNCATE 清空的資料，能用 ROLLBACK 救回來嗎？**

- (A) 不能，TRUNCATE 是 DDL、會隱含提交
- (B) 可以，跟 DELETE 一樣
- (C) 只有清空一半時可以
- (D) 加上 SAVEPOINT 就可以

<details><summary>看答案</summary>

**答案：(A)** MySQL 的 TRUNCATE 歸類為 DDL，執行時隱含提交，無法用 ROLLBACK 復原。

</details>
