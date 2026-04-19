"use client";

import { useCallback, useEffect, useState } from "react";
import { api, downloadHistoryCsv } from "@/lib/api";
import type { HistoryItem } from "@/lib/types";

export default function HistoryPage() {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [filter, setFilter] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const q = filter ? `?limit=100&analysis_type=${encodeURIComponent(filter)}` : "?limit=100";
      const res = await api<{ items: HistoryItem[]; total: number }>(`/history${q}`);
      setItems(res.items);
      setTotal(res.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load history");
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    void load();
  }, [load]);

  const remove = async (id: string) => {
    setBusyId(id);
    try {
      await api(`/history/${id}`, { method: "DELETE" });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200"
        >
          <option value="">All types</option>
          <option value="text">Text</option>
          <option value="face">Face</option>
          <option value="voice">Voice</option>
        </select>
        <button
          type="button"
          onClick={() => void load()}
          className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-200 hover:bg-slate-800"
        >
          Refresh
        </button>
        <button
          type="button"
          onClick={() => {
            void downloadHistoryCsv(filter || undefined).catch((e) =>
              setError(e instanceof Error ? e.message : "Export failed"),
            );
          }}
          className="rounded-lg bg-sky-600 px-3 py-2 text-sm font-medium text-white hover:bg-sky-500"
        >
          Export CSV
        </button>
        <span className="text-sm text-slate-500">{total} total</span>
      </div>

      {error && (
        <div className="rounded-lg border border-red-900/60 bg-red-950/50 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-sky-500 border-t-transparent" />
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-900/80 text-slate-400">
              <tr>
                <th className="px-4 py-2">Time</th>
                <th className="px-4 py-2">Type</th>
                <th className="px-4 py-2">Label</th>
                <th className="px-4 py-2">Preview</th>
                <th className="px-4 py-2" />
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                    No saved analyses yet.
                  </td>
                </tr>
              ) : (
                items.map((row) => (
                  <tr key={row.id} className="border-t border-slate-800">
                    <td className="px-4 py-2 text-slate-300">
                      {row.timestamp ? new Date(row.timestamp).toLocaleString() : "—"}
                    </td>
                    <td className="px-4 py-2 capitalize text-sky-300">{row.analysis_type}</td>
                    <td className="px-4 py-2">{row.dominant_label ?? "—"}</td>
                    <td className="max-w-xs truncate px-4 py-2 text-slate-400">
                      {(row.text || row.explanation || "").slice(0, 120)}
                    </td>
                    <td className="px-4 py-2 text-right">
                      <button
                        type="button"
                        disabled={busyId === row.id}
                        onClick={() => void remove(row.id)}
                        className="text-xs text-red-400 hover:text-red-300 disabled:opacity-50"
                      >
                        {busyId === row.id ? "…" : "Delete"}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
