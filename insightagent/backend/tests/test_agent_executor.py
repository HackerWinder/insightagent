"""
Agent执行引擎的单元测试
"""
import pytest
import uuid
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

from app.services.agent_executor import (
    AgentExecutorService, 
    LangChainToolWrapper, 
    InsightAgentCallbackHandler
)
from app.services.task_manager import TaskManager
from app.models.task import LogLevel


class TestLangChainToolWrapper:
    """LangChainToolWrapper测试"""
    
    @pytest.fixture
    def mock_collect_func(self):
        """模拟数据收集函数"""
        async def mock_func(product_name: str, **kwargs):
            return {
                "product_name": product_name,
                "data": "mock_data",
                "source": "test_tool"
            }
        return mock_func
    
    @pytest.fixture
    def tool_wrapper(self, mock_collect_func):
        """创建工具包装器实例"""
        return LangChainToolWrapper(
            tool_name="test_tool",
            description="Test tool for testing",
            collect_func=mock_collect_func
        )
    
    def test_tool_wrapper_initialization(self, tool_wrapper):
        """测试工具包装器初始化"""
        assert tool_wrapper.name == "test_tool"
        assert tool_wrapper.description == "Test tool for testing"
        assert tool_wrapper.collect_func is not None
    
    @pytest.mark.asyncio
    async def test_arun(self, tool_wrapper):
        """测试异步运行"""
        result = await tool_wrapper._arun("TestProduct")
        
        # 结果应该是JSON字符串
        import json
        parsed_result = json.loads(result)
        
        assert parsed_result["product_name"] == "TestProduct"
        assert parsed_result["data"] == "mock_data"
        assert parsed_result["source"] == "test_tool"
    
    @pytest.mark.asyncio
    async def test_arun_with_error(self, mock_collect_func):
        """测试异步运行时的错误处理"""
        # 创建会抛出异常的函数
        async def error_func(product_name: str, **kwargs):
            raise Exception("Test error")
        
        tool_wrapper = LangChainToolWrapper(
            tool_name="error_tool",
            description="Error tool",
            collect_func=error_func
        )
        
        result = await tool_wrapper._arun("TestProduct")
        assert "工具执行失败" in result
        assert "Test error" in result


class TestInsightAgentCallbackHandler:
    """InsightAgentCallbackHandler测试"""
    
    @pytest.fixture
    def mock_task_manager(self):
        """模拟任务管理器"""
        task_manager = Mock(spec=TaskManager)
        task_manager.add_task_log = AsyncMock()
        return task_manager
    
    @pytest.fixture
    def callback_handler(self, mock_task_manager):
        """创建回调处理器实例"""
        return InsightAgentCallbackHandler(
            task_id="test_task_id",
            user_id="test_user",
            task_manager=mock_task_manager
        )
    
    @pytest.mark.asyncio
    async def test_on_agent_action(self, callback_handler, mock_task_manager):
        """测试Agent动作回调"""
        from langchain.schema import AgentAction
        
        action = AgentAction(
            tool="test_tool",
            tool_input="test_input",
            log="test_log"
        )
        
        await callback_handler.on_agent_action(action)
        
        # 验证日志记录被调用
        mock_task_manager.add_task_log.assert_called_once()
        call_args = mock_task_manager.add_task_log.call_args
        
        assert call_args[1]["level"] == LogLevel.INFO
        assert "test_tool" in call_args[1]["message"]
        assert "agent_action_1" in call_args[1]["step"]
    
    @pytest.mark.asyncio
    async def test_on_agent_finish(self, callback_handler, mock_task_manager):
        """测试Agent完成回调"""
        from langchain.schema import AgentFinish
        
        finish = AgentFinish(
            return_values={"output": "Test output"},
            log="test_log"
        )
        
        await callback_handler.on_agent_finish(finish)
        
        # 验证日志记录被调用
        mock_task_manager.add_task_log.assert_called_once()
        call_args = mock_task_manager.add_task_log.call_args
        
        assert call_args[1]["level"] == LogLevel.INFO
        assert "Agent执行完成" in call_args[1]["message"]
        assert call_args[1]["step"] == "agent_finish"
    
    @pytest.mark.asyncio
    async def test_on_tool_start(self, callback_handler, mock_task_manager):
        """测试工具开始回调"""
        serialized = {"name": "test_tool"}
        
        await callback_handler.on_tool_start(serialized, "test_input")
        
        # 验证日志记录被调用
        mock_task_manager.add_task_log.assert_called_once()
        call_args = mock_task_manager.add_task_log.call_args
        
        assert call_args[1]["level"] == LogLevel.INFO
        assert "开始执行工具" in call_args[1]["message"]
        assert "test_tool" in call_args[1]["message"]
    
    @pytest.mark.asyncio
    async def test_on_tool_error(self, callback_handler, mock_task_manager):
        """测试工具错误回调"""
        error = Exception("Test tool error")
        
        await callback_handler.on_tool_error(error)
        
        # 验证日志记录被调用
        mock_task_manager.add_task_log.assert_called_once()
        call_args = mock_task_manager.add_task_log.call_args
        
        assert call_args[1]["level"] == LogLevel.ERROR
        assert "工具执行错误" in call_args[1]["message"]
        assert "Test tool error" in call_args[1]["message"]


class TestAgentExecutorService:
    """AgentExecutorService测试"""
    
    @pytest.fixture
    def agent_service(self):
        """创建Agent执行服务实例"""
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.openai_api_key = "test_api_key"
            mock_settings.openai_model = "gpt-3.5-turbo"
            
            service = AgentExecutorService()
            return service
    
    def test_agent_service_initialization(self, agent_service):
        """测试Agent服务初始化"""
        # 检查工具是否被初始化
        assert len(agent_service.tools) >= 2
        
        tool_names = [tool.name for tool in agent_service.tools]
        assert "reddit_search" in tool_names
        assert "product_hunt_search" in tool_names
    
    def test_get_agent_status(self, agent_service):
        """测试获取Agent状态"""
        status = agent_service.get_agent_status()
        
        assert "llm_available" in status
        assert "tools_count" in status
        assert "agent_available" in status
        assert "tools" in status
        
        assert status["tools_count"] >= 2
        assert isinstance(status["tools"], list)
    
    @pytest.mark.asyncio
    async def test_plan_execution_steps(self, agent_service):
        """测试执行步骤规划"""
        steps = await agent_service.plan_execution_steps("TestProduct")
        
        assert len(steps) == 5
        assert all("step" in step for step in steps)
        assert all("name" in step for step in steps)
        assert all("description" in step for step in steps)
        
        # 验证步骤顺序
        step_names = [step["name"] for step in steps]
        assert "数据收集规划" in step_names[0]
        assert "报告生成" in step_names[-1]
    
    @pytest.mark.asyncio
    async def test_collect_reddit_data(self, agent_service):
        """测试Reddit数据收集包装函数"""
        with patch('app.services.agent_executor.tool_manager') as mock_tool_manager:
            mock_tool_manager.collect_data_from_tool = AsyncMock(return_value={
                "source": "reddit",
                "data": "test_data"
            })
            
            result = await agent_service._collect_reddit_data("TestProduct")
            
            assert result["source"] == "reddit"
            assert result["data"] == "test_data"
            
            # 验证工具管理器被正确调用
            mock_tool_manager.collect_data_from_tool.assert_called_once_with(
                "reddit_tool", "TestProduct"
            )
    
    @pytest.mark.asyncio
    async def test_collect_reddit_data_with_error(self, agent_service):
        """测试Reddit数据收集错误处理"""
        with patch('app.services.agent_executor.tool_manager') as mock_tool_manager:
            mock_tool_manager.collect_data_from_tool = AsyncMock(
                side_effect=Exception("Reddit API error")
            )
            
            result = await agent_service._collect_reddit_data("TestProduct")
            
            assert "error" in result
            assert result["source"] == "reddit"
            assert "Reddit API error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_collect_product_hunt_data(self, agent_service):
        """测试Product Hunt数据收集包装函数"""
        with patch('app.services.agent_executor.tool_manager') as mock_tool_manager:
            mock_tool_manager.collect_data_from_tool = AsyncMock(return_value={
                "source": "product_hunt",
                "data": "test_data"
            })
            
            result = await agent_service._collect_product_hunt_data("TestProduct")
            
            assert result["source"] == "product_hunt"
            assert result["data"] == "test_data"
            
            # 验证工具管理器被正确调用
            mock_tool_manager.collect_data_from_tool.assert_called_once_with(
                "product_hunt_tool", "TestProduct"
            )
    
    @pytest.mark.asyncio
    async def test_health_check_without_llm(self):
        """测试没有LLM时的健康检查"""
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.openai_api_key = None
            
            service = AgentExecutorService()
            health_info = await service.health_check()
            
            assert health_info["status"] == "unhealthy"
            assert health_info["details"]["llm_connection"] == "not_configured"
    
    @pytest.mark.asyncio
    async def test_health_check_with_llm(self, agent_service):
        """测试有LLM时的健康检查"""
        # Mock LLM调用
        if agent_service.llm:
            with patch.object(agent_service.llm, 'invoke', return_value="Hello response"):
                with patch('app.services.agent_executor.tool_manager') as mock_tool_manager:
                    mock_tool_manager.health_check_all_tools = AsyncMock(return_value={
                        "overall_status": "healthy"
                    })
                    
                    health_info = await agent_service.health_check()
                    
                    assert "status" in health_info
                    assert "details" in health_info
    
    @pytest.mark.asyncio
    async def test_execute_task_without_agent(self):
        """测试没有Agent时的任务执行"""
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.openai_api_key = None
            
            service = AgentExecutorService()
            
            mock_task_manager = Mock(spec=TaskManager)
            
            with pytest.raises(Exception, match="Agent executor not initialized"):
                await service.execute_task(
                    task_id="test_task",
                    user_id="test_user",
                    product_name="TestProduct",
                    task_manager=mock_task_manager
                )
    
    def test_initialization_without_openai_key(self):
        """测试没有OpenAI API密钥时的初始化"""
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.openai_api_key = None
            
            service = AgentExecutorService()
            
            assert service.llm is None
            assert service.agent_executor is None
            assert len(service.tools) >= 2  # 工具仍然应该被初始化
    
    def test_initialization_with_openai_key(self):
        """测试有OpenAI API密钥时的初始化"""
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.openai_api_key = "test_key"
            mock_settings.openai_model = "gpt-3.5-turbo"
            
            with patch('langchain_openai.ChatOpenAI') as mock_llm:
                with patch('langchain.agents.create_react_agent') as mock_create_agent:
                    with patch('langchain.agents.AgentExecutor') as mock_executor:
                        
                        service = AgentExecutorService()
                        
                        # 验证LLM被创建
                        mock_llm.assert_called_once()
                        
                        # 验证Agent被创建（如果LLM和工具都可用）
                        if service.llm and service.tools:
                            mock_create_agent.assert_called_once()
                            mock_executor.assert_called_once()