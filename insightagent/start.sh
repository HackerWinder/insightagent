#!/bin/bash

echo "🚀 启动 InsightAgent 系统..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 未运行，请先启动 Docker"
    exit 1
fi

# 检查环境变量文件
if [ ! -f .env ]; then
    echo "📝 创建环境变量文件..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件并配置必要的API密钥"
fi

# 启动服务
echo "🐳 启动 Docker 服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose ps

echo ""
echo "✅ InsightAgent 系统启动完成！"
echo ""
echo "📋 服务地址："
echo "  🌐 前端应用: http://localhost:3000"
echo "  🔧 后端API: http://localhost:8000"
echo "  📚 API文档: http://localhost:8000/docs"
echo "  🗄️  数据库: localhost:5432"
echo "  🔴 Redis: localhost:6379"
echo ""
echo "📖 使用说明："
echo "  1. 访问 http://localhost:3000 开始使用"
echo "  2. 输入产品名称创建分析任务"
echo "  3. 系统将自动收集和分析市场数据"
echo "  4. 查看生成的洞察报告"
echo ""
echo "🛠️  管理命令："
echo "  停止服务: docker-compose down"
echo "  查看日志: docker-compose logs -f"
echo "  重启服务: docker-compose restart"
echo ""