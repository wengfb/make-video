"""
FastAPI Web应用入口
科普视频自动化制作系统 - Web界面
"""
import sys
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入API路由
from web.api import topics, scripts, videos, materials, history
from web.api import tts_and_subtitles, config

# 创建FastAPI应用
app = FastAPI(
    title="科普视频自动化制作系统",
    description="AI驱动的端到端视频生产平台",
    version="5.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置静态文件
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 配置素材文件访问
materials_dir = project_root / "materials"
if materials_dir.exists():
    app.mount("/materials", StaticFiles(directory=str(materials_dir)), name="materials")

# 配置输出文件访问
output_dir = project_root / "output"
if output_dir.exists():
    app.mount("/output", StaticFiles(directory=str(output_dir)), name="output")

# 配置模板
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))

# 注册API路由
app.include_router(topics.router)
app.include_router(scripts.router)
app.include_router(videos.router)
app.include_router(materials.router)
app.include_router(history.router)
app.include_router(tts_and_subtitles.tts_router)
app.include_router(tts_and_subtitles.subtitle_router)
app.include_router(config.router)


# ==================== WebSocket端点 ====================

from web.websocket.progress_handler import get_progress_handler

@app.websocket("/ws/progress/{task_id}")
async def progress_websocket(websocket: WebSocket, task_id: str):
    """
    WebSocket进度推送端点

    客户端连接此端点接收任务进度更新
    """
    progress_handler = get_progress_handler()
    await progress_handler.handle_progress_websocket(websocket, task_id)


# ==================== 健康检查 ====================

@app.get("/health", tags=["系统"])
async def health_check():
    """
    健康检查端点
    用于监控服务是否正常运行
    """
    return {
        "status": "healthy",
        "service": "科普视频自动化制作系统",
        "version": "5.0.0"
    }


# ==================== 首页 ====================

@app.get("/", response_class=HTMLResponse, tags=["页面"])
async def index(request: Request):
    """
    首页/仪表盘
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/topics", response_class=HTMLResponse, tags=["页面"])
async def topics_page(request: Request):
    """
    主题生成页面
    """
    return templates.TemplateResponse("topics.html", {"request": request})


@app.get("/scripts", response_class=HTMLResponse, tags=["页面"])
async def scripts_page(request: Request):
    """
    脚本生成页面
    """
    return templates.TemplateResponse("scripts.html", {"request": request})


@app.get("/materials", response_class=HTMLResponse, tags=["页面"])
async def materials_page(request: Request):
    """
    素材管理页面
    """
    return templates.TemplateResponse("materials.html", {"request": request})


@app.get("/videos", response_class=HTMLResponse, tags=["页面"])
async def videos_page(request: Request):
    """
    视频合成页面
    """
    return templates.TemplateResponse("videos.html", {"request": request})


@app.get("/history", response_class=HTMLResponse, tags=["页面"])
async def history_page(request: Request):
    """
    历史记录页面
    """
    return templates.TemplateResponse("history.html", {"request": request})


@app.get("/config", response_class=HTMLResponse, tags=["页面"])
async def config_page(request: Request):
    """
    系统配置页面
    """
    return templates.TemplateResponse("config.html", {"request": request})


@app.get("/test-styles", response_class=HTMLResponse, tags=["页面"])
async def test_styles_page(request: Request):
    """
    样式测试页面
    """
    return templates.TemplateResponse("test_styles.html", {"request": request})


# ==================== API路由 ====================
# 注意：这些路由将在后续步骤中实现
# - /api/topics/*      - 主题相关API
# - /api/scripts/*     - 脚本相关API
# - /api/materials/*   - 素材相关API
# - /api/videos/*      - 视频相关API
# - /api/tts/*         - TTS相关API
# - /api/subtitles/*   - 字幕相关API
# - /ws/progress/*     - WebSocket进度推送


# ==================== 启动事件 ====================

@app.on_event("startup")
async def startup_event():
    """
    应用启动时执行
    """
    print("=" * 60)
    print("🚀 科普视频自动化制作系统 - Web界面")
    print("=" * 60)
    print(f"📖 版本: 5.0.0")
    print(f"🌐 API文档: http://localhost:8000/api/docs")
    print(f"🏠 首页: http://localhost:8000/")
    print(f"⚙️  配置: http://localhost:8000/config")
    print("=" * 60)

    # 确保配置备份目录存在
    backup_dir = project_root / "config" / "backups"
    backup_dir.mkdir(exist_ok=True)
    print(f"✅ 配置备份目录: {backup_dir}")

    # 设置配置文件安全权限
    settings_file = project_root / "config" / "settings.json"
    if settings_file.exists():
        import os
        os.chmod(settings_file, 0o600)  # 仅所有者可读写
        print("✅ 配置文件权限已设置 (600)")

    # 验证项目配置
    try:
        from web.utils.module_loader import get_module_loader

        loader = get_module_loader()
        print("✅ 模块加载器初始化成功")

        # 测试加载主题生成器
        TopicGenerator = loader.load_topic_generator()
        print("✅ 主题生成器加载成功")

    except Exception as e:
        print(f"❌ 启动检查失败: {e}")
        print("⚠️  请确保项目已正确初始化")


@app.on_event("shutdown")
async def shutdown_event():
    """
    应用关闭时执行
    """
    print("=" * 60)
    print("👋 科普视频自动化制作系统 - 已关闭")
    print("=" * 60)


# ==================== 主函数 ====================

if __name__ == "__main__":
    import uvicorn

    # 开发服务器配置
    uvicorn.run(
        "web.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 自动重载（开发模式）
        log_level="info"
    )
