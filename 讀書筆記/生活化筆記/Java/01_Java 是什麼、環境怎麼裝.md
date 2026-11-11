# 01. Java 是什麼、環境怎麼裝

> 🏠 **生活化版本**：每個段落開頭的「生活比喻」先用日常情境帶你抓到感覺，接著再看原本的技術說明與程式碼；篇末有「比喻對照表」可以快速複習。

> 來源：[筆記平台 · Java](https://hhtim.github.io/notes-platform/java/#/lesson/java-env)　第 1 課 / 共 18 課 · 約 11 分鐘

**分清 JVM、JRE、JDK 三個縮寫，看懂原始碼怎麼變成可執行的位元碼，並跑出第一支程式。**

### 讀完這課你會

- 講清楚 Java 程式怎麼從原始碼變成跑得動的東西，以及誰負責哪一段
- 分辨 JVM、JRE、JDK 這三個長很像的縮寫
- 自己裝好 JDK、確認環境變數，並編譯執行第一支程式
- 知道現在該裝哪個版本，以及幾個版本分水嶺

---

*【先建立全貌】*

## Java 是什麼

> 🏠 **生活比喻**
>
> Java 像**一種通用語言**，寫一次就能在 Windows、Mac、Linux 上執行，因為每台電腦都裝了**同一款翻譯機**（JVM）。

Java 是一種高階、物件導向、強型別的程式語言。它刻意不讓你直接去碰記憶體位址，不再使用的物件也交給垃圾回收器（garbage collector，自動把沒人用的記憶體收回去的機制）處理，所以比起要自己管記憶體的語言好入門得多。

它最有名的特色是跨平台：原始碼先編譯成跟作業系統無關的位元碼（bytecode），再交給各平台自己的 Java 虛擬機（JVM）執行。像是先把稿件翻成一份共通格式，再由各地的口譯員轉成當地語言。

Java 由昇陽電腦（Sun Microsystems）在 1995 年推出，早期叫 Oak；2009 年 4 月 20 日 Oracle 發的是「雙方簽訂收購協議」的公告，實際完成合併要到 2010 年 1 月 27 日 [[出處]](https://www.oracle.com/us/corporate/press/018363) [[出處]](https://www.sec.gov/Archives/edgar/data/1341439/000119312510015241/dex991.htm)。它主要用在伺服器端系統、企業應用、開發工具，以及各種要跨平台的軟體。初學語法通常從 Java SE（標準版）開始，企業端那一套後來改名叫 Jakarta EE。

---

*【程式怎麼跑起來】*

## 從 .java 到 .class

> 🏠 **生活比喻**
>
> - `.java`＝**你寫的中文食譜**
> - `javac` 編譯＝**翻譯成國際通用的圖示食譜**（`.class` 位元組碼）
> - JVM＝**各國廚房裡看得懂圖示食譜的廚師**，照著做出菜

你寫的檔案叫原始碼（source code），副檔名是 `.java`。編譯器 `javac` 會檢查語法、產生含有位元碼的 `.class` 檔；接著 JVM 把這個 `.class` 載進來執行。

```text
HelloWorld.java
      │ javac HelloWorld.java   ← 編譯
      ▼
HelloWorld.class
      │ java HelloWorld         ← 執行
      ▼
JVM 載入位元碼，在目前這台機器上跑
```

**負責編譯的是 `javac`，負責執行的是 JVM——不是「JVM 編譯、JRE 執行」，也不能說 JVM 是編譯器** [[出處]](https://docs.oracle.com/en/java/javase/21/docs/specs/man/javac.html)。JRE 是「JVM＋標準函式庫」這一整包執行環境，它本身不做編譯。

> 📝 原筆記更正：原筆記一處寫「JVM編譯，JRE執行」，另一處（Node.js & Java 比較）寫「JVM 是 Java 的編譯器」，兩句都把角色弄反了，查證後更正

「一次編譯，到處執行」不是說平台差異全部消失，而是同一份相容的位元碼，可以交給 Windows、macOS、Linux 上各自適用的 JVM 去跑。

---

*【三個縮寫一次分清楚】*

## JVM、JRE 與 JDK

> 🏠 **生活比喻**
>
> - JVM＝**引擎**
> - JRE＝**引擎＋整台車**，能開（執行程式）
> - JDK＝**整台車＋修車工具箱**，能開也能造（開發程式）

| 縮寫 | 全名 | 它負責什麼 |
|---|---|---|
| **JVM** | Java Virtual Machine<br>Java 虛擬機 | 載入並執行位元碼 |
| **JRE** | Java Runtime Environment<br>Java 執行環境 | JVM＋執行程式需要的標準函式庫 |
| **JDK** | Java Development Kit<br>Java 開發工具組 | 開發與執行都有：`javac`、`java`、`javadoc` 等 |

> 💡 **JVM 是引擎，JRE 是能把車開上路的整套設備，JDK 再加上製造與維修的工具**

要寫程式，直接裝 JDK 最省事。Java 9 把執行環境改成模組化映像檔之後，JDK 內就沒有獨立的 `jre` 目錄了；到 JDK 11，Oracle 連獨立的 JRE 安裝檔也不再提供 [[出處]](https://openjdk.org/jeps/220) [[出處]](https://www.oracle.com/java/technologies/javase/11-relnote-issues.html#Important_Changes)。概念上 JRE 還在（就是 JDK 裡那份執行環境），但你不會再看到那個資料夾。

> 對照 JavaScript：Node.js 讓 JavaScript 能在瀏覽器以外執行，JVM 讓位元碼能在各平台執行。兩者涵蓋範圍不一樣：Node.js 是一套執行環境，JDK 除了執行還包含編譯器與各種開發工具。

---

*【準備工具】*

## 裝 JDK、設環境變數

> 🏠 **生活比喻**
>
> 設 `JAVA_HOME` 和 `PATH` 像**告訴家人「工具箱放在哪個櫃子」**，之後不管在哪個房間喊「拿 java 來」，大家都找得到。

依你的作業系統與處理器架構下載對應的 JDK 裝好，然後在終端機（Windows 是命令提示字元）打：

```text
java -version
javac -version
```

兩個指令都印得出版本，表示指令搜尋路徑大致設對了。`java` 是啟動程式的工具，`javac` 是編譯器。

- **PATH**：作業系統的地址簿，讓你在任何資料夾都叫得到 `java` 與 `javac`。
- **JAVA_HOME**：指向 JDK 的安裝目錄，讓建置工具（Maven、Gradle）和其他程式找得到 JDK。
- **CLASSPATH**：告訴編譯器與 JVM 去哪些根目錄或 jar 檔找類別。現在多半交給建置工具處理，很少手動設。

```text
JAVA_HOME = JDK 安裝目錄
PATH 加入 %JAVA_HOME%\bin（Windows）或 $JAVA_HOME/bin（macOS、Linux）
```

> 路徑寫起來像 `JAVA_HOME C:\jdk-17.0.6` 這樣。實際畫面與路徑會隨作業系統和你挑的 JDK 發行版而不同。

---

*【現在該裝哪一版】*

## 版本界線：長期支援版與幾個分水嶺

> 🏠 **生活比喻**
>
> LTS 長期支援版像**手機的長期保固型號**（8、11、17、21、25），公司多半選這些；中間的版本像**試用新功能的短期版**，很快就不維護。

Java 每半年出一版，但只有少數版本是長期支援版（LTS，Long-Term Support，官方保證長期修補的版本）。到 2026 年，手上在用的長期支援版是 Java 21（2023 年 9 月）與 Java 25（2025 年 9 月）；新專案通常直接從這兩個挑 [[出處]](https://www.oracle.com/java/technologies/java-se-support-roadmap.html)。

幾個分水嶺：

- **Java 8**：介面可以有帶實作的方法（default、static），Lambda 與 Stream 進來。
- **Java 9**：模組化，`rt.jar` 與獨立的 jre 目錄消失。
- **Java 10**：區域變數可以寫 `var`。
- **Java 14〜17**：switch 可以當運算式用、文字區塊、record、sealed 類別。
- **Java 21**：虛擬執行緒、switch 的模式比對正式定案。

---

*【第一支程式】*

## 編譯與執行 Hello World

> 🏠 **生活比喻**
>
> `javac` 是**翻譯**，`java` 是**照翻譯好的食譜開火**；檔名要跟 public 類別同名，就像**食譜的檔名要跟菜名一樣**。

```java
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello World!");
    }
}
```

存成 `HelloWorld.java`。`javac` 只對公開類別（`public class`）強制檔名要跟類別名稱完全一致，大小寫也要一樣。語言規格把這條寫成「執行環境可以選擇強制」，而且允許強制的對象有兩種——宣告成 `public` 的類別，以及被同套件其他原始檔引用到的非公開類別；`javac` 實際只對前者強制，後者換個檔名照樣編得過。至於「類別名稱大寫開頭」是命名慣例，不是編譯器會擋的規定 [[出處]](https://docs.oracle.com/javase/specs/jls/se21/html/jls-7.html#jls-7.6)。

```text
javac HelloWorld.java
java HelloWorld
```

第一行產生 `HelloWorld.class`；第二行傳的是**類別名稱**，不要加 `.class`。成功就會印出 `Hello World!`。

那一行宣告裡的四個字各有職責：

- **public**：讓啟動器存取得到這個方法。
- **static**：不必先建立物件就能呼叫。**把類別載進來的是 JVM 的類別載入機制，不是作業系統** [[出處]](https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-5.html)。 > 📝 原筆記更正：原筆記寫「static:表示此方法是靜態方法 static function，可以讓OS載入時就被儲存在記憶體中」，查證後更正：載入類別的是 JVM 的類別載入機制，不是作業系統
- **void**：這個方法不回傳資料。
- **String[] args**：接收命令列引數的字串陣列。

> **JVM 去找 `main()` 方法來執行，是 `java` 啟動器這一端的事；`javac` 只出現在編譯階段，兩者不要混在一起講** [[出處]](https://docs.oracle.com/en/java/javase/21/docs/specs/man/java.html)。
>
> 📝 原筆記更正：原筆記寫「這樣Java虛擬機可以找到main()方法，來運行javac程序」，把執行與編譯混在一起了，查證後更正

---

*【開發工具】*

## IDE 與 Eclipse

> 🏠 **生活比喻**
>
> IDE 像**有自動校正、提示、一鍵執行的高級文書軟體**；用記事本寫程式就像用紙筆寫論文，可以，但很累。

整合開發環境（IDE，Integrated Development Environment）把編輯、編譯、執行、除錯與程式碼提示集中在同一套工具裡。Java 界常見的是 Eclipse、IntelliJ IDEA 與 Visual Studio Code。

> Eclipse 專案是 IBM 在 2001 年 11 月建立並釋出、由一群廠商組成聯盟支持；獨立的 Eclipse 基金會要到 2004 年 1 月才成立 [[出處]](https://www.eclipse.org/org/foundation/)。

Eclipse 的設計特色是「什麼都是外掛」，核心之外的功能都用外掛加上去，所以擴充性強。但用 IDE 並沒有改變 Java 的流程——它只是代替你去呼叫編譯器與執行工具，再把結果畫得好看一點。

### 🗺️ 比喻對照表

| 技術名詞 | 生活比喻 |
| --- | --- |
| 編譯 / 位元組碼 | 翻成國際通用圖示食譜 |
| JVM / JRE / JDK | 引擎 / 整台車 / 車＋修車工具 |
| JAVA_HOME | 工具箱放哪個櫃子 |
| LTS | 長期保固型號 |
| IDE | 高級文書軟體 |

### 重點整理

- `.java` 是原始碼，`javac` 把它編成含位元碼的 `.class`，JVM 負責執行——編譯跟執行是兩個人的事。
- JVM 執行、JRE 是執行環境、JDK 是開發工具組；要寫程式就裝 JDK。
- 跨平台靠的是各平台自己的 JVM，不代表所有系統細節都一樣。
- 只有 public 類別強制跟檔名同名；大寫開頭是慣例不是規定。
- Java 9 之後 JDK 裡沒有獨立的 jre 目錄了。
- 現在挑版本從長期支援版下手：Java 21 或 Java 25。

---

## 隨堂測驗

**Q1. Java 原始碼經過 javac 成功編譯後，產生的是什麼？**

- (A) 含有位元碼的 .class 檔
- (B) 給瀏覽器讀的 .html 檔
- (C) 可以直接雙擊執行的 .exe 檔
- (D) 另一份 .java 原始碼

<details><summary>看答案</summary>

**答案：(A)** javac 把 .java 編成 .class，裡面裝的是跟作業系統無關的位元碼。

</details>

**Q2. 同一份位元碼能在 Windows、macOS、Linux 上執行，靠的是什麼？**

- (A) IDE 的外掛系統
- (B) 所有平台共用同一份機器碼
- (C) 各平台自己那一套 JVM
- (D) JAVA_HOME 這個環境變數

<details><summary>看答案</summary>

**答案：(C)** 位元碼只有一份，各平台裝自己的 JVM 把它翻成當地的機器指令。

</details>

**Q3. 「JVM 編譯、JRE 執行」這句話錯在哪？**

- (A) 反了：編譯的是 javac，執行的是 JVM
- (B) 沒錯，這是標準說法
- (C) JRE 只能處理未編譯的 .java
- (D) JVM 只負責下載函式庫

<details><summary>看答案</summary>

**答案：(A)** javac 是編譯器；JVM 載入並執行位元碼，JRE 則是包住 JVM 的執行環境。

</details>

**Q4. 要自己寫 Java 程式並編譯，最直接該裝哪一項？**

- (A) 只裝一個 IDE 外掛
- (B) 只裝 JVM
- (C) JDK
- (D) 只裝標準函式庫

<details><summary>看答案</summary>

**答案：(C)** JDK 裡有 javac 等開發工具，也包含執行 Java 程式所需的一切。

</details>

**Q5. 關於 Java 9 之後的 JDK 目錄結構，下列哪項正確？**

- (A) JDK 從此不含執行環境
- (B) jre 目錄改名成 jvm 目錄
- (C) JDK 內不再有獨立的 jre 子目錄
- (D) JDK 內多了兩個 jre 子目錄

<details><summary>看答案</summary>

**答案：(C)** Java 9 把執行環境改成模組化映像檔，獨立的 jre 目錄消失，但執行環境本身還在 JDK 裡。

</details>

**Q6. 某個原始檔寫了 public class HelloWorld，檔名應該是什麼？**

- (A) HelloWorld.class
- (B) HelloWorld.java
- (C) Main.java
- (D) helloworld.java

<details><summary>看答案</summary>

**答案：(B)** 公開類別的名稱要跟檔名完全一致，大小寫也算，再加上 .java。

</details>

**Q7. 已經編譯出 HelloWorld.class 了，要執行它該打哪個指令？**

- (A) javac HelloWorld
- (B) java HelloWorld.class
- (C) javac HelloWorld.class
- (D) java HelloWorld

<details><summary>看答案</summary>

**答案：(D)** java 指令接的是類別名稱，不加副檔名；javac 是編譯用的。

</details>

**Q8. PATH 這個環境變數在 Java 開發裡解決什麼問題？**

- (A) 指定 main 方法要收幾個參數
- (B) 決定物件存放在哪塊記憶體
- (C) 讓作業系統在任何目錄都找得到 java 與 javac
- (D) 決定類別的繼承順序

<details><summary>看答案</summary>

**答案：(C)** PATH 是作業系統搜尋可執行程式的路徑清單，跟 Java 的語言規則無關。

</details>
