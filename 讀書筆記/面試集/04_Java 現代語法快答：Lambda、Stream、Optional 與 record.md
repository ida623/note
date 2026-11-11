# 04. Java 現代語法快答：Lambda、Stream、Optional 與 record

> 來源：[筆記平台 · 面試集](https://hhtim.github.io/notes-platform/interview/#/lesson/java-modern-qa)　第 4 課 / 共 23 課 · 約 18 分鐘

**Lambda 與函式介面、方法參考、Stream 的惰性與只能用一次、平行流的坑、Optional 該怎麼用、var、record、sealed 與 switch 模式比對，每題一句話定義再指回教材。**

### 讀完這課你會

*   答出 lambda 跟匿名類別的差別
*   講清 Stream 的惰性求值與常見地雷
*   判斷平行流與 Optional 該不該用
*   說出 record、var、sealed 各解決什麼

*【Lambda 與函式介面】*

## lambda 從哪來、能抓什麼

答題公式：先一句話定義，再講差別與取捨，最後補版本註記。以下以 Java 21 為準，Java 22 之後的差異另外標。

> 💡 面試官：lambda 跟匿名類別差在哪？

**一句話定義**：lambda 是只留參數與本體的匿名方法，用來實作函式介面那唯一的抽象方法；在某些情況下，它是寫匿名類別實例的另一種、更簡單的方式。[出處](https://dev.java/learn/language/fp/lambdas/first-lambdas/)

**差別一，this 指誰**：匿名類別是一個新類別，裡面的 `this` 指那個匿名物件；lambda 本體裡的名稱與 `this`、`super` 跟周圍的程式碼意義相同。[出處](https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html#jls-15.27.2)

**差別二，編譯方式（點到即可）**：匿名類別會多編出一個 `外層$1.class`；lambda 不會，本體編成外層類別裡的私有方法（javac 的做法，Java 21 實測），執行時才由 `invokedynamic` 指令透過 `LambdaMetafactory` 產生實作物件；`LambdaMetafactory` 的方法通常當作 `invokedynamic` 呼叫點的啟動方法，用來支援 lambda 運算式與方法參考。[出處](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/invoke/LambdaMetafactory.html)

```
public class ThisDemo {
    String name = "外層物件";

    void run() {
        Runnable anon = new Runnable() {
            String name = "匿名類別物件";
            public void run() { System.out.println("匿名類別：" + this.name); }
        };
        Runnable lambda = () -> System.out.println("lambda：" + this.name);
        anon.run();
        lambda.run();
    }

    public static void main(String[] args) {
        new ThisDemo().run();
    }
}
```

```
匿名類別：匿名類別物件
lambda：外層物件

$ javac -d out ThisDemo.java && ls out
ThisDemo.class
ThisDemo$1.class
$ javap -c -p -cp out ThisDemo | grep -E 'invokedynamic|lambda\$'
      10: invokedynamic #20,  0             // InvokeDynamic #0:run:(LThisDemo;)Ljava/lang/Runnable;
  private void lambda$run$0();
       7: invokedynamic #36,  0             // InvokeDynamic #1:makeConcatWithConstants:(Ljava/lang/String;)Ljava/lang/String;
```

只有匿名類別多了 `ThisDemo$1.class`；lambda 的本體編成私有方法 `lambda$run$0`（javac 的做法，Java 21 實測），執行時由 `invokedynamic` 指令產生 `Runnable` 物件。最後一行是字串串接，跟 lambda 無關。

> 💡 面試官：什麼是函式介面？@FunctionalInterface 一定要加嗎？

**一句話定義**：概念上，函式介面恰好有一個抽象方法；default 方法有實作所以不算，跟 `Object` 公開方法同名的抽象方法也不算；lambda 只能放在需要函式介面的地方。[出處](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/FunctionalInterface.html)

**差別與取捨**：不加 `@FunctionalInterface` 也能用 lambda，不論有沒有這個標註，編譯器都會把符合定義的介面當函式介面；加了的好處是防呆，有人多加一個抽象方法時直接編譯失敗。常用的不必自己寫：`Function`（T 到 R）、`Predicate`（T 到 boolean）、`Consumer`（T 到沒有回傳）、`Supplier`（不收參數到 T）。[出處](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/function/package-summary.html)

```
import java.util.function.Function;
import java.util.function.Predicate;

public class FuncIface {
    @FunctionalInterface
    interface FeeRule {
        long fee(long amount);                         // 唯一的抽象方法
        default FeeRule plus(long extra) {             // default 方法不算
            return a -> fee(a) + extra;
        }
    }

    public static void main(String[] args) {
        FeeRule perMille = a -> a / 1000;                 // 千分之一
        System.out.println(perMille.plus(15).fee(50_000));

        Predicate<Long> large = a -> a >= 1_000_000;
        Function<Long, String> label = a -> large.test(a) ? "大額" : "一般";
        System.out.println(label.apply(2_000_000L) + " " + label.apply(300L));
    }
}
```

```
65
大額 一般
```

> 💡 面試官：lambda 裡為什麼不能改外面的區域變數？什麼是 effectively final？

**一句話定義**：lambda 用到但沒在裡面宣告的區域變數、參數或例外參數，必須是 final 或 effectively final[出處](https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html#jls-15.27.2)；effectively final 是沒寫 `final`、但加上 final 也不會有任何編譯錯誤的變數，也就是宣告後從沒被重新指派。[出處](https://docs.oracle.com/javase/specs/jls/se21/html/jls-4.html#jls-4.12.4)

**為什麼**：這樣就禁止存取一直在變動的區域變數，因為捕獲它們很可能引出並行問題。[出處](https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html#jls-15.27.2) lambda 可能在別的執行緒、之後才執行，捕獲的其實是「值」。要加總就讓結果變成回傳值：

```
import java.util.List;

public class Capture {
    public static void main(String[] args) {
        List<Long> amounts = List.of(100L, 200L, 300L);
        long total = 0;
        amounts.forEach(a -> total += a);              // 想在 lambda 裡累加
        System.out.println(total);
    }
}
```

```
Capture.java:7: error: local variables referenced from a lambda expression must be final or effectively final
        amounts.forEach(a -> total += a);              // 想在 lambda 裡累加
                             ^
1 error
```

```
import java.util.List;

public class CaptureFix {
    public static void main(String[] args) {
        List<Long> amounts = List.of(100L, 200L, 300L);
        long limit = 150;                              // 沒被改過：effectively final
        long total = amounts.stream()
                .filter(a -> a > limit)                // 讀它可以
                .mapToLong(Long::longValue)
                .sum();                                // 加總交給終端操作回傳
        System.out.println(total);
    }
}
```

```
500
```

**實務註記**：這條限制只管區域變數、參數與例外參數，物件的欄位可以在 lambda 裡改，但多執行緒時就要自己處理同步，見〈Java 並行快答：執行緒池、鎖與並行集合〉。

**常被追問**：lambda 能不能丟受檢例外？要看函式介面的方法有沒有宣告 throws：lambda 本體丟出的受檢例外，必須是目標方法 throws 子句所列例外的子類別[出處](https://docs.oracle.com/javase/specs/jls/se21/html/jls-11.html#jls-11.2.3)，而 `Function.apply`、`Consumer.accept` 都沒宣告，所以在 `forEach` 裡直接讀檔會編不過，只能在 lambda 裡自己 try／catch，或改回一般迴圈。

> 💡 面試官：方法參考有哪幾種？

**一句話定義**：方法參考用 `::` 指向一個方法的呼叫，但不實際執行它[出處](https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html#jls-15.13)；用來取代那種只是呼叫某個在別處定義好的方法的 lambda。[出處](https://dev.java/learn/language/fp/lambdas/method-references/)

分四種：[出處](https://dev.java/learn/language/fp/lambdas/method-references/)

*   **靜態方法**：`Integer::parseInt`
*   **特定物件的實例方法**：`System.out::println`，也叫綁定
*   **某型別任意物件的實例方法**：`String::toUpperCase`，未綁定，第一個參數當呼叫者
*   **建構子**：`ArrayList::new`，依目標型別決定呼叫哪個建構子

```
import java.util.ArrayList;
import java.util.List;
import java.util.function.BiFunction;
import java.util.function.Consumer;
import java.util.function.Function;
import java.util.function.Supplier;

public class MethodRefs {
    public static void main(String[] args) {
        Function<String, Integer> parse = Integer::parseInt;          // 靜態方法
        Consumer<String> print = System.out::println;                 // 特定物件（System.out）的實例方法
        Function<String, String> upper = String::toUpperCase;         // 任意物件：第一個參數當呼叫者
        BiFunction<String, String, Boolean> same = String::equalsIgnoreCase;
        Supplier<List<String>> newList = ArrayList::new;              // 建構子

        print.accept("parse " + (parse.apply("42") + 1));
        print.accept(upper.apply("twd"));
        print.accept("same " + same.apply("TWD", "twd"));
        List<String> list = newList.get();
        list.add("A-001");
        print.accept(list.toString());
    }
}
```

```
parse 43
TWD
same true
[A-001]
```

**常被追問：**`String::equalsIgnoreCase` 放進 `BiFunction` 時，第一個參數是呼叫者、第二個是引數，這就是「未綁定」。

*【Stream】*

## 惰性、一次性、收集器與平行

> 💡 面試官：Stream 的惰性求值是什麼？為什麼一條流只能用一次？中間操作跟終端操作差在哪？

**一句話定義**：管線是來源＋零個或多個中間操作＋一個終端操作：

*   **中間操作**（`filter`、`map`、`sorted`……）：回傳新的流，一律是惰性的
*   **終端操作**（`toList`、`collect`、`count`、`findFirst`……）：它執行之前，不會開始走訪來源。[出處](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/package-summary.html)

**只能用一次：**

*   流的元素在一條流的生命期間只會被走訪一次；跟 `Iterator` 一樣，要再走就得產生新的流[出處](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/package-summary.html)
*   偵測到重用時，實作可能丟出 `IllegalStateException`[出處](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/Stream.html)

下面的輸出還看得出 Java 21 的循序流是一筆一筆走完整條管線，不是全部 filter 完才 map：

```
import java.util.List;
import java.util.stream.Stream;

public class LazyOnce {
    public static void main(String[] args) {
        Stream<Integer> s = List.of(5, 20, 8).stream()
                .filter(x -> { System.out.println("filter " + x); return x > 6; })
                .map(x -> { System.out.println("map " + x); return x * 10; });
        System.out.println("還沒有終端操作");
        System.out.println(s.toList());                // 終端操作：這時才開始跑

        try {
            s.count();                                 // 同一條流再用一次
        } catch (IllegalStateException e) {
            System.out.println(e.getMessage());
        }
    }
}
```

```
還沒有終端操作
filter 5
filter 20
map 20
filter 8
map 8
[200, 80]
stream has already been operated upon or closed
```

**實務註記**：中間操作再分無狀態（`filter`、`map`）與有狀態（`distinct`、`sorted`，要看過全部元素才能輸出）；`findFirst`、`anyMatch`、`limit` 是短路操作，答案確定就停。`peek` 主要給除錯用；`count()` 能直接從來源算出筆數時，實作可能選擇不執行管線。[出處](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/Stream.html) 細節見〈Stream API：把迴圈寫成資料流〉。

> 💡 面試官：map 跟 flatMap 差在哪？

**一句話定義：**`map` 一進一出；`flatMap` 把每個元素換成一條流再接起來，也就是一對多的轉換，再把產生的元素攤平成一條新的流。[出處](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/Stream.html) 迴圈的對應是「兩層 for」：外層走帳戶、內層走交易。

```
import java.util.List;

public class FlatMapDemo {
    record Account(String id, List<Long> txs) {}

    public static void main(String[] args) {
        List<Account> accounts = List.of(
                new Account("A", List.of(100L, 250L)),
                new Account("B", List.of()),
                new Account("C", List.of(40L)));

        List<List<Long>> nested = accounts.stream().map(Account::txs).toList();
        List<Long> flat = accounts.stream().flatMap(a -> a.txs().stream()).toList();
        System.out.println(nested);
        System.out.println(flat);
    }
}
```

```
[[100, 250], [], [40]]
[100, 250, 40]
```

> 💡 面試官：groupingBy 跟 toMap 怎麼選？toMap 遇到重複的鍵會怎樣？

**一句話定義：**`groupingBy` 把同一個鍵的元素收成一組（預設 `Map<K, List<T>>`，可以接下游收集器做加總、計數）；`toMap` 一個元素對一個值，**鍵重複時，收集時會丟出 `IllegalStateException`**，要給第三個參數「合併函式」決定兩個值怎麼合成一個。[出處](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/Collectors.html)

```
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.stream.Collectors;

public class Grouping {
    record Tx(String branch, long amount) {}

    public static void main(String[] args) {
        List<Tx> txs = List.of(new Tx("台北", 500), new Tx("台中", 300), new Tx("台北", 200));

        Map<String, Long> byBranch = txs.stream().collect(
                Collectors.groupingBy(Tx::branch, TreeMap::new, Collectors.summingLong(Tx::amount)));
        System.out.println(byBranch);

        try {
            txs.stream().collect(Collectors.toMap(Tx::branch, Tx::amount));   // 台北出現兩次
        } catch (IllegalStateException e) {
            System.out.println(e.getMessage());
        }

        Map<String, Long> merged = txs.stream().collect(
                Collectors.toMap(Tx::branch, Tx::amount, Long::sum, TreeMap::new));  // 第三個參數：鍵重複時怎麼合併
        System.out.println(merged);
    }
}
```

```
{台中=300, 台北=700}
Duplicate key 台北 (attempted merging values 500 and 200)
{台中=300, 台北=700}
```

**實務註記**：兩者回傳的 `Map` 型別都不保證，要固定順序就傳 `TreeMap::new`；`counting()` 的結果是 `Long` 不是 `Integer`。[出處](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/Collectors.html)

> 💡 面試官：stream.toList() 跟 collect(Collectors.toList()) 一樣嗎？

**一句話定義**：不一樣。`Stream.toList()`（Java 16 起）回傳的清單不可修改，呼叫任何修改方法都一定會丟出 `UnsupportedOperationException`[出處](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/Stream.html#toList())；`Collectors.toList()` 則對清單的型別、可變性都沒有任何保證，需要可修改的清單就用 `toCollection(ArrayList::new)`。另外 `Collectors.toUnmodifiableList()` 不收 `null`，遇到就丟 `NullPointerException`。[出處](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/Collectors.html)

```
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

public class ToListDemo {
    public static void main(String[] args) {
        List<String> a = Arrays.asList("x", null, "y");

        List<String> t = a.stream().toList();                          // Java 16 起
        List<String> c = a.stream().collect(Collectors.toList());
        System.out.println(t + " " + c);

        try { t.add("z"); } catch (UnsupportedOperationException e) { System.out.println("toList() 不能改"); }
        c.add("z");                                                    // 目前的實作給 ArrayList，但文件不保證
        System.out.println(c.getClass().getSimpleName() + " " + c);

        try {
            a.stream().collect(Collectors.toUnmodifiableList());
        } catch (NullPointerException e) {
            System.out.println("toUnmodifiableList 不收 null");
        }
        List<String> m = a.stream().collect(Collectors.toCollection(ArrayList::new));  // 要可修改就指定
        m.add("z");
        System.out.println(m);
    }
}
```

```
[x, null, y] [x, null, y]
toList() 不能改
ArrayList [x, null, y, z]
toUnmodifiableList 不收 null
[x, null, y, z]
```

**版本註記**：從 Java 8 的程式升上來時，把 `collect(Collectors.toList())` 一律換成 `toList()` 要小心：後面若有 `add`、`sort` 這類修改，會變成執行時才丟例外。`Collectors.toList()` 在 Java 21 實跑給的是 `ArrayList`，但那是實作，不是保證。

> 💡 面試官：平行流什麼時候不該用？

**一句話定義：**`parallelStream()` 把工作切給整個 JVM 共用的 Fork/Join 池；平行不會自動比循序快，資料夠多、核心夠多時才可能。[出處](https://docs.oracle.com/javase/tutorial/collections/streams/parallelism.html)

**不該用的情況：**

*   資料量小
*   **來源難切**（例如 `LinkedList`）或合併成本高
*   **阻塞的 I/O**：lambda 裡有阻塞的 I/O（會佔住共用池，見〈Java 並行快答：執行緒池、鎖與並行集合〉）
*   **改外面的集合**：lambda 裡改外面的集合，行為參數的副作用一般是不鼓勵的；`ArrayList` 不是執行緒安全的，會造成錯誤的結果。[出處](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/package-summary.html)

這個共用池的平行度預設是處理器數減一（OpenJDK 的預設，見〈Java 並行快答：執行緒池、鎖與並行集合〉），整個 JVM 共用，一個平行流卡住，其他用到它的地方都可能跟著變慢，包括 `CompletableFuture` 沒指定執行緒池的非同步工作：沒有明確 `Executor` 參數的非同步方法，都用 `ForkJoinPool.commonPool()` 執行。[出處](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/CompletableFuture.html)

守則：不要猜，量測你的程式碼的效能。[出處](https://dev.java/learn/api/collections-and-streams/streams/parallel-streams/) 結果交給終端操作產生，平行也照來源順序：

```
import java.util.List;
import java.util.stream.IntStream;

public class ParallelDemo {
    public static void main(String[] args) {
        List<Integer> seq = IntStream.range(0, 10_000).map(x -> x * 2).boxed().toList();
        List<Integer> par = IntStream.range(0, 10_000).parallel().map(x -> x * 2).boxed().toList();
        System.out.println(seq.equals(par));            // 結果交給終端操作：順序與內容都一樣

        StringBuilder order = new StringBuilder();
        IntStream.range(0, 5).parallel().forEachOrdered(order::append);   // 要照順序就用 forEachOrdered
        System.out.println(order);
    }
}
```

```
true
01234
```

*【Optional 與現代語法】*

## Optional、record、var、switch、sealed

> 💡 面試官：Optional 該怎麼用？哪些用法是錯的？

**一句話定義**：可能裝著、也可能沒裝著一個非 null 值的容器，主要設計來當方法的回傳型別，用在明確要表達「沒有結果」、用 null 很可能出錯的地方。[出處](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Optional.html)

**不該怎麼用：**[出處](https://dev.java/learn/api/collections-and-streams/streams/optionals/)

*   Optional 變數或回傳值永遠不要是 null
*   不要用在欄位、方法參數、集合與 Map 裡
*   優先用 `map`、`orElse` 這些方法，而不是先 `isPresent()` 再 `get()`

**常被追問：**`orElse(x)` 的 x 在呼叫前就算好了，`orElseGet(supplier)` 只在沒有值時才呼叫，預設值很貴（查資料庫）時用後者：

```
import java.util.Map;
import java.util.Optional;

public class OptionalDemo {
    static final Map<String, String> NAMES = Map.of("A-001", "王小明");

    static Optional<String> findName(String id) {        // 查不到回傳 Optional.empty()，不回傳 null
        return Optional.ofNullable(NAMES.get(id));
    }

    static String loadDefault() {
        System.out.println("  （查了一次預設值）");
        return "未知戶名";
    }

    public static void main(String[] args) {
        System.out.println(findName("A-001").map(n -> n.charAt(0) + "**").orElse("無此帳號"));
        System.out.println("orElse：");
        System.out.println(findName("A-001").orElse(loadDefault()));      // 有值也先算預設值
        System.out.println("orElseGet：");
        System.out.println(findName("A-001").orElseGet(OptionalDemo::loadDefault));  // 沒值才算
        System.out.println(findName("B-404").orElseGet(OptionalDemo::loadDefault));
    }
}
```

```
王**
orElse：
  （查了一次預設值）
王小明
orElseGet：
王小明
  （查了一次預設值）
未知戶名
```

細節與更多守則見〈Lambda 與函式介面〉最後一段。

> 💡 面試官：record 是什麼？有什麼限制？

**一句話定義**：record（Java 16 起，JEP 395）是透明地裝著不可變資料的類別，宣告元件後自動有 private final 欄位、同名讀取方法（`amount()`，不是 `getAmount()`）、標準建構子，以及依元件值的 `equals`、`hashCode`、`toString`；驗證寫在不寫參數列的緊湊建構子。[出處](https://openjdk.org/jeps/395)

**限制**：不能 `extends`（父類別固定是 `java.lang.Record`），但可以實作介面；隱含 `final`；不能另外宣告實體欄位。[出處](https://openjdk.org/jeps/395) 而且只是淺層不可變（shallowly immutable）[出處](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Record.html)：元件指向的清單還是改得動，要在緊湊建構子裡 `List.copyOf`。

```
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

public class RecordDemo {
    record Money(BigDecimal amount, String currency) {
        Money {                                          // 緊湊建構子：驗證與正規化參數
            if (amount.signum() < 0) throw new IllegalArgumentException("金額不能是負的");
            currency = currency.toUpperCase();
        }
    }

    record Batch(String id, List<String> txIds) {}       // 欄位是 final，但清單本身可以改

    public static void main(String[] args) {
        Money a = new Money(new BigDecimal("100"), "twd");
        System.out.println(a + " " + a.equals(new Money(new BigDecimal("100"), "TWD")));

        List<String> ids = new ArrayList<>(List.of("T1"));
        Batch b = new Batch("B1", ids);
        ids.add("T2");                                   // 從外面改原本的清單
        System.out.println(b.txIds());                   // 淺層不可變：跟著變了
    }
}
```

```
Money[amount=100, currency=TWD] true
[T1, T2]
```

**實務註記**：因為 `equals`、`hashCode` 依元件值，record 很適合當 `HashMap` 的鍵、API 的回應物件、Stream 的中間結果。教材見〈現代 Java 語法：var、record、switch、文字區塊與 sealed〉。

> 💡 面試官：var 要不要用？有什麼取捨？

**一句話定義**：var（Java 10 起，JEP 286）只用在有初始值的區域變數、增強型 for 的索引、傳統 for 迴圈裡宣告的區域變數，欄位、方法參數、回傳型別都不行；型別在編譯期就定了，不是動態型別。它不是關鍵字，而是保留的型別名稱。[出處](https://openjdk.org/jeps/286)

**取捨：**[出處](https://openjdk.org/projects/amber/guides/lvti-style-guide)

*   讀程式碼比寫程式碼重要
*   初始值已經提供足夠資訊時才考慮 var
*   var 配菱形會推成 `Object`、配整數字面值一律推成 `int`

```
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class VarDemo {
    public static void main(String[] args) {
        var balances = new HashMap<String, List<Long>>();   // 右邊看得出型別：var 省掉重複
        balances.put("A-001", new ArrayList<>(List.of(100L)));
        for (var e : balances.entrySet()) System.out.println(e.getKey() + " " + e.getValue());

        var things = new ArrayList<>();                      // 菱形沒有線索：推成 ArrayList<Object>
        things.add(1);
        things.add("不小心放了字串");
        System.out.println(things);

        var big = 3_000_000_000L;                            // 要 long 就得自己寫 L，var 不會替你轉
        System.out.println(((Object) big).getClass().getSimpleName());
    }
}
```

```
A-001 [100]
[1, 不小心放了字串]
Long
```

> 💡 面試官：switch 運算式跟以前的 switch 差在哪？模式比對又是什麼？

**一句話定義**：Java 14 起（JEP 361）switch 可以產生值；箭頭 `->` 只執行箭頭右邊，不會穿透（no fall through），區塊裡用 `yield` 交出值，而且 switch 運算式必須窮舉。[出處](https://openjdk.org/jeps/361)

模式比對是「檢查形狀、順便取出內容」：

*   **Java 16**：`instanceof String s`（JEP 394，Java 16）[出處](https://openjdk.org/jeps/394)
*   **Java 21**：case 可以寫型別模式、`when` 守衛與 `case null`（JEP 441）[出處](https://openjdk.org/jeps/441)
*   **record 解構**：還能把 record 元件直接拆出來（JEP 440）[出處](https://openjdk.org/jeps/440)。

```
public class SwitchPattern {
    sealed interface Payment permits Card, Transfer, Cash {}
    record Card(String last4, long amount) implements Payment {}
    record Transfer(String bank, long amount) implements Payment {}
    record Cash(long amount) implements Payment {}

    static String describe(Payment p) {
        return switch (p) {                                       // 沒有 default：sealed 讓編譯器知道只有三種
            case Card(var last4, var amt) when amt >= 100_000 -> "大額刷卡 *" + last4;
            case Card c -> "刷卡 " + c.amount();
            case Transfer(String bank, long amt) -> bank + " 轉帳 " + amt;
            case Cash cash -> "現金 " + cash.amount();
        };
    }

    static int fee(String channel) {
        return switch (channel) {                                 // switch 運算式：箭頭不穿透，要窮舉
            case "ATM", "網銀" -> 15;
            case "臨櫃" -> {
                int base = 30;
                yield base + 5;                                   // 區塊裡用 yield 交出值
            }
            default -> 0;
        };
    }

    public static void main(String[] args) {
        System.out.println(describe(new Card("1234", 250_000)));
        System.out.println(describe(new Card("5678", 900)));
        System.out.println(describe(new Transfer("B 銀行", 5_000)));
        System.out.println(describe(new Cash(300)));
        System.out.println(fee("網銀") + " " + fee("臨櫃") + " " + fee("其他"));
    }
}
```

```
大額刷卡 *1234
刷卡 900
B 銀行 轉帳 5000
現金 300
15 35 0
```

**常被追問**：由上往下第一個符合的生效，所以有 `when` 的 `case Card(...)` 要放在 `case Card c` 前面，反過來會被「支配」而編譯錯誤；`default` 不接 `null`，沒寫 `case null` 時還是丟 `NullPointerException`。[出處](https://openjdk.org/jeps/441) **版本註記**：用不到的元件寫成 `_` 是 Java 22 正式（JEP 456），Java 21 還是預覽。[出處](https://openjdk.org/jeps/456)

> 💡 面試官：sealed 類別解決什麼問題？

**一句話定義**：sealed 類別與介面（Java 17 起，JEP 409）限制哪些類別或介面可以延伸或實作它們，用 `permits` 列出名單；每個子類別都要寫 `final`、`sealed` 或 `non-sealed` 表明要不要繼續開放（record 隱含 final）。[出處](https://openjdk.org/jeps/409)

**用途**：上一題的 `Payment` 只有三種，switch 不寫 `default` 編譯器也知道已經窮舉：選擇值是 sealed 型別時，窮舉檢查會參考 permits 清單。[出處](https://openjdk.org/jeps/441) 好處是之後新增第四種付款方式，沒寫 `default` 的模式 switch，重新編譯時就會**編譯失敗**，而不是默默掉進 `default`。少寫一種的實跑結果：

```
public class SealedBad {
    sealed interface Payment permits Card, Cash {}
    record Card(long amount) implements Payment {}
    record Cash(long amount) implements Payment {}

    static String describe(Payment p) {
        return switch (p) {
            case Card c -> "刷卡";
        };
    }
}
```

```
SealedBad.java:7: error: the switch expression does not cover all possible input values
        return switch (p) {
               ^
1 error
```

**跟 enum 比**：enum 是固定的幾個「值」，sealed 是固定的幾種「型別」，每種可以帶不同的欄位（刷卡有卡號末四碼、轉帳有銀行）。sealed 加 record 加模式 switch，就是 Java 表達「這筆資料是 A、B、C 其中一種」的寫法。教材見〈現代 Java 語法：var、record、switch、文字區塊與 sealed〉。

> Java 21 的現代寫法：record 裝資料、sealed 定種類、模式 switch 分情況、Stream 做轉換、Optional 表達沒有結果

### 重點整理

*   lambda 實作函式介面唯一的抽象方法；裡面的 `this` 指外層物件；匿名類別會多一個 `$1.class`，lambda 靠 `invokedynamic` 執行時產生。
*   lambda 只能讀 final 或 effectively final 的區域變數，理由是避免並行問題；要累加就讓 Stream 回傳結果。方法參考四種：靜態、特定物件、任意物件（第一個參數當呼叫者）、建構子。
*   Stream 中間操作是惰性的，終端操作才開始跑；一條流只能用一次，重用時可能丟 `IllegalStateException`（Java 21 實跑會丟）。`flatMap` 是一對多再攤平。
*   `toMap` 鍵重複丟 `IllegalStateException`，要給合併函式；`toList()` 不可修改，`Collectors.toList()` 不保證可變性，要可修改用 `toCollection(ArrayList::new)`。
*   平行流不一定快：資料少、難切、有阻塞 I/O、lambda 有副作用時不要用，先量再用。
*   Optional 只當回傳型別，不放欄位、參數、集合；本身不要是 null；預設值很貴用 `orElseGet`。
*   record 自動產生讀取方法與依值的 `equals`，不能繼承、只到第一層不可變；var 只用在區域變數、右邊看得出型別時才用；switch 運算式要窮舉、箭頭不穿透；sealed 讓模式 switch 不寫 default 也能窮舉，新增子型別時編譯器會提醒。

## 隨堂測驗

**Q1. 在一個物件的方法裡寫 lambda，lambda 本體裡的 this 指的是什麼？**

- (A) 外層那個物件，跟周圍程式碼的 this 一樣
- (B) lambda 自己被產生出來的那個物件
- (C) Java 替 lambda 另外產生的匿名類別物件
- (D) 編譯錯誤，lambda 本體裡不能使用 this

<details><summary>看答案</summary>

**答案：(A)** lambda 本體裡名稱與 this、super 的意義跟周圍的程式碼相同。匿名類別才會有自己的 this。

</details>

**Q2. 下面哪一個介面不是函式介面？**

- (A) 有兩個沒有實作的抽象方法 a() 與 b() 的介面
- (B) 只有一個抽象方法、另外有三個 default 方法的介面
- (C) 有一個抽象方法，外加一個抽象的 boolean equals(Object o)
- (D) 只有一個抽象方法、沒有加 @FunctionalInterface 的介面

<details><summary>看答案</summary>

**答案：(A)** 函式介面恰好一個抽象方法；default 方法與跟 Object 公開方法同名的抽象方法都不算，@FunctionalInterface 也不是必要條件。兩個抽象方法就不是。

</details>

**Q3. lambda 為什麼只能讀 final 或 effectively final 的區域變數？**

- (A) 避免捕獲會變動的變數，引出並行問題
- (B) 因為 lambda 一定會被編譯成匿名類別
- (C) 因為區域變數放在堆上，lambda 讀不到它們
- (D) 這只是編譯器的建議，不遵守照樣能編譯

<details><summary>看答案</summary>

**答案：(A)** 理由是捕獲會變動的區域變數很可能引出並行問題；lambda 可能在別的執行緒、之後才執行。違反時是編譯錯誤，不是建議。

</details>

**Q4. Function&lt;String, String> f = String::toUpperCase; 這是哪一種方法參考？**

- (A) 任意物件的實例方法（未綁定）
- (B) 靜態方法參考，toUpperCase 是靜態的
- (C) 特定物件（綁定）的實例方法參考
- (D) 建構子參考，會建立一個新字串

<details><summary>看答案</summary>

**答案：(A)** toUpperCase 是實例方法，呼叫它的字串不寫在方法參考裡，而是 f.apply(x) 時傳進來的 x，這叫未綁定。System.out::println 才是特定物件的那種。

</details>

**Q5. 一段 Stream 程式只寫了 list.stream().filter(...).map(...)，沒有接任何終端操作。filter 與 map 裡的 lambda 會執行幾次？**

- (A) 0 次，管線只是先串好、還沒開始跑
- (B) 每個元素各執行一次
- (C) 只對第一個元素執行一次
- (D) 執行時丟出 IllegalStateException

<details><summary>看答案</summary>

**答案：(A)** 中間操作一律是惰性的，只是把管線串好；要等 toList、collect、count 這類終端操作呼叫時，才開始走訪來源。

</details>

**Q6. 同一個 Stream 物件已經呼叫過 toList()，再對它呼叫 count()，Java 21 上會怎樣？**

- (A) 丟出 IllegalStateException
- (B) 回傳元素個數，跟第一次一樣
- (C) 回傳 0，因為元素已經被取走了
- (D) 自動重新從來源再跑一次

<details><summary>看答案</summary>

**答案：(A)** 流只能用一次；偵測到重用時可能丟 IllegalStateException，Java 21 實跑的訊息是 stream has already been operated upon or closed。要再用就重新呼叫 list.stream()。

</details>

**Q7. 用 Collectors.toMap(Tx::branch, Tx::amount) 收集，資料裡有兩筆分行都是「台北」，結果是什麼？**

- (A) 收集時丟出 IllegalStateException
- (B) 後一筆的金額蓋掉前一筆
- (C) 兩筆的金額自動相加起來
- (D) 只保留第一筆，後面的直接忽略

<details><summary>看答案</summary>

**答案：(A)** 兩個參數的 toMap 遇到重複的鍵會丟 IllegalStateException。要相加就用三個參數的版本，傳 Long::sum 當合併函式，或改用 groupingBy。

</details>

**Q8. List&lt;String> r = stream.toList(); 之後執行 r.add("x") 會怎樣？**

- (A) 丟出 UnsupportedOperationException
- (B) 成功加入，清單長度加一
- (C) 編譯錯誤，List 沒有 add 方法可用
- (D) 回傳 false，清單內容維持不變

<details><summary>看答案</summary>

**答案：(A)** Stream.toList() 回傳的是不可修改的清單，任何修改方法都一定會丟這個例外。要能修改就用 collect(Collectors.toCollection(ArrayList::new))。

</details>

**Q9. 下面哪一種 Optional 用法符合建議？**

- (A) 方法查不到資料時回傳 Optional.empty()
- (B) 把類別的欄位宣告成 Optional&lt;String>
- (C) 方法參數宣告成 Optional&lt;Long>，讓呼叫端可以不傳
- (D) 回傳型別是 Optional 時，查不到就回傳 null

<details><summary>看答案</summary>

**答案：(A)** Optional 主要設計來當方法的回傳型別；不要用在欄位、方法參數、集合，Optional 本身也永遠不該是 null。

</details>

**Q10. Payment 是 sealed 介面，只 permits Card 與 Cash 兩個 record。對它寫 switch 運算式，只寫了 case Card c，會怎樣？**

- (A) 編譯錯誤：switch 運算式沒有涵蓋所有可能的值
- (B) 可以編譯，Cash 執行時回傳 null
- (C) 可以編譯，Cash 執行時丟出例外
- (D) 一定要寫 default 才能編譯，跟 sealed 無關

<details><summary>看答案</summary>

**答案：(A)** switch 運算式必須窮舉，sealed 讓編譯器知道只有 Card 與 Cash，所以漏了 Cash 是編譯錯誤；兩種都寫了就不需要 default。實跑錯誤訊息是 the switch expression does not cover all possible input values。

</details>
