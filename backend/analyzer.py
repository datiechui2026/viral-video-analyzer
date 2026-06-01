"""
爆款分析引擎 — 核心价值模块
分析视频结构、钩子、情绪曲线，输出可复制模板
"""

import json
import os
import httpx

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

ANALYSIS_SYSTEM = """你是一位顶级短视频爆款分析师，曾帮数百个账号从0做到百万粉。
你需要分析一段视频的逐句文本和时间轴，输出一份专业的「爆款拆解报告」。

## 分析维度

1. **黄金前3秒钩子**：用了什么手法？（反常识/悬念/痛点/数字/情绪宣泄），为什么会让人停下滑动？
2. **结构拆解**：按时间轴分段，每段标注「功能」（钩子/痛点展开/解决方案/证据展示/CTA号召），并给出该段的话术技巧
3. **情绪曲线**：标注每个节点的情绪值（1-10），画出起承转合
4. **BGM/音效使用**：根据文本推测应该配什么类型音乐（如果没有音频信息则给出建议）
5. **字幕/视觉风格**：适合什么字体、颜色、出现节奏
6. **爆款公式提炼**：用一句话总结这类视频的底层逻辑

## 输出要求

严格输出 JSON，不要任何额外文字：

{
  "hook_analysis": {
    "type": "反常识/悬念/痛点/数字/情绪宣泄/对比",
    "text": "具体的钩子文案",
    "why_it_works": "为什么这个钩子有效"
    "score": 8
  },
  "structure": [
    {
      "start_seconds": 0,
      "end_seconds": 3,
      "function": "钩子",
      "content_summary": "这段讲了什么",
      "technique": "用了什么话术技巧"
    }
  ],
  "emotional_curve": [
    {"time_label": "0s 开头", "emotion": "好奇", "intensity": 7},
    {"time_label": "5s 展开", "emotion": "焦虑", "intensity": 6}
  ],
  "bgm_recommendation": "推荐的 BGM 风格和节奏变化",
  "subtitle_style": "推荐的字幕样式（字体/颜色/大小/出现方式）",
  "viral_formula": "一句话爆款公式",
  "copyable_script_template": "可以直接套用的脚本模板，用 ___ 标注可替换部分"
}"""


async def analyze_video(
    duration: float,
    resolution: str,
    transcription: list[dict],  # [{start, end, text}]
    keyframe_count: int,
    video_title: str = "",
) -> dict:
    """
    分析视频并返回结构化报告。
    
    transcription: whisper 输出，每段包含 start/end/text
    """
    # 构建逐句文本（带时间戳）
    lines = []
    full_text = ""
    for seg in transcription:
        start = seg.get("start", 0)
        end = seg.get("end", 0)
        text = seg.get("text", "").strip()
        if text:
            lines.append(f"[{start:.1f}s-{end:.1f}s] {text}")
            full_text += text

    transcript_block = "\n".join(lines)

    user_prompt = f"""请分析以下短视频：

## 视频基本信息
- 时长：{duration:.0f} 秒
- 分辨率：{resolution}
- 标题：{video_title or "未提供"}
- 关键帧数：{keyframe_count}

## 逐句文本（带时间轴）
{transcript_block}

请输出 JSON 分析报告。"""

    # 尝试调用 DeepSeek
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    
    if not api_key:
        print("[analyzer] No DEEPSEEK_API_KEY set, using fallback")
        return _fallback_analysis(duration, transcription)

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek/deepseek-v4-pro",
                    "messages": [
                        {"role": "system", "content": ANALYSIS_SYSTEM},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.7,
                },
            )
            if r.status_code == 200:
                content = r.json()["choices"][0]["message"]["content"]
                # 提取 JSON（可能被 ```json 包裹）
                content = content.strip()
                if content.startswith("```"):
                    # 移除 markdown 代码块
                    lines = content.split("\n")
                    content = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
                return json.loads(content)
    except Exception as e:
        print(f"[analyzer] DeepSeek error: {e}")

    # Fallback: 基于规则的模板分析
    return _fallback_analysis(duration, transcription)


def _fallback_analysis(duration: float, transcription: list[dict]) -> dict:
    """无 API 时的规则分析"""
    text = " ".join(s.get("text", "") for s in transcription)
    word_count = len(text)
    seg_count = len(transcription)

    return {
        "hook_analysis": {
            "type": "待分析",
            "text": transcription[0].get("text", "") if transcription else "",
            "why_it_works": "需接入 DeepSeek API 获取详细分析",
            "score": 0,
        },
        "structure": [
            {
                "start_seconds": 0,
                "end_seconds": min(3, duration),
                "function": "开头",
                "content_summary": transcription[0].get("text", "")[:80] if transcription else "",
                "technique": "待分析",
            }
        ],
        "emotional_curve": [
            {"time_label": "0s", "emotion": "未知", "intensity": 5},
            {"time_label": f"{duration:.0f}s", "emotion": "未知", "intensity": 5},
        ],
        "bgm_recommendation": f"建议根据 {seg_count} 段内容的情感变化搭配 BGM（需 API 详细分析）",
        "subtitle_style": "建议使用黄色大字描边，每句 1-2 秒切换（需 API 详细分析）",
        "viral_formula": f"此视频时长 {duration:.0f} 秒，共 {seg_count} 个段落，{word_count} 字（需 API 深度拆解）",
        "copyable_script_template": "___[你的钩子]___\n\n___[痛点展开]___\n\n___[解决方案]___\n\n___[CTA 号召关注]___",
    }
