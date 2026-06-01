"""
语音转录器 — ffmpeg 提取音频 + Whisper 转文字
"""

import subprocess
from pathlib import Path

AUDIO_DIR = Path("data/audio")


def extract_audio(video_path: str) -> str:
    """从视频提取音频为 16kHz mono WAV"""
    audio_path = AUDIO_DIR / f"{Path(video_path).stem}.wav"
    audio_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",                # 不要视频流
        "-acodec", "pcm_s16le",
        "-ar", "16000",       # 16kHz
        "-ac", "1",           # mono
        str(audio_path),
    ]
    subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=True)
    return str(audio_path)


def transcribe_audio(audio_path: str) -> list[dict]:
    """
    Whisper 语音转文字，返回带时间轴的段落列表。
    每段: {start: float, end: float, text: str}
    """
    import whisper

    # 使用 small 模型（平衡速度和准确度）
    model = whisper.load_model("small")
    result = model.transcribe(audio_path, language="zh", verbose=False)

    segments = []
    for seg in result.get("segments", []):
        segments.append({
            "start": round(seg["start"], 1),
            "end": round(seg["end"], 1),
            "text": seg["text"].strip(),
        })
    return segments


def extract_keyframes(video_path: str, count: int = 5) -> list[dict]:
    """提取关键帧（场景检测）"""
    frames_dir = Path("data/frames") / Path(video_path).stem
    frames_dir.mkdir(parents=True, exist_ok=True)

    # 先尝试场景检测
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"select='gt(scene\\,0.3)',scale=640:-1",
        "-vsync", "vfr",
        "-frames:v", str(count),
        f"{frames_dir}/frame_%03d.jpg",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    # 如果场景检测没产出足够帧，回退到均匀采样
    actual = list(frames_dir.glob("*.jpg"))
    if len(actual) < count:
        # 清理
        for f in actual:
            f.unlink()
        cmd2 = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", f"fps=1/{max(1, 10/count)},scale=640:-1",
            f"{frames_dir}/frame_%03d.jpg",
        ]
        subprocess.run(cmd2, capture_output=True, text=True, timeout=60)

    actual = sorted(frames_dir.glob("frame_*.jpg"))
    result = []
    for f in actual:
        result.append({
            "filename": f"{Path(video_path).stem}/{f.name}",
            "size_kb": round(f.stat().st_size / 1024, 1),
        })
    return result
