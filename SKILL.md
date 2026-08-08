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
    "reason": "OPPO 笔试邀请，nowcoder 系统发送"
  }
]
```

`verdict` 为 `no` 时只需 `id` + `reason`。

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

使用 OpenClaw 的 cron 系统（每小时检查，Agent 判定）。**两个任务都使用 isolated 会话 + announce 投递**，不要用 main 会话 systemEvent（依赖 heartbeat，且脚本内调用 `openclaw message send` 会因会话文件锁而失败）：

```text
每小时整点（isolated agentTurn + announce → 飞书）：
1) python3 scripts/fetch-emails.py 拉取未处理邮件候选
2) Agent 逐封判断是否为招聘邮件，写入 scripts/pending_judged.json
3) python3 scripts/record-emails.py 记录结果到表格
4) 有新邮件/紧急事项才汇报；无则回复 NO_REPLY 静默

每天早上 9:00（isolated agentTurn + announce → 飞书）：
python3 scripts/email-daily-briefing.py，Agent 在回复中完整转发简报全文
```

## 脚本说明

### fetch-emails.py

**功能**: 连接邮箱，拉取未处理邮件候选（主题/发件人/日期/正文预览/链接），写入 `pending_candidates.json`。只预过滤营销发件域名（Humble Bundle/IEEE/领英等），不做关键词判定。

**运行频率**: 建议每小时一次（由 Agent 流程调用）

**输出**: `scripts/pending_candidates.json`（候选列表）

### 判定环节（Agent）

读取 `pending_candidates.json`，逐封判断是否为招聘邮件，输出 `scripts/pending_judged.json`。判定依据：发件人是否为招聘系统/企业 HR、内容是否为投递/笔试/面试/测评/Offer 流程等。

### record-emails.py

**功能**: 根据 `pending_judged.json` 判定结果，把招聘邮件写入 Excel，并更新 `processed_emails.json` 去重列表（yes/no 都会标记已处理，避免重复拉取）

**运行频率**: 每次判定完成后立即执行

**输出**: 更新 Excel 表格

### email-daily-briefing.py

**功能**: 汇总待处理邮件，生成日报并保存到 `/home/erhao/shared/招聘邮件每日简报.txt`，打印完整简报内容

**超期自动归档**: 运行时会先把收到时间超过 `STALE_DAYS`（默认 30 天）的待处理邮件标记为 `✅ 已完成（超期自动归档）`，归档后不再出现在简报中，并在简报中提示本次归档数量

**运行频率**: 每天早上 9:00（由 isolated cron 任务调用，Agent 转发简报全文给用户）

> ⚠️ 脚本默认**不再**调用 `openclaw message send` CLI —— 在 Agent 会话运行期间调用会因会话文件锁（SessionWriteLockTimeoutError）失败。投递由 cron 的 announce delivery 或 Agent 回复完成。仅当设置环境变量 `BRIEFING_SEND_CLI=1` 且在会话空闲时手动运行，才会尝试 CLI 发送。

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
- `scripts/record-emails.py` - 按 Agent 判定记录到表格
- `scripts/email-daily-briefing.py` - 每日简报脚本
- `scripts/email-heartbeat-check.keyword-version.py` - 旧版关键词匹配脚本（已弃用）
- `scripts/pending_candidates.json` / `scripts/pending_judged.json` - 判定流程临时文件
- `/home/erhao/shared/招聘邮件汇总.xlsx` - 邮件汇总表格
- `/home/erhao/shared/招聘邮件每日简报.txt` - 简报输出文件
