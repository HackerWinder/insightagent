"""
报告生成服务
"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid
import re

from app.models.task import AnalysisResult
from app.core.config import settings

logger = logging.getLogger(__name__)


class ReportService:
    """报告生成服务"""
    
    def __init__(self):
        self.report_templates = {
            "executive_summary": self._generate_executive_summary,
            "detailed_analysis": self._generate_detailed_analysis,
            "markdown_report": self._generate_markdown_report,
            "json_report": self._generate_json_report
        }
    
    async def generate_insight_report(
        self, 
        task_id: str, 
        product_name: str, 
        analysis_result: AnalysisResult,
        raw_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成洞察报告
        
        Args:
            task_id: 任务ID
            product_name: 产品名称
            analysis_result: 分析结果
            raw_data: 原始数据
            
        Returns:
            生成的报告
        """
        try:
            logger.info(f"Generating insight report for task {task_id}")
            
            # 准备报告数据
            report_data = {
                "task_id": task_id,
                "product_name": product_name,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "analysis_result": analysis_result.to_dict() if analysis_result else {},
                "raw_data_summary": self._summarize_raw_data(raw_data) if raw_data else {}
            }
            
            # 生成不同格式的报告
            reports = {}
            for format_name, generator in self.report_templates.items():
                try:
                    reports[format_name] = await generator(report_data)
                except Exception as e:
                    logger.error(f"Failed to generate {format_name} report: {e}")
                    reports[format_name] = {"error": str(e)}
            
            # 主报告（Markdown格式）
            main_report = reports.get("markdown_report", {})
            
            return {
                "task_id": task_id,
                "product_name": product_name,
                "report_type": "insight_analysis",
                "generated_at": report_data["generated_at"],
                "main_report": main_report,
                "alternative_formats": {
                    "json": reports.get("json_report"),
                    "executive_summary": reports.get("executive_summary"),
                    "detailed_analysis": reports.get("detailed_analysis")
                },
                "metadata": {
                    "generator": "InsightAgent ReportService",
                    "version": "1.0.0",
                    "data_sources": self._extract_data_sources(raw_data)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate insight report for task {task_id}: {e}")
            raise Exception(f"Report generation failed: {str(e)}")
    
    def _summarize_raw_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        汇总原始数据
        
        Args:
            raw_data: 原始数据
            
        Returns:
            数据汇总
        """
        summary = {
            "total_sources": 0,
            "total_posts": 0,
            "total_comments": 0,
            "data_sources": [],
            "collection_timeframe": None
        }
        
        if not raw_data:
            return summary
        
        try:
            # 统计各数据源
            for source, data in raw_data.items():
                if isinstance(data, dict):
                    summary["total_sources"] += 1
                    summary["data_sources"].append(source)
                    
                    # 统计帖子数量
                    if "posts" in data:
                        posts = data["posts"]
                        if isinstance(posts, list):
                            summary["total_posts"] += len(posts)
                    
                    # 统计评论数量
                    if "comments" in data:
                        comments = data["comments"]
                        if isinstance(comments, list):
                            summary["total_comments"] += len(comments)
                    
                    # 收集时间信息
                    if "collected_at" in data and not summary["collection_timeframe"]:
                        summary["collection_timeframe"] = data["collected_at"]
        
        except Exception as e:
            logger.error(f"Error summarizing raw data: {e}")
        
        return summary
    
    def _extract_data_sources(self, raw_data: Optional[Dict[str, Any]]) -> List[str]:
        """提取数据源列表"""
        if not raw_data:
            return []
        
        sources = []
        for key, value in raw_data.items():
            if isinstance(value, dict) and "source" in value:
                sources.append(value["source"])
            else:
                sources.append(key)
        
        return list(set(sources))  # 去重
    
    async def _generate_executive_summary(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成执行摘要"""
        analysis = report_data.get("analysis_result", {})
        product_name = report_data.get("product_name", "Unknown Product")
        
        # 提取关键洞察
        key_insights = analysis.get("key_insights", [])
        sentiment_score = analysis.get("sentiment_score", 0)
        
        # 生成摘要
        summary_points = []
        
        # 情感分析摘要
        if sentiment_score > 0.6:
            sentiment_summary = f"{product_name} 获得了积极的用户反馈"
        elif sentiment_score < -0.2:
            sentiment_summary = f"{product_name} 面临一些用户满意度挑战"
        else:
            sentiment_summary = f"{product_name} 获得了中性的用户反馈"
        
        summary_points.append(sentiment_summary)
        
        # 添加关键洞察
        if key_insights:
            summary_points.extend(key_insights[:3])  # 取前3个洞察
        
        return {
            "title": f"{product_name} 市场洞察执行摘要",
            "overall_sentiment": sentiment_summary,
            "key_points": summary_points,
            "recommendation": self._generate_recommendation(analysis),
            "generated_at": report_data.get("generated_at")
        }
    
    async def _generate_detailed_analysis(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成详细分析"""
        analysis = report_data.get("analysis_result", {})
        raw_summary = report_data.get("raw_data_summary", {})
        
        return {
            "data_collection": {
                "sources_count": raw_summary.get("total_sources", 0),
                "posts_analyzed": raw_summary.get("total_posts", 0),
                "comments_analyzed": raw_summary.get("total_comments", 0),
                "data_sources": raw_summary.get("data_sources", [])
            },
            "sentiment_analysis": {
                "overall_score": analysis.get("sentiment_score", 0),
                "distribution": analysis.get("sentiment_distribution", {}),
                "interpretation": self._interpret_sentiment(analysis.get("sentiment_score", 0))
            },
            "topic_analysis": {
                "top_topics": analysis.get("top_topics", []),
                "topic_count": len(analysis.get("top_topics", []))
            },
            "feature_requests": {
                "requests": analysis.get("feature_requests", []),
                "total_requests": len(analysis.get("feature_requests", []))
            },
            "key_insights": analysis.get("key_insights", [])
        }
    
    async def _generate_markdown_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成Markdown格式报告"""
        product_name = report_data.get("product_name", "Unknown Product")
        analysis = report_data.get("analysis_result", {})
        raw_summary = report_data.get("raw_data_summary", {})
        generated_at = report_data.get("generated_at", "")
        
        # 构建Markdown内容
        markdown_content = f"""# {product_name} 市场洞察分析报告

## 📊 报告概览

- **产品名称**: {product_name}
- **分析时间**: {generated_at}
- **数据源数量**: {raw_summary.get('total_sources', 0)}
- **分析帖子数**: {raw_summary.get('total_posts', 0)}
- **分析评论数**: {raw_summary.get('total_comments', 0)}

## 🎯 执行摘要

{self._format_executive_summary(analysis, product_name)}

## 📈 情感分析

### 整体情感评分
- **评分**: {analysis.get('sentiment_score', 0):.2f} / 1.0
- **解读**: {self._interpret_sentiment(analysis.get('sentiment_score', 0))}

### 情感分布
{self._format_sentiment_distribution(analysis.get('sentiment_distribution', {}))}

## 🏷️ 热门话题

{self._format_topics(analysis.get('top_topics', []))}

## 💡 功能需求分析

{self._format_feature_requests(analysis.get('feature_requests', []))}

## 🔍 关键洞察

{self._format_key_insights(analysis.get('key_insights', []))}

## 📋 建议与行动项

{self._generate_recommendation(analysis)}

---
*报告由 InsightAgent 自动生成*
"""
        
        return {
            "format": "markdown",
            "content": markdown_content,
            "word_count": len(markdown_content.split()),
            "sections": [
                "报告概览", "执行摘要", "情感分析", 
                "热门话题", "功能需求分析", "关键洞察", "建议与行动项"
            ]
        }
    
    async def _generate_json_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成JSON格式报告"""
        return {
            "format": "json",
            "data": report_data,
            "structure": {
                "task_info": ["task_id", "product_name", "generated_at"],
                "analysis_results": ["sentiment_score", "sentiment_distribution", "top_topics", "feature_requests", "key_insights"],
                "data_summary": ["total_sources", "total_posts", "total_comments", "data_sources"]
            }
        }
    
    def _format_executive_summary(self, analysis: Dict[str, Any], product_name: str) -> str:
        """格式化执行摘要"""
        sentiment_score = analysis.get("sentiment_score", 0)
        key_insights = analysis.get("key_insights", [])
        
        summary = f"基于对 {product_name} 的市场数据分析，"
        
        if sentiment_score > 0.6:
            summary += "产品获得了用户的积极反馈。"
        elif sentiment_score < -0.2:
            summary += "产品在用户满意度方面存在改进空间。"
        else:
            summary += "产品获得了中性的用户反馈。"
        
        if key_insights:
            summary += f" 主要发现包括：{key_insights[0] if key_insights else '暂无特别洞察'}。"
        
        return summary
    
    def _format_sentiment_distribution(self, distribution: Dict[str, float]) -> str:
        """格式化情感分布"""
        if not distribution:
            return "- 暂无情感分布数据"
        
        formatted = []
        for sentiment, ratio in distribution.items():
            percentage = ratio * 100
            formatted.append(f"- **{sentiment.title()}**: {percentage:.1f}%")
        
        return "\n".join(formatted)
    
    def _format_topics(self, topics: List[Dict[str, Any]]) -> str:
        """格式化话题列表"""
        if not topics:
            return "暂无热门话题数据"
        
        formatted = []
        for i, topic in enumerate(topics[:5], 1):  # 只显示前5个话题
            topic_name = topic.get("topic", f"话题{i}")
            weight = topic.get("weight", 0)
            formatted.append(f"{i}. **{topic_name}** (权重: {weight:.2f})")
        
        return "\n".join(formatted)
    
    def _format_feature_requests(self, requests: List[Dict[str, Any]]) -> str:
        """格式化功能需求"""
        if not requests:
            return "暂无功能需求数据"
        
        formatted = []
        for i, request in enumerate(requests[:5], 1):  # 只显示前5个需求
            feature = request.get("feature", f"功能需求{i}")
            frequency = request.get("frequency", 0)
            sentiment = request.get("sentiment", 0)
            formatted.append(f"{i}. **{feature}** (提及次数: {frequency}, 情感: {sentiment:.2f})")
        
        return "\n".join(formatted)
    
    def _format_key_insights(self, insights: List[str]) -> str:
        """格式化关键洞察"""
        if not insights:
            return "暂无关键洞察"
        
        formatted = []
        for i, insight in enumerate(insights[:5], 1):  # 只显示前5个洞察
            formatted.append(f"{i}. {insight}")
        
        return "\n".join(formatted)
    
    def _interpret_sentiment(self, score: float) -> str:
        """解释情感评分"""
        if score >= 0.7:
            return "非常积极 - 用户对产品表现出强烈的正面情感"
        elif score >= 0.3:
            return "积极 - 用户对产品持正面态度"
        elif score >= -0.1:
            return "中性 - 用户对产品的情感较为平衡"
        elif score >= -0.5:
            return "消极 - 用户对产品存在一些不满"
        else:
            return "非常消极 - 用户对产品表现出强烈的负面情感"
    
    def _generate_recommendation(self, analysis: Dict[str, Any]) -> str:
        """生成建议"""
        sentiment_score = analysis.get("sentiment_score", 0)
        feature_requests = analysis.get("feature_requests", [])
        
        recommendations = []
        
        # 基于情感评分的建议
        if sentiment_score < 0:
            recommendations.append("🔧 **优先改进用户体验** - 当前用户满意度较低，建议深入分析用户痛点")
        elif sentiment_score > 0.7:
            recommendations.append("🚀 **扩大市场推广** - 用户反馈积极，可考虑加大营销投入")
        else:
            recommendations.append("📊 **持续监控反馈** - 保持当前产品质量，定期收集用户反馈")
        
        # 基于功能需求的建议
        if feature_requests:
            top_request = feature_requests[0] if feature_requests else {}
            feature_name = top_request.get("feature", "")
            if feature_name:
                recommendations.append(f"💡 **考虑开发 '{feature_name}'** - 这是用户最关注的功能需求")
        
        # 通用建议
        recommendations.extend([
            "📈 **定期进行市场分析** - 建议每月进行一次类似分析",
            "🎯 **关注竞争对手动态** - 保持对市场变化的敏感度"
        ])
        
        return "\n".join(recommendations)
    
    async def export_report(
        self, 
        report: Dict[str, Any], 
        format_type: str = "markdown"
    ) -> Dict[str, Any]:
        """
        导出报告
        
        Args:
            report: 报告数据
            format_type: 导出格式 (markdown, json, pdf)
            
        Returns:
            导出结果
        """
        try:
            if format_type == "markdown":
                content = report.get("main_report", {}).get("content", "")
                return {
                    "format": "markdown",
                    "content": content,
                    "filename": f"insight_report_{report.get('task_id', 'unknown')}.md",
                    "size": len(content.encode('utf-8'))
                }
            
            elif format_type == "json":
                content = json.dumps(report, ensure_ascii=False, indent=2)
                return {
                    "format": "json",
                    "content": content,
                    "filename": f"insight_report_{report.get('task_id', 'unknown')}.json",
                    "size": len(content.encode('utf-8'))
                }
            
            else:
                raise ValueError(f"Unsupported export format: {format_type}")
                
        except Exception as e:
            logger.error(f"Failed to export report: {e}")
            raise Exception(f"Report export failed: {str(e)}")


# 全局报告服务实例
report_service = ReportService()