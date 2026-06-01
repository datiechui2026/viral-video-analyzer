"""
API 路由
"""

import os
import shutil
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from downloader import download_video
from transcriber import extract_audio, transcribe_audio, extract_keyframes
from analyzer import analyze_video

router = APIRouter(prefix="/api")


@router.get("/health")
async def health():
    return {"status": "healthy"}


@router.post("/analyze")
async def analyze(url: str = Form(...)):
    """
    分析视频：下载 → 语音转文字 → AI 爆款拆解

    入参: url - 视频链接（YouTube/B站/抖音等）
    返回: 结构化爆款分析报告
    """
    if not url.strip():
        raise HTTPException(400, "请输入视频链接")

    # 1) 下载视频
    try:
        video = download_video(url.strip())
    except RuntimeError as e:
        raise HTTPException(400, f"视频下载失败: {str(e)[:200]}")
    except Exception as e:
        raise HTTPException(500, f"下载异常: {str(e)[:200]}")

    # 2) 提取音频 + 语音转文字
    transcription = []
    try:
        audio_path = extract_audio(video["path"])
        transcription = transcribe_audio(audio_path)
    except Exception as e:
        print(f"[routes] 转录失败: {e}，跳过文字分析")

    # 3) 提取关键帧
    frames = []
    try:
        frames = extract_keyframes(video["path"], count=5)
    except Exception as e:
        print(f"[routes] 关键帧提取失败: {e}")

    # 4) AI 分析
    resolution = f"{video.get('width', 0)}x{video.get('height', 0)}"
    analysis = await analyze_video(
        duration=video["duration"],
        resolution=resolution,
        transcription=transcription,
        keyframe_count=len(frames),
        video_title=video.get("title", ""),
    )

    return {
        "video_id": video["video_id"],
        "title": video["title"],
        "duration": video["duration"],
        "resolution": resolution,
        "frames": frames,
        "transcription": transcription[:20],  # 前 20 句预览
        "transcription_full_length": len(transcription),
        "analysis": analysis,
    }


@router.get("/frames/{path:path}")
async def get_frame(path: str):
    """返回关键帧图片"""
    full = Path("data/frames") / path
    if not full.exists():
        raise HTTPException(404, "图片不存在")
    return FileResponse(str(full), media_type="image/jpeg")


@router.post("/analyze-local")
async def analyze_local(url: str = Form(...)):
    """
    轻量版：只用 LLM 分析转录文本，不下载视频。
    适合快速测试分析引擎。
    """
    from analyzer import analyze_video

    analysis = await analyze_video(
        duration=60,
        resolution="1920x1080",
        transcription=[{"start": 0, "end": 5, "text": "示例文本（请在 /analyze 接口传入真实视频链接）"}],
        keyframe_count=3,
        video_title="示例标题",
    )
    return {
        "mode": "text-only",
        "analysis": analysis,
    }
