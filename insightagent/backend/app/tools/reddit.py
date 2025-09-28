"""
Reddit数据收集工具
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from .base import BaseTool, ToolError, RateLimitError
from app.core.config import settings

logger = logging.getLogger(__name__)


class RedditTool(BaseTool):
    """Reddit数据收集工具"""
    
    def __init__(self):
        super().__init__(
            name="reddit_tool",
            description="从Reddit收集产品相关的讨论和反馈数据"
        )
        self.base_url = "https://www.reddit.com"
        self.api_base_url = "https://oauth.reddit.com"
        self.auth_url = "https://www.reddit.com/api/v1/access_token"
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        
        # 默认搜索的subreddit列表
        self.default_subreddits = [
            "technology", "startups", "entrepreneur", "SaaS", "webdev",
            "design", "UXDesign", "ProductManagement", "software"
        ]
    
    async def authenticate(self) -> bool:
        """
        Reddit API认证
        
        Returns:
            是否认证成功
        """
        if not settings.reddit_client_id or not settings.reddit_client_secret:
            logger.warning("Reddit API credentials not configured")
            return False
        
        try:
            # 检查现有token是否有效
            if (self.access_token and self.token_expires_at and 
                datetime.now(timezone.utc) < self.token_expires_at):
                return True
            
            # 获取新的访问token
            auth_data = {
                "grant_type": "client_credentials"
            }
            
            auth_headers = {
                "User-Agent": settings.reddit_user_agent
            }
            
            response = await self.make_request(
                method="POST",
                url=self.auth_url,
                headers=auth_headers,
                data=auth_data,
                auth=(settings.reddit_client_id, settings.reddit_client_secret)
            )
            
            token_data = response.json()
            self.access_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 3600)
            
            # 设置token过期时间（提前5分钟过期以确保安全）
            self.token_expires_at = datetime.now(timezone.utc).timestamp() + expires_in - 300
            
            logger.info("Reddit API authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Reddit API authentication failed: {e}")
            return False
    
    async def collect_data(self, product_name: str, **kwargs) -> Dict[str, Any]:
        """
        收集Reddit数据
        
        Args:
            product_name: 产品名称
            **kwargs: 其他参数
                - subreddits: 指定的subreddit列表
                - limit: 每个subreddit的帖子数量限制
                - time_filter: 时间过滤器 (hour, day, week, month, year, all)
                
        Returns:
            收集到的Reddit数据
        """
        product_name = self.validate_product_name(product_name)
        subreddits = kwargs.get("subreddits", self.default_subreddits)
        limit = kwargs.get("limit", 25)
        time_filter = kwargs.get("time_filter", "month")
        
        logger.info(f"Starting Reddit data collection for: {product_name}")
        
        # 如果有API凭据，尝试使用官方API
        if await self.authenticate():
            return await self._collect_via_api(product_name, subreddits, limit, time_filter)
        else:
            # 否则使用公开的JSON接口
            return await self._collect_via_json(product_name, subreddits, limit, time_filter)
    
    async def _collect_via_api(
        self, 
        product_name: str, 
        subreddits: List[str], 
        limit: int,
        time_filter: str
    ) -> Dict[str, Any]:
        """
        通过Reddit官方API收集数据
        """
        all_posts = []
        all_comments = []
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "User-Agent": settings.reddit_user_agent
        }
        
        for subreddit in subreddits:
            try:
                # 搜索帖子
                posts = await self.execute_with_retry(
                    self._search_subreddit_api,
                    subreddit, product_name, limit, time_filter, headers
                )
                all_posts.extend(posts)
                
                # 为每个帖子获取评论
                for post in posts[:5]:  # 只获取前5个帖子的评论以控制数据量
                    comments = await self.execute_with_retry(
                        self._get_post_comments_api,
                        subreddit, post["id"], headers
                    )
                    all_comments.extend(comments)
                
                # 添加延迟以避免触发限制
                await asyncio.sleep(self._rate_limit_delay)
                
            except Exception as e:
                logger.error(f"Failed to collect from r/{subreddit}: {e}")
                continue
        
        return {
            "source": "reddit_api",
            "product_name": product_name,
            "subreddits_searched": subreddits,
            "posts": all_posts,
            "comments": all_comments,
            "total_posts": len(all_posts),
            "total_comments": len(all_comments),
            "collected_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def _collect_via_json(
        self, 
        product_name: str, 
        subreddits: List[str], 
        limit: int,
        time_filter: str
    ) -> Dict[str, Any]:
        """
        通过Reddit公开JSON接口收集数据
        """
        all_posts = []
        
        for subreddit in subreddits:
            try:
                posts = await self.execute_with_retry(
                    self._search_subreddit_json,
                    subreddit, product_name, limit, time_filter
                )
                all_posts.extend(posts)
                
                # 添加延迟以避免触发限制
                await asyncio.sleep(self._rate_limit_delay)
                
            except Exception as e:
                logger.error(f"Failed to collect from r/{subreddit}: {e}")
                continue
        
        return {
            "source": "reddit_json",
            "product_name": product_name,
            "subreddits_searched": subreddits,
            "posts": all_posts,
            "total_posts": len(all_posts),
            "collected_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def _search_subreddit_api(
        self, 
        subreddit: str, 
        product_name: str, 
        limit: int,
        time_filter: str,
        headers: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        通过API搜索subreddit
        """
        url = f"{self.api_base_url}/r/{subreddit}/search"
        params = {
            "q": product_name,
            "restrict_sr": "true",
            "sort": "relevance",
            "t": time_filter,
            "limit": limit,
            "type": "link"
        }
        
        response = await self.make_request("GET", url, headers=headers, params=params)
        data = response.json()
        
        posts = []
        for post_data in data.get("data", {}).get("children", []):
            post = post_data.get("data", {})
            posts.append(self._extract_post_data(post))
        
        return posts
    
    async def _search_subreddit_json(
        self, 
        subreddit: str, 
        product_name: str, 
        limit: int,
        time_filter: str
    ) -> List[Dict[str, Any]]:
        """
        通过JSON接口搜索subreddit
        """
        url = f"{self.base_url}/r/{subreddit}/search.json"
        params = {
            "q": product_name,
            "restrict_sr": "1",
            "sort": "relevance",
            "t": time_filter,
            "limit": limit
        }
        
        headers = {
            "User-Agent": settings.reddit_user_agent
        }
        
        response = await self.make_request("GET", url, headers=headers, params=params)
        data = response.json()
        
        posts = []
        for post_data in data.get("data", {}).get("children", []):
            post = post_data.get("data", {})
            posts.append(self._extract_post_data(post))
        
        return posts
    
    async def _get_post_comments_api(
        self, 
        subreddit: str, 
        post_id: str, 
        headers: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        通过API获取帖子评论
        """
        url = f"{self.api_base_url}/r/{subreddit}/comments/{post_id}"
        params = {
            "limit": 50,
            "sort": "top"
        }
        
        response = await self.make_request("GET", url, headers=headers, params=params)
        data = response.json()
        
        comments = []
        if len(data) > 1:
            comment_listing = data[1].get("data", {}).get("children", [])
            for comment_data in comment_listing:
                comment = comment_data.get("data", {})
                if comment.get("body") and comment.get("body") != "[deleted]":
                    comments.append(self._extract_comment_data(comment))
        
        return comments
    
    def _extract_post_data(self, post: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取帖子数据
        """
        return {
            "id": post.get("id"),
            "title": self.extract_text_content(post.get("title", "")),
            "selftext": self.extract_text_content(post.get("selftext", "")),
            "url": post.get("url"),
            "subreddit": post.get("subreddit"),
            "author": post.get("author"),
            "score": post.get("score", 0),
            "upvote_ratio": post.get("upvote_ratio", 0),
            "num_comments": post.get("num_comments", 0),
            "created_utc": self.format_timestamp(post.get("created_utc")),
            "permalink": f"{self.base_url}{post.get('permalink', '')}" if post.get("permalink") else None,
            "flair_text": post.get("link_flair_text"),
            "is_self": post.get("is_self", False),
            "domain": post.get("domain")
        }
    
    def _extract_comment_data(self, comment: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取评论数据
        """
        return {
            "id": comment.get("id"),
            "body": self.extract_text_content(comment.get("body", "")),
            "author": comment.get("author"),
            "score": comment.get("score", 0),
            "created_utc": self.format_timestamp(comment.get("created_utc")),
            "parent_id": comment.get("parent_id"),
            "link_id": comment.get("link_id"),
            "subreddit": comment.get("subreddit"),
            "depth": comment.get("depth", 0),
            "is_submitter": comment.get("is_submitter", False)
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Reddit工具健康检查
        """
        try:
            # 测试基本的JSON接口访问
            url = f"{self.base_url}/r/test.json"
            headers = {"User-Agent": settings.reddit_user_agent}
            
            response = await self.make_request("GET", url, headers=headers, params={"limit": 1})
            
            health_info = {
                "tool": self.name,
                "status": "healthy",
                "api_accessible": True,
                "authenticated": bool(self.access_token),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # 如果配置了API凭据，测试认证
            if settings.reddit_client_id and settings.reddit_client_secret:
                auth_success = await self.authenticate()
                health_info["api_auth_available"] = auth_success
            else:
                health_info["api_auth_available"] = False
                health_info["note"] = "API credentials not configured, using public JSON interface"
            
            return health_info
            
        except Exception as e:
            return {
                "tool": self.name,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }