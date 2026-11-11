# CLN_ZR_SRC 與 ZRWeb

## CLN\_ZR\_SRC / ZRWeb｜既有報表與檔案 Web 應用

## 專案架構

ZRWeb 是獨立的 Java 8 WAR 專案，使用傳統 Servlet/JSP 結構：POM 把 `JavaSource` 設成 source directory、`WebContent` 設為 WAR web root，並以 `WEB-INF/web.xml` 註冊 Servlet。此專案與 Spring Boot API 的啟動、路由及部署方式不同。

## API 慣例

ZRWeb 使用 `web.xml` 註冊 Servlet，不使用 Spring `@RestController`；Request/Response 由 DTO 與 ReqRespUtil 處理，各 Servlet 的 URL mapping、multipart/Base64 格式須個別確認。

## 實作流程

先從 web.xml 找 Servlet mapping，再追 Request 解析、Servlet/Mod 處理、報表/檔案資源，最後核對回應或下載結果。

### 新寫一張報表

### 確認工具已安裝

JBoss 與 Jaspersoft，安裝檔在 `\\pfdepnas48\科技應用發展部\應用開發科\其他資訊\報表`。

### 用 Jaspersoft 拉版型

把報表畫好，產生對應的 `.jrxml`。

### jrxml 放進 CLN\_ZR\_SRC

`D:\DEVTOOLS\Projects\ZR\CLN_ZR_SRC\ZRWeb\WebContent\reports\xml\CLN`

### 寫 B + C 層邏輯

查資料的電文照一般 API 寫法開發。

### 測試

見下方兩種方式。

**地端測試（捷徑）**

地端測試時會直接去 UT 環境抓 jrxml。用 WinSCP 連 `88.249.29.126`（報表檔案主機），把 jrxml 放到 `/appool/CLN/ZRWeb/reports/xml/CLN`。注意：關掉 WinSCP 後，新增的檔案會被 reset。

**正常路徑**

地端程式推到 UT，透過正常 CI/CD 把 ZRWeb 裡的 jrxml 部署到 `/appool/CLN/ZRWeb/reports/xml/CLN`，再從 UT 測試。

WinSCP 主機：`88.249.29.125` 放批次檔案、`88.249.29.126` 放報表檔案。

## 完整案例

報表產生路徑是 `RptGeneratorServlet` 解析 RequestTemplate、呼叫 `RptGeneratorMod.doGenRpt`，再由 ReqRespUtil 回傳；CLN 報表範本可對照 `LIP-C-CLNREPOTC001.jrxml`。

| 區域 | 用途觀察 | 注意事項 |
| --- | --- | --- |
| 報表 | `RptGeneratorServlet` 將 RequestTemplate 解析後交給報表模組；WebContent 內含 CLN 的 `.jrxml` 報表範本。 | 報表版型與資料組裝需一併追 Servlet、Mod 和 jrxml；POM 的報表目錄設定含特定 Windows 路徑。 |
| 檔案 | Servlet 包含檔案上傳、下載、刪除、複製，以及 multipart/Base64 傳輸入口。 | 檢查 web.xml mapping、檔案儲存設定與呼叫端電文，不要當作 Spring Controller。 |
| 頁面資源 | `WebContent/html` 有 JSP 工具頁，另有 `reports` 報表資源。 | 目前盤點所見不足以代表所有使用中的頁面或部署設定。 |
| 部署型態 | Maven `war`，web.xml 宣告 Servlet 2.4；不是獨立 executable Spring Boot JAR。 | 實際 Servlet container 與部署版本需向目標環境核對。 |

**ZRWeb/pom.xml WAR、source root 與資源設定 XML · 92 行**

CLN\_ZR\_SRC/ZRWeb/pom.xml

```xml
<project xmlns="http://maven.apache.org/POM/4.0.0"
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
	xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
	<modelVersion>4.0.0</modelVersion>
	<groupId>com.bank</groupId>
	<artifactId>ZRWeb</artifactId>
	<version>0.0.1-SNAPSHOT</version>
	<packaging>war</packaging>
	<properties>
		<project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
		<project.reporting.outputEncoding>UTF-8</project.reporting.outputEncoding>
		<java.version>1.8</java.version>
		<rptSrc>D:/DEVTOOLS/Projects/ZR/CLN_ZR_SRC/ZRWeb/WebContent/reports</rptSrc>
	</properties>
	<dependencies>
		<!-- 【報表】 -->
		<!-- 【報表核心】 -->
		<dependency>
			<groupId>ebaf.bank.subsys</groupId>
			<artifactId>CommonZR</artifactId>
			<version>1.3.4</version>
			<exclusions>
				<exclusion>
					<groupId>ebaf.thirdparty.report</groupId>
					<artifactId>bankKAI</artifactId>
				</exclusion>
				<exclusion>
					<groupId>ebaf.thirdparty.report</groupId>
					<artifactId>bankMing</artifactId>
				</exclusion>
			</exclusions>
		</dependency>
		<dependency>
			<groupId>commons-codec</groupId>
			<artifactId>commons-codec</artifactId>
			<version>1.15</version>
		</dependency>
		<dependency>
			<groupId>org.jboss.spec.javax.servlet</groupId>
			<artifactId>jboss-servlet-api_3.0_spec</artifactId>
			<version>1.0.2.Final</version>
			<scope>provided</scope>
		</dependency>
		<dependency>
			<groupId>com.alibaba</groupId>
			<artifactId>fastjson</artifactId>
			<version>1.2.75</version>
		</dependency>
		<dependency>
			<groupId>org.apache.pdfbox</groupId>
			<artifactId>pdfbox</artifactId>
			<version>2.0.8</version>
		</dependency>
	</dependencies>
	<build>
		<sourceDirectory>JavaSource</sourceDirectory>
		<resources>
			<resource>
				<directory>JavaSource</directory>
				<excludes>
					<exclude>**/*.java</exclude>
				</excludes>
			</resource>
		</resources>
		<plugins>
			<plugin>
				<artifactId>maven-war-plugin</artifactId>
				<version>3.0.0</version>
				<configuration>
					<warName>${project.artifactId}</warName>
					<warSourceDirectory>WebContent</warSourceDirectory>
					<failOnMissingWebXml>false</failOnMissingWebXml>
					<webResources>
						<resource>
							<!-- 請放至對應的report檔案 -->
							<directory>${rptSrc}</directory>
							<targetPath>reports</targetPath>
						</resource>
					</webResources>
				</configuration>
			</plugin>
			<plugin>
				<artifactId>maven-compiler-plugin</artifactId>
				<version>3.5.1</version>
				<configuration>
					<source>1.8</source>
					<target>1.8</target>
				</configuration>
			</plugin>
		</plugins>
	</build>
</project>
```

**WEB-INF/web.xml Servlet 註冊與 URL mapping XML · 225 行**

CLN\_ZR\_SRC/ZRWeb/WebContent/WEB-INF/web.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<web-app id="WebApp_ID" version="2.4"
	xmlns="http://java.sun.com/xml/ns/j2ee"
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
	xsi:schemaLocation="http://java.sun.com/xml/ns/j2ee http://java.sun.com/xml/ns/j2ee/web-app_2_4.xsd">
	<display-name>ZRWeb</display-name>
	<servlet>
		<servlet-name>log4j</servlet-name>
		<servlet-class>com.bank.rpt.servlets.Log4jServlet</servlet-class>
		<load-on-startup>1</load-on-startup>
	</servlet>
	<servlet>
		<description></description>
		<display-name>RptServlet</display-name>
		<servlet-name>RptServlet</servlet-name>
		<servlet-class>com.bank.rpt.servlets.RptServlet</servlet-class>
	</servlet>
	<servlet>
		<description></description>
		<display-name>XlsServlet</display-name>
		<servlet-name>XlsServlet</servlet-name>
		<servlet-class>com.bank.rpt.servlets.XlsServlet</servlet-class>
	</servlet>
	<servlet>
		<description></description>
		<display-name>FileDownloadServlet</display-name>
		<servlet-name>FileDownloadServlet</servlet-name>
		<servlet-class>com.bank.rpt.servlets.FileDownloadServlet</servlet-class>
	</servlet>
	<servlet>
		<description></description>
		<display-name>BarcodeGeneratorServlet</display-name>
		<servlet-name>BarcodeGeneratorServlet</servlet-name>
		<servlet-class>com.bank.rpt.servlets.BarcodeGeneratorServlet</servlet-class>
	</servlet>
	<servlet>
		<description></description>
		<display-name>FileWatchDogServlet</display-name>
		<servlet-name>FileWatchDogServlet</servlet-name>
		<servlet-class>com.bank.rpt.servlets.FileWatchDogServlet</servlet-class>
	</servlet>
	<servlet>
		<description></description>
		<display-name>AppletServlet</display-name>
		<servlet-name>AppletServlet</servlet-name>
		<servlet-class>com.bank.rpt.servlets.AppletServlet</servlet-class>
	</servlet>
	<!-- <servlet> -->
	<!-- <description></description> -->
	<!-- <display-name>HtmlToPdfServlet</display-name> -->
	<!-- <servlet-name>HtmlToPdfServlet</servlet-name> -->
	<!-- <servlet-class>com.bank.rpt.servlets.HtmlToPdfServlet</servlet-class> -->
	<!-- </servlet> -->
	<servlet>
		<description></description>
		<display-name>FileUploadMultipartServlet</display-name>
		<servlet-name>FileUploadMultipartServlet</servlet-name>
		<servlet-class>com.bank.rpt.servlets.FileUploadMultipartServlet</servlet-class>
	</servlet>
	<servlet>
		<description></description>
		<display-name>FileUploadBase64Servlet</display-name>
		<servlet-name>FileUploadBase64Servlet</servlet-name>
		<servlet-class>com.bank.rpt.servlets.FileUploadBase64Servlet</servlet-class>
	</servlet>
	<servlet>
		<description></description>
		<display-name>FileDownloadMultipartServlet</display-name>
		<servlet-name>FileDownloadMultipartServlet</servlet-name>
		<servlet-class>com.bank.rpt.servlets.FileDownloadMultipartServlet</servlet-class>
	</servlet>
	<servlet>
		<description></description>
		<display-name>ClnFileDownloadBase64Servlet</display-name>
		<servlet-name>ClnFileDownloadBase64Servlet</servlet-name>
		<servlet-class>com.bank.rpt.servlets.ClnFileDownloadBase64Servlet</servlet-class>
	</servlet>
	<servlet>
		<description></description>
		<display-name>ZipUploadMultipartServlet</display-name>
		<servlet-name>ZipUploadMultipartServlet</servlet-name>
		<servlet-class>com.bank.rpt.servlets.ZipUploadMultipartServlet</servlet-class>
	</servlet>
	<servlet>
		<description></description>
		<display-name>FileDeleteServlet</display-name>
		<servlet-name>FileDeleteServlet</servlet-name>
		<servlet-class>com.bank.rpt.servlets.FileDeleteServlet</servlet-class>
	</servlet>
	<servlet>
		<description></description>
		<display-name>ClnFileDeleteServlet</display-name>
		<servlet-name>ClnFileDeleteServlet</servlet-name>
		<servlet-class>com.bank.rpt.servlets.ClnFileDeleteServlet</servlet-class>
	</servlet>
	<servlet>
		<description></description>
		<display-name>RptLandingServlet</display-name>
		<servlet-name>RptLandingServlet</servlet-name>
		<servlet-class>com.bank.rpt.servlets.RptLandingServlet</servlet-class>
	</servlet>
	<servlet>
		<description></description>
		<display-name>ClnFileDownloadMultipartServlet</display-name>
		<servlet-name>ClnFileDownloadMultipartServlet</servlet-name>
		<servlet-class>com.bank.rpt.servlets.ClnFileDownloadMultipartServlet</servlet-class>
	</servlet>
	<servlet>
		<description></description>
		<display-name>FileCopyServlet</display-name>
		<servlet-name>FileCopyServlet</servlet-name>
		<servlet-class>com.bank.rpt.servlets.FileCopyServlet</servlet-class>
	</servlet>
	<servlet>
		<description></description>
		<display-name>MultiFileUploadMultipartServlet</display-name>
		<servlet-name>MultiFileUploadMultipartServlet</servlet-name>
		<servlet-class>com.bank.rpt.servlets.MultiFileUploadMultipartServlet</servlet-class>
	</servlet>
	<servlet>
		<description></description>
		<display-name>CheckServlet</display-name>
		<servlet-name>CheckServlet</servlet-name>
		<servlet-class>com.bank.rpt.servlets.CheckServlet</servlet-class>
	</servlet>
	<servlet>
		<description></description>
		<display-name>PdfTransImgTransZipUploadServlet</display-name>
		<servlet-name>PdfTransImgTransZipUploadServlet</servlet-name>
		<servlet-class>com.bank.rpt.servlets.PdfTransImgTransZipUploadServlet</servlet-class>
	</servlet>
	<servlet-mapping>
		<servlet-name>RptLandingServlet</servlet-name>
		<url-pattern>/RptLandingServlet</url-pattern>
	</servlet-mapping>
	<servlet>
		<description></description>
		<display-name>RptGeneratorServlet</display-name>
		<servlet-name>RptGeneratorServlet</servlet-name>
		<servlet-class>com.bank.rpt.servlets.RptGeneratorServlet</servlet-class>
	</servlet>
	<servlet-mapping>
		<servlet-name>RptGeneratorServlet</servlet-name>
		<url-pattern>/RptGeneratorServlet</url-pattern>
	</servlet-mapping>
	<servlet-mapping>
		<servlet-name>RptServlet</servlet-name>
		<url-pattern>/RptServlet</url-pattern>
	</servlet-mapping>
	<servlet-mapping>
		<servlet-name>XlsServlet</servlet-name>
		<url-pattern>/xls</url-pattern>
	</servlet-mapping>
	<servlet-mapping>
		<servlet-name>FileDownloadServlet</servlet-name>
		<url-pattern>/FileDownload</url-pattern>
	</servlet-mapping>
	<servlet-mapping>
		<servlet-name>BarcodeGeneratorServlet</servlet-name>
		<url-pattern>/BarcodeGenerator</url-pattern>
	</servlet-mapping>
	<servlet-mapping>
		<servlet-name>FileWatchDogServlet</servlet-name>
		<url-pattern>/FileWatchDog</url-pattern>
	</servlet-mapping>
	<!-- <servlet-mapping> -->
	<!-- <servlet-name>HtmlToPdfServlet</servlet-name> -->
	<!-- <url-pattern>/HtmlToPdfServlet</url-pattern> -->
	<!-- </servlet-mapping> -->
	<servlet-mapping>
		<servlet-name>AppletServlet</servlet-name>
		<url-pattern>/AppletServlet</url-pattern>
	</servlet-mapping>
	<servlet-mapping>
		<servlet-name>FileUploadMultipartServlet</servlet-name>
		<url-pattern>/FileUploadMultipartServlet</url-pattern>
	</servlet-mapping>
	<servlet-mapping>
		<servlet-name>FileUploadBase64Servlet</servlet-name>
		<url-pattern>/FileUploadBase64Servlet</url-pattern>
	</servlet-mapping>
	<servlet-mapping>
		<servlet-name>FileDownloadMultipartServlet</servlet-name>
		<url-pattern>/FileDownloadMultipartServlet</url-pattern>
	</servlet-mapping>
	<servlet-mapping>
		<servlet-name>ClnFileDownloadMultipartServlet</servlet-name>
		<url-pattern>/ClnFileDownloadMultipartServlet</url-pattern>
	</servlet-mapping>
	<servlet-mapping>
		<servlet-name>ClnFileDownloadBase64Servlet</servlet-name>
		<url-pattern>/ClnFileDownloadBase64Servlet</url-pattern>
	</servlet-mapping>
	<servlet-mapping>
		<servlet-name>ZipUploadMultipartServlet</servlet-name>
		<url-pattern>/ZipUploadMultipartServlet</url-pattern>
	</servlet-mapping>
	<servlet-mapping>
		<servlet-name>FileDeleteServlet</servlet-name>
		<url-pattern>/FileDeleteServlet</url-pattern>
	</servlet-mapping>
	<servlet-mapping>
		<servlet-name>ClnFileDeleteServlet</servlet-name>
		<url-pattern>/ClnFileDeleteServlet</url-pattern>
	</servlet-mapping>
	<servlet-mapping>
		<servlet-name>FileCopyServlet</servlet-name>
		<url-pattern>/FileCopyServlet</url-pattern>
	</servlet-mapping>
	<servlet-mapping>
		<servlet-name>MultiFileUploadMultipartServlet</servlet-name>
		<url-pattern>/MultiFileUploadMultipartServlet</url-pattern>
	</servlet-mapping>
	<servlet-mapping>
		<servlet-name>CheckServlet</servlet-name>
		<url-pattern>/CheckServlet</url-pattern>
	</servlet-mapping>
	<servlet-mapping>
		<servlet-name>PdfTransImgTransZipUploadServlet</servlet-name>
		<url-pattern>/PdfTransImgTransZipUploadServlet</url-pattern>
	</servlet-mapping>
	<welcome-file-list>
		<welcome-file>html/index.jsp</welcome-file>
	</welcome-file-list>
</web-app>
```

**RptGeneratorServlet.java 報表產生入口 Java · 42 行**

CLN\_ZR\_SRC/ZRWeb/JavaSource/com/bank/rpt/servlets/RptGeneratorServlet.java

```java
package com.bank.rpt.servlets;

import java.io.IOException;

import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.apache.log4j.Logger;

import com.bank.common.exception.ErrorInputException;
import com.bank.dto.RptGeneratorTranrq;
import com.bank.dto.RptGeneratorTranrs;
import com.bank.dto.base.RequestTemplate;
import com.bank.enums.ReturnCodeAndDescEnum;
import com.bank.rpt.mod.RptGeneratorMod;
import com.bank.rpt.servlets.util.ReqRespUtil;

public class RptGeneratorServlet extends HttpServlet {

    private static final long serialVersionUID = 1L;

    private static Logger LOG = Logger.getLogger(RptGeneratorServlet.class);

    @Override
    public void service(HttpServletRequest request, HttpServletResponse response) throws IOException {
        // 取得 requestBody convert to Map
        RequestTemplate<RptGeneratorTranrq> req = ReqRespUtil.getRequest(request, RptGeneratorTranrq.class);

        try {
            RptGeneratorTranrs tranrs = new RptGeneratorMod().doGenRpt(req.getTranrq());
            ReqRespUtil.returnNormalResponse(tranrs, req, response);
        } catch (ErrorInputException eie) {
            LOG.fatal(eie.getMessage(), eie);
            ReqRespUtil.returnCustomResponse(null, req, response, ReturnCodeAndDescEnum.SE903.getCode(), eie.getMessage());
        } catch (Exception e) {
            LOG.fatal(e.getMessage(), e);
            ReqRespUtil.returnCustomResponse(null, req, response, ReturnCodeAndDescEnum.SE008.getCode(), e.getMessage());
        }

    }
}
```

**RptGeneratorMod.java 報表產生模組 Java · 96 行**

CLN\_ZR\_SRC/ZRWeb/JavaSource/com/bank/rpt/mod/RptGeneratorMod.java

```java
package com.bank.rpt.mod;

import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.UUID;

import org.apache.commons.io.IOUtils;
import org.apache.commons.lang3.StringUtils;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONObject;
import com.bank.common.exception.ErrorInputException;
import com.bank.common.util.http.HttpClientHelper;
import com.bank.dto.RptGeneratorTranrq;
import com.bank.dto.RptGeneratorTranrs;

public class RptGeneratorMod {

    public RptGeneratorTranrs doGenRpt(RptGeneratorTranrq tranrq) throws Exception {

        ErrorInputException eie = null;
        String jasperName = tranrq.getJasperName();
        if (StringUtils.isBlank(jasperName)) {
            eie = getErrorInputException(eie, "報表名稱不得為空");
        }

        String version = tranrq.getVersion();
        if (StringUtils.isBlank(version)) {
            eie = getErrorInputException(eie, "報表版本不得為空");
        }

        String rptPath = tranrq.getRptPath();
        if (StringUtils.isBlank(rptPath)) {
            eie = getErrorInputException(eie, "報表路徑不得為空");
        }

        if (eie != null) {
            throw eie;
        }

        String fileName = StringUtils.defaultIfBlank(tranrq.getFileName(), UUID.randomUUID().toString());
        boolean download = tranrq.isDownload();

        // CLN 中台上行參數
        JSONObject json = new JSONObject();
        json.put("fileName", fileName);
        json.put("paramMap", JSON.parseObject(tranrq.getParamMap()));
        json.put("dataSource", JSON.parseArray(tranrq.getDataSource()));

        String targetFileName = new StringBuilder().append(rptPath).append(File.separator).append(fileName).toString();
        ByteArrayInputStream ist = null;
        FileInputStream fis = null;
        RptGeneratorTranrs tranrs = new RptGeneratorTranrs();
        try (FileOutputStream fos = new FileOutputStream(targetFileName);) {
            // call 中台
            HttpClientHelper httpClient = new HttpClientHelper();
            String url = new StringBuilder(tranrq.getRptUrl()).append('/').append(jasperName).append('/').append(version).toString();

            ist = httpClient.getHttpResponseAsStream(url, json.toJSONString());

            // 寫檔至 naspool 路徑下
            IOUtils.copy(ist, fos);
            fos.flush();

            tranrs.setExisted(Files.exists(Paths.get(targetFileName)));
            // 判斷是否需要報表檔案
            if (download) {
                fis = new FileInputStream(targetFileName);
                tranrs.setRptFile(IOUtils.toByteArray(fis));
            }

        } finally {
            if (ist != null) {
                ist.close();
            }

            if (fis != null) {
                fis.close();
            }
        }

        return tranrs;
    }

    private ErrorInputException getErrorInputException(ErrorInputException eie, String errMsg) {
        if (eie == null) {
            eie = new ErrorInputException();
        }
        eie.appendMessage(errMsg);
        return eie;
    }
}
```

**LIP-C-CLNREPOTC001.jrxml CLN 報表範本範例 JRXML · 285 行**

CLN\_ZR\_SRC/ZRWeb/WebContent/reports/xml/CLN/LIP-C-CLNREPOTC001.jrxml

```
<?xml version="1.0" encoding="UTF-8"?>
<!-- Created with Jaspersoft Studio version 6.18.1.final using JasperReports Library version 6.18.1-9d75d1969e774d4f179fb3be8401e98a0e6d1611  -->
<jasperReport xmlns="http://jasperreports.sourceforge.net/jasperreports" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://jasperreports.sourceforge.net/jasperreports http://jasperreports.sourceforge.net/xsd/jasperreport.xsd" name="LIP-C-CLNREPOTC001" pageWidth="595" pageHeight="842" whenNoDataType="AllSectionsNoDetail" columnWidth="575" leftMargin="10" rightMargin="10" topMargin="20" bottomMargin="20" uuid="23ca1ecd-27ba-4720-8ca1-ffd45ea37fec">
	<property name="ireport.zoom" value="1.100000000000006"/>
	<property name="ireport.x" value="0"/>
	<property name="ireport.y" value="0"/>
	<parameter name="LAWBARCODE" class="java.lang.String"/>
	<parameter name="VERSION" class="java.lang.String"/>
	<parameter name="BARCODE" class="java.lang.String"/>
	<parameter name="LIP-C-CLNREPOTC001_1_Sub" class="net.sf.jasperreports.engine.JasperReport"/>
	<parameter name="LIP-C-CLNREPOTC001_1_Param" class="java.util.Map"/>
	<parameter name="LIP-C-CLNREPOTC001_1_Detail" class="com.bank.rpt.datasource.WebappDataSource"/>
	<parameter name="LIP-C-CLNREPOTC001_2_Sub" class="net.sf.jasperreports.engine.JasperReport"/>
	<parameter name="LIP-C-CLNREPOTC001_2_Param" class="java.util.Map"/>
	<parameter name="LIP-C-CLNREPOTC001_2_Detail" class="com.bank.rpt.datasource.WebappDataSource"/>
	<parameter name="BARCODE_2" class="java.lang.String"/>
	<parameter name="OTHER" class="java.lang.String"/>
	<pageHeader>
		<band height="20">
			<textField>
				<reportElement x="381" y="0" width="152" height="20" uuid="c61d779e-6acb-4a9f-a4bf-833cd074ef60"/>
				<textElement textAlignment="Right" verticalAlignment="Top">
					<font fontName="標楷體" size="12" pdfEncoding="Identity-H"/>
				</textElement>
				<textFieldExpression><![CDATA[$P{LAWBARCODE}]]></textFieldExpression>
			</textField>
		</band>
	</pageHeader>
	<detail>
		<band height="742">
			<image scaleImage="FillFrame" hAlign="Left">
				<reportElement mode="Opaque" x="0" y="5" width="575" height="737" uuid="b80909bb-46d1-4e6f-9b15-d83f10e6b988"/>
				<imageExpression><![CDATA["/appool/CLN/ZRWeb/reports/images/CLN/DSA1_1510_1.png"]]></imageExpression>
			</image>
			<staticText>
				<reportElement x="235" y="5" width="105" height="33" uuid="c04377f8-643d-43db-a659-978a0fde7cb9"/>
				<textElement textAlignment="Center" verticalAlignment="Middle">
					<font fontName="標楷體" size="18" isBold="true" isUnderline="false" isStrikeThrough="false" pdfEncoding="Identity-H"/>
					<paragraph lineSpacing="Proportional" lineSpacingSize="1.0"/>
				</textElement>
				<text><![CDATA[切  結  書]]></text>
			</staticText>
			<staticText>
				<reportElement x="521" y="0" width="15" height="33" uuid="a2369ca8-d612-411c-aed4-b091dddab8fc"/>
				<textElement verticalAlignment="Middle">
					<font fontName="標楷體" size="18" isBold="false" isUnderline="false" isStrikeThrough="false" pdfEncoding="Identity-H"/>
					<paragraph lineSpacing="Proportional" lineSpacingSize="1.6"/>
				</textElement>
				<text><![CDATA[)]]></text>
			</staticText>
			<staticText>
				<reportElement x="386" y="0" width="15" height="33" uuid="2158b3a9-977a-45f0-8bdd-04442a5e0488"/>
				<textElement verticalAlignment="Middle">
					<font fontName="標楷體" size="18" isBold="false" isUnderline="false" isStrikeThrough="false" pdfEncoding="Identity-H"/>
					<paragraph lineSpacing="Proportional" lineSpacingSize="1.6"/>
				</textElement>
				<text><![CDATA[(]]></text>
			</staticText>
			<staticText>
				<reportElement x="394" y="0" width="139" height="33" uuid="a1c1e0b3-42a9-47e2-a1c3-c0b59dcf9ef6"/>
				<textElement verticalAlignment="Middle">
					<font fontName="標楷體" size="9" isBold="false" isUnderline="false" isStrikeThrough="false" pdfEncoding="Identity-H"/>
					<paragraph lineSpacing="Proportional" lineSpacingSize="1.0"/>
				</textElement>
				<text><![CDATA[適用借款切結資金流向、不動產
相關背景、不動產貸款業務規定]]></text>
			</staticText>
		</band>
		<band height="529">
			<image scaleImage="FillFrame">
				<reportElement x="0" y="0" width="575" height="420" uuid="71274df7-7d11-4361-964a-58bf6074ba7a"/>
				<imageExpression><![CDATA["/appool/CLN/ZRWeb/reports/images/CLN/DSA1_1510_2.png"]]></imageExpression>
			</image>
			<staticText>
				<reportElement x="315" y="441" width="222" height="23" uuid="ffa45951-ae9a-4452-86bb-46f31ff04f56"/>
				<textElement>
					<font fontName="標楷體" size="12" isStrikeThrough="false" pdfEncoding="Identity-H"/>
					<paragraph lineSpacing="Proportional" lineSpacingSize="1.6"/>
				</textElement>
				<text><![CDATA[：＿＿＿＿＿＿＿＿＿＿＿]]></text>
			</staticText>
			<staticText>
				<reportElement x="315" y="412" width="222" height="23" uuid="ea45d4ac-fdea-4cde-b702-c0861195e7d6"/>
				<textElement>
					<font fontName="標楷體" size="12" isStrikeThrough="false" pdfEncoding="Identity-H"/>
					<paragraph lineSpacing="Proportional" lineSpacingSize="1.6"/>
				</textElement>
				<text><![CDATA[：＿＿＿＿＿＿＿＿＿＿＿（簽章）]]></text>
			</staticText>
			<staticText>
				<reportElement x="229" y="412" width="100" height="23" uuid="599d6c67-f72b-4ab6-972d-579f38f8b2ba"/>
				<textElement textAlignment="Center">
					<font fontName="標楷體" size="12" isStrikeThrough="false" pdfEncoding="Identity-H"/>
					<paragraph lineSpacing="Single" lineSpacingSize="1.6"/>
				</textElement>
				<text><![CDATA[立　書　人]]></text>
			</staticText>
			<staticText>
				<reportElement x="229" y="432" width="100" height="36" uuid="574e7329-8942-40d3-9c07-2143ef6ccc3d"/>
				<textElement textAlignment="Center">
					<font fontName="標楷體" size="12" isStrikeThrough="false" pdfEncoding="Identity-H"/>
					<paragraph lineSpacing="Single" lineSpacingSize="1.6"/>
				</textElement>
				<text><![CDATA[身分證字號
（統一編號）]]></text>
			</staticText>
			<staticText>
				<reportElement x="37" y="513" width="505" height="16" uuid="91dbc0ae-d353-4476-af28-c7f0ace2e8b5"/>
				<box>
					<bottomPen lineWidth="0.25"/>
				</box>
				<textElement verticalAlignment="Top">
					<font fontName="標楷體" size="10" isBold="true" isStrikeThrough="false" pdfEncoding="Identity-H"/>
				</textElement>
				<text><![CDATA[【擔保物明細】]]></text>
			</staticText>
			<staticText>
				<reportElement positionType="Float" stretchType="RelativeToTallestObject" x="526" y="497" width="16" height="16" uuid="32eae661-4192-45e5-95e4-63c5013c2ea2"/>
				<textElement verticalAlignment="Top">
					<font fontName="標楷體" size="10" isBold="true" isStrikeThrough="false" pdfEncoding="Identity-H"/>
				</textElement>
				<text><![CDATA[日]]></text>
			</staticText>
			<staticText>
				<reportElement positionType="Float" stretchType="RelativeToTallestObject" x="417" y="497" width="17" height="16" uuid="e73ba8a6-14a2-456d-a54f-9b4c365c7130"/>
				<textElement verticalAlignment="Top">
					<font fontName="標楷體" size="10" isBold="true" isStrikeThrough="false" pdfEncoding="Identity-H"/>
				</textElement>
				<text><![CDATA[月]]></text>
			</staticText>
			<staticText>
				<reportElement positionType="Float" stretchType="RelativeToTallestObject" x="42" y="497" width="105" height="16" uuid="745769e4-8b33-4128-8fe1-e337e80a08f1"/>
				<textElement verticalAlignment="Top">
					<font fontName="標楷體" size="12" isBold="true" isStrikeThrough="false" pdfEncoding="Identity-H"/>
				</textElement>
				<text><![CDATA[中　華　民　國]]></text>
			</staticText>
			<staticText>
				<reportElement positionType="Float" stretchType="RelativeToTallestObject" x="309" y="497" width="17" height="16" uuid="5bf2d502-cb32-4b04-8a5b-5a1fc4e45895"/>
				<textElement verticalAlignment="Top">
					<font fontName="標楷體" size="10" isBold="true" isStrikeThrough="false" pdfEncoding="Identity-H"/>
				</textElement>
				<text><![CDATA[年]]></text>
			</staticText>
		</band>
		<band height="15">
			<subreport isUsingCache="false">
				<reportElement stretchType="RelativeToTallestObject" x="37" y="0" width="505" height="15" uuid="22f3ec6f-3f52-4b91-8edc-9b5eb2d5ef15"/>
				<parametersMapExpression><![CDATA[$P{LIP-C-CLNREPOTC001_1_Param}]]></parametersMapExpression>
				<subreportParameter name="REPORT_ID"/>
				<dataSourceExpression><![CDATA[$P{LIP-C-CLNREPOTC001_1_Detail}]]></dataSourceExpression>
				<subreportExpression><![CDATA[$P{LIP-C-CLNREPOTC001_1_Sub}]]></subreportExpression>
			</subreport>
		</band>
		<band height="15">
			<subreport isUsingCache="false">
				<reportElement stretchType="RelativeToTallestObject" x="37" y="0" width="505" height="15" uuid="1c9837f4-998f-41ef-89ac-6a4fc9ea2901"/>
				<parametersMapExpression><![CDATA[$P{LIP-C-CLNREPOTC001_2_Param}]]></parametersMapExpression>
				<subreportParameter name="REPORT_ID"/>
				<dataSourceExpression><![CDATA[$P{LIP-C-CLNREPOTC001_2_Detail}]]></dataSourceExpression>
				<subreportExpression><![CDATA[$P{LIP-C-CLNREPOTC001_2_Sub}]]></subreportExpression>
			</subreport>
		</band>
		<band height="30">
			<staticText>
				<reportElement positionType="Float" stretchType="RelativeToTallestObject" x="37" y="0" width="505" height="15" uuid="7db1f068-2946-4be2-8ed8-9e1b23df4a3c">
					<property name="com.jaspersoft.studio.unit.height" value="px"/>
				</reportElement>
				<box>
					<leftPen lineWidth="0.25"/>
					<bottomPen lineWidth="0.25"/>
					<rightPen lineWidth="0.25"/>
				</box>
				<textElement verticalAlignment="Top">
					<font fontName="標楷體" size="10" isBold="true" isStrikeThrough="false" pdfEncoding="Identity-H"/>
				</textElement>
				<text><![CDATA[前開建物之基地應有持分全部（依地政機關登記為憑）
]]></text>
			</staticText>
			<textField>
				<reportElement positionType="Float" x="37" y="14" width="505" height="15" uuid="77a2482c-50f1-457a-8f5c-77c604ef3596">
					<property name="com.jaspersoft.studio.unit.x" value="px"/>
					<property name="com.jaspersoft.studio.unit.y" value="px"/>
					<property name="com.jaspersoft.studio.unit.width" value="px"/>
					<property name="com.jaspersoft.studio.unit.height" value="px"/>
				</reportElement>
				<box>
					<topPen lineWidth="0.0" lineStyle="Solid" lineColor="#000000"/>
					<leftPen lineWidth="1.0" lineStyle="Solid" lineColor="#000000"/>
					<bottomPen lineWidth="1.0" lineStyle="Solid" lineColor="#000000"/>
					<rightPen lineWidth="1.0" lineStyle="Solid" lineColor="#000000"/>
				</box>
				<textElement>
					<font fontName="標楷體" isBold="true"/>
				</textElement>
				<textFieldExpression><![CDATA[$P{OTHER}]]></textFieldExpression>
			</textField>
		</band>
	</detail>
	<pageFooter>
		<band height="40" splitType="Stretch">
			<textField>
				<reportElement x="33" y="1" width="152" height="20" uuid="4334bca7-e788-4208-b3b4-f05c64095e38">
					<property name="com.jaspersoft.studio.unit.x" value="px"/>
					<property name="com.jaspersoft.studio.unit.y" value="px"/>
				</reportElement>
				<textElement verticalAlignment="Top">
					<font fontName="標楷體" size="10" pdfEncoding="Identity-H"/>
				</textElement>
				<textFieldExpression><![CDATA[$P{VERSION}]]></textFieldExpression>
			</textField>
			<textField evaluationTime="Report">
				<reportElement x="299" y="0" width="16" height="20" uuid="3fa7484f-0c34-497d-88b7-06ff57d04378"/>
				<box topPadding="2"/>
				<textElement textAlignment="Center" verticalAlignment="Top">
					<font fontName="標楷體" size="10" isBold="false" isItalic="false" isUnderline="false" pdfEncoding="Identity-H" isPdfEmbedded="false"/>
				</textElement>
				<textFieldExpression><![CDATA[$V{PAGE_NUMBER}]]></textFieldExpression>
			</textField>
			<staticText>
				<reportElement mode="Transparent" x="311" y="1" width="16" height="20" forecolor="#000000" backcolor="#FFFFFF" uuid="76e90acb-d074-4a94-9630-45d66f9bf2cb"/>
				<textElement textAlignment="Center" verticalAlignment="Top" rotation="None" markup="none">
					<font fontName="標楷體" size="10" isBold="false" isItalic="false" isUnderline="false" isStrikeThrough="false" pdfEncoding="Identity-H" isPdfEmbedded="false"/>
					<paragraph lineSpacing="Single"/>
				</textElement>
				<text><![CDATA[頁]]></text>
			</staticText>
			<staticText>
				<reportElement mode="Transparent" x="287" y="1" width="16" height="20" forecolor="#000000" backcolor="#FFFFFF" uuid="70867a3d-b4bd-4a5b-94d5-0d7151e55ced"/>
				<textElement textAlignment="Center" verticalAlignment="Top" rotation="None" markup="none">
					<font fontName="標楷體" size="10" isBold="false" isItalic="false" isUnderline="false" isStrikeThrough="false" pdfEncoding="Identity-H" isPdfEmbedded="false"/>
					<paragraph lineSpacing="Single"/>
				</textElement>
				<text><![CDATA[共]]></text>
			</staticText>
			<staticText>
				<reportElement mode="Transparent" x="275" y="1" width="21" height="20" forecolor="#000000" backcolor="#FFFFFF" uuid="c76180c5-80e7-41a9-b440-9a18cfb77c3d"/>
				<textElement textAlignment="Center" verticalAlignment="Top" rotation="None" markup="none">
					<font fontName="標楷體" size="10" isBold="false" isItalic="false" isUnderline="false" isStrikeThrough="false" pdfEncoding="Identity-H" isPdfEmbedded="false"/>
					<paragraph lineSpacing="Single"/>
				</textElement>
				<text><![CDATA[，]]></text>
			</staticText>
			<textField>
				<reportElement x="257" y="0" width="16" height="20" uuid="ba9be367-70ab-4de1-89da-2231a21d773d"/>
				<box topPadding="2"/>
				<textElement textAlignment="Center" verticalAlignment="Top">
					<font fontName="標楷體" size="10" isBold="false" isItalic="false" isUnderline="false" pdfEncoding="Identity-H" isPdfEmbedded="false"/>
				</textElement>
				<textFieldExpression><![CDATA[$V{PAGE_NUMBER}]]></textFieldExpression>
			</textField>
			<staticText>
				<reportElement mode="Transparent" x="269" y="1" width="16" height="20" forecolor="#000000" backcolor="#FFFFFF" uuid="f0f08a75-6581-4a84-b3a9-8e0836e773d3"/>
				<textElement textAlignment="Center" verticalAlignment="Top" rotation="None" markup="none">
					<font fontName="標楷體" size="10" isBold="false" isItalic="false" isUnderline="false" isStrikeThrough="false" pdfEncoding="Identity-H" isPdfEmbedded="false"/>
					<paragraph lineSpacing="Single"/>
				</textElement>
				<text><![CDATA[頁]]></text>
			</staticText>
			<staticText>
				<reportElement mode="Transparent" x="245" y="1" width="16" height="20" forecolor="#000000" backcolor="#FFFFFF" uuid="e3e1e6e3-cc3b-412c-a79a-8a8c04fa908f"/>
				<textElement textAlignment="Center" verticalAlignment="Top" rotation="None" markup="none">
					<font fontName="標楷體" size="10" isBold="false" isItalic="false" isUnderline="false" isStrikeThrough="false" pdfEncoding="Identity-H" isPdfEmbedded="false"/>
					<paragraph lineSpacing="Single"/>
				</textElement>
				<text><![CDATA[第]]></text>
			</staticText>
			<textField>
				<reportElement x="341" y="17" width="152" height="20" uuid="fa9d2b7b-7530-456a-802e-b0dcefd7a62e"/>
				<box topPadding="2"/>
				<textElement textAlignment="Right" verticalAlignment="Top">
					<font fontName="標楷體" size="10" isBold="false" isItalic="false" isUnderline="false" pdfEncoding="Identity-H" isPdfEmbedded="false"/>
				</textElement>
				<textFieldExpression><![CDATA["110000330"+$V{PAGE_NUMBER}+"2509A"]]></textFieldExpression>
			</textField>
			<textField isBlankWhenNull="false">
				<reportElement x="343" y="2" width="200" height="20" isPrintWhenDetailOverflows="true" uuid="afce4d3f-2631-4fe4-9f22-fb0a68369142"/>
				<textElement textAlignment="Right" verticalAlignment="Top">
					<font fontName="3 of 9 Barcode" size="20" pdfEncoding="Identity-H"/>
				</textElement>
				<textFieldExpression><![CDATA["*110000330"+$V{PAGE_NUMBER}+"2509A*"]]></textFieldExpression>
			</textField>
		</band>
	</pageFooter>
</jasperReport>
```

**CLN\_ZR\_SRC/README.md 目前仍是通用範本 Markdown · 20 行**

CLN\_ZR\_SRC/README.md

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

-   [ ] 確認 WAR/Servlet 專案、URL mapping 與部署容器。
-   [ ] 核對電文、錯誤碼、multipart/Base64 協定。
-   [ ] 報表範本、字型與檔案資源在目標環境可載入。
-   [ ] 上傳/下載限制、儲存路徑、存取權限與清理行為已驗證。
