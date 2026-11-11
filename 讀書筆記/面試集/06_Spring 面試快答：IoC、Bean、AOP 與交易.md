# 06. Spring 面試快答：IoC、Bean、AOP 與交易

> 來源：[筆記平台 · 面試集](https://hhtim.github.io/notes-platform/interview/#/lesson/spring-quick-answers)　第 6 課 / 共 23 課 · 約 17 分鐘

**IoC 與 Bean 生命週期、三種注入與循環相依、AOP 代理與自我呼叫、交易傳播與失效情境、Spring Boot 自動組態、Spring MVC 請求路徑——十五題的面試答法，每句附官方出處。**

### 讀完這課你會

*   分清控制反轉與依賴注入、Bean 生命週期
*   選對注入方式，說出循環相依為何失敗
*   解釋代理與內部呼叫讓註解失效
*   答出交易傳播與 @Transactional 失效情境

*【IoC 容器】*

## 容器、Bean 與生命週期

答題公式：先一句話定義，再講差別與取捨，最後補版本或實務註記。以下以 Spring Framework 7.0、Spring Boot 4.1 為準，跟 Spring 6、Boot 3 不同處會標出。

> 💡 面試官：IoC 與 DI 差在哪？Spring 容器做了什麼？

**一句話定義**：控制反轉（Inversion of Control，IoC）是一種原則——物件不再自己建立或尋找它需要的相依物件，改由容器負責；依賴注入（Dependency Injection，DI）是實現這個原則的一種做法——容器在建立物件時把相依物件送進去。

**差別與取捨**：IoC 也稱為依賴注入，兩者講的是同一件事的兩面：

*   物件只透過建構子參數、工廠方法參數，或建立之後設定的屬性，宣告自己需要什麼
*   容器在建立 Bean 時把這些相依注入進去
*   這正好是 Bean 自己建立或查找相依物件的反面，所以叫控制反轉[出處](https://docs.spring.io/spring-framework/reference/core/beans/introduction.html)

追問時要能區分：IoC 是「誰負責」的原則，DI 是「怎麼送進去」的手段。

**容器做了什麼**：由容器管理的物件叫 Bean，就是由 Spring IoC 容器實例化、組裝與管理的物件[出處](https://docs.spring.io/spring-framework/reference/core/beans/introduction.html)——容器的工作就是這三件。範例程式與「為什麼不該到處 new」見〈Spring 入門與 IoC、DI〉。

> 💡 面試官：BeanFactory 與 ApplicationContext 差在哪？

**一句話定義**：BeanFactory 是容器的最底層介面，只管 Bean 的建立與組裝；ApplicationContext 是它的子介面，多了企業應用要的整合功能。

**差別與取捨**：ApplicationContext 是 BeanFactory 的子介面，多了：[出處](https://docs.spring.io/spring-framework/reference/core/beans/introduction.html)

*   與 Spring AOP 更容易整合
*   訊息資源處理（用於國際化）
*   事件發布
*   應用層專用的容器（例如 WebApplicationContext）

常被追問的是 BeanPostProcessor 與 BeanFactoryPostProcessor 的自動註冊：BeanFactory 沒有、ApplicationContext 有。用陽春的 BeanFactory 得自己一個個 `addBeanPostProcessor`，很不方便，這正是各種 ApplicationContext 比陽春的 DefaultListableBeanFactory 更常用的原因。[出處](https://docs.spring.io/spring-framework/reference/core/beans/beanfactory.html)

**實務註記**：除非有好理由，否則就用 ApplicationContext。[出處](https://docs.spring.io/spring-framework/reference/core/beans/beanfactory.html) 另一個常考差別是建立時機：ApplicationContext 預設在初始化時就把所有 singleton Bean 建好、設定好，好處是組態或環境的錯誤會立刻被發現；不想這樣可以標 @Lazy。[出處](https://docs.spring.io/spring-framework/reference/core/beans/dependencies/factory-lazy-init.html)

> 💡 面試官：Bean 的作用域有哪幾種？singleton 的 Bean 是執行緒安全的嗎？

**一句話定義**：作用域（scope）決定一個 Bean 定義會產生幾個實例、活多久。共六種：singleton（預設）、prototype，加上只在 Web 環境有效的 request、session、application、websocket。[出處](https://docs.spring.io/spring-framework/reference/core/beans/factory-scopes.html)

| 作用域 | 意思 | 面試要補的一句 |
| --- | --- | --- |
| singleton | 每個 Spring IoC 容器對一個 Bean 定義只有一個物件實例 | 跟設計模式的 Singleton 不同：後者是「每個 ClassLoader 一個」，Spring 的是「每個容器、每個 Bean 定義一個」 |
| prototype | 每次跟容器要這個 Bean 都建立一個新的實例 | 容器不管它的完整生命週期：初始化回呼會執行，設定的銷毀回呼不會被呼叫 |
| request／session／application／websocket | 分別綁在一次 HTTP 請求、一個 HTTP Session、一個 ServletContext、一條 WebSocket 連線的生命週期 | 只在 Web 環境的 ApplicationContext 中有效，一般的 ApplicationContext 用了會失敗 |

**執行緒安全怎麼答**：容器不替你保證。singleton 是容器只管理一個共用實例，所有對這個 Bean 的請求都拿到同一個實例[出處](https://docs.spring.io/spring-framework/reference/core/beans/factory-scopes.html)——多個請求同時進來，就是多條執行緒共用同一個物件。

*   Bean 沒有可變狀態（只持有注入的相依、方法裡只用區域變數）：沒有東西可以壞
*   放了可變欄位當計數器或暫存：那個欄位就是多執行緒共用的

答案是「取決於 Bean 有沒有可變狀態」，不是「安全」或「不安全」。

> 💡 面試官：Bean 的完整生命週期是什麼順序？

**一句話定義**：實例化、屬性填入、各個 Aware 介面回呼、BeanPostProcessor 前置處理、初始化、BeanPostProcessor 後置處理、使用、銷毀。每一步的細部順序列在 BeanFactory 介面的 Javadoc。[出處](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/beans/factory/BeanFactory.html)

| 階段 | 發生什麼 | 補充 |
| --- | --- | --- |
| 實例化、屬性填入 | 建立物件，填好建構子參數與屬性（含注入的相依） | Aware 回呼在一般屬性填入之後、初始化回呼之前[出處](https://docs.spring.io/spring-framework/reference/core/beans/factory-nature.html) |
| Aware 介面 | 依序 BeanNameAware、BeanClassLoaderAware、BeanFactoryAware……到 ApplicationContextAware | BeanFactory Javadoc 初始化順序的第 1〜9 項（Web 環境再多第 10 項 ServletContextAware）[出處](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/beans/factory/BeanFactory.html) |
| BeanPostProcessor 前置 | `postProcessBeforeInitialization` | 後置處理器在容器的初始化方法被呼叫之前、以及任何 Bean 初始化回呼之後，都會收到回呼[出處](https://docs.spring.io/spring-framework/reference/core/beans/factory-extension.html) |
| 初始化 | 依序 @PostConstruct、`afterPropertiesSet()`、自訂 init 方法 | 多種生命週期機制同時用時就照這個順序[出處](https://docs.spring.io/spring-framework/reference/core/beans/factory-nature.html) |
| BeanPostProcessor 後置 | `postProcessAfterInitialization`——AOP 代理在這裡包上去 | 有些 Spring AOP 基礎建設類別就是以 Bean 後置處理器實作，負責包代理[出處](https://docs.spring.io/spring-framework/reference/core/beans/factory-extension.html) |
| 銷毀 | 容器關閉時依序 @PreDestroy、`destroy()`、自訂 destroy 方法 | 銷毀跟初始化同樣順序；prototype 不走這步[出處](https://docs.spring.io/spring-framework/reference/core/beans/factory-nature.html) |

**實務註記**：被問「該用哪一種初始化回呼」：

*   用 @PostConstruct 與 @PreDestroy：這是現代 Spring 應用程式接收生命週期回呼的最佳做法，Bean 不會綁死在 Spring 專屬介面上
*   Aware 介面相反：它把程式碼綁在 Spring API 上、不符合控制反轉的風格，只建議給需要直接操作容器的基礎建設 Bean 用[出處](https://docs.spring.io/spring-framework/reference/core/beans/factory-nature.html)

*【依賴注入】*

## 怎麼注、注哪一個、繞成圈怎麼辦

> 💡 面試官：建構子注入、setter 注入、欄位注入怎麼選？為什麼建議用建構子？

**一句話定義**：必要的相依用建構子注入，可有可無的相依用 setter 注入，欄位注入能動但不推薦。

**差別與取捨：**[出處](https://docs.spring.io/spring-framework/reference/core/beans/dependencies/factory-collaborators.html)

*   建構子注入：Spring 團隊一般提倡這種，元件可以寫成不可變物件，必要的相依也保證不會是 null
*   setter 注入：只用在類別內能給合理預設值的可選相依，否則每個用到那個相依的地方都要檢查非 null
*   欄位注入（@Autowired 直接放在欄位上）：可以用[出處](https://docs.spring.io/spring-framework/reference/core/beans/annotation-config/autowired.html)，但欄位不能宣告成 final，單元測試也沒辦法不靠容器就把替身傳進去

**實務註記**：目標 Bean 只定義一個建構子時，那個建構子上的 @Autowired 可以省略[出處](https://docs.spring.io/spring-framework/reference/core/beans/annotation-config/autowired.html)；建構子參數太多不是注入方式的問題，而是壞味道，代表這個類別可能責任太多，應該重構。[出處](https://docs.spring.io/spring-framework/reference/core/beans/dependencies/factory-collaborators.html)

> 💡 面試官：循環相依 Spring 怎麼處理？為什麼建構子注入會直接失敗？

**一句話定義**：A 需要 B、B 又需要 A 叫循環相依；建構子注入下容器無解，啟動時直接丟例外。

**為什麼會失敗**：建構子注入要求物件建立那一刻就拿到完整相依，A 建到一半等 B、B 建到一半等 A，誰都建不完。主要用建構子注入時，就可能造出這種無解的循環；容器在執行期偵測到循環參考，丟出 BeanCurrentlyInCreationException。[出處](https://docs.spring.io/spring-framework/reference/core/beans/dependencies/factory-collaborators.html)

**setter 注入為什麼能過**：把其中一些類別改成用 setter 設定就能解開，但這是雞生蛋、蛋生雞的情況：其中一個 Bean 會在還沒完全初始化之前就被注入到另一個裡面[出處](https://docs.spring.io/spring-framework/reference/core/beans/dependencies/factory-collaborators.html)——面試常說的「先給一個半成品」就是這個。

**版本註記**：Spring Boot 2.6 起 Bean 之間的循環參考預設禁止，強烈建議改組態打破循環；真要放行得把 `spring.main.allow-circular-references` 設成 true。[出處](https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-2.6-Release-Notes) 所以在 Spring Boot 3 與 4 上，標準答案是「循環相依代表責任切錯了，優先重新設計」，不是背容器怎麼繞過去。

> 💡 面試官：@Autowired、@Resource、@Qualifier、@Primary 差在哪？

*   **@Autowired**：Spring 自己的註解，先照型別找候選者；預設 required 為 true，找不到就失敗。型別有多個候選又沒有其他指示時，Spring 拿注入點的名稱（欄位名或參數名）跟 Bean 名稱比對，選同名的那一個。[出處](https://docs.spring.io/spring-framework/reference/core/beans/annotation-config/autowired-qualifiers.html)
*   **@Resource**：Jakarta 標準註解（`jakarta.annotation.Resource`），照名稱找：name 的值就是要注入的 Bean 名稱；沒寫 name 就從欄位名或 setter 方法推出名稱，那個名字找不到才退回照型別找。只能放在欄位與 setter 方法上。[出處](https://docs.spring.io/spring-framework/reference/core/beans/annotation-config/resource.html)
*   **@Qualifier**：加在注入點，把限定值綁在某個參數上，縮小型別比對的範圍，讓每個參數選到特定的 Bean；Bean 名稱就是預設的限定值，所以直接寫 Bean 名稱也行。[出處](https://docs.spring.io/spring-framework/reference/core/beans/annotation-config/autowired-qualifiers.html)
*   **@Primary**：加在 Bean 定義上，多個 Bean 都符合同一個單值相依時，優先選這個。能決定出一個主要候選者時用 @Primary，需要更細地控制選哪個時才用 @Qualifier。[出處](https://docs.spring.io/spring-framework/reference/core/beans/annotation-config/autowired-qualifiers.html)

> @Autowired 先看型別、@Resource 先看名稱；@Primary 是「沒指定時預設給這個」、@Qualifier 是「這裡就要那一個」

@Qualifier 與 @Primary 的程式碼範例、Bean 名稱怎麼從類別名推出來，見〈Spring 入門與 IoC、DI〉。

*【AOP 與代理】*

## 代理怎麼建，以及它攔不到什麼

> 💡 面試官：Spring AOP 的代理是 JDK 動態代理還是 CGLIB？Spring Boot 預設哪個？

**一句話定義**：兩種都會用，Spring 的 AOP 代理不是 JDK 動態代理就是 CGLIB 代理[出處](https://docs.spring.io/spring-framework/reference/core/aop/introduction-defn.html)；純 Spring Framework 看目標有沒有實作介面來選，Spring Boot 則預設一律 CGLIB。

**差別與取捨：**[出處](https://docs.spring.io/spring-framework/reference/core/aop/proxying.html)

*   JDK 動態代理：Java 標準函式庫內建，只能替介面產生代理
*   CGLIB（一個在執行期直接產生子類別的函式庫，Spring 已把它打包進 spring-core）：在執行期替目標型別產生一個子類別
*   選擇規則：目標至少實作一個介面就用 JDK 動態代理，沒有實作任何介面就用 CGLIB
*   CGLIB 的代價來自「子類別」：final 類別不能被代理、final 方法不能被通知，因為子類別覆寫不了它們

**版本註記**：Spring Boot 的自動組態預設讓 Spring AOP 用 CGLIB 代理；要改用 JDK 代理，把 `spring.aop.proxy-target-class` 設成 false。[出處](https://docs.spring.io/spring-boot/reference/features/aop.html) 這個預設從 Spring Boot 2.0 開始，AOP 支援也包含在內。[出處](https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-2.0-Migration-Guide) 面試被問「為什麼 Boot 要改成 CGLIB」，答「這樣不必為了讓代理成立而替每個 Service 多開一個介面，注入具體類別也不會因為拿到 JDK 代理而轉型失敗」。切面、切入點、通知這些名詞與計時切面的範例見〈Spring AOP 與交易控制〉。

> 💡 面試官：為什麼同一個類別內部呼叫，@Transactional 或 @Cacheable 不會生效？

**一句話定義**：因為註解的行為長在代理物件上，內部呼叫用的是 `this`，沒經過代理。

**機制怎麼講**：容器交給別人的是代理；外部呼叫先到代理、跑完通知才轉給目標。呼叫一旦到了目標物件，它對自己發出的方法呼叫都是對 `this`、不是對代理，所以自我呼叫不會觸發綁在那個方法上的通知。[出處](https://docs.spring.io/spring-framework/reference/core/aop/proxying.html)

交易與快取都靠這套代理，所以兩者有同一個限制：在代理模式（預設）下，只有從外部經由代理進來的方法呼叫會被攔截。

*   自我呼叫 @Transactional 方法：執行期不會有實際的交易[出處](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html)
*   自我呼叫 @Cacheable 方法：執行期不會有實際的快取[出處](https://docs.spring.io/spring-framework/reference/integration/cache/annotations.html)

**解法怎麼答**：三條路，照推薦順序：[出處](https://docs.spring.io/spring-framework/reference/core/aop/proxying.html)

*   最推薦：重構程式碼，讓自我呼叫不會發生——把要被攔的方法搬到另一個 Bean
*   其次：把自己注入自己（注入進來的是代理），改對它呼叫
*   最不建議：`AopContext.currentProxy()`，它把程式碼完全綁死在 Spring AOP

真要讓自我呼叫也生效，交易可以改用 AspectJ 模式（`@EnableTransactionManagement(mode = AdviceMode.ASPECTJ)`），它直接改位元組碼、不靠代理。[出處](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html)

*【交易】*

## 傳播行為與失效情境

各情境的實跑結果見〈@Transactional 的傳播、隔離與失效情境〉。

> 💡 面試官：@Transactional 的傳播行為有哪些？REQUIRED 與 REQUIRES_NEW 差在哪？

**一句話定義**：傳播行為（propagation）決定「一個有交易的方法呼叫另一個有交易的方法時，裡面那層要加入外面的交易、另開一筆，還是不要交易」。Spring 定了七種，預設是 REQUIRED。[出處](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html)

| 傳播行為 | 外層有交易時 | 外層沒有交易時 |
| --- | --- | --- |
| REQUIRED（預設） | 加入現有交易 | 開一筆新的 |
| REQUIRES_NEW | 暫停外層，另開一筆獨立交易 | 開一筆新的 |
| NESTED | 在現有交易裡設一個儲存點（savepoint，交易中途的還原點），只還原到那裡 | 行為同 REQUIRED |
| SUPPORTS | 加入現有交易 | 不開交易、直接執行 |
| MANDATORY | 加入現有交易 | 丟例外 |
| NOT_SUPPORTED | 暫停外層，不在交易中執行 | 不開交易、直接執行 |
| NEVER | 丟例外 | 不開交易、直接執行 |

出處：[Propagation 列舉型別](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/transaction/annotation/Propagation.html)

**REQUIRED 與 REQUIRES_NEW 的差別**：差在「幾筆實體交易」。[出處](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/tx-propagation.html)

*   REQUIRED：內外兩層對應到同一筆實體交易，各自只是一個邏輯範圍。內層把交易標成只能還原（rollback-only）時，外層並不知情、照常提交，結果會拿到 UnexpectedRollbackException——用來清楚指出實際上做的是還原而不是提交
*   REQUIRES_NEW：每個交易範圍都用一筆獨立的實體交易，絕不參與外層既有的交易；底層的資源交易不同，可以各自提交或還原，內層還原不影響外層、內層的鎖也在它完成時就釋放

**實務註記：**[出處](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/tx-propagation.html)

*   REQUIRES_NEW 多吃一條資料庫連線：外層的還綁著，內層再取得自己的資源（例如一條新的資料庫連線）。這可能耗盡連線池，甚至造成死結；除非連線池至少比同時執行的執行緒數多 1，否則不要用
*   NESTED 靠 JDBC 的儲存點，只對 JDBC 資源交易有效，走 JPA 時別拿它當答案

ACID、隔離層級與 rollbackFor 見〈Spring AOP 與交易控制〉，交易邊界為什麼放服務層見〈Spring 資料存取〉。

> 💡 面試官：@Transactional 什麼情況會失效？

**一句話定義**：宣告式交易是 AOP 代理加上 TransactionInterceptor[出處](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/tx-decl-explained.html)，所以失效情境分兩類：代理攔不到，或攔到了但還原條件沒成立。

*   **方法不是 public**。在代理模式（預設）下，public 方法上的 @Transactional 一定有效；從 6.0 起，類別式代理預設也讓 protected 或套件可見的方法有交易；介面式代理（JDK 動態代理）的方法則一定要是 public，而且定義在被代理的介面裡。private 方法哪一種代理都攔不到。[出處](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html) 這一條是 Spring 5 到 6 的差異：Spring 5 只認 public。
*   **自我呼叫**。同一個類別裡沒交易的方法呼叫有交易的方法，走的是 `this`，執行期不會有實際的交易。[出處](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html) 同理，自己 `new` 出來的物件不是容器交出的代理，上面的註解不會生效。
*   **丟的是受檢例外**。預設只有執行期的非受檢例外（RuntimeException 與其子類別）會讓交易還原，Error 預設也會；受檢例外在預設組態下不會還原。要讓受檢例外也還原，用 `rollbackFor`。[出處](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/rolling-back.html)
*   **例外被吃掉**。還原的判斷是例外往上冒出呼叫堆疊時，由交易基礎建設接住未處理的例外來做的[出處](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/rolling-back.html)；方法內部 try／catch 把例外吞掉、只寫個日誌，例外到不了攔截器，交易照常提交。
*   **另開執行緒**。Spring 的交易資源是綁在執行緒上的——負責管理的 TransactionSynchronizationManager 就是以每條執行緒為單位管理資源與交易同步的中央委派。[出處](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/transaction/support/TransactionSynchronizationManager.html) 交易方法裡開新執行緒或丟進執行緒池的工作，跑在另一條執行緒上，拿不到這筆交易綁的連線，等於在交易外執行。

> 代理攔不到（非 public、自我呼叫、自己 new）→ 根本沒開交易；攔到了但受檢例外、例外被吃、換執行緒 → 開了卻不還原

*【Spring Boot 與 Spring MVC】*

## 自動組態、啟動註解與一次請求的路徑

實跑的條件報告與 Actuator 見〈Spring Boot 自動組態與 Actuator〉。

> 💡 面試官：Spring Boot 自動組態怎麼運作？

**一句話定義**：自動組態（auto-configuration）是根據你加了哪些 jar 相依，自動設定 Spring 應用程式。例如 classpath 上有 HSQLDB、你又沒有手動設定任何資料庫連線 Bean，Spring Boot 就自動組態一個記憶體內資料庫。[出處](https://docs.spring.io/spring-boot/reference/using/auto-configuration.html)

**機制分三層講：**

*   **候選者從哪來**：每個自動組態類別標 `@AutoConfiguration`，Spring Boot 檢查發布的 jar 裡有沒有 `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` 檔，一行一個類別名。自動組態類別只能透過列在 imports 檔裡載入，絕不能被元件掃描掃到。[出處](https://docs.spring.io/spring-boot/reference/features/developing-auto-configuration.html)
*   **要不要生效由條件決定：**@Conditional 家族——@ConditionalOnClass／OnMissingClass 看類別在不在、@ConditionalOnBean／OnMissingBean 看容器裡有沒有某個 Bean、@ConditionalOnProperty 看設定值、@ConditionalOnWebApplication 看是不是 Web 應用程式。自動組態類別應該標 @ConditionalOnClass，因為那個類別執行期可能不存在；用 @ConditionalOnMissingBean 是好習慣，讓開發者能覆寫你的預設。[出處](https://docs.spring.io/spring-boot/reference/features/developing-auto-configuration.html)
*   **你的設定永遠優先**：自動組態隨時可以被你自己的組態取代一部分，例如加了自己的 DataSource Bean，預設的內嵌資料庫支援就會退開。想知道哪些自動組態生效、為什麼，用 `--debug` 啟動會印出條件報告；要關掉某一個，用 `@SpringBootApplication(exclude = …)` 或 `spring.autoconfigure.exclude`。[出處](https://docs.spring.io/spring-boot/reference/using/auto-configuration.html)

**版本註記**：Spring Boot 2 的答案是 `META-INF/spring.factories` 裡的 EnableAutoConfiguration 鍵。3.0 移除了這條路，改用上面的 imports 檔；Boot 3 同時有三個地基變動：Java 17 起跳、javax 套件全面改 jakarta、底層升到 Spring Framework 6。[出處](https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-3.0-Migration-Guide)

> 💡 面試官：@SpringBootApplication 包了哪三個註解？

**一句話定義：**@EnableAutoConfiguration、@ComponentScan、@SpringBootConfiguration，一個 @SpringBootApplication 就同時啟用這三項：[出處](https://docs.spring.io/spring-boot/reference/using/using-the-springbootapplication-annotation.html)

*   @EnableAutoConfiguration：啟用 Spring Boot 的自動組態機制
*   @ComponentScan：在應用程式所在的套件上掃描 @Component
*   @SpringBootConfiguration：讓你註冊額外 Bean 或匯入額外組態類別；它取代 Spring 標準的 @Configuration，好處是整合測試能自動找到組態

**追問時要補的**：第三個常被答成 @Configuration，要答對是 @SpringBootConfiguration——它本身標了 @Configuration，多出來的價值是測試能自動找到它。@ComponentScan 掃的是啟動類別所在套件及其子套件，這是把啟動類別放最外層套件的理由。這三項功能都不是非用不可[出處](https://docs.spring.io/spring-boot/reference/using/using-the-springbootapplication-annotation.html)，而且 @SpringBootApplication 或 @EnableAutoConfiguration 只該加一個。[出處](https://docs.spring.io/spring-boot/reference/using/auto-configuration.html)

> 💡 面試官：Spring MVC 一次請求走過哪些元件？

**一句話定義**：Spring MVC 圍繞前端控制器模式設計：一個中央 Servlet（DispatcherServlet）提供共用的請求處理流程，實際工作交給可設定的委派元件。[出處](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-servlet.html)

| 順序 | 元件 | 做什麼 |
| --- | --- | --- |
| 1 | DispatcherServlet | 接下請求，把 WebApplicationContext、地區解析器綁上請求，檢查是不是多部分（檔案上傳）請求 |
| 2 | HandlerMapping | 把請求對應到一個處理器，連同一串做前後處理的攔截器；支援 @RequestMapping 的實作是 RequestMappingHandlerMapping |
| 3 | HandlerAdapter | 替 DispatcherServlet 呼叫對應的處理器，不論處理器實際上怎麼被呼叫——DispatcherServlet 就不必知道這些細節 |
| 4 | Controller | 你的處理器方法，回傳視圖名稱、模型，或直接回傳要序列化的物件 |
| 5a | ViewResolver | 把處理器回傳的字串邏輯視圖名稱解析成實際的 View，用來算繪回應 |
| 5b | HttpMessageConverter | 方法有 @ResponseBody（@RestController 就是 @Controller 加 @ResponseBody）時，回傳值透過 HttpMessageConverter 序列化到回應本體，不走視圖 |
| 例外 | HandlerExceptionResolver | 處理例外的策略，可能把例外交給處理器、HTML 錯誤視圖或其他目標；@ExceptionHandler 走的就是這條 |

出處：[特殊 Bean 型別](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-servlet/special-bean-types.html)、[處理順序](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-servlet/sequence.html)、[@ResponseBody](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-methods/responsebody.html)

**追問時要補的**：REST API 沒有視圖那一步。註解式控制器的回應可以在 HandlerAdapter 內直接算繪，不必回傳視圖[出處](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-servlet/sequence.html)，所以答 @RestController 的路徑時第 5 步講 HttpMessageConverter，不講 ViewResolver。取參數的註解見〈Spring MVC 與 RESTful API〉；DispatcherServlet 之外的例外為什麼 @ControllerAdvice 抓不到，見〈Maven、微服務與全域例外〉。

> 💡 面試官：Filter、Interceptor、AOP 三者的位置與分工？

**一句話定義**：三個都是「在正事前後插一段共同邏輯」，差在插在哪一層：Filter 在 Servlet 容器、DispatcherServlet 之前；Interceptor 在 DispatcherServlet 之內、Controller 前後；AOP 在任何 Bean 的方法上，跟 Web 無關。

|   | Filter | Interceptor（HandlerInterceptor） | Spring AOP |
| --- | --- | --- | --- |
| 誰定義的 | Jakarta Servlet 規格：對資源的請求、回應或兩者做過濾的物件[出處](https://jakarta.ee/specifications/servlet/6.0/apidocs/jakarta.servlet/jakarta/servlet/filter) | Spring MVC；由 HandlerMapping 連同處理器一起交出[出處](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-servlet/special-bean-types.html) | Spring Framework；在 Spring AOP 裡，連接點永遠是一次方法執行[出處](https://docs.spring.io/spring-framework/reference/core/aop/introduction-defn.html) |
| 看得到什麼 | 原始的 HttpServletRequest／Response，還不知道會交給哪個 Controller | 請求加上「處理器」——知道要進哪個 Controller 方法 | 方法的參數、回傳值與例外；不知道 HTTP |
| 幾個切入時機 | doFilter 一個，前後自己包 | preHandle（回 false 就略過其餘的執行鏈、不呼叫處理器）、postHandle、afterCompletion[出處](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-servlet/handlermapping-interceptor.html) | Before、After、AfterReturning、AfterThrowing、Around |
| 典型用途 | 編碼、CORS、Spring Security 的整條安全鏈 | 請求追蹤、地區判斷這類 MVC 流程的事 | 交易、快取、計時、稽核日誌 |

**追問時要補的**：兩個坑。

*   **第一，安全不要放 Interceptor**：攔截器的路徑比對可能跟註解式控制器不一致，不適合當安全層；一般建議用 Spring Security，或整合進 Servlet Filter 鏈、盡早套用的類似做法。[出處](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-config/interceptors.html) Spring Security 就在 Filter 這一層：整組安全 Filter 裝在 FilterChainProxy（Spring Security 提供的特殊 Filter，透過 SecurityFilterChain 委派給許多 Filter），再由 DelegatingFilterProxy 註冊進容器。[出處](https://docs.spring.io/spring-security/reference/servlet/architecture.html)
*   **第二，postHandle 對 REST API 幾乎沒用**：@ResponseBody 與 ResponseEntity 的控制器方法，回應在 HandlerAdapter 內就已寫出並提交，postHandle 才被呼叫；要改回應本體得用 ResponseBodyAdvice。[出處](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-servlet/handlermapping-interceptor.html)

Spring Security 的 Filter 鏈見〈Spring Security 認證與授權〉，Filter 與 DispatcherServlet 的先後見〈Maven、微服務與全域例外〉。

### 重點整理

*   IoC 是「誰負責建立相依」的原則，DI 是「容器把相依送進去」的手段；ApplicationContext 是 BeanFactory 的子介面，多了自動註冊後置處理器、事件、國際化，沒有好理由就用它。
*   singleton 是「每個容器一份共用實例」，執行緒安不安全取決於 Bean 有沒有可變狀態；生命週期順序：屬性填入 → Aware → 後置處理器前置 → @PostConstruct → afterPropertiesSet → init → 後置處理器後置。
*   必要相依用建構子注入（不可變、不為 null）；建構子注入下的循環相依直接丟 BeanCurrentlyInCreationException，Spring Boot 2.6 起循環參考預設禁止，正解是重新設計。
*   Spring AOP 代理有 JDK 動態代理與 CGLIB 兩種，Spring Boot 2.0 起預設 CGLIB；同類別內部呼叫走 this 不經代理，所以 @Transactional 與 @Cacheable 都不生效，首選解法是重構、不是 AopContext。
*   REQUIRED 是同一筆實體交易、內層標還原外層會拿到 UnexpectedRollbackException；REQUIRES_NEW 另開一筆、多吃一條連線。
*   @Transactional 失效五情境：非 public（Spring 6 起類別式代理放寬到 protected）、自我呼叫、受檢例外預設不還原、例外被吃掉、另開執行緒。
*   Spring Boot 3 起自動組態靠 AutoConfiguration.imports 檔加 @Conditional 條件，spring.factories 是 Boot 2 的答案；@SpringBootApplication ＝ @EnableAutoConfiguration ＋ @ComponentScan ＋ @SpringBootConfiguration。

## 隨堂測驗

**Q1. 面試官問「IoC 跟 DI 是同一件事嗎？」最準確的回答是？**

- (A) IoC 是「物件不自己建立相依、交給容器」的原則，DI 是實現它的一種做法（容器把相依注入進來）
- (B) IoC 是 Spring 的容器名稱，DI 是 Spring Boot 的容器名稱
- (C) DI 是原則，IoC 是 Spring 對 DI 的實作
- (D) 兩者完全同義，只是不同年代的叫法

<details><summary>看答案</summary>

**答案：(A)** DI 是 IoC 的做法：物件宣告需要什麼、容器建立時注入，這正好是物件自己控制相依的反面。

</details>

**Q2. 一個沒有任何可變欄位、只持有注入相依的 singleton Service，被多個請求同時呼叫時會怎樣？**

- (A) 沒有共用狀態可以壞，所以沒有執行緒安全問題——問題只在 Bean 放了可變欄位時才出現
- (B) Spring 會替每個請求複製一份，所以永遠安全
- (C) singleton 天生不安全，必須全部改成 prototype
- (D) 容器會自動對方法加鎖，所以安全

<details><summary>看答案</summary>

**答案：(A)** singleton 是同一個實例被所有請求共用；容器不加鎖也不複製，安不安全取決於 Bean 有沒有可變狀態。

</details>

**Q3. 同一個 Bean 同時實作 InitializingBean、標了 @PostConstruct、又設了自訂 init 方法，三者的執行順序是？**

- (A) @PostConstruct → afterPropertiesSet() → 自訂 init 方法
- (B) afterPropertiesSet() → @PostConstruct → 自訂 init 方法
- (C) 自訂 init 方法 → afterPropertiesSet() → @PostConstruct
- (D) 三者順序不固定，看宣告先後

<details><summary>看答案</summary>

**答案：(A)** 多種生命週期機制同時用時，註解最先、介面回呼其次、自訂方法最後；銷毀也是同樣順序。

</details>

**Q4. A 用建構子注入 B、B 用建構子注入 A，在 Spring Boot 3 上啟動會發生什麼？**

- (A) 啟動失敗，丟 BeanCurrentlyInCreationException；官方建議重新設計打破循環
- (B) 容器先交出 A 的半成品給 B，兩個都能建好
- (C) 容器自動把其中一方改成延遲載入，正常啟動
- (D) 只會印警告，兩個 Bean 都是 null

<details><summary>看答案</summary>

**答案：(A)** 建構子注入要求建立當下就拿到完整相依，循環無解；而且 Boot 2.6 起循環參考預設禁止，setter 注入那條「半成品」路也被關掉了。

</details>

**Q5. 容器裡有兩個 Printer 實作，某個注入點就是要 hpPrinter，其他地方都用預設那一個。最合適的組合是？**

- (A) 預設那一個的定義標 @Primary，那個注入點加 @Qualifier("hpPrinter")
- (B) 兩個都標 @Primary，讓容器自己挑
- (C) 兩個注入點都改用 @Resource，不寫名稱
- (D) 把其中一個實作從元件掃描拿掉

<details><summary>看答案</summary>

**答案：(A)** @Primary 表達「沒指定時預設給這個」，@Qualifier 表達「這裡就要那一個」；需要更細地控制選哪個時才用 @Qualifier。

</details>

**Q6. Spring Boot 專案裡一個 Service 實作了介面，Spring AOP 替它建的代理預設是哪一種？**

- (A) CGLIB 子類別代理——Spring Boot 2.0 起預設 proxy-target-class 為 true，不看有沒有介面
- (B) JDK 動態代理——因為它有實作介面
- (C) 兩種都建，由呼叫端決定用哪一個
- (D) 不建代理，直接用原物件

<details><summary>看答案</summary>

**答案：(A)** 純 Spring Framework 才是「有介面就 JDK 動態代理」；Spring Boot 預設把 Spring AOP 設成 CGLIB 代理，要 JDK 代理得自己把屬性設成 false。

</details>

**Q7. 同一個類別裡，沒有 @Transactional 的 a() 呼叫了有 @Transactional 的 b()，外部只呼叫 a()。b() 的交易會生效嗎？**

- (A) 不會——a() 對 b() 的呼叫走 this、沒經過代理，交易攔截器根本沒介入
- (B) 會——只要 b() 有標註解，容器就會在它進入時開交易
- (C) 會——因為 CGLIB 代理是子類別，內部呼叫也會被覆寫的方法攔到
- (D) 不會，但把 a() 也標上 @Transactional 就能讓 b() 另開一筆交易

<details><summary>看答案</summary>

**答案：(A)** 代理模式下只有從外部經由代理進來的呼叫會被攔截，自我呼叫不會產生實際的交易。CGLIB 是子類別也沒用，因為 this 指的仍是目標物件。

</details>

**Q8. 外層方法用 REQUIRED，呼叫另一個 Bean 上同樣標 REQUIRED 的方法，內層丟出 RuntimeException 但被外層 catch 住、外層繼續正常結束。提交時會怎樣？**

- (A) 外層提交時拿到 UnexpectedRollbackException——內層已把同一筆實體交易標成只能還原
- (B) 外層照常提交，因為例外已經被接住了
- (C) 只有內層的變更被還原，外層的變更成功提交
- (D) 內層自動改成 REQUIRES_NEW，各自獨立

<details><summary>看答案</summary>

**答案：(A)** REQUIRED 之下內外是同一筆實體交易；內層標了 rollback-only 而外層不知情照常提交，所以丟這個例外來明確告知實際做的是還原。

</details>

**Q9. @Transactional 方法丟出一個自訂的受檢例外（extends Exception），沒有額外設定。交易會還原嗎？**

- (A) 不會——預設只對 RuntimeException 與 Error 還原，要還原得設 rollbackFor
- (B) 會——任何例外離開交易方法都會還原
- (C) 會——受檢例外比執行期例外更嚴重，所以優先還原
- (D) 不會還原也不會提交，交易會卡在待決狀態

<details><summary>看答案</summary>

**答案：(A)** 交易方法丟出的受檢例外在預設組態下不會讓交易還原，這是最常見的失效情境之一。

</details>

**Q10. Spring Boot 3 以後，一個 starter 要讓自己的自動組態類別被找到，正確做法是？**

- (A) 列在 META-INF/​spring/​org.​springframework.​boot.​autoconfigure.​AutoConfiguration.​imports 檔裡，一行一個類別名
- (B) 寫進 META-INF/spring.factories 的 EnableAutoConfiguration 鍵
- (C) 把類別放進應用程式的元件掃描範圍
- (D) 在 @SpringBootApplication 的 scanBasePackages 加上 starter 的套件

<details><summary>看答案</summary>

**答案：(A)** Spring Boot 3.0 移除了 spring.factories 那條路；自動組態類別只能靠 imports 檔載入、絕不能成為元件掃描的目標。

</details>
