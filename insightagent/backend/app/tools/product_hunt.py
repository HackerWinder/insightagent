"""
Product Hunt数据收集工具
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta

from .base import BaseTool, ToolError, RateLimitError
from app.core.config import settings

logger = logging.getLogger(__name__)


class ProductHuntTool(BaseTool):
    """Product Hunt数据收集工具"""
    
    def __init__(self):
        super().__init__(
            name="product_hunt_tool",
            description="从Product Hunt收集产品信息、评论和用户反馈数据"
        )
        self.api_base_url = "https://api.producthunt.com/v2/api/graphql"
        self.web_base_url = "https://www.producthunt.com"
        self.access_token: Optional[str] = None
        self._rate_limit_delay = 2.0  # Product Hunt有更严格的限制
    
    async def authenticate(self) -> bool:
        """
        Product Hunt API认证
        
        Returns:
            是否认证成功
        """
        if not settings.product_hunt_api_key:
            logger.warning("Product Hunt API key not configured")
            return False
        
        try:
            self.access_token = settings.product_hunt_api_key
            logger.info("Product Hunt API authentication configured")
            return True
            
        except Exception as e:
            logger.error(f"Product Hunt API authentication failed: {e}")
            return False
    
    async def collect_data(self, product_name: str, **kwargs) -> Dict[str, Any]:
        """
        收集Product Hunt数据
        
        Args:
            product_name: 产品名称
            **kwargs: 其他参数
                - search_limit: 搜索结果数量限制
                - include_comments: 是否包含评论
                - days_back: 搜索多少天前的数据
                
        Returns:
            收集到的Product Hunt数据
        """
        product_name = self.validate_product_name(product_name)
        search_limit = kwargs.get("search_limit", 20)
        include_comments = kwargs.get("include_comments", True)
        days_back = kwargs.get("days_back", 30)
        
        logger.info(f"Starting Product Hunt data collection for: {product_name}")
        
        # 如果有API密钥，尝试使用GraphQL API
        if await self.authenticate():
            return await self._collect_via_graphql(product_name, search_limit, include_comments, days_back)
        else:
            # 否则使用网页抓取（简化版本）
            return await self._collect_via_web_scraping(product_name, search_limit)
    
    async def _collect_via_graphql(
        self, 
        product_name: str, 
        search_limit: int,
        include_comments: bool,
        days_back: int
    ) -> Dict[str, Any]:
        """
        通过GraphQL API收集数据
        """
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # 搜索产品
        products = await self.execute_with_retry(
            self._search_products_graphql,
            product_name, search_limit, headers
        )
        
        # 为每个产品获取详细信息和评论
        detailed_products = []
        for product in products:
            try:
                product_details = await self.execute_with_retry(
                    self._get_product_details_graphql,
                    product["id"], include_comments, headers
                )
                detailed_products.append(product_details)
                
                # 添加延迟以避免触发限制
                await asyncio.sleep(self._rate_limit_delay)
                
            except Exception as e:
                logger.error(f"Failed to get details for product {product.get('name', 'unknown')}: {e}")
                detailed_products.append(product)  # 使用基本信息
        
        return {
            "source": "product_hunt_graphql",
            "product_name": product_name,
            "products": detailed_products,
            "total_products": len(detailed_products),
            "search_limit": search_limit,
            "collected_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def _collect_via_web_scraping(
        self, 
        product_name: str, 
        search_limit: int
    ) -> Dict[str, Any]:
        """
        通过网页抓取收集数据（简化版本）
        """
        logger.info("Using web scraping method for Product Hunt data collection")
        
        # 这里实现简化的网页抓取逻辑
        # 实际项目中可能需要使用BeautifulSoup等工具
        
        return {
            "source": "product_hunt_web_scraping",
            "product_name": product_name,
            "products": [],
            "total_products": 0,
            "note": "Web scraping implementation needed",
            "collected_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def _search_products_graphql(
        self, 
        product_name: str, 
        limit: int,
        headers: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        通过GraphQL搜索产品
        """
        query = """
        query SearchPosts($query: String!, $first: Int!) {
            posts(query: $query, first: $first) {
                edges {
                    node {
                        id
                        name
                        tagline
                        description
                        slug
                        url
                        website
                        votesCount
                        commentsCount
                        createdAt
                        featuredAt
                        user {
                            id
                            name
                            username
                        }
                        makers {
                            id
                            name
                            username
                        }
                        topics {
                            edges {
                                node {
                                    id
                                    name
                                }
                            }
                        }
                        thumbnail {
                            url
                        }
                        gallery {
                            images {
                                url
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            "query": product_name,
            "first": limit
        }
        
        response = await self.make_request(
            method="POST",
            url=self.api_base_url,
            headers=headers,
            json_data={"query": query, "variables": variables}
        )
        
        data = response.json()
        
        if "errors" in data:
            raise ToolError(f"GraphQL errors: {data['errors']}")
        
        products = []
        edges = data.get("data", {}).get("posts", {}).get("edges", [])
        
        for edge in edges:
            node = edge.get("node", {})
            products.append(self._extract_product_data(node))
        
        return products
    
    async def _get_product_details_graphql(
        self, 
        product_id: str, 
        include_comments: bool,
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        通过GraphQL获取产品详细信息
        """
        query = """
        query GetPost($id: ID!, $commentsFirst: Int) {
            post(id: $id) {
                id
                name
                tagline
                description
                slug
                url
                website
                votesCount
                commentsCount
                createdAt
                featuredAt
                reviewsCount
                reviewsRating
                user {
                    id
                    name
                    username
                }
                makers {
                    id
                    name
                    username
                }
                topics {
                    edges {
                        node {
                            id
                            name
                        }
                    }
                }
                comments(first: $commentsFirst) {
                    edges {
                        node {
                            id
                            body
                            createdAt
                            votesCount
                            user {
                                id
                                name
                                username
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            "id": product_id,
            "commentsFirst": 50 if include_comments else 0
        }
        
        response = await self.make_request(
            method="POST",
            url=self.api_base_url,
            headers=headers,
            json_data={"query": query, "variables": variables}
        )
        
        data = response.json()
        
        if "errors" in data:
            raise ToolError(f"GraphQL errors: {data['errors']}")
        
        post_data = data.get("data", {}).get("post", {})
        return self._extract_detailed_product_data(post_data, include_comments)
    
    def _extract_product_data(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取产品基本数据
        """
        return {
            "id": product.get("id"),
            "name": product.get("name"),
            "tagline": self.extract_text_content(product.get("tagline", "")),
            "description": self.extract_text_content(product.get("description", "")),
            "slug": product.get("slug"),
            "url": product.get("url"),
            "website": product.get("website"),
            "votes_count": product.get("votesCount", 0),
            "comments_count": product.get("commentsCount", 0),
            "created_at": self.format_timestamp(product.get("createdAt")),
            "featured_at": self.format_timestamp(product.get("featuredAt")),
            "user": self._extract_user_data(product.get("user", {})),
            "makers": [self._extract_user_data(maker) for maker in product.get("makers", [])],
            "topics": [topic["node"]["name"] for topic in product.get("topics", {}).get("edges", [])],
            "thumbnail_url": product.get("thumbnail", {}).get("url"),
            "product_hunt_url": f"{self.web_base_url}/posts/{product.get('slug')}" if product.get("slug") else None
        }
    
    def _extract_detailed_product_data(self, product: Dict[str, Any], include_comments: bool) -> Dict[str, Any]:
        """
        提取产品详细数据
        """
        basic_data = self._extract_product_data(product)
        
        # 添加详细信息
        basic_data.update({
            "reviews_count": product.get("reviewsCount", 0),
            "reviews_rating": product.get("reviewsRating", 0),
        })
        
        # 添加评论
        if include_comments:
            comments = []
            comment_edges = product.get("comments", {}).get("edges", [])
            for edge in comment_edges:
                comment_node = edge.get("node", {})
                comments.append(self._extract_comment_data(comment_node))
            basic_data["comments"] = comments
        
        return basic_data
    
    def _extract_user_data(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取用户数据
        """
        return {
            "id": user.get("id"),
            "name": user.get("name"),
            "username": user.get("username"),
            "profile_url": f"{self.web_base_url}/@{user.get('username')}" if user.get("username") else None
        }
    
    def _extract_comment_data(self, comment: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取评论数据
        """
        return {
            "id": comment.get("id"),
            "body": self.extract_text_content(comment.get("body", "")),
            "created_at": self.format_timestamp(comment.get("createdAt")),
            "votes_count": comment.get("votesCount", 0),
            "user": self._extract_user_data(comment.get("user", {}))
        }
    
    async def get_trending_products(self, days: int = 7) -> Dict[str, Any]:
        """
        获取趋势产品
        
        Args:
            days: 获取多少天内的趋势产品
            
        Returns:
            趋势产品数据
        """
        if not await self.authenticate():
            raise ToolError("Product Hunt API authentication required")
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # 计算日期范围
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        query = """
        query GetTrendingPosts($after: DateTime!, $before: DateTime!, $first: Int!) {
            posts(after: $after, before: $before, first: $first, order: VOTES) {
                edges {
                    node {
                        id
                        name
                        tagline
                        votesCount
                        commentsCount
                        createdAt
                        featuredAt
                        slug
                        url
                        website
                    }
                }
            }
        }
        """
        
        variables = {
            "after": start_date.isoformat(),
            "before": end_date.isoformat(),
            "first": 50
        }
        
        response = await self.make_request(
            method="POST",
            url=self.api_base_url,
            headers=headers,
            json_data={"query": query, "variables": variables}
        )
        
        data = response.json()
        
        if "errors" in data:
            raise ToolError(f"GraphQL errors: {data['errors']}")
        
        products = []
        edges = data.get("data", {}).get("posts", {}).get("edges", [])
        
        for edge in edges:
            node = edge.get("node", {})
            products.append(self._extract_product_data(node))
        
        return {
            "source": "product_hunt_trending",
            "products": products,
            "total_products": len(products),
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            },
            "collected_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Product Hunt工具健康检查
        """
        try:
            health_info = {
                "tool": self.name,
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # 检查API密钥配置
            if settings.product_hunt_api_key:
                auth_success = await self.authenticate()
                health_info["api_auth_available"] = auth_success
                
                if auth_success:
                    # 测试简单的API调用
                    headers = {
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    }
                    
                    # 简单的查询测试
                    test_query = """
                    query {
                        viewer {
                            user {
                                id
                                name
                            }
                        }
                    }
                    """
                    
                    response = await self.make_request(
                        method="POST",
                        url=self.api_base_url,
                        headers=headers,
                        json_data={"query": test_query}
                    )
                    
                    health_info["api_accessible"] = True
                else:
                    health_info["api_accessible"] = False
            else:
                health_info["api_auth_available"] = False
                health_info["note"] = "API key not configured"
            
            return health_info
            
        except Exception as e:
            return {
                "tool": self.name,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }