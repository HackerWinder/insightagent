#!/bin/bash

echo "🚀 启动InsightAgent开发环境..."

# 检查依赖
echo "📦 检查依赖..."
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行 python -m venv venv"
    exit 1
fi

if [ ! -d "frontend/node_modules" ]; then
    echo "❌ 前端依赖不存在，请先运行 cd frontend && npm install"
    exit 1
fi

# 停止现有进程
echo "🛑 停止现有进程..."
pkill -f "uvicorn app.main:app" || true
pkill -f "react-scripts start" || true
sleep 2

# 启动后端
echo "🔧 启动后端服务..."
cd backend
source ../venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# 等待后端启动
echo "⏳ 等待后端启动..."
sleep 5

# 检查后端健康状态
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ 后端服务启动成功"
else
    echo "❌ 后端服务启动失败"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# 启动前端
echo "🎨 启动前端服务..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

# 等待前端启动
echo "⏳ 等待前端启动..."
sleep 10

# 检查前端
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ 前端服务启动成功"
else
    echo "❌ 前端服务启动失败"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit 1
fi

echo "✅ 服务启动完成！"
echo "📱 访问地址:"
echo "   前端: http://localhost:3000"
echo "   后端API文档: http://localhost:8000/docs"
echo "   后端健康检查: http://localhost:8000/health"
echo ""
echo "🔍 调试信息:"
echo "   查看前端页面源码: curl -s http://localhost:3000"
echo "   检查JavaScript bundle: curl -s http://localhost:3000/static/js/bundle.js | head -50"
echo "   检查后端健康状态: curl -s http://localhost:8000/health"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待用户中断
trap 'echo "🛑 停止所有服务..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true; exit 0' INT

# 监控服务状态
while true; do
    sleep 30
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "❌ 后端服务已停止"
        break
    fi
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "❌ 前端服务已停止"
        break
    fi
    
    # 健康检查
    if ! curl -s http://localhost:8000/health > /dev/null; then
        echo "⚠️  后端健康检查失败"
    fi
    if ! curl -s http://localhost:3000 > /dev/null; then
        echo "⚠️  前端健康检查失败"
    fi
done

echo "🛑 服务已停止"
