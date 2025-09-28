"""
LangChain Agent执行引擎
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone
import uuid

from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import BaseTool as LangChainBaseTool
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import AgentAction, AgentFinish
from langchain.callbacks.base import BaseCallbackHandler

from app.core.config import settings
from app.services.tool_manager import tool_manager
from app.services.task_manager import TaskManager
from app.models.task import TaskStatus, LogLevel
from app.services.websocket_manager import websocket_notifier

logger = logging.getLogger(__name__)


class InsightAgentCallbackHandler(BaseCallbackHandler):
    """InsightAgent专用的回调处理器"""
    
    def __init__(self, task_id: str, user_id: str, task_manager: TaskManager):
        self.task_id = task_id
        self.user_id = user_id
        self.task_manager = task_manager
        self.step_count = 0
    
    async def on_agent_action(self, action: AgentAction, **kwargs) -> None:
        """Agent执行动作时的回调"""
        self.step_count += 1
        
        # 记录Agent动作
        message = f"执行步骤 {self.step_count}: {action.tool} - {action.tool_input}"
        await self.task_manager.add_task_log(
            task_id=uuid.UUID(self.task_id),
            level=LogLevel.INFO,
            message=message,
            step=f"agent_action_{self.step_count}"
        )
        
        logger.info(f"Agent action for task {self.task_id}: {action.tool}")
    
    async def on_agent_finish(self, finish: AgentFinish, **kwargs) -> None:
        """Agent完成时的回调"""
        message = f"Agent执行完成: {finish.return_values.get('output', 'No output')}"
        await self.task_manager.add_task_log(
            task_id=uuid.UUID(self.task_id),
            level=LogLevel.INFO,
            message=message,
            step="agent_finish"
        )
        
        logger.info(f"Agent finished for task {self.task_id}")
    
    async def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs) -> None:
        """工具开始执行时的回调"""
        tool_name = serialized.get("name", "unknown_tool")
        message = f"开始执行工具: {tool_name}"
        
        await self.task_manager.add_task_log(
            task_id=uuid.UUID(self.task_id),
            level=LogLevel.INFO,
            message=message,
            step=f"tool_start_{tool_name}"
        )
    
    async def on_tool_end(self, output: str, **kwargs) -> None:
        """工具执行完成时的回调"""
        message = f"工具执行完成，输出长度: {len(output)} 字符"
        
        await self.task_manager.add_task_log(
            task_id=uuid.UUID(self.task_id),
            level=LogLevel.INFO,
            message=message,
            step="tool_end"
        )
    
    async def on_tool_error(self, error: Exception, **kwargs) -> None:
        """工具执行错误时的回调"""
        message = f"工具执行错误: {str(error)}"
        
        await self.task_manager.add_task_log(
            task_id=uuid.UUID(self.task_id),
            level=LogLevel.ERROR,
            message=message,
            step="tool_error"
        )


class LangChainToolWrapper(LangChainBaseTool):
    """将我们的数据收集工具包装为LangChain工具"""
    
    collect_func: Callable = None
    
    def __init__(self, tool_name: str, description: str, collect_func: Callable):
        super().__init__(name=tool_name, description=description, collect_func=collect_func)
    
    def _run(self, product_name: str, **kwargs) -> str:
        """同步运行工具（LangChain要求）"""
        try:
            # 尝试获取当前运行的事件循环
            try:
                loop = asyncio.get_running_loop()
                # 如果已经在事件循环中，使用线程池在新循环中运行
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._run_in_new_loop, product_name, **kwargs)
                    result = future.result(timeout=300)  # 5分钟超时
            except RuntimeError:
                # 没有运行的事件循环，直接创建新的
                result = asyncio.run(self.collect_func(product_name, **kwargs))
            
            # 将结果转换为字符串
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Tool {self.name} execution failed: {e}")
            return f"工具执行失败: {str(e)}"
    
    def _run_in_new_loop(self, product_name: str, **kwargs):
        """在新的事件循环中运行异步函数"""
        return asyncio.run(self.collect_func(product_name, **kwargs))
    async def _arun(self, product_name: str, **kwargs) -> str:
        """异步运行工具"""
        try:
            result = await self.collect_func(product_name, **kwargs)
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Tool {self.name} async execution failed: {e}")
            return f"工具执行失败: {str(e)}"


class AgentExecutorService:
    """Agent执行服务"""
    
    def __init__(self):
        self.llm = None
        self.agent_executor = None
        self.tools = []
        self._initialize_llm()
        self._initialize_tools()
        self._initialize_agent()
    
    def _initialize_llm(self):
        """初始化语言模型 - 优先使用SiliconFlow，回退到OpenAI"""
        # 优先使用SiliconFlow
        if settings.siliconflow_api_key:
            try:
                self.llm = ChatOpenAI(
                    model=settings.siliconflow_model,
                    temperature=0.1,
                    max_tokens=2000,
                    openai_api_key=settings.siliconflow_api_key,
                    openai_api_base=settings.siliconflow_base_url
                )
                logger.info(f"Initialized LLM with SiliconFlow: {settings.siliconflow_model}")
                return
            except Exception as e:
                logger.error(f"Failed to initialize SiliconFlow LLM: {e}")
        
        # 回退到OpenAI
        if settings.openai_api_key:
            try:
                self.llm = ChatOpenAI(
                    model=settings.openai_model,
                    temperature=0.1,
                    max_tokens=2000,
                    openai_api_key=settings.openai_api_key
                )
                logger.info(f"Initialized LLM with OpenAI: {settings.openai_model}")
                return
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI LLM: {e}")
        
        # 如果都没有配置
        logger.warning("Neither SiliconFlow nor OpenAI API key configured")
    
    def _initialize_tools(self):
        """初始化工具"""
        self.tools = []
        
        # 包装Reddit工具
        reddit_tool = LangChainToolWrapper(
            tool_name="reddit_search",
            description="搜索Reddit上关于产品的讨论、评论和用户反馈。输入产品名称，返回相关的帖子和评论数据。",
            collect_func=self._collect_reddit_data
        )
        self.tools.append(reddit_tool)
        
        # 包装Product Hunt工具
        ph_tool = LangChainToolWrapper(
            tool_name="product_hunt_search",
            description="搜索Product Hunt上的产品信息、评论和用户反馈。输入产品名称，返回产品详情和评论数据。",
            collect_func=self._collect_product_hunt_data
        )
        self.tools.append(ph_tool)
        
        logger.info(f"Initialized {len(self.tools)} tools for agent")
    
    async def _collect_reddit_data(self, product_name: str, **kwargs) -> Dict[str, Any]:
        """收集Reddit数据的包装函数"""
        try:
            return await tool_manager.collect_data_from_tool("reddit_tool", product_name, **kwargs)
        except Exception as e:
            logger.error(f"Reddit data collection failed: {e}")
            return {"error": str(e), "source": "reddit"}
    
    async def _collect_product_hunt_data(self, product_name: str, **kwargs) -> Dict[str, Any]:
        """收集Product Hunt数据的包装函数"""
        try:
            return await tool_manager.collect_data_from_tool("product_hunt_tool", product_name, **kwargs)
        except Exception as e:
            logger.error(f"Product Hunt data collection failed: {e}")
            return {"error": str(e), "source": "product_hunt"}
    
    def _initialize_agent(self):
        """初始化Agent"""
        if not self.llm or not self.tools:
            logger.warning("Cannot initialize agent: LLM or tools not available")
            return
        
        try:
            # 创建Agent提示模板
            prompt_template = """你是一个专业的市场洞察分析师，专门分析产品的用户反馈和市场表现。

你的任务是：
1. 使用可用的工具收集关于指定产品的数据
2. 分析收集到的数据，提取关键洞察
3. 生成结构化的分析报告

可用工具：
{tools}

工具名称: {tool_names}

使用以下格式：

Question: 需要分析的产品名称
Thought: 我需要分析这个产品，首先收集相关数据
Action: [工具名称]
Action Input: [工具输入]
Observation: [工具输出]
... (重复Thought/Action/Action Input/Observation直到有足够信息)
Thought: 我现在有足够的信息来生成分析报告
Final Answer: [最终的分析报告]

开始！

Question: {input}
Thought: {agent_scratchpad}"""

            prompt = PromptTemplate(
                template=prompt_template,
                input_variables=["input", "agent_scratchpad", "tools", "tool_names"]
            )
            
            # 创建ReAct Agent
            agent = create_react_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=prompt
            )
            
            # 创建Agent执行器
            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=True,
                max_iterations=10,
                max_execution_time=1800,  # 30分钟超时
                handle_parsing_errors=True,
                return_intermediate_steps=True
            )
            
            logger.info("Agent executor initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
    
    async def execute_task(
        self, 
        task_id: str, 
        user_id: str, 
        product_name: str,
        task_manager: TaskManager
    ) -> Dict[str, Any]:
        """
        执行市场洞察分析任务
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            product_name: 产品名称
            task_manager: 任务管理器
            
        Returns:
            分析结果
        """
        if not self.agent_executor:
            raise Exception("Agent executor not initialized")
        
        logger.info(f"Starting agent execution for task {task_id}, product: {product_name}")
        
        # 更新任务状态为运行中
        from app.schemas.task import TaskUpdate
        await task_manager.update_task(
            task_id=uuid.UUID(task_id),
            task_update=TaskUpdate(status=TaskStatus.RUNNING, progress=0.1),
            user_id=user_id
        )
        
        try:
            # 创建回调处理器
            callback_handler = InsightAgentCallbackHandler(task_id, user_id, task_manager)
            
            # 准备输入
            agent_input = f"请分析产品 '{product_name}' 的市场表现和用户反馈"
            
            # 执行Agent
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.agent_executor.invoke(
                    {"input": agent_input},
                    {"callbacks": [callback_handler]}
                )
            )
            
            # 更新进度
            await task_manager.update_task(
                task_id=uuid.UUID(task_id),
                task_update=TaskUpdate(progress=0.8),
                user_id=user_id
            )
            
            # 处理结果
            analysis_result = {
                "task_id": task_id,
                "product_name": product_name,
                "agent_output": result.get("output", ""),
                "intermediate_steps": result.get("intermediate_steps", []),
                "execution_metadata": {
                    "total_steps": len(result.get("intermediate_steps", [])),
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "agent_model": settings.openai_model
                }
            }
            
            logger.info(f"Agent execution completed for task {task_id}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Agent execution failed for task {task_id}: {e}")
            
            # 记录错误
            await task_manager.add_task_log(
                task_id=uuid.UUID(task_id),
                level=LogLevel.ERROR,
                message=f"Agent执行失败: {str(e)}",
                step="agent_execution_error"
            )
            
            raise Exception(f"Agent execution failed: {str(e)}")
    
    async def plan_execution_steps(self, product_name: str) -> List[Dict[str, Any]]:
        """
        规划执行步骤
        
        Args:
            product_name: 产品名称
            
        Returns:
            执行步骤列表
        """
        steps = [
            {
                "step": 1,
                "name": "数据收集规划",
                "description": f"分析产品 '{product_name}' 并规划数据收集策略",
                "estimated_duration": "2-3分钟"
            },
            {
                "step": 2,
                "name": "Reddit数据收集",
                "description": "从Reddit收集用户讨论和反馈",
                "estimated_duration": "3-5分钟"
            },
            {
                "step": 3,
                "name": "Product Hunt数据收集",
                "description": "从Product Hunt收集产品信息和评论",
                "estimated_duration": "2-4分钟"
            },
            {
                "step": 4,
                "name": "数据分析",
                "description": "分析收集到的数据，提取关键洞察",
                "estimated_duration": "5-8分钟"
            },
            {
                "step": 5,
                "name": "报告生成",
                "description": "生成结构化的市场洞察报告",
                "estimated_duration": "2-3分钟"
            }
        ]
        
        return steps
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        获取Agent状态
        
        Returns:
            Agent状态信息
        """
        return {
            "llm_available": self.llm is not None,
            "llm_model": settings.openai_model if self.llm else None,
            "tools_count": len(self.tools),
            "agent_available": self.agent_executor is not None,
            "tools": [tool.name for tool in self.tools] if self.tools else []
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Agent健康检查
        
        Returns:
            健康状态信息
        """
        try:
            status = self.get_agent_status()
            
            # 检查LLM连接
            if self.llm:
                try:
                    # 简单的测试调用
                    test_response = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: self.llm.invoke("Hello")
                    )
                    status["llm_connection"] = "healthy"
                except Exception as e:
                    status["llm_connection"] = f"error: {str(e)}"
            else:
                status["llm_connection"] = "not_configured"
            
            # 检查工具状态
            tools_health = await tool_manager.health_check_all_tools()
            status["tools_health"] = tools_health["overall_status"]
            
            overall_status = "healthy"
            if not status["agent_available"] or status["llm_connection"] != "healthy":
                overall_status = "unhealthy"
            elif status["tools_health"] != "healthy":
                overall_status = "degraded"
            
            return {
                "status": overall_status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "details": status
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }


# 全局Agent执行器实例
agent_executor_service = AgentExecutorService()