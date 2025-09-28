# InsightAgent - 自主市场洞察智能体

一个输入产品名即可全自动从多渠道搜集公开信息、分析并生成深度用户洞察报告的AI市场分析师。

## 项目结构

```
insight-agent/
├── backend/                 # FastAPI后端服务
│   ├── app/
│   │   ├── api/            # API路由
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据模型
│   │   ├── services/       # 业务服务
│   │   └── tools/          # 数据收集工具
│   ├── tests/              # 后端测试
│   └── requirements.txt    # Python依赖
├── frontend/               # React前端应用
│   ├── src/
│   │   ├── components/     # React组件
│   │   ├── services/       # API客户端
│   │   ├── store/          # 状态管理
│   │   └── utils/          # 工具函数
│   ├── public/
│   └── package.json        # Node.js依赖
├── docker-compose.yml      # 开发环境配置
└── README.md
```

## 技术栈

- **前端**: React, TypeScript, Tailwind CSS
- **后端**: FastAPI, Python 3.11+
- **AI框架**: LangChain, OpenAI
- **数据库**: PostgreSQL, Redis
- **部署**: Docker, Docker Compose

## 快速开始

1. 克隆项目并进入目录
2. 启动开发环境：`docker-compose up -d`
3. 安装依赖并启动服务

详细的开发指南请参考各子目录的README文件。