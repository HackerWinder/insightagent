# InsightAgent Backend

基于FastAPI的后端服务，提供市场洞察分析的API接口。

## 目录结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI应用入口
│   ├── api/                 # API路由
│   │   ├── __init__.py
│   │   ├── v1/              # API v1版本
│   │   └── deps.py          # 依赖注入
│   ├── core/                # 核心配置
│   │   ├── __init__.py
│   │   ├── config.py        # 应用配置
│   │   └── database.py      # 数据库配置
│   ├── models/              # 数据模型
│   │   ├── __init__.py
│   │   └── task.py          # 任务模型
│   ├── services/            # 业务服务
│   │   ├── __init__.py
│   │   ├── task_manager.py  # 任务管理
│   │   └── agent_executor.py # Agent执行器
│   └── tools/               # 数据收集工具
│       ├── __init__.py
│       ├── base.py          # 基础工具类
│       └── reddit.py        # Reddit工具
├── tests/                   # 测试文件
├── alembic/                 # 数据库迁移
├── requirements.txt         # 依赖文件
└── Dockerfile              # Docker配置
```

## 开发指南

1. 安装依赖：`pip install -r requirements.txt`
2. 设置环境变量：复制`.env.example`为`.env`并填写配置
3. 启动服务：`uvicorn app.main:app --reload`
4. 访问API文档：http://localhost:8000/docs

## API接口

- `GET /health` - 健康检查
- `POST /api/v1/tasks` - 创建分析任务
- `GET /api/v1/tasks` - 获取任务列表
- `GET /api/v1/tasks/{task_id}` - 获取任务详情
- `WebSocket /ws/{task_id}` - 任务状态实时推送