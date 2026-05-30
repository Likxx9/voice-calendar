"""
Health Check API Router
健康检查API路由
"""
from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "voice-calendar-api"
    }


@router.get("/version")
async def get_version():
    """获取版本信息"""
    return {
        "version": "1.0.0",
        "build": "2026-05-30",
        "python": "3.11+"
    }
