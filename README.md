# 多模态文档知识库问答系统（RAG + 多 Agent）

## 项目简介

基于RAG（检索增强生成）和多Agent协作技术的智能文档问答系统，支持多模态文档解析、向量化存储和智能问答。

## 技术栈

- **后端**: Python 3.10+ / FastAPI / asyncio
- **前端**: React + TypeScript + TailwindCSS
- **向量数据库**: Chroma（默认），可切换 Milvus/FAISS
- **大模型**: OpenAI API / DeepSeek API
- **多Agent框架**: LangChain + LangGraph/MCP
- **部署**: Docker / docker-compose

## 项目结构

```
├── backend/          # 后端服务
├── frontend/         # 前端界面
├── docs/            # 项目文档
├── scripts/         # 部署脚本
├── prd.md           # 产品需求文档
└── README.md        # 项目说明
```

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 16+
- Docker & Docker Compose

### 安装依赖

```bash
# 后端依赖
cd backend
pip install -r requirements.txt

# 前端依赖
cd frontend
npm install
```

### 运行项目

```bash
# 使用Docker Compose一键启动
docker-compose up -d
```

## 功能特性

- ✅ 多格式文档解析（PDF/DOCX/HTML/TXT/MD）
- ✅ 智能文本切分和向量化
- ✅ 基于向量相似度的精准检索
- ✅ 多Agent协作问答
- ✅ 现代化Web界面
- ✅ 私有化部署支持

## 开发计划

详见 [PRD文档](prd.md)

## 许可证

MIT License
