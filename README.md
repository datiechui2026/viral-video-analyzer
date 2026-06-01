# AI 爆款视频分析

粘贴视频链接 → AI 拆解爆款公式 → 一键生成同款拍摄脚本

## 技术栈

- **后端**: Python FastAPI + yt-dlp + Whisper + DeepSeek API
- **前端**: React + Vite + TypeScript
- **部署**: nginx + systemd (Tencent Cloud CVM)

## 功能

1. 粘贴任意平台视频链接（抖音/小红书/YouTube/B站）
2. 自动下载视频 + 语音转文字
3. AI 分析爆款公式：
   - 黄金前 3 秒钩子
   - 逐段结构拆解
   - 情绪曲线
   - BGM / 字幕推荐
   - 可复制脚本模板

## 部署

```bash
# 后端
sudo systemctl restart viral-video-analyzer

# 前端
cd frontend && npm run build
sudo systemctl reload nginx
```

在线地址: http://124.221.85.247:3789
