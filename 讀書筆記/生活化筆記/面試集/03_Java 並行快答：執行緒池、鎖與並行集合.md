# 03. Java 並行快答：執行緒池、鎖與並行集合

> 🏠 **生活化版本**：每個段落開頭的「生活比喻」先用日常情境帶你抓到感覺，接著再看原本的技術說明與程式碼；篇末有「比喻對照表」可以快速複習。

> 來源：[筆記平台 · 面試集](https://hhtim.github.io/notes-platform/interview/#/lesson/java-concurrency-qa)　第 3 課 / 共 23 課 · 約 13 分鐘

**平台對虛擬執行緒與 Thread.State 六種、ThreadPoolExecutor 七個參數與處理順序、四種拒絕策略與 Executors 的坑、池要多大、synchronized 對 ReentrantLock、volatile 與 happens-before、ABA 與 LongAdder、ConcurrentHashMap、Latch／Barrier／Semaphore、CompletableFuture、BlockingQueue 生產者消費者、死結排查——十四題以 Java 25 為準。**

### 讀完這課你會

*   分清平台執行緒與虛擬執行緒
*   背出執行緒池七個參數與處理順序
*   比較 synchronized、ReentrantLock、volatile
*   答出並行集合與死結怎麼抓

*【執行緒本身】*

## 從作業系統執行緒到虛擬執行緒，以及六種狀態

> 🏠 **生活比喻**
>
> - 平台執行緒＝**正職員工**，人數有限、很貴
> - 虛擬執行緒＝**大量臨時工**，等待時讓出座位

答題公式：先一句話定義，再講差別與取捨，最後補版本或實務註記。以下以 Java 25 為準，跟 Java 21 不同處會標出。

> 💡 面試官：行程與執行緒差在哪？Java 執行緒跟作業系統執行緒是什麼關係？虛擬執行緒改變了什麼？

**一句話定義**：基礎見〈執行緒與並行〉。每個行程有自己的記憶體空間；執行緒存在於行程之內，共用行程的資源，包括記憶體與開啟的檔案。[出處](https://docs.oracle.com/javase/tutorial/essential/concurrency/procthread.html)

**跟作業系統執行緒的關係**：Java 執行緒分兩種：

*   **平台執行緒（platform thread）**：通常與作業系統排程的核心執行緒一對一對應，可能是有限的資源。
*   **虛擬執行緒（virtual thread）**：由 Java 執行時、而非作業系統排程，一個 JVM 可以撐住數百萬條；適合大部分時間在等 I/O 的工作，不適合 CPU 密集運算。[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Thread.html)

**虛擬執行緒改變了什麼**：M:N 排程：大量（M）虛擬執行緒排到少量（N）作業系統執行緒上，承載它的平台執行緒叫載體（carrier）。Java 21 正式推出（JEP 444）。三句一定要答：

*   虛擬執行緒不是更快的執行緒，提供的是規模（更高吞吐量），不是速度（更低延遲）。
*   不要池化虛擬執行緒。
*   要限制並行數，改用專門為此設計的結構，例如 semaphore。[出處](https://openjdk.org/jeps/444)

**版本註記（21 與 25 答案不同）**：釘住（pinning）指虛擬執行緒阻塞時卸不下載體。

*   **Java 21**：在 `synchronized` 區塊或方法內阻塞會釘住。[出處](https://openjdk.org/jeps/444)
*   **Java 24**：JEP 491 改了 JVM，阻塞等待監視器時會卸載虛擬執行緒、把載體還給排程器。從此 `synchronized` 與 `java.util.concurrent.locks` 純粹看哪個最適合問題來選。[出處](https://openjdk.org/jeps/491)
*   **Java 25**：執行原生方法或外部函式時會被釘住。[出處](https://docs.oracle.com/en/java/javase/25/core/virtual-threads.html)
*   **其他**：類別載入與初始化時阻塞，還有少數情況會釘住，列為 JEP 491 的後續工作。[出處](https://openjdk.org/jeps/491)

> 虛擬執行緒換的是吞吐不是速度；不池化、用 Semaphore 限量；Java 24 起 synchronized 不再釘住載體

> 💡 面試官：執行緒有哪幾種狀態？

**一句話定義：**`Thread.State` 列舉六個。一條執行緒在任一時間點只在一個狀態；這些是虛擬機的狀態，不反映任何作業系統執行緒的狀態。[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Thread.State.html)

| 狀態 | 定義 | 怎麼進去 |
| --- | --- | --- |
| `NEW` | 尚未啟動 | `start()` 之前 |
| `RUNNABLE` | 正在 JVM 中執行，但可能在等作業系統的資源，例如處理器 | 沒有 RUNNING 狀態，排到 CPU 與否不區分 |
| `BLOCKED` | 等監視器鎖，以進入 `synchronized` 區塊／方法，或在 `Object.wait` 後重新進入（監視器鎖就是 `synchronized` 用的那把內建鎖） | 只有 `synchronized` |
| `WAITING` | 呼叫了無逾時的 `Object.wait`、無逾時的 `Thread.join`、`LockSupport.park` | 等 `ReentrantLock`、`take()` 這類工具，底層都是 `park` |
| `TIMED_WAITING` | 呼叫了帶正數等待時間的 `Thread.sleep`、有逾時的 `wait`／`join`、`parkNanos`、`parkUntil` | `sleep`、`tryLock(1, SECONDS)` |
| `TERMINATED` | 已完成執行 | `run()` 結束或丟出例外 |

**差別與取捨**：追問「等 `ReentrantLock` 是哪個狀態」答 `WAITING`，不是 `BLOCKED`：它靠 `LockSupport.park`，`BLOCKED` 只留給監視器鎖。[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Thread.State.html)

*【執行緒池】*

## 七個參數、一條處理順序、四種拒絕、多大才夠

> 🏠 **生活比喻**
>
> 執行緒池＝**外包工作室**：正職先做 → 滿了放工作籃 → 籃子滿了找臨時工 → 全滿就拒絕（四種拒絕方式：抱怨、叫你自己做、默默丟、丟最舊的）。

每個實驗的實跑輸出見〈執行緒池與並行工具〉。

> 💡 面試官：ThreadPoolExecutor 的參數有哪些？任務進來怎麼處理？

**一句話定義**：建構子七個參數：

*   `corePoolSize`：保留在池中的執行緒數，即使閒置也留著
*   `maximumPoolSize`：允許的最大執行緒數
*   `keepAliveTime`：超過核心數的閒置執行緒，最多等這麼久就結束
*   `unit`：`keepAliveTime` 的單位
*   `workQueue`：任務執行前存放的佇列
*   `threadFactory`：建執行緒
*   `handler`：執行緒與佇列都到頂時的拒絕處理器[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ThreadPoolExecutor.html)

**處理順序三條：**

*   少於 `corePoolSize`：一律新開執行緒，不排隊；即使其他執行緒閒置也照開。
*   已達 `corePoolSize`：一律先排隊，不新開執行緒。
*   排不進佇列：才新開執行緒；會超過 `maximumPoolSize` 時，任務被拒絕。[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ThreadPoolExecutor.html)

答成「先加到最大再排隊」是反的。

> 核心沒滿就開執行緒，核心滿了先排隊，佇列滿了才加到最大，最大也滿了才拒絕

批次對帳的池可以這樣建：

```
int cores = Runtime.getRuntime().availableProcessors();
ThreadFactory factory = Thread.ofPlatform().name("reconcile-", 0).factory();
ExecutorService pool = new ThreadPoolExecutor(
        cores,                                  // corePoolSize：常駐執行緒數
        cores * 2,                              // maximumPoolSize：佇列滿了最多加到這麼多
        60, TimeUnit.SECONDS,                   // keepAliveTime 與 unit：多出來的閒置執行緒活多久
        new ArrayBlockingQueue<>(1_000),        // workQueue：有界佇列，滿了才會加執行緒
        factory,                                // threadFactory：執行緒命名，thread dump（把每條執行緒當下在跑什麼、等什麼全部印出來）才認得出來
        new ThreadPoolExecutor.CallerRunsPolicy()); // handler：塞不進去就由呼叫端自己跑
```

**實務註記（佇列決定一切）**：三種佇列策略：

*   **直接交遞（`SynchronousQueue`）**：通常要配無上限的 `maximumPoolSize`，執行緒可能無上限成長。
*   **無界佇列（沒給容量的 `LinkedBlockingQueue`）**：永遠不會建立超過 `corePoolSize` 的執行緒，`maximumPoolSize` 因此沒有作用；佇列可能無上限成長。
*   **有界佇列（`ArrayBlockingQueue`）**：有助於避免資源耗盡，但較難調校。[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ThreadPoolExecutor.html)

> 💡 面試官：四種拒絕策略？為什麼常聽到「不要用 Executors 的工廠方法」？

| 策略 | 行為 | 什麼時候選 |
| --- | --- | --- |
| `AbortPolicy`（預設） | 丟出 `RejectedExecutionException` | 寧可失敗也不能默默丟，例如轉帳 |
| `CallerRunsPolicy` | 呼叫 `execute` 的執行緒自己執行該任務；簡單的回饋控制，會減慢新任務提交的速度 | 批次工作：呼叫端被拖慢就是自動減速 |
| `DiscardPolicy` | 直接丟掉；只適合極少數從不依賴任務完成的情況 | 可丟的統計、心跳 |
| `DiscardOldestPolicy` | 丟掉佇列最前面的任務再重試；很少能接受 | 幾乎不選 |

出處：[ThreadPoolExecutor 文件](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ThreadPoolExecutor.html)

**工廠方法怎麼答才準：**`ThreadPoolExecutor` 的 Javadoc 本身鼓勵改用更方便的 `Executors` 工廠方法[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ThreadPoolExecutor.html)，所以答「知道預設值再用」。

工廠方法的預設值：[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/Executors.html)

*   **fixed 與 single**：`newFixedThreadPool` 與 `newSingleThreadExecutor` 用的是無界佇列
*   **cached**：`newCachedThreadPool` 視需要建立新執行緒，六十秒沒用到的會被終止

OpenJDK 原始碼裡的實際值：[出處](https://github.com/openjdk/jdk/blob/master/src/java.base/share/classes/java/util/concurrent/Executors.java)

*   **fixed**：`new LinkedBlockingQueue<>()`（容量 `Integer.MAX_VALUE`）
*   **cached**：`maximumPoolSize = Integer.MAX_VALUE` 配 `SynchronousQueue`

結論：fixed 與 single 在任務湧入時佇列吃光堆（`Java heap space`）；cached 是執行緒無上限（`unable to create native thread`），兩種錯見〈Java 進階快答：JVM 記憶體、垃圾回收與類別載入〉。對帳池用有界佇列加 `CallerRunsPolicy`，兩個洞一起堵。

> 💡 面試官：執行緒池要開多大？

**一句話定義**：沒有官方公式，只有通則：CPU 密集約等於核心數，I/O 密集可以多很多。

核心數用 `Runtime.availableProcessors()`，回傳 JVM 可用的處理器數[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Runtime.html)。

Linux 容器裡 JVM 預設開著容器支援（`-XX:+UseContainerSupport`），會判斷 docker 容器內的 Java 行程可用的記憶體量與處理器數[出處](https://docs.oracle.com/en/java/javase/25/docs/specs/man/java.html)；前提是容器有設 CPU 上限才回傳上限；沒設上限時一般就是主機核心數（這半句是推論，java 指令手冊沒明寫）。

**差別與取捨**：任務常阻塞（例如 I/O 密集）時，系統排得動的執行緒可能比你設的上限還多。[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ThreadPoolExecutor.html) 面試常聽到的估算式「執行緒數約等於核心數乘上（1 加 等待時間除以計算時間）」出自並行程式設計教材，不是 Java 官方給的，只是起點，要靠壓測與監控修正。

**版本註記**：Java 21 起 I/O 密集的另一個答案是不估：`Executors.newVirtualThreadPerTaskExecutor()` 為每個任務啟動一條新的虛擬執行緒，建立的執行緒數無上限[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/Executors.html)，要限的是下游承受量，用 `Semaphore`。

*【鎖與記憶體模型】*

## synchronized、ReentrantLock、volatile 與 CAS（比較並交換）

> 🏠 **生活比喻**
>
> - synchronized＝**廁所門鎖**
> - ReentrantLock＝**功能更多的智慧門鎖**
> - volatile＝**數字只寫在公告欄**，大家都看最新的
> - CAS＝**改白板前先確認舊值沒變**

> 💡 面試官：synchronized 與 ReentrantLock 差在哪？什麼是公平鎖、可中斷、條件變數？

**一句話定義**：基礎見〈執行緒與並行〉。`ReentrantLock` 與 `synchronized` 所用的隱含監視器鎖，基本行為與語意相同，但多了擴充能力[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/locks/ReentrantLock.html)：結構更靈活，一把鎖可以關聯多個 `Condition` 物件。[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/locks/Lock.html)

|   | `synchronized` | `ReentrantLock` |
| --- | --- | --- |
| 取鎖與解鎖 | 進出區塊自動 | 手動；`lock` 後立刻接 `try`，`unlock` 當 `finally` 第一句[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/locks/ReentrantLock.html) |
| 限時、可中斷 | 沒有，拿不到就一直等 | `tryLock(時間)`、`lockInterruptibly()`（等鎖時可被 `interrupt()` 叫醒） |
| 公平鎖 | 沒有 | `new ReentrantLock(true)`：競爭時偏好等最久的執行緒，保證不會飢餓；代價是吞吐量較低（常常慢很多）；`tryLock()` 不遵守公平設定[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/locks/ReentrantLock.html) |
| 條件變數 | 一個物件一組 `wait`／`notify` | `Condition` 把 `wait`、`notify` 拆成獨立物件，一個物件可以有多個等待集合[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/locks/Condition.html)，例如「非滿」與「非空」分開等 |
| dump 狀態 | `BLOCKED` | `WAITING` |

兩者都可重入（同一條執行緒可以再拿一次自己已經握著的鎖）。轉帳要同時鎖兩個帳戶：`tryLock` 帶逾時加固定取鎖順序，一次破壞死結兩個條件：

```
static boolean transfer(Account from, Account to, long amount) throws InterruptedException {
    Account first = from.id < to.id ? from : to;   // 一律照帳號大小拿鎖：破壞循環等待
    Account second = (first == from) ? to : from;
    if (!first.lock.tryLock(1, TimeUnit.SECONDS)) return false;   // 等不到就放棄，不是死等
    try {
        if (!second.lock.tryLock(1, TimeUnit.SECONDS)) return false;
        try {
            if (from.balance < amount) return false;
            from.balance -= amount;
            to.balance += amount;
            return true;
        } finally {
            second.lock.unlock();   // 解鎖一定放 finally
        }
    } finally {
        first.lock.unlock();
    }
}
```

**選型**：先用 `synchronized`：寫法短、忘不了解鎖；要限時、可中斷、公平或多個條件才換 `ReentrantLock`。

> 💡 面試官：volatile 保證什麼、不保證什麼？happens-before 是什麼？

**一句話定義**：欄位宣告成 `volatile`，Java 記憶體模型確保所有執行緒看到該變數一致的值。[出處](https://docs.oracle.com/javase/specs/jls/se25/html/jls-8.html#jls-8.3.1.4) 「一致」的定義就是 happens-before（先行發生）：一個動作 happens-before 另一個，第一個就對第二個可見、且排在它之前。[出處](https://docs.oracle.com/javase/specs/jls/se25/html/jls-17.html#jls-17.4.5)

**規則：**

*   對 `volatile` 欄位的寫入，happens-before 之後每一次對該欄位的讀取。
*   監視器的解鎖，happens-before 之後每一次對同一監視器的上鎖。
*   `start()` 與 `join()` 也各建立一條。[出處](https://docs.oracle.com/javase/specs/jls/se25/html/jls-17.html#jls-17.4.5)

因為可傳遞，寫 `volatile` 旗標之前寫的普通變數，讀到旗標的執行緒也都看得到，這是 `volatile` 真正的用處。**不保證**原子性：`count++` 仍是三步，「先檢查再動作」要鎖或原子類別。

**加分句**：happens-before 也延伸到 `java.util.concurrent` 的高階工具：`Lock.unlock`、`Semaphore.release`、`CountDownLatch.countDown` 之前的動作，happens-before 對應的成功 `acquire` 之後的動作。[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/package-summary.html#MemoryVisibility) 透過這些工具交手的資料不必再加 `volatile`。

> 💡 面試官：CAS 的 ABA 問題是什麼？AtomicInteger 與 LongAdder 怎麼選？

**一句話定義**：CAS（compare-and-swap，比較並交換）基礎見〈執行緒與並行〉。ABA 是通則名詞，不是 Java 官方用語：值從 A 變 B 又變回 A，CAS 只比「現在是不是 A」，誤判成沒人動過。數字計數器無害，「參考加狀態」有害。解法是 `AtomicStampedReference`：同時維護一個物件參考與一個整數「戳記」，兩者原子地一起更新[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/atomic/AtomicStampedReference.html)，戳記當版本號。

**差別與取捨：**

*   **`AtomicInteger`**：可原子更新的 `int`，用在原子遞增的計數器[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/atomic/AtomicInteger.html)；競爭激烈時大家在同一個位址反覆 CAS 失敗重試。
*   **`LongAdder`**：多條執行緒更新一個用於統計、而非精細同步控制的共用總和時，通常比 `AtomicLong` 好；高競爭時吞吐量顯著較高，代價是多用一些空間。[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/atomic/LongAdder.html)

`LongAdder` 的原理是把總和拆成多個格子分散競爭，`sum()` 時再加總。

> 要拿「更新後的值」立刻做決定（發序號、判斷扣到沒）用 Atomic；只要累計統計（處理筆數、失敗數）用 LongAdder

*【並行集合與協調工具】*

## ConcurrentHashMap、三個同步輔助類別、CompletableFuture、BlockingQueue

> 🏠 **生活比喻**
>
> - ConcurrentHashMap＝**每個置物櫃各有一把鎖**
> - CountDownLatch＝**發射倒數**
> - Semaphore＝**停車位看板**
> - CyclicBarrier＝**旅行團集合點**

> 💡 面試官：ConcurrentHashMap 怎麼做到高並行？Java 8 之後結構變成什麼？

**一句話定義：**

*   所有操作都是執行緒安全的，但讀取不加鎖，也不支援鎖住整張表。
*   讀取（含 `get`）一般不阻塞，可與更新重疊。
*   讀取反映的是它開始時、最近已完成的更新結果。[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ConcurrentHashMap.html)

**Java 8 之後的結構：**

*   在空桶插入第一個節點，只靠 CAS。
*   其他更新要鎖。為了不替每個桶配一個鎖物件，直接拿桶裡的第一個節點當鎖，用內建的 `synchronized` 監視器。
*   桶太長轉紅黑樹（一種會自己保持平衡的搜尋樹；原始碼叫 `TreeBin`）。
*   Java 7 的 `Segment` 只剩相容用途：平常沒用到，只在序列化時建立。[出處](https://github.com/openjdk/jdk/blob/master/src/java.base/share/classes/java/util/concurrent/ConcurrentHashMap.java)

所以「16 個 Segment」是 Java 7 的答案，現在是「CAS 加桶級 `synchronized`」。

**實務註記**：不允許 `null` 當鍵或值；「先 `get` 再 `put`」兩次呼叫之間會被插隊，用 `computeIfAbsent`、`merge`、`compute` 一次做完。拿它當可擴充的頻率表：`freqs.computeIfAbsent(key, k -> new LongAdder()).increment()`。[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ConcurrentHashMap.html) 〈系統設計：秒殺與限流〉的單機本地計數就用這一行。

> 💡 面試官：CountDownLatch、CyclicBarrier、Semaphore 各解決什麼？

| 類別 | 定義 | 關鍵性質 | 銀行情境 |
| --- | --- | --- | --- |
| `CountDownLatch` | 讓一或多條執行緒等待其他執行緒的一組操作完成 | 一次性，計數不能重設；要重設用 `CyclicBarrier`[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CountDownLatch.html) | 主執行緒 `await`，等 8 個對帳分片各 `countDown` 才出總表 |
| `CyclicBarrier` | 讓一組執行緒全部互相等待，直到到達共同的屏障點 | 叫 cyclic 是因為釋放後可重用；可帶一個動作，在最後一條到達後、釋放前執行一次[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CyclicBarrier.html) | 多輪計算，每輪全部算完才進下一輪 |
| `Semaphore` | 維護一組許可（permits）：`acquire` 在有許可前阻塞、然後取走一個，`release` 加回一個；常用來限制能存取某資源的執行緒數 | 沒有擁有者：釋放許可的執行緒，不必是取得那個許可的執行緒[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/Semaphore.html) | 核心帳務一次只接 20 個查詢就開 20 個許可；虛擬執行緒用它取代「拿池限流」 |

> Latch 是「等別人做完」，Barrier 是「大家互等」，Semaphore 是「限量放行」

> 💡 面試官：CompletableFuture 跟 Future 差在哪？怎麼組合非同步任務？

**一句話定義：**

*   **`Future`**：代表非同步計算的結果，只能在計算完成後用 `get` 取得，必要時阻塞到就緒[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/Future.html)。只能等，不能「完成時通知我」、不能串接合併。
*   **`CompletableFuture`**：可以明確完成的 `Future`，也是 `CompletionStage`，支援在完成時觸發的相依函式與動作。[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CompletableFuture.html)

**怎麼組合**：串接用 `thenApply`、`thenCompose`（下一步也是非同步）；兩個合一用 `thenCombine`；多個用 `allOf`；錯誤用 `exceptionally`；逾時用 `orTimeout`（逾時未完成，就以 `TimeoutException` 結束）；取結果用 `join`，不丟受檢例外。[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CompletableFuture.html) 授信查核同時問餘額與額度：

```
CompletableFuture<Balance> balance =
        CompletableFuture.supplyAsync(() -> coreBanking.balance(account), pool); // 指定自己的池，不用 common pool
CompletableFuture<Limit> limit =
        CompletableFuture.supplyAsync(() -> risk.limit(account), pool);
return balance.thenCombine(limit, CreditCheck::decide)       // 兩個結果都到了才合併
        .orTimeout(2, TimeUnit.SECONDS)                         // 超過兩秒以 TimeoutException 結束
        .exceptionally(ex -> {
            // 上游丟出的例外會被包成 CompletionException，先拆一層才看得到真正原因；逾時的 TimeoutException 不會被包
            Throwable cause = (ex instanceof CompletionException && ex.getCause() != null) ? ex.getCause() : ex;
            return Decision.reject("查詢失敗：" + cause.getClass().getSimpleName());
        })
        .join();                                                // 等結果；失敗已在上一段轉成 Decision
```

**實務註記（最常被問倒的坑）：**

*   **預設跑在 common pool**：沒有明確傳 `Executor` 參數的 async 方法，都在 `ForkJoinPool.commonPool()` 執行[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CompletableFuture.html)
*   **common pool 的平行度**（同時在跑的工作執行緒數）：預設是可用處理器數減一、最少 1（OpenJDK 原始碼：`pc = Math.max(1, Runtime.getRuntime().availableProcessors() - 1)`）[出處](https://github.com/openjdk/jdk/blob/master/src/java.base/share/classes/java/util/concurrent/ForkJoinPool.java)
*   **自己建的池**：自己 `new ForkJoinPool()`，平行度預設才等於可用處理器數[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ForkJoinPool.html)

它是整個 JVM 共用的，拿它跑阻塞 I/O，幾個慢請求就卡住全 JVM 的非同步工作，所以範例都傳自己的池。

> 💡 面試官：生產者消費者用 BlockingQueue 怎麼寫？

**一句話定義：**

*   `BlockingQueue` 取元素時等佇列變成非空、放元素時等有空間，主要用在生產者消費者佇列。
*   不接受 `null`。
*   本身不支援 close 或 shutdown；要收工，就由生產者放入特殊的結束物件（poison object）。[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/BlockingQueue.html)

| 做不到時 | 放入 | 取出 |
| --- | --- | --- |
| 丟例外 | `add(e)` | `remove()` |
| 回傳特殊值（`false`／`null`） | `offer(e)` | `poll()` |
| 阻塞 | `put(e)` | `take()` |
| 阻塞到逾時 | `offer(e, time, unit)` | `poll(time, unit)` |

出處：[BlockingQueue 文件](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/BlockingQueue.html)

生產者消費者要的是「阻塞」那一列，不必自己 `wait`／`notify`。對帳檔多執行緒入帳的骨架：

```
private static final String END = new String("__END__");   // 結束物件：new 出來的獨一物件，比對「是不是同一個物件」而不是內容；不用字面值，因為字面值會進字串池、別處同樣的字面值會是同一個物件
BlockingQueue<String> queue = new ArrayBlockingQueue<>(100);   // 有界：生產者太快就會被 put 擋住

Thread producer = Thread.ofPlatform().start(() -> {
    try {
        for (String line : lines) queue.put(line);              // 滿了就等，不丟資料
        for (int i = 0; i < consumers; i++) queue.put(END);     // 每個消費者發一個結束物件
    } catch (InterruptedException e) {
        Thread.currentThread().interrupt();
    }
});

for (int i = 0; i < consumers; i++) {
    Thread.ofPlatform().start(() -> {
        try {
            while (true) {
                String line = queue.take();                     // 空了就等，不會空轉耗 CPU
                if (line == END) break;                         // 比同一性不比內容：資料列剛好是 "__END__" 也照常處理
                process(line);
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    });
}
```

**選哪個實作**（三種正好對應執行緒池那題的三種佇列策略）：

*   **`ArrayBlockingQueue`**：以陣列實作的有界阻塞佇列，經典的有界緩衝[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ArrayBlockingQueue.html)
*   **`LinkedBlockingQueue`**：可選有界，未指定容量就是 `Integer.MAX_VALUE`[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/LinkedBlockingQueue.html)
*   **`SynchronousQueue`**：沒有任何內部容量，連一個都沒有[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/SynchronousQueue.html)

放進去之前的動作 happens-before 另一執行緒取出之後的動作。[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/BlockingQueue.html)

*【出事了怎麼查】*

## ThreadLocal 洩漏、死結排查、活鎖與飢餓

> 🏠 **生活比喻**
>
> - ThreadLocal 洩漏＝**員工抽屜沒清，下一個任務看到別人的東西**
> - 死結＝**兩人各拿一支筷子互等**
> - 活鎖＝**兩人在走廊一直互相讓路，結果誰都過不去**

> 💡 面試官：ThreadLocal 用在哪？為什麼會洩漏？

**一句話定義**：每條存取它的執行緒都有自己獨立初始化的副本；通常宣告成 `private static` 欄位，把狀態綁在執行緒上（例如使用者 ID 或交易 ID）。[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/ThreadLocal.html) 另一個用途是快取非執行緒安全的物件，例如 `SimpleDateFormat`。[出處](https://docs.oracle.com/en/java/javase/25/core/virtual-threads.html)

**洩漏**：池裡的執行緒不會死，副本一直掛著，用完一定 `remove()`；原理與排查見〈Java 進階快答：JVM 記憶體、垃圾回收與類別載入〉。[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/ThreadLocal.html)

**版本註記**：這種快取只在執行緒被多個任務重複使用時有幫助；虛擬執行緒從不池化、從不被不相關的任務重用，快取失去意義。[出處](https://docs.oracle.com/en/java/javase/25/core/virtual-threads.html)

> 💡 面試官：死結的四個條件？線上服務卡住怎麼確認是死結？活鎖、飢餓是什麼？

**一句話定義**：死結是兩條以上執行緒永遠阻塞、互相等待。[出處](https://docs.oracle.com/javase/tutorial/essential/concurrency/deadlock.html) 四個條件（互斥、持有並等待、不可搶占、循環等待）是作業系統教科書的通則（Coffman 條件），不是 Java 官方用語[出處](https://en.wikipedia.org/wiki/Deadlock_(computer_science))，解釋見〈執行緒與並行〉。預防就是破壞其中一條：固定取鎖順序破壞循環等待，`tryLock` 帶逾時破壞持有並等待，轉帳範例兩招都用了。

**怎麼確認**：印出 thread dump 之後，HotSpot VM 會跑死結偵測演算法；偵測到就印 `Found one Java-level deadlock:`，下面列出誰 `waiting to lock` 哪個監視器、`which is held by` 誰。[出處](https://docs.oracle.com/en/java/javase/25/troubleshoot/troubleshoot-process-hangs-loops.html)

拿 dump 兩條路：

*   **送訊號**：主控台按 `Control+\` 或 `kill -QUIT pid`[出處](https://docs.oracle.com/en/java/javase/25/troubleshoot/troubleshoot-process-hangs-loops.html)
*   **jcmd**：`jcmd <pid> Thread.print -l`（印出所有執行緒與堆疊，`-l` 加印 `java.util.concurrent` 的鎖）[出處](https://docs.oracle.com/en/java/javase/25/docs/specs/man/jcmd.html)

先看 CPU：吃光 CPU 比較可能是迴圈，不是死結。[出處](https://docs.oracle.com/en/java/javase/25/troubleshoot/troubleshoot-process-hangs-loops.html)

**活鎖與飢餓：**[出處](https://docs.oracle.com/javase/tutorial/essential/concurrency/starvelive.html)

*   **飢餓**（starvation）：執行緒無法定期取得共用資源而無法推進，成因是貪心的執行緒長期佔住資源
*   **活鎖**（livelock）：執行緒沒有被阻塞，只是忙著回應彼此而無法繼續工作

怎麼解：

*   **搶同一把鎖的飢餓**：用公平鎖，`ReentrantLock` 的公平模式保證不會飢餓；但鎖的公平不保證執行緒排程的公平[出處](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/locks/ReentrantLock.html)
*   **其他飢餓**：要縮短持鎖時間；典型例子是 `synchronized` 方法常常要很久才回傳[出處](https://docs.oracle.com/javase/tutorial/essential/concurrency/starvelive.html)
*   **活鎖**：常見解法是重試時加隨機等待（通則）。

> 卡住先看 CPU：滿載是迴圈、閒著才是死結；再 jcmd Thread.print 找 Found one Java-level deadlock

### 🗺️ 比喻對照表

| 技術名詞 | 生活比喻 |
| --- | --- |
| 執行緒池 | 外包工作室 |
| volatile | 只寫在公告欄 |
| CAS | 改前確認舊值 |
| 死結 / 活鎖 | 各拿一支筷子 / 走廊互讓 |

### 重點整理

*   虛擬執行緒由 JVM 排程、M:N 掛在載體上，換吞吐不換速度，不池化、用 `Semaphore` 限量；Java 24 起（JEP 491）`synchronized` 不再釘住載體。
*   `Thread.State` 六種；`BLOCKED` 只給 `synchronized`，等 `java.util.concurrent` 的鎖與工具是 `WAITING`（帶逾時的是 `TIMED_WAITING`）。
*   執行緒池順序是核心、佇列、最大、拒絕；無界佇列讓 `maximumPoolSize` 失效。`newFixedThreadPool` 吃堆、`newCachedThreadPool` 執行緒無上限；批次選有界佇列加 `CallerRunsPolicy`。
*   `ReentrantLock` 多了限時、可中斷、公平、多個 `Condition`。`volatile` 靠 happens-before 給可見性與順序，不給原子性。
*   ABA 用 `AtomicStampedReference`；統計計數選 `LongAdder`。`ConcurrentHashMap` 讀不加鎖，寫是 CAS 加桶級 `synchronized`，複合操作用 `compute` 家族。
*   Latch 等別人做完、Barrier 大家互等、Semaphore 限量放行；`CompletableFuture` 跑阻塞 I/O 傳自己的池；`BlockingQueue` 用 `put`／`take` 加結束物件。
*   卡住先看 CPU，再 `jcmd Thread.print` 找 `Found one Java-level deadlock`；`ThreadLocal` 用完 `remove()`。

## 隨堂測驗

**Q1. 一個 ThreadPoolExecutor 設 corePoolSize 4、maximumPoolSize 8、佇列容量 100。目前 4 條執行緒都在忙、佇列裡有 10 個任務，這時再提交一個任務會怎樣？**

- (A) 進佇列排隊，不會新開執行緒
- (B) 立刻新開第 5 條執行緒處理它
- (C) 被拒絕，交給 RejectedExecutionHandler
- (D) 由呼叫端自己執行

<details><summary>看答案</summary>

**答案：(A)** 已達 corePoolSize 時，一律先排隊、不新開執行緒；只有佇列滿了才會加到 maximumPoolSize，最大也滿了才拒絕。

</details>

**Q2. 批次對帳一次提交五十萬個任務給 Executors.newFixedThreadPool(8)，最可能先撞到哪個問題？**

- (A) 任務堆在無界佇列裡吃光堆，出現 OutOfMemoryError: Java heap space
- (B) 執行緒無上限成長，出現 unable to create native thread
- (C) 超出 8 條執行緒的任務被 AbortPolicy 拒絕
- (D) 池會自動擴到 maximumPoolSize 把任務跑完

<details><summary>看答案</summary>

**答案：(A)** newFixedThreadPool 用的是共用的無界佇列，原始碼裡是沒給容量的 LinkedBlockingQueue；執行緒數固定 8 條，堆積的是任務物件。執行緒無上限是 newCachedThreadPool 的問題。

</details>

**Q3. thread dump 裡看到很多執行緒是 WAITING（parking），堆疊停在 ReentrantLock.lock()；另一批是 BLOCKED。這兩批各在等什麼？**

- (A) WAITING 那批在等 ReentrantLock 這類鎖，BLOCKED 那批在等 synchronized 的監視器鎖
- (B) 兩批都在等 synchronized 的監視器鎖，等得比較久的那批被 JVM 改標成 WAITING
- (C) WAITING 那批在等作業系統把 CPU 排給它，BLOCKED 那批在等磁碟或網路 I/O 回來
- (D) WAITING 那批已經拿到鎖正在跑臨界區，BLOCKED 那批是還沒呼叫 start() 的新執行緒

<details><summary>看答案</summary>

**答案：(A)** BLOCKED 是等監視器鎖、以進入 synchronized 區塊；WAITING 的來源是 Object.wait、Thread.join 或 LockSupport.park，ReentrantLock 靠的是 park。等 CPU 的執行緒是 RUNNABLE。

</details>

**Q4. 把共用計數器宣告成 volatile int count，多條執行緒同時 count++，結果會正確嗎？**

- (A) 不會，volatile 只保證可見性與順序（happens-before），count++ 仍是讀、算、寫三步
- (B) 會，volatile 讓每次寫入立刻對所有執行緒可見，所以遞增不會遺失
- (C) 會，volatile 欄位的所有操作都是原子的
- (D) 不會，因為 volatile 變數不能在多執行緒間共用

<details><summary>看答案</summary>

**答案：(A)** volatile 只保證對該欄位的寫入 happens-before 之後每一次讀取，沒有讓複合動作變成不可分割；要正確計數用 AtomicInteger、LongAdder 或鎖。

</details>

**Q5. 轉帳服務把鎖改成 new ReentrantLock(true) 公平模式後，應該預期什麼？**

- (A) 整體吞吐量下降，但等最久的執行緒優先拿到鎖、不會飢餓；不帶時間的 tryLock() 仍會插隊
- (B) 吞吐量上升，因為鎖的分配更有秩序
- (C) 死結從此不會發生，因為所有執行緒照順序取鎖
- (D) tryLock() 也會照排隊順序等待，不再立刻回傳

<details><summary>看答案</summary>

**答案：(A)** 公平鎖保證不會飢餓，代價是吞吐量較低（常常慢很多）；不帶時間的 tryLock() 不遵守公平設定；公平與死結無關。

</details>

**Q6. 要統計對帳批次「已處理筆數」給監控看，幾十條執行緒高頻遞增、偶爾讀一次總數。AtomicLong 與 LongAdder 選哪個，為什麼？**

- (A) LongAdder：高競爭下吞吐量顯著較高，統計用途不需要每次拿到精確的更新後值
- (B) AtomicLong：LongAdder 不是執行緒安全的
- (C) AtomicLong：因為 LongAdder 的 sum() 需要加鎖，讀取太慢
- (D) 兩者一樣，LongAdder 只是 AtomicLong 的別名

<details><summary>看答案</summary>

**答案：(A)** 多條執行緒更新用於統計、而非精細同步控制的共用總和時，LongAdder 通常比 AtomicLong 好；要靠遞增後的值立刻做決定（發序號）才選 Atomic。

</details>

**Q7. 用 ConcurrentHashMap 做每個使用者的請求計數，寫成「Integer n = map.get(user); map.put(user, n == null ? 1 : n + 1);」，問題在哪？**

- (A) get 與 put 是兩次獨立呼叫，中間別的執行緒可能插隊，計數會遺失；應改用 merge 或 compute 一次完成
- (B) ConcurrentHashMap 的 get 需要鎖整張表，效能太差
- (C) ConcurrentHashMap 不允許 Integer 當值
- (D) 沒有問題，ConcurrentHashMap 的所有操作都是執行緒安全的，包含這兩行的組合

<details><summary>看答案</summary>

**答案：(A)** 單一操作執行緒安全不等於「先讀再寫」的組合原子；例如用 computeIfAbsent 配 LongAdder 的 increment，一次呼叫做完。

</details>

**Q8. 主執行緒要等 8 個分片各自對帳完才產出總表，而且這件事整批只做一次。CountDownLatch 與 CyclicBarrier 選哪個？**

- (A) CountDownLatch(8)：主執行緒 await，各分片完成時 countDown，一次性不需重設
- (B) CyclicBarrier(8)：因為它可以重用，比較保險
- (C) Semaphore(8)：讓 8 個分片同時拿許可
- (D) CyclicBarrier(9)：主執行緒也算一方一起等

<details><summary>看答案</summary>

**答案：(A)** CountDownLatch 讓一或多條執行緒等待其他執行緒的一組操作完成，而且是一次性的，計數不能重設；CyclicBarrier 是一組執行緒互相等待並可重用，多輪迭代才需要。

</details>

**Q9. Java 21 把請求處理改成虛擬執行緒後，下游核心帳務只能同時接 20 個請求。應該怎麼限制？**

- (A) 不要池化虛擬執行緒，改用 Semaphore(20) 限制同時進入下游的數量
- (B) 改成 Executors.newFixedThreadPool(20) 的虛擬執行緒池
- (C) 把虛擬執行緒調成更高優先權，讓它們更快跑完
- (D) 不用限制，虛擬執行緒本身比平台執行緒快

<details><summary>看答案</summary>

**答案：(A)** 不要池化虛擬執行緒，限流改用專門為此設計的結構，例如 semaphore；虛擬執行緒也不是更快的執行緒，而且虛擬執行緒的優先權固定不能改。

</details>

**Q10. 線上服務無回應、CPU 幾乎是零。最直接確認是不是死結的做法是？**

- (A) 拿 thread dump，看 HotSpot 有沒有印出「Found one Java-level deadlock」
- (B) 先重啟服務讓對外功能恢復，之後幾天盯著監控看會不會再卡一次，重現了才值得開始查原因
- (C) 調大執行緒池的 maximumPoolSize，讓更多執行緒接手，卡住的那幾條自然就會被繞過
- (D) 用 jcmd GC.heap_dump 抓 heap dump，從物件之間的參考鏈找出是誰卡住了誰

<details><summary>看答案</summary>

**答案：(A)** 印出 thread dump 之後，HotSpot VM 會跑死結偵測演算法，偵測到就印出死結與相關堆疊；CPU 閒著才像死結，吃光 CPU 反而像迴圈。heap dump 是查記憶體問題的工具。

</details>
