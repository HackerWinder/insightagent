"""
报告相关端点
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, Optional
from pydantic import BaseModel
import uuid

from app.api.deps import get_current_user_id, get_db_session
from app.services.report_service import report_service
from app.services.task_manager import TaskManager
from sqlalchemy.orm import Session

router = APIRouter()


def get_task_manager(db: Session = Depends(get_db_session)) -> TaskManager:
    """获取任务管理器实例"""
    return TaskManager(db)


class ReportGenerationRequest(BaseModel):
    """报告生成请求模型"""
    task_id: str
    format_type: Optional[str] = "markdown"


@router.post("/generate")
async def generate_report(
    request: ReportGenerationRequest,
    task_manager: TaskManager = Depends(get_task_manager),
    current_user_id: str = Depends(get_current_user_id)
):
    """生成任务报告"""
    try:
        # 验证任务存在且属于当前用户
        task = await task_manager.get_task_by_id(uuid.UUID(request.task_id), current_user_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # 获取分析结果
        from app.models.task import AnalysisResult
        analysis_result = task_manager.db.query(AnalysisResult).filter(
            AnalysisResult.task_id == uuid.UUID(request.task_id)
        ).first()
        
        if not analysis_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis result not found for this task"
            )
        
        # 生成报告
        report = await report_service.generate_insight_report(
            task_id=request.task_id,
            product_name=task.product_name,
            analysis_result=analysis_result,
            raw_data=None  # 可以从数据库获取原始数据
        )
        
        return {
            "status": "success",
            "data": report
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )


@router.get("/{task_id}")
async def get_report(
    task_id: str,
    format_type: str = Query("markdown", description="报告格式 (markdown, json)"),
    task_manager: TaskManager = Depends(get_task_manager),
    current_user_id: str = Depends(get_current_user_id)
):
    """获取任务报告"""
    try:
        # 验证任务存在且属于当前用户
        task = await task_manager.get_task_by_id(uuid.UUID(task_id), current_user_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # 检查任务是否已完成
        from app.models.task import TaskStatus
        if task.status != TaskStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task is not completed yet"
            )
        
        # 获取分析结果
        from app.models.task import AnalysisResult
        analysis_result = task_manager.db.query(AnalysisResult).filter(
            AnalysisResult.task_id == uuid.UUID(task_id)
        ).first()
        
        if not analysis_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis result not found"
            )
        
        # 生成报告
        report = await report_service.generate_insight_report(
            task_id=task_id,
            product_name=task.product_name,
            analysis_result=analysis_result
        )
        
        # 根据请求格式返回相应内容
        if format_type == "markdown":
            return {
                "status": "success",
                "data": report.get("main_report", {})
            }
        elif format_type == "json":
            return {
                "status": "success",
                "data": report.get("alternative_formats", {}).get("json", {})
            }
        else:
            return {
                "status": "success",
                "data": report
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get report: {str(e)}"
        )


@router.post("/{task_id}/export")
async def export_report(
    task_id: str,
    format_type: str = Query("markdown", description="导出格式 (markdown, json)"),
    task_manager: TaskManager = Depends(get_task_manager),
    current_user_id: str = Depends(get_current_user_id)
):
    """导出任务报告"""
    try:
        # 验证任务存在且属于当前用户
        task = await task_manager.get_task_by_id(uuid.UUID(task_id), current_user_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # 获取分析结果
        from app.models.task import AnalysisResult
        analysis_result = task_manager.db.query(AnalysisResult).filter(
            AnalysisResult.task_id == uuid.UUID(task_id)
        ).first()
        
        if not analysis_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis result not found"
            )
        
        # 生成报告
        report = await report_service.generate_insight_report(
            task_id=task_id,
            product_name=task.product_name,
            analysis_result=analysis_result
        )
        
        # 导出报告
        export_result = await report_service.export_report(report, format_type)
        
        return {
            "status": "success",
            "data": export_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export report: {str(e)}"
        )


@router.get("/{task_id}/summary")
async def get_report_summary(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager),
    current_user_id: str = Depends(get_current_user_id)
):
    """获取报告摘要"""
    try:
        # 验证任务存在且属于当前用户
        task = await task_manager.get_task_by_id(uuid.UUID(task_id), current_user_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # 获取分析结果
        from app.models.task import AnalysisResult
        analysis_result = task_manager.db.query(AnalysisResult).filter(
            AnalysisResult.task_id == uuid.UUID(task_id)
        ).first()
        
        if not analysis_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis result not found"
            )
        
        # 生成报告
        report = await report_service.generate_insight_report(
            task_id=task_id,
            product_name=task.product_name,
            analysis_result=analysis_result
        )
        
        # 返回执行摘要
        executive_summary = report.get("alternative_formats", {}).get("executive_summary", {})
        
        return {
            "status": "success",
            "data": executive_summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get report summary: {str(e)}"
        )


@router.get("/templates/available")
async def get_available_templates(
    current_user_id: str = Depends(get_current_user_id)
):
    """获取可用的报告模板"""
    try:
        templates = {
            "markdown_report": {
                "name": "Markdown报告",
                "description": "结构化的Markdown格式报告，包含完整的分析内容",
                "format": "markdown",
                "sections": [
                    "报告概览", "执行摘要", "情感分析", 
                    "热门话题", "功能需求分析", "关键洞察", "建议与行动项"
                ]
            },
            "executive_summary": {
                "name": "执行摘要",
                "description": "简洁的高层次摘要，适合管理层查看",
                "format": "json",
                "sections": ["整体情感", "关键要点", "建议"]
            },
            "detailed_analysis": {
                "name": "详细分析",
                "description": "包含所有分析数据的详细报告",
                "format": "json",
                "sections": ["数据收集", "情感分析", "话题分析", "功能需求", "关键洞察"]
            },
            "json_report": {
                "name": "JSON数据报告",
                "description": "原始JSON格式的完整数据报告",
                "format": "json",
                "sections": ["所有原始数据"]
            }
        }
        
        return {
            "status": "success",
            "data": {
                "templates": templates,
                "total_templates": len(templates),
                "supported_formats": ["markdown", "json"]
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get available templates: {str(e)}"
        )