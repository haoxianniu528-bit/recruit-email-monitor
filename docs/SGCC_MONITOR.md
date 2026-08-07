# 🏢 国家电网招聘监控 - 实施指南

## 📋 目标

监控国家电网有限公司人力资源招聘平台，重点关注**陕西省电力公司**的招聘信息。

**官方网址**：
- 国家电网人力资源招聘平台：https://hr.sgcc.com.cn/
- 招聘公告栏目：https://hr.sgcc.com.cn/zpchngsgg/index.htm

---

## 🚀 实施步骤

### 步骤 1: 下载网页查看结构

```bash
# 进入脚本目录
cd /home/erhao/shared/skill/recruit-email-monitor/scripts

# 下载网页源码
curl -H "User-Agent: Mozilla/5.0" https://hr.sgcc.com.cn/zpchngsgg/index.htm > sgcc.html

# 查看文件大小
ls -lh sgcc.html
```

### 步骤 2: 分析网页结构

**方法 1: 用浏览器查看（推荐）**

1. 用浏览器打开：https://hr.sgcc.com.cn/zpchngsgg/index.htm
2. 按 `F12` 打开开发者工具
3. 右键点击招聘公告列表 → 检查
4. 查看 HTML 结构，找到：
   - 公告列表的容器元素（`<ul>`、`<table>` 等）
   - 每条公告的标题、链接、日期在哪个标签里
   - 有没有特殊的 class 名或 ID

**方法 2: 用命令行查看**

```bash
# 查看前 100 行
head -100 sgcc.html

# 搜索关键词
grep -i "陕西" sgcc.html
grep -i "公告" sgcc.html
grep -i "href" sgcc.html | head -20
```

### 步骤 3: 运行测试脚本

```bash
# 运行测试
python3 test_sgcc_parser.py

# 查看输出
# 如果解析成功，会显示公告列表
# 如果失败，需要调整解析器
```

### 步骤 4: 调整解析器（如果需要）

编辑 `company-website-monitor.py` 中的 `parse_sgcc()` 函数：

```python
def parse_sgcc(html):
    announcements = []
    soup = BeautifulSoup(html, 'html.parser')
    
    # 根据实际结构调整选择器
    # 例如：如果公告列表在 <ul class="news-list"> 中
    items = soup.select('ul.news-list li')  # 修改这里
    
    for item in items:
        # 根据实际结构调整提取逻辑
        title = item.select_one('a').get_text(strip=True)
        link = item.select_one('a')['href']
        date = item.select_one('span.date').get_text(strip=True)
        
        announcements.append({...})
    
    return announcements
```

### 步骤 5: 测试运行

```bash
# 直接运行监控脚本
python3 company-website-monitor.py

# 观察输出
# 应该看到：
# 🏢 开始检查公司官网招聘公告
# 检查：国家电网招聘平台
# 📢 发现新公告：国网陕西省电力公司 2026 年高校毕业生招聘公告（第一批）
```

### 步骤 6: 启用定时任务

编辑 `cron-jobs.json`，将官网监控任务启用：

```json
{
  "id": "recruit-company-website",
  "name": "公司官网招聘监控",
  "enabled": true,  // ← 改为 true
  "schedule": {
    "kind": "cron",
    "expr": "0 */4 * * *"  // 每 4 小时检查一次
  }
}
```

然后重新导入：

```bash
cd /home/erhao/.openclaw
openclaw cron import /home/erhao/shared/skill/recruit-email-monitor/cron-jobs.json
```

---

## ⚠️ 常见问题

### 问题 1: 网页无法访问

**症状**：`curl` 返回错误或超时

**解决**：
- 检查网络连接
- 添加 User-Agent：`curl -H "User-Agent: Mozilla/5.0" ...`
- 可能是网站限制了访问，需要降低频率

### 问题 2: 解析不到任何内容

**症状**：`test_sgcc_parser.py` 输出"没有解析到任何公告"

**可能原因**：
1. **网页结构变化** - 需要调整 HTML 选择器
2. **动态加载** - 网页内容是用 JavaScript 加载的，需要 Selenium
3. **反爬虫** - 网站检测到爬虫，返回了不同内容

**排查方法**：
```bash
# 查看下载的 HTML 内容
cat sgcc.html | head -200

# 搜索是否包含招聘公告
grep -i "招聘" sgcc.html
grep -i "公告" sgcc.html
```

### 问题 3: 动态网页无法解析

**症状**：HTML 源码中没有公告内容（是空的）

**原因**：内容是用 JavaScript 动态加载的

**解决方案**：使用 Selenium 或 Playwright

```bash
# 安装 Selenium
pip3 install selenium --break-system-packages

# 安装浏览器驱动
apt install chromium-chromedriver  # 或使用其他浏览器
```

然后修改解析器使用 Selenium（需要时再实现）。

---

## 📝 国家电网招聘特点

### 招聘批次

国家电网招聘通常分批次进行：

1. **第一批**：每年 11-12 月（主要面向电工类专业）
2. **第二批**：次年 3-4 月（补录和其他专业）
3. **提前批**：部分省份有

### 公告标题特征

陕西省电力公司的公告标题通常包含：

- "国网陕西省电力公司"
- "陕西省电力公司"
- "陕西电力"
- "西安"（有时用省会代替）

### 关键词配置

在 `company-website-monitor.py` 中已配置：

```python
{
    'name': '国家电网招聘平台',
    'keywords': ['陕西', '陕西省', '西安', '招聘', '高校毕业生', '第一批', '第二批']
}
```

---

## 🎯 预期效果

**成功后**：

1. **自动检查**：每 4 小时自动访问国家电网招聘平台
2. **智能筛选**：只关注陕西省相关的招聘公告
3. **实时通知**：发现新公告时立即发送飞书消息
4. **记录到表格**：自动记录到 Excel，方便查看历史

**飞书通知示例**：

```
🏢 发现 1 条新招聘公告

1. 国家电网陕西电力 - 国网陕西省电力公司 2026 年高校毕业生招聘公告（第一批）
   链接：https://hr.sgcc.com.cn/xxx/xxx.htm

⏰ 检查时间：2026-03-19 01:48
```

---

## 🔧 下一步

### 立即行动

1. **下载网页**：
   ```bash
   cd /home/erhao/shared/skill/recruit-email-monitor/scripts
   curl -H "User-Agent: Mozilla/5.0" https://hr.sgcc.com.cn/zpchngsgg/index.htm > sgcc.html
   ```

2. **运行测试**：
   ```bash
   python3 test_sgcc_parser.py
   ```

3. **查看结果**：
   - 如果成功 → 启用定时任务
   - 如果失败 → 查看网页结构，调整解析器

### 需要帮助时

如果测试失败，请提供：
1. `sgcc.html` 文件（或前 200 行）
2. `test_sgcc_parser.py` 的输出
3. 浏览器中看到的网页截图（可选）

我可以帮你分析网页结构并调整解析器！

---

**祝你成功！有问题随时找我！** 🍊
