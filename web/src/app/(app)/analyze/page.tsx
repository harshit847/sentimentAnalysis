"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, uploadFace } from "@/lib/api";
import type { FaceResult, TextResult, VoiceResult } from "@/lib/types";

type Tab = "text" | "face" | "voice";

export default function AnalyzePage() {
  const [tab, setTab] = useState<Tab>("text");
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [textResult, setTextResult] = useState<TextResult | null>(null);
  const [faceResult, setFaceResult] = useState<FaceResult | null>(null);
  const [voiceResult, setVoiceResult] = useState<VoiceResult | null>(null);

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const runText = async () => {
    setLoading(true);
    setError(null);
    setTextResult(null);
    try {
      const res = await api<TextResult>("/analyze/text", {
        method: "POST",
        json: { text: text.trim() },
      });
      setTextResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const captureFace = async () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;
    setLoading(true);
    setError(null);
    setFaceResult(null);
    try {
      const ctx = canvas.getContext("2d");
      if (!ctx) throw new Error("Canvas not supported");
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      ctx.drawImage(video, 0, 0);
      const blob = await new Promise<Blob | null>((resolve) =>
        canvas.toBlob(resolve, "image/jpeg", 0.92),
      );
      if (!blob) throw new Error("Could not capture frame");
      const res = await uploadFace(blob, "frame.jpg");
      setFaceResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Face analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const [listening, setListening] = useState(false);
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return;
    const r = new SR();
    r.lang = "en-US";
    r.interimResults = false;
    r.maxAlternatives = 1;
    r.onresult = (ev: SpeechRecognitionEvent) => {
      const t = ev.results[0]?.[0]?.transcript ?? "";
      setText(t);
      setListening(false);
    };
    r.onerror = () => setListening(false);
    r.onend = () => setListening(false);
    recognitionRef.current = r;
  }, []);

  const toggleListen = () => {
    const r = recognitionRef.current;
    if (!r) {
      setError("Speech recognition is not supported in this browser.");
      return;
    }
    if (listening) {
      r.stop();
      setListening(false);
      return;
    }
    setError(null);
    setListening(true);
    try {
      r.start();
    } catch {
      setListening(false);
    }
  };

  const runVoice = async () => {
    if (!text.trim()) {
      setError("Transcribe or type speech text first.");
      return;
    }
    setLoading(true);
    setError(null);
    setVoiceResult(null);
    try {
      const res = await api<VoiceResult>("/analyze/voice", {
        method: "POST",
        json: { text: text.trim(), locale: typeof navigator !== "undefined" ? navigator.language : null },
      });
      setVoiceResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Voice analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    if (tab !== "face") return;
    let cancelled = false;
    let videoEl: HTMLVideoElement | null = null;
    (async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        videoEl = videoRef.current;
        if (videoEl) videoEl.srcObject = stream;
      } catch {
        if (!cancelled) setError("Camera permission is required for face analysis.");
      }
    })();
    return () => {
      cancelled = true;
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
      if (videoEl) videoEl.srcObject = null;
    };
  }, [tab]);

  const scoreRows = useCallback((scores: Record<string, number>) => {
    return Object.entries(scores).map(([name, value]) => ({ name, value }));
  }, []);

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex flex-wrap gap-2 rounded-xl border border-slate-800 bg-slate-900/40 p-1">
        {(
          [
            ["text", "Text"],
            ["face", "Live camera"],
            ["voice", "Voice"],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            onClick={() => {
              setTab(id);
              setError(null);
            }}
            className={`flex-1 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              tab === id ? "bg-sky-600 text-white" : "text-slate-400 hover:text-white"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {error && (
        <div className="rounded-lg border border-red-900/60 bg-red-950/50 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}

      {tab === "text" && (
        <div className="space-y-4">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={5}
            placeholder="Paste or type text to analyze..."
            className="w-full rounded-xl border border-slate-700 bg-slate-900/80 px-4 py-3 text-slate-100 placeholder:text-slate-600 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
          />
          <button
            type="button"
            disabled={loading || !text.trim()}
            onClick={() => void runText()}
            className="rounded-lg bg-sky-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-sky-500 disabled:opacity-50"
          >
            {loading ? "Analyzing…" : "Analyze text"}
          </button>
          {textResult && <ResultText data={textResult} scoreRows={scoreRows} />}
        </div>
      )}

      {tab === "face" && (
        <div className="space-y-4">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full max-w-lg rounded-xl border border-slate-700 bg-black"
          />
          <canvas ref={canvasRef} className="hidden" />
          <button
            type="button"
            disabled={loading}
            onClick={() => void captureFace()}
            className="rounded-lg bg-sky-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-sky-500 disabled:opacity-50"
          >
            {loading ? "Processing…" : "Capture & analyze frame"}
          </button>
          {faceResult && <ResultFace data={faceResult} scoreRows={scoreRows} />}
        </div>
      )}

      {tab === "voice" && (
        <div className="space-y-4">
          <p className="text-sm text-slate-400">
            Use the microphone to transcribe (Web Speech API), edit the transcript if needed, then analyze.
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => toggleListen()}
              className={`rounded-lg px-4 py-2 text-sm font-medium ${
                listening ? "bg-amber-600 text-white" : "bg-slate-800 text-slate-200"
              }`}
            >
              {listening ? "Stop" : "Start speaking"}
            </button>
          </div>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={5}
            placeholder="Transcript appears here..."
            className="w-full rounded-xl border border-slate-700 bg-slate-900/80 px-4 py-3 text-slate-100 placeholder:text-slate-600 focus:border-sky-500 focus:outline-none"
          />
          <button
            type="button"
            disabled={loading || !text.trim()}
            onClick={() => void runVoice()}
            className="rounded-lg bg-sky-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-sky-500 disabled:opacity-50"
          >
            {loading ? "Analyzing…" : "Analyze transcript"}
          </button>
          {voiceResult && <ResultVoice data={voiceResult} scoreRows={scoreRows} />}
        </div>
      )}
    </div>
  );
}

function ResultText({
  data,
  scoreRows,
}: {
  data: TextResult;
  scoreRows: (s: Record<string, number>) => { name: string; value: number }[];
}) {
  const chart = scoreRows(data.scores as unknown as Record<string, number>);
  return (
    <div className="space-y-4 rounded-xl border border-slate-800 bg-slate-900/40 p-4">
      <div className="flex flex-wrap gap-4">
        <div>
          <div className="text-xs uppercase text-slate-500">Dominant sentiment</div>
          <div className="text-lg font-semibold capitalize text-white">{data.dominant_label}</div>
        </div>
        <div>
          <div className="text-xs uppercase text-slate-500">Confidence</div>
          <div className="text-lg font-semibold text-sky-300">{data.confidence.toFixed(3)}</div>
        </div>
      </div>
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chart}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="name" stroke="#94a3b8" />
            <YAxis domain={[-1, 1]} stroke="#94a3b8" />
            <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155" }} />
            <Bar dataKey="value" fill="#38bdf8" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div>
        <h3 className="text-sm font-medium text-slate-400">AI explanation</h3>
        <p className="mt-1 whitespace-pre-wrap text-slate-200">{data.explanation}</p>
        <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-300">
          {data.suggestions.map((s, i) => (
            <li key={i}>{s}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function ResultFace({
  data,
  scoreRows,
}: {
  data: FaceResult;
  scoreRows: (s: Record<string, number>) => { name: string; value: number }[];
}) {
  const chart = scoreRows(data.emotions || {});
  return (
    <div className="space-y-4 rounded-xl border border-slate-800 bg-slate-900/40 p-4">
      <div className="flex flex-wrap gap-4">
        <div>
          <div className="text-xs uppercase text-slate-500">Dominant emotion</div>
          <div className="text-lg font-semibold capitalize text-white">{data.dominant_label}</div>
        </div>
        <div>
          <div className="text-xs uppercase text-slate-500">Confidence</div>
          <div className="text-lg font-semibold text-sky-300">{data.confidence.toFixed(3)}</div>
        </div>
        <div>
          <div className="text-xs uppercase text-slate-500">Faces</div>
          <div className="text-lg font-semibold text-slate-200">{data.faces}</div>
        </div>
      </div>
      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chart}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="name" stroke="#94a3b8" />
            <YAxis domain={[0, 1]} stroke="#94a3b8" />
            <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155" }} />
            <Bar dataKey="value" fill="#a78bfa" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div>
        <h3 className="text-sm font-medium text-slate-400">AI explanation</h3>
        <p className="mt-1 whitespace-pre-wrap text-slate-200">{data.explanation}</p>
        <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-300">
          {data.suggestions.map((s, i) => (
            <li key={i}>{s}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function ResultVoice({
  data,
  scoreRows,
}: {
  data: VoiceResult;
  scoreRows: (s: Record<string, number>) => { name: string; value: number }[];
}) {
  const chart = scoreRows(data.scores as unknown as Record<string, number>);
  return (
    <div className="space-y-4 rounded-xl border border-slate-800 bg-slate-900/40 p-4">
      <div className="flex flex-wrap gap-4">
        <div>
          <div className="text-xs uppercase text-slate-500">Dominant sentiment</div>
          <div className="text-lg font-semibold capitalize text-white">{data.dominant_label}</div>
        </div>
        <div>
          <div className="text-xs uppercase text-slate-500">Confidence</div>
          <div className="text-lg font-semibold text-sky-300">{data.confidence.toFixed(3)}</div>
        </div>
      </div>
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chart}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="name" stroke="#94a3b8" />
            <YAxis domain={[-1, 1]} stroke="#94a3b8" />
            <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155" }} />
            <Bar dataKey="value" fill="#34d399" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div>
        <h3 className="text-sm font-medium text-slate-400">AI explanation</h3>
        <p className="mt-1 whitespace-pre-wrap text-slate-200">{data.explanation}</p>
        <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-300">
          {data.suggestions.map((s, i) => (
            <li key={i}>{s}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
