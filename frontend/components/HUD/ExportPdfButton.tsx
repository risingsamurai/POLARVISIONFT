"use client";

import { PDFDocument, StandardFonts, rgb } from "pdf-lib";
import { selectLockedRoute, usePolarisStore } from "@/lib/store";

export function ExportPdfButton() {
  const route = usePolarisStore(selectLockedRoute);
  const vessel = usePolarisStore((s) => s.vessel);
  const alerts = usePolarisStore((s) => s.alerts);

  return (
    <button
      type="button"
      className="w-full rounded-lg border border-white/20 px-3 py-2 text-xs font-bold uppercase"
      onClick={async () => {
        const doc = await PDFDocument.create();
        const page = doc.addPage([612, 792]);
        const font = await doc.embedFont(StandardFonts.HelveticaBold);
        const body = await doc.embedFont(StandardFonts.Helvetica);
        page.drawText("POLARIS Mission Plan", {
          x: 48,
          y: 740,
          size: 18,
          font,
          color: rgb(0.05, 0.15, 0.35),
        });
        const lines = [
          `Route: ${route.name}`,
          `Distance: ${route.distanceNm} NM`,
          `ETA: ${route.etaHours} h`,
          `Fuel: ${route.fuelMt} MT`,
          `Risk: ${route.riskScore}`,
          `Vessel: ${vessel.lat.toFixed(3)}, ${vessel.lon.toFixed(3)}`,
          `Hazards: ${alerts.slice(-5).map((a) => a.message).join(" | ") || "none logged"}`,
        ];
        lines.forEach((t, i) => {
          page.drawText(t, { x: 48, y: 700 - i * 22, size: 12, font: body });
        });
        const bytes = await doc.save();
        const blob = new Blob([new Uint8Array(bytes)], { type: "application/pdf" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "polaris-mission-plan.pdf";
        a.click();
        URL.revokeObjectURL(url);
      }}
    >
      Export mission PDF
    </button>
  );
}
