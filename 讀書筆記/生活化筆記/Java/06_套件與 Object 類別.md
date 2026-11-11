# 06. 套件與 Object 類別

> 🏠 **生活化版本**：每個段落開頭的「生活比喻」先用日常情境帶你抓到感覺，接著再看原本的技術說明與程式碼；篇末有「比喻對照表」可以快速複習。

> 來源：[筆記平台 · Java](https://hhtim.github.io/notes-platform/java/#/lesson/packages-object)　第 6 課 / 共 18 課 · 約 12 分鐘

**用套件整理類別、正確匯入名稱，並掌握 equals、hashCode、toString 與包裝類別。**

### 讀完這課你會

- 用套件替類別分組、處理同名類別撞在一起的狀況
- 看懂 `import` 到底做了什麼（以及沒做什麼）
- 正確覆寫 `equals()`、`hashCode()` 與 `toString()`，並記得它們的約定
- 使用包裝類別、裝箱拆箱與字串轉數字，並避開幾個經典的坑

---

*【程式碼的地址】*

## 套件替類別分組，也避免名稱撞車

> 🏠 **生活比喻**
>
> 套件像**地址的縣市區**：台北的「中山路」和台中的「中山路」不會搞混，因為前面有縣市（`com.bank.Account` vs `com.shop.Account`）。

套件（package）像類別的地址。不同團隊都可以有自己的 `Date` 或 `User`，只要住在不同套件，完整名稱就不一樣。慣例是**全小寫**，並用反過來寫的網域名稱降低撞名機會，例如 `tw.example.billing`。

一個 Java 原始檔裡的三種元素都不是必要的，但只要出現就得照這個順序：

> 💡 **`package` 宣告 → `import` 敘述 → 類別等型別宣告**

```java
package tw.example.app;

import java.time.LocalDate;
import java.util.ArrayList;

public class Main {
    public static void main(String[] args) {
        ArrayList<LocalDate> dates = new ArrayList<>();
    }
}
```

一個原始檔**最多只能有一個 public 頂層類別**，而且檔名要跟它一致；同一個檔案裡還是可以放其他非公開的類別。這樣安排的理由很實際：那些類別別的地方用不到，放在一起互相搭配還比較好讀。

> 常用的標準套件：`java.lang`（語言核心，String 就住這）、`java.io`（輸入輸出）、`java.net`（網路）、`java.util`（工具與集合）、`java.sql`（資料庫）。Java 9 模組化之後，前四個都在 `java.base` 這個預設就有的模組裡；`java.sql` 則自己是一個同名的獨立模組。

---

*【尋找類別】*

## import 省的是名稱，不是把程式載進來

> 🏠 **生活比喻**
>
> `import` 像**在通訊錄存「小明」**，之後不用每次都講全名「台北市大安區王小明」；它**不會把小明叫來你家**（不會載入程式）。

`import` 只是讓你可以寫簡短的類別名稱，不會把任何東西複製或載入到你的檔案裡。兩個地方不必匯入：`java.lang` 裡的型別，以及跟你同一個套件的型別。

```java
import java.sql.Date;

Date sqlDate = new Date(System.currentTimeMillis());
java.util.Date utilDate = new java.util.Date();   // 完整限定名稱
```

兩個套件都有 `Date` 的時候，不可能讓兩個都用簡名，至少要有一個寫成完整限定名稱（fully qualified name，連套件一起寫）。

星號只涵蓋指定的那個套件，**不會連子套件一起匯入**——`import java.util.*;` 不會匯入 `java.util.function` 裡的東西。

靜態匯入（static import，Java 5 起）可以連類別名稱都省掉：

```java
import static java.lang.Math.PI;
import static java.lang.Math.sin;

double value = sin(PI / 2);   // 不必寫 Math.sin(Math.PI / 2)
```

> 數學式用一點會清楚很多，但用太多讀的人就看不出這個成員是從哪來的。

---

*【編譯與執行】*

## 目錄位置與類別路徑要對得上套件名稱

> 🏠 **生活比喻**
>
> 套件名稱和資料夾要對得上，像**地址寫台北市，信就要真的放在台北的信箱**，不然郵差找不到。

套件名稱對應目錄階層。類別宣告在 `tw.example.app`，編譯出來的 `.class` 就會放在 `tw/example/app` 底下。執行時要用完整類別名稱：

```text
javac -d out src/tw/example/app/Main.java
java -cp out tw.example.app.Main
```

`-d` 指定編譯輸出的**根目錄**；類別路徑（classpath）則告訴編譯器與 JVM 去哪些根目錄或 jar 檔找類別。注意它指的是套件樹的**起點**，不是某個 `.class` 檔本身的路徑。

**Java 9 把執行環境改成模組化映像檔之後，`rt.jar` 與 `jre/lib/ext` 這個擴充機制整個被移除，連 `java.ext.dirs` 這個系統屬性都不能再設——設了編譯器與啟動器會直接失敗。類別載入器仍然分成啟動、平台、應用程式三層，只是前兩層由 JDK 自己管，你會設定到的只剩自己的類別路徑（以及模組路徑）** [[出處]](https://openjdk.org/jeps/220)。日常開發多半交給 Maven 或 Gradle 處理，很少手動設。

> 📝 原筆記更正：原筆記把 classpath 的搜尋分成「1. Bootstrap classes：已置於 %JAVA_HOME%\jre\lib\rt.jar 檔案」「2. Extension classes：指的是 %JAVA_HOME%\jre\lib\ext 目錄下的jar檔或zip檔」「3. Users classes」三類，查證後更正：Java 9 起擴充機制已整個移除（JEP 220），照原筆記設定 java.ext.dirs 時 JVM 會拒絕啟動

---

*【共同祖先】*

## 所有類別追到底都是 Object

> 🏠 **生活比喻**
>
> `Object` 像**所有人的共同祖先**，每個類別一定繼承它，所以大家都有 `toString`、`equals`、`hashCode` 這些祖傳技能。

沒寫父類別的類別直接繼承 `java.lang.Object`；有父類別的，也會沿著繼承鏈間接連到它。所以任何物件都用得到 `Object` 定義的那幾個方法。

| 方法 | 做什麼 |
|---|---|
| **`toString()`** | 給物件一段文字表示，方便記錄、列印與除錯 |
| **`equals(Object)`** | 由你定義「兩個物件算不算相等」 |
| **`hashCode()`** | 給一個整數，供雜湊型集合搭配 `equals` 使用 |
| **`getClass()`** | 取得物件執行時的類別資訊 |
| **`wait()`、`notify()`、`notifyAll()`** | 執行緒之間的協調 |

`equals(Object obj)` 的參數之所以是 `Object`，就是要讓任何物件都傳得進來比較。`System.out.println(物件)` 印的是 `toString()` 的結果；沒覆寫的話那串預設內容對人類沒什麼意義，所以自訂類別通常會給一個好讀的版本。

> `Object` 還有一個 `finalize()`，Java 9 起被標記為棄用（deprecated），Java 18 起更進一步標記為**準備移除**，不要靠它釋放資源 [[出處]](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Object.html#finalize()) [[出處]](https://openjdk.org/jeps/421)。要收尾請用 try-with-resources（〈例外機制〉）。

---

*【相等的定義】*

## == 看是不是同一個，equals 看內容一不一樣

> 🏠 **生活比喻**
>
> - `==`＝**是不是同一個人**（同一個物件）
> - `equals`＝**長得一不一樣**（內容相同）
>
> 雙胞胎 `equals` 是 true，但 `==` 是 false。

對參考型別而言，`==` 比的是兩個參考指不指向同一個物件；`equals()` 則可以由類別自己覆寫，定義什麼叫「內容相等」。

```java
final class Member {
    private final int id;
    private final String name;

    Member(int id, String name) {
        this.id = id;
        this.name = name;
    }

    @Override
    public boolean equals(Object obj) {
        if (this == obj) return true;
        if (!(obj instanceof Member other)) return false;   // Java 16 起的寫法
        return id == other.id && Objects.equals(name, other.name);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id, name);
    }

    @Override
    public String toString() {
        return "Member{id=" + id + ", name='" + name + "'}";
    }
}
```

**覆寫了 `equals()` 就要一起覆寫 `hashCode()`。**不然物件丟進 `HashSet`、或當 `HashMap` 的鍵時，會出現「明明放進去了卻查不到」這種怪事。

**`hashCode()` 的約定只有兩個方向：同一個物件多次呼叫 `hashCode()` 要給同樣的值；`equals()` 相等的兩個物件，`hashCode()` **必須**相同。反過來**沒有**要求——`equals()` 不相等的物件，雜湊碼完全可以一樣，那叫雜湊碰撞（hash collision），是正常現象** [[出處]](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Object.html#hashCode())。

> 📝 原筆記更正：原筆記（集合的大集合）列的四條裡，第 3 條寫「若兩物件的equals()不相等，則hashCode()回傳的值必不相等」，這一條錯了，而且跟同一份筆記第 4 條「若兩物件的hashCode()回傳的值相等，但equals()回傳的值不一定相等」自相矛盾，查證後更正

> 💡 **先用 `hashCode()` 粗篩位置，再用 `equals()` 精確確認——像先看郵遞區號，再核對完整地址**

**`hashCode()` 是先產生一個整數，`HashMap` 這類雜湊表再**拿它去用**，不是雜湊表算出 hashCode。官方文件只規定「同一個物件每次要回傳同樣的值」，至於那個值怎麼算出來（是不是由記憶體位址來的）並沒有規定** [[出處]](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Object.html#hashCode())。這也是為什麼不覆寫就直接丟進 `HashSet`，兩個內容相同的物件會被當成兩筆。

> 📝 原筆記更正：原筆記寫「一個物件一定有記憶體位址，當呼叫hashCode()方法後，會將該記憶體位址輸入到Hash Table中，接著產生出一組hashCode」，查證後更正：因果反了——hashCode() 是先產生出一個整數，HashMap 這類雜湊表再拿它去用，不是雜湊表算出 hashCode。至於它是不是由記憶體位址算來的，規格並沒有規定

---

*【基本型別的物件外衣】*

## 包裝類別、裝箱與拆箱

> 🏠 **生活比喻**
>
> 包裝類別像**把散裝的數字裝進禮盒**（`int` → `Integer`），才能放進只收禮盒的集合；自動裝箱拆箱就是**系統自動幫你包裝和拆封**。
> 小心空禮盒（`null`）拆封會出錯。

- **整數**：`byte→Byte`、`short→Short`、`int→Integer`、`long→Long`
- **浮點數**：`float→Float`、`double→Double`
- **其他**：`char→Character`、`boolean→Boolean`

把基本型別包成物件叫**裝箱**（boxing），反過來取出值叫**拆箱**（unboxing）。為什麼要裝箱？因為集合、泛型這些地方只收參考型別。Java 5 起編譯器會自動幫你裝拆，所以平常寫起來沒什麼感覺。

```text
Integer boxed = 10;   // 自動裝箱
int number = boxed;   // 自動拆箱

int parsed = Integer.parseInt("42");      // 回傳 int
Integer wrapped = Integer.valueOf("42");  // 回傳 Integer
```

> 💡 **`parseXxx()` 給你基本型別，`valueOf()` 給你包裝物件**

建立包裝物件請寫 `Integer.valueOf()`，Java 9 起就是這樣建議的；Java 16 起更進一步，包裝類別的建構子已經標記為**準備移除**。在 Java 21、25 還是編得過，只是會跳警告——但既然已經預告要拿掉，新程式就別再寫 `new Integer(...)` 了 [[出處]](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Integer.html#%3Cinit%3E(int)) [[出處]](https://www.oracle.com/java/technologies/javase/16-relnote-issues.html#JDK-8249100)。`valueOf()` 省的不只是一次配置——小範圍的整數它會重複使用快取好的物件。

兩個常見的坑：

- **比包裝物件的值要用 `equals()`**。因為有快取，`==` 在小數字時看起來會相等、換成大數字又不相等，很容易誤判。
- **自動拆箱一個 `null` 會丟 `NullPointerException`**。`Integer` 可以是 `null`，`int` 不行。

### 🗺️ 比喻對照表

| 技術名詞 | 生活比喻 |
| --- | --- |
| package | 地址的縣市區 |
| import | 通訊錄存簡稱 |
| Object | 所有人的共同祖先 |
| == / equals | 同一個人 / 長得一樣 |
| 裝箱拆箱 | 散裝裝進禮盒 / 拆封 |

### 重點整理

- 套件是類別的命名空間，也對應目錄階層；套件名稱全小寫、用反向網域。
- `import` 只是讓名稱可以寫短；星號不包含子套件。
- classpath 指的是套件樹或 jar 的搜尋**起點**；Java 9 之後 `rt.jar` 與 ext 機制已經沒了。
- `==` 比是不是同一個物件，覆寫過的 `equals()` 才比內容。
- 覆寫 `equals()` 就要一起覆寫 `hashCode()`；但雜湊碼相同**不**代表物件相等。
- `parseInt()` 給 int、`valueOf()` 給 Integer；比包裝物件的值用 `equals()`，小心拆箱 `null`。

---

## 隨堂測驗

**Q1. 原始檔同時有 package、import 與類別宣告時，正確順序是什麼？**

- (A) import、package、類別宣告
- (B) package、import、類別宣告
- (C) package、類別宣告、import
- (D) 類別宣告、package、import

<details><summary>看答案</summary>

**答案：(B)** 三者都不是必要的，但只要出現就得照這個順序，否則編譯不過。

</details>

**Q2. import java.util.*; 會產生什麼效果？**

- (A) 連 java.util 底下所有子套件一起匯入
- (B) 可以簡寫 java.util 裡的型別名稱，但不含子套件
- (C) 把 java.util 的原始碼複製進目前的檔案
- (D) 讓 java.util 裡的方法全部變成靜態方法

<details><summary>看答案</summary>

**答案：(B)** 星號只涵蓋指定的那個套件，java.util.function 之類的子套件要另外匯入。

</details>

**Q3. classpath 指的是什麼？**

- (A) 尋找類別時的套件樹根目錄或 jar 檔位置
- (B) 某個 .class 檔本身的完整路徑
- (C) main 方法所在的行號
- (D) JDK 的安裝目錄

<details><summary>看答案</summary>

**答案：(A)** classpath 給的是搜尋起點，不是單一檔案路徑；Java 9 之後 rt.jar 與 ext 那兩層機制已經拿掉了。

</details>

**Q4. 為什麼覆寫 equals() 時通常也要覆寫 hashCode()？**

- (A) 讓相等的物件產生相同雜湊值，雜湊型集合才找得到
- (B) 讓 toString() 自動顯示所有 private 欄位
- (C) 讓物件可以繞過建構子直接建立
- (D) 確保物件一定配置在同一塊記憶體

<details><summary>看答案</summary>

**答案：(A)** HashSet 與 HashMap 先用 hashCode 粗篩位置、再用 equals 確認，兩者不一致就會出現放得進去卻查不到的狀況。

</details>

**Q5. 兩個物件的 equals() 判定為不相等，它們的 hashCode() 一定不一樣嗎？**

- (A) 不一定，雜湊碼相同是允許的，這叫雜湊碰撞
- (B) 一定一樣，雜湊碼只看類別
- (C) 一定不一樣，這是規格要求
- (D) 規格沒有任何規定

<details><summary>看答案</summary>

**答案：(A)** hashCode 的約定只要求 equals 相等時 hashCode 必須相同，反方向沒有要求，碰撞是正常現象。

</details>

**Q6. Integer.parseInt("42") 的結果型別是什麼？**

- (A) int
- (B) Integer
- (C) String
- (D) long

<details><summary>看答案</summary>

**答案：(A)** parseXxx 回傳基本型別，valueOf 才回傳包裝物件。

</details>

**Q7. 要比較兩個 Integer 物件的數值內容，哪種做法比較妥當？**

- (A) 用 equals()，並留意可能是 null
- (B) 用 notify() 比較
- (C) 先呼叫 toString() 再比較位址
- (D) 一律用 ==，所有 Integer 都是同一個物件

<details><summary>看答案</summary>

**答案：(A)** 包裝類別有小範圍快取，== 在小數字看起來相等、大數字又不相等；另外自動拆箱 null 會丟 NullPointerException。

</details>

**Q8. Object.finalize() 現在的狀態是什麼？**

- (A) Java 21 起變成必須實作的方法
- (B) Java 9 標記棄用，Java 18 起進一步標記為準備移除
- (C) 仍是釋放資源的建議做法
- (D) 從來沒有存在過

<details><summary>看答案</summary>

**答案：(B)** 不要靠 finalize 釋放資源；要收尾請用 try-with-resources。

</details>
