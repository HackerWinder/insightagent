#!/bin/bash

echo "🚀 启动 InsightAgent 服务..."

# 检查端口是否被占用
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "⚠️ 端口 8000 已被占用，正在清理..."
    kill -9 $(lsof -ti:8000) 2>/dev/null
fi

if lsof -ti:3000 > /dev/null 2>&1; then
    echo "⚠️ 端口 3000 已被占用，正在清理..."
    kill -9 $(lsof -ti:3000) 2>/dev/null
fi

# 启动后端
echo "🔧 启动后端服务..."
cd backend
source ../venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 启动前端
echo "🎨 启动前端服务..."
cd ../frontend
npm start &
FRONTEND_PID=$!

# 等待前端启动
sleep 5

echo ""
echo "✅ 服务启动完成！"
echo "📱 访问地址:"
echo "   前端: http://localhost:3000"
echo "   后端API文档: http://localhost:8000/docs"
echo "   后端健康检查: http://localhost:8000/health"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待用户中断
trap "echo '🛑 正在停止服务...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait
