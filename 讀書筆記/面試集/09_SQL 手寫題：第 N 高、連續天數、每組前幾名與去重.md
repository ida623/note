# 09. SQL 手寫題：第 N 高、連續天數、每組前幾名與去重

> 來源：[筆記平台 · 面試集](https://hhtim.github.io/notes-platform/interview/#/lesson/sql-coding)　第 9 課 / 共 23 課 · 約 55 分鐘

**十題現場手寫 SQL：第 N 高、每部門前三高、連續出現、比前一天高、刪重複、移動平均、年增率與月增率、列轉欄、差集、最新交易與每日餘額，每題附寫錯版本的實跑結果與索引追問。**

### 讀完這課你會

*   寫出第 N 高、每組前 N 名與刪重複
*   分清移動平均裡的 ROWS 與 RANGE
*   寫出列轉欄與三種差集
*   寫出最新一筆交易與每日餘額

*【先講好怎麼答】*

## 手寫 SQL 的四個步驟

面試的 SQL 手寫題通常給你一兩張表、一句需求，要你在白板或線上編輯器寫出來。建議每題都照這個順序：

*   **先問邊界**：同分怎麼算？沒有資料時回空結果還是 NULL？「前一天」是日曆上的前一天，還是前一筆資料？
*   **先寫最直接的版本**，確定答案對了再談效能。
*   **自己舉一個會出錯的例子**：同分、缺號、缺日期、NULL，帶進去走一遍。
*   **主動補追問**：要建什麼索引、資料量大到幾千萬列時怎麼改。

以下用 MySQL 8.4，預設 `sql_mode`（含 `ONLY_FULL_GROUP_BY` 與嚴格模式）。

*【第一題】*

## 第 N 高的薪資（LeetCode 177）

> 💡 面試官：寫一個函式，傳入 N，回傳第 N 高的薪資；不存在就回 NULL。

測資是三個部門十個行員，授信部有兩人同為 85,000：

```
CREATE TABLE dept (id INT PRIMARY KEY, name VARCHAR(10) NOT NULL);
CREATE TABLE emp (
  id      INT PRIMARY KEY,
  name    VARCHAR(10) NOT NULL,
  dept_id INT NOT NULL,
  salary  INT NOT NULL
);
INSERT INTO dept VALUES (1, '授信部'), (2, '存匯部'), (3, '資訊部');
INSERT INTO emp VALUES
  (1, '王大明', 1, 90000), (2, '陳小美', 1, 85000), (3, '林志強', 1, 85000),
  (4, '張雅婷', 1, 70000), (5, '李建國', 1, 60000),
  (6, '黃淑芬', 2, 80000), (7, '吳家豪', 2, 75000), (8, '蔡宜君', 2, 50000),
  (9, '鄭文傑', 3, 120000), (10, '劉佳穎', 3, 95000);
```

第二高怎麼寫（包成純量子查詢，也就是只回一個值的子查詢，才會在沒有時回 NULL），〈SQL 進階：JOIN、子查詢、GROUP BY 與視窗函式〉講過。第 N 高的難處在於 N 是變數。最直覺的寫法是把 `N - 1` 直接寫進 OFFSET：

```
CREATE FUNCTION bad_nth(N INT) RETURNS INT DETERMINISTIC
  RETURN (SELECT DISTINCT salary FROM emp ORDER BY salary DESC LIMIT 1 OFFSET N - 1);

ERROR 1064 (42000): You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near '- 1)' at line 2
```

LIMIT 不接受運算式，參數必須是非負的整數常數，例外有兩個：[出處](https://dev.mysql.com/doc/refman/8.4/en/select.html)

*   預備陳述式可以用 `?`。
*   預存程式裡可以用整數型別的參數或區域變數。

所以先用 `SET N = N - 1` 算好，再把變數放進 OFFSET。第二個坑是函式的特性宣告：

```
DELIMITER //
CREATE FUNCTION nth_nochar(N INT) RETURNS INT
BEGIN
  SET N = N - 1;
  RETURN (SELECT DISTINCT salary FROM emp ORDER BY salary DESC LIMIT 1 OFFSET N);
END//

ERROR 1418 (HY000): This function has none of DETERMINISTIC, NO SQL, or READS SQL DATA in its declaration and binary logging is enabled (you *might* want to use the less safe log_bin_trust_function_creators variable)
```

MySQL 8.4 預設開著二進位日誌（binlog，複寫與還原用的變更紀錄）。這時建立預存函式必須宣告它是確定性的、或它不修改資料，否則可能對資料還原或複寫不安全；預設至少要寫 DETERMINISTIC、NO SQL、READS SQL DATA 其中一個（確定性是指同樣的輸入一定得到同樣的結果）。[出處](https://dev.mysql.com/doc/refman/8.4/en/stored-programs-logging.html) 這個函式只讀資料，寫 `READS SQL DATA`：

```
DELIMITER //
CREATE FUNCTION getNthHighestSalary(N INT) RETURNS INT
READS SQL DATA
BEGIN
  SET N = N - 1;
  RETURN (SELECT DISTINCT salary FROM emp ORDER BY salary DESC LIMIT 1 OFFSET N);
END//
DELIMITER ;

SELECT getNthHighestSalary(1) AS n1, getNthHighestSalary(4) AS n4, getNthHighestSalary(10) AS n10;
+--------+-------+------+
| n1     | n4    | n10  |
+--------+-------+------+
| 120000 | 85000 | NULL |
+--------+-------+------+
```

不同的薪資只有九種，第 10 高不存在：`RETURN` 後面的純量子查詢沒有列，值就是 NULL。`DISTINCT` 不能省，少了它，同分會佔掉名次：

```
SELECT salary FROM emp ORDER BY salary DESC LIMIT 1 OFFSET 4;           -- 85000（兩個 85000 佔了第 4、5 名）
SELECT DISTINCT salary FROM emp ORDER BY salary DESC LIMIT 1 OFFSET 4;  -- 80000（第 5 高）
```

不寫函式時，也可以用 DENSE_RANK（同分同名次、不跳號）篩 `dr = N`，實跑第 4 高一樣是 85000。

**追問：索引**。在 `salary` 上建索引後，實跑 EXPLAIN：

```
EXPLAIN FORMAT=TREE SELECT DISTINCT salary FROM emp ORDER BY salary DESC LIMIT 1 OFFSET 4;
-> Limit/Offset: 1/4 row(s)  (cost=0.875 rows=0)
    -> Group (no aggregates)  (cost=0.875 rows=2.24)
        -> Covering index scan on emp using idx_sal (reverse)  (cost=0.375 rows=5)
```

倒著讀索引（reverse）、邊讀邊去重，讀到第 5 個不同值就停，沒有另外排序。EXPLAIN 怎麼看見〈索引是怎麼運作的〉。

**🧩 小練習：** 在 MySQL 8.4 寫 `… LIMIT 1 OFFSET N - 1`（N 是函式參數），會怎樣？

- (A) 報錯：LIMIT 不接受運算式
- (B) 正常執行，回傳第 N 高的薪資
- (C) 正常執行，但回傳第 N − 1 高
- (D) 只有 N 大於 1 的時候才報錯

<details><summary>看答案</summary>

**答案：(A)** 實跑 ERROR 1064。LIMIT 的參數要是整數常數，預存程式裡可以用參數或區域變數，但不能是運算式；所以先 SET N = N - 1。

</details>

**🧩 小練習：** 函式沒寫 DETERMINISTIC、NO SQL、READS SQL DATA 任何一個，在預設開著二進位日誌的 MySQL 8.4 建立時會怎樣？

- (A) 自動當成 DETERMINISTIC
- (B) 可以建立，但執行時報錯
- (C) 建立時就報 ERROR 1418
- (D) 只會出現警告，照常建立

<details><summary>看答案</summary>

**答案：(C)** 開著二進位日誌時，建立預存函式必須宣告它是確定性的或不修改資料，否則對還原與複寫不安全。實跑 ERROR 1418；這個函式只讀資料，寫 READS SQL DATA。

</details>

**🧩 小練習：** 薪資由高到低是 120000、95000、90000、85000、85000、80000……。`SELECT salary … ORDER BY salary DESC LIMIT 1 OFFSET 4`（沒有 DISTINCT）回傳什麼？

- (A) 80000
- (B) 90000
- (C) 75000
- (D) 85000

<details><summary>看答案</summary>

**答案：(D)** 不去重時跳過的是 4 列：120000、95000、90000、85000，第 5 列還是 85000。要第 5 高（80000）就加 DISTINCT。

</details>

**🧩 小練習：** 不同的薪資只有 9 種，`getNthHighestSalary(10)` 回傳什麼？

- (A) NULL
- (B) 最低的薪資 50000
- (C) 報錯：沒有第 10 列
- (D) 0

<details><summary>看答案</summary>

**答案：(A)** RETURN 後面是純量子查詢，子查詢沒有列，值就是 NULL，題目要求的正是這個。

</details>

*【第二題】*

## 每部門前三高，同分都要列（LeetCode 184、185）

> 💡 面試官：列出每個部門薪資前三高的人；「前三高」指前三種薪資，同分的都要列出來。

「每組前 N 名」的基本骨架（子查詢裡排名、外層篩）〈SQL 進階：JOIN、子查詢、GROUP BY 與視窗函式〉講過。這題的考點是同分：授信部的薪資是 90000、85000、85000、70000、60000，前三種薪資是 90000、85000、70000，所以要列出 4 個人。

```
SELECT d.name AS dept, e.name, e.salary
FROM (SELECT e.*, DENSE_RANK() OVER (PARTITION BY dept_id ORDER BY salary DESC) AS dr FROM emp e) e
JOIN dept d ON d.id = e.dept_id
WHERE e.dr <= 3
ORDER BY d.id, e.salary DESC, e.id;
+-----------+-----------+--------+
| dept      | name      | salary |
+-----------+-----------+--------+
| 授信部    | 王大明    |  90000 |
| 授信部    | 陳小美    |  85000 |
| 授信部    | 林志強    |  85000 |
| 授信部    | 張雅婷    |  70000 |
| 存匯部    | 黃淑芬    |  80000 |
| 存匯部    | 吳家豪    |  75000 |
| 存匯部    | 蔡宜君    |  50000 |
| 資訊部    | 鄭文傑    | 120000 |
| 資訊部    | 劉佳穎    |  95000 |
+-----------+-----------+--------+
9 rows in set
```

把 DENSE_RANK 換成 ROW_NUMBER，實跑只剩 8 列：兩個 85000 拿了 2、3 號，張雅婷的 70000 排到第 4 號被篩掉。資訊部只有兩個人，就只列兩個，不會補空列。

沒有視窗函式時的經典寫法是相關子查詢（子查詢裡用到外層那一列的欄位，外層每一列都重算一次）：「同部門裡，薪資比我高的**不同薪資**少於 3 種」：

```
SELECT d.name AS dept, e1.name, e1.salary
FROM emp e1 JOIN dept d ON d.id = e1.dept_id
WHERE (SELECT COUNT(DISTINCT e2.salary) FROM emp e2
       WHERE e2.dept_id = e1.dept_id AND e2.salary > e1.salary) < 3
ORDER BY d.id, e1.salary DESC, e1.id;
```

實跑結果跟 DENSE_RANK 版完全相同（9 列）。把 `COUNT(DISTINCT e2.salary)` 寫成 `COUNT(*)` 是最常見的寫錯：張雅婷上面有 3 個人（90000、85000、85000），COUNT(\*) 是 3、不小於 3，她就被篩掉，實跑同樣只剩 8 列。

只要每部門最高（184）時，可以用「部門、最高薪資」整組比對，同分的會一起留下：

```
SELECT d.name AS dept, e.name, e.salary
FROM emp e JOIN dept d ON d.id = e.dept_id
WHERE (e.dept_id, e.salary) IN (SELECT dept_id, MAX(salary) FROM emp GROUP BY dept_id)
ORDER BY d.id;
+-----------+-----------+--------+
| dept      | name      | salary |
+-----------+-----------+--------+
| 授信部    | 王大明    |  90000 |
| 存匯部    | 黃淑芬    |  80000 |
| 資訊部    | 鄭文傑    | 120000 |
+-----------+-----------+--------+
```

**追問：索引**。直覺是建複合索引 `(dept_id, salary)`，但它幫到哪一種寫法要看 EXPLAIN。建好之後實跑：

```
-- 視窗函式版（節錄）：仍然要排序
-> Window aggregate: dense_rank() OVER (PARTITION BY e.dept_id ORDER BY e.salary desc )
    -> Sort: e.dept_id, e.salary DESC  (cost=1.25 rows=10)
        -> Table scan on e  (cost=1.25 rows=10)

-- 相關子查詢版（節錄）：子查詢用上了索引
-> Select #2 (subquery in condition; dependent)
    -> Aggregate: count(distinct e2.salary)
        -> Filter: (e2.salary > e1.salary)
            -> Covering index lookup on e2 using idx_dept_sal (dept_id=e1.dept_id)
```

視窗函式版在這份資料上還是整表讀出、再依部門與薪資排序；相關子查詢版的子查詢則改成「到索引裡找同部門的薪資」，不必讀整張表。但相關子查詢是外層每一列都跑一次子查詢，部門人數一多總量還是大。結論要照實講：索引不是建了就一定有用，建完要看 EXPLAIN。索引失效的常見寫法見〈資料庫面試題：索引、交易隔離與鎖〉。

**🧩 小練習：** 授信部薪資 90000、85000、85000、70000、60000。用 `DENSE_RANK() … <= 3`，授信部列出幾個人？

- (A) 3
- (B) 4
- (C) 5
- (D) 2

<details><summary>看答案</summary>

**答案：(B)** DENSE_RANK 給 90000 第 1、兩個 85000 第 2、70000 第 3，共 4 人。題目要的是「前三種薪資」，同分都列。

</details>

**🧩 小練習：** 同一題改用 `ROW_NUMBER() … <= 3`，授信部少了誰？

- (A) 王大明
- (B) 陳小美或林志強其中一個
- (C) 張雅婷
- (D) 沒有少，一樣 4 人

<details><summary>看答案</summary>

**答案：(C)** ROW_NUMBER 同分也硬排：90000 是 1、兩個 85000 是 2 和 3，70000 變成 4 號被篩掉。實跑全表 8 列，少的就是張雅婷。

</details>

**🧩 小練習：** 相關子查詢寫成 `(SELECT COUNT(*) FROM emp e2 WHERE e2.dept_id = e1.dept_id AND e2.salary > e1.salary) < 3`，錯在哪？

- (A) 相關子查詢在 MySQL 不能用
- (B) 比較條件應該改成 <= 3
- (C) 應該改比 e2.salary < e1.salary
- (D) 同分重複算，要數不同薪資

<details><summary>看答案</summary>

**答案：(D)** 題目要的是比我高的「不同薪資」有幾種。COUNT(\*) 把兩個 85000 算成兩個，張雅婷上面變成 3、被篩掉。

</details>

**🧩 小練習：** 每部門最高薪資，兩個人同為最高時，`WHERE (dept_id, salary) IN (SELECT dept_id, MAX(salary) … GROUP BY dept_id)` 會列出幾個人？

- (A) 兩個都列
- (B) 只列 id 小的那個
- (C) 隨機列一個
- (D) 報錯：IN 不能比兩欄

<details><summary>看答案</summary>

**答案：(A)** 比對的是「部門、薪資」這一組值，兩個人的值都等於該部門最高，所以都會留下。

</details>

*【第三題】*

## 連續出現至少三次（LeetCode 180）

> 💡 面試官：日誌表依 id 排序，找出連續出現至少三次的數字。

```
CREATE TABLE logs (id INT PRIMARY KEY, num INT NOT NULL);
INSERT INTO logs VALUES (1,1),(2,1),(3,1),(4,2),(5,1),(6,2),(7,2),(8,3),(9,3),(10,2);
```

最常見的寫錯是只數總次數：`GROUP BY num HAVING COUNT(*) >= 3` 實跑回 1 和 2。但 2 出現在第 4、6、7、10 列，從沒連續三次。正解有兩種：

```
-- 自我連接：自己、下一號、下下一號都相同
SELECT DISTINCT l1.num AS ConsecutiveNums
FROM logs l1
JOIN logs l2 ON l2.id = l1.id + 1 AND l2.num = l1.num
JOIN logs l3 ON l3.id = l1.id + 2 AND l3.num = l1.num;

-- LAG／LEAD：跟前一列、後一列比
SELECT DISTINCT num AS ConsecutiveNums
FROM (SELECT num, LAG(num) OVER (ORDER BY id) AS prev, LEAD(num) OVER (ORDER BY id) AS nxt FROM logs) t
WHERE num = prev AND num = nxt;
```

兩種實跑都只回 1。差別在 id 有缺號時。LAG 拿的是同一分組裡往前第 N **列**的值。[出處](https://dev.mysql.com/doc/refman/8.4/en/window-function-descriptions.html) 自我連接比的是 id 數字。另一張表 `logs2` 是 (1,7)、(2,7)、(4,7)、(5,8)，第 3 號被刪掉了：自我連接實跑是 Empty set（找不到 id 3），LAG／LEAD 版回 7。哪個對，要先問清楚「連續」是指日誌裡一筆接一筆，還是 id 數字相連。

題目改成「至少連續 N 次、列出起訖」，用〈SQL 進階：JOIN、子查詢、GROUP BY 與視窗函式〉連續登入那招的變形：兩個列號相減。整體列號是一筆接一筆編，分組內列號只在同一個數字裡編；同一段連續的值，兩者一起往前走，差值固定。

```
SELECT num, COUNT(*) AS times
FROM (SELECT num, ROW_NUMBER() OVER (ORDER BY id)
                  - ROW_NUMBER() OVER (PARTITION BY num ORDER BY id) AS grp FROM logs2) t
GROUP BY num, grp;
+-----+-------+
| num | times |
+-----+-------+
|   7 |     3 |
|   8 |     1 |
+-----+-------+
```

如果改用 `id - ROW_NUMBER() OVER (PARTITION BY num ORDER BY id)`，缺號會被當成斷開：實跑 7 被分成「2 次」與「1 次」兩段。另一個坑是型別：ROW_NUMBER 回傳的是不帶正負號的整數，相減結果是負數時會直接報錯。實跑 `0 - ROW_NUMBER() OVER (…)` 得到 `ERROR 1690 (22003): BIGINT UNSIGNED value is out of range`。整數相減時只要有一方是 UNSIGNED，結果預設也是 UNSIGNED，結果原本會是負數就出錯。[出處](https://dev.mysql.com/doc/refman/8.4/en/out-of-range-and-overflow.html) 讓大的減小的（整體列號一定不小於分組內列號），或先 `CAST(… AS SIGNED)`。

**🧩 小練習：** `SELECT num FROM logs GROUP BY num HAVING COUNT(*) >= 3` 為什麼不是「連續三次」的正解？

- (A) 它數的是總次數，不管有沒有相連
- (B) GROUP BY 不能配 HAVING
- (C) COUNT(\*) 會把 NULL 也算進去
- (D) 它只會回傳一個數字

<details><summary>看答案</summary>

**答案：(A)** 2 出現了 4 次但從沒連續三次，這個寫法照樣把它列出來。連續要比前後列，或用列號相減分段。

</details>

**🧩 小練習：** id 是 1、2、4（num 都是 7），3 號被刪掉了。自我連接 `l2.id = l1.id + 1 AND l3.id = l1.id + 2` 找得到 7 嗎？

- (A) 找得到，因為還是三筆 7
- (B) 找不到，沒有 id 3 可以接
- (C) 報錯，id 不連續不能自我連接
- (D) 找得到，但會重複出現兩次

<details><summary>看答案</summary>

**答案：(B)** 自我連接比的是 id 的數字，缺號就接不上，實跑 Empty set；LAG／LEAD 比的是前後列，實跑回 7。先問清楚「連續」的定義。

</details>

**🧩 小練習：** 「整體列號 − 分組內列號」為什麼能把連續的同一個值分成一組？

- (A) 同值連續時兩個列號同步加一
- (B) 因為兩個列號在每一列都相等
- (C) 因為 ROW_NUMBER 會自動跳過缺號
- (D) 因為相減之後結果一定是 0

<details><summary>看答案</summary>

**答案：(A)** 同一段連續的 7，整體列號與 7 自己的列號同步往前；中間插進別的數字，整體列號多走幾步，差值就變成新的一組。

</details>

**🧩 小練習：** `0 - ROW_NUMBER() OVER (ORDER BY x)` 在 MySQL 8.4 會怎樣？

- (A) 回傳 −1、−2 這樣的負數
- (B) 回傳 0，負數一律當成 0
- (C) ERROR 1690，超出範圍
- (D) 自動轉成帶正負號的整數再算

<details><summary>看答案</summary>

**答案：(C)** ROW_NUMBER 是不帶正負號的整數；有一方是 UNSIGNED 時相減結果也是 UNSIGNED，結果為負就出錯。讓大的減小的，或先 CAST(… AS SIGNED)。

</details>

*【第四題】*

## 比前一天高（LeetCode 197）

> 💡 面試官：牌告匯率表每天一筆，列出「美元匯率比前一天高」的日子。

```
CREATE TABLE fx (id INT PRIMARY KEY, rate_date DATE NOT NULL, usd_rate DECIMAL(6,3) NOT NULL);
INSERT INTO fx VALUES
  (1, '2026-09-01', 30.100), (2, '2026-09-02', 30.250), (3, '2026-09-03', 30.200),
  (5, '2026-09-04', 30.180), (4, '2026-09-07', 30.300), (6, '2026-09-08', 30.420);
```

這份資料有兩個細節：9/5、9/6 是週末沒有牌告；id 不照日期順序（補登過）。照日曆的「前一天」，用日期自我連接：

```
SELECT today.rate_date, today.usd_rate
FROM fx today
JOIN fx yest ON yest.rate_date = today.rate_date - INTERVAL 1 DAY
WHERE today.usd_rate > yest.usd_rate
ORDER BY today.rate_date;
+------------+----------+
| rate_date  | usd_rate |
+------------+----------+
| 2026-09-02 |   30.250 |
| 2026-09-08 |   30.420 |
+------------+----------+
```

9/7 沒有「前一天」（9/6 沒資料），不列。兩種常見寫法會多出 9/7：

*   **用 id 當前一天**（`yest.id = today.id - 1`）：9/7 的 id 是 4，接到 id 3 的 9/3，30.300 > 30.200 就被列出來。id 只是流水號，不保證跟日期同順序。
*   **用 LAG**（`LAG(usd_rate) OVER (ORDER BY rate_date)`）：LAG 拿的是前一**列**，9/7 的前一列是 9/4，30.300 > 30.180，也被列出來。要用 LAG，就連日期一起拿出來檢查 `DATEDIFF(rate_date, prev_date) = 1`，實跑結果跟自我連接相同。

反過來，如果需求其實是「跟前一個營業日比」，9/7 就該列，這時直接用 LAG 才對。這正是開頭說的「先問邊界」。

**追問：索引與資料量。**`rate_date` 建唯一索引，自我連接每一列都是一次等號查找；LAG 版只要依日期排序掃一次，資料量大時通常比較省。

**🧩 小練習：** 9/5、9/6 沒有資料。照「日曆上的前一天」，9/7 應不應該列出來？

- (A) 應該，它比 9/4 的匯率高
- (B) 應該，它比 9/3 的匯率高
- (C) 要看 id 是不是連號才知道
- (D) 不應該，沒有前一天可比

<details><summary>看答案</summary>

**答案：(D)** 9/7 的前一天是 9/6，沒有牌告，就沒得比。實跑日期自我連接只回 9/2、9/8。

</details>

**🧩 小練習：** 用 `yest.id = today.id - 1` 找前一天，這份資料為什麼會錯？

- (A) id 是主鍵，不能拿來運算
- (B) id 是流水號，跟日期順序不一致
- (C) DECIMAL 不能比大小
- (D) 自我連接一定要用 LEFT JOIN

<details><summary>看答案</summary>

**答案：(B)** 9/7 的 id 是 4，接到 id 3 的 9/3，於是 30.300 > 30.200 被列出來。比日期就用日期。

</details>

**🧩 小練習：** `LAG(usd_rate) OVER (ORDER BY rate_date)` 在 9/7 那列拿到的是哪一天的匯率？

- (A) 9/6
- (B) NULL，因為 9/6 沒資料
- (C) 9/8
- (D) 9/4

<details><summary>看答案</summary>

**答案：(D)** LAG 拿的是前一列，不是前一天；9/7 的前一列是 9/4。所以 LAG 版會多列出 9/7，要再檢查日期差是 1。

</details>

**🧩 小練習：** 面試官說「其實是跟前一個營業日比」。哪個寫法最直接？

- (A) LAG 拿前一列，直接比
- (B) 日期自我連接減 1 天
- (C) id 自我連接減 1
- (D) GROUP BY 日期再比 MAX

<details><summary>看答案</summary>

**答案：(A)** 資料只有營業日，前一列就是前一個營業日，LAG 正好符合。需求一變，正解就跟著變。

</details>

*【第五題】*

## 刪掉重複的資料，只留 id 最小的（LeetCode 196）

> 💡 面試官：聯絡人表的 email 有重複，刪到每個 email 只剩 id 最小的那一筆。

```
CREATE TABLE contact (id INT PRIMARY KEY, email VARCHAR(50) NOT NULL);
INSERT INTO contact VALUES
  (1, 'ming@example.com'), (2, 'mei@example.com'), (3, 'ming@example.com'),
  (4, 'hua@example.com'),  (5, 'mei@example.com'), (6, 'ming@example.com');

-- 先 SELECT 看要刪的範圍
SELECT email, COUNT(*) AS n, MIN(id) AS keep_id
FROM contact GROUP BY email HAVING COUNT(*) > 1 ORDER BY email;
+------------------+---+---------+
| email            | n | keep_id |
+------------------+---+---------+
| mei@example.com  | 2 |       2 |
| ming@example.com | 3 |       1 |
+------------------+---+---------+
```

最直覺的寫法是「刪掉不在『每組最小 id』裡的」：

```
DELETE FROM contact WHERE id NOT IN (SELECT MIN(id) FROM contact GROUP BY email);

ERROR 1093 (HY000): You can't specify target table 'contact' for update in FROM clause
```

不能從一張表刪除，又在子查詢裡從同一張表讀取。[出處](https://dev.mysql.com/doc/refman/8.4/en/delete.html) 兩種改法：

```
-- 改法一：多表 DELETE，自己接自己，刪掉「有更小 id 的同一個 email」
DELETE c1 FROM contact c1
JOIN contact c2 ON c1.email = c2.email AND c1.id > c2.id;
Query OK, 3 rows affected

-- 改法二：子查詢再包一層衍生資料表
DELETE FROM contact
WHERE id NOT IN (SELECT keep_id FROM (SELECT MIN(id) AS keep_id FROM contact GROUP BY email) AS k);
Query OK, 3 rows affected
```

兩種實跑都刪了 3 筆，剩下 1、2、4。改法二能跑的原因：

*   MySQL 把衍生資料表（放在 FROM 裡、有名字的子查詢結果）先算成暫存表，EXPLAIN 裡那一列的 select_type 是 DERIVED；刪除時讀的是暫存表，不是正要刪的那張表。
*   這題的內層剛好有 GROUP BY，屬於一定不會合併的寫法；會阻止合併的還有聚合函式、視窗函式、DISTINCT、LIMIT 等。
*   不合併就能避開 ER_UPDATE_TABLE_USED 錯誤，也就是 1093 這個錯。[出處](https://dev.mysql.com/doc/refman/8.4/en/derived-table-optimization.html)
*   不含 GROUP BY 的衍生資料表一樣能刪：實跑 `DELETE FROM contact WHERE id IN (SELECT id FROM (SELECT id FROM contact WHERE id > 4) AS k)` 刪了 2 筆，EXPLAIN 那一列同樣是 DERIVED。

改成保留「最新一筆」的版本用 ROW_NUMBER，見〈SQL 進階：JOIN、子查詢、GROUP BY 與視窗函式〉去重那段。

**追問：之後怎麼不再重複、表很大怎麼刪**。清完加唯一索引 `ALTER TABLE contact ADD UNIQUE KEY uk_email (email)`，再插入重複的 email 實跑是 `ERROR 1062 (23000): Duplicate entry 'ming@example.com' for key 'contact.uk_email'`。幾千萬列的表不要一次刪：[出處](https://dev.mysql.com/doc/refman/8.4/en/delete.html)

*   從大表刪很多列時，InnoDB 可能超過鎖表的容量，也會讓表被鎖住比較久。
*   為了讓單一 DELETE 不要跑太久，可以加 LIMIT，重複執行到影響的列數小於 LIMIT 為止。
*   多表 DELETE 不能用 ORDER BY 或 LIMIT。

所以要分批就用改法二，它是單表 DELETE：

```
DELETE FROM contact
WHERE id NOT IN (SELECT keep_id FROM (SELECT MIN(id) AS keep_id FROM contact GROUP BY email) AS k)
ORDER BY id LIMIT 2;          -- 實跑第一次刪 2 筆，第二次刪 1 筆，小於 LIMIT 就停
```

正式環境把 LIMIT 設成 10000 這類數字，重複執行到影響的列數小於它為止；另一種做法是依主鍵範圍一段一段刪（例如每次 `id BETWEEN 1 AND 10000`）。

**🧩 小練習：** `DELETE FROM contact WHERE id NOT IN (SELECT MIN(id) FROM contact GROUP BY email)` 在 MySQL 8.4 會怎樣？

- (A) 正常執行，刪掉 3 筆重複
- (B) ERROR 1093，讀了要刪的表
- (C) 把整張表的資料全部刪光
- (D) 只刪掉 email 是 NULL 的列

<details><summary>看答案</summary>

**答案：(B)** 不能從一張表刪除，又在子查詢裡從同一張表讀取。改用多表 DELETE 自我連接，或把子查詢再包一層衍生資料表。

</details>

**🧩 小練習：** `DELETE c1 FROM contact c1 JOIN contact c2 ON c1.email = c2.email AND c1.id > c2.id` 刪掉的是哪些列？

- (A) 每個 email 裡 id 最小的那一筆
- (B) 還有更小 id 的同 email 列
- (C) 所有 email 有重複的列都刪
- (D) 只刪掉每組 id 最大的那一筆

<details><summary>看答案</summary>

**答案：(B)** c1.id > c2.id 的意思是「c1 前面還有同 email 的更小 id」，這些都刪；每組 id 最小的那筆找不到更小的，留下。實跑刪 3 筆，剩 1、2、4。

</details>

**🧩 小練習：** 把子查詢再包一層 `(SELECT keep_id FROM (SELECT MIN(id) … GROUP BY email) AS k)` 就不報 1093 了。主要原因是？

- (A) 衍生資料表一定要取別名
- (B) MIN 會自動加鎖
- (C) 衍生資料表先算成暫存表，刪時不讀原表
- (D) NOT IN 遇到衍生資料表會自動改成 NOT EXISTS

<details><summary>看答案</summary>

**答案：(C)** EXPLAIN 裡那一列是 DERIVED：衍生資料表先算成暫存表，刪除時讀的是暫存表，所以避開了 ER_UPDATE_TABLE_USED（1093）。不含 GROUP BY 的衍生資料表實跑一樣能刪。

</details>

**🧩 小練習：** 幾千萬列的表要分批刪重複資料，為什麼不能直接在多表 DELETE 後面加 `LIMIT 10000`？

- (A) 多表 DELETE 不能用 LIMIT
- (B) LIMIT 會讓刪除變得很慢
- (C) LIMIT 只能用在 SELECT 裡
- (D) InnoDB 不支援分批刪除資料

<details><summary>看答案</summary>

**答案：(A)** 多表 DELETE 不能用 ORDER BY 或 LIMIT。單表 DELETE 可以用 LIMIT；多表版通常改成依主鍵範圍一段一段刪，或改用單表寫法加 LIMIT。

</details>

*【第六題】*

## 七日移動平均（LeetCode 1321）

> 💡 面試官：ATM 每日提款總額，算每天的「近 7 日」平均。

```
CREATE TABLE atm_daily (d DATE PRIMARY KEY, amount INT NOT NULL);
INSERT INTO atm_daily VALUES
  ('2026-09-01', 100), ('2026-09-02', 120), ('2026-09-03', 80), ('2026-09-04', 140),
  ('2026-09-05', 60),  ('2026-09-06', 90),  ('2026-09-07', 110),
  ('2026-09-09', 150), ('2026-09-10', 130);   -- 9/8 機台維修，沒有資料
```

累計（從頭加到目前這列）〈SQL 進階：JOIN、子查詢、GROUP BY 與視窗函式〉講過；移動平均是「只看最近幾天」，要自己寫框架（frame，算這一列時要納入哪幾列）。關鍵是 ROWS 與 RANGE 的差別（沒寫框架時的預設框架與同分列，見〈SQL 進階：JOIN、子查詢、GROUP BY 與視窗函式〉）：[出處](https://dev.mysql.com/doc/refman/8.4/en/window-functions-frames.html)

*   `ROWS`：框架由起訖的列位置定義，位移是列號的差。
*   `RANGE`：框架由一個值的範圍內的列定義，位移是列值的差；位移可以寫成時間區間 `INTERVAL val unit`。

先用「近 3 日」看差別：

```
SELECT d, amount,
       SUM(amount) OVER (ORDER BY d ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)                 AS sum_3rows,
       SUM(amount) OVER (ORDER BY d RANGE BETWEEN INTERVAL 2 DAY PRECEDING AND CURRENT ROW)   AS sum_3days,
       COUNT(*)    OVER (ORDER BY d RANGE BETWEEN INTERVAL 2 DAY PRECEDING AND CURRENT ROW)   AS days_in
FROM atm_daily ORDER BY d;
+------------+--------+-----------+-----------+---------+
| d          | amount | sum_3rows | sum_3days | days_in |
+------------+--------+-----------+-----------+---------+
| 2026-09-01 |    100 |       100 |       100 |       1 |
| 2026-09-02 |    120 |       220 |       220 |       2 |
| 2026-09-03 |     80 |       300 |       300 |       3 |
| 2026-09-04 |    140 |       340 |       340 |       3 |
| 2026-09-05 |     60 |       280 |       280 |       3 |
| 2026-09-06 |     90 |       290 |       290 |       3 |
| 2026-09-07 |    110 |       260 |       260 |       3 |
| 2026-09-09 |    150 |       350 |       260 |       2 |
| 2026-09-10 |    130 |       390 |       280 |       2 |
+------------+--------+-----------+-----------+---------+
```

9/8 沒資料之前兩者一樣。到了 9/9，ROWS 拿的是「前兩列」9/6、9/7，其實橫跨了 4 天；RANGE 拿的是「前兩天以內」9/7、9/9 兩筆（9/8 本來就沒有）。「近 N 日」要用 RANGE。七日版本，只列滿 7 天的日子：

```
SELECT d, sum_7d, ROUND(sum_7d / 7, 2) AS avg_7d
FROM (SELECT d,
             SUM(amount) OVER (ORDER BY d RANGE BETWEEN INTERVAL 6 DAY PRECEDING AND CURRENT ROW) AS sum_7d
      FROM atm_daily) t
WHERE d >= (SELECT MIN(d) FROM atm_daily) + INTERVAL 6 DAY
ORDER BY d;
+------------+--------+--------+
| d          | sum_7d | avg_7d |
+------------+--------+--------+
| 2026-09-07 |    700 | 100.00 |
| 2026-09-09 |    630 |  90.00 |
| 2026-09-10 |    680 |  97.14 |
+------------+--------+--------+
```

這裡用 `sum_7d / 7`，是把沒資料的 9/8 當成 0；如果寫 `AVG(amount) OVER (…)`，9/9 會除以 6 筆，得到 105。哪個對又是需求問題：維修沒營業算 0，還是不列入？另外，結果裡沒有 9/8 這一列，要列出來就先用遞迴 CTE 產生日期序列再 LEFT JOIN，做法見〈SQL 進階：JOIN、子查詢、GROUP BY 與視窗函式〉。

**🧩 小練習：** 9/8 沒有資料。`ROWS BETWEEN 2 PRECEDING AND CURRENT ROW` 在 9/9 那列加總了哪幾天？

- (A) 9/7、9/8、9/9
- (B) 只有 9/9
- (C) 9/6、9/7、9/9
- (D) 9/7、9/9

<details><summary>看答案</summary>

**答案：(C)** ROWS 數的是列：9/9 的前兩列是 9/6、9/7。實跑 sum_3rows = 90 + 110 + 150 = 350，其實橫跨 4 天。

</details>

**🧩 小練習：** 同一列改用 `RANGE BETWEEN INTERVAL 2 DAY PRECEDING AND CURRENT ROW`，加總是多少？

- (A) 350
- (B) 260
- (C) 150
- (D) 390

<details><summary>看答案</summary>

**答案：(B)** RANGE 看的是值的範圍：9/7 到 9/9 之間有資料的是 9/7（110）與 9/9（150），共 260，實跑 days_in = 2。

</details>

**🧩 小練習：** 「近 7 日平均」在 9/9 這天，`SUM(…) / 7` 得 90、`AVG(…)` 得 105。差在哪？

- (A) AVG 會自動四捨五入到整數
- (B) SUM 用的是 ROWS，AVG 用的是 RANGE
- (C) 前者把 9/8 當 0，後者除以 6
- (D) AVG 會把沒資料的日子當成 0

<details><summary>看答案</summary>

**答案：(C)** 9/3 到 9/9 有資料的是 6 天，加總 630；除以 7 是 90，除以 6 是 105。要哪一個，先問需求。

</details>

**🧩 小練習：** MySQL 8.4 的 RANGE 框架，位移可以怎麼寫？

- (A) 只能寫列數，例如 6 PRECEDING
- (B) 只能寫 UNBOUNDED PRECEDING
- (C) 只能用在數字型別的欄位
- (D) 可以寫 INTERVAL 6 DAY

<details><summary>看答案</summary>

**答案：(D)** 位移可以是非負數字或 INTERVAL val unit 形式的時間區間；RANGE 要配數字或時間型別的 ORDER BY。

</details>

*【第七題】*

## 年增率與月增率

> 💡 面試官：每月新增存款，算出每個月的月增率與年增率。

先講名詞。**月增率**是跟「上一個月」比（month-over-month，前後相鄰的兩期）；**年增率**是跟「去年同一個月」比（year-over-year，抵消季節性，例如年終獎金月份）。中國大陸的面試題把這兩個叫「環比」與「同比」。成長率＝（本期 − 比較期）÷ 比較期 × 100%。

```
CREATE TABLE monthly_deposit (ym DATE PRIMARY KEY, amount INT NOT NULL);   -- ym 存每月 1 日，單位：萬元
INSERT INTO monthly_deposit VALUES
  ('2025-01-01', 500), ('2025-02-01', 480), ('2025-03-01', 520), ('2025-04-01', 510),
  ('2025-05-01', 530), ('2025-06-01', 0),   ('2025-07-01', 560), ('2025-08-01', 540),
  ('2025-09-01', 580), ('2025-10-01', 600), ('2025-11-01', 590), ('2025-12-01', 640),
  ('2026-01-01', 600), ('2026-03-01', 650), ('2026-04-01', 660), ('2026-05-01', 630),
  ('2026-06-01', 700);
```

這份資料有兩個細節：2025 年 6 月這項產品暫停，新增為 0；2026 年 2 月資料還沒進來，整列不存在。最穩的寫法是用日期找「上個月」與「去年同月」：

```
SELECT cur.ym, cur.amount,
       prev_m.amount AS last_month,
       ROUND((cur.amount - prev_m.amount) / NULLIF(prev_m.amount, 0) * 100, 1) AS mom_pct,
       prev_y.amount AS last_year,
       ROUND((cur.amount - prev_y.amount) / NULLIF(prev_y.amount, 0) * 100, 1) AS yoy_pct
FROM monthly_deposit cur
LEFT JOIN monthly_deposit prev_m ON prev_m.ym = cur.ym - INTERVAL 1 MONTH
LEFT JOIN monthly_deposit prev_y ON prev_y.ym = cur.ym - INTERVAL 1 YEAR
WHERE cur.ym >= '2026-01-01'
ORDER BY cur.ym;
+------------+--------+------------+---------+-----------+---------+
| ym         | amount | last_month | mom_pct | last_year | yoy_pct |
+------------+--------+------------+---------+-----------+---------+
| 2026-01-01 |    600 |        640 |    -6.3 |       500 |    20.0 |
| 2026-03-01 |    650 |       NULL |    NULL |       520 |    25.0 |
| 2026-04-01 |    660 |        650 |     1.5 |       510 |    29.4 |
| 2026-05-01 |    630 |        660 |    -4.5 |       530 |    18.9 |
| 2026-06-01 |    700 |        630 |    11.1 |         0 |    NULL |
+------------+--------+------------+---------+-----------+---------+
```

拿 2026 年 4 月算一次：月增率 (660 − 650) ÷ 650 ≈ 1.54%，年增率 (660 − 510) ÷ 510 ≈ 29.41%。3 月沒有上個月，月增率是 NULL，而不是拿 1 月硬比。用 LEFT JOIN 是為了缺比較期時本期照樣列出。

常見的寫錯是用 `LAG(amount, 12)` 當去年同月。LAG 數的是列，2 月缺了一列，實跑 2026 年 6 月的 `LAG(ym, 12)` 指到的是 2025-05-01，年增率就比錯月份了；`LAG(amount, 1)` 在 3 月拿到的也是 1 月。月份齊全時 LAG 可以用，但答題時要講出這個前提。

分母是 0 時（2025 年 6 月），`NULLIF(prev_y.amount, 0)` 把 0 換成 NULL，除出來就是 NULL。不加的話，SELECT 裡除以零也回傳 NULL，預設開著的 `ERROR_FOR_DIVISION_BY_ZERO` 還會多一個警告；實跑 `SELECT 700 / 0` 是 NULL 加 `Warning 1365 Division by 0`。[出處](https://dev.mysql.com/doc/refman/8.4/en/sql-mode.html) 結果一樣是 NULL，但用 NULLIF 寫明意圖，也不會在報表程式裡留下一堆警告。

**🧩 小練習：** 「月增率」是跟哪一期比？

- (A) 去年同一個月
- (B) 上一個月
- (C) 今年第一個月
- (D) 過去 12 個月的平均

<details><summary>看答案</summary>

**答案：(B)** 月增率是相鄰的前一期（month-over-month）；跟去年同月比叫年增率（year-over-year），用來抵消季節性。

</details>

**🧩 小練習：** 2026 年 4 月 660、3 月 650。月增率約多少？

- (A) 10%
- (B) 15.4%
- (C) −1.5%
- (D) 1.5%

<details><summary>看答案</summary>

**答案：(D)** (660 − 650) ÷ 650 ≈ 1.54%，實跑 ROUND 到一位是 1.5。分母是比較期（3 月），不是本期。

</details>

**🧩 小練習：** 2026 年 2 月整列不存在。用 `LAG(amount, 12) OVER (ORDER BY ym)` 當 2026 年 6 月的年增率基準，會拿到哪個月？

- (A) 2025 年 6 月
- (B) NULL
- (C) 2025 年 5 月
- (D) 2025 年 7 月

<details><summary>看答案</summary>

**答案：(C)** LAG 往前數 12 列，少了 2 月那一列，就多數到 2025 年 5 月，實跑 lag12_month = 2025-05-01。用日期自我連接（ym − INTERVAL 1 YEAR）才不會錯。

</details>

**🧩 小練習：** 去年同月是 0，`(本期 − 0) / NULLIF(0, 0)` 的結果是？

- (A) NULL
- (B) 0
- (C) 無限大
- (D) 報錯，查詢中止

<details><summary>看答案</summary>

**答案：(A)** NULLIF 把 0 換成 NULL，除以 NULL 就是 NULL。不加 NULLIF 時，SELECT 裡除以零一樣回 NULL，但會多一個 1365 警告。

</details>

*【第八題】*

## 列轉欄：CASE WHEN 加聚合（LeetCode 1179）

> 💡 面試官：手續費收入表一列是「分行、季、金額」，改成一個分行一列、四季各一欄。

台灣的「列」是橫的一筆（row）、「欄」是直的一欄（column），這題就是把「每季一列」轉成「每季一欄」。中國大陸的資料把橫的叫「行」、直的叫「列」，剛好跟台灣相反，所以他們的「行轉列」就是這裡的「列轉欄」。

```
CREATE TABLE branch_fee (branch VARCHAR(10) NOT NULL, quarter CHAR(2) NOT NULL, fee INT NOT NULL,
                         PRIMARY KEY (branch, quarter));
INSERT INTO branch_fee VALUES
  ('台北', 'Q1', 120), ('台北', 'Q2', 135), ('台北', 'Q3', 150), ('台北', 'Q4', 160),
  ('新竹', 'Q1', 80),  ('新竹', 'Q3', 95),
  ('高雄', 'Q2', 70),  ('高雄', 'Q4', 88);

SELECT branch,
       SUM(CASE WHEN quarter = 'Q1' THEN fee END) AS q1,
       SUM(CASE WHEN quarter = 'Q2' THEN fee END) AS q2,
       SUM(CASE WHEN quarter = 'Q3' THEN fee END) AS q3,
       SUM(CASE WHEN quarter = 'Q4' THEN fee END) AS q4,
       SUM(fee) AS total
FROM branch_fee
GROUP BY branch
ORDER BY total DESC;
+--------+------+------+------+------+-------+
| branch | q1   | q2   | q3   | q4   | total |
+--------+------+------+------+------+-------+
| 台北   |  120 |  135 |  150 |  160 |   565 |
| 新竹   |   80 | NULL |   95 | NULL |   175 |
| 高雄   | NULL |   70 | NULL |   88 |   158 |
+--------+------+------+------+------+-------+
```

原理：每一列先用 CASE 決定它屬於哪一欄，不屬於的那幾欄是 NULL（沒有條件成立、又沒有 ELSE 時，CASE 的結果就是 NULL）[出處](https://dev.mysql.com/doc/refman/8.4/en/flow-control-functions.html)；再 GROUP BY 分行，用 SUM 把同一欄的值收成一個，NULL 不算。兩種寫錯：

*   **有 GROUP BY 卻沒有聚合**：`CASE WHEN quarter = 'Q1' THEN fee END` 直接放在 SELECT，實跑 ERROR 1055（quarter 不在 GROUP BY、也沒有聚合），規則見〈SQL 進階：JOIN、子查詢、GROUP BY 與視窗函式〉GROUP BY 那段。
*   **沒有 GROUP BY**：每一列各自一列，台北實跑 4 列、每列只有一格有值，沒有「轉」成功。

還有一個細節：寫 `ELSE 0` 時，新竹的 Q2 會顯示 0 而不是 NULL，要看題目是要「0」還是「沒有資料」。數筆數時更危險：`COUNT(CASE WHEN quarter = 'Q2' THEN fee ELSE 0 END)` 實跑台北是 4、新竹是 2，因為 0 也是一個值，COUNT 照數；不寫 ELSE 才是正確的 1 和 0。

**🧩 小練習：** 新竹沒有 Q2 的資料，`SUM(CASE WHEN quarter = 'Q2' THEN fee END)` 回傳什麼？

- (A) 0
- (B) NULL
- (C) 報錯
- (D) 新竹整列不出現

<details><summary>看答案</summary>

**答案：(B)** 沒有 ELSE 時不符合的列是 NULL，SUM 全是 NULL 的一組結果是 NULL。要顯示 0 就寫 ELSE 0 或外面包 COALESCE。

</details>

**🧩 小練習：** `COUNT(CASE WHEN quarter = 'Q2' THEN fee ELSE 0 END)` 在台北（四季都有）的結果是？

- (A) 1
- (B) 0
- (C) 135
- (D) 4

<details><summary>看答案</summary>

**答案：(D)** ELSE 0 讓每一列都有值，COUNT 數的是「非 NULL 的值有幾個」，四列都算。數筆數時不要寫 ELSE 0。

</details>

**🧩 小練習：** 列轉欄寫成 `SELECT branch, CASE WHEN quarter = 'Q1' THEN fee END AS q1 … GROUP BY branch`（沒有 SUM），在預設設定下會怎樣？

- (A) ERROR 1055，quarter 沒聚合
- (B) 每個分行回一列，值是第一筆
- (C) 每個分行回一列，值全是 NULL
- (D) 每一筆資料各自一列

<details><summary>看答案</summary>

**答案：(A)** 預設的 ONLY_FULL_GROUP_BY 擋下沒聚合的欄位，實跑 ERROR 1055。CASE 外面要包聚合函式。

</details>

*【第九題】*

## 兩個集合的差：EXCEPT、NOT EXISTS、LEFT JOIN

> 💡 面試官：找出八月有交易、九月沒有交易的帳戶。

這題跟〈SQL 進階：JOIN、子查詢、GROUP BY 與視窗函式〉的「從沒當過轉帳對象」同一類（差集），NOT IN 遇到 NULL 為什麼一列都不回也見那課。MySQL 8.4 可以直接寫 EXCEPT。交易表：

```
CREATE TABLE txn (
  tx_id      INT PRIMARY KEY,
  account_id INT NOT NULL,
  tx_time    DATETIME NOT NULL,
  amount     INT NOT NULL,
  ref_acct   INT NULL          -- 轉帳對方帳號；存提款是 NULL
);
INSERT INTO txn VALUES
  (1, 201, '2026-08-28 10:00',  3000, NULL), (2, 202, '2026-08-30 09:00',  5000, NULL),
  (3, 203, '2026-08-31 15:00',  2000, NULL), (4, 201, '2026-09-01 09:30', -1000, 202),
  (5, 202, '2026-09-01 09:30',  1000, 201),  (6, 201, '2026-09-03 12:00',  -500, NULL),
  (7, 202, '2026-09-03 18:00', -2000, NULL), (8, 204, '2026-09-04 11:00',  4000, NULL),
  (9, 202, '2026-09-04 11:00',   300, NULL), (10, 202, '2026-09-04 11:00', -100, NULL);
```

```
SELECT account_id FROM txn WHERE tx_time >= '2026-08-01' AND tx_time < '2026-09-01'
EXCEPT
SELECT account_id FROM txn WHERE tx_time >= '2026-09-01' AND tx_time < '2026-10-01';
+------------+
| account_id |
+------------+
|        203 |
+------------+
```

*   EXCEPT 只留下第一個查詢裡、在第二個查詢找不到的那些列。[出處](https://dev.mysql.com/doc/refman/8.4/en/except.html)
*   沒寫 ALL 時結果會去重：集合運算預設移除重複的列，寫 ALL 才保留。[出處](https://dev.mysql.com/doc/refman/8.4/en/set-operations.html) 實跑 a 表 (1)、(1)、(2) EXCEPT b 表 (2)，得到一列 1；改 EXCEPT ALL 是兩列 1。

NOT EXISTS 與 LEFT JOIN … IS NULL 的版本實跑結果相同（都要加 DISTINCT，因為同一帳戶八月可能有好幾筆），可以在任何資料庫跑，面試寫這兩種最保險。

效能方面，MySQL 會把 NOT IN 與 NOT EXISTS 子查詢改寫成反連接（antijoin），也就是只回傳找不到相符列的那些列的運算。[出處](https://dev.mysql.com/doc/refman/8.4/en/semijoins-antijoins.html) 實跑「哪些帳戶從沒當過轉帳對象」的 EXPLAIN：

```
EXPLAIN FORMAT=TREE
SELECT account_id FROM acct a WHERE NOT EXISTS (SELECT 1 FROM txn t WHERE t.ref_acct = a.account_id);

-> Nested loop antijoin  (cost=6.25 rows=50)
    -> Covering index scan on a using PRIMARY  (cost=0.75 rows=5)
    -> Single-row index lookup on <subquery2> using <auto_distinct_key> (ref_acct=a.account_id)  (cost=2.31..2.31 rows=1)
        -> Materialize with deduplication  (cost=2.25..2.25 rows=10)
            -> Filter: (t.ref_acct is not null)  (cost=1.25 rows=10)
                -> Table scan on t  (cost=1.25 rows=10)
```

（`acct` 是 201〜205 五個帳戶。）第一行就是 `Nested loop antijoin`：MySQL 自己把子查詢去重、建一個臨時的查找鍵，再逐一檢查每個帳戶「找不找得到」。同一題用 NOT IN 寫，因為 `ref_acct` 有 NULL，實跑一樣是 Empty set，原因見〈SQL 進階：JOIN、子查詢、GROUP BY 與視窗函式〉。

**追問：索引**。計畫裡的 `Table scan on t` 是因為 `ref_acct` 沒有索引，小表無所謂；交易表很大時，替 `ref_acct`（或八月九月那題的 `(account_id, tx_time)`）建索引，子查詢就能直接查找、不必整表掃。

**🧩 小練習：** 八月有交易的帳戶是 201、202、203，九月有交易的是 201、202、204。EXCEPT 的結果是？

- (A) 204
- (B) 201、202
- (C) 203
- (D) 203、204

<details><summary>看答案</summary>

**答案：(C)** EXCEPT 留下「第一組有、第二組沒有」的：只有 203。204 是九月才出現，不在第一組。

</details>

**🧩 小練習：** 八月有兩筆交易的 201，如果九月也沒交易，在 `… EXCEPT …`（沒寫 ALL）的結果裡出現幾次？

- (A) 1 次
- (B) 2 次
- (C) 0 次
- (D) 要看執行計畫而定

<details><summary>看答案</summary>

**答案：(A)** EXCEPT 預設是 DISTINCT，結果會去重。要保留重複才寫 EXCEPT ALL。

</details>

**🧩 小練習：** EXPLAIN 第一行出現 `Nested loop antijoin`，意思是？

- (A) 查詢有語法錯誤
- (B) MySQL 把 NOT EXISTS 改成了 INNER JOIN
- (C) 只回傳在子查詢裡找不到相符列的那些列
- (D) 結果一定是空的

<details><summary>看答案</summary>

**答案：(C)** antijoin 是只回傳找不到相符列的運算；NOT IN 與 NOT EXISTS 子查詢會被改寫成反連接。

</details>

**🧩 小練習：** 同一題用 `WHERE account_id NOT IN (SELECT ref_acct FROM txn)`，而 `ref_acct` 有 NULL。實跑結果是？

- (A) 203、204、205
- (B) 201、202
- (C) Empty set
- (D) 報錯

<details><summary>看答案</summary>

**答案：(C)** 清單裡有 NULL，NOT IN 對找不到的帳戶算出 NULL 而不是 TRUE，全部被濾掉；NOT EXISTS 版實跑回 203、204、205。細節見〈SQL 進階：JOIN、子查詢、GROUP BY 與視窗函式〉。

</details>

*【第十題】*

## 銀行情境：每個帳戶最新一筆交易、每日餘額

> 💡 面試官：用同一張交易表，列出每個帳戶最新的一筆交易。

注意帳戶 202 在 9/4 11:00 有兩筆（tx 9 與 tx 10），時間完全相同。先看「JOIN 每組最大時間」的寫法：

```
SELECT t.account_id, t.tx_id, t.tx_time, t.amount
FROM txn t
JOIN (SELECT account_id, MAX(tx_time) AS last_time FROM txn GROUP BY account_id) m
  ON m.account_id = t.account_id AND m.last_time = t.tx_time
ORDER BY t.account_id, t.tx_id;
+------------+-------+---------------------+--------+
| account_id | tx_id | tx_time             | amount |
+------------+-------+---------------------+--------+
|        201 |     6 | 2026-09-03 12:00:00 |   -500 |
|        202 |     9 | 2026-09-04 11:00:00 |    300 |
|        202 |    10 | 2026-09-04 11:00:00 |   -100 |
|        203 |     3 | 2026-08-31 15:00:00 |   2000 |
|        204 |     8 | 2026-09-04 11:00:00 |   4000 |
+------------+-------+---------------------+--------+
```

202 出現兩次：兩筆都等於最大時間。題目若要「剛好一筆」，就用 ROW_NUMBER 並加第二排序鍵：

```
SELECT account_id, tx_id, tx_time, amount
FROM (SELECT t.*, ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY tx_time DESC, tx_id DESC) AS rn
      FROM txn t) x
WHERE rn = 1
ORDER BY account_id;
+------------+-------+---------------------+--------+
| account_id | tx_id | tx_time             | amount |
+------------+-------+---------------------+--------+
|        201 |     6 | 2026-09-03 12:00:00 |   -500 |
|        202 |    10 | 2026-09-04 11:00:00 |   -100 |
|        203 |     3 | 2026-08-31 15:00:00 |   2000 |
|        204 |     8 | 2026-09-04 11:00:00 |   4000 |
+------------+-------+---------------------+--------+
```

「時間相同時交易編號大的算最新」是一個要講出來的假設；同一秒的兩筆，真正的先後要看系統怎麼產生編號。

**追問：索引**。建 `(account_id, tx_time, tx_id)` 複合索引後，「每個帳戶的最大時間」實跑的執行計畫是：

```
EXPLAIN FORMAT=TREE SELECT account_id, MAX(tx_time) FROM txn GROUP BY account_id;
-> Covering index skip scan for grouping on txn using idx_acct_time  (cost=1.5 rows=5)
```

這就是 Loose Index Scan：分組欄位在索引裡已經排好，MySQL 直接從索引取分組欄位，每個帳戶只要跳到它那一段的最後一筆，不必讀完每個帳戶的所有交易。[出處](https://dev.mysql.com/doc/refman/8.4/en/group-by-optimization.html) 帳戶有幾百萬、每戶交易很多時，這比整表算 ROW_NUMBER 省得多；另一種常見做法是直接在帳戶表維護一個「最後交易時間」欄位。

> 💡 面試官：列出帳戶 201、202 在 9/1 到 9/4 每天的日終餘額，沒交易的日子也要有一列。

只用交易表做累計是常見的寫錯：沒有交易的日子根本沒有列，實跑 201 只有 8/28、9/1、9/3 三列，9/2 與 9/4 不見了，8/28 也跑進來。正解是「日期序列 × 帳戶」先排好每一格，再把當天淨額接上去，用 SUM OVER 往下累計，最後加上期初餘額：

```
WITH RECURSIVE days AS (
    SELECT DATE '2026-09-01' AS d
    UNION ALL
    SELECT d + INTERVAL 1 DAY FROM days WHERE d < '2026-09-04'
),
opening AS (                                  -- 9/1 以前的餘額
    SELECT account_id, SUM(amount) AS bal FROM txn WHERE tx_time < '2026-09-01' GROUP BY account_id
),
daily AS (                                    -- 每天的淨額
    SELECT account_id, DATE(tx_time) AS d, SUM(amount) AS net
    FROM txn WHERE tx_time >= '2026-09-01' AND tx_time < '2026-09-05'
    GROUP BY account_id, DATE(tx_time)
),
accts AS (SELECT DISTINCT account_id FROM txn)
SELECT a.account_id, days.d,
       COALESCE(o.bal, 0) + SUM(COALESCE(dl.net, 0)) OVER (PARTITION BY a.account_id ORDER BY days.d) AS closing
FROM accts a
CROSS JOIN days
LEFT JOIN daily dl ON dl.account_id = a.account_id AND dl.d = days.d
LEFT JOIN opening o ON o.account_id = a.account_id
WHERE a.account_id IN (201, 202)
ORDER BY a.account_id, days.d;
+------------+------------+---------+
| account_id | d          | closing |
+------------+------------+---------+
|        201 | 2026-09-01 |    2000 |
|        201 | 2026-09-02 |    2000 |
|        201 | 2026-09-03 |    1500 |
|        201 | 2026-09-04 |    1500 |
|        202 | 2026-09-01 |    6000 |
|        202 | 2026-09-02 |    6000 |
|        202 | 2026-09-03 |    4000 |
|        202 | 2026-09-04 |    4200 |
+------------+------------+---------+
```

以 202 為例：期初 5000，9/1 轉入 1000 是 6000，9/2 沒交易照舊，9/3 提款 2000 剩 4000，9/4 兩筆 +300、−100 是 4200。遞迴 CTE 產生日期序列的寫法與停止條件見〈SQL 進階：JOIN、子查詢、GROUP BY 與視窗函式〉。

**追問：資料量大怎麼辦**。每天從頭加一年份的交易太慢。常見做法是在日終批次把每個帳戶的餘額存成一張「日終餘額表」，查詢時直接讀；要補算某段期間，也只需要從上一個日終快照往後加。

**🧩 小練習：** 帳戶 202 有兩筆同時間的最新交易。「JOIN 每組最大時間」的寫法會回傳 202 幾列？

- (A) 1
- (B) 0
- (C) 3
- (D) 2

<details><summary>看答案</summary>

**答案：(D)** 兩筆的 tx_time 都等於 MAX(tx_time)，都配得上，實跑 tx 9 與 tx 10 都出現。要剛好一筆就改用 ROW_NUMBER 加第二排序鍵。

</details>

**🧩 小練習：** `ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY tx_time DESC, tx_id DESC)` 對 202 選了哪一筆？

- (A) tx 10
- (B) tx 9
- (C) tx 7
- (D) 不一定，每次不同

<details><summary>看答案</summary>

**答案：(A)** 時間相同時再比 tx_id，由大到小，tx 10 拿到 rn = 1。有了第二排序鍵，結果就固定。

</details>

**🧩 小練習：** 建 `(account_id, tx_time, tx_id)` 索引後，`SELECT account_id, MAX(tx_time) … GROUP BY account_id` 的計畫是 `Covering index skip scan for grouping`。這代表？

- (A) 索引沒用上，還是全表掃描
- (B) 先把資料排序再分組
- (C) 每組直接跳到該段最後一筆
- (D) 每個帳戶都要讀完所有交易

<details><summary>看答案</summary>

**答案：(C)** 這是 Loose Index Scan：分組欄位在索引裡排好，每組只取需要的那筆，資料量大時省很多。

</details>

**🧩 小練習：** 只用交易表 `GROUP BY account_id, DATE(tx_time)` 再累計，為什麼算不出「每日餘額」？

- (A) SUM OVER 不能配 GROUP BY
- (B) DATE() 會讓索引完全失效
- (C) 累計一定要改用 ROWS 框架
- (D) 沒交易的日子沒有列可算

<details><summary>看答案</summary>

**答案：(D)** 實跑 201 只有 8/28、9/1、9/3 三列，9/2、9/4 不見。要先用日期序列 × 帳戶排好每一格，再接當天淨額。

</details>

**🧩 小練習：** 每日餘額查詢裡，帳戶 202 在 9/2（沒有交易）那列的值是？

- (A) 0
- (B) NULL
- (C) 5000
- (D) 6000

<details><summary>看答案</summary>

**答案：(D)** 當天淨額 COALESCE 成 0，累計沿用前一天：期初 5000 加 9/1 的 1000，是 6000。

</details>

*【刷題清單】*

## 動手練

| 題號＋題名 | 對應本課 | 難度 |
| --- | --- | --- |
| [176. Second Highest Salary](https://leetcode.com/problems/second-highest-salary/) | 第一題的 N＝2 | Medium |
| [177. Nth Highest Salary](https://leetcode.com/problems/nth-highest-salary/) | 第一題：函式、LIMIT 變數 | Medium |
| [184. Department Highest Salary](https://leetcode.com/problems/department-highest-salary/) | 第二題：每部門最高、同分都列 | Medium |
| [185. Department Top Three Salaries](https://leetcode.com/problems/department-top-three-salaries/) | 第二題：前三種薪資 | Hard |
| [180. Consecutive Numbers](https://leetcode.com/problems/consecutive-numbers/) | 第三題 | Medium |
| [197. Rising Temperature](https://leetcode.com/problems/rising-temperature/) | 第四題 | Easy |
| [196. Delete Duplicate Emails](https://leetcode.com/problems/delete-duplicate-emails/) | 第五題 | Easy |
| [1321. Restaurant Growth](https://leetcode.com/problems/restaurant-growth/) | 第六題：七日移動平均 | Medium |
| [1179. Reformat Department Table](https://leetcode.com/problems/reformat-department-table/) | 第八題：列轉欄 | Easy |
| [183. Customers Who Never Order](https://leetcode.com/problems/customers-who-never-order/) | 第九題：差集 | Easy |

### 重點整理

*   手寫題先問邊界：同分怎麼算、沒有時回空還是 NULL、「前一天」是日曆還是前一筆；寫完自己帶同分、缺號、缺日期、NULL 走一遍，再主動補索引與資料量。
*   第 N 高：LIMIT 不接受運算式，函式裡先 SET N = N - 1；要宣告 READS SQL DATA 等特性，否則 ERROR 1418；DISTINCT 不能省；純量子查詢沒有列就是 NULL。
*   每組前 N 種薪資用 DENSE_RANK，ROW_NUMBER 會砍掉同分後的人；相關子查詢要數 COUNT(DISTINCT 薪資)。
*   LAG 拿前一列、不是前一天：缺日期時會比錯，自我連接用日期 − INTERVAL 1 DAY；連續分段用「整體列號 − 分組內列號」，ROW_NUMBER 是 UNSIGNED，相減為負會報 1690。
*   刪重複：DELETE 的子查詢不能讀同一張表（1093），用多表 DELETE 自我連接或包一層衍生資料表（MySQL 先算成暫存表）；清完加唯一索引；多表 DELETE 不能 LIMIT，大表改用單表寫法加 LIMIT 重複執行，或依主鍵範圍分批。
*   移動平均用 RANGE … INTERVAL n DAY，ROWS 數的是列；年增率是跟去年同月、月增率是跟上個月，用日期自我連接找比較期，LAG(…, 12) 在缺月份時會錯；分母用 NULLIF 防 0。
*   列轉欄＝CASE WHEN 加聚合再 GROUP BY，計數不要寫 ELSE 0；差集可用 EXCEPT、NOT EXISTS、LEFT JOIN，NOT EXISTS 會被改寫成 antijoin；最新一筆要防同時間、加第二排序鍵，(account_id, tx_time, tx_id) 索引讓分組取最大值變 Loose Index Scan；每日餘額要先排日期 × 帳戶再累計。

## 隨堂測驗

**Q1. 在 MySQL 8.4 的預存函式裡要用參數 N 取第 N 高，OFFSET 該怎麼寫？**

- (A) 先 SET N = N - 1，再寫 OFFSET N
- (B) 直接寫 OFFSET N - 1
- (C) 寫 OFFSET (N - 1)，加括號就可以
- (D) OFFSET 不能用在函式裡，要改用迴圈

<details><summary>看答案</summary>

**答案：(A)** LIMIT 的參數要是整數常數，預存程式裡可以用參數或區域變數，但不接受運算式。OFFSET N - 1 實跑是 ERROR 1064。

</details>

**Q2. 每部門「前三種薪資」的人都要列出，同分都算。排名函式該用哪個？**

- (A) DENSE_RANK
- (B) ROW_NUMBER
- (C) RANK
- (D) NTILE(3)

<details><summary>看答案</summary>

**答案：(A)** DENSE_RANK 同分同名次、不跳號，篩前 3 名就是前三種薪資。ROW_NUMBER 同分硬排，會把同分後面的人擠掉；RANK 同分後會跳號，第三種薪資可能被排到第 4、5 名。

</details>

**Q3. 牌告匯率週末沒有資料。用 LAG(rate) OVER (ORDER BY rate_date) 判斷「比前一天高」，週一那列會跟哪一天比？**

- (A) 上週五
- (B) 上週日
- (C) 前一天，沒資料就是 NULL
- (D) 下一個營業日

<details><summary>看答案</summary>

**答案：(A)** LAG 拿的是前一列，不是日曆上的前一天。週一的前一列是週五；要比日曆前一天就用日期自我連接，或再檢查日期差是 1。

</details>

**Q4. 刪除重複 email 只留 id 最小的，寫 DELETE FROM t WHERE id NOT IN (SELECT MIN(id) FROM t GROUP BY email)，會怎樣？**

- (A) ERROR 1093，讀了要刪的表
- (B) 正常刪除所有重複的列
- (C) 整張表的列全部被刪掉
- (D) 只刪掉 email 是 NULL 的列

<details><summary>看答案</summary>

**答案：(A)** 不能從一張表刪除，又在子查詢裡讀同一張表。改用多表 DELETE 自我連接，或把子查詢再包一層衍生資料表：MySQL 會先把它算成暫存表，刪除時讀的不是原表。

</details>

**Q5. 每日資料中間缺了一天。要算「近 7 日」加總，框架該怎麼寫？**

- (A) RANGE，位移寫 INTERVAL 6 DAY
- (B) ROWS，位移寫成 6 PRECEDING 即可
- (C) ROWS，位移寫成 7 PRECEDING 才夠
- (D) 不寫框架，只寫 ORDER BY d 就好

<details><summary>看答案</summary>

**答案：(A)** ROWS 數的是列，缺一天時 7 列會橫跨 8 個日曆天；RANGE 看的是日期值的範圍，位移可以寫成 INTERVAL。不寫框架、只有 ORDER BY 時是從頭累計，不是近 7 日。

</details>

**Q6. 「年增率」指的是跟哪一期比較？**

- (A) 去年同一期
- (B) 上一期
- (C) 本年第一期
- (D) 過去所有期的平均

<details><summary>看答案</summary>

**答案：(A)** 年增率是跟去年同期比（year-over-year），用來抵消季節性；跟上一期比叫月增率（month-over-month）。

</details>

**Q7. 月份資料缺了一個月。用 LAG(amount, 12) OVER (ORDER BY ym) 當去年同月，結果會怎樣？**

- (A) 往前數 12 列，會拿到錯的月份
- (B) 一樣正確，LAG 會自動跳過缺的月份
- (C) 回傳 NULL
- (D) 報錯，LAG 的位移不能超過 10

<details><summary>看答案</summary>

**答案：(A)** LAG 數的是列，少一列就多數一個月。用日期自我連接（ym − INTERVAL 1 YEAR）才保證是去年同月。

</details>

**Q8. 列轉欄時，要數每個分行 Q2 有幾筆，哪個寫法對？**

- (A) COUNT(CASE WHEN quarter = 'Q2' THEN 1 END)
- (B) COUNT(CASE WHEN quarter = 'Q2' THEN 1 ELSE 0 END)
- (C) SUM(CASE WHEN quarter = 'Q2' THEN fee END)
- (D) MAX(CASE WHEN quarter = 'Q2' THEN 1 ELSE 0 END)

<details><summary>看答案</summary>

**答案：(A)** 不寫 ELSE 時不符合的列是 NULL，COUNT 不數 NULL。寫 ELSE 0 時每列都有值，COUNT 會把全部列都數進去；SUM fee 算的是金額；MAX 只能看有沒有。

</details>

**Q9. 「八月有交易、九月沒有」的帳戶，用 EXCEPT 寫。八月有三筆交易的帳戶在結果裡出現幾次？**

- (A) 1 次
- (B) 3 次
- (C) 0 次
- (D) 看九月有幾筆

<details><summary>看答案</summary>

**答案：(A)** 集合運算預設會移除重複的列，要保留才寫 EXCEPT ALL。

</details>

**Q10. 同一帳戶有兩筆時間相同的最新交易，題目要求剛好回一筆，哪個做法最可靠？**

- (A) ROW_NUMBER 依時間與編號排，取第 1
- (B) JOIN 每個帳戶的 MAX(tx_time) 比對
- (C) WHERE tx_time 等於子查詢的最大時間
- (D) GROUP BY account_id 後直接選 tx_id

<details><summary>看答案</summary>

**答案：(A)** 比對最大時間的兩種寫法，兩筆都等於最大值就都留下；GROUP BY 後直接選 tx_id 會被 ONLY_FULL_GROUP_BY 擋下。ROW_NUMBER 加第二排序鍵才保證每帳戶一筆。

</details>
