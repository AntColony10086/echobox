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
import type { ImageItem, ImageListResponse } from "../types/annotation";
import type { Project } from "../types/project";

type Mode = "select" | "exemplar";

function Kbd({ children }: { children: React.ReactNode }): JSX.Element {
  return (
    <kbd
      style={{
        fontSize: 10,
        padding: "1px 5px",
        border: "1px solid #cbd5e0",
        borderRadius: 3,
        background: "white",
        color: "#2d3748",
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

  // Use a callback-ref so measurement re-fires whenever the <main> remounts
  // (e.g. after the loading-state early-return swaps to the real layout).
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
      // disconnect previous observer (when remounting)
      roRef.current?.disconnect();
      mainElRef.current = node;
      if (!node) return;
      // measure synchronously now
      measure(node);
      // observe future size changes
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

  // Initial load — auto-open setup modal if project is still in draft.
  useEffect(() => {
    if (!pid) return;
    refetchProject().then((p) => {
      if (p && p.status === "draft") setSetupOpen(true);
    });
    refetchImages();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pid]);

  // window resize as last-resort backup (ResizeObserver handles most cases)
  useEffect(() => {
    const onResize = (): void => {
      if (mainElRef.current) measure(mainElRef.current);
    };
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, [measure]);

  // Reset zoom when switching to a different image
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

  if (!pid) return <div style={{ padding: 24 }}>missing project_id</div>;
  if (!project) return <div style={{ padding: 24 }}>loading…</div>;

  const hasPending = ann.annotations.some((a) => a.source === "geco2_pending");
  const hasSelection = selectedAnnId != null;

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "220px 1fr 280px",
        height: "100vh",
      }}
    >
      <aside
        style={{
          background: "white",
          color: "#2d3748",
          overflow: "hidden",
          display: "flex",
          flexDirection: "column",
          minHeight: 0,
          borderRight: "1px solid #e2e8f0",
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
          background: "#edf2f7",
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
            height: 40,
            background: "white",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "0 12px",
            gap: 12,
            color: "#2d3748",
            fontSize: 12,
            borderBottom: "1px solid #e2e8f0",
            zIndex: 5,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontWeight: 700 }}>{project.name}</span>
            <span style={{ color: "#a0aec0" }}>
              · {project.status} · #{project.id}
            </span>
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
              top: 40,
              left: 0,
              right: 0,
              bottom: 40,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#718096",
              fontSize: 14,
              padding: 24,
              textAlign: "center",
            }}
          >
            {project.status === "draft" ? (
              <div>
                项目尚未配置完成
                <br />
                点击右上角 <b style={{ color: "#2d3748" }}>配置项目</b> 或{" "}
                <b style={{ color: "#2d3748" }}>与 Agent 对话</b> 完成设置
              </div>
            ) : (
              <div>暂无图片</div>
            )}
          </div>
        )}
        {currentImage && containerSize.w > 0 && containerSize.h > 0 && (
          <div
            style={{
              position: "absolute",
              top: 40,
              left: 0,
              right: 0,
              bottom: 40,
              overflow: "hidden",
            }}
          >
            <ImageCanvas
              src={imageFileUrl(currentImage.id)}
              imageWidth={currentImage.width}
              imageHeight={currentImage.height}
              containerWidth={containerSize.w}
              containerHeight={containerSize.h - 80}
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
            height: 40,
            background: "white",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "0 12px",
            gap: 12,
            color: "#2d3748",
            fontSize: 12,
            borderTop: "1px solid #e2e8f0",
            zIndex: 5,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <Button size="sm" variant="ghost" onClick={() => navigateImage(-1)}>
              ← 上一张
            </Button>
            <span
              style={{
                minWidth: 140,
                textAlign: "center",
                color: "#4a5568",
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
          <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <span style={{ color: "#a0aec0", marginRight: 4 }}>缩放</span>
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
                minWidth: 48,
                textAlign: "center",
                color: "#2d3748",
                fontWeight: 600,
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
          background: "#f7fafc",
          color: "#2d3748",
          padding: 12,
          overflowY: "auto",
          borderLeft: "1px solid #e2e8f0",
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
            <span style={{ fontWeight: 600, color: "#2d3748" }}>
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
              accentColor: "#3182ce",
              display: "block",
            }}
          />
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              fontSize: 10,
              color: "#a0aec0",
              marginTop: 4,
            }}
          >
            <span>更宽松</span>
            <span>更严格</span>
          </div>
          <div style={{ fontSize: 11, color: "#718096", marginTop: 6 }}>
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
                  style={{ color: selectedAnn.label.color, fontWeight: 600 }}
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
                        padding: "6px 8px",
                        border: `1px solid ${isCurrent ? l.color : "#cbd5e0"}`,
                        borderRadius: 4,
                        background: isCurrent ? `${l.color}1a` : "white",
                        color: "#2d3748",
                        fontSize: 12,
                        fontWeight: isCurrent ? 600 : 400,
                        cursor: isCurrent ? "default" : "pointer",
                      }}
                    >
                      <span
                        style={{
                          width: 10,
                          height: 10,
                          borderRadius: 2,
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
              color: "#4a5568",
              lineHeight: 1.7,
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
