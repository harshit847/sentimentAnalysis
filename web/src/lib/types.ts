export type SentimentScores = {
  neg: number;
  neu: number;
  pos: number;
  compound: number;
};

export type TextResult = {
  type: "text";
  sentiment: string;
  confidence: number;
  scores: SentimentScores;
  length: number;
  dominant_label: string;
  explanation: string;
  suggestions: string[];
};

export type FaceResult = {
  type: "face";
  emotion: string;
  confidence: number;
  emotions: Record<string, number>;
  faces: number;
  dominant_label: string;
  explanation: string;
  suggestions: string[];
  filename?: string | null;
};

export type VoiceResult = {
  type: "voice";
  sentiment: string;
  confidence: number;
  scores: SentimentScores;
  length: number;
  dominant_label: string;
  locale?: string | null;
  explanation: string;
  suggestions: string[];
};

export type User = {
  id: string;
  email: string;
  name: string;
  created_at?: string | null;
};

export type HistoryItem = {
  id: string;
  user_id: string;
  analysis_type: string;
  timestamp?: string | null;
  dominant_label?: string;
  confidence?: number;
  text?: string;
  sentiment?: string;
  emotion?: string;
  faces?: number;
  explanation?: string;
  suggestions?: string[];
  scores?: SentimentScores;
  emotions?: Record<string, number>;
  locale?: string | null;
};

export type AnalyticsResponse = {
  total: number;
  window_days: number;
  by_type: Record<string, number>;
  sentiment_distribution: { label: string; count: number }[];
  emotion_distribution: { label: string; count: number }[];
  daily_trend: {
    date: string;
    text: number;
    face: number;
    voice: number;
    total: number;
  }[];
};
