/** Export Recharts / DOM chart containers as PNG or SVG (client-only). */

export async function exportElementAsPng(element: HTMLElement, filename: string): Promise<void> {
  const svg = element.querySelector("svg");
  if (!svg) {
    throw new Error("No chart SVG found");
  }
  const svgData = new XMLSerializer().serializeToString(svg);
  const canvas = document.createElement("canvas");
  const bbox = svg.getBoundingClientRect();
  const scale = 2;
  canvas.width = Math.max(1, Math.floor(bbox.width * scale));
  canvas.height = Math.max(1, Math.floor(bbox.height * scale));
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("Canvas not supported");
  const img = new Image();
  const url = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svgData)}`;
  await new Promise<void>((resolve, reject) => {
    img.onload = () => {
      ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue("--forge-bg") || "#fff";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      resolve();
    };
    img.onerror = () => reject(new Error("Failed to render chart"));
    img.src = url;
  });
  const a = document.createElement("a");
  a.href = canvas.toDataURL("image/png");
  a.download = filename.endsWith(".png") ? filename : `${filename}.png`;
  a.click();
}

export function exportElementAsSvg(element: HTMLElement, filename: string): void {
  const svg = element.querySelector("svg");
  if (!svg) throw new Error("No chart SVG found");
  const blob = new Blob([new XMLSerializer().serializeToString(svg)], {
    type: "image/svg+xml;charset=utf-8",
  });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename.endsWith(".svg") ? filename : `${filename}.svg`;
  a.click();
  URL.revokeObjectURL(a.href);
}
