# 11. Spring Boot 單元測試

> 來源：[筆記平台 · Spring 後端](https://hhtim.github.io/notes-platform/spring/#/lesson/spring-unittest)　第 11 課 / 共 23 課 · 約 11 分鐘

**用 JUnit、Mockito 與「準備、執行、驗證」三段式，寫出快速、獨立又能說清楚需求的服務層測試。**

### 讀完這課你會

*   用「準備、執行、驗證」三段式組織一個單元測試
*   分辨替身物件、被測物件與各種生命週期註解
*   正確使用 stub、verify 與參數比對器
*   設計正向、負向、例外與邊界四個方向的案例

*【只測一小塊，不把整個系統搬進來】*

## 什麼是單元測試

單元測試聚焦在一小段程式，例如 Service 的某一個方法。它像把一顆齒輪單獨放上測試台：隔離掉資料庫、網路與其他元件之後，只檢查這顆齒輪在不同輸入下會不會產生預期結果。

Mockito 負責建立替身物件（Mock），讓測試控制相依物件的回應；JUnit Jupiter 則提供測試執行、生命週期與斷言功能。

| 註解 | 用途 |
| --- | --- |
| `@Test` | 標記測試方法 |
| `@Mock` | 建立相依物件的替身 |
| `@InjectMocks` | 建立被測物件，並把可用的替身注入進去 |
| `@BeforeEach`／`@AfterEach` | 每個測試前／後執行 |
| `@BeforeAll`／`@AfterAll` | 整個測試類別前／後執行一次 |
| `@DisplayName` | 提供好讀的測試名稱 |
| `@ParameterizedTest` | 用多組參數重複執行同一段測試邏輯 |
| `@Disabled` | 暫時停掉這個測試 |

如果測試啟動了完整的 Spring 容器、連了真的資料庫，或跨越多個元件，那比較接近整合測試，不是純單元測試。

*【先布置舞台，再演出，最後核對】*

## 準備、執行、驗證

把測試分成三段，讀的人就能很快回答三個問題：測試準備了什麼、執行了什麼、期待什麼結果。英文常寫成 Arrange、Act、Assert。

```
@ExtendWith(MockitoExtension.class)
class OrderServiceTest {
    @Mock
    private OrderRepository orderRepository;

    @InjectMocks
    private OrderService orderService;

    @Test
    void cancelOrder_當倉儲刪除一筆_回傳成功() {
        // 準備：安排輸入與相依物件的行為
        when(orderRepository.deleteByOrderNo(eq("A001"))).thenReturn(1);

        // 執行：只做一次被測行為
        boolean result = orderService.cancelOrder("A001");

        // 驗證：檢查結果與重要的互動
        assertTrue(result);
        verify(orderRepository).deleteByOrderNo(eq("A001"));
    }
}
```

「準備」不只是建測試資料，也包含設定替身的行為。「執行」盡量精簡，讓人一眼看出被測的動作是哪一個。「驗證」可以檢查回傳值、例外、狀態變化，以及必要的協作行為。

*【規定替身怎麼回答，再確認它真的被叫到】*

## Stub 與互動驗證

`when(...).thenReturn(...)` 是替替身安排回答（stub）；`verify(...)` 是確認某個呼叫有沒有發生。兩者用途不同，不要只安排了回應卻完全忘了檢查結果。

```
when(sqlTemplateLoader.load(anyString(), anyMap()))
    .thenReturn("DELETE FROM order_item WHERE order_no = :ORDER_NO");

verify(orderRepository, times(1))
    .deleteByOrderNo(eq("A001"));

verify(notificationClient, never())
    .send(any());
```

驗證互動時只鎖定對需求重要的呼叫。如果把每一個內部呼叫的順序都綁死，之後重構實作但行為沒變，測試也會無謂地一大片紅掉。

*【重要的精確比對，不重要的放寬】*

## 參數比對器的使用規則

*   **eq(value)**：參數必須等於指定的值。
*   **any()**：接受符合方法型別的任意值。
*   **isNull()／isNotNull()**：明確要求是空值或不是空值。
*   **startsWith(...)／contains(...)**：比對字串的特徵。
*   **argThat(...)**：用自訂條件檢查比較複雜的物件。

```
when(sqlTemplateLoader.load(
    eq("order-cancel.sql"),
    argThat(params ->
        "A001".equals(params.get("ORDER_NO"))
        && params.containsKey("AMOUNT"))
)).thenReturn(expectedSql);
```

同一次方法呼叫裡，只要有一個參數用了比對器，其他參數也都要用比對器包起來。

```
// 正確
when(client.call(eq("exact"), anyInt())).thenReturn("OK");

// 錯誤：直接值與比對器混用
when(client.call("exact", anyInt())).thenReturn("OK");
```

混用直接值與比對器不會編譯失敗。這個寫法是錯的，會丟出例外，因為第三個參數沒有用參數比對器給——注意是丟出例外，不是編譯錯誤。編譯得過的原因：`eq()` 這類比對器方法並不回傳比對器，而是在內部把比對器記到一個堆疊上，再回傳一個假值（通常是 null）。既然回傳的是符合參數型別的值，編譯器當然看不出問題，錯誤要到執行時才冒出來[出處](https://site.mockito.org/javadoc/current/org/mockito/ArgumentMatchers.html)。

> 📝 查證更正：原筆記在這個例子旁邊註解「編譯錯誤！一旦使用 matcher，所有參數都要用 matcher」，查證後更正：混用直接值與比對器不會編譯失敗——比對器方法的回傳型別就是參數型別，編譯器看不出問題；它是在執行到那一行 stub 或 verify 時丟出 Mockito 的 InvalidUseOfMatchersException

後續如果要對同一個參數做好幾項斷言，可以改用 `ArgumentCaptor` 把實際參數抓出來。只需要判斷一個條件時，`argThat` 通常比較精簡。

*【不只證明會成功，也要證明怎麼失敗】*

## 測試案例的四個方向

| 方向 | 例子 | 要驗證的重點 |
| --- | --- | --- |
| 正向 | 合法訂單編號成功刪除一筆資料 | 結果正確，必要的相依方法被呼叫 |
| 負向 | 必填欄位是 `null` 或空字串 | 系統拒絕這個輸入，而且沒有真的去刪資料 |
| 例外 | SQL 產生器或資料存取元件丟出例外 | 例外被正確傳遞或轉換，後續操作停下來 |
| 邊界 | 零、最大值、空集合、單一元素、跨月日期 | 臨界點以及它前後的行為符合規則 |

負向測試最容易寫歪。舉個常見的寫法：把必填欄位設成 `null`，接著安排成必填欄位為空時會產生另一段 SQL、刪除回傳 0 筆，最後驗證刪除方法有被呼叫一次。這樣沒有測到任何驗證規則，它證明的只是「空值也會照跑一次刪除」。負向測試要先定義預期是什麼：丟出驗證例外、回傳錯誤，還是允許查無資料，再據此寫斷言。

> 好的測試案例是在保存業務規則，不是在替目前的實作湊出綠燈。

*【錯誤路徑也要驗證「沒有發生什麼」】*

## 例外與提前中止

```
@Test
void cancelOrder_當SQL產生失敗_不執行刪除() {
    when(sqlTemplateLoader.load(anyString(), anyMap()))
        .thenThrow(new IllegalStateException("樣板讀取失敗"));

    IllegalStateException error = assertThrows(
        IllegalStateException.class,
        () -> orderService.cancelOrder("A001")
    );

    assertEquals("樣板讀取失敗", error.getMessage());
    verify(orderRepository, never()).deleteByOrderNo(any());
}
```

`assertThrows` 驗證例外型別，也會把例外回傳讓你繼續檢查。搭配 `never()` 就能確認前一步失敗之後，有副作用的刪除操作沒有繼續執行。

*【名稱就是失敗時的第一份診斷報告】*

## 命名、獨立性與覆蓋率

測試名稱可以用「方法＿情境＿預期結果」的格式：

```
cancelOrder_當請求合法_回傳成功
cancelOrder_當訂單編號為空_丟出驗證例外
cancelOrder_當資料庫失敗_不繼續執行
cancelOrder_當序號為最大值_原樣傳遞
```

*   每個測試都要能獨立執行，不依賴其他測試的先後順序。
*   共用資料在 `@BeforeEach` 重建，避免測試互相汙染。
*   優先測公開行為、條件分支、例外路徑與業務邊界。
*   單純的 getter、setter 或框架本身不必重複寫測試。
*   輔助方法可以減少重複，但不要把案例之間的重要差異全藏起來。

常聽到的兩條原則——「每個 public 方法都要測試」和「不要測 getter、setter 這類簡單方法」——其實會互相打架。比較實用的是後者：看方法裡有沒有值得保護的規則，而不是看它是不是公開的。

覆蓋率能指出哪些程式碼還沒被執行過，但不能證明斷言是對的。高覆蓋率是線索，不是測試品質的保證。

### 重點整理

*   單元測試要隔離外部相依，專注驗證一個小行為。
*   三段式分別是準備、執行、驗證。
*   `when` 安排替身的回應，`verify` 檢查重要的互動。
*   同一次呼叫只要用了比對器，其他參數也要用比對器；混用不會編譯失敗，是執行時才爆。
*   案例要涵蓋正向、負向、例外與邊界，負向測試必須真的對到需求裡的規則。
*   覆蓋率取代不了有意義的斷言。

## 隨堂測驗

**Q1. 在「準備、執行、驗證」三段式裡，「執行」這一段負責什麼？**

- (A) 執行被測的方法或行為
- (B) 建立所有替身與測試資料
- (C) 檢查回傳值與互動
- (D) 啟動完整的正式環境

<details><summary>看答案</summary>

**答案：(A)** 準備負責布置，執行只做被測動作，驗證才檢查結果。

</details>

**Q2. @Mock 與 @InjectMocks 的典型分工是什麼？**

- (A) 前者建立相依物件的替身，後者建立被測物件並把替身注入進去
- (B) 前者啟動資料庫，後者清除資料表
- (C) 前者標記測試方法，後者停用測試
- (D) 前者驗證例外，後者比對字串

<details><summary>看答案</summary>

**答案：(A)** @Mock 用在相依元件，@InjectMocks 用在被測物件本身。

</details>

**Q3. when(​repository.​find(...)).​thenReturn(​value) 的主要用途是什麼？**

- (A) 安排替身在特定呼叫下回傳指定結果
- (B) 驗證方法剛好被呼叫一次
- (C) 擷取方法實際收到的參數
- (D) 斷言被測方法一定會丟出例外

<details><summary>看答案</summary>

**答案：(A)** 這是建立 stub，控制替身怎麼回答。

</details>

**Q4. 同一次 Mockito 呼叫裡已經用了 anyInt()，固定的字串參數應該怎麼寫？**

- (A) 用 eq("exact")
- (B) 直接寫 "exact" 跟比對器混用
- (C) 改用 assertEquals("exact") 當參數
- (D) 改用 verifyNoInteractions("exact")

<details><summary>看答案</summary>

**答案：(A)** 只要有一個參數用了比對器，同一次呼叫的其他參數也要用比對器。

</details>

**Q5. 直接值與參數比對器混用時，錯誤在什麼時候出現？**

- (A) 編譯會過，執行時才丟出 InvalidUseOfMatchersException
- (B) 編譯階段就會失敗
- (C) 完全不會出錯
- (D) 只有在整合測試才會出錯

<details><summary>看答案</summary>

**答案：(A)** 比對器方法的回傳型別就是參數型別，編譯器看不出問題；執行到那一行 stub 或 verify 時 Mockito 就丟出 InvalidUseOfMatchersException。

</details>

**Q6. 測試 SQL 產生器丟出例外時，為什麼還要驗證刪除方法從未被呼叫？**

- (A) 確認流程已經中止，沒有繼續執行有副作用的操作
- (B) 確認替身會自動連上真的資料庫
- (C) 確認例外已經被轉成成功結果
- (D) 確認所有測試會依固定順序執行

<details><summary>看答案</summary>

**答案：(A)** 除了驗證例外，也要確認失敗之後沒有把資料刪掉。

</details>

**Q7. 下列哪一項最符合邊界測試？**

- (A) 測允許數量的最大值，以及最大值前後的行為
- (B) 只測最常見的一組正常輸入
- (C) 改用正式資料庫跑完所有案例
- (D) 只確認替身物件可以成功建立

<details><summary>看答案</summary>

**答案：(A)** 邊界測試關注臨界值與它前後的位置，例如零、最大值與空集合。

</details>

**Q8. 需求規定訂單編號不可為空，最有力的負向測試該驗證什麼？**

- (A) 空值被明確拒絕，而且刪除方法不會執行
- (B) 空值仍然產生 SQL 並完成呼叫
- (C) 測試只要沒當機就算過
- (D) 把訂單編號替換成任何非空字串

<details><summary>看答案</summary>

**答案：(A)** 負向測試要對上實際的規則，並確認無效輸入沒有觸發副作用。

</details>

**Q9. 為什麼高程式碼覆蓋率不一定代表測試品質好？**

- (A) 程式碼可能被執行過，但測試沒有做有意義的斷言
- (B) 覆蓋率只適用於前端 CSS
- (C) 覆蓋率越高表示測試一定互相依賴
- (D) 覆蓋率無法計算任何條件分支

<details><summary>看答案</summary>

**答案：(A)** 覆蓋率衡量的是執行範圍，不會判斷斷言有沒有真的驗證到需求。

</details>
