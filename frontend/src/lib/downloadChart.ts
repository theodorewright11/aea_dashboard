/**
 * Downloads a Recharts (SVG-based) chart as a PNG file.
 * Optionally adds a title above the chart in the downloaded image.
 */
export function downloadChartAsPng(
  container: HTMLElement | null,
  filename: string,
  options?: { title?: string },
): void {
  if (!container) return;
  const svg = container.querySelector<SVGElement>("svg");
  if (!svg) return;

  const w = svg.clientWidth  || svg.getBoundingClientRect().width;
  const h = svg.clientHeight || svg.getBoundingClientRect().height;
  if (!w || !h) return;

  const TITLE_H  = options?.title ? 40 : 0;
  const PAD_SIDE = 0;

  // Clone and annotate the SVG so it renders standalone
  const clone = svg.cloneNode(true) as SVGElement;
  clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  clone.setAttribute("width",  String(w));
  clone.setAttribute("height", String(h));

  const svgStr = new XMLSerializer().serializeToString(clone);
  const blob   = new Blob([svgStr], { type: "image/svg+xml;charset=utf-8" });
  const url    = URL.createObjectURL(blob);

  const dpr    = window.devicePixelRatio || 1;
  const canvas = document.createElement("canvas");
  canvas.width  = (w + PAD_SIDE * 2) * dpr;
  canvas.height = (h + TITLE_H) * dpr;

  const ctx = canvas.getContext("2d")!;
  ctx.scale(dpr, dpr);
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, w + PAD_SIDE * 2, h + TITLE_H);

  if (options?.title && TITLE_H > 0) {
    ctx.font      = "600 13px Inter, -apple-system, BlinkMacSystemFont, sans-serif";
    ctx.fillStyle = "#1a1a1a";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(options.title, (w + PAD_SIDE * 2) / 2, TITLE_H / 2);
    // Subtle separator line
    ctx.strokeStyle = "#e4e4de";
    ctx.lineWidth   = 1;
    ctx.beginPath();
    ctx.moveTo(PAD_SIDE, TITLE_H - 1);
    ctx.lineTo(w + PAD_SIDE, TITLE_H - 1);
    ctx.stroke();
  }

  const img = new Image();
  img.onload = () => {
    ctx.drawImage(img, PAD_SIDE, TITLE_H, w, h);
    URL.revokeObjectURL(url);

    const a = document.createElement("a");
    a.download = `${filename}.png`;
    a.href     = canvas.toDataURL("image/png");
    a.click();
  };
  img.src = url;
}
