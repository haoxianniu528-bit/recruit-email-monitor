# 🚀 v1.3.0 发布说明（2026-08-21）

## ✨ 新增功能

### 1. 表格美化（共享样式模块 `scripts/excel_styles.py`）
- 表头深蓝白字加粗、行高留白；正文微软雅黑、行高加高（解决文字拥挤）
- 隔行斑马纹、浅色边框、垂直居中、长文本自动换行
- 状态/类型/结果列语义化彩色标签（待处理黄 / 已完成绿 / 面试橙 / Offer 绿等）
- 链接列自动转可点击超链接；冻结首行 + 自动筛选

### 2. 状态/结果下拉列表 + 条件格式自动变色
- 邮件表「状态」列、进度表「结果」列支持下拉切换（进度表新增「✅ 已完成」选项）
- 条件格式：切换下拉值颜色实时跟随，无需等待脚本重跑
- 修复 openpyxl 条件格式 dxf 填充缺 bgColor 导致颜色不渲染的 bug
- 自动清理孤儿 dxf 样式，防止文件反复保存膨胀

### 3. 两个表格合并为一个 Excel 文件
- `招聘邮件汇总.xlsx` 内含两个工作表：sheet1 邮件列表（默认打开）+ sheet2 投递记录进度表，底部 tab 切换
- 所有脚本改为按工作表名读写（不再依赖 active sheet），自动追加的新行同样保持美化
- 路径/表头常量集中到 `scripts/excel_styles.py`，改路径只改一处

### 4. 补齐投递进度表脚本（修复线上缺文件）
- 线上 v1.2.x 缺少投递记录进度表相关脚本，本版补齐：
  `apply-progress-updates.py`（Agent 判定增量更新进度）、`build-progress-table.py`（全量重建）、`company_extract.py`（公司/岗位提取）

## 🔧 脚本变更
- 新增：`scripts/excel_styles.py`
- 修改：`record-emails.py`（自动建表/美化/状态下拉）、`apply-progress-updates.py`（进度 sheet 更新+结果下拉）、`build-progress-table.py`（同文件重建进度 sheet）、`email-daily-briefing.py`（按 sheet 名读取）
- 弃用保留：`email-heartbeat-check.keyword-version.py`（旧版关键词匹配，不随发布）

## 📋 安装/升级
```bash
clawhub install recruit-email-monitor --version 1.3.0
cp scripts/config.example.json scripts/config.json   # 填入邮箱授权码与飞书目标
```
> ⚠️ 路径常量集中在 `scripts/excel_styles.py` 顶部（`EXCEL_PATH` / `SHEET_MAIL` / `SHEET_PROGRESS`），部署到其他机器时按需修改。

---

# 🎉 历史发布记录

## v1.2.x（2026-08-08）
- Agent 判定模式：逐封语义判断是否为招聘邮件，替代脆弱的关键词匹配
- 智能分类（笔试/测评、面试、Offer、宣讲会、投递确认等）+ 截止时间提取
- 超期自动归档（30 天以上待处理邮件自动标记完成，不再进简报）
- 每日简报绕过 LLM 直发飞书 API，消除 DeepSeek 高峰期超时
- cron 任务改 isolated 会话 + announce 投递架构

## v1.0.0（2026-03-18）
- 首版发布：多邮箱监控、关键词过滤、Excel 记录、飞书通知、每日简报
