---
name: recruit-email-monitor
description: 招聘邮件监控系统 - 自动检查邮箱、记录到表格、飞书通知、每日简报
homepage: https://github.com/haoxianniu528-bit/recruit-email-monitor
metadata: {
  "clawdbot": {
    "emoji": "📧",
    "requires": {
      "bins": ["python3"],
      "pip": ["openpyxl", "poplib"]
    },
    "install": [
      {
        "id": "pip-deps",
        "kind": "pip",
        "packages": ["openpyxl"],
        "label": "安装依赖 (openpyxl)"
      }
    ],
    "config": {
      "email_accounts": "配置邮箱账号 (QQ/163 等)",
      "excel_path": "招聘邮件汇总表格路径",
      "feishu_target": "飞书通知目标用户 ID"
    }
  }
}
---

# 招聘邮件监控系统

自动监控多个邮箱的招聘相关邮件，记录到 Excel 表格，支持飞书实时通知和每日简报。

## 功能

- **自动检查**: 每小时检查 QQ 邮箱、163 邮箱等
- **Agent 智能判定**: 拉取未处理邮件信息后，由 Agent 逐封判断是否为招聘邮件（不再依赖脆弱的关键词匹配）
- **智能分类**: 自动识别笔试/测评、面试、Offer、宣讲会、投递确认等类型
- **实时通知**: 发现新邮件时立即发送飞书消息（由 Agent 汇报）
- **每日简报**: 每天早上 9:00 汇总待处理邮件
- **超期自动归档**: 收到超过 30 天的待处理邮件自动标记为已完成，不再进入简报
- **表格管理**: 自动记录到 Excel，支持状态标记
- **投递记录进度表**: 按公司记录投递/测评/各轮面试时间/结果/链接，**由 Agent 每封邮件判定驱动更新**（Agent 判断是否更新、更新到哪个阶段），只统计 2026-08-01 以来的记录
- **单文件双工作表**: 邮件列表与投递进度合并在一个 Excel（`招聘邮件汇总.xlsx`），底部切换「招聘邮件汇总」/「投递记录进度表」两个 sheet 查看；状态栏/结果栏带下拉列表 + 条件格式（切换值自动变色）

## 工作原理（Agent 判定模式）

不再用关键词判断。每次检查分三步：

1. **拉取**: `fetch-emails.py` 连接邮箱，拉取未处理邮件（主题/发件人/日期/正文预览/链接），写入 `scripts/pending_candidates.json`（仅预过滤营销发件域名，不做关键词判定）
2. **判定**: Agent（主会话或子 agent）阅读候选，逐封判断是否为招聘邮件，结果写入 `scripts/pending_judged.json`
3. **记录**: `record-emails.py` 按判定结果把招聘邮件写入 Excel，并把所有已判定邮件标记为已处理

### 判定文件格式（pending_judged.json）

```json
[
  {
    "id": 1,
    "verdict": "yes",
    "type": "面试",
    "deadline": "8月10日 23:59",
    "progress": {
      "update": true,
      "company": "中兴通讯",
      "position": "软件开发工程师",
      "stage": "一面",
      "time": "2026-08-11 10:56",
      "link": "https://...",
      "result": "⏳ 进行中",
      "note": "备注内容"
    },
    "reason": "中兴通讯面试通知，更新为一面"
  }
]
```

`verdict` 为 `no` 时只需 `id` + `reason`。`progress` 字段说明：
- `update: false` 表示该邮件不更新进度表（宣讲会/宣传/重复通知等）
- `stage` 可选：投递 | 测评 | 一面 | 二面 | 三面 | HR面 | Offer | 结果
- `time` 缺省时用邮件日期；`link` 仅当表格为空时写入；`note` 追加到备注（保留用户手动内容）
- 岗位/备注/自定义结果列保留用户手动填写，不覆盖

## 快速开始

### 1. 创建本地配置

复制示例配置并填写你的邮箱账号（QQ/163 使用授权码，不是登录密码）与飞书目标：

```bash
cp scripts/config.example.json scripts/config.json
```

```json
{
  "email_accounts": [
    {
      "name": "QQ 邮箱",
      "user": "your_qq@qq.com",
      "password": "your_auth_code",
      "host": "pop.qq.com",
      "port": 995
    }
  ],
  "feishu_target": "user:YOUR_FEISHU_USER_ID"
}
```

> ⚠️ `config.json` 包含真实凭据，已加入 .gitignore，不会随 Skill 发布到 ClawHub。

### 3. 设置定时任务

使用 OpenClaw 的 cron 系统（每小时检查，Agent 判定）+ 系统 crontab（每日简报，直发飞书）。**每小时检查使用 isolated 会话 + announce 投递**，不要用 main 会话 systemEvent（依赖 heartbeat，且脚本内调用 `openclaw message send` 会因会话文件锁而失败）：

```text
每小时整点（OpenClaw cron，isolated agentTurn + announce → 飞书）：
1) python3 scripts/fetch-emails.py 拉取未处理邮件候选
2) Agent 逐封判断是否为招聘邮件，写入 scripts/pending_judged.json
3) python3 scripts/record-emails.py 记录结果到表格
4) 有新邮件/紧急事项才汇报；无则回复 NO_REPLY 静默

每天早上 9:00（系统 crontab，不经过 LLM）：
/usr/bin/python3 /home/erhao/.openclaw/skills/recruit-email-monitor/scripts/email-daily-briefing.py
脚本直接调飞书开放平台 API 发送简报，无 Agent 参与，永不因 LLM 超时失败
```

> 💡 **为什么每日简报不走 OpenClaw cron？** 2026-08-10 起迁移：简报任务本质是"脚本生成文本 + 转发"，不需要 LLM 判断，但 agentTurn 模式每次都要调 LLM（DeepSeek 高峰期排队可致 900s 超时、任务整体失败）。改用系统 crontab 直接跑脚本，脚本内用 `send_via_feishu_api()` 直发飞书（凭据在 config.json），彻底消除 LLM 依赖。每小时检查的 Agent 判定环节是语义判断，必须保留 LLM。

> ⚠️ 如 DeepSeek 主模型不可用，每小时检查任务已配置 fallback：`deepseek-v4-flash` → `astron-code-latest`（讯飞）→ `deepseek-chat`。

> ⚠️ 两个任务均已配置 fallback：`deepseek-v4-flash` → `astron-code-latest`（讯飞）→ `deepseek-chat`，DeepSeek 高峰期主模型超时/失败时自动切换。

## 脚本说明

### fetch-emails.py

**功能**: 连接邮箱，拉取未处理邮件候选（主题/发件人/日期/正文预览/链接），写入 `pending_candidates.json`。只预过滤营销发件域名（Humble Bundle/IEEE/领英等），不做关键词判定。

**运行频率**: 建议每小时一次（由 Agent 流程调用）

**输出**: `scripts/pending_candidates.json`（候选列表）

### 判定环节（Agent）

读取 `pending_candidates.json`，逐封判断是否为招聘邮件，输出 `scripts/pending_judged.json`。判定依据：发件人是否为招聘系统/企业 HR、内容是否为投递/笔试/面试/测评/Offer 流程等。

### record-emails.py

**功能**: 根据 `pending_judged.json` 判定结果，把招聘邮件写入 Excel，并更新 `processed_emails.json` 去重列表（yes/no 都会标记已处理，避免重复拉取）。保存后自动调用 apply-progress-updates.py 应用 Agent 的进度表更新指令。

**运行频率**: 每次判定完成后立即执行

**输出**: 更新 Excel 表格 + 增量更新投递记录进度表

### apply-progress-updates.py

**功能**: 读取 `pending_judged.json` 中 Agent 给出的 `progress` 指令，**增量更新**投递记录进度表（只更新指定行/字段，不重建）。由 `record-emails.py` 在记录邮件后自动调用。

**运行频率**: 每次判定完成后立即执行（record-emails.py 自动调用）

**规则**: 只处理 2026-08-01 以来的邮件；公司名优先用 `progress.company`；岗位/备注/自定义结果保留用户手动内容；`update:false` 或未给 progress 的邮件不更新。

### build-progress-table.py

**功能**: 从总表「招聘邮件汇总」sheet **全量重建**「投递记录进度表」sheet，只统计 2026-08-01 以来的邮件（用户 8 月开始投秋招正式批）。按公司分组邮件，自动提取投递时间、测评时间、一面/二面/三面/HR面时间、结果、投递链接、最近动态；保留用户手动填写的投递岗位、备注和自定义结果。

**⚠️ 日常更新不要跑这个脚本**：Agent 增量更新（apply-progress-updates.py）已智能判断轮次，全量重建会覆盖 Agent 的轮次判断。本脚本仅用于**初始化/修复进度表**：
```bash
python3 scripts/build-progress-table.py
```

**输出**: `/home/erhao/shared/招聘邮件汇总.xlsx` 的「投递记录进度表」sheet（同一文件，与邮件列表切换查看）

### email-daily-briefing.py

**功能**: 汇总待处理邮件，生成日报并保存到 `/home/erhao/shared/招聘邮件每日简报.txt`，打印完整简报内容

**超期自动归档**: 运行时会先把收到时间超过 `STALE_DAYS`（默认 30 天）的待处理邮件标记为 `✅ 已完成（超期自动归档）`，归档后不再出现在简报中，并在简报中提示本次归档数量

**运行频率**: 每天早上 9:00（系统 crontab 直接调用，脚本直发飞书 API，不经过 LLM/Agent）

**发送方式**: 默认通过飞书开放平台 API 直发（`send_via_feishu_api()`，用 config.json 中的 `feishu_app_id`/`feishu_app_secret` 获取 tenant_access_token 后调 `im/v1/messages`），同时保存文件 + 打印全文。环境变量：`BRIEFING_SEND_API=0` 关闭直发；`BRIEFING_SEND_CLI=1` 启用旧 CLI 发送（仅会话空闲时手动用）。

### email-heartbeat-check.py（已弃用）

旧版关键词匹配脚本，已由 Agent 判定模式取代，保留为 `email-heartbeat-check.keyword-version.py` 供参考。

## 邮件分类规则（Agent 判定后归类）

| 类型 | 典型场景 |
|------|----------|
| 笔试/测评 | 在线笔试、测评邀请 |
| 面试 | 面试邀请、面试通知 |
| Offer/录用 | offer、录用、签约、三方 |
| 宣讲会 | 宣讲会、说明会、open day |
| 投递确认 | 投递成功、简历确认 |
| 其他招聘相关 | 其他招聘流程邮件 |

## 表格结构

| 状态 | 说明 |
|------|------|
| ⏳ 待处理 | 未处理 |
| ✅ 已完成 | 手动标记完成 |
| ✅ 已完成（超期自动归档） | 收到超过 30 天自动归档 |

## 命令行示例

```bash
# 1. 拉取未处理邮件候选
python3 scripts/fetch-emails.py

# 2. （Agent）读取 scripts/pending_candidates.json 并判断，写入 scripts/pending_judged.json

# 3. 按判定结果记录到表格
python3 scripts/record-emails.py

# 4. 手动生成简报
python3 scripts/email-daily-briefing.py

# 查看表格
open /home/erhao/shared/招聘邮件汇总.xlsx
```

## 注意事项

1. **邮箱授权码**: QQ/163 邮箱需要使用授权码，不是登录密码
2. **表格路径**: 确保 Excel 文件路径正确，首次运行会自动创建
3. **判定成本**: 每小时候选邮件通常不多；若单次候选过多（>40 封），脚本会自动截断，可考虑用子 agent 分担判定
4. **营销域名预过滤**: `NOISE_DOMAINS` 列表可继续补充，减少无效候选

## 故障排查

**问题**: 没有检测到新邮件
- 检查邮箱授权码是否正确
- 查看 `fetch-emails.py` 拉取输出和 `pending_candidates.json`
- 确认邮件是否已被标记处理（processed_emails.json）

**问题**: 判定遗漏或误判
- 检查邮件正文预览是否完整（HTML 邮件可能提取不到正文）
- 补充 `NOISE_DOMAINS` 过滤营销发件人
- 判定标准由 Agent 掌握，可在判定时给出明确理由

**问题**: 表格写入失败
- 检查文件路径权限
- 确保 Excel 文件未被其他程序占用

## 相关文件

- `scripts/fetch-emails.py` - 拉取未处理邮件候选
- `scripts/record-emails.py` - 按 Agent 判定记录到表格 + 自动应用进度表更新
- `scripts/apply-progress-updates.py` - 按 Agent progress 指令增量更新投递记录进度表
- `scripts/build-progress-table.py` - 投递记录进度表全量重建（仅初始化/修复用，只统计 8 月以来）
- `scripts/excel_styles.py` - 共享 Excel 样式模块（表头/斑马纹/边框/行高/彩色标签/超链接，两个表格统一美化）
- `scripts/company_extract.py` - 公司名/岗位提取共享模块
- `scripts/email-daily-briefing.py` - 每日简报脚本
- `scripts/email-heartbeat-check.keyword-version.py` - 旧版关键词匹配脚本（已弃用）
- `scripts/pending_candidates.json` / `scripts/pending_judged.json` - 判定流程临时文件
- `/home/erhao/shared/招聘邮件汇总.xlsx` - 合并总表：sheet1「招聘邮件汇总」（邮件列表）+ sheet2「投递记录进度表」（按公司聚合，自动生成）
- `/home/erhao/shared/招聘邮件每日简报.txt` - 简报输出文件
