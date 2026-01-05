"""
配置API路由
提供配置读取、更新、验证、测试等功能
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from web.services.config_service import get_config_service


# 创建路由器
router = APIRouter(prefix="/api/config", tags=["配置"])


# ==================== 数据模型 ====================


class SettingsUpdateRequest(BaseModel):
    """Settings配置更新请求"""
    section: str = Field(..., description="配置区块（如：ai/tts/video等）")
    updates: Dict[str, Any] = Field(..., description="要更新的配置键值对")
    create_backup: bool = Field(True, description="是否创建备份")


class TemplatesUpdateRequest(BaseModel):
    """Templates配置更新请求"""
    section: str = Field(..., description="配置区块（如：script_templates/prompt_templates等）")
    updates: Dict[str, Any] = Field(..., description="要更新的配置键值对")
    create_backup: bool = Field(True, description="是否创建备份")


class APIKeyTestRequest(BaseModel):
    """API密钥测试请求"""
    provider: str = Field(..., description="提供商（openai/glm/anthropic）")
    api_key: str = Field(..., description="API密钥")
    base_url: Optional[str] = Field(None, description="API地址")
    model: Optional[str] = Field(None, description="模型名称")


class ImageAPITestRequest(BaseModel):
    """图片API测试请求"""
    provider: str = Field(..., description="提供商（dalle/cogview/sd）")
    api_key: str = Field(..., description="API密钥")


class ConfigValidationRequest(BaseModel):
    """配置验证请求"""
    config_type: str = Field(..., description="配置类型（settings/templates）")
    config: Dict[str, Any] = Field(..., description="要验证的配置")


class RestoreBackupRequest(BaseModel):
    """恢复备份请求"""
    config_type: str = Field(..., description="配置类型（settings/templates）")
    backup_id: str = Field(..., description="备份ID")


class ConfigResponse(BaseModel):
    """配置响应"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class ValidationResponse(BaseModel):
    """验证响应"""
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []


class APITestResponse(BaseModel):
    """API测试响应"""
    success: bool
    message: str


class BackupListResponse(BaseModel):
    """备份列表响应"""
    backups: List[Dict[str, Any]]


class AuditLogResponse(BaseModel):
    """审计日志响应"""
    logs: List[Dict[str, Any]]


# ==================== API端点 ====================


@router.get("/", response_model=ConfigResponse)
async def get_all_configs():
    """
    获取所有配置

    Returns:
        包含settings和templates的完整配置
    """
    try:
        service = get_config_service()
        configs = service.get_all_configs()

        return ConfigResponse(
            success=True,
            message="配置获取成功",
            data=configs
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/settings", response_model=ConfigResponse)
async def get_settings():
    """
    获取settings.json配置

    Returns:
        settings.json配置内容
    """
    try:
        service = get_config_service()
        settings = service.get_settings()

        return ConfigResponse(
            success=True,
            message="Settings配置获取成功",
            data=settings
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates", response_model=ConfigResponse)
async def get_templates():
    """
    获取templates.json配置

    Returns:
        templates.json配置内容
    """
    try:
        service = get_config_service()
        templates = service.get_templates()

        return ConfigResponse(
            success=True,
            message="Templates配置获取成功",
            data=templates
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings", response_model=ConfigResponse)
async def update_settings(request: SettingsUpdateRequest):
    """
    更新settings.json配置

    Args:
        request: 配置更新请求

    Returns:
        更新结果
    """
    try:
        service = get_config_service()

        # 构建更新字典
        updates = {request.section: request.updates}

        # 更新配置
        success, message = service.update_settings(updates, request.create_backup)

        if success:
            return ConfigResponse(
                success=True,
                message=message
            )
        else:
            raise HTTPException(status_code=400, detail=message)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/templates", response_model=ConfigResponse)
async def update_templates(request: TemplatesUpdateRequest):
    """
    更新templates.json配置

    Args:
        request: 配置更新请求

    Returns:
        更新结果
    """
    try:
        service = get_config_service()

        # 构建更新字典
        updates = {request.section: request.updates}

        # 更新配置
        success, message = service.update_templates(updates, request.create_backup)

        if success:
            return ConfigResponse(
                success=True,
                message=message
            )
        else:
            raise HTTPException(status_code=400, detail=message)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate", response_model=ValidationResponse)
async def validate_config(request: ConfigValidationRequest):
    """
    验证配置

    Args:
        request: 配置验证请求

    Returns:
        验证结果
    """
    try:
        service = get_config_service()

        if request.config_type == "settings":
            valid, errors, warnings = service.validate_settings(request.config)
        elif request.config_type == "templates":
            valid, errors, warnings = service.validate_templates(request.config)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的配置类型: {request.config_type}")

        return ValidationResponse(
            valid=valid,
            errors=errors,
            warnings=warnings
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-api", response_model=APITestResponse)
async def test_api_key(request: APIKeyTestRequest):
    """
    测试AI API密钥

    Args:
        request: API测试请求

    Returns:
        测试结果
    """
    try:
        service = get_config_service()

        success, message = await service.test_ai_api(
            provider=request.provider,
            api_key=request.api_key,
            base_url=request.base_url or "",
            model=request.model or ""
        )

        return APITestResponse(
            success=success,
            message=message
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-image-api", response_model=APITestResponse)
async def test_image_api(request: ImageAPITestRequest):
    """
    测试图片生成API密钥

    Args:
        request: 图片API测试请求

    Returns:
        测试结果
    """
    try:
        service = get_config_service()

        success, message = await service.test_image_api(
            provider=request.provider,
            api_key=request.api_key
        )

        return APITestResponse(
            success=success,
            message=message
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backup", response_model=ConfigResponse)
async def create_backup(config_type: str = "settings"):
    """
    手动创建配置备份

    Args:
        config_type: 配置类型（settings/templates）

    Returns:
        备份结果
    """
    try:
        service = get_config_service()

        if config_type not in ["settings", "templates"]:
            raise HTTPException(status_code=400, detail="config_type必须是'settings'或'templates'")

        backup_id = service.backup_config(config_type)

        return ConfigResponse(
            success=True,
            message=f"备份已创建: {backup_id}",
            data={"backup_id": backup_id}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backups/{config_type}", response_model=BackupListResponse)
async def get_backup_history(config_type: str, limit: int = 10):
    """
    获取配置备份历史

    Args:
        config_type: 配置类型（settings/templates）
        limit: 返回数量限制

    Returns:
        备份列表
    """
    try:
        service = get_config_service()

        if config_type not in ["settings", "templates"]:
            raise HTTPException(status_code=400, detail="config_type必须是'settings'或'templates'")

        backups = service.get_backup_history(config_type, limit)

        return BackupListResponse(backups=backups)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restore", response_model=ConfigResponse)
async def restore_backup(request: RestoreBackupRequest):
    """
    恢复配置备份

    Args:
        request: 恢复备份请求

    Returns:
        恢复结果
    """
    try:
        service = get_config_service()

        success, message = service.restore_config(
            config_type=request.config_type,
            backup_id=request.backup_id
        )

        if success:
            return ConfigResponse(
                success=True,
                message=message
            )
        else:
            raise HTTPException(status_code=400, detail=message)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit-logs", response_model=AuditLogResponse)
async def get_audit_logs(limit: int = 50):
    """
    获取审计日志

    Args:
        limit: 返回数量限制

    Returns:
        审计日志列表
    """
    try:
        service = get_config_service()
        logs = service.get_audit_logs(limit)

        return AuditLogResponse(logs=logs)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
