# 多模态文档知识库问答系统（RAG + 多 Agent）

## 1. 产品概述

### 1.1 背景

企业或个人拥有大量非结构化文档（PDF、Word、HTML、Markdown 等），传统全文搜索难以实现精准、上下文理解的问答。

本系统利用 RAG（检索增强生成）+ 多 Agent 协作技术，将文档自动解析、向量化、检索，并通过大模型生成高质量回答，提升知识检索效率 60% 以上，可广泛应用于企业知识库、客服助手、科研文献分析、电商产品资料管理等场景。

### 1.2 目标

- 支持多模态文档（PDF/DOCX/HTML/MD/TXT）自动向量化存储
- 提供基于内容的智能问答和多 Agent 协作分析
- 前端提供便捷的上传、聊天交互界面
- 可私有化部署，保障数据安全

### 1.3 核心价值

- **检索精准**：结合向量检索（Milvus/Chroma/FAISS）与 rerank 提升相关性
- **可扩展**：可适配行业场景（法律、电商、医学、科研）
- **数据安全**：本地向量库，不依赖外部存储

## 2. 用户和场景

### 2.1 目标用户

- 企业员工（内部知识库）
- 客服团队（标准问答）
- 科研人员（文献辅助分析）
- 电商运营（商品说明文档管理）

### 2.2 使用场景

- 上传公司业务手册 → 随时提问 → 系统准确回答
- 上交科研论文 PDF → 系统总结研究方法与结论
- 导入电商商品规格书 → 快速生成营销文案

## 3. 功能需求

### 3.1 核心功能列表

| 模块 | 功能 | 详述 |
|------|------|------|
| 文档解析 | 多格式解析（PDF、DOCX、HTML、TXT、MD） | 自动识别并解析，提取纯文本 |
| 文本切分 | 内容分块（chunk size=500, overlap=100） | 适配向量相似度检索 |
| 向量化 | 生成文本 embedding | 使用 OpenAIEmbeddings 或 SentenceTransformer |
| 向量存储 | 本地持久化 | Chroma/Milvus/FAISS |
| 检索 | 相似度检索（top-k=5） | 支持 MMR、Hybrid Search |
| 大模型问答 | 基于检索结果生成回答 | gpt-3.5-turbo / DeepSeek-Chat |
| 多 Agent 协作 | 检索 Agent → 摘要 Agent → 答案 Agent | LangGraph/MCP 实现 |
| 接口服务 | 文件上传接口 / 提问接口 | FastAPI 实现 Restful API |
| 前端界面 | 上传文档 + 聊天交互 | React + Tailwind |
| 部署 | Docker 一键部署 | 后端+前端容器化 |

### 3.2 功能流程图

```
用户上传文档 → 文档解析模块 → 文本切分 → 向量化 → 向量存储 → 提问 → 检索器 → 检索 Agent → 摘要 Agent → 答案 Agent → 返回结果
```

## 4. 技术方案

### 4.1 技术选型

- **后端**：Python 3.10+ / FastAPI / asyncio
- **大模型调用**：OpenAI API / DeepSeek API
- **向量数据库**：Chroma（默认），可切换 Milvus/FAISS
- **多 Agent 框架**：LangChain + LangGraph/MCP
- **前端**：React + TypeScript + TailwindCSS
- **数据解析**：PyMuPDF / python-docx / BeautifulSoup
- **部署**：Docker / docker-compose

### 4.2 系统架构图（MVP版本）

```
[前端React] <—REST API—> [FastAPI] —解析模块—> [文本切分] —> [嵌入生成] —> [Chroma向量库]
                                                                    ↑
                                                                 [检索Agent] ←→ [摘要Agent] ←→ [答案Agent] ←→ [大模型API]
```

## 5. 数据流程（RAG Pipeline）

1. 文档上传接口接收文件
2. 文件解析为纯文本
3. 按 500 tokens 切分，overlap 100
4. 每段文本嵌入 + 存入向量数据库
5. 用户提问 → 检索器返回相关文本块
6. 将相关块拼接到 Prompt → 传入大模型
7. 模型结合上下文生成最终答案

## 6. 验收标准（MVP版本）

- [ ] 成功上传一个 5MB 的 PDF 文件并完成入库
- [ ] 问答结果中至少 80% 答案来自上传文档内容（可人工验证）
- [ ] 单次问答响应时间 ≤ 3 秒（本地+GPT API 场景）
- [ ] 同时支持 3 种文档格式（PDF/DOCX/TXT）
- [ ] 支持多轮对话，保留上下文（后端会话管理或前端状态）

## 7. 未来扩展功能

- [ ] 支持 HTML/Markdown/图片 OCR
- [ ] 向量检索 + 关键词检索（Hybrid Search）
- [ ] 用户身份鉴权与私有化知识库
- [ ] 大模型本地部署（如 LLaMA2）
- [ ] 知识库可视化管理界面
