# 02. Java 進階快答：JVM 記憶體、垃圾回收與類別載入

> 🏠 **生活化版本**：每個段落開頭的「生活比喻」先用日常情境帶你抓到感覺，接著再看原本的技術說明與程式碼；篇末有「比喻對照表」可以快速複習。

> 來源：[筆記平台 · 面試集](https://hhtim.github.io/notes-platform/interview/#/lesson/jvm-memory-gc)　第 2 課 / 共 23 課 · 約 21 分鐘

**五塊執行期資料區、分代與晉升、Metaspace、可達性、五個回收器怎麼選、OOM 種類與 heap dump、類別載入三步與父委派、JIT 暖機——連 Java 21 與 25 的差別一起答。**

### 讀完這課你會

*   答出 JVM 記憶體分哪幾塊、誰共用
*   分清各種垃圾回收器與預設是哪個
*   看懂 OutOfMemoryError 是哪塊爆了
*   答出類別載入與父委派

*【執行期資料區】*

## JVM 把記憶體分成哪幾塊

> 🏠 **生活比喻**
>
> - 堆積＝**公司共用倉庫**，物件都放這
> - 堆疊＝**每位員工自己的辦公桌**
> - Metaspace＝**放類別說明書的檔案室**
> - 程式計數器＝**每人手上的「做到第幾行」書籤**

每個實驗的實跑輸出見〈JVM 記憶體與垃圾回收〉。

答題公式：先一句話定義，再講差別與取捨，最後補版本或實務註記。以下以 Java 25 的 HotSpot 為準，跟 Java 21 不同處會標出。JVM、JRE、JDK 與位元碼見〈Java 是什麼、環境怎麼裝〉。

> 💡 面試官：JVM 執行期資料區有哪些？哪些是執行緒共用、哪些私有？

**一句話定義**：Java 虛擬機規格（JVMS，定義 JVM 該怎麼運作的正式文件）第 2.5 節把執行期間用到的記憶體分成幾塊執行期資料區（run-time data areas）：有的在 JVM 啟動時建立、關機才銷毀；有的隨執行緒建立與銷毀。[出處](https://docs.oracle.com/javase/specs/jvms/se25/html/jvms-2.html#jvms-2.5)

| 區域（JVMS 正式名稱） | 放什麼 | 誰擁有 | 爆掉時丟什麼 |
| --- | --- | --- | --- |
| 堆（heap） | 所有物件與陣列的實體 | 全部執行緒共用 | `OutOfMemoryError` |
| 方法區（method area） | 類別結構：欄位與方法的資訊、方法的位元碼、執行時常數池（run-time constant pool，每個類別的常數與符號參考表） | 全部執行緒共用 | `OutOfMemoryError` |
| JVM 堆疊（Java Virtual Machine stack） | 每次方法呼叫一個「框」（frame）：區域變數、運算元堆疊 | 每條執行緒一個 | `StackOverflowError`；開新執行緒配不出堆疊時是 `OutOfMemoryError` |
| pc 暫存器（pc register） | 這條執行緒目前執行到哪一條指令 | 每條執行緒一個 | — |
| 本機方法堆疊（native method stack） | 執行 C 這類原生程式碼時用的堆疊 | 每條執行緒一個 | `StackOverflowError` 或 `OutOfMemoryError` |

**差別與取捨**：面試官真正想聽的是「堆與方法區共用，所以要垃圾回收、要同步；堆疊與 pc 私有，所以區域變數天生執行緒安全」。堆與方法區在所有 JVM 執行緒之間共用；每條 JVM 執行緒則有自己私有的 JVM 堆疊，跟執行緒同時建立。[出處](https://docs.oracle.com/javase/specs/jvms/se25/html/jvms-2.html#jvms-2.5) 執行緒與共享狀態為什麼要協調，見〈執行緒與並行〉。

**實務註記**：每條執行緒的堆疊大小用 `-Xss` 設，Linux/x64 與 macOS/x64 預設 1024 KB、Aarch64 預設 2048 KB。[出處](https://docs.oracle.com/en/java/javase/25/docs/specs/man/java.html) 遞迴太深丟的是 `StackOverflowError`，不是 `OutOfMemoryError`——兩個常被混著答。

> 💡 面試官：堆裡的年輕代、老年代是什麼？物件什麼時候晉升？

**一句話定義**：HotSpot 把堆分成年輕代（young generation）與老年代（old generation）；年輕代再分成 Eden 與兩塊 Survivor 空間。分代的依據是弱分代假說（weak generational hypothesis）：多數物件只活很短的時間，所以把新物件集中放一區、頻繁回收那一區，效率最好。[出處](https://docs.oracle.com/en/java/javase/25/gctuning/garbage-collector-implementation.html)

**差別與取捨**：物件在年輕代裡的流程：[出處](https://docs.oracle.com/en/java/javase/25/gctuning/garbage-collector-implementation.html)

*   多數物件一開始配置在 Eden
*   任何時候都有一塊 Survivor 是空的，當作回收時 Eden 與另一塊 Survivor 裡活物件的目的地；回收完，Eden 與來源 Survivor 都清空
*   物件就這樣在兩塊 Survivor 之間來回複製，這叫老化（aging）
*   複製過一定次數、或 Survivor 空間不夠，就複製進老年代，這叫晉升

年輕代越大，年輕代回收（minor GC）越少發生；但堆總量固定時老年代就變小，老年代回收（major GC）反而變多——這是調年輕代大小的核心取捨。[出處](https://docs.oracle.com/en/java/javase/25/gctuning/factors-affecting-garbage-collection-performance.html)

**實務註記（一定會被問的參數）：**`-Xms` 設堆的初始（也是最小）大小、`-Xmx` 設最大；沒設時預設初始值是實體記憶體的 1/64、最大值是 1/4[出處](https://docs.oracle.com/en/java/javase/25/gctuning/ergonomics.html)。

伺服器部署通常把 `-Xms` 與 `-Xmx` 設成同一個值，省掉執行中反覆擴縮堆的成本。[出處](https://docs.oracle.com/en/java/javase/25/docs/specs/man/java.html)

年輕代對老年代的比例用 `-XX:NewRatio`（例如 `=3` 表示 1:3）、Eden 對單塊 Survivor 的比例用 `-XX:SurvivorRatio`（預設 8）。[出處](https://docs.oracle.com/en/java/javase/25/gctuning/factors-affecting-garbage-collection-performance.html)

> 年輕代靠「大部分物件很快就死」賺效率；活過幾輪 Survivor 來回的才晉升老年代

> 💡 面試官：Metaspace 取代永久代解決了什麼？

**一句話定義**：Metaspace是 HotSpot 放類別中繼資料（class metadata，JVM 內部對每個類別的描述：欄位、方法、位元碼）的地方，也就是 JVMS 裡的方法區在 HotSpot 的實作。Java 8 起它從堆裡的永久代（permanent generation，PermGen）搬到原生記憶體（native memory，作業系統直接給行程的記憶體，不在 Java 堆內）。[出處](https://docs.oracle.com/en/java/javase/25/gctuning/other-considerations.html)

**差別與取捨**：解決的是「要手動調永久代大小」這件事。Java 8（JEP 122）從 HotSpot 移除永久代，從此不必再調它的大小：類別中繼資料改配置在原生記憶體，字串池與類別的靜態變數則搬進 Java 堆。[出處](https://openjdk.org/jeps/122)

舊時代 `-XX:MaxPermSize` 設太小就 `OutOfMemoryError: PermGen space`；現在 Metaspace 預設沒有上限，要限制才用 `-XX:MaxMetaspaceSize`。[出處](https://docs.oracle.com/en/java/javase/25/gctuning/other-considerations.html)

**實務註記：**「沒有上限」不等於不會爆——類別載入器一直載新類別（例如反覆重新部署、動態產生代理類別）而載入器又沒被回收，就會把 Metaspace 吃到 `OutOfMemoryError: Metaspace`。原因在 Metaspace 的配置方式：空間切成一塊塊（chunk），每塊綁定某個類別載入器；那個載入器的類別被卸載時，它的區塊才回收再用或還給作業系統。[出處](https://docs.oracle.com/en/java/javase/25/gctuning/other-considerations.html) 所以 Metaspace 洩漏幾乎都是「類別載入器洩漏」，下一節再講。另一個常被搞混的參數 `-XX:MetaspaceSize` 不是上限，是觸發垃圾回收的高水位線（high-water mark）。[出處](https://docs.oracle.com/en/java/javase/25/gctuning/other-considerations.html)

*【垃圾回收】*

## 怎麼判斷死活、選哪個回收器、停頓怎麼縮

> 🏠 **生活比喻**
>
> - 可達性＝**從大門順著通訊錄找得到的就是在職員工**
> - 回收器＝不同的**清潔公司**：Serial 一人慢掃、G1 分區掃、ZGC 邊上班邊掃
> - Stop-The-World＝**大掃除全員暫停**

> 💡 面試官：什麼是 GC Root？可達性分析怎麼判斷物件死了？

**一句話定義**：HotSpot 判斷死活的準則是可達性（reachability）：一個物件從執行中程式的任何活物件、經由任何參考都到達不了，就是垃圾，記憶體可以被 VM 重用。[出處](https://docs.oracle.com/en/java/javase/25/gctuning/garbage-collector-implementation.html)

*   起點叫 GC Root（根）：從堆外指進 Java 物件堆的指標，例如類別的靜態欄位、執行中方法框裡的區域參考[出處](https://openjdk.org/groups/hotspot/docs/HotSpotGlossary.html)
*   從根出發沿著參考走得到的都算活，走不到的就是垃圾
*   這種「從根追蹤」的做法叫追蹤式回收（tracing garbage collection）

**差別與取捨**：面試官常追問「為什麼不用參考計數？」參考計數（reference counting，每個物件記著有幾個參考指著它，歸零就回收）最單純的版本處理不了參考循環（一個物件直接或間接指回自己）：兩個互相指著對方、但外面沒人指的物件，計數永遠不會歸零。追蹤式回收從根出發，這兩個物件走不到，自然回收。[出處](https://en.wikipedia.org/wiki/Reference_counting)

**實務註記：**「走得到」有強弱之分——`java.lang.ref` 套件把可達性分成強、軟、弱、虛四級，後面「強、軟、弱、虛參考差在哪」那題會講。

> 💡 面試官：常見垃圾回收器 Serial、Parallel、G1、ZGC 各適合什麼？現在預設是哪個？

**一句話定義**：Oracle JDK 的調校指南列出四個回收器，取捨軸只有兩條：吞吐量（throughput，單位時間內能做多少應用程式的工作）對停頓時間（pause time，應用程式被暫停等回收的時間），再加上機器大小。

| 回收器 | 特性 | 適合 | 開啟 |
| --- | --- | --- | --- |
| Serial | 用單一執行緒做所有垃圾回收工作，沒有執行緒間溝通成本 | 資料量小（約 100 MB 以內）、單處理器、不在意停頓 | `-XX:+UseSerialGC` |
| Parallel | 也叫吞吐量回收器，跟 Serial 一樣分代，差在用多條執行緒加速回收 | 要榨出最高峰值吞吐量、能忍受一秒以上停頓（批次工作） | `-XX:+UseParallelGC` |
| G1 | 大致並行（mostly concurrent）的回收器，能以高機率達成停頓時間目標，同時保有高吞吐量 | 回應時間重要、要短停頓的一般伺服器應用 | `-XX:+UseG1GC` |
| ZGC | 最大停頓在一毫秒以內，但犧牲一些吞吐量；停頓時間與堆大小無關，適用幾百 MB 到 16 TB 的堆 | 延遲最優先、堆很大 | `-XX:+UseZGC` |

出處：[Java 25 HotSpot 調校指南](https://docs.oracle.com/en/java/javase/25/gctuning/available-collectors.html)

面試也常提到 **Shenandoah**：另一個走低停頓路線的回收器，Java 15 起從實驗功能轉正式（JEP 379）。[出處](https://openjdk.org/jeps/379)

*   原本是 Red Hat 在 8u 與 11u 下游版本中出貨的受支援回收器
*   Oracle 的調校指南只列上面四個、沒有它——用不用得到，要看手上的 JDK 是哪家建置的
*   有的話用 `-XX:+UseShenandoahGC` 開

**現在預設是哪個**：G1 自 Java 9 起是預設回收器（JEP 248），之前是 Parallel。理由是限制停頓時間一般比最大化吞吐量更重要，對多數使用者來說，G1 這種低停頓回收器的整體體驗比吞吐導向的 Parallel 好。[出處](https://openjdk.org/jeps/248) 但有一個常被忽略的前提：預設 G1 的條件是伺服器級機器——JVM 偵測到兩顆以上處理器、且實體記憶體大於等於 1792 MB 才算，否則預設 Serial。[出處](https://docs.oracle.com/en/java/javase/25/gctuning/ergonomics.html) 容器只給 1 顆 CPU 時拿到的是 Serial，這是面試加分點。

**版本註記**：舊教材裡的 CMS（Concurrent Mark Sweep）在 Java 14 已移除（JEP 363），現在下 `-XX:+UseConcMarkSweepGC` 只會得到一行「Ignoring option」警告然後用預設回收器。[出處](https://openjdk.org/jeps/363)

ZGC 的參數隨版本變過：

*   **ZGC 在 Java 15** 從實驗功能轉正式（JEP 377，不再需要 `-XX:+UnlockExperimentalVMOptions`）[出處](https://openjdk.org/jeps/377)。
*   **Java 21 加入分代模式**，當時要多加 `-XX:+ZGenerational`（JEP 439）[出處](https://openjdk.org/jeps/439)。
*   **Java 23 起分代是預設**（JEP 474）[出處](https://openjdk.org/jeps/474)。
*   **Java 24 起不分代的模式整個移除**，`ZGenerational` 這個選項也拿掉了（JEP 490）[出處](https://openjdk.org/jeps/490)。

所以 Java 21 與 Java 25 答 ZGC 的參數不一樣：21 要加旗標，25 直接 `-XX:+UseZGC` 就是分代 ZGC。[出處](https://docs.oracle.com/en/java/javase/25/gctuning/z-garbage-collector1.html)

> 吞吐量要最高選 Parallel，停頓要可預期選 G1，停頓要一毫秒以內選 ZGC，機器小到只有一顆 CPU 就是 Serial

> 💡 面試官：Stop-The-World 是什麼？G1 怎麼縮短停頓？

**一句話定義**：Stop-The-World（STW）是回收器把所有應用程式執行緒全部暫停、只剩回收執行緒在跑的那段時間；最基本的 Serial 就是序列的 stop-the-world 回收器，整段回收都在暫停中做完。[出處](https://docs.oracle.com/en/java/javase/25/gctuning/introduction-garbage-collection-tuning.html) 為什麼一定要停？因為回收器在搬物件、改參考的時候，應用程式若同時在改同一批物件，兩邊會互相踩到。

**G1 怎麼做**：三招。[出處](https://docs.oracle.com/en/java/javase/25/gctuning/garbage-first-g1-garbage-collector1.html)

*   切區域：把堆切成一組大小相等的區域（region），每塊是配置與回收的單位；區域大小依最大堆算，目標是切出大約 2048 塊、每塊上限 32 MB。這樣每次回收可以只挑幾塊來做，不必整個堆一起
*   並行標記：最花時間的「標記活物件」與應用程式同時進行（concurrent marking），用的演算法叫 SATB（Snapshot-At-The-Beginning，在並行標記開始的那個停頓點替堆拍一張虛擬快照，之後照快照標）；標記結束只剩兩個短的 STW 停頓：Remark 與 Cleanup
*   停頓時間目標：`-XX:MaxGCPauseMillis` 預設 200 毫秒；G1 追蹤過去應用程式行為與回收停頓的資訊建立成本模型，用它決定每次停頓做多少工作，也就是這一輪挑幾塊區域來搬

**要老實講的限制**：G1 不是零停頓——它仍在 stop-the-world 停頓中回收，把活物件從來源區域複製到一或多塊目的區域、並調整既有參考，只是把停頓切小、切得可預期。最壞情況是疏散失敗（evacuation failure，要搬的物件找不到地方放）：一次回收完全清不出空間時，G1 會排一次 Full GC，對整個堆做原地壓縮，那一次停頓就長了。[出處](https://docs.oracle.com/en/java/javase/25/gctuning/garbage-first-g1-garbage-collector1.html)

> 💡 面試官：強、軟、弱、虛參考差在哪？

**一句話定義**：一般寫的 `Object o = new Object()` 是強參考（strong reference）；`java.lang.ref` 套件另外提供三種比較弱的參考，讓程式可以指著一個物件、但不阻止它被回收，並在它被回收前後收到通知。四種對應四級可達性，由強到弱：

| 參考 | 可達性定義 | 建議用途 |
| --- | --- | --- |
| 強 | 不需經過任何 Reference 物件就能到達——只要強可達就絕不回收 | 一般程式碼 |
| 軟（SoftReference） | 不是強可達，但經過軟參考可以到達；保證在虛擬機丟出 `OutOfMemoryError` 之前，所有指向軟可達物件的軟參考都已被清除[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/ref/SoftReference.html) | 對記憶體敏感的快取 |
| 弱（WeakReference） | 既非強也非軟可達，但經過弱參考可以到達；回收器一判定物件只剩弱可達，就一次清除所有指向它的弱參考[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/ref/WeakReference.html) | 正規化對應表（canonicalizing mapping，不阻止鍵被回收的對照表，例如 `WeakHashMap`） |
| 虛（PhantomReference） | 非強、軟、弱可達，且已經 finalize 過，但有虛參考指著它；虛參考的 `get` 永遠回傳 `null`[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/ref/PhantomReference.html) | 安排物件死後的清理動作，也可交給 `Cleaner` 管理 |

出處：[java.lang.ref 套件](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/ref/package-summary.html)

**取捨：**

*   軟參考當快取看起來省事，代價是回收時機交給 JVM 決定，效能不可預期
*   弱參考最常見的實務用途是「鍵是別人擁有的物件，不該因為對照表記著它就讓它一直活著」
*   虛參考定義裡的 finalize 機制已不建議用，它可能帶來安全、效能與可靠性的問題；JDK 18 起標為棄用、預定移除（JEP 421）[出處](https://docs.oracle.com/en/java/javase/25/gctuning/other-considerations.html)

*【記憶體出問題時】*

## OutOfMemoryError 的種類、洩漏來源與診斷工具

> 🏠 **生活比喻**
>
> - 堆積不足＝**倉庫塞爆**
> - 洩漏＝**東西一直塞進公共收納箱沒人拿走**，清潔工不敢丟
> - 診斷＝**拍下倉庫照片（heap dump）看是誰佔最多**

> 💡 面試官：OutOfMemoryError 有哪幾種？各怎麼排查？

**一句話定義：**`OutOfMemoryError` 不是一種錯，是一組錯——訊息文字告訴你是哪一塊記憶體爆了：

| 訊息 | 成因 | 先做什麼 |
| --- | --- | --- |
| `Java heap space` | 物件無法在 Java 堆配置。這不一定代表洩漏，可能只是 `-Xmx` 設太小；但長時間執行的應用出現它，可能是程式無意間持有物件的參考、讓它們無法被回收——這就是 Java 版的記憶體洩漏 | 先確認 `-Xmx`；還是爆就抓 heap dump 看誰占最多 |
| `GC overhead limit exceeded` | 回收器幾乎一直在跑、程式進展極慢：一次回收後，若連續五次花超過約 98% 的時間在回收、卻回收不到 2% 的堆，就丟這個錯；通常是活資料剛好塞滿堆，幾乎沒空間給新配置 | 本質同上：堆太小或洩漏。`-XX:-UseGCOverheadLimit` 能關掉這個檢查，但只是讓它變成另一種 OOM（OutOfMemoryError 的簡稱） |
| `Metaspace` | 類別中繼資料配置在原生記憶體（Metaspace），用量超過 `MaxMetaspaceSize` 就丟 | 沒設上限卻爆了，找類別載入器洩漏；有設就評估調高 |
| `Compressed class space` | 64 位元平台開了壓縮類別指標（把 64 位元的類別指標壓成 32 位元存放以省記憶體）時，類別中繼資料的一部分放在大小固定的區域（`CompressedClassSpaceSize`，預設 1 GB[出處](https://docs.oracle.com/en/java/javase/25/gctuning/other-considerations.html)），超過就丟 | 調大 `-XX:CompressedClassSpaceSize`，或一樣找載入器洩漏 |
| `Requested array size exceeds VM limit` | 要配置的陣列大於 VM 實作上限，跟堆還剩多少無關 | 程式邏輯錯，改程式 |
| `request … bytes for … Out of swap space?` | 原生堆配置失敗、原生堆可能接近耗盡——不是 Java 堆，是整個行程的記憶體 | 看 JVM 產生的致命錯誤日誌，用作業系統工具查 |

出處：[Java 25 疑難排解指南](https://docs.oracle.com/en/java/javase/25/troubleshoot/troubleshooting-memory-leaks.html)

另外兩種面試常問的：

*   **`unable to create native thread: possibly out of memory or process/resource limits reached`**——啟動執行緒時作業系統拒絕建立原生執行緒就丟。訊息文字定義在 HotSpot 原始碼 `os.hpp`。[出處](https://github.com/openjdk/jdk/blob/master/src/hotspot/share/runtime/os.hpp) 對應 JVMS 的規則：配不出足夠記憶體給新執行緒建立初始 JVM 堆疊時，丟 `OutOfMemoryError`。[出處](https://docs.oracle.com/javase/specs/jvms/se25/html/jvms-2.html#jvms-2.5.2) 排查方向是執行緒數：作業系統的行程執行緒上限、每條執行緒的 `-Xss`、有沒有執行緒池無上限地開。注意 `-XX:+HeapDumpOnOutOfMemoryError` 對它無效：這個選項只適用於 Java 堆耗盡造成的 OutOfMemoryError，原生執行緒建立失敗這類其他資源耗盡不適用。[出處](https://docs.oracle.com/en/java/javase/25/docs/specs/man/java.html)
*   **`Cannot reserve … bytes of direct buffer memory`**——`ByteBuffer.allocateDirect()` 這類直接緩衝區（direct buffer，配置在堆外、讓 I/O 少複製一次的記憶體）超過上限時由 `java.nio.Bits` 丟出。[出處](https://github.com/openjdk/jdk/blob/master/src/java.base/share/classes/java/nio/Bits.java) 上限用 `-XX:MaxDirectMemorySize` 設，沒設時由 JVM 自動決定。[出處](https://docs.oracle.com/en/java/javase/25/docs/specs/man/java.html) 它不在 Java 堆裡，所以 `-Xmx` 調再大也沒用。

**怎麼抓 heap dump、看什麼**：heap dump（堆轉存，把堆裡所有物件與參考關係一次寫成檔案）有三條路：

*   事前加 `-XX:+HeapDumpOnOutOfMemoryError`：爆的當下自動寫，配 `-XX:HeapDumpPath` 指定位置，預設在目前目錄、檔名 `java_pid<pid>.hprof`[出處](https://docs.oracle.com/en/java/javase/25/docs/specs/man/java.html)
*   事中用 `jcmd <pid> GC.heap_dump filename=heapdump.dmp`
*   或 `jmap -dump:format=b,file=snapshot.jmap <pid>`

看之前先跑 `jcmd <pid> GC.class_histogram`（或 `jmap -histo`）——它列出每個類別有幾個實體、占多少位元組，便宜又常常直接看出兇手。dump 檔用分析工具開（例如 JDK Mission Control、Eclipse Memory Analyzer），看兩件事：哪些物件占最多，以及從 GC Root 到那個物件的參考鏈——誰抓著它不放，就是洩漏點。[出處](https://docs.oracle.com/en/java/javase/25/troubleshoot/troubleshooting-memory-leaks.html)

> 💡 面試官：記憶體洩漏在 Java 怎麼發生？常見來源？

**一句話定義**：Java 有垃圾回收，所以「忘記釋放」不會洩漏，「忘記放手」才會：程式無意間持有物件的參考，讓它們無法被回收。[出處](https://docs.oracle.com/en/java/javase/25/troubleshoot/troubleshooting-memory-leaks.html) 每一種常見來源都是同一個模式：一個活很久的東西抓著一個本該死掉的東西。

*   **static 集合**：靜態欄位的壽命跟類別一樣長，而類別只有在它的類別載入器可被回收時才可能被卸載，由啟動載入器載的類別永不卸載（JLS 12.7）。[出處](https://docs.oracle.com/javase/specs/jls/se25/html/jls-12.html#jls-12.7) 所以往 `static Map` 塞東西不拿出來，等於永久持有。
*   **沒關閉的資源**：連線、檔案、串流背後是作業系統資源，要用 try-with-resources：它宣告一或多個用完必須關閉的資源，保證每個資源在敘述結束時被關閉；任何實作 `AutoCloseable` 的物件都能放進去。[出處](https://docs.oracle.com/javase/tutorial/essential/exceptions/tryResourceClose.html)
*   **`ThreadLocal`**：只要執行緒活著、`ThreadLocal` 實體也還能存取，每條執行緒就對自己那份執行緒區域變數持有隱含參考；執行緒消失後，那些副本才可被回收。[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/ThreadLocal.html) 問題在執行緒池——池裡的執行緒不會消失，值就一直掛在上面，還會被下一個借到這條執行緒的請求讀到。用完呼叫 `remove()`。
*   **監聽器與回呼**：向一個長壽物件（事件來源、全域註冊表）註冊了監聽器卻沒取消註冊，該物件就從長壽物件可達，照可達性定義永遠不是垃圾。[出處](https://docs.oracle.com/en/java/javase/25/gctuning/garbage-collector-implementation.html)
*   **類別載入器洩漏**（Metaspace 版的洩漏）：只要載入器載出來的任何一個類別還有實體活著、或有人持有那個載入器，整個載入器和它所有類別的中繼資料都留在 Metaspace（由 JLS 12.7 推得）。典型情境是應用伺服器反覆重新部署同一個應用卻不重啟行程。

> 💡 面試官：常用的 JVM 診斷工具有哪些？

**一句話定義**：JDK 自帶一整組命令列工具；現在建議用 `jcmd` 取代先前的 `jmap`、`jstack`、`jinfo`，診斷能力更強、效能負擔更低。[出處](https://docs.oracle.com/en/java/javase/25/troubleshoot/diagnostic-tools.html)

| 工具 | 做什麼 | 面試會問的情境 |
| --- | --- | --- |
| `jcmd` | 送診斷命令給 JVM，必須在同一台機器、同一個使用者下執行。常用子命令：`Thread.print`（印出所有執行緒與堆疊）、`GC.heap_dump`、`GC.class_histogram`、`GC.heap_info`、`VM.flags`（目前生效的 JVM 參數）、`VM.native_memory`（原生記憶體用量）、`JFR.start` | 「線上服務卡住了，第一步做什麼」——`jcmd <pid> Thread.print` 看執行緒在等什麼 |
| `jstack` | 印 Java 執行緒的堆疊，看死結與執行緒卡在哪；建議改用 `jcmd` 或 `jhsdb jstack` | 死結排查（基礎見〈執行緒與並行〉） |
| `jmap` | 印出執行中 VM 或核心轉存檔的記憶體統計：類別直方圖、heap dump | OOM 排查 |
| `jstat` | 用 HotSpot 內建的計數器提供執行中應用程式的效能與資源消耗資訊——各代用量、回收次數與時間 | 「懷疑 GC 太頻繁怎麼確認」 |
| JFR | Flight Recorder，內建於 JDK 的側寫與事件收集框架；Java 11 起隨 OpenJDK 開放（JEP 328），目標是開箱即用時效能負擔至多 1%，適合開在正式環境 | 「不能重現的效能問題怎麼抓」——開錄，事後用 JDK Mission Control 分析 |

出處：[疑難排解指南的工具章](https://docs.oracle.com/en/java/javase/25/troubleshoot/diagnostic-tools.html)、[jcmd 手冊](https://docs.oracle.com/en/java/javase/25/docs/specs/man/jcmd.html)、[JEP 328](https://openjdk.org/jeps/328)

> 先 Thread.print 看執行緒、再 GC.class_histogram 看物件、還不夠才 heap dump；長期趨勢交給 JFR

*【類別載入與 JIT】*

## 類別怎麼進來、程式碼怎麼變快

> 🏠 **生活比喻**
>
> - 雙親委派＝**遇到事先問主管**，避免假冒的核心類別
> - JIT＝**常說的話寫成正式譯稿**，越跑越快

> 💡 面試官：類別載入的三步與父委派模型是什麼？

**一句話定義**：JVMS 第 5 章把一個類別從 `.class` 檔到可用分成三步：[出處](https://docs.oracle.com/javase/specs/jvms/se25/html/jvms-5.html)

*   **載入**（loading）：找到某個名稱的類別的二進位表示，據此建立類別
*   **連結**（linking）：把類別結合進 JVM 的執行時狀態，讓它可以執行。又分三小步：驗證（確認二進位結構正確）、準備（建立靜態欄位並設為預設值，例如 0 與 `null`）、解析（把執行時常數池裡的符號參考換成實際位址）
*   **初始化**（initialization）：執行類別初始化方法 `<clinit>`，也就是靜態欄位的初始值與 static 區塊

**差別與取捨**：面試官愛問「準備」與「初始化」的差別——`static int x = 5` 在準備階段 x 是 0，初始化才變 5。初始化是懶的（lazy）：類別在第一次發生下列任一事件之前才初始化——建立它的實體、呼叫它的靜態方法、對它的靜態欄位賦值、讀取它的非常數靜態欄位；載入與連結不會觸發。[出處](https://docs.oracle.com/javase/specs/jls/se25/html/jls-12.html#jls-12.4.1) 反過來，`Class.forName("X")` 會讓名為 X 的類別被初始化，所以舊式 JDBC 程式碼靠它讓驅動程式的 static 區塊執行、把自己註冊進去。[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Class.html#forName(java.lang.String))

**三層載入器與父委派**：JDK 內建三層：

*   **啟動類別載入器**（bootstrap）：虛擬機內建，通常以 `null` 表示，沒有父載入器
*   **平台類別載入器**（platform）：載 Java SE 平台 API 與其實作類別
*   **系統類別載入器**（system，也叫應用程式類別載入器）：載類別路徑與模組路徑上的類別

每個 `ClassLoader` 實體都有一個父載入器；被要求找類別時，通常先委派給父載入器，再自己找。`loadClass` 的預設演算法就三步：`findLoadedClass` 看載過沒 → 呼叫父載入器的 `loadClass`（父是 `null` 就用啟動載入器）→ 都沒有才呼叫自己的 `findClass`。[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/ClassLoader.html)

這就是父委派模型（parent delegation model；面試常聽到的講法「雙親委派」指的是同一件事——先問父親，父親找不到才自己找）。效果：同一個名稱的類別，由委派鏈上最上層找得到它的載入器定義，自己寫一個 `java.lang.String` 放進類別路徑也搶不到。另外還有一道硬規定：名稱以 `java.` 開頭的類別只能由平台類別載入器或其祖先定義，否則 `defineClass` 丟 `SecurityException`。[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/ClassLoader.html#defineClass(java.lang.String,byte%5B%5D,int,int))

**版本註記**：Java 8 以前的第二層叫「擴充類別載入器」，載 `jre/lib/ext` 下的 jar；Java 9 起這個擴充機制整個移除（JEP 220）：設了 `java.ext.dirs` 系統屬性、或 `lib/ext` 目錄存在，編譯器與啟動器會直接失敗，`rt.jar` 也沒了。[出處](https://openjdk.org/jeps/220) 面試答「Bootstrap、Extension、Application」三層是 Java 8 的答案，現在中間那層是「Platform」。classpath 與這段歷史的細節見〈套件與 Object 類別〉。

> 載入找檔、連結接線、初始化才跑 static；載入器先問父親、找不到才自己找

> 💡 面試官：JIT 是什麼？分層編譯做了什麼？為什麼「暖機」後比較快？

**一句話定義**：JIT（Just-In-Time，即時編譯）是 HotSpot 在程式執行中把位元碼編成機器碼的機制：[出處](https://docs.oracle.com/en/java/javase/25/vm/java-virtual-machine-technology-overview.html)

*   一開始用標準的直譯器啟動應用程式
*   程式跑起來後，分析程式碼找出效能瓶頸，也就是熱點（hot spots）
*   只編譯效能關鍵的那部分，很少用到的程式碼（也就是應用程式的大部分）不編
*   由自適應編譯器決定內嵌（inlining，把被呼叫的小方法直接貼進呼叫端）這類最佳化

這也是 HotSpot 名字的由來。

**分層編譯做了什麼**：HotSpot 有兩個編譯器：C1（client compiler，先求快速編出可用的版本）與 C2（server compiler，負責產生最終、最佳化最深的版本）。

分層編譯（tiered compilation）在 Java SE 7 引入，差別在側寫（profiling，記錄哪個分支常走、哪個型別常出現）怎麼做：[出處](https://docs.oracle.com/en/java/javase/25/vm/java-hotspot-virtual-machine-performance-enhancements.html)

*   沒有分層編譯：伺服器 VM 用直譯器收集方法的側寫資訊，送給編譯器
*   有分層編譯：先用 C1 產生一版會自己收集側寫資訊的編譯碼。編譯碼比直譯器快得多，所以側寫階段本身就跑得快
*   側寫跑得快，就能側寫更久，最佳化更好，峰值效能反而更好

分層編譯預設開啟，`-XX:-TieredCompilation` 可以關。

預設值也是同時使用 C1 與 C2 的分層編譯器。[出處](https://docs.oracle.com/en/java/javase/25/gctuning/ergonomics.html)

**為什麼要暖機**：把上面兩段連起來就是答案——剛啟動時所有程式碼都在直譯器裡跑，慢；要跑一陣子讓熱點浮現、側寫收集夠、C1 再到 C2 逐層編完，速度才到頂。所以壓力測試與效能量測要先跑一段「暖機」（warm-up）再計時，剛部署的服務前幾分鐘延遲偏高也是正常現象。

*【兩個老面孔】*

## HashMap 的內部與字串池

> 🏠 **生活比喻**
>
> - HashMap＝**車站置物櫃**，用算的找櫃號；同櫃太擠會改成排序好的樹
> - 字串池＝**公用的印章架**，相同字樣的印章只刻一個大家共用

> 💡 面試官：HashMap 的內部結構、擴容機制？Java 8 為什麼加紅黑樹？HashMap、ConcurrentHashMap、Hashtable 怎麼選？

**一句話定義：**`HashMap` 是一張桶（bucket）陣列：用鍵的 `hashCode()` 算出落在哪個桶，同一桶裡的多個項目串成鏈結串列。兩個參數：[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/HashMap.html)

*   初始容量（initial capacity）：雜湊表裡桶的數量，預設 16
*   負載因子（load factor）：允許表填到多滿才自動擴容，預設 0.75
*   項目數超過負載因子乘以目前容量，雜湊表就重新雜湊（rehash），桶數大約變成兩倍

所以門檻是 16 × 0.75 = 12，放進第 13 筆（超過 12）時擴到 32。`equals()` 與 `hashCode()` 為什麼要一起覆寫，見〈套件與 Object 類別〉；集合怎麼選見〈集合與泛型〉。

**Java 8 為什麼加紅黑樹**：紅黑樹是一種自己會保持平衡的搜尋樹。很多鍵撞進同一個桶時，鏈結串列查找退化成 O(n)；Java 8（JEP 180）在高碰撞情況下改用平衡樹存放項目，最壞情況從 O(n) 改善到 O(log n)。[出處](https://openjdk.org/jeps/180) 門檻是 OpenJDK 原始碼 `HashMap.java` 裡的常數：[出處](https://github.com/openjdk/jdk/blob/master/src/java.base/share/classes/java/util/HashMap.java)

*   樹化：同一桶已有 `TREEIFY_THRESHOLD`（8）個節點、再放進一筆，且表容量已達 `MIN_TREEIFY_CAPACITY`（64）；容量還不到 64 時選擇擴容而不樹化
*   退回串列：縮回 `UNTREEIFY_THRESHOLD`（6）個
*   樹節點大約是普通節點的兩倍大，所以只在值得的時候用

**三個怎麼選：**

|   | 執行緒安全 | null 鍵值 | 定位 |
| --- | --- | --- | --- |
| `HashMap` | 否——不是同步的，多執行緒要改結構必須外部同步 | 允許 | 單執行緒或外面已經有鎖的預設選擇 |
| `Hashtable` | 是——整張表一把鎖 | 都不允許 | 不需要執行緒安全就用 `HashMap`；需要執行緒安全又要高並行就用 `ConcurrentHashMap`——也就是兩種情況都不該選它 |
| `ConcurrentHashMap` | 是——讀取操作不加鎖，也不支援鎖住整張表；讀取（含 `get`）一般不會阻塞，可與更新重疊 | 都不允許 | 多執行緒共用的對照表 |

出處：[HashMap](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/HashMap.html)、[Hashtable](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/Hashtable.html)、[ConcurrentHashMap](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ConcurrentHashMap.html)

> 💡 面試官：字串池是什麼？intern() 做什麼？為什麼 String 不可變？

**一句話定義：**`String` 是常數，建立後值不能改變；因為不可變，所以可以被共用。[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/String.html)

「可以被共用」就是字串池存在的前提：[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/String.html#intern())

*   字串池（string pool）是 `String` 類別私下維護的一個池
*   `intern()`：池裡已有 `equals` 相等的字串就回傳池裡那個，否則把這個字串放進池並回傳它
*   所有字面值字串與字串型別的常數表達式都會被 intern

不可變的鋪陳與 `==` 對 `equals()` 的差別見〈物件與類別〉。

**差別與取捨——那組經典的 `==` 題**：字串字面值永遠指向同一個 `String` 實體，因為字面值與常數表達式會被 intern、共用唯一實體，如同執行了 `String.intern`（JLS 3.10.5）。[出處](https://docs.oracle.com/javase/specs/jls/se25/html/jls-3.html#jls-3.10.5)

*   `"Hello" == "Hel" + "lo"` 是 `true`：兩邊都是編譯期常數
*   `"Hello" == "Hel" + lo`（`lo` 是變數）是 `false`：執行期串接出來的是新物件，加上 `.intern()` 後才又是 `true`
*   `new String("Hi")` 也一樣是堆上的新物件，不在池裡

**為什麼要不可變、池在哪裡**：理由都是「共用」的推論：

*   池裡的字串被很多變數共用，若能改，改了一個大家都被改
*   值不變所以 `hashCode()` 可以算一次存起來（`String.java` 的 `hash` 欄位就是快取雜湊碼用的），`HashMap` 用字串當鍵才快[出處](https://github.com/openjdk/jdk/blob/master/src/java.base/share/classes/java/lang/String.java)
*   多執行緒讀同一個字串也不需要鎖

至於池的位置：Java 8 移除永久代時（JEP 122），類別中繼資料改放原生記憶體，intern 的字串與類別靜態變數搬進 Java 堆——所以現在字串池在堆裡，池裡沒人參考的字串一樣會被回收，「intern 太多會爆 PermGen」是永久代時代的老答案。[出處](https://openjdk.org/jeps/122)

### 🗺️ 比喻對照表

| 技術名詞 | 生活比喻 |
| --- | --- |
| Heap / Stack | 共用倉庫 / 個人辦公桌 |
| GC | 清潔公司 |
| 記憶體洩漏 | 塞進公共收納箱沒人拿 |
| HashMap | 車站置物櫃 |
| 字串池 | 公用印章架 |

### 重點整理

*   五塊執行期資料區：堆與方法區全執行緒共用，JVM 堆疊、pc 暫存器、本機方法堆疊每條執行緒一份；遞迴太深是 `StackOverflowError`。
*   堆分年輕代（Eden＋兩塊 Survivor）與老年代，依據是「多數物件很快就死」；活過幾輪複製才晉升。`-Xms`／`-Xmx` 伺服器通常設相等。
*   Java 8 起類別中繼資料放原生記憶體的 Metaspace（JEP 122），預設無上限，`-XX:MaxMetaspaceSize` 才是上限；Metaspace 爆掉幾乎都是類別載入器洩漏。
*   死活看可達性（從 GC Root 走得到才活），不用參考計數，所以循環參考不是問題；四種參考強度：強不回收、軟快取、弱對照表、虛做死後清理。
*   G1 自 Java 9 預設（JEP 248，前提是兩顆 CPU 以上與 1792 MB 以上，否則 Serial）；吞吐選 Parallel、一毫秒停頓選 ZGC；CMS 在 Java 14 移除；ZGC 在 Java 23 起預設分代、24 起只剩分代。
*   OOM 看訊息：`Java heap space`／`GC overhead limit exceeded` 是堆、`Metaspace` 是類別、`unable to create native thread` 是執行緒數、`direct buffer memory` 是堆外。排查順序：`jcmd Thread.print` → `GC.class_histogram` → heap dump；長期看 JFR。
*   類別載入三步是載入、連結、初始化；載入器三層是啟動、平台、應用程式（Java 9 起沒有 Extension），先問父載入器再自己找。JIT 靠直譯器找熱點、C1 先編再側寫、C2 深度最佳化，所以要暖機。

## 隨堂測驗

**Q1. 下列哪一組執行期資料區是「全部執行緒共用」的？**

- (A) 堆與方法區
- (B) JVM 堆疊與 pc 暫存器
- (C) 本機方法堆疊與 JVM 堆疊
- (D) pc 暫存器與方法區

<details><summary>看答案</summary>

**答案：(A)** 堆與方法區在 JVM 啟動時建立、所有執行緒共用，所以才需要垃圾回收與同步；JVM 堆疊、pc 暫存器、本機方法堆疊都是每條執行緒一份。

</details>

**Q2. HotSpot 把堆分成年輕代與老年代，主要依據是什麼？**

- (A) 弱分代假說：多數物件只活很短的時間，集中放一區頻繁回收最有效率
- (B) 物件大小：大物件放老年代、小物件放年輕代
- (C) 執行緒歸屬：各執行緒自己配置的物件放年輕代
- (D) 類別載入順序：先載入的類別實體放老年代

<details><summary>看答案</summary>

**答案：(A)** 分代的依據是多數物件只活很短的時間；分代讓回收器把力氣花在死亡率最高的 Eden，活過幾輪 Survivor 複製的才晉升老年代。物件大小只影響 G1 的巨型物件（humongous object，比半塊區域還大的物件）配置，不是分代的依據。

</details>

**Q3. Java 8 用 Metaspace 取代永久代（PermGen），直接解決了什麼問題？**

- (A) 類別中繼資料改放原生記憶體、預設不設上限，不必再手動調永久代大小
- (B) 字串字串池從堆搬到原生記憶體，減少堆的壓力
- (C) 類別中繼資料從此不需要垃圾回收
- (D) Metaspace 有固定上限，再也不會出現類別相關的 OutOfMemoryError

<details><summary>看答案</summary>

**答案：(A)** Java 8（JEP 122）移除永久代，所以不再需要調校它的大小；字串字串池與靜態變數反而是搬進堆。Metaspace 預設無上限，但類別載入器洩漏仍會撞到 OutOfMemoryError: Metaspace。

</details>

**Q4. HotSpot 為什麼能正確回收「兩個物件互相參考、但外面沒人指著它們」的情況？**

- (A) 因為它用可達性分析：從 GC Root 出發走不到的都是垃圾，互相參考與否無關
- (B) 因為它用參考計數：兩個物件的計數會同時歸零
- (C) 因為 finalize() 會在物件互相參考時被呼叫並解開參考
- (D) 因為弱參考會自動把循環參考中的一方清掉

<details><summary>看答案</summary>

**答案：(A)** 從任何活物件的參考都到達不了的物件就是垃圾。最單純的參考計數處理不了參考循環——這正是面試官要你對比的點。

</details>

**Q5. Java 9 之後在一台 8 核、32 GB 記憶體的伺服器上不加任何 GC 參數啟動 JVM，會用哪個回收器？如果換成只給 1 顆 CPU 的容器呢？**

- (A) 伺服器用 G1；1 顆 CPU 的容器用 Serial
- (B) 兩者都用 G1，Java 9 起無條件預設 G1
- (C) 伺服器用 Parallel；容器用 Serial
- (D) 兩者都用 ZGC，因為停頓最短

<details><summary>看答案</summary>

**答案：(A)** JEP 248 讓 G1 成為預設，但條件是伺服器級機器：兩顆以上處理器且記憶體大於等於 1792 MB，否則預設 Serial。ZGC 要自己開。

</details>

**Q6. G1 用哪一招讓停頓時間「可預期」？**

- (A) 把堆切成大小相等的區域，依成本模型決定每次停頓挑幾塊區域來回收，以達成 -XX:MaxGCPauseMillis 的目標
- (B) 完全不做 Stop-The-World，所有工作都與應用程式同時進行
- (C) 把整個堆一次壓縮整理，讓下次回收沒有碎片
- (D) 固定每 200 毫秒觸發一次完整回收

<details><summary>看答案</summary>

**答案：(A)** G1 仍在 Stop-The-World 停頓中搬物件，只是靠區域化與過去停頓的成本模型把每次停頓的工作量切到目標以內；預設目標 200 毫秒是上限目標，不是固定週期。完全不停頓的描述比較接近 ZGC 的宣傳，但它也還有極短停頓。

</details>

**Q7. 服務跑了兩天後丟出 OutOfMemoryError，訊息是「unable to create native thread: possibly out of memory or process/resource limits reached」，第一個該查的方向是？**

- (A) 執行緒數量：是否有執行緒池無上限地開執行緒，以及作業系統的行程執行緒上限與 -Xss
- (B) 調大 -Xmx，因為堆不夠放新物件
- (C) 調大 -XX:MaxMetaspaceSize，因為類別載入太多
- (D) 開 -XX:+HeapDumpOnOutOfMemoryError 等它再爆一次抓 heap dump

<details><summary>看答案</summary>

**答案：(A)** 這個訊息是作業系統拒絕建立原生執行緒，跟堆與 Metaspace 無關；而且 HeapDumpOnOutOfMemoryError 對原生執行緒建立失敗這類資源耗盡不生效。

</details>

**Q8. 在執行緒池環境下，為什麼用完 ThreadLocal 要呼叫 remove()？**

- (A) 因為值的壽命綁在執行緒上，池裡的執行緒不會結束，值就一直被持有、還會被下一個請求讀到
- (B) 因為 ThreadLocal 的值放在 Metaspace，不呼叫 remove() 會吃光類別空間
- (C) 因為 ThreadLocal 預設用強參考指著執行緒，會讓執行緒無法被回收
- (D) 因為不呼叫 remove() 的話，同一條執行緒下次呼叫 get() 會丟例外

<details><summary>看答案</summary>

**答案：(A)** 只要執行緒活著，它就對自己那份執行緒區域變數持有隱含參考；執行緒池的執行緒長期存活，值就跟著活，這是典型的「長壽物件抓著短命物件」洩漏。

</details>

**Q9. Java 9 之後，JDK 內建的三層類別載入器是哪三層？**

- (A) 啟動（bootstrap）、平台（platform）、應用程式（application，也叫系統類別載入器）
- (B) 啟動（bootstrap）、擴充（extension）、應用程式（application）
- (C) 啟動（bootstrap）、模組（module）、使用者（user）
- (D) 核心（core）、平台（platform）、自訂（custom）

<details><summary>看答案</summary>

**答案：(A)** 「Bootstrap、Extension、Application」是 Java 8 的答案；Java 9 起擴充機制（jre/lib/ext、java.ext.dirs）整個移除（JEP 220），中間那層是平台類別載入器。

</details>

**Q10. 為什麼 Java 服務剛啟動時比較慢、跑一陣子「暖機」後才到全速？**

- (A) 程式碼一開始由直譯器執行，要等熱點浮現、側寫收集夠，C1 再到 C2 逐層編譯完成才變快
- (B) 因為類別要全部載入完才開始執行任何位元碼
- (C) 因為 G1 要先做一次 Full GC 整理堆才能正常配置
- (D) 因為字串字串池要先把所有字面值 intern 完

<details><summary>看答案</summary>

**答案：(A)** HotSpot 先用直譯器啟動，執行中找出熱點再編譯；分層編譯讓 C1 先編出會自我側寫的版本，C2 最後產出深度最佳化版，這段過程就是暖機。類別載入是懶的，不會在啟動時全部載完。

</details>
