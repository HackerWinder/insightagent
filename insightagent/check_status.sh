#!/bin/bash

echo "🔍 检查 InsightAgent 服务状态..."
echo ""

# 检查后端
echo "📡 后端服务 (端口 8000):"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 运行中"
    curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "   健康检查正常"
else
    echo "❌ 未运行"
fi

echo ""

# 检查前端
echo "🎨 前端服务 (端口 3000):"
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ 运行中"
else
    echo "❌ 未运行"
fi

echo ""

# 检查进程
echo "🔧 运行中的进程:"
ps aux | grep -E "(uvicorn|react-scripts)" | grep -v grep | awk '{print "   " $2 ": " $11 " " $12 " " $13 " " $14}'

echo ""
echo "📱 访问地址:"
echo "   前端: http://localhost:3000"
echo "   后端API文档: http://localhost:8000/docs"
echo "   后端健康检查: http://localhost:8000/health"
