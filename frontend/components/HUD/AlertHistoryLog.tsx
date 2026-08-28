"use client";

import { usePolarisStore } from "@/lib/store";
import { FileDown, History, AlertCircle } from "lucide-react";

const TEXT_COLOR: Record<string, string> = {
  CRITICAL: "text-red-400 border-red-500/20 bg-red-500/5",
  WARNING: "text-amber-400 border-amber-500/20 bg-amber-500/5",
  INFO: "text-blue-400 border-blue-500/20 bg-blue-500/5",
  CLEAR: "text-emerald-400 border-emerald-500/20 bg-emerald-500/5",
};

export function AlertHistoryLog() {
  const alerts = usePolarisStore((s) => s.alerts);

  const handleExportCsv = () => {
    if (alerts.length === 0) {
      alert("No alerts in history to export!");
      return;
    }
    const header = "id,tier,message,timestamp";
    const rows = alerts.map((a) => {
      const ts = a.timestamp || a.ts;
      const id = a.id || `${a.tier}-${Date.parse(a.ts)}`;
      return `${id},${a.tier},"${a.message.replace(/"/g, '""')}",${ts}`;
    });
    
    const csvContent = [header, ...rows].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `polaris_alerts_log_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <section className="hud-panel p-3.5 w-72 shadow-2xl flex flex-col gap-2.5">
      <div className="flex items-center justify-between border-b border-white/10 pb-2">
        <h3 className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
          <History className="h-4 w-4 text-blue-400 shrink-0" />
          Alert History Log
        </h3>
        <button
          onClick={handleExportCsv}
          disabled={alerts.length === 0}
          className="flex items-center gap-1 px-2 py-1 rounded bg-white/5 border border-white/10 hover:bg-white/10 text-[9px] font-bold uppercase text-slate-300 disabled:opacity-40 disabled:hover:bg-white/5 transition-all"
          title="Download alert log as CSV"
        >
          <FileDown className="h-3 w-3" />
          Export CSV
        </button>
      </div>

      <div className="max-h-48 overflow-y-auto pr-1 flex flex-col gap-1.5 scrollbar-thin">
        {alerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-6 text-center text-slate-500">
            <AlertCircle className="h-5 w-5 mb-1.5 opacity-30" />
            <p className="text-[10px] italic">No alert history logged yet</p>
          </div>
        ) : (
          [...alerts]
            .reverse()
            .map((a, i) => {
              const ts = a.timestamp || a.ts;
              const formattedTime = new Date(ts).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
                hour12: false,
              });
              const borderTheme = TEXT_COLOR[a.tier] || "text-slate-300 border-white/10 bg-white/5";

              return (
                <div
                  key={`${a.id || i}`}
                  className={`p-2 rounded-lg border text-[10px] flex flex-col gap-0.5 leading-normal ${borderTheme}`}
                >
                  <div className="flex items-center justify-between font-bold text-[9px] uppercase tracking-wider">
                    <span>{a.tier}</span>
                    <span className="text-slate-400 lowercase font-medium text-[8px]">{formattedTime}</span>
                  </div>
                  <p className="text-slate-200 font-medium break-words mt-0.5">{a.message}</p>
                </div>
              );
            })
        )}
      </div>
    </section>
  );
}
