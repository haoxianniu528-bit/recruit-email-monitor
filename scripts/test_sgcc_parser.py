#!/usr/bin/env python3
"""
测试国家电网招聘平台解析器

使用方法：
1. 手动下载网页：curl https://hr.sgcc.com.cn/zpchngsgg/index.htm > sgcc.html
2. 运行测试：python3 test_sgcc_parser.py
"""

from company_website_monitor import parse_sgcc

def main():
    print('🔍 测试国家电网招聘平台解析器')
    print('=' * 60)
    
    # 读取本地 HTML 文件
    try:
        with open('sgcc.html', 'r', encoding='utf-8') as f:
            html = f.read()
        print('✅ 成功加载 sgcc.html')
    except FileNotFoundError:
        print('❌ 错误：找不到 sgcc.html 文件')
        print()
        print('请先下载网页：')
        print('  curl https://hr.sgcc.com.cn/zpchngsgg/index.htm > sgcc.html')
        return
    
    # 解析
    results = parse_sgcc(html)
    
    print(f'\n📊 解析结果：共 {len(results)} 条公告')
    print('=' * 60)
    
    if not results:
        print('\n⚠️  没有解析到任何公告')
        print('可能原因：')
        print('  1. 网页结构已变化')
        print('  2. 需要调整 HTML 选择器')
        print('  3. 网页是动态加载的（需要 Selenium）')
        return
    
    for i, ann in enumerate(results[:10], 1):
        print(f'\n{i}. {ann["title"]}')
        print(f'   公司：{ann["company"]}')
        print(f'   日期：{ann["date"]}')
        print(f'   链接：{ann["link"]}')
    
    if len(results) > 10:
        print(f'\n... 还有 {len(results) - 10} 条')
    
    print()
    print('=' * 60)
    print('✅ 测试完成')

if __name__ == '__main__':
    main()
