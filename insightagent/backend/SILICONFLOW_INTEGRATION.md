# SiliconFlow 集成指南

## 概述

本项目已集成 SiliconFlow API，作为 OpenAI API 的替代方案。SiliconFlow 提供了多种开源模型，包括 DeepSeek、Qwen 等。

## 配置

### 环境变量

在 `.env` 文件中添加以下配置：

```bash
# SiliconFlow 配置
SILICONFLOW_API_KEY=your_api_key_here
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
SILICONFLOW_MODEL=deepseek-ai/deepseek-chat
```

### 支持的模型

SiliconFlow 支持多种模型，常用的包括：

- `deepseek-ai/deepseek-chat` - DeepSeek Chat 模型
- `deepseek-ai/deepseek-coder` - DeepSeek Coder 模型
- `Qwen/Qwen2.5-72B-Instruct` - Qwen 2.5 72B 模型
- `Qwen/Qwen2.5-14B-Instruct` - Qwen 2.5 14B 模型

## 使用方法

### 1. 在代码中使用

```python
from app.core.config import settings
from langchain_openai import ChatOpenAI

# 初始化 LLM
llm = ChatOpenAI(
    model=settings.siliconflow_model,
    temperature=0.1,
    max_tokens=1000,
    openai_api_key=settings.siliconflow_api_key,
    openai_api_base=settings.siliconflow_base_url
)

# 使用 LLM
response = llm.invoke("Hello, how are you?")
print(response.content)
```

### 2. 在 LangChain 中使用

```python
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

# 创建提示模板
prompt = PromptTemplate(
    input_variables=["question"],
    template="请回答以下问题：{question}"
)

# 创建链
chain = LLMChain(llm=llm, prompt=prompt)

# 运行链
result = chain.run("什么是人工智能？")
print(result)
```

## 配置验证

运行测试脚本验证配置：

```bash
python3 test_siliconflow.py
```

## 注意事项

1. **API 密钥安全**：请确保将 API 密钥存储在环境变量中，不要硬编码在代码里
2. **模型选择**：根据任务需求选择合适的模型
3. **速率限制**：注意 API 的速率限制
4. **成本控制**：监控 API 使用量和成本

## 故障排除

### 常见错误

1. **401 Invalid token**：检查 API 密钥是否正确
2. **429 Rate limit exceeded**：请求过于频繁，需要等待
3. **500 Internal server error**：服务器内部错误，稍后重试

### 调试技巧

1. 检查环境变量是否正确设置
2. 验证 API 密钥是否有效
3. 查看网络连接是否正常
4. 检查模型名称是否正确

## 更多信息

- [SiliconFlow 官方文档](https://siliconflow.cn/)
- [API 文档](https://siliconflow.cn/docs)
- [模型列表](https://siliconflow.cn/models)
