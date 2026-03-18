/**
 * Downloads a Recharts (SVG-based) chart as a PNG file.
 * Finds the first <svg> inside the given container, serializes it,
 * draws it onto a 2× canvas for retina quality, then triggers download.
 */
export function downloadChartAsPng(container: HTMLElement | null, filename: string): void {
  if (!container) return;
  const svg = container.querySelector<SVGElement>("svg");
  if (!svg) return;

  const w = svg.clientWidth  || svg.getBoundingClientRect().width;
  const h = svg.clientHeight || svg.getBoundingClientRect().height;
  if (!w || !h) return;

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
  canvas.width  = w * dpr;
  canvas.height = h * dpr;

  const ctx = canvas.getContext("2d")!;
  ctx.scale(dpr, dpr);
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, w, h);

  const img = new Image();
  img.onload = () => {
    ctx.drawImage(img, 0, 0, w, h);
    URL.revokeObjectURL(url);

    const a = document.createElement("a");
    a.download = `${filename}.png`;
    a.href     = canvas.toDataURL("image/png");
    a.click();
  };
  img.src = url;
}
