#!/bin/bash
# 国家电网招聘监控 - 快速开始脚本

echo "🏢 国家电网招聘监控 - 快速开始"
echo "========================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "步骤 1: 下载国家电网招聘平台网页"
echo "----------------------------------------"

# 尝试下载
curl -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
     -o sgcc.html \
     -w "状态码：%{http_code}\n" \
     "https://hr.sgcc.com.cn/zpchngsgg/index.htm" 2>&1

if [ -f sgcc.html ] && [ -s sgcc.html ]; then
    echo "✅ 下载成功"
    ls -lh sgcc.html
    echo ""
    
    echo "步骤 2: 运行测试解析器"
    echo "----------------------------------------"
    python3 test_sgcc_parser.py
else
    echo "❌ 下载失败"
    echo ""
    echo "可能原因："
    echo "  1. 网络连接问题"
    echo "  2. DNS 解析失败"
    echo "  3. 网站暂时不可访问"
    echo ""
    echo "建议："
    echo "  1. 检查网络连接：ping hr.sgcc.com.cn"
    echo "  2. 用浏览器访问：https://hr.sgcc.com.cn/zpchngsgg/index.htm"
    echo "  3. 稍后重试"
    echo ""
    echo "或者手动下载："
    echo "  1. 用浏览器打开 https://hr.sgcc.com.cn/zpchngsgg/index.htm"
    echo "  2. 右键 → 另存为 → 保存为 sgcc.html"
    echo "  3. 将文件放到：$SCRIPT_DIR/sgcc.html"
    echo "  4. 运行：python3 test_sgcc_parser.py"
fi

echo ""
echo "========================================"
echo "📚 详细文档：docs/SGCC_MONITOR.md"
