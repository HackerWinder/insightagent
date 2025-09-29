# InsightAgent - AI驱动的产品分析系统

![InsightAgent Logo](https://img.shields.io/badge/InsightAgent-AI%20分析-blue?style=for-the-badge&logo=robot)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/React-18-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-blue.svg)](https://www.docker.com/)

## 🏷️ 项目标签

`ai` `产品分析` `fastapi` `react` `langchain` `reddit-api` `product-hunt` `市场研究` `情感分析` `网络爬虫` `机器学习` `typescript` `postgresql` `redis` `docker` `websocket` `实时` `数据收集` `商业智能` `自动化`

## 📋 项目简介

**InsightAgent** 是一个全面的AI驱动产品分析平台，通过自动收集、分析和生成来自多个平台用户讨论的可操作洞察，彻底改变市场研究方式。采用现代Web技术构建，提供产品性能、用户情感和市场趋势的实时分析。

### 🎯 核心功能

- **多平台数据收集**: 自动从Reddit、Product Hunt等社交平台收集用户反馈
- **先进AI分析**: 利用最先进的语言模型进行情感分析、趋势识别和洞察提取
- **实时处理**: 基于WebSocket的实时更新和任务监控，即时获得结果
- **综合报告**: 生成详细的结构化报告，包含可操作的商业建议
- **可扩展架构**: 基于微服务的设计，使用队列处理大规模分析任务

### 🚀 应用场景

- **产品经理**: 即时获取用户反馈和市场接受度洞察
- **营销团队**: 了解情感趋势，识别关键话题点
- **商业分析师**: 获取综合市场数据，支持战略决策
- **初创公司**: 通过自动化用户反馈分析验证产品市场契合度
- **研究人员**: 为学术或商业研究收集和分析大规模社交媒体数据

## 🚀 主要特性

- **自动化数据收集**: 从Reddit和Product Hunt抓取用户讨论和反馈
- **AI驱动分析**: 使用先进语言模型分析情感并提取关键洞察
- **实时处理**: 基于WebSocket的实时更新和任务监控
- **现代Web界面**: 美观的React前端，响应式设计
- **综合API**: 基于FastAPI后端的RESTful API
- **任务管理**: 基于Redis的队列任务处理
- **详细报告**: 生成结构化分析报告，包含可操作洞察

## 🏗️ 系统架构

```
InsightAgent/
├── backend/                 # FastAPI 后端服务
│   ├── app/
│   │   ├── api/            # API 路由和端点
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据库模型
│   │   ├── services/       # 业务逻辑服务
│   │   ├── tools/          # 数据收集工具
│   │   └── worker.py       # 后台任务工作器
│   ├── tests/              # 后端测试套件
│   └── requirements.txt    # Python 依赖
├── frontend/               # React 前端应用
│   ├── src/
│   │   ├── components/     # React 组件
│   │   ├── pages/          # 页面组件
│   │   ├── services/       # API 客户端服务
│   │   ├── store/          # 状态管理
│   │   └── types/          # TypeScript 定义
│   └── package.json        # Node.js 依赖
├── docker-compose.yml      # 开发环境
└── README.md
```

## 🛠️ 技术栈

### 后端
- **框架**: FastAPI (Python 3.11+)
- **AI/ML**: LangChain, OpenAI API
- **数据库**: PostgreSQL with SQLAlchemy ORM
- **缓存/队列**: Redis
- **任务处理**: 类似Celery的工作器系统
- **API文档**: Swagger/OpenAPI

### 前端
- **框架**: React 18 with TypeScript
- **样式**: Tailwind CSS
- **状态管理**: Zustand
- **HTTP客户端**: Axios
- **实时通信**: WebSocket连接
- **构建工具**: Create React App

### 基础设施
- **容器化**: Docker & Docker Compose
- **数据库迁移**: Alembic
- **测试**: Pytest (后端), Jest (前端)
- **代码质量**: ESLint, Prettier

## 🚀 快速开始

### 前置要求
- Docker 和 Docker Compose
- Node.js 18+ (前端开发)
- Python 3.11+ (后端开发)

### 开发环境设置

1. **克隆仓库**
   ```bash
   git clone https://github.com/HackerWinder/insightagent.git
   cd insightagent
   ```

2. **环境配置**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填入您的API密钥和配置
   ```

3. **使用Docker Compose启动**
   ```bash
   docker-compose up -d
   ```

4. **或单独启动服务**
   ```bash
   # 后端
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python -m app.main

   # 前端
   cd frontend
   npm install
   npm start
   ```

5. **访问应用**
   - 前端: http://localhost:3000
   - 后端API: http://localhost:8000
   - API文档: http://localhost:8000/docs

## 📊 使用方法

1. **创建分析任务**: 在Web界面中输入产品名称
2. **数据收集**: 系统自动从Reddit和Product Hunt收集数据
3. **AI分析**: 先进语言模型分析收集的数据
4. **报告生成**: 生成详细洞察和建议
5. **查看结果**: 通过Web界面访问综合报告

## 🔧 配置

### 环境变量

```bash
# 数据库
DATABASE_URL=postgresql://user:password@localhost/insightagent

# Redis
REDIS_URL=redis://localhost:6379

# AI服务
OPENAI_API_KEY=your_openai_api_key
SILICONFLOW_API_KEY=your_siliconflow_api_key

# 外部API
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
PRODUCT_HUNT_API_TOKEN=your_product_hunt_token
```

## 🧪 测试

### 后端测试
```bash
cd backend
pytest tests/
```

### 前端测试
```bash
cd frontend
npm test
```

## 📈 API端点

- `GET /api/v1/tasks/` - 列出所有分析任务
- `POST /api/v1/tasks/` - 创建新的分析任务
- `GET /api/v1/tasks/{task_id}` - 获取任务详情
- `GET /api/v1/reports/{task_id}` - 获取分析报告
- `WebSocket /ws` - 实时任务更新

## 🤝 贡献指南

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m '添加一些很棒的功能'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

## 📝 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- OpenAI 提供语言模型
- Reddit 和 Product Hunt 提供数据访问
- 开源社区提供各种库和工具

## 📞 支持

如需支持和问题解答，请在GitHub上开启issue或联系开发团队。

---

**由 InsightAgent 团队 ❤️ 制作**
