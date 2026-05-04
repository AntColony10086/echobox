import { useCallback, useEffect, useRef, useState } from "react";

import { ModeSwitcher } from "../components/ModeSwitcher";

type Annotation =
  | {
      type: "box";
      category: string;
      x: number;
      y: number;
      width: number;
      height: number;
    }
  | { type: "point"; category: string; x: number; y: number };

type StatusKind = "idle" | "ready" | "warn" | "error";

type ImageAsset = {
  name: string;
  element: HTMLImageElement;
  width: number;
  height: number;
};

const STATUS_LABEL: Record<StatusKind, string> = {
  idle: "待导入",
  ready: "就绪",
  warn: "警告",
  error: "错误",
};

const STATUS_COLOR: Record<StatusKind, { bg: string; fg: string }> = {
  idle: { bg: "rgba(93, 107, 115, 0.12)", fg: "#47545c" },
  ready: { bg: "rgba(45, 143, 103, 0.14)", fg: "#166447" },
  warn: { bg: "rgba(182, 122, 19, 0.14)", fg: "#865d10" },
  error: { bg: "rgba(178, 65, 52, 0.12)", fg: "#973328" },
};

function hashString(value: string): number {
  let hash = 0;
  for (let i = 0; i < value.length; i += 1) {
    hash = value.charCodeAt(i) + ((hash << 5) - hash);
  }
  return Math.abs(hash);
}

function colorForCategory(category: string): {
  stroke: string;
  fill: string;
  label: string;
  dot: string;
} {
  const hue = hashString(category || "default") % 360;
  return {
    stroke: `hsl(${hue} 78% 42%)`,
    fill: `hsla(${hue} 78% 42% / 0.14)`,
    label: `hsl(${hue} 88% 24%)`,
    dot: `hsl(${hue} 78% 46%)`,
  };
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

function isLikelyNormalized(value: number): boolean {
  return value >= 0 && value <= 1;
}

function parseAnnotations(
  text: string,
  imageMeta: { width: number; height: number } | null,
): { annotations: Annotation[]; formats: string[]; skipped: number } {
  const annotations: Annotation[] = [];
  const formats = new Set<string>();
  let skipped = 0;

  for (const rawLine of text.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line) continue;
    const tokens = line.split(/\s+/);

    if (tokens.length === 5 && imageMeta) {
      const [category, cx, cy, w, h] = tokens;
      const centerX = Number(cx);
      const centerY = Number(cy);
      const width = Number(w);
      const height = Number(h);
      if (
        category &&
        Number.isFinite(centerX) &&
        Number.isFinite(centerY) &&
        Number.isFinite(width) &&
        Number.isFinite(height) &&
        isLikelyNormalized(centerX) &&
        isLikelyNormalized(centerY) &&
        isLikelyNormalized(width) &&
        isLikelyNormalized(height)
      ) {
        const boxW = width * imageMeta.width;
        const boxH = height * imageMeta.height;
        const left = centerX * imageMeta.width - boxW / 2;
        const top = centerY * imageMeta.height - boxH / 2;
        const x = clamp(left, 0, imageMeta.width);
        const y = clamp(top, 0, imageMeta.height);
        const right = clamp(left + boxW, 0, imageMeta.width);
        const bottom = clamp(top + boxH, 0, imageMeta.height);
        annotations.push({
          type: "box",
          category,
          x,
          y,
          width: Math.max(0, right - x),
          height: Math.max(0, bottom - y),
        });
        formats.add("YOLO 检测框");
        continue;
      }
    } else if (tokens.length === 3) {
      const [category, xs, ys] = tokens;
      const x = Number(xs);
      const y = Number(ys);
      if (category && Number.isFinite(x) && Number.isFinite(y)) {
        annotations.push({ type: "point", category, x, y });
        formats.add("点标注");
        continue;
      }
    }

    skipped += 1;
  }

  return { annotations, formats: Array.from(formats), skipped };
}

function drawLabel(
  ctx: CanvasRenderingContext2D,
  text: string,
  x: number,
  y: number,
  color: string,
): void {
  const paddingX = 10;
  const labelHeight = 28;
  ctx.font = "600 16px 'Segoe UI', sans-serif";
  const metrics = ctx.measureText(text);
  const labelWidth = Math.ceil(metrics.width) + paddingX * 2;
  const labelX = Math.max(0, x);
  const labelY = Math.max(labelHeight, y);

  ctx.fillStyle = "rgba(255, 252, 247, 0.92)";
  ctx.strokeStyle = color;
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.roundRect(labelX, labelY - labelHeight, labelWidth, labelHeight, 8);
  ctx.fill();
  ctx.stroke();

  ctx.fillStyle = color;
  ctx.fillText(text, labelX + paddingX, labelY - 9);
}

function drawAnnotation(ctx: CanvasRenderingContext2D, ann: Annotation): void {
  const colors = colorForCategory(ann.category);
  if (ann.type === "box") {
    ctx.lineWidth = 3;
    ctx.strokeStyle = colors.stroke;
    ctx.fillStyle = colors.fill;
    ctx.beginPath();
    ctx.rect(ann.x, ann.y, ann.width, ann.height);
    ctx.fill();
    ctx.stroke();
    drawLabel(ctx, ann.category, ann.x + 2, ann.y - 6, colors.label);
  } else {
    ctx.fillStyle = colors.dot;
    ctx.strokeStyle = "rgba(255, 255, 255, 0.95)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(ann.x, ann.y, 8, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
    drawLabel(ctx, ann.category, ann.x + 14, ann.y - 14, colors.label);
  }
}

function loadImage(file: File): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("图片读取失败"));
    reader.onload = () => {
      const img = new Image();
      img.onerror = () => reject(new Error("图片解析失败"));
      img.onload = () => resolve(img);
      img.src = String(reader.result || "");
    };
    reader.readAsDataURL(file);
  });
}

function readText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("标注读取失败"));
    reader.onload = () => resolve(String(reader.result || ""));
    reader.readAsText(file, "utf-8");
  });
}

export function ViewerPage(): JSX.Element {
  const baseCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const overlayCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const stageRef = useRef<HTMLDivElement | null>(null);

  const [image, setImage] = useState<ImageAsset | null>(null);
  const [annotationText, setAnnotationText] = useState("");
  const [annotationFileName, setAnnotationFileName] = useState("");
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [formats, setFormats] = useState<string[]>([]);
  const [skipped, setSkipped] = useState(0);
  const [status, setStatus] = useState<StatusKind>("idle");
  const [banner, setBanner] = useState("等待拖入图片和标注文件。");
  const [imageError, setImageError] = useState<string | null>(null);
  const [annError, setAnnError] = useState<string | null>(null);
  const [imageDragOver, setImageDragOver] = useState(false);
  const [annDragOver, setAnnDragOver] = useState(false);

  const renderImage = useCallback((asset: ImageAsset) => {
    const base = baseCanvasRef.current;
    const overlay = overlayCanvasRef.current;
    if (!base || !overlay) return;
    base.width = asset.width;
    base.height = asset.height;
    overlay.width = asset.width;
    overlay.height = asset.height;
    const ctx = base.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, asset.width, asset.height);
    ctx.drawImage(asset.element, 0, 0);
  }, []);

  const renderAnnotations = useCallback((items: Annotation[]) => {
    const overlay = overlayCanvasRef.current;
    if (!overlay) return;
    const ctx = overlay.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, overlay.width, overlay.height);
    for (const ann of items) drawAnnotation(ctx, ann);
  }, []);

  const updateScale = useCallback(() => {
    const stage = stageRef.current;
    const base = baseCanvasRef.current;
    const overlay = overlayCanvasRef.current;
    if (!stage || !base || !overlay || !image) return;
    const minHeight = parseFloat(getComputedStyle(stage).minHeight) || 0;
    const stageW = stage.clientWidth || image.width;
    const stageH = Math.max(stage.clientHeight || 0, minHeight);
    const scale = Math.min(stageW / image.width, stageH / image.height, 1);
    const dispW = Math.round(image.width * scale);
    const dispH = Math.round(image.height * scale);
    base.style.width = `${dispW}px`;
    base.style.height = `${dispH}px`;
    overlay.style.width = `${dispW}px`;
    overlay.style.height = `${dispH}px`;
    stage.style.height = `${Math.max(dispH, minHeight)}px`;
  }, [image]);

  useEffect(() => {
    if (!image) return;
    renderImage(image);
    updateScale();
    renderAnnotations(annotations);
  }, [image, annotations, renderImage, renderAnnotations, updateScale]);

  useEffect(() => {
    const handler = (): void => updateScale();
    window.addEventListener("resize", handler);
    return () => window.removeEventListener("resize", handler);
  }, [updateScale]);

  const handleImageFile = useCallback(
    async (file: File | null) => {
      if (!file) return;
      const ext = file.name.toLowerCase().split(".").pop();
      if (!ext || !["jpg", "jpeg", "png"].includes(ext)) {
        setImageError("仅支持 JPG / PNG");
        setStatus("error");
        setBanner("仅支持 JPG / PNG 图片。");
        return;
      }
      try {
        const el = await loadImage(file);
        setImage({
          name: file.name,
          element: el,
          width: el.naturalWidth,
          height: el.naturalHeight,
        });
        setImageError(null);
        if (annotationText) {
          const result = parseAnnotations(annotationText, {
            width: el.naturalWidth,
            height: el.naturalHeight,
          });
          setAnnotations(result.annotations);
          setFormats(result.formats);
          setSkipped(result.skipped);
          if (result.annotations.length === 0) {
            setStatus("warn");
            setBanner("标注文件已读取，但没有识别出有效标注。");
          } else if (result.skipped > 0) {
            setStatus("warn");
            setBanner(
              `已渲染 ${result.annotations.length} 条标注，跳过 ${result.skipped} 条无效或空白行。`,
            );
          } else {
            setStatus("ready");
            setBanner(
              `已渲染 ${result.annotations.length} 条标注，可继续拖入新标注文件直接刷新。`,
            );
          }
        } else {
          setAnnotations([]);
          setStatus("ready");
          setBanner("图片加载完成，继续拖入 TXT 标注文件进行叠加预览。");
        }
      } catch (err) {
        setImageError(err instanceof Error ? err.message : String(err));
        setStatus("error");
        setBanner(err instanceof Error ? err.message : String(err));
      }
    },
    [annotationText],
  );

  const handleAnnFile = useCallback(
    async (file: File | null) => {
      if (!file) return;
      const ext = file.name.toLowerCase().split(".").pop();
      if (ext !== "txt") {
        setAnnError("仅支持 TXT 标注文件");
        setStatus("error");
        setBanner("仅支持 TXT 标注文件。");
        return;
      }
      try {
        const text = await readText(file);
        setAnnotationText(text);
        setAnnotationFileName(file.name);
        setAnnError(null);
        if (!image) {
          setAnnotations([]);
          setFormats([]);
          setSkipped(0);
          setStatus("warn");
          setBanner("标注文件已加载。YOLO 格式需要图片尺寸，请先拖入图片。");
          return;
        }
        const result = parseAnnotations(text, {
          width: image.width,
          height: image.height,
        });
        setAnnotations(result.annotations);
        setFormats(result.formats);
        setSkipped(result.skipped);
        if (result.annotations.length === 0) {
          setStatus("warn");
          setBanner("标注文件已读取，但没有识别出有效标注。");
        } else if (result.skipped > 0) {
          setStatus("warn");
          setBanner(
            `已渲染 ${result.annotations.length} 条标注，跳过 ${result.skipped} 条无效或空白行。`,
          );
        } else {
          setStatus("ready");
          setBanner(
            `已渲染 ${result.annotations.length} 条标注，可继续拖入新标注文件直接刷新。`,
          );
        }
      } catch (err) {
        setAnnError(err instanceof Error ? err.message : String(err));
        setStatus("error");
        setBanner(err instanceof Error ? err.message : String(err));
      }
    },
    [image],
  );

  const boxCount = annotations.filter((a) => a.type === "box").length;
  const pointCount = annotations.filter((a) => a.type === "point").length;

  return (
    <div
      style={{
        minHeight: "100vh",
        fontFamily: "'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif",
        color: "#1f2a33",
        background:
          "radial-gradient(circle at top left, rgba(212,107,54,0.14), transparent 28%), radial-gradient(circle at 100% 0, rgba(45,143,103,0.12), transparent 24%), linear-gradient(135deg, #f4efe6, #f7f2ea 45%, #e6dcc8)",
      }}
    >
      <div
        style={{ maxWidth: 1440, margin: "0 auto", padding: "28px 24px 32px" }}
      >
        <ModeSwitcher current="viewer" />

        <header
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-end",
            gap: 24,
            margin: "20px 0 28px",
            flexWrap: "wrap",
          }}
        >
          <div>
            <p
              style={{
                margin: "0 0 10px",
                letterSpacing: "0.18em",
                textTransform: "uppercase",
                fontSize: "0.78rem",
                color: "#b14c1e",
              }}
            >
              Offline Annotation Viewer
            </p>
            <h1
              style={{
                margin: 0,
                fontSize: "clamp(1.8rem, 3.4vw, 2.8rem)",
                lineHeight: 1.06,
              }}
            >
              本地图片标注可视化工具
            </h1>
            <p
              style={{
                margin: "12px 0 0",
                maxWidth: 720,
                lineHeight: 1.7,
                color: "#5d6b73",
              }}
            >
              纯前端、纯本地、零依赖。拖拽图片和 TXT 标注文件，即可实时叠加查看
              YOLO 检测框和点标注。
            </p>
          </div>
          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: 10,
              justifyContent: "flex-end",
            }}
          >
            <Badge tone="safe">本地离线</Badge>
            <Badge>JPG / PNG</Badge>
            <Badge>TXT</Badge>
          </div>
        </header>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "minmax(0, 360px) minmax(0, 1fr)",
            gap: 24,
            alignItems: "start",
          }}
        >
          <aside style={{ display: "grid", gap: 20, minWidth: 0 }}>
            <Card>
              <CardHead title="文件导入" note="仅支持拖拽" />
              <Dropzone
                icon="IMG"
                title="图片拖拽区"
                hint="拖入 JPG 或 PNG 文件"
                detail={
                  imageError
                    ? imageError
                    : image
                      ? `${image.name} | ${image.width} x ${image.height}`
                      : "未加载图片"
                }
                state={imageError ? "error" : image ? "loaded" : "idle"}
                dragOver={imageDragOver}
                onDragOver={setImageDragOver}
                onDrop={handleImageFile}
              />
              <div style={{ height: 16 }} />
              <Dropzone
                icon="TXT"
                title="标注拖拽区"
                hint="拖入 TXT 标注文件"
                detail={
                  annError
                    ? annError
                    : annotationFileName
                      ? annotationFileName
                      : "未加载标注"
                }
                state={
                  annError ? "error" : annotationFileName ? "loaded" : "idle"
                }
                dragOver={annDragOver}
                onDragOver={setAnnDragOver}
                onDrop={handleAnnFile}
              />
            </Card>

            <Card>
              <CardHead
                title="当前状态"
                right={
                  <span
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      justifyContent: "center",
                      minWidth: 78,
                      padding: "8px 12px",
                      borderRadius: 999,
                      fontSize: "0.9rem",
                      fontWeight: 600,
                      background: STATUS_COLOR[status].bg,
                      color: STATUS_COLOR[status].fg,
                    }}
                  >
                    {STATUS_LABEL[status]}
                  </span>
                }
              />
              <div
                style={{
                  minHeight: 58,
                  padding: "14px 16px",
                  borderRadius: 18,
                  border: "1px solid transparent",
                  lineHeight: 1.6,
                  fontSize: "0.95rem",
                  background:
                    status === "ready"
                      ? "rgba(45,143,103,0.1)"
                      : status === "warn"
                        ? "rgba(182,122,19,0.1)"
                        : status === "error"
                          ? "rgba(178,65,52,0.1)"
                          : "rgba(255,255,255,0.6)",
                  borderColor:
                    status === "ready"
                      ? "rgba(45,143,103,0.2)"
                      : status === "warn"
                        ? "rgba(182,122,19,0.18)"
                        : status === "error"
                          ? "rgba(178,65,52,0.18)"
                          : "transparent",
                }}
              >
                {banner}
              </div>

              <dl
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
                  gap: 12,
                  margin: "18px 0",
                }}
              >
                <MetaItem
                  label="图片尺寸"
                  value={image ? `${image.width} × ${image.height}` : "-"}
                />
                <MetaItem label="标注数量" value={String(annotations.length)} />
                <MetaItem label="检测框" value={String(boxCount)} />
                <MetaItem label="点标注" value={String(pointCount)} />
              </dl>

              <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
                {formats.length === 0 ? (
                  <FormatTag>尚未识别标注格式</FormatTag>
                ) : (
                  formats.map((f) => <FormatTag key={f}>{f}</FormatTag>)
                )}
                {skipped > 0 && <FormatTag>跳过 {skipped} 行</FormatTag>}
              </div>
            </Card>
          </aside>

          <section
            style={{
              padding: 24,
              border: "1px solid rgba(87,66,44,0.14)",
              borderRadius: 28,
              background: "rgba(255,250,242,0.84)",
              boxShadow: "0 24px 60px rgba(58,37,18,0.12)",
              backdropFilter: "blur(16px)",
              minWidth: 0,
            }}
          >
            <div style={{ marginBottom: 18 }}>
              <p
                style={{
                  margin: "0 0 10px",
                  letterSpacing: "0.18em",
                  textTransform: "uppercase",
                  fontSize: "0.78rem",
                  color: "#b14c1e",
                }}
              >
                Canvas Preview
              </p>
              <h2 style={{ margin: 0 }}>图像与标注叠加预览</h2>
            </div>

            <div
              style={{
                padding: 18,
                borderRadius: 20,
                background:
                  "linear-gradient(180deg, rgba(251,248,242,0.86), rgba(241,233,220,0.72))",
                border: "1px solid rgba(87,66,44,0.08)",
              }}
            >
              <div
                ref={stageRef}
                style={{
                  position: "relative",
                  width: "100%",
                  minHeight: 520,
                  overflow: "auto",
                  borderRadius: 18,
                  background:
                    "linear-gradient(45deg, rgba(31,42,51,0.03) 25%, transparent 25%), linear-gradient(-45deg, rgba(31,42,51,0.03) 25%, transparent 25%), linear-gradient(45deg, transparent 75%, rgba(31,42,51,0.03) 75%), linear-gradient(-45deg, transparent 75%, rgba(31,42,51,0.03) 75%), #f8f4ec",
                  backgroundSize: "24px 24px",
                  backgroundPosition: "0 0, 0 12px, 12px -12px, -12px 0",
                }}
              >
                <canvas
                  ref={baseCanvasRef}
                  style={{
                    position: "absolute",
                    top: "50%",
                    left: "50%",
                    transform: "translate(-50%, -50%)",
                    display: image ? "block" : "none",
                  }}
                />
                <canvas
                  ref={overlayCanvasRef}
                  style={{
                    position: "absolute",
                    top: "50%",
                    left: "50%",
                    transform: "translate(-50%, -50%)",
                    display: image ? "block" : "none",
                  }}
                />
                {!image && (
                  <div
                    style={{
                      position: "absolute",
                      inset: 0,
                      display: "grid",
                      placeItems: "center",
                      padding: 24,
                    }}
                  >
                    <div
                      style={{
                        maxWidth: 420,
                        padding: "28px 24px",
                        textAlign: "center",
                        borderRadius: 24,
                        background: "rgba(255,255,255,0.72)",
                        border: "1px solid rgba(87,66,44,0.08)",
                        boxShadow: "0 14px 30px rgba(58,37,18,0.08)",
                      }}
                    >
                      <strong
                        style={{
                          display: "block",
                          marginBottom: 8,
                          fontSize: "1.05rem",
                        }}
                      >
                        拖入图片开始预览
                      </strong>
                      <p
                        style={{ margin: 0, color: "#5d6b73", lineHeight: 1.7 }}
                      >
                        图片绘制在底层画布，标注绘制在上层画布，重复加载会自动刷新。
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

function Card({ children }: { children: React.ReactNode }): JSX.Element {
  return (
    <section
      style={{
        padding: 20,
        border: "1px solid rgba(87,66,44,0.14)",
        borderRadius: 28,
        background: "rgba(255,250,242,0.84)",
        boxShadow: "0 24px 60px rgba(58,37,18,0.12)",
        backdropFilter: "blur(16px)",
      }}
    >
      {children}
    </section>
  );
}

function CardHead({
  title,
  note,
  right,
}: {
  title: string;
  note?: string;
  right?: React.ReactNode;
}): JSX.Element {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 16,
        marginBottom: 18,
      }}
    >
      <h2 style={{ margin: 0 }}>{title}</h2>
      {right ??
        (note && (
          <span style={{ color: "#5d6b73", fontSize: "0.9rem" }}>{note}</span>
        ))}
    </div>
  );
}

function Badge({
  children,
  tone,
}: {
  children: React.ReactNode;
  tone?: "safe";
}): JSX.Element {
  return (
    <span
      style={{
        padding: "10px 14px",
        borderRadius: 999,
        background:
          tone === "safe" ? "rgba(45,143,103,0.12)" : "rgba(255,255,255,0.72)",
        color: tone === "safe" ? "#166447" : "inherit",
        border:
          tone === "safe"
            ? "1px solid transparent"
            : "1px solid rgba(87,66,44,0.1)",
        fontSize: "0.92rem",
        whiteSpace: "nowrap",
      }}
    >
      {children}
    </span>
  );
}

function MetaItem({
  label,
  value,
}: {
  label: string;
  value: string;
}): JSX.Element {
  return (
    <div
      style={{
        padding: 14,
        borderRadius: 12,
        background: "rgba(255,255,255,0.62)",
        border: "1px solid rgba(87,66,44,0.08)",
      }}
    >
      <dt style={{ marginBottom: 8, color: "#5d6b73", fontSize: "0.9rem" }}>
        {label}
      </dt>
      <dd style={{ margin: 0, fontSize: "1.15rem", fontWeight: 700 }}>
        {value}
      </dd>
    </div>
  );
}

function FormatTag({ children }: { children: React.ReactNode }): JSX.Element {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        padding: "8px 12px",
        borderRadius: 999,
        background: "rgba(31,42,51,0.07)",
        fontSize: "0.9rem",
      }}
    >
      {children}
    </span>
  );
}

function Dropzone({
  icon,
  title,
  hint,
  detail,
  state,
  dragOver,
  onDragOver,
  onDrop,
}: {
  icon: string;
  title: string;
  hint: string;
  detail: string;
  state: "idle" | "loaded" | "error";
  dragOver: boolean;
  onDragOver: (over: boolean) => void;
  onDrop: (file: File | null) => void;
}): JSX.Element {
  const borderColor =
    state === "loaded"
      ? "rgba(45,143,103,0.55)"
      : state === "error"
        ? "rgba(178,65,52,0.62)"
        : dragOver
          ? "rgba(212,107,54,0.9)"
          : "rgba(180,115,78,0.45)";
  const borderStyle =
    state === "loaded" || state === "error" ? "solid" : "dashed";

  return (
    <div
      onDragEnter={(e) => {
        e.preventDefault();
        onDragOver(true);
      }}
      onDragOver={(e) => {
        e.preventDefault();
        onDragOver(true);
      }}
      onDragLeave={() => onDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        onDragOver(false);
        const f = e.dataTransfer?.files?.[0] ?? null;
        onDrop(f);
      }}
      style={{
        position: "relative",
        display: "grid",
        gap: 10,
        padding: 18,
        minHeight: 160,
        borderRadius: 18,
        border: `1px ${borderStyle} ${borderColor}`,
        background:
          "linear-gradient(180deg, rgba(255,255,255,0.78), rgba(249,242,230,0.72))",
        transition:
          "transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease",
        transform: dragOver ? "translateY(-2px)" : "none",
        boxShadow: dragOver ? "0 18px 36px rgba(212,107,54,0.16)" : "none",
      }}
    >
      <div
        style={{
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          width: 54,
          height: 54,
          borderRadius: 16,
          background: "rgba(212,107,54,0.14)",
          color: "#b14c1e",
          fontWeight: 700,
          letterSpacing: "0.08em",
        }}
      >
        {icon}
      </div>
      <h3 style={{ margin: 0 }}>{title}</h3>
      <p style={{ margin: 0, color: "#5d6b73" }}>{hint}</p>
      <small style={{ margin: 0, color: "#5d6b73" }}>{detail}</small>
    </div>
  );
}
