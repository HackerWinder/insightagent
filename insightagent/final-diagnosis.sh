#!/bin/bash

echo "🔍 InsightAgent 最终诊断"
echo "========================"

echo ""
echo "1. 检查服务状态..."
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ 前端服务正在运行"
else
    echo "❌ 前端服务未运行"
    exit 1
fi

echo ""
echo "2. 检查HTML结构..."
echo "HTML中的root div:"
curl -s http://localhost:3000 | grep -A 3 -B 3 "root"

echo ""
echo "3. 检查JavaScript bundle..."
if curl -s http://localhost:3000/static/js/bundle.js > /dev/null; then
    echo "✅ JavaScript bundle可访问"
    echo "Bundle大小: $(curl -s http://localhost:3000/static/js/bundle.js | wc -c) 字节"
    
    if curl -s http://localhost:3000/static/js/bundle.js | grep -q "InsightAgent"; then
        echo "✅ 发现InsightAgent代码"
    else
        echo "❌ 未发现InsightAgent代码"
    fi
else
    echo "❌ JavaScript bundle不可访问"
fi

echo ""
echo "4. 检查后端服务..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ 后端服务正在运行"
    echo "   健康状态: $(curl -s http://localhost:8000/health)"
else
    echo "❌ 后端服务未运行"
fi

echo ""
echo "5. 诊断建议..."
echo "如果页面显示空白，可能的原因："
echo "   1. JavaScript执行错误 - 请打开浏览器开发者工具查看控制台"
echo "   2. 浏览器缓存问题 - 请尝试强制刷新 (Ctrl+F5)"
echo "   3. 网络问题 - 检查是否有资源加载失败"
echo ""
echo "访问地址:"
echo "   前端: http://localhost:3000"
echo "   后端API: http://localhost:8000/docs"
echo ""
echo "请在浏览器中打开 http://localhost:3000 并查看开发者工具的控制台"
