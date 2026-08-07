#!/usr/bin/env python3
"""
公司官网招聘公告监控
定期检查目标公司官网的招聘栏目，发现新公告时通知
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import json
import os

# 本地配置文件（含 feishu_target，不随 Skill 发布）
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


CFG = load_config()
FEISHU_TARGET = CFG.get('feishu_target', 'user:YOUR_FEISHU_USER_ID')

# 目标公司配置
COMPANIES = [
    {
        'name': '国家电网招聘平台',
        'url': 'https://hr.sgcc.com.cn/zpchngsgg/index.htm',
        'type': '电网',
        'parser': 'parse_sgcc',
        'keywords': ['陕西', '陕西省', '西安', '招聘', '高校毕业生', '第一批', '第二批'],
        'priority': 'high'  # 高优先级
    },
    {
        'name': '腾讯招聘',
        'url': 'https://join.qq.com/notice.html',
        'type': '官网',
        'parser': 'parse_tencent',
        'keywords': ['招聘', '校招', '社招', '实习', '笔试', '面试']
    },
    {
        'name': '阿里巴巴招聘',
        'url': 'https://talent.alibaba.com/campus/home',
        'type': '官网',
        'parser': 'parse_alibaba',
        'keywords': ['招聘', '校招', '社招', '实习', '笔试', '面试']
    },
    {
        'name': '华为招聘',
        'url': 'https://career.huawei.com/reccampportal/portal5/campus/notice.html',
        'type': '官网',
        'parser': 'parse_huawei',
        'keywords': ['招聘', '校招', '社招', '实习', '宣讲', '笔试']
    },
    # 可以继续添加更多公司
]

# 已处理公告记录文件
PROCESSED_FILE = '/home/erhao/.openclaw/skills/recruit-email-monitor/scripts/processed_companies.json'

# 表格路径
EXCEL_PATH = '/home/erhao/shared/招聘邮件汇总.xlsx'

def load_processed():
    """加载已处理的公告"""
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_processed(processed):
    """保存已处理的公告"""
    with open(PROCESSED_FILE, 'w', encoding='utf-8') as f:
        json.dump(processed, f, ensure_ascii=False, indent=2)

def parse_tencent(html):
    """解析腾讯招聘"""
    announcements = []
    try:
        soup = BeautifulSoup(html, 'html.parser')
        # 根据实际情况调整选择器
        items = soup.select('.notice-item')  # 需要查看实际页面结构
        
        for item in items[:10]:  # 最新 10 条
            title = item.get_text(strip=True)
            link = item.get('href', '')
            date = item.get('data-date', datetime.now().strftime('%Y-%m-%d'))
            
            announcements.append({
                'title': title,
                'link': link if link.startswith('http') else f'https://join.qq.com/{link}',
                'date': date,
                'company': '腾讯'
            })
    except Exception as e:
        print(f"解析腾讯失败：{e}")
    
    return announcements

def parse_alibaba(html):
    """解析阿里巴巴招聘"""
    announcements = []
    # TODO: 根据实际页面结构调整
    return announcements

def parse_huawei(html):
    """解析华为招聘"""
    announcements = []
    # TODO: 根据实际页面结构调整
    return announcements

def parse_sgcc(html):
    """
    解析国家电网有限公司人力资源招聘平台
    
    国家电网招聘平台统一发布各省电力公司招聘信息
    网址：https://hr.sgcc.com.cn/
    
    页面结构分析（需要实际验证）：
    - 招聘公告列表通常在 <ul class="list"> 或类似结构中
    - 每条公告包含：标题、发布日期、链接
    - 陕西省电力公司的公告标题通常包含"陕西"字样
    """
    announcements = []
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # 尝试多种可能的选择器（因为无法实时查看网页）
        # 方案 1: 常见的列表结构
        items = soup.select('ul.list li') or soup.select('ul.newlist li') or soup.select('.list-box li')
        
        # 方案 2: 表格结构
        if not items:
            items = soup.select('table tr') or soup.select('.table tr')
        
        for item in items[:20]:  # 检查最新 20 条
            # 提取标题
            title_elem = item.find('a') or item.find('span') or item.find('td')
            if not title_elem:
                continue
            
            title = title_elem.get_text(strip=True)
            
            # 跳过空标题
            if not title or len(title) < 5:
                continue
            
            # 提取链接
            link_elem = item.find('a')
            link = ''
            if link_elem:
                link = link_elem.get('href', '')
                if link and not link.startswith('http'):
                    # 补全相对路径
                    if link.startswith('/'):
                        link = f'https://hr.sgcc.com.cn{link}'
                    else:
                        link = f'https://hr.sgcc.com.cn/{link}'
            
            # 提取日期
            date = datetime.now().strftime('%Y-%m-%d')
            date_elem = item.find('span', class_='date') or item.find('span', class_='time')
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                # 尝试解析日期
                date_match = re.search(r'\d{4}-\d{2}-\d{2}', date_text)
                if date_match:
                    date = date_match.group()
            
            # 只保留包含关键词的公告（特别是陕西相关）
            if any(kw in title for kw in ['陕西', '陕西省', '西安']):
                announcements.append({
                    'title': title,
                    'link': link,
                    'date': date,
                    'company': '国家电网陕西电力'
                })
        
        # 如果没有找到陕西相关的，返回所有招聘公告（让用户自己筛选）
        if not announcements:
            for item in items[:10]:
                title_elem = item.find('a') or item.find('span')
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                if not title or len(title) < 5:
                    continue
                
                link_elem = item.find('a')
                link = ''
                if link_elem:
                    link = link_elem.get('href', '')
                    if link and not link.startswith('http'):
                        link = f'https://hr.sgcc.com.cn/{link}' if link.startswith('/') else f'https://hr.sgcc.com.cn/{link}'
                
                announcements.append({
                    'title': title,
                    'link': link,
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'company': '国家电网招聘平台'
                })
    
    except Exception as e:
        print(f"解析国家电网失败：{e}")
    
    return announcements

def fetch_page(url):
    """获取网页内容"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = response.apparent_encoding
        return response.text
    except Exception as e:
        print(f"获取 {url} 失败：{e}")
        return None

def check_keywords(text, keywords):
    """检查是否包含关键词"""
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)

def check_company_websites():
    """检查所有公司官网"""
    print('🏢 开始检查公司官网招聘公告')
    print(f'检查时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print()
    
    processed = load_processed()
    new_announcements = []
    
    for company in COMPANIES:
        print(f"检查：{company['name']}")
        
        html = fetch_page(company['url'])
        if not html:
            continue
        
        # 调用对应的解析器
        parser_func = globals().get(company['parser'])
        if not parser_func:
            print(f"  ⚠️ 未找到解析器：{company['parser']}")
            continue
        
        announcements = parser_func(html)
        
        for ann in announcements:
            # 生成唯一 ID
            ann_id = f"{company['name']}|{ann['title']}|{ann['date']}"
            
            # 跳过已处理的
            if ann_id in processed:
                continue
            
            # 检查关键词
            if not check_keywords(ann['title'], company['keywords']):
                continue
            
            # 添加到新公告列表
            new_announcements.append({
                'date': ann['date'],
                'company': company['name'],
                'title': ann['title'],
                'link': ann['link'],
                'type': '官网公告',
                'status': '⏳ 待处理'
            })
            
            # 标记为已处理
            processed.append(ann_id)
            
            print(f"  📢 发现新公告：{ann['title']}")
    
    # 保存处理记录
    if new_announcements:
        save_processed(processed)
        print(f"\n✅ 发现 {len(new_announcements)} 条新公告")
    else:
        print("\n✅ 没有新的招聘公告")
    
    return new_announcements

def append_to_excel(new_announcements):
    """将新公告添加到表格"""
    if not new_announcements:
        return
    
    # TODO: 实现 Excel 写入
    print("📝 记录到表格功能待实现")

def send_feishu_notification(new_announcements):
    """发送飞书通知"""
    import subprocess
    
    if not new_announcements:
        return
    
    message = f"🏢 发现 {len(new_announcements)} 条新招聘公告\n\n"
    
    for i, ann in enumerate(new_announcements[:5], 1):
        message += f"{i}. {ann['company']} - {ann['title']}\n"
        message += f"   链接：{ann['link']}\n\n"
    
    if len(new_announcements) > 5:
        message += f"... 还有 {len(new_announcements) - 5} 条\n"
    
    try:
        cmd = [
            'openclaw', 'message', 'send',
            '--channel', 'feishu',
            '--target', FEISHU_TARGET,
            '--message', message
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        print("✅ 飞书通知已发送")
    except Exception as e:
        print(f"❌ 发送失败：{e}")

def main():
    print('=' * 60)
    print('🏢 公司官网招聘公告监控')
    print('=' * 60)
    print()
    
    # 检查官网
    new_announcements = check_company_websites()
    
    # 记录到表格
    if new_announcements:
        append_to_excel(new_announcements)
        
        # 发送通知
        send_feishu_notification(new_announcements)
    
    print()
    print('=' * 60)
    print('✅ 检查完成')

if __name__ == '__main__':
    main()
