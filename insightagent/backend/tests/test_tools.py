"""
数据收集工具的单元测试
"""
import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
import httpx

from app.tools.base import BaseTool, ToolError, RateLimitError
from app.tools.reddit import RedditTool
from app.tools.product_hunt import ProductHuntTool
from app.services.tool_manager import ToolManager


class TestBaseTool:
    """BaseTool基类测试"""
    
    class MockTool(BaseTool):
        """测试用的Mock工具"""
        
        def __init__(self):
            super().__init__("mock_tool", "Mock tool for testing")
        
        async def collect_data(self, product_name: str, **kwargs):
            return {"product_name": product_name, "data": "mock_data"}
    
    @pytest.fixture
    def mock_tool(self):
        """创建Mock工具实例"""
        return self.MockTool()
    
    def test_tool_initialization(self, mock_tool):
        """测试工具初始化"""
        assert mock_tool.name == "mock_tool"
        assert mock_tool.description == "Mock tool for testing"
        assert mock_tool._rate_limit_delay == 1.0
        assert mock_tool._max_retries == 3
    
    def test_validate_product_name(self, mock_tool):
        """测试产品名称验证"""
        # 正常情况
        assert mock_tool.validate_product_name("Figma") == "Figma"
        assert mock_tool.validate_product_name("  Figma  ") == "Figma"
        
        # 异常情况
        with pytest.raises(ToolError):
            mock_tool.validate_product_name("")
        
        with pytest.raises(ToolError):
            mock_tool.validate_product_name("   ")
    
    def test_extract_text_content(self, mock_tool):
        """测试文本内容提取"""
        # 正常文本
        text = "This is a test text"
        assert mock_tool.extract_text_content(text) == text
        
        # 多余空白字符
        text_with_spaces = "This   is\n\na   test\t\ttext"
        expected = "This is a test text"
        assert mock_tool.extract_text_content(text_with_spaces) == expected
        
        # 超长文本
        long_text = "a" * 1500
        result = mock_tool.extract_text_content(long_text, max_length=100)
        assert len(result) == 103  # 100 + "..."
        assert result.endswith("...")
    
    def test_format_timestamp(self, mock_tool):
        """测试时间戳格式化"""
        # Unix时间戳
        timestamp = 1640995200  # 2022-01-01 00:00:00 UTC
        result = mock_tool.format_timestamp(timestamp)
        assert "2022-01-01" in result
        
        # 字符串时间戳
        iso_string = "2022-01-01T00:00:00Z"
        result = mock_tool.format_timestamp(iso_string)
        assert "2022-01-01" in result
    
    def test_get_tool_info(self, mock_tool):
        """测试获取工具信息"""
        info = mock_tool.get_tool_info()
        
        assert info["name"] == "mock_tool"
        assert info["description"] == "Mock tool for testing"
        assert "rate_limit_delay" in info
        assert "max_retries" in info
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_tool):
        """测试健康检查"""
        health_info = await mock_tool.health_check()
        
        assert health_info["tool"] == "mock_tool"
        assert health_info["status"] == "healthy"
        assert "timestamp" in health_info
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_success(self, mock_tool):
        """测试重试机制 - 成功情况"""
        async def mock_func():
            return "success"
        
        result = await mock_tool.execute_with_retry(mock_func)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_with_retries(self, mock_tool):
        """测试重试机制 - 需要重试的情况"""
        call_count = 0
        
        async def mock_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RateLimitError("Rate limited")
            return "success"
        
        # 减少延迟以加快测试
        mock_tool._rate_limit_delay = 0.01
        
        result = await mock_tool.execute_with_retry(mock_func)
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_max_retries_exceeded(self, mock_tool):
        """测试重试机制 - 超过最大重试次数"""
        async def mock_func():
            raise RateLimitError("Always fails")
        
        mock_tool._rate_limit_delay = 0.01
        mock_tool._max_retries = 1
        
        with pytest.raises(RateLimitError):
            await mock_tool.execute_with_retry(mock_func)


class TestRedditTool:
    """RedditTool测试"""
    
    @pytest.fixture
    def reddit_tool(self):
        """创建RedditTool实例"""
        return RedditTool()
    
    @pytest.fixture
    def mock_response(self):
        """模拟Reddit API响应"""
        return {
            "data": {
                "children": [
                    {
                        "data": {
                            "id": "test_post_1",
                            "title": "Great product!",
                            "selftext": "I love this product",
                            "score": 100,
                            "num_comments": 25,
                            "created_utc": 1640995200,
                            "author": "test_user",
                            "subreddit": "technology",
                            "permalink": "/r/technology/comments/test_post_1/",
                            "url": "https://example.com",
                            "is_self": True
                        }
                    }
                ]
            }
        }
    
    def test_reddit_tool_initialization(self, reddit_tool):
        """测试Reddit工具初始化"""
        assert reddit_tool.name == "reddit_tool"
        assert "Reddit" in reddit_tool.description
        assert len(reddit_tool.default_subreddits) > 0
        assert "technology" in reddit_tool.default_subreddits
    
    @pytest.mark.asyncio
    async def test_authenticate_without_credentials(self, reddit_tool):
        """测试无凭据时的认证"""
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.reddit_client_id = None
            mock_settings.reddit_client_secret = None
            
            result = await reddit_tool.authenticate()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_authenticate_with_credentials(self, reddit_tool):
        """测试有凭据时的认证"""
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.reddit_client_id = "test_client_id"
            mock_settings.reddit_client_secret = "test_client_secret"
            mock_settings.reddit_user_agent = "TestAgent/1.0"
            
            # Mock HTTP响应
            mock_response = Mock()
            mock_response.json.return_value = {
                "access_token": "test_token",
                "expires_in": 3600
            }
            
            with patch.object(reddit_tool, 'make_request', return_value=mock_response):
                result = await reddit_tool.authenticate()
                assert result is True
                assert reddit_tool.access_token == "test_token"
    
    def test_extract_post_data(self, reddit_tool):
        """测试帖子数据提取"""
        post_data = {
            "id": "test_post",
            "title": "Test Title",
            "selftext": "Test content",
            "score": 100,
            "num_comments": 25,
            "created_utc": 1640995200,
            "author": "test_user",
            "subreddit": "technology",
            "permalink": "/r/technology/comments/test_post/",
            "url": "https://example.com"
        }
        
        extracted = reddit_tool._extract_post_data(post_data)
        
        assert extracted["id"] == "test_post"
        assert extracted["title"] == "Test Title"
        assert extracted["score"] == 100
        assert extracted["subreddit"] == "technology"
        assert "2022-01-01" in extracted["created_utc"]
    
    def test_extract_comment_data(self, reddit_tool):
        """测试评论数据提取"""
        comment_data = {
            "id": "test_comment",
            "body": "Great comment!",
            "author": "commenter",
            "score": 50,
            "created_utc": 1640995200,
            "parent_id": "t3_test_post",
            "subreddit": "technology"
        }
        
        extracted = reddit_tool._extract_comment_data(comment_data)
        
        assert extracted["id"] == "test_comment"
        assert extracted["body"] == "Great comment!"
        assert extracted["score"] == 50
        assert extracted["author"] == "commenter"


class TestProductHuntTool:
    """ProductHuntTool测试"""
    
    @pytest.fixture
    def ph_tool(self):
        """创建ProductHuntTool实例"""
        return ProductHuntTool()
    
    def test_product_hunt_tool_initialization(self, ph_tool):
        """测试Product Hunt工具初始化"""
        assert ph_tool.name == "product_hunt_tool"
        assert "Product Hunt" in ph_tool.description
        assert ph_tool._rate_limit_delay == 2.0  # 更严格的限制
    
    @pytest.mark.asyncio
    async def test_authenticate_without_api_key(self, ph_tool):
        """测试无API密钥时的认证"""
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.product_hunt_api_key = None
            
            result = await ph_tool.authenticate()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_authenticate_with_api_key(self, ph_tool):
        """测试有API密钥时的认证"""
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.product_hunt_api_key = "test_api_key"
            
            result = await ph_tool.authenticate()
            assert result is True
            assert ph_tool.access_token == "test_api_key"
    
    def test_extract_product_data(self, ph_tool):
        """测试产品数据提取"""
        product_data = {
            "id": "test_product",
            "name": "Test Product",
            "tagline": "Amazing product",
            "description": "This is a test product",
            "slug": "test-product",
            "url": "https://producthunt.com/posts/test-product",
            "website": "https://testproduct.com",
            "votesCount": 150,
            "commentsCount": 25,
            "createdAt": "2022-01-01T00:00:00Z",
            "user": {
                "id": "user1",
                "name": "Test User",
                "username": "testuser"
            },
            "makers": [],
            "topics": {"edges": [{"node": {"name": "productivity"}}]}
        }
        
        extracted = ph_tool._extract_product_data(product_data)
        
        assert extracted["id"] == "test_product"
        assert extracted["name"] == "Test Product"
        assert extracted["votes_count"] == 150
        assert extracted["topics"] == ["productivity"]
        assert extracted["user"]["name"] == "Test User"
    
    def test_extract_user_data(self, ph_tool):
        """测试用户数据提取"""
        user_data = {
            "id": "user1",
            "name": "Test User",
            "username": "testuser"
        }
        
        extracted = ph_tool._extract_user_data(user_data)
        
        assert extracted["id"] == "user1"
        assert extracted["name"] == "Test User"
        assert extracted["username"] == "testuser"
        assert "testuser" in extracted["profile_url"]


class TestToolManager:
    """ToolManager测试"""
    
    @pytest.fixture
    def tool_manager(self):
        """创建ToolManager实例"""
        return ToolManager()
    
    def test_tool_manager_initialization(self, tool_manager):
        """测试工具管理器初始化"""
        available_tools = tool_manager.get_available_tools()
        
        assert "reddit_tool" in available_tools
        assert "product_hunt_tool" in available_tools
        assert len(available_tools) >= 2
    
    def test_get_tool(self, tool_manager):
        """测试获取工具"""
        reddit_tool = tool_manager.get_tool("reddit_tool")
        assert reddit_tool is not None
        assert reddit_tool.name == "reddit_tool"
        
        # 测试不存在的工具
        non_existent = tool_manager.get_tool("non_existent_tool")
        assert non_existent is None
    
    def test_get_tools_info(self, tool_manager):
        """测试获取工具信息"""
        tools_info = tool_manager.get_tools_info()
        
        assert "reddit_tool" in tools_info
        assert "product_hunt_tool" in tools_info
        
        reddit_info = tools_info["reddit_tool"]
        assert reddit_info["name"] == "reddit_tool"
        assert "description" in reddit_info
    
    @pytest.mark.asyncio
    async def test_get_tool_capabilities(self, tool_manager):
        """测试获取工具能力"""
        capabilities = await tool_manager.get_tool_capabilities("reddit_tool")
        
        assert capabilities["name"] == "reddit_tool"
        assert "description" in capabilities
        assert "supported_parameters" in capabilities
        assert "rate_limits" in capabilities
        assert "data_sources" in capabilities
        
        # 测试不存在的工具
        with pytest.raises(Exception):
            await tool_manager.get_tool_capabilities("non_existent_tool")
    
    @pytest.mark.asyncio
    async def test_collect_data_from_tool_not_found(self, tool_manager):
        """测试从不存在的工具收集数据"""
        with pytest.raises(Exception):
            await tool_manager.collect_data_from_tool("non_existent_tool", "TestProduct")
    
    @pytest.mark.asyncio
    async def test_health_check_all_tools(self, tool_manager):
        """测试所有工具健康检查"""
        # Mock工具的健康检查方法
        for tool in tool_manager.tools.values():
            tool.health_check = AsyncMock(return_value={
                "tool": tool.name,
                "status": "healthy",
                "timestamp": "2022-01-01T00:00:00Z"
            })
        
        health_status = await tool_manager.health_check_all_tools()
        
        assert "overall_status" in health_status
        assert "healthy_tools" in health_status
        assert "total_tools" in health_status
        assert "tools" in health_status
        
        # 验证所有工具都被检查了
        for tool_name in tool_manager.get_available_tools():
            assert tool_name in health_status["tools"]