/**
 * Downloads a Recharts (SVG-based) chart as a PNG file.
 * Supports an optional title, a legend rendered as a grid below the chart,
 * and a config footer rendered as small text at the very bottom.
 */

export interface LegendItem {
  color: string;
  label: string;
  /** Small badge shown after the label, e.g. "+2.3%" */
  extra?: string;
}

export function downloadChartAsPng(
  container: HTMLElement | null,
  filename: string,
  options?: {
    title?: string;
    configLines?: string[];
    legendItems?: LegendItem[];
  },
): void {
  if (!container) return;
  const svg = container.querySelector<SVGElement>("svg");
  if (!svg) return;

  const w = svg.clientWidth  || svg.getBoundingClientRect().width;
  const h = svg.clientHeight || svg.getBoundingClientRect().height;
  if (!w || !h) return;

  const FONT = "Inter, -apple-system, BlinkMacSystemFont, sans-serif";

  const TITLE_H = options?.title ? 40 : 0;

  const legendItems = options?.legendItems ?? [];
  const LEGEND_COLS  = legendItems.length > 0 ? Math.min(4, Math.max(1, Math.floor(w / 210))) : 0;
  const LEGEND_ROWS  = legendItems.length > 0 ? Math.ceil(legendItems.length / LEGEND_COLS) : 0;
  const LEGEND_H     = LEGEND_ROWS > 0 ? LEGEND_ROWS * 20 + 16 : 0;

  const configLines = options?.configLines ?? [];
  const FOOTER_H    = configLines.length > 0 ? configLines.length * 16 + 20 : 0;

  const TOTAL_H = h + TITLE_H + LEGEND_H + FOOTER_H;

  // Clone SVG so it renders standalone
  const clone = svg.cloneNode(true) as SVGElement;
  clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  clone.setAttribute("width",  String(w));
  clone.setAttribute("height", String(h));
  const svgStr = new XMLSerializer().serializeToString(clone);
  const blob   = new Blob([svgStr], { type: "image/svg+xml;charset=utf-8" });
  const url    = URL.createObjectURL(blob);

  const dpr    = window.devicePixelRatio || 1;
  const canvas = document.createElement("canvas");
  canvas.width  = w * dpr;
  canvas.height = TOTAL_H * dpr;

  const ctx = canvas.getContext("2d")!;
  ctx.scale(dpr, dpr);
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, w, TOTAL_H);

  // Title
  if (options?.title && TITLE_H > 0) {
    ctx.font      = `600 13px ${FONT}`;
    ctx.fillStyle = "#1a1a1a";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(options.title, w / 2, TITLE_H / 2);
    ctx.strokeStyle = "#e4e4de";
    ctx.lineWidth   = 1;
    ctx.beginPath();
    ctx.moveTo(0, TITLE_H - 1);
    ctx.lineTo(w, TITLE_H - 1);
    ctx.stroke();
  }

  const img = new Image();
  img.onload = () => {
    ctx.drawImage(img, 0, TITLE_H, w, h);
    URL.revokeObjectURL(url);

    // Legend grid
    if (legendItems.length > 0) {
      const colW    = w / LEGEND_COLS;
      const legendY = TITLE_H + h + 8;

      legendItems.forEach((item, i) => {
        const col = i % LEGEND_COLS;
        const row = Math.floor(i / LEGEND_COLS);
        const cx  = col * colW + 16;
        const cy  = legendY + row * 20 + 10;

        // Colored circle
        ctx.fillStyle = item.color;
        ctx.beginPath();
        ctx.arc(cx, cy, 4, 0, Math.PI * 2);
        ctx.fill();

        // Label — truncate to fit
        ctx.font         = `10px ${FONT}`;
        ctx.fillStyle    = "#5a5a5a";
        ctx.textAlign    = "left";
        ctx.textBaseline = "middle";

        const extraW  = item.extra ? ctx.measureText(` ${item.extra}`).width + 4 : 0;
        const maxLabelW = colW - 30 - extraW;
        let label = item.label;
        while (label.length > 3 && ctx.measureText(label).width > maxLabelW) {
          label = label.slice(0, -1);
        }
        if (label !== item.label) label = label.slice(0, -1) + "…";
        ctx.fillText(label, cx + 10, cy);

        // Extra badge (increase value)
        if (item.extra) {
          const lw = ctx.measureText(label).width;
          const isPos = item.extra.startsWith("+") || (!item.extra.startsWith("-") && parseFloat(item.extra) >= 0);
          ctx.fillStyle = isPos ? "#16a34a" : "#dc2626";
          ctx.font      = `600 10px ${FONT}`;
          ctx.fillText(item.extra, cx + 10 + lw + 4, cy);
        }
      });
    }

    // Config footer
    if (configLines.length > 0) {
      const footerY = TITLE_H + h + LEGEND_H + 8;

      ctx.strokeStyle = "#e4e4de";
      ctx.lineWidth   = 1;
      ctx.beginPath();
      ctx.moveTo(24, footerY);
      ctx.lineTo(w - 24, footerY);
      ctx.stroke();

      configLines.forEach((line, i) => {
        ctx.font         = `10px ${FONT}`;
        ctx.fillStyle    = "#9b9b9b";
        ctx.textAlign    = "left";
        ctx.textBaseline = "top";
        ctx.fillText(line, 24, footerY + 8 + i * 16);
      });
    }

    const a = document.createElement("a");
    a.download = `${filename}.png`;
    a.href     = canvas.toDataURL("image/png");
    a.click();
  };
  img.src = url;
}
