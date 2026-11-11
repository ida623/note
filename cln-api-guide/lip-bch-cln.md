# lip-bch-cln

## lip-bch-cln｜CLN 背景批次作業

## 專案架構

此模組以 Spring Batch Job/Step 與 Tasklet/Reader/Writer 執行非同步或排程工作；不是提供一般前端同步呼叫的 REST API。POM 顯示它使用 batch 共用 library、CLN 共用 library，並設定 DB2 driver 與 Caffeine。

| 批次範例 | 從 Job/Tasklet 命名可確認的功能 | 閱讀入口 |
| --- | --- | --- |
| `CLNS0B001` | 評等資料更新與批次資料處理流程。 | JobConfig + 多個 Tasklet。 |
| `CLNS0B007` | 訊息通知批次；Job 先跑共用前置檢查，再以 chunk reader/writer 發送。 | JobConfig、MessageSendTasklet。 |
| `CLNS0B008` | 訊息重送/重試批次。 | JobConfig、MessageRetryTasklet。 |
| `CLNS0B009` | JCIC 結果處理、案件處理狀態標記與更新/發送等多步驟工作。 | JobConfig 與對應 Tasklet。 |
| 其他 Job | 可見 DB-to-DB、案件指派、撤件、商品狀態與檔案備份等工作。 | 依 Job ID 追對應 Config、Step、Tasklet。 |

## API 慣例

此模組的對外作業介面是 Batch Job/Step/Tasklet，不是 REST API。Job ID、JobParameters、啟動方式、前置檢查、chunk 邊界與失敗恢復需依 JobConfig 及共用 Batch library 查證。

## 實作流程

**啟動 Job** 排程或啟動器帶入參數

**前置檢查** 串接 JobConfig 指定的檢查

**執行 Step** Tasklet 或 chunk pipeline

**處理資料** 讀取、轉換、更新或發送

**記錄結果** 確認失敗與重跑條件

### 新寫批次：檔案怎麼分工

-   **JobConfig**：定義 Job 有哪些 Step，每個 Step 傳入對應的 Tasklet。
    
    需要交易控制時，在 JobConfig 該 Step 上傳入 `PlatformTransactionManager` 參數。
    
-   **Tasklet**：寫業務邏輯，角色類似新交易的 SvcImpl。
    
-   批次結構裡**不需要 Svc**。
    

### 手動測試批次

所有批次都走同一個入口 `/commonEntrance`：`http://localhost:8181/swagger-ui/index.html#/common-controller/commonEntrance`，用 MSGID 指定要跑哪支。

```
// CLNS0_B102 申請詐欺月檔
{
  "MWHEADER": {
    "MSGID": "CLNS0_B102",
    "SOURCECHANNEL": "LON-LX-LIP-01",
    "TXNSEQ": "202654789"
  },
  "TRANRQ": {
    "others": {
      "additionalProp1": {},
      "additionalProp2": {},
      "additionalProp3": {}
    },
    "ExecDate": "20260813",
    "DataDate": "20260807",
    "EmpId": "string"
  }
}
```

## 完整案例

以 `CLNS0B007` 為例：Job 先接共用前置檢查，再跑訊息發送 Step，由 chunk Reader 載入項目，Writer 將每批資料交給 Tasklet 發送。

**不要把 Job 啟動方式當作一般 API。**

排程/啟動參數、重跑條件、JobParameters、失敗恢復與資料區間會影響批次結果；需查 Job Config、共用 Batch library 和部署設定，不能只從 Tasklet 名稱推定操作方式。

**pom.xml batch 依賴、DB2 與建置設定 XML · 85 行**

lip-bch-cln/pom.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
	xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
	<modelVersion>4.0.0</modelVersion>

	<groupId>cub.lip</groupId>
	<artifactId>lip-bch-cln</artifactId>
	<version>1.0.0-RELEASE</version>
	<packaging>jar</packaging>

	<parent>
		<groupId>cub.cloud</groupId>
		<artifactId>cub-cloud</artifactId>
		<version>1.1.1</version>
		<relativePath /> <!-- lookup parent from repository -->
	</parent>

	<properties>
		<project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
		<project.reporting.outputEncoding>UTF-8
		</project.reporting.outputEncoding>
		<java.version>1.8</java.version>
		<tomcat.version>9.0.106</tomcat.version>
	</properties>

	<dependencies>
		<dependency>
			<groupId>cub.lip</groupId>
			<artifactId>lip-lib-batch</artifactId>
			<version>1.3.12-SNAPSHOT</version>
		</dependency>
		<dependency>
			<groupId>cub.lip</groupId>
			<artifactId>lip-lib-cln-common</artifactId>
			<version>1.0.0-SNAPSHOT</version>
		</dependency>
		<dependency>
			<groupId>org.springframework.boot</groupId>
			<artifactId>spring-boot-starter-cache</artifactId>
		</dependency>
		<dependency>
			<groupId>org.springframework.boot</groupId>
			<artifactId>spring-boot-starter-test</artifactId>
			<scope>test</scope>
		</dependency>
		<dependency>
			<groupId>org.projectlombok</groupId>
			<artifactId>lombok</artifactId>
			<optional>true</optional>
		</dependency>
		<!-- DB2 -->
		<dependency>
			<groupId>com.ibm.db2.jcc</groupId>
			<artifactId>db2jcc</artifactId>
			<version>db2jcc4</version>
		</dependency>

		<dependency>
			<groupId>com.github.ben-manes.caffeine</groupId>
			<artifactId>caffeine</artifactId>
		</dependency>
<!-- 		<dependency> -->
<!-- 			<groupId>org.springframework.boot</groupId> -->
<!-- 			<artifactId>spring-boot-starter-security</artifactId> -->
<!-- 		</dependency> -->
	</dependencies>

	<build>
		<finalName>lip-bch-cln</finalName>
		<plugins>
			<plugin>
				<groupId>org.springframework.boot</groupId>
				<artifactId>spring-boot-maven-plugin</artifactId>
				<executions>
					<execution>
						<goals>
							<goal>repackage</goal>
						</goals>
					</execution>
				</executions>
			</plugin>
		</plugins>
	</build>
</project>
```

**LipSvcClnBatchApplication.java Batch application 入口 Java · 21 行**

lip-bch-cln/src/main/java/cub/lip/bch/cln/LipSvcClnBatchApplication.java

```java
package cub.lip.bch.cln;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.retry.annotation.EnableRetry;
import org.springframework.scheduling.annotation.EnableScheduling;

@ComponentScan({ "cub.lip.bch.cln", "cub.lip.svc.batch" })
@SpringBootApplication
@EnableScheduling
@EnableRetry
@EnableCaching
public class LipSvcClnBatchApplication {

    public static void main(String[] args) {
        SpringApplication.run(LipSvcClnBatchApplication.class, args);
    }

}
```

**CLNS0B007JobConfig.java 訊息通知 Job/Step/Chunk Java · 81 行**

lip-bch-cln/src/main/java/cub/lip/bch/cln/job/CLNS0B007JobConfig.java

```java
package cub.lip.bch.cln.job;

import java.util.ArrayList;
import java.util.Map;

import org.springframework.batch.core.Job;
import org.springframework.batch.core.Step;
import org.springframework.batch.core.configuration.annotation.JobBuilderFactory;
import org.springframework.batch.core.configuration.annotation.StepBuilderFactory;
import org.springframework.batch.core.configuration.annotation.StepScope;
import org.springframework.batch.item.ItemReader;
import org.springframework.batch.item.ItemWriter;
import org.springframework.batch.item.support.ListItemReader;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import cub.lip.bch.cln.tasklet.CLNS0B007MessageSendTasklet;
import cub.lip.lib.cln.common.base.dto.ClnMessageLogVo;
import cub.lip.svc.batch.flow.PreBatchCheckFlowConfig;
import cub.lip.svc.batch.listener.SimpleJobListener;

/**
 * CLNS0_B007 訊息通知批次作業
 * 
 * @author 00550381
 */
@Configuration
public class CLNS0B007JobConfig {

    /** JobBuilderFactory */
    @Autowired
    private JobBuilderFactory jobBuilderFactory;

    /** StepBuilderFactory */
    @Autowired
    private StepBuilderFactory stepBuilderFactory;

    /** PreBatchCheckFlowConfig */
    @Autowired
    private PreBatchCheckFlowConfig preBatchCheck;

    /** 批次更新筆數 */
    private static final int CHUNK_SIZE = 200;

    @Bean
    public Job CLNS0B007Job(SimpleJobListener simpleJobListener,
            @Qualifier("CLNS0B007MessageSendStep") Step messageSendStep) {
        return jobBuilderFactory.get("CLNS0_B007")
                .start(preBatchCheck.preBatchCheckFlow())
                .next(messageSendStep)
                .end()
                .listener(simpleJobListener)
                .build();
    }

    @Bean
    public Step CLNS0B007MessageSendStep(ItemReader<Map.Entry<ClnMessageLogVo, String>> CLNS0B007MessageSendReader,
            ItemWriter<Map.Entry<ClnMessageLogVo, String>> CLNS0B007MessageSendWriter) {
        return stepBuilderFactory.get("CLNS0B007MessageSendStep")
                .<Map.Entry<ClnMessageLogVo, String>, Map.Entry<ClnMessageLogVo, String>>chunk(CHUNK_SIZE)
                .reader(CLNS0B007MessageSendReader)
                .writer(CLNS0B007MessageSendWriter)
                .build();
    }

    @Bean
    @StepScope
    public ItemReader<Map.Entry<ClnMessageLogVo, String>> CLNS0B007MessageSendReader(CLNS0B007MessageSendTasklet messageSendTasklet)
            throws Exception {
        return new ListItemReader<>(messageSendTasklet.loadMessageItems());
    }

    @Bean
    @StepScope
    public ItemWriter<Map.Entry<ClnMessageLogVo, String>> CLNS0B007MessageSendWriter(CLNS0B007MessageSendTasklet messageSendTasklet) {
        return items -> messageSendTasklet.flushMessageChunk(new ArrayList<>(items));
    }

}
```

**CLNS0B007MessageSendTasklet.java 訊息載入與分批發送 Java · 522 行**

lip-bch-cln/src/main/java/cub/lip/bch/cln/tasklet/CLNS0B007MessageSendTasklet.java

```java
package cub.lip.bch.cln.tasklet;

import java.io.IOException;
import java.sql.Timestamp;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

import org.apache.commons.collections.CollectionUtils;
import org.apache.commons.collections.MapUtils;
import org.apache.commons.lang3.StringUtils;
import org.springframework.batch.core.configuration.annotation.StepScope;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import cub.lip.bch.cln.dto.cmss.*;
import cub.lip.bch.cln.entity.ClnMessageLogEntity;
import cub.lip.bch.cln.repository.ClnMessageLogRepository;
import cub.lip.lib.cln.common.base.dto.ChkMessageVo;
import cub.lip.lib.cln.common.base.dto.ClnMessageLogVo;
import cub.lip.lib.cln.common.util.MessageUtil;
import cub.lip.lib.common.dto.base.ResponseTemplate;
import cub.lip.lib.common.enums.WorkingDayEnum;
import cub.lip.lib.common.util.resttemplate.RestTemplateHelper;
import cub.lip.lib.common.util.sql.SqlAction;
import cub.lip.lib.common.util.sql.SqlUtils;
import cub.lip.lib.common.util.transfer.NormalRequestFactory;
import cub.lip.lib.common.util.valid.ValidWorkingdayUtil;
import lombok.extern.slf4j.Slf4j;

/**
 * CLNS0_B007 訊息通知批次作業 Tasklet
 * 
 * @author 00550381
 */
@Slf4j
@Component
@StepScope
public class CLNS0B007MessageSendTasklet {

    /** SqlUtils */
    @Autowired
    private SqlUtils sqlUtils;

    /** SqlAction */
    @Autowired
    private SqlAction sqlAction;

    /** ClnMessageLogRepository */
    @Autowired
    private ClnMessageLogRepository clnMessageLogRepository;

    /** NormalRequestFactory */
    @Autowired
    private NormalRequestFactory normalReqFactory;

    /** RestTemplateHelper */
    @Autowired
    private RestTemplateHelper restTemplateHelper;

    /** MessageUtil */
    @Autowired
    private MessageUtil messageUtil;

    /** ValidWorkingdayUtil */
    @Autowired
    private ValidWorkingdayUtil validWorkingdayUtil;

    /** args */
    @Value("#{jobParameters[args]}")
    private String args;

    /** txnSeq */
    @Value("#{jobParameters[txnSeq]}")
    private String txnSeq;

    /** SourceChannel */
    @Value("${cub.ap-id}")
    private String sourceChannel;

    /** CLNS0B007_QueryMessageSetting */
    private static final String SQL_Q001 = "CLNS0B007_QueryMessageSetting_Q001.sql";

    /** CLNS0B007_InsertMessageHistory */
    private static final String SQL_I001 = "CLNS0B007_InsertMessageHistory_I001.sql";

    /** CLNS0B007_UpdateMessageLog */
    private static final String SQL_U001 = "CLNS0B007_UpdateMessageLog_U001.sql";

    public List<Map.Entry<ClnMessageLogVo, String>> loadMessageItems() throws Exception {
        // 2. 設定參數
        String[] inputArgs = StringUtils.isEmpty(args) ? new String[0] : args.split(",", -1);
        String inputDate;
        String inputTime;
        String sendType;
        LocalDateTime now = LocalDateTime.now();
        String defaultDate = now.toLocalDate().format(DateTimeFormatter.BASIC_ISO_DATE);
        String defaultTime = now.toLocalTime().format(DateTimeFormatter.ofPattern("HHmm"));

        if (inputArgs.length == 0) {
            inputDate = defaultDate;
            inputTime = defaultTime;
            sendType = StringUtils.EMPTY;
        } else {
            inputDate = inputArgs[0];
            try {
                LocalDate.parse(inputDate, DateTimeFormatter.BASIC_ISO_DATE);
            } catch (Exception e) {
                log.error("傳入參數非日期格式 : {}", inputDate);
                return Collections.emptyList();
            }

            if (inputArgs.length == 1) {
                inputTime = defaultTime;
                sendType = StringUtils.EMPTY;
            } else if (inputArgs.length == 2) {
                inputTime = inputArgs[1];
                sendType = StringUtils.EMPTY;
            } else if (inputArgs.length == 3) {
                inputTime = inputArgs[1];
                sendType = inputArgs[2];
            } else {
                log.error("傳入參數個數有誤 : 傳入長度={}", inputArgs.length);
                return Collections.emptyList();
            }

            try {
                LocalTime.parse(inputTime, DateTimeFormatter.ofPattern("HHmm"));
            } catch (Exception e) {
                log.error("傳入參數非時間格式 : {}", inputTime);
                return Collections.emptyList();
            }

        }

        // 3. CLN_MESSAGE_LOG(訊息發送記錄檔)只保留近6個月的檔案，超過則搬到CLN_MESSAGE_HISTORY(訊息發送歷史檔)
        LocalDate inputDateMinus6Months = LocalDate.parse(inputDate, DateTimeFormatter.BASIC_ISO_DATE).minusMonths(6L);
        String inputDateS6M = inputDateMinus6Months.format(DateTimeFormatter.BASIC_ISO_DATE);

        Map<String, Object> historyParamMap = new HashMap<>();
        historyParamMap.put("InputDateS6M", inputDateS6M);
        sqlAction.update(sqlUtils.getQuerySql(SQL_I001), historyParamMap);

        LocalDateTime cutoffDateTime = inputDateMinus6Months.atStartOfDay();
        clnMessageLogRepository.deleteByInputTimeLessThanEqualAndNewsStatus(Timestamp.valueOf(cutoffDateTime), 3);

        // 4. 處理本次訊息通知
        // 4.1 查詢CLN_MESSAGE_SETTING (訊息來源控制檔)
        Map<String, Object> messageSettingParamMap = new HashMap<>();
        messageSettingParamMap.put("InputDate", inputDate);
        messageSettingParamMap.put("SendType", StringUtils.trimToNull(sendType));

        List<Map<String, Object>> messageSettingList = sqlAction.queryForList(sqlUtils.getQuerySql(SQL_Q001), messageSettingParamMap);

        if (CollectionUtils.isNotEmpty(messageSettingList)) {
            List<Map.Entry<ClnMessageLogVo, String>> messageItems = new ArrayList<>();

            // 4.2 確認是否為假日
            Optional<Boolean> isHolidayOptional = isInputDateHoliday(inputDate);
            if (!isHolidayOptional.isPresent()) {
                return Collections.emptyList();
            }

            boolean isHoliday = isHolidayOptional.get();
            // 建立 SMS/Email 待發送清單
            for (Map<String, Object> messageSetting : messageSettingList) {
                if (!processMessageSendSetting(messageSetting, inputDate, inputTime, isHoliday, messageItems)) {
                    return Collections.emptyList();
                }
            }

            log.info("輸入件數:{}件", messageItems.size());
            return messageItems;

        }

        log.info("輸入件數:0件");
        return Collections.emptyList();
    }

    /**
     * 確認是否為假日
     */
    private Optional<Boolean> isInputDateHoliday(String inputDate) {
        try {
            LocalDateTime inputDateTime = LocalDate.parse(inputDate, DateTimeFormatter.BASIC_ISO_DATE).atStartOfDay();
            boolean isWorkingDay = validWorkingdayUtil.validWorkingday(WorkingDayEnum.WORKING_DAY.getBussDateCheckMode(), inputDateTime);
            return Optional.of(!isWorkingDay);
        } catch (Exception e) {
            log.error("檢核營業日失敗, inputDate={}", inputDate, e);
            return Optional.empty();
        }
    }

    /**
     * 是否成功建立 SMS/Email 待發送清單
     */
    private boolean processMessageSendSetting(Map<String, Object> messageSetting, String inputDate, String inputTime, boolean isHoliday,
            List<Map.Entry<ClnMessageLogVo, String>> messageItems) throws Exception {

        String writeStrTime = MapUtils.getString(messageSetting, "WRITE_STR_TIME");
        String writeEndTime = MapUtils.getString(messageSetting, "WRITE_END_TIME");

        if (StringUtils.isAnyBlank(writeStrTime, writeEndTime)) {
            return true;
        }

        String writeHoliday = MapUtils.getString(messageSetting, "WRITE_HOLIDAY");
        int cycleMin = MapUtils.getIntValue(messageSetting, "CYCLE_MIN", 0);
        if (cycleMin <= 0) {
            return true;
        }

        int currentInputTime = Integer.parseInt(inputTime);
        int writeStart = Integer.parseInt(writeStrTime);
        int writeEnd = Integer.parseInt(writeEndTime);
        Timestamp inputTimestamp = Timestamp.valueOf(
            LocalDate.parse(inputDate, DateTimeFormatter.BASIC_ISO_DATE).atTime(currentInputTime / 100, currentInputTime % 100));

        // 平日一律執行，假日則需看 table 設定，再決定是否要執行
        if ((isHoliday && !"Y".equals(writeHoliday)) || currentInputTime < writeStart || currentInputTime > writeEnd) {
            return true;
        }

        int inputMinute = currentInputTime / 100 * 60 + currentInputTime % 100;
        int writeStartMinute = writeStart / 100 * 60 + writeStart % 100;

        // 誤差超過 1 分鐘
        if (Math.abs((inputMinute - writeStartMinute) % cycleMin) > 1) {
            return true;
        }

        // 取得簡訊內容參數，取得每一個寄信對象資料 extractstrList
        String extractStr = MapUtils.getString(messageSetting, "EXTRACTSTR");
        List<Map<String, Object>> extractstrList = Collections.emptyList();
        if (StringUtils.isNotBlank(extractStr)) {
            Map<String, Object> paramMap = new HashMap<>();
            paramMap.put("InputDate", inputDate);
            String parsedSql = messageUtil.replaceParam(extractStr, paramMap);
            extractstrList = sqlAction.queryForList(parsedSql, Collections.emptyMap());
        }

        String sendType = StringUtils.defaultString(MapUtils.getString(messageSetting, "SEND_TYPE"));
        String subject = StringUtils.defaultString(MapUtils.getString(messageSetting, "TITLE"));
        String msgTemplate = StringUtils.defaultString(MapUtils.getString(messageSetting, "MSG"));

        for (Map<String, Object> extractstrMap : extractstrList) {
            String message = messageUtil.replaceParam(msgTemplate, extractstrMap);

            ClnMessageLogVo messageLog = buildMessageLogVo(extractstrMap, sendType, subject, message, inputTimestamp);

            // 資料檢核
            ChkMessageVo chkMessage = messageUtil.chkMessageParams(messageLog);
            String isContinue = chkMessage.getIsContinue();
            String errorMessage = chkMessage.getErrorMessage();
            if ("Y".equals(isContinue) && StringUtils.isNotBlank(errorMessage)) {
                log.info(errorMessage);
                continue;
            }

            String notifyKind = StringUtils.left(messageLog.getSendType(), 1);
            if (!"A".equals(notifyKind) && !"B".equals(notifyKind) && !"C".equals(notifyKind)) {
                log.error("未支援類型 [{}]", notifyKind);
                return false;
            }

            messageItems.add(new AbstractMap.SimpleEntry<>(messageLog, MapUtils.getString(extractstrMap, "REMIT_BRANCH")));
        }

        return true;
    }

    /**
     * 送出 SMS/Email 待發送清單，更新訊息紀錄與批次筆數
     * 
     * @throws IOException
     */
    public void flushMessageChunk(List<Map.Entry<ClnMessageLogVo, String>> messageItems) throws IOException {
        if (CollectionUtils.isEmpty(messageItems)) {
            return;
        }

        List<ClnMessageLogVo> messageList = messageItems.stream().map(Map.Entry::getKey).collect(Collectors.toList());

        // 當作 messageList 的 index，後續更新狀態用
        Map<String, ClnMessageLogVo> messageLogBySendKey = new HashMap<>();

        // 收集簡訊清單，一次發送
        List<CMSSDSMST001TranrqSmsNotify> smsList = new ArrayList<>();

        // 收集 email 清單，一次發送
        List<CMSSMAILT001TranrqMailNotify> emailList = new ArrayList<>();

        for (Map.Entry<ClnMessageLogVo, String> messageItem : messageItems) {
            ClnMessageLogVo messageLog = messageItem.getKey();
            String notifyKind = StringUtils.left(messageLog.getSendType(), 1);

            // A: SMS 簡訊
            if ("A".equals(notifyKind)) {
                CMSSDSMST001TranrqSmsNotify smsItem = new CMSSDSMST001TranrqSmsNotify();
                smsItem.setCaseNbr(messageLog.getApplyId());
                smsItem.setSmsNotifyContent(messageLog.getNews());
                smsItem.setSmsNotifySubject(messageLog.getSubject());
                smsItem.setNotifyCode(messageLog.getNotifyType());
                smsItem.setRecipientCellPhone(messageLog.getMobile());
                smsItem.setRecipientId(messageLog.getInfmId());
                smsItem.setRecipientName(messageLog.getInfmName());
                smsItem.setAcntDeptCode(messageItem.getValue());
                smsList.add(smsItem);
                messageLogBySendKey.put(buildSmsKey(smsItem.getCaseNbr(), smsItem.getNotifyCode(), smsItem.getRecipientCellPhone()),
                    messageLog);

                // B:INTERNAL-EMAIL 內部郵件// C: EXTERNAL-EMAIL 外部郵件
            } else if ("B".equals(notifyKind) || "C".equals(notifyKind)) {
                CMSSMAILT001TranrqRecipient recipient = new CMSSMAILT001TranrqRecipient();
                recipient.setRecipientEmail(messageLog.getEmail());
                recipient.setRecipientName(messageLog.getInfmName());
                recipient.setCcFlag("N");

                List<CMSSMAILT001TranrqRecipient> recipientList = new ArrayList<>();
                recipientList.add(recipient);

                CMSSMAILT001TranrqMailNotify emailItem = new CMSSMAILT001TranrqMailNotify();
                emailItem.setCaseNbr(messageLog.getApplyId());
                emailItem.setMailNotifyCode("B".equals(notifyKind) ? "1" : "2");
                emailItem.setMailNotifyContent(messageLog.getNews());
                emailItem.setMailNotifySubject(messageLog.getSubject());
                emailItem.setMailTypeCode("2");
                emailItem.setNotifyCode(messageLog.getNotifyType());
                emailItem.setRecipientList(recipientList);
                emailList.add(emailItem);
                String recipientEmail = CollectionUtils.isEmpty(emailItem.getRecipientList()) ? ""
                        : emailItem.getRecipientList().get(0).getRecipientEmail();
                messageLogBySendKey.put(buildEmailKey(emailItem.getCaseNbr(), emailItem.getMailNotifySubject(), recipientEmail),
                    messageLog);
            }
        }

        // 新增 log 訊息通知紀錄
        if (CollectionUtils.isNotEmpty(messageList)) {
            insertMessageLogs(messageList);
        }

        // 呼叫【LIP-C-CMSSDSMST001簡訊發送服務】
        if (CollectionUtils.isNotEmpty(smsList)) {
            sendSms(smsList, messageLogBySendKey);
            smsList.clear();
        }

        // 呼叫【LIP-C-CMSSMAILT001 行內信寄送】
        if (CollectionUtils.isNotEmpty(emailList)) {
            sendEmail(emailList, messageLogBySendKey);
            emailList.clear();
        }

        // 更新 log 訊息通知紀錄
        if (CollectionUtils.isNotEmpty(messageList)) {
            updateMessageLogs(messageList);
            log.info("輸出件數:{}件", messageList.size());
        }
    }

    /**
     * 呼叫【LIP-C-CMSSDSMST001 簡訊發送服務】
     */
    private void sendSms(List<CMSSDSMST001TranrqSmsNotify> smsList, Map<String, ClnMessageLogVo> messageLogBySendKey) {
        for (CMSSDSMST001TranrqSmsNotify item : smsList) {
            ClnMessageLogVo logVo = messageLogBySendKey
                    .get(buildSmsKey(item.getCaseNbr(), item.getNotifyCode(), item.getRecipientCellPhone()));
            logVo.setNewsStatus(3);
            logVo.setSendCount(1);

        }
        CMSSDSMST001Tranrq tranrq = new CMSSDSMST001Tranrq();
        tranrq.setModuleTypeCode("CLN");
        tranrq.setSmsNotifyList(smsList);

        ResponseTemplate<CMSSDSMST001Tranrs> response = restTemplateHelper.postForEntity(
            normalReqFactory.genRequestTemplate(tranrq, "LIP-C-CMSSDSMST001", sourceChannel, txnSeq), CMSSDSMST001Tranrs.class);

        String returnCode = response.getMwHeaderResponse().getReturnCode();
        if (!"0000".equals(returnCode) && response.getTranrs() != null
                && CollectionUtils.isNotEmpty(response.getTranrs().getSmsNotifyItemTranrs())) {
            for (CMSSDSMST001TranrsSmsNotify smsResult : response.getTranrs().getSmsNotifyItemTranrs()) {
                // 不成功的訊息，才會更新為失敗
                if (!"Success".equalsIgnoreCase(smsResult.getReturnDesc())) {
                    ClnMessageLogVo messageLog = messageLogBySendKey
                            .get(buildSmsKey(smsResult.getCaseNbr(), smsResult.getNotifyCode(), smsResult.getRecipientCellPhone()));

                    // 更新狀態為失敗
                    if (messageLog != null) {
                        messageLog.setNewsStatus(-1);
                    }
                }
            }
        }
    }

    /**
     * 呼叫【LIP-C-CMSSMAILT001 行內信寄送】
     */
    private void sendEmail(List<CMSSMAILT001TranrqMailNotify> emailList, Map<String, ClnMessageLogVo> messageLogBySendKey) {
        for (CMSSMAILT001TranrqMailNotify item : emailList) {
            String email = CollectionUtils.isEmpty(item.getRecipientList()) ? "" : item.getRecipientList().get(0).getRecipientEmail();
            ClnMessageLogVo logVo = messageLogBySendKey.get(buildEmailKey(item.getCaseNbr(), item.getMailNotifySubject(), email));
            logVo.setNewsStatus(3);
            logVo.setSendCount(1);
        }
        CMSSMAILT001Tranrq tranrq = new CMSSMAILT001Tranrq();
        tranrq.setModuleTypeCode("CLN");
        tranrq.setMailNotifyList(emailList);

        ResponseTemplate<CMSSMAILT001Tranrs> response = restTemplateHelper.postForEntity(
            normalReqFactory.genRequestTemplate(tranrq, "LIP-C-CMSSMAILT001", sourceChannel, txnSeq), CMSSMAILT001Tranrs.class);

        // 把這次的 emailList 都更新為失敗
        if (!"0000".equals(response.getMwHeaderResponse().getReturnCode())) {
            for (CMSSMAILT001TranrqMailNotify emailItem : emailList) {
                String recipientEmail = CollectionUtils.isEmpty(emailItem.getRecipientList()) ? ""
                        : emailItem.getRecipientList().get(0).getRecipientEmail();
                ClnMessageLogVo messageLog = messageLogBySendKey
                        .get(buildEmailKey(emailItem.getCaseNbr(), emailItem.getMailNotifySubject(), recipientEmail));

                // 更新狀態為失敗
                if (messageLog != null) {
                    messageLog.setNewsStatus(-1);
                }
            }
        }
    }

    /**
     * 將查詢結果轉成 MessageLogVo
     */
    private ClnMessageLogVo buildMessageLogVo(Map<String, Object> sourceMap, String sendType, String subject, String message,
            Timestamp inputTimestamp) {
        ClnMessageLogVo messageLog = new ClnMessageLogVo();
        messageLog.setApplyId(MapUtils.getString(sourceMap, "APPLY_ID"));
        messageLog.setSendType(sendType);
        messageLog.setNewsStatus(2);
        messageLog.setCnt(MapUtils.getInteger(sourceMap, "CNT"));
        messageLog.setInfmId(StringUtils.defaultString(MapUtils.getString(sourceMap, "INFM_ID")));
        messageLog.setInfmName(StringUtils.defaultString(MapUtils.getString(sourceMap, "INFM_NAME")));
        messageLog.setSubject(subject);
        messageLog.setEmail(MapUtils.getString(sourceMap, "EMAIL"));
        messageLog.setMobile(MapUtils.getString(sourceMap, "MOBILE"));
        messageLog.setNews(message);
        messageLog.setInputTime(inputTimestamp);
        messageLog.setSendCount(0);
        messageLog.setNotifyType(StringUtils.defaultString(MapUtils.getString(sourceMap, "NOTIFY_TYPE")));
        messageLog.setMemoKey(StringUtils.defaultString(MapUtils.getString(sourceMap, "MEMO_KEY")));
        return messageLog;
    }

    /**
     * 新增 MessageLog
     */
    private void insertMessageLogs(List<ClnMessageLogVo> messageList) {
        List<ClnMessageLogEntity> entities = messageList.stream().map(vo -> {
            ClnMessageLogEntity entity = new ClnMessageLogEntity();

            // ClnMessageLogVo 比 ClnMessageLogEntity 多了 Cnt 欄位，使用手動轉換
            entity.setApplyId(vo.getApplyId());
            entity.setSendType(vo.getSendType());
            entity.setNewsStatus(vo.getNewsStatus());
            entity.setInfmId(vo.getInfmId());
            entity.setInfmName(vo.getInfmName());
            entity.setSubject(vo.getSubject());
            entity.setEmail(vo.getEmail());
            entity.setMobile(vo.getMobile());
            entity.setNews(vo.getNews());
            entity.setInputTime(vo.getInputTime());
            entity.setSendCount(vo.getSendCount());
            entity.setNotifyType(vo.getNotifyType());
            entity.setMemoKey(vo.getMemoKey());
            return entity;
        }).collect(Collectors.toList());

        clnMessageLogRepository.saveAll(entities);
    }

    /**
     * SQL 更新 MessageLog
     */
    private void updateMessageLogs(List<ClnMessageLogVo> messageList) throws IOException {
        for (ClnMessageLogVo messageLog : messageList) {
            Map<String, Object> paramMap = new HashMap<>();
            paramMap.put("APPLY_ID", messageLog.getApplyId());
            paramMap.put("SEND_TYPE", messageLog.getSendType());
            paramMap.put("INFM_ID", messageLog.getInfmId());
            paramMap.put("INPUT_TIME", messageLog.getInputTime());
            String memoKey = StringUtils.trimToNull(messageLog.getMemoKey());
            if (memoKey != null) {
                paramMap.put("MEMO_KEY", memoKey);
            }
            paramMap.put("NEWS_STATUS", messageLog.getNewsStatus());
            paramMap.put("SEND_COUNT", messageLog.getSendCount());
            paramMap.put("OUTPUT_TIME", Timestamp.valueOf(LocalDateTime.now()));
            sqlAction.update(sqlUtils.getDynamicQuerySQL(SQL_U001, paramMap), paramMap);
        }
    }

    /**
     * 產生 SMS key
     */
    private String buildSmsKey(String applyId, String notifyType, String mobile) {
        return String.join("|", StringUtils.defaultString(applyId), StringUtils.defaultString(notifyType),
            StringUtils.defaultString(mobile));
    }

    /**
     * 組裝 Email key
     */
    private String buildEmailKey(String applyId, String subject, String email) {
        return String.join("|", StringUtils.defaultString(applyId), StringUtils.defaultString(subject), StringUtils.defaultString(email));
    }

}
```

**CLNS0B008JobConfig.java 訊息重送 Job Java · 76 行**

lip-bch-cln/src/main/java/cub/lip/bch/cln/job/CLNS0B008JobConfig.java

```java
package cub.lip.bch.cln.job;

import java.util.ArrayList;
import java.util.Map;

import org.springframework.batch.core.Job;
import org.springframework.batch.core.Step;
import org.springframework.batch.core.configuration.annotation.JobBuilderFactory;
import org.springframework.batch.core.configuration.annotation.StepBuilderFactory;
import org.springframework.batch.core.configuration.annotation.StepScope;
import org.springframework.batch.item.ItemReader;
import org.springframework.batch.item.ItemWriter;
import org.springframework.batch.item.support.ListItemReader;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import cub.lip.bch.cln.tasklet.CLNS0B008MessageRetryTasklet;
import cub.lip.svc.batch.flow.PreBatchCheckFlowConfig;
import cub.lip.svc.batch.listener.SimpleJobListener;

/**
 * CLNS0_B008 訊息通知重送批次作業
 * 
 * @author 00550381
 */
@Configuration
public class CLNS0B008JobConfig {

    /** JobBuilderFactory */
    @Autowired
    private JobBuilderFactory jobBuilderFactory;

    /** StepBuilderFactory */
    @Autowired
    private StepBuilderFactory stepBuilderFactory;

    /** PreBatchCheckFlowConfig */
    @Autowired
    private PreBatchCheckFlowConfig preBatchCheck;

    /** 批次更新筆數 */
    private static final int CHUNK_SIZE = 200;

    @Bean
    public Job CLNS0B008Job(SimpleJobListener simpleJobListener, @Qualifier("CLNS0B008MessageRetryStep")
    Step messageRetryStep) {
        return jobBuilderFactory.get("CLNS0_B008").start(preBatchCheck.preBatchCheckFlow()).next(messageRetryStep).end()
                .listener(simpleJobListener).build();
    }

    @Bean
    public Step CLNS0B008MessageRetryStep(ItemReader<Map<String, Object>> CLNS0B008MessageRetryReader,
            ItemWriter<Map<String, Object>> CLNS0B008MessageRetryWriter) {
        return stepBuilderFactory.get("CLNS0B008MessageRetryStep")
                .<Map<String, Object>, Map<String, Object>>chunk(CHUNK_SIZE)
                .reader(CLNS0B008MessageRetryReader)
                .writer(CLNS0B008MessageRetryWriter)
                .build();
    }

    @Bean
    @StepScope
    public ItemReader<Map<String, Object>> CLNS0B008MessageRetryReader(CLNS0B008MessageRetryTasklet messageRetryTasklet)
            throws Exception {
        return new ListItemReader<>(messageRetryTasklet.loadRetryTargets());
    }

    @Bean
    @StepScope
    public ItemWriter<Map<String, Object>> CLNS0B008MessageRetryWriter(CLNS0B008MessageRetryTasklet messageRetryTasklet) {
        return items -> messageRetryTasklet.flushRetryChunk(new ArrayList<>(items));
    }

}
```

**README.md 目前仍是通用範本 Markdown · 20 行**

lip-bch-cln/README.md

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

-   [ ] Job ID、參數、資料區間與啟動方式有依據。
-   [ ] Step 順序、chunk/commit 邊界和交易範圍明確。
-   [ ] 失敗重跑、重複處理和外部副作用已評估。
-   [ ] 成功、無資料、部分失敗與重跑案例已驗證。
