"""
视频下载器 — yt-dlp 封装
支持 YouTube / B站 / 抖音等多平台
"""

import subprocess
import uuid
from pathlib import Path

DATA_DIR = Path("data")
VIDEO_DIR = DATA_DIR / "videos"
AUDIO_DIR = DATA_DIR / "audio"
FRAMES_DIR = DATA_DIR / "frames"

for d in [VIDEO_DIR, AUDIO_DIR, FRAMES_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def download_video(url: str) -> dict:
    """
    下载视频，返回元信息。
    返回: {video_id, path, title, duration, width, height, fps}
    """
    video_id = uuid.uuid4().hex[:12]
    output_template = str(VIDEO_DIR / f"{video_id}.%(ext)s")

    # 第一步：获取视频信息（不下载）
    cmd_info = [
        "yt-dlp", "--dump-json", "--no-playlist",
        "-f", "best[height<=1080]",
        url,
    ]
    result = subprocess.run(cmd_info, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp 解析失败: {result.stderr[:500]}")

    import json
    info = json.loads(result.stdout.splitlines()[-1])

    # 第二步：下载
    cmd_dl = [
        "yt-dlp", "--no-playlist",
        "-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "-o", output_template,
        "--merge-output-format", "mp4",
        url,
    ]
    subprocess.run(cmd_dl, capture_output=True, text=True, timeout=120)

    # 找到输出文件
    video_path = None
    for ext in ["mp4", "mkv", "webm"]:
        candidate = VIDEO_DIR / f"{video_id}.{ext}"
        if candidate.exists():
            video_path = candidate
            break

    if not video_path:
        raise RuntimeError("下载后未找到视频文件")

    return {
        "video_id": video_id,
        "path": str(video_path),
        "title": info.get("title", "未知标题"),
        "duration": info.get("duration", 0),
        "width": info.get("width", 0),
        "height": info.get("height", 0),
        "fps": info.get("fps", 0),
    }
