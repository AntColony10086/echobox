import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { listImages, imageFileUrl } from "../api/images";
import { getProject } from "../api/projects";
import { BBoxLayer } from "../components/canvas/BBoxLayer";
import { ExemplarTool } from "../components/canvas/ExemplarTool";
import { ImageCanvas } from "../components/canvas/ImageCanvas";
import { ChatModal } from "../components/annotate/ChatModal";
import { ClassPicker } from "../components/annotate/ClassPicker";
import { ImageList } from "../components/annotate/ImageList";
import { SaveIndicator } from "../components/annotate/SaveIndicator";
import { SetupModal } from "../components/annotate/SetupModal";
import { Toolbar } from "../components/annotate/Toolbar";
import { Button } from "../components/ui/Button";
import { Panel } from "../components/ui/Panel";
import { useAnnotations } from "../hooks/useAnnotations";
import { useSaveState } from "../hooks/useSaveState";
import { CANVAS_BG, COLORS, FONT_STACK, PAGE_BG } from "../theme";
import type { ImageItem, ImageListResponse } from "../types/annotation";
import type { Project } from "../types/project";

type Mode = "select" | "exemplar";

function Kbd({ children }: { children: React.ReactNode }): JSX.Element {
  return (
    <kbd
      style={{
        fontSize: 10,
        padding: "1px 6px",
        border: `1px solid ${COLORS.cardBorder}`,
        borderRadius: 4,
        background: "rgba(255,255,255,0.85)",
        color: COLORS.ink,
        fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
      }}
    >
      {children}
    </kbd>
  );
}

export function AnnotatePage(): JSX.Element {
  const [searchParams] = useSearchParams();
  const pid = Number(searchParams.get("project_id"));

  const [project, setProject] = useState<Project | null>(null);
  const [imageList, setImageList] = useState<ImageListResponse | null>(null);
  const [currentImage, setCurrentImage] = useState<ImageItem | null>(null);
  const [selectedLabelId, setSelectedLabelId] = useState<number | null>(null);
  const [selectedAnnId, setSelectedAnnId] = useState<number | null>(null);
  const [mode, setMode] = useState<Mode>("exemplar");
  const [zoom, setZoom] = useState<number>(1);
  const [scoreThreshold, setScoreThreshold] = useState<number>(0.25);
  const [setupOpen, setSetupOpen] = useState<boolean>(false);
  const [chatOpen, setChatOpen] = useState<boolean>(false);

  const mainElRef = useRef<HTMLElement | null>(null);
  const roRef = useRef<ResizeObserver | null>(null);
  const [containerSize, setContainerSize] = useState({ w: 0, h: 0 });

  const measure = useCallback((el: HTMLElement | null): void => {
    if (!el) return;
    const r = el.getBoundingClientRect();
    setContainerSize((prev) =>
      prev.w === r.width && prev.h === r.height
        ? prev
        : { w: r.width, h: r.height },
    );
  }, []);

  const containerRef = useCallback(
    (node: HTMLElement | null): void => {
      roRef.current?.disconnect();
      mainElRef.current = node;
      if (!node) return;
      measure(node);
      const ro = new ResizeObserver(() => measure(node));
      ro.observe(node);
      roRef.current = ro;
    },
    [measure],
  );

  const ann = useAnnotations(pid, currentImage?.id ?? null);
  const save = useSaveState();

  const refetchProject = useCallback(async (): Promise<Project | null> => {
    if (!pid) return null;
    const p = await getProject(pid);
    setProject(p);
    if (p.labels.length > 0 && selectedLabelId == null) {
      setSelectedLabelId(
        (p.labels as { id: number; name: string; color: string }[])[0].id,
      );
    }
    return p;
  }, [pid, selectedLabelId]);

  const refetchImages = useCallback((): void => {
    if (!pid) return;
    listImages(pid).then((data) => {
      setImageList(data);
      if (data.items.length > 0 && !currentImage) {
        setCurrentImage(data.items[0]);
      }
    });
  }, [pid, currentImage]);

  useEffect(() => {
    if (!pid) return;
    refetchProject().then((p) => {
      if (p && p.status === "draft") setSetupOpen(true);
    });
    refetchImages();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pid]);

  useEffect(() => {
    const onResize = (): void => {
      if (mainElRef.current) measure(mainElRef.current);
    };
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, [measure]);

  useEffect(() => {
    setZoom(1);
  }, [currentImage?.id]);

  useEffect(() => {
    const handler = (e: KeyboardEvent): void => {
      if ((e.target as HTMLElement).tagName === "INPUT") return;
      if (e.key === "e" || e.key === "E") setMode("exemplar");
      else if (e.key === "v" || e.key === "V") setMode("select");
      else if (
        (e.key === "Delete" || e.key === "d" || e.key === "D") &&
        selectedAnnId
      ) {
        save.wrap(() => ann.remove(selectedAnnId));
        setSelectedAnnId(null);
      } else if ((e.key === "a" || e.key === "A") && selectedAnnId) {
        const a = ann.annotations.find((x) => x.id === selectedAnnId);
        if (a) save.wrap(() => ann.accept(a.id, a.version));
      } else if (e.key === "ArrowRight") {
        navigateImage(+1);
      } else if (e.key === "ArrowLeft") {
        navigateImage(-1);
      } else if (e.key === "+" || e.key === "=") {
        setZoom((z) => Math.min(8, +(z * 1.25).toFixed(3)));
      } else if (e.key === "-" || e.key === "_") {
        setZoom((z) => Math.max(0.25, +(z / 1.25).toFixed(3)));
      } else if (e.key === "0") {
        setZoom(1);
      } else if (project && /^[1-9]$/.test(e.key)) {
        const idx = parseInt(e.key, 10) - 1;
        const labels = project.labels as {
          id: number;
          name: string;
          color: string;
        }[];
        if (idx < labels.length) setSelectedLabelId(labels[idx].id);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  });

  const navigateImage = (delta: number): void => {
    if (!imageList || !currentImage) return;
    const i = imageList.items.findIndex((x) => x.id === currentImage.id);
    const next =
      imageList.items[
        Math.max(0, Math.min(imageList.items.length - 1, i + delta))
      ];
    if (next) setCurrentImage(next);
  };

  const onExemplarDrawn = async (
    bbox: [number, number, number, number],
  ): Promise<void> => {
    if (!selectedLabelId) {
      alert("先选一个类别");
      return;
    }
    await save.wrap(() =>
      ann.drawExemplar(selectedLabelId, bbox, scoreThreshold),
    );
    setMode("select");
  };

  const onBboxChange = async (
    id: number,
    bbox: [number, number, number, number],
  ): Promise<void> => {
    const a = ann.annotations.find((x) => x.id === id);
    if (!a) return;
    await save.wrap(() => ann.updateBbox(id, bbox, a.version));
  };

  if (!pid)
    return (
      <div
        style={{
          padding: 24,
          fontFamily: FONT_STACK,
          color: COLORS.ink,
          background: PAGE_BG,
          minHeight: "100vh",
        }}
      >
        missing project_id
      </div>
    );
  if (!project)
    return (
      <div
        style={{
          padding: 24,
          fontFamily: FONT_STACK,
          color: COLORS.muted,
          background: PAGE_BG,
          minHeight: "100vh",
        }}
      >
        loading…
      </div>
    );

  const hasPending = ann.annotations.some((a) => a.source === "geco2_pending");
  const hasSelection = selectedAnnId != null;

  const chromeBg = "rgba(255,250,242,0.86)";
  const chromeBorder = `1px solid ${COLORS.cardBorder}`;

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "240px 1fr 300px",
        height: "100vh",
        background: PAGE_BG,
        color: COLORS.ink,
        fontFamily: FONT_STACK,
      }}
    >
      <aside
        style={{
          background: chromeBg,
          backdropFilter: "blur(16px)",
          color: COLORS.ink,
          overflow: "hidden",
          display: "flex",
          flexDirection: "column",
          minHeight: 0,
          borderRight: chromeBorder,
        }}
      >
        <ImageList
          data={
            imageList ?? {
              total: 0,
              items: [],
              progress: {
                train: { total: 0, annotated: 0 },
                val: { total: 0, annotated: 0 },
                test: { total: 0, annotated: 0 },
              },
            }
          }
          currentId={currentImage?.id ?? null}
          onSelect={setCurrentImage}
        />
      </aside>

      <main
        ref={containerRef}
        style={{
          position: "relative",
          overflow: "hidden",
          background: CANVAS_BG,
          backgroundSize: "24px 24px",
          backgroundPosition: "0 0, 0 12px, 12px -12px, -12px 0",
          minWidth: 0,
          minHeight: 0,
        }}
      >
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            height: 48,
            background: chromeBg,
            backdropFilter: "blur(16px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "0 16px",
            gap: 12,
            color: COLORS.ink,
            fontSize: 12,
            borderBottom: chromeBorder,
            zIndex: 5,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ fontWeight: 700, fontSize: 14 }}>
              {project.name}
            </span>
            <span
              style={{
                padding: "2px 10px",
                borderRadius: 999,
                fontSize: 11,
                fontWeight: 600,
                background:
                  project.status === "ready"
                    ? "rgba(45,143,103,0.14)"
                    : "rgba(182,122,19,0.14)",
                color:
                  project.status === "ready"
                    ? COLORS.successDark
                    : COLORS.warnDark,
              }}
            >
              {project.status}
            </span>
            <span style={{ color: COLORS.faint }}>#{project.id}</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSetupOpen(true)}
            >
              配置项目
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => setChatOpen(true)}
            >
              与 Agent 对话
            </Button>
          </div>
        </div>
        {!currentImage && (
          <div
            style={{
              position: "absolute",
              top: 48,
              left: 0,
              right: 0,
              bottom: 48,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: COLORS.muted,
              fontSize: 14,
              padding: 24,
              textAlign: "center",
            }}
          >
            <div
              style={{
                maxWidth: 420,
                padding: "28px 24px",
                background: COLORS.cardBg,
                border: chromeBorder,
                borderRadius: 24,
                boxShadow: COLORS.cardShadow,
                backdropFilter: "blur(16px)",
                lineHeight: 1.7,
              }}
            >
              {project.status === "draft" ? (
                <div>
                  项目尚未配置完成
                  <br />
                  点击右上角 <b style={{ color: COLORS.ink }}>
                    配置项目
                  </b> 或 <b style={{ color: COLORS.ink }}>与 Agent 对话</b>{" "}
                  完成设置
                </div>
              ) : (
                <div>暂无图片</div>
              )}
            </div>
          </div>
        )}
        {currentImage && containerSize.w > 0 && containerSize.h > 0 && (
          <div
            style={{
              position: "absolute",
              top: 48,
              left: 0,
              right: 0,
              bottom: 48,
              overflow: "hidden",
            }}
          >
            <ImageCanvas
              src={imageFileUrl(currentImage.id)}
              imageWidth={currentImage.width}
              imageHeight={currentImage.height}
              containerWidth={containerSize.w}
              containerHeight={containerSize.h - 96}
              zoom={zoom}
            >
              {(ctx) => (
                <>
                  <BBoxLayer
                    annotations={ann.annotations}
                    selectedId={selectedAnnId}
                    scale={ctx.scale}
                    offsetX={ctx.offsetX}
                    offsetY={ctx.offsetY}
                    onSelect={(id) => setSelectedAnnId(id)}
                    onChange={(id, bbox) => onBboxChange(id, bbox)}
                  />
                  <ExemplarTool
                    active={mode === "exemplar"}
                    scale={ctx.scale}
                    offsetX={ctx.offsetX}
                    offsetY={ctx.offsetY}
                    onDrawn={onExemplarDrawn}
                  />
                </>
              )}
            </ImageCanvas>
          </div>
        )}
        <div
          style={{
            position: "absolute",
            bottom: 0,
            left: 0,
            right: 0,
            height: 48,
            background: chromeBg,
            backdropFilter: "blur(16px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "0 16px",
            gap: 12,
            color: COLORS.ink,
            fontSize: 12,
            borderTop: chromeBorder,
            zIndex: 5,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Button size="sm" variant="ghost" onClick={() => navigateImage(-1)}>
              ← 上一张
            </Button>
            <span
              style={{
                minWidth: 160,
                textAlign: "center",
                color: COLORS.muted,
                fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
                fontSize: 11,
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {currentImage?.filename ?? "-"}
            </span>
            <Button size="sm" variant="ghost" onClick={() => navigateImage(+1)}>
              下一张 →
            </Button>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{ color: COLORS.faint, marginRight: 4 }}>缩放</span>
            <Button
              size="sm"
              variant="ghost"
              onClick={() =>
                setZoom((z) => Math.max(0.25, +(z / 1.25).toFixed(3)))
              }
            >
              −
            </Button>
            <span
              style={{
                minWidth: 52,
                textAlign: "center",
                color: COLORS.ink,
                fontWeight: 700,
              }}
            >
              {Math.round(zoom * 100)}%
            </span>
            <Button
              size="sm"
              variant="ghost"
              onClick={() =>
                setZoom((z) => Math.min(8, +(z * 1.25).toFixed(3)))
              }
            >
              +
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setZoom(1)}>
              复原
            </Button>
          </div>
        </div>
      </main>

      <aside
        style={{
          background: chromeBg,
          backdropFilter: "blur(16px)",
          color: COLORS.ink,
          padding: 14,
          overflowY: "auto",
          borderLeft: chromeBorder,
        }}
      >
        <ClassPicker
          pid={pid}
          labels={
            project.labels as { id: number; name: string; color: string }[]
          }
          selectedId={selectedLabelId}
          onSelect={setSelectedLabelId}
          onLabelsChanged={() => getProject(pid).then(setProject)}
        />
        <Toolbar
          mode={mode}
          onModeChange={setMode}
          onAcceptAll={() => save.wrap(ann.acceptAll).then(refetchImages)}
          onRejectAll={() => save.wrap(ann.rejectAll).then(refetchImages)}
          onDelete={() => {
            if (selectedAnnId) {
              save.wrap(() => ann.remove(selectedAnnId)).then(refetchImages);
              setSelectedAnnId(null);
            }
          }}
          hasSelection={hasSelection}
          hasPending={hasPending}
          predictBusy={ann.predictBusy}
        />

        <Panel
          title="GECO2 阈值"
          trailing={
            <span style={{ fontWeight: 700, color: COLORS.ink }}>
              {scoreThreshold.toFixed(2)}
            </span>
          }
        >
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={scoreThreshold}
            onChange={(e) => setScoreThreshold(parseFloat(e.target.value))}
            style={{
              width: "100%",
              accentColor: COLORS.accent,
              display: "block",
            }}
          />
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              fontSize: 10,
              color: COLORS.faint,
              marginTop: 4,
            }}
          >
            <span>更宽松</span>
            <span>更严格</span>
          </div>
          <div style={{ fontSize: 11, color: COLORS.muted, marginTop: 6 }}>
            下次画框时生效
          </div>
        </Panel>

        {(() => {
          const selectedAnn = ann.annotations.find(
            (a) => a.id === selectedAnnId,
          );
          if (!selectedAnn) return null;
          const labels = project.labels as {
            id: number;
            name: string;
            color: string;
          }[];
          return (
            <Panel
              title="改选中框的类别"
              trailing={
                <span
                  style={{ color: selectedAnn.label.color, fontWeight: 700 }}
                >
                  {selectedAnn.label.name}
                </span>
              }
            >
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fill, minmax(96px, 1fr))",
                  gap: 6,
                }}
              >
                {labels.map((l) => {
                  const isCurrent = selectedAnn.label.id === l.id;
                  return (
                    <button
                      key={l.id}
                      disabled={isCurrent || save.state === "saving"}
                      onClick={() =>
                        save
                          .wrap(() =>
                            ann.changeLabel(
                              selectedAnn.id,
                              l.id,
                              selectedAnn.version,
                            ),
                          )
                          .then(refetchImages)
                      }
                      title={isCurrent ? "已经是这个类别" : `改成 ${l.name}`}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 6,
                        padding: "6px 10px",
                        border: `1px solid ${
                          isCurrent ? l.color : COLORS.cardBorder
                        }`,
                        borderRadius: 999,
                        background: isCurrent
                          ? `${l.color}1f`
                          : "rgba(255,255,255,0.7)",
                        color: COLORS.ink,
                        fontSize: 12,
                        fontWeight: isCurrent ? 700 : 500,
                        cursor: isCurrent ? "default" : "pointer",
                        fontFamily: FONT_STACK,
                      }}
                    >
                      <span
                        style={{
                          width: 10,
                          height: 10,
                          borderRadius: 3,
                          background: l.color,
                          flexShrink: 0,
                        }}
                      />
                      <span
                        style={{
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {l.name}
                      </span>
                    </button>
                  );
                })}
              </div>
            </Panel>
          );
        })()}

        <Panel title="编辑提示">
          <ul
            style={{
              margin: 0,
              padding: 0,
              listStyle: "none",
              fontSize: 12,
              color: COLORS.muted,
              lineHeight: 1.8,
            }}
          >
            <li>· 点击选中后拖动整框可移动</li>
            <li>· 拖四角 / 四边手柄调整大小</li>
            <li>
              · 按 <Kbd>Del</Kbd> 或 <Kbd>D</Kbd> 删除
            </li>
            <li>
              · 按 <Kbd>A</Kbd> 接受待审核框
            </li>
          </ul>
        </Panel>

        <SaveIndicator
          state={save.state}
          lastError={save.error}
          lastElapsedMs={ann.lastElapsedMs}
        />
      </aside>

      {setupOpen && (
        <SetupModal
          project={project}
          onUpdated={setProject}
          onRefetch={refetchProject}
          onReady={refetchImages}
          onClose={() => {
            setSetupOpen(false);
            refetchProject();
            refetchImages();
          }}
        />
      )}
      {chatOpen && (
        <ChatModal
          pid={pid}
          initialMessages={project.messages ?? []}
          onClose={() => {
            setChatOpen(false);
            refetchProject();
            refetchImages();
          }}
          onSync={() => {
            refetchProject();
            refetchImages();
          }}
        />
      )}
    </div>
  );
}
