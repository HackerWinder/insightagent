#!/bin/bash

echo "🔍 InsightAgent 应用测试脚本"
echo "================================"

echo ""
echo "1. 检查服务状态..."
echo "前端服务 (端口3000):"
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ 前端服务正在运行"
else
    echo "❌ 前端服务未运行"
fi

echo ""
echo "后端服务 (端口8000):"
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ 后端服务正在运行"
    echo "   健康状态: $(curl -s http://localhost:8000/health)"
else
    echo "❌ 后端服务未运行"
fi

echo ""
echo "2. 检查前端页面内容..."
echo "HTML结构:"
curl -s http://localhost:3000 | grep -A 3 -B 3 "root"

echo ""
echo "3. 检查JavaScript bundle..."
if curl -s http://localhost:3000/static/js/bundle.js > /dev/null; then
    echo "✅ JavaScript bundle可访问"
    echo "Bundle大小: $(curl -s http://localhost:3000/static/js/bundle.js | wc -c) 字节"
    
    if curl -s http://localhost:3000/static/js/bundle.js | grep -q "React 应用正在运行"; then
        echo "✅ 发现React应用代码"
    else
        echo "❌ 未发现React应用代码"
    fi
else
    echo "❌ JavaScript bundle不可访问"
fi

echo ""
echo "4. 测试建议..."
echo "如果页面显示空白，请尝试："
echo "   1. 在浏览器中打开开发者工具查看控制台错误"
echo "   2. 检查网络选项卡是否有加载失败的资源"
echo "   3. 确认JavaScript已启用"
echo ""
echo "访问地址:"
echo "   前端: http://localhost:3000"
echo "   后端API: http://localhost:8000/docs"
