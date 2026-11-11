# lip-svc-cln-todo

## lip-svc-cln-todo｜待辦與覆核清單服務

## 專案架構

此 Spring Boot REST service 專注彙整不同角色與案件流程的待辦清單，並提供部分待辦參數設定及覆核/委員會待辦查詢。適合從「清單類 API」理解資料聚合與狀態篩選，不是交易寫入服務。

| 功能群組 | 程式中可見範例 | 入口 |
| --- | --- | --- |
| 角色/流程待辦 | PS、徵審、產包、補件及資深副總/督導副總待辦。 | `TodoController` |
| 覆核與委員會 | 待辦筆數、委員會待辦筆數、待辦清單及委員會清單。 | `ReviewController` |
| API 型態 | 以 `POST` 查詢為主，回傳分頁/清單相關 Tranrs。 | 確切分頁、排序、權限與狀態條件需按各電文契約核對。 |

## API 慣例

待辦入口分在 `TodoController` 與 `ReviewController`，常見 POST 查詢如 `/todoPsList/query`、`/todoAList/query`、`/committeeTodo/query`。查詢欄位、權限和狀態條件需逐支核對 Tranrq 契約。

## 實作流程

**確認角色與清單** PS、徵審、產包、補件或覆核

**核對請求條件** 使用者、單位與案件條件

**追蹤 Service 查詢** 檢查資料來源與狀態篩選

**組合清單回應** 確認排序、筆數與空集合

**回到呼叫端** 確認後續動作使用哪個 API

## 完整案例

**與 Query API 的差別**

todo service 的焦點是跨案件與角色的工作佇列，不是單筆案件的完整查詢，也不負責執行待辦所代表的異動；後續動作通常由其他 transaction/API 完成，呼叫關係需由實際消費端確認。

**pom.xml 專案依賴與 Java 版本 XML · 92 行**

lip-svc-cln-todo/pom.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>cub.cloud</groupId>
        <artifactId>cub-cloud</artifactId>
        <version>1.1.1</version>
        <relativePath/><!-- lookup parent from repository -->
    </parent>

    <groupId>cub.lip</groupId>
    <artifactId>lip-svc-cln-todo</artifactId>
    <properties>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <java.version>1.8</java.version>
        <tomcat.version>9.0.102</tomcat.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>cub.lip</groupId>
            <artifactId>lip-lib-cln-common</artifactId>
            <version>1.0.0-SNAPSHOT</version>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
            <scope>provided</scope>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web-services</artifactId>
        </dependency>
        <!-- axis 1.4 -->
        <dependency>
            <groupId>commons-discovery</groupId>
            <artifactId>commons-discovery</artifactId>
            <version>0.2</version>
            <exclusions>
                <exclusion>
                    <groupId>commons-logging</groupId>
                    <artifactId>commons-logging</artifactId>
                </exclusion>
            </exclusions>
        </dependency>
        <dependency>
            <groupId>org.apache.axis</groupId>
            <artifactId>axis</artifactId>
            <version>1.4</version>
        </dependency>
        <dependency>
            <groupId>org.apache.axis</groupId>
            <artifactId>axis-jaxrpc</artifactId>
            <version>1.4</version>
        </dependency>
        <dependency>
            <groupId>org.apache.axis</groupId>
            <artifactId>axis-saaj</artifactId>
            <version>1.4</version>
        </dependency>
        <dependency>
            <groupId>wsdl4j</groupId>
            <artifactId>wsdl4j</artifactId>
        </dependency>
        <dependency>
            <groupId>ebaf.commons</groupId>
            <artifactId>BankCmn4eBAF</artifactId>
            <version>0.0.3</version>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-devtools</artifactId>
            <optional>true</optional>
        </dependency>
    </dependencies>
    <build>
        <finalName>lip-svc-cln-todo</finalName>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
```

**LipSvcClnTodoApplication.java Spring Boot 啟動類別 Java · 16 行**

lip-svc-cln-todo/src/main/java/cub/lip/svc/cln/todo/LipSvcClnTodoApplication.java

```java
package cub.lip.svc.cln.todo;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cache.annotation.EnableCaching;

@SpringBootApplication
@EnableCaching
//@EnableJpaRepositories(repositoryBaseClass = CUBRepositoryImpl.class, bootstrapMode = BootstrapMode.DEFERRED)
public class LipSvcClnTodoApplication {

    public static void main(String[] args) {
        SpringApplication.run(LipSvcClnTodoApplication.class, args);
    }

}
```

**TodoController.java PS、徵審、產包、補件等待辦 Java · 204 行**

lip-svc-cln-todo/src/main/java/cub/lip/svc/cln/todo/controller/TodoController.java

```java
package cub.lip.svc.cln.todo.controller;

import java.io.IOException;

import javax.validation.Valid;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.validation.Errors;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import cub.lip.lib.common.controller.BaseController;
import cub.lip.lib.common.dto.base.RequestTemplate;
import cub.lip.lib.common.dto.base.ResponseTemplate;
import cub.lip.lib.common.exception.DataNotFoundException;
import cub.lip.lib.common.exception.RestException;
import cub.lip.svc.cln.todo.dto.cto.CTOTODOAQ001Tranrq;
import cub.lip.svc.cln.todo.dto.cto.CTOTODOAQ001Tranrs;
import cub.lip.svc.cln.todo.dto.cto.CTOTODODQ001Tranrq;
import cub.lip.svc.cln.todo.dto.cto.CTOTODODQ001Tranrs;
import cub.lip.svc.cln.todo.dto.cto.CTOTODOPQ001Tranrq;
import cub.lip.svc.cln.todo.dto.cto.CTOTODOPQ001Tranrs;
import cub.lip.svc.cln.todo.dto.cto.CTOTODOPQ002Tranrq;
import cub.lip.svc.cln.todo.dto.cto.CTOTODOPQ002Tranrs;
import cub.lip.svc.cln.todo.dto.cto.CTOTODOSQ001Tranrq;
import cub.lip.svc.cln.todo.dto.cto.CTOTODOSQ001Tranrs;
import cub.lip.svc.cln.todo.dto.cto.CTOTODOVQ001Tranrq;
import cub.lip.svc.cln.todo.dto.cto.CTOTODOVQ001Tranrs;
import cub.lip.svc.cln.todo.dto.cto.CTOTODOVQ002Tranrq;
import cub.lip.svc.cln.todo.dto.cto.CTOTODOVQ002Tranrs;
import cub.lip.svc.cln.todo.svc.CTOTODOAQ001Svc;
import cub.lip.svc.cln.todo.svc.CTOTODODQ001Svc;
import cub.lip.svc.cln.todo.svc.CTOTODOPQ001Svc;
import cub.lip.svc.cln.todo.svc.CTOTODOPQ002Svc;
import cub.lip.svc.cln.todo.svc.CTOTODOSQ001Svc;
import cub.lip.svc.cln.todo.svc.CTOTODOVQ001Svc;
import cub.lip.svc.cln.todo.svc.CTOTODOVQ002Svc;
import io.swagger.v3.oas.annotations.Operation;

/**
 * TodoController
 *
 * @author 00550352
 */
@RestController
@RequestMapping("/todo")
public class TodoController extends BaseController {

    /** CTOTODOPQ001Svc PS待辦事項查詢 */
    @Autowired
    private CTOTODOPQ001Svc theCTOTODOPQ001Svc;

    /** CTOTODOPQ002Svc PS查詢待辦參數設定 */
    @Autowired
    private CTOTODOPQ002Svc theCTOTODOPQ002Svc;

    /** CTOTODOAQ001Svc 徵審待辦事項查詢 */
    @Autowired
    private CTOTODOAQ001Svc theCTOTODOAQ001Svc;

    /** CTOTODODQ001Svc 產包待辦事項查詢 */
    @Autowired
    private CTOTODODQ001Svc theCTOTODODQ001Svc;

    /** CTOTODOSQ001Svc 補件待辦事項查詢 */
    @Autowired
    private CTOTODOSQ001Svc theCTOTODOSQ001Svc;

    /** CTOTODOVQ001Svc 資深副總&督導副總待辦事項查詢 */
    @Autowired
    private CTOTODOVQ001Svc theCTOTODOVQ001Svc;

    /** CTOTODOVQ002Svc 資深副總&督導副總查詢待辦參數設定 */
    @Autowired
    private CTOTODOVQ002Svc theCTOTODOVQ002Svc;

    /**
     * LIP-B-CTOTODOPQ001 PS待辦事項查詢
     *
     * @param req
     * @param err
     * @return
     * @throws IOException
     */
    @PostMapping("/todoPsList/query")
    @Operation(summary = "LIP-B-CTOTODOPQ001 PS待辦事項查詢")
    public ResponseTemplate<CTOTODOPQ001Tranrs> queryTodoPsList(@Valid
    @RequestBody
    RequestTemplate<CTOTODOPQ001Tranrq> req, Errors err) throws IOException, ClassNotFoundException, DataNotFoundException, RestException {
        validateRequest(err);
        return theCTOTODOPQ001Svc.queryTodoPsList(req);
    }

    /**
     * LIP-B-CTOTODOPQ002 PS查詢待辦參數設定
     *
     * @param req
     * @param err
     * @return
     * @throws IOException
     */
    @PostMapping("/todoPsList/querySetting")
    @Operation(summary = "LIP-B-CTOTODOPQ002 PS查詢待辦參數設定")
    public ResponseTemplate<CTOTODOPQ002Tranrs> queryTodoPsListSetting(@Valid
    @RequestBody
    RequestTemplate<CTOTODOPQ002Tranrq> req, Errors err) throws IOException, RestException {
        validateRequest(err);
        return theCTOTODOPQ002Svc.queryTodoPsListSetting(req);
    }

    /**
     * LIP-B-CTOTODOAQ001 徵審待辦事項查詢
     *
     * @param req
     * @param err
     * @return
     * @throws IOException
     */
    @PostMapping("/todoAList/query")
    @Operation(summary = "LIP-B-CTOTODOAQ001 徵審待辦事項查詢")
    public ResponseTemplate<CTOTODOAQ001Tranrs> queryTodoAList(@Valid
    @RequestBody
    RequestTemplate<CTOTODOAQ001Tranrq> req, Errors err) throws IOException {
        validateRequest(err);
        return theCTOTODOAQ001Svc.queryTodoAList(req);
    }

    /**
     * LIP-B-CTOTODODQ001 產包待辦事項查詢
     *
     * @param req
     * @param err
     * @return
     * @throws IOException
     */
    @PostMapping("/todoDList/query")
    @Operation(summary = "LIP-B-CTOTODODQ001 產包待辦事項查詢")
    public ResponseTemplate<CTOTODODQ001Tranrs> queryTodoDList(@Valid
    @RequestBody
    RequestTemplate<CTOTODODQ001Tranrq> req, Errors err) throws IOException {
        validateRequest(err);
        return theCTOTODODQ001Svc.queryTodoDList(req);
    }

    /**
     * LIP-B-CTOTODOSQ001 補件待辦事項查詢
     *
     * @param req
     * @param err
     * @return
     * @throws IOException
     */
    @PostMapping("/todoSList/query")
    @Operation(summary = "LIP-B-CTOTODOSQ001 補件待辦事項查詢")
    public ResponseTemplate<CTOTODOSQ001Tranrs> queryTodoSList(@Valid
    @RequestBody
    RequestTemplate<CTOTODOSQ001Tranrq> req, Errors err) throws IOException, ClassNotFoundException, DataNotFoundException, RestException {
        validateRequest(err);
        return theCTOTODOSQ001Svc.queryTodoSList(req);
    }

    /**
     * LIP-B-CTOTODOVQ001 資深副總&督導副總待辦事項查詢
     * 
     * @param req
     * @param err
     * @return
     * @throws DataNotFoundException
     * @throws RestException
     * @throws IOException
     * @throws ClassNotFoundException
     */
    @PostMapping("/todoVList/query")
    @Operation(summary = "LIP-B-CTOTODOVQ001 資深副總&督導副總待辦事項查詢")
    public ResponseTemplate<CTOTODOVQ001Tranrs> queryTodoVList(@Valid
    @RequestBody
    RequestTemplate<CTOTODOVQ001Tranrq> req, Errors err) throws DataNotFoundException, RestException, IOException, ClassNotFoundException {
        validateRequest(err);
        return theCTOTODOVQ001Svc.queryTodoVList(req);
    }

    /**
     * LIP-B-CTOTODOVQ002 資深副總&督導副總查詢待辦參數設定
     * 
     * @param req
     * @param err
     * @return
     * @throws IOException
     * @throws DataNotFoundException
     * @throws ClassNotFoundException
     * @throws RestException
     */
    @PostMapping("/todoVList/querySetting")
    @Operation(summary = "LIP-B-CTOTODOVQ002 資深副總&督導副總查詢待辦參數設定")
    public ResponseTemplate<CTOTODOVQ002Tranrs> queryTodoVListSetting(@Valid
    @RequestBody
    RequestTemplate<CTOTODOVQ002Tranrq> req, Errors err) throws IOException, DataNotFoundException, ClassNotFoundException, RestException {
        validateRequest(err);
        return theCTOTODOVQ002Svc.queryTodoVListSetting(req);
    }

}
```

**ReviewController.java 覆核與委員會待辦 Java · 121 行**

lip-svc-cln-todo/src/main/java/cub/lip/svc/cln/todo/controller/ReviewController.java

```java
package cub.lip.svc.cln.todo.controller;

import java.io.IOException;

import javax.validation.Valid;

import cub.lip.lib.common.exception.DataNotFoundException;
import cub.lip.svc.cln.todo.dto.cto.CTORVLCUQ002Tranrq;
import cub.lip.svc.cln.todo.dto.cto.CTORVLCUQ002Tranrs;
import cub.lip.svc.cln.todo.dto.cto.CTORVTDLQ001Tranrq;
import cub.lip.svc.cln.todo.dto.cto.CTORVTDLQ001Tranrs;
import cub.lip.svc.cln.todo.dto.cto.CTORVTDLQ002Tranrq;
import cub.lip.svc.cln.todo.dto.cto.CTORVTDLQ002Tranrs;
import cub.lip.svc.cln.todo.svc.CTORVLCUQ002Svc;
import cub.lip.svc.cln.todo.svc.CTORVTDLQ001Svc;
import cub.lip.svc.cln.todo.svc.CTORVTDLQ002Svc;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.validation.Errors;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import cub.lip.lib.common.controller.BaseController;
import cub.lip.lib.common.dto.base.RequestTemplate;
import cub.lip.lib.common.dto.base.ResponseTemplate;
import cub.lip.svc.cln.todo.dto.cto.CTORVLCUQ001Tranrq;
import cub.lip.svc.cln.todo.dto.cto.CTORVLCUQ001Tranrs;
import cub.lip.svc.cln.todo.svc.CTORVLCUQ001Svc;
import io.swagger.v3.oas.annotations.Operation;

@RestController
@RequestMapping("/review")
public class ReviewController extends BaseController {

    /** CTORVLCUQ001Svc 查詢主管待審件數量 */
    @Autowired
    private CTORVLCUQ001Svc theCTORVLCUQ001Svc;

    /** CTORVLCUQ002Svc 查詢主管待審件數量-授審委員 */
    @Autowired
    private CTORVLCUQ002Svc theCTORVLCUQ002Svc;

    /** CTORVTDLQ001Svc 查詢主管待審件清單 */
    @Autowired
    private CTORVTDLQ001Svc theCTORVTDLQ001Svc;

    /** CTORVTDLQ002Svc 查詢主管待審件清單-授審委員 */
    @Autowired
    private CTORVTDLQ002Svc theCTORVTDLQ002Svc;

    /**
     * LIP-B-CTORVLCUQ001 查詢主管待審件數量
     *
     * @param req
     * @param err
     * @return
     * @throws IOException
     */
    @PostMapping("/todoListCount/query")
    @Operation(summary = "LIP-B-CTORVLCUQ001 查詢主管待審件數量")
    public ResponseTemplate<CTORVLCUQ001Tranrs> queryTodoListCount(@Valid
    @RequestBody
    RequestTemplate<CTORVLCUQ001Tranrq> req, Errors err) throws IOException {
        validateRequest(err);
        return theCTORVLCUQ001Svc.queryTodoListCount(req);
    }

    /**
     * LIP-B-CTORVLCUQ002 查詢主管待審件數量-授審委員
     *
     * @param req
     * @param err
     * @return
     * @throws IOException
     */
    @PostMapping("/committeeTodoCount/query")
    @Operation(summary = "LIP-B-CTORVLCUQ002 查詢主管待審件數量-授審委員")
    public ResponseTemplate<CTORVLCUQ002Tranrs> queryCommitteeTodoCount(@Valid
    @RequestBody
    RequestTemplate<CTORVLCUQ002Tranrq> req, Errors err) throws IOException {
        validateRequest(err);
        return theCTORVLCUQ002Svc.queryCommitteeTodoCount(req);
    }

    /**
     * LIP-B-CTORVTDLQ001 查詢主管待審件清單
     *
     * @param req
     * @param err
     * @return
     * @throws IOException
     * @throws DataNotFoundException
     */
    @PostMapping("/todoList/query")
    @Operation(summary = "LIP-B-CTORVTDLQ001 查詢主管待審件清單")
    public ResponseTemplate<CTORVTDLQ001Tranrs> queryTodoList(@Valid
    @RequestBody
    RequestTemplate<CTORVTDLQ001Tranrq> req, Errors err) throws IOException, DataNotFoundException {
        validateRequest(err);
        return theCTORVTDLQ001Svc.queryTodoList(req);
    }

    /**
     * LIP-B-CTORVTDLQ002 查詢主管待審件清單-授審委員
     *
     * @param req
     * @param err
     * @return
     * @throws IOException
     * @throws DataNotFoundException
     */
    @PostMapping("/committeeTodo/query")
    @Operation(summary = "LIP-B-CTORVTDLQ002 查詢主管待審件清單-授審委員")
    public ResponseTemplate<CTORVTDLQ002Tranrs> queryCommitteeTodo(@Valid
    @RequestBody
    RequestTemplate<CTORVTDLQ002Tranrq> req, Errors err) throws IOException, DataNotFoundException {
        validateRequest(err);
        return theCTORVTDLQ002Svc.queryCommitteeTodo(req);
    }
}
```

**README.md 目前仍是通用範本 Markdown · 20 行**

lip-svc-cln-todo/README.md

```markdown
# Introduction 
TODO: Give a short introduction of your project. Let this section explain the objectives or the motivation behind this project. 

# Getting Started
TODO: Guide users through getting your code up and running on their own system. In this section you can talk about:
1.	Installation process
2.	Software dependencies
3.	Latest releases
4.	API references

# Build and Test
TODO: Describe and show how to build your code and run the tests. 

# Contribute
TODO: Explain how other users and developers can contribute to make your code better. 

If you want to learn more about creating good readme files then refer the following [guidelines](https://docs.microsoft.com/en-us/azure/devops/repos/git/create-a-readme?view=azure-devops). You can also seek inspiration from the below readme files:
- [ASP.NET Core](https://github.com/aspnet/Home)
- [Visual Studio Code](https://github.com/Microsoft/vscode)
- [Chakra Core](https://github.com/Microsoft/ChakraCore)
```

## 交付檢查

-   [ ] 不同角色/流程的篩選條件有各自規格依據。
-   [ ] 筆數、排序、分頁、空清單與權限行為明確。
-   [ ] 清單欄位皆有來源，後續異動 API 已確認。
-   [ ] 成功、無資料和重要篩選情境都有測試。
