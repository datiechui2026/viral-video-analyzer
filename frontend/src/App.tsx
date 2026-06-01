import { useState, useRef } from "react";

/* ---------- types ---------- */

interface AnalysisResult {
  video_id: string;
  title: string;
  duration: number;
  resolution: string;
  frames: { filename: string; size_kb: number }[];
  transcription: { start: number; end: number; text: string }[];
  transcription_full_length: number;
  analysis: {
    hook_analysis: { type: string; text: string; why_it_works: string; score: number };
    structure: { start_seconds: number; end_seconds: number; function: string; content_summary: string; technique: string }[];
    emotional_curve: { time_label: string; emotion: string; intensity: number }[];
    bgm_recommendation: string;
    subtitle_style: string;
    viral_formula: string;
    copyable_script_template: string;
  };
}

type Stage = "idle" | "loading" | "done" | "error";

/* ---------- api ---------- */

async function analyze(url: string): Promise<AnalysisResult> {
  const fd = new FormData();
  fd.append("url", url);
  const r = await fetch("/api/analyze", { method: "POST", body: fd });
  if (!r.ok) throw new Error((await r.json()).detail ?? "分析失败");
  return r.json();
}

/* ---------- components ---------- */

export default function App() {
  const [stage, setStage] = useState<Stage>("idle");
  const [url, setUrl] = useState("");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState("");

  const run = async () => {
    if (!url.trim()) return;
    setStage("loading");
    setError("");
    try {
      const r = await analyze(url.trim());
      setResult(r);
      setStage("done");
    } catch (e: any) {
      setError(e.message);
      setStage("error");
    }
  };

  return (
    <div className="app">
      <header className="hero">
        <h1>🔍 AI 爆款视频分析</h1>
        <p>粘贴视频链接 → AI 拆解爆款公式 → 一键生成同款脚本</p>
      </header>

      {/* input */}
      <section className="input-row">
        <input
          className="url-input"
          placeholder="粘贴抖音/小红书/YouTube/B站视频链接…"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && run()}
        />
        <button className="btn-analyze" onClick={run} disabled={stage === "loading"}>
          {stage === "loading" ? "分析中…" : "开始分析"}
        </button>
      </section>

      {error && <div className="error-msg">❌ {error}</div>}

      {/* loading */}
      {stage === "loading" && (
        <section className="loading-box">
          <div className="spinner" />
          <div className="loading-steps">
            <p className="step active">📥 下载视频…</p>
            <p className="step">🎙️ 语音转文字…</p>
            <p className="step">🧠 AI 拆解爆款公式…</p>
          </div>
        </section>
      )}

      {/* results */}
      {stage === "done" && result && <AnalysisReport result={result} />}

      {/* reset */}
      {stage === "done" && (
        <button className="btn-reset" onClick={() => { setStage("idle"); setResult(null); setUrl(""); }}>
          分析新视频
        </button>
      )}
    </div>
  );
}

/* ---------- analysis report ---------- */

function AnalysisReport({ result }: { result: AnalysisResult }) {
  const a = result.analysis;
  const copy = (text: string) => navigator.clipboard.writeText(text);

  return (
    <section className="report">
      {/* meta bar */}
      <div className="meta-bar">
        <span>📹 {result.title}</span>
        <span>⏱️ {Math.floor(result.duration)}s</span>
        <span>📐 {result.resolution}</span>
      </div>

      {/* 1. viral formula - most important */}
      <Card icon="🎯" title="爆款公式" highlight>
        <p className="formula-text">{a.viral_formula}</p>
      </Card>

      {/* 2. hook analysis */}
      <Card icon="🪝" title="黄金前3秒 · 钩子分析">
        <div className="hook-badge">{a.hook_analysis.type}</div>
        <p className="hook-text">"{a.hook_analysis.text}"</p>
        <p className="hook-why">{a.hook_analysis.why_it_works}</p>
        <ScoreBar score={a.hook_analysis.score} />
      </Card>

      {/* 3. structure */}
      <Card icon="📐" title="结构拆解">
        <div className="timeline">
          {a.structure.map((s, i) => (
            <div key={i} className="timeline-item">
              <div className="timeline-time">{s.start_seconds}s - {s.end_seconds}s</div>
              <div className="timeline-content">
                <span className="timeline-func">{s.function}</span>
                <p className="timeline-summary">{s.content_summary}</p>
                <span className="timeline-tech">{s.technique}</span>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* 4. emotional curve */}
      <Card icon="📈" title="情绪曲线">
        <div className="emotion-bar">
          {a.emotional_curve.map((e, i) => (
            <div key={i} className="emotion-point">
              <div className="emotion-value" style={{ height: `${e.intensity * 10}%` }}>
                <span>{e.intensity}</span>
              </div>
              <span className="emotion-label">{e.emotion}</span>
              <span className="emotion-time">{e.time_label}</span>
            </div>
          ))}
        </div>
      </Card>

      {/* 5. BGM */}
      <Card icon="🎵" title="BGM 推荐">
        <p>{a.bgm_recommendation}</p>
      </Card>

      {/* 6. subtitle style */}
      <Card icon="✏️" title="字幕样式">
        <p>{a.subtitle_style}</p>
      </Card>

      {/* 7. script template */}
      <Card icon="📝" title="可复制脚本模板">
        <pre className="script-template">{a.copyable_script_template}</pre>
        <button className="btn-copy" onClick={() => copy(a.copyable_script_template)}>
          📋 复制脚本
        </button>
      </Card>

      {/* 8. transcription preview */}
      {result.transcription.length > 0 && (
        <Card icon="🗣️" title={`逐句文本（${result.transcription_full_length} 句）`}>
          <div className="transcript">
            {result.transcription.map((t, i) => (
              <p key={i} className="transcript-line">
                <span className="ts">{t.start}s</span> {t.text}
              </p>
            ))}
          </div>
        </Card>
      )}
    </section>
  );
}

function Card({
  icon, title, children, highlight,
}: {
  icon: string; title: string; children: React.ReactNode; highlight?: boolean;
}) {
  return (
    <div className={`card ${highlight ? "card-highlight" : ""}`}>
      <h3>{icon} {title}</h3>
      <div className="card-body">{children}</div>
    </div>
  );
}

function ScoreBar({ score }: { score: number }) {
  return (
    <div className="score-bar">
      <span className="score-label">钩子力度</span>
      <div className="score-track">
        <div className="score-fill" style={{ width: `${score * 10}%` }} />
      </div>
      <span className="score-value">{score}/10</span>
    </div>
  );
}
