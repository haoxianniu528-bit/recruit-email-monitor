# 🏢 公司官网招聘公告监控 - 实施指南

## 📋 功能说明

自动监控目标公司官网的招聘栏目，发现新公告时自动记录并发送飞书通知。

**监控目标**：
- 腾讯招聘官网
- 阿里巴巴招聘官网
- 华为招聘官网
- 国家电网（各省电力公司）
- 其他可配置公司

---

## ⚠️ 重要说明

### 为什么官网监控比邮箱监控复杂？

| 对比项 | 邮箱监控 | 官网监控 |
|--------|----------|----------|
| 接口标准 | POP3/IMAP 标准协议 | 每个公司网站结构不同 |
| 数据格式 | 标准邮件格式 | 各公司自定义 HTML |
| 反爬机制 | 无 | 可能有 |
| 维护成本 | 低 | 高（每个公司单独适配） |

**结论**：官网监控需要为**每个公司单独编写解析器**

---

## 🚀 实施步骤

### 步骤 1: 安装依赖

```bash
pip3 install requests beautifulsoup4 --break-system-packages
```

### 步骤 2: 查看目标网站结构

以腾讯为例：

```bash
# 获取网页源码
curl https://join.qq.com/notice.html > tencent.html

# 或用浏览器打开，按 F12 查看 HTML 结构
```

**查找规律**：
- 公告列表在哪个 HTML 元素里？
- 每条公告的标题、链接、日期分别在哪里？
- 有没有统一的 class 名或 ID？

### 步骤 3: 编写解析器

示例：假设腾讯招聘公告结构如下：

```html
<div class="notice-list">
  <div class="notice-item" data-date="2026-03-19">
    <a href="/notice/123.html">2026 届校园招聘笔试通知</a>
  </div>
  <div class="notice-item" data-date="2026-03-18">
    <a href="/notice/122.html">2026 届校园招聘面试安排</a>
  </div>
</div>
```

**编写解析器**：

```python
def parse_tencent(html):
    """解析腾讯招聘"""
    announcements = []
    soup = BeautifulSoup(html, 'html.parser')
    
    # 根据实际结构调整选择器
    items = soup.select('.notice-list .notice-item')
    
    for item in items[:10]:  # 最新 10 条
        title_elem = item.find('a')
        if not title_elem:
            continue
        
        announcements.append({
            'title': title_elem.get_text(strip=True),
            'link': title_elem.get('href', ''),
            'date': item.get('data-date', datetime.now().strftime('%Y-%m-%d')),
            'company': '腾讯'
        })
    
    return announcements
```

### 步骤 4: 测试解析器

```bash
# 获取网页
curl https://join.qq.com/notice.html > test_tencent.html

# 创建测试脚本
cat > test_parser.py << 'EOF'
from company_website_monitor import parse_tencent

with open('test_tencent.html', 'r') as f:
    html = f.read()

results = parse_tencent(html)
for ann in results:
    print(f"{ann['date']} | {ann['title']} | {ann['link']}")
EOF

python3 test_parser.py
```

### 步骤 5: 添加到公司列表

编辑 `company-website-monitor.py`：

```python
COMPANIES = [
    {
        'name': '腾讯招聘',
        'url': 'https://join.qq.com/notice.html',
        'type': '官网',
        'parser': 'parse_tencent',  # 解析器函数名
        'keywords': ['招聘', '校招', '社招', '实习', '笔试', '面试']
    },
    # 添加更多公司...
]
```

### 步骤 6: 启用定时任务

```bash
# 编辑 cron-jobs.json，将 enabled 改为 true
# 或手动添加 crontab
0 */4 * * * python3 /path/to/company-website-monitor.py
```

---

## 📝 各公司官网参考

### 腾讯招聘
- 网址：https://join.qq.com/notice.html
- 特点：需要查看实际结构
- 难度：⭐⭐

### 阿里巴巴招聘
- 网址：https://talent.alibaba.com/campus/home
- 特点：可能是动态页面，需要 Selenium
- 难度：⭐⭐⭐

### 华为招聘
- 网址：https://career.huawei.com/reccampportal/portal5/campus/notice.html
- 特点：需要查看实际结构
- 难度：⭐⭐

### 国家电网
- 网址：http://sgcc.com.cn/
- 各省电力公司单独招聘，需要分别监控
- 陕西电网：需要查找具体链接
- 难度：⭐⭐⭐⭐

---

## 🔧 实施建议

### 优先级排序

1. **高优先级**（容易 + 重要）：
   - 腾讯招聘（结构简单）
   - 华子招聘（信息集中）

2. **中优先级**（较重要但复杂）：
   - 阿里巴巴（可能动态页面）
   - 国家电网各省公司（网站分散）

3. **低优先级**（可选）：
   - 其他公司

### 分阶段实施

**阶段 1**（1-2 小时）：
- 完成腾讯招聘解析器
- 测试通过

**阶段 2**（2-4 小时）：
- 完成华为、阿里解析器
- 整合到监控系统

**阶段 3**（4-8 小时）：
- 完成国家电网各省公司
- 添加更多目标公司

---

## 💡 替代方案

### 方案 1: RSS 订阅（推荐优先尝试）

有些公司提供 RSS 源，比爬虫简单可靠：

```python
import feedparser

def check_rss():
    feeds = [
        {'name': '腾讯', 'url': 'https://join.qq.com/rss.xml'},  # 假设有
    ]
    
    for feed_info in feeds:
        feed = feedparser.parse(feed_info['url'])
        for entry in feed.entries:
            print(f"{entry.title} - {entry.link}")
```

**优点**：
- 无需解析 HTML
- 官方提供，稳定
- 数据格式标准

**缺点**：
- 不是所有公司都有

### 方案 2: 第三方聚合平台

- 牛客网：https://www.nowcoder.com/
- 应届生求职网：http://www.yingjiesheng.com/
- 拉勾网：https://www.lagou.com/

这些网站聚合了多家公司招聘信息，可以只监控这几个网站。

---

## ⚠️ 注意事项

1. **反爬虫**：
   - 设置合理的 User-Agent
   - 控制请求频率（不要太频繁）
   - 必要时使用代理

2. **网站结构变化**：
   - 公司官网改版后解析器会失效
   - 需要定期检查更新

3. **法律风险**：
   - 仅用于个人使用
   - 不要高频爬取
   - 遵守 robots.txt

---

## 🎯 下一步行动

1. **选择 1-2 个目标公司**（建议从腾讯开始）
2. **查看网站结构**（浏览器 F12）
3. **编写解析器**（参考上面的示例）
4. **测试运行**
5. **启用定时任务**

---

**需要我帮你分析具体某个公司的网站结构吗？** 🍊
