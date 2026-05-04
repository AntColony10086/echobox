import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  createProject,
  deleteProject,
  listProjects,
  type ProjectSummary,
} from "../api/projects";
import { Modal } from "../components/ui/Modal";
import { ModeSwitcher } from "../components/ModeSwitcher";

const FONT_STACK = "'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif";
const PAGE_BG =
  "radial-gradient(circle at top left, rgba(212,107,54,0.14), transparent 28%), radial-gradient(circle at 100% 0, rgba(45,143,103,0.12), transparent 24%), linear-gradient(135deg, #f4efe6, #f7f2ea 45%, #e6dcc8)";
const CARD_BG = "rgba(255,250,242,0.84)";
const CARD_BORDER = "1px solid rgba(87,66,44,0.14)";
const CARD_SHADOW = "0 24px 60px rgba(58,37,18,0.12)";
const ACCENT = "#d46b36";
const ACCENT_STRONG = "#b14c1e";
const SUCCESS = "#2d8f67";
const SUCCESS_DARK = "#166447";
const WARN_DARK = "#865d10";
const DANGER = "#b24134";
const INK = "#1f2a33";
const MUTED = "#5d6b73";

export function HomePage(): JSX.Element {
  const [projects, setProjects] = useState<ProjectSummary[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const navigate = useNavigate();

  const refetch = (): void => {
    listProjects()
      .then(setProjects)
      .catch((e) => setLoadError(String(e)));
  };

  useEffect(() => {
    refetch();
  }, []);

  const handleDelete = async (p: ProjectSummary): Promise<void> => {
    const confirmed = window.confirm(
      `确定删除项目 "${p.name}" (#${p.id})?\n\n` +
        `这会删除所有标注、聊天记录、导出文件。源图片文件夹不受影响。\n` +
        `此操作不可撤销。`,
    );
    if (!confirmed) return;
    try {
      await deleteProject(p.id);
      refetch();
    } catch (e) {
      alert(`删除失败：${String(e)}`);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: PAGE_BG,
        color: INK,
        fontFamily: FONT_STACK,
      }}
    >
      <div
        style={{ maxWidth: 960, margin: "0 auto", padding: "28px 24px 48px" }}
      >
        <ModeSwitcher current="projects" />

        <header
          style={{
            display: "flex",
            alignItems: "flex-end",
            justifyContent: "space-between",
            margin: "20px 0 28px",
            gap: 24,
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
                color: ACCENT_STRONG,
              }}
            >
              Project Workbench
            </p>
            <h1
              style={{
                margin: 0,
                fontSize: "clamp(1.8rem, 3.4vw, 2.8rem)",
                lineHeight: 1.06,
              }}
            >
              echobox
            </h1>
            <p style={{ margin: "12px 0 0", color: MUTED, lineHeight: 1.7 }}>
              多模态智能标注 Agent 平台
            </p>
          </div>
          <button
            onClick={() => setCreateOpen(true)}
            style={{
              padding: "12px 22px",
              background: `linear-gradient(135deg, ${ACCENT}, ${ACCENT_STRONG})`,
              color: "white",
              border: "none",
              borderRadius: 999,
              cursor: "pointer",
              fontSize: 14,
              fontWeight: 600,
              boxShadow: "0 12px 28px rgba(212,107,54,0.28)",
              fontFamily: FONT_STACK,
            }}
          >
            + 新建项目
          </button>
        </header>

        <section
          style={{
            padding: 24,
            border: CARD_BORDER,
            borderRadius: 28,
            background: CARD_BG,
            boxShadow: CARD_SHADOW,
            backdropFilter: "blur(16px)",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: 18,
              gap: 16,
            }}
          >
            <h2 style={{ margin: 0, fontSize: "1.15rem" }}>已有项目</h2>
            <span style={{ color: MUTED, fontSize: "0.9rem" }}>
              {projects ? `${projects.length} 个项目` : ""}
            </span>
          </div>

          {loadError && (
            <div
              style={{
                padding: "14px 16px",
                background: "rgba(178,65,52,0.1)",
                color: "#973328",
                border: "1px solid rgba(178,65,52,0.18)",
                borderRadius: 18,
                fontSize: 13,
                marginBottom: 12,
              }}
            >
              {loadError}
            </div>
          )}

          {projects === null && !loadError && (
            <div style={{ color: MUTED, fontSize: 13, padding: "8px 4px" }}>
              加载中…
            </div>
          )}

          {projects && projects.length === 0 && (
            <div
              style={{
                padding: 28,
                border: "1px dashed rgba(180,115,78,0.45)",
                background: "rgba(255,255,255,0.6)",
                borderRadius: 18,
                textAlign: "center",
                color: MUTED,
                fontSize: 13,
              }}
            >
              还没有项目，点击右上角「新建项目」开始
            </div>
          )}

          {projects && projects.length > 0 && (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {projects.map((p) => (
                <ProjectRow
                  key={p.id}
                  project={p}
                  onOpen={() => navigate(`/annotate?project_id=${p.id}`)}
                  onDelete={() => handleDelete(p)}
                />
              ))}
            </div>
          )}
        </section>
      </div>

      {createOpen && (
        <CreateProjectModal
          onClose={() => setCreateOpen(false)}
          onCreated={(pid) => navigate(`/annotate?project_id=${pid}`)}
        />
      )}
    </div>
  );
}

function statusToken(status: string): {
  label: string;
  bg: string;
  fg: string;
} {
  if (status === "ready") {
    return { label: status, bg: "rgba(45,143,103,0.14)", fg: SUCCESS_DARK };
  }
  if (status === "draft") {
    return { label: status, bg: "rgba(182,122,19,0.14)", fg: WARN_DARK };
  }
  return { label: status, bg: "rgba(93,107,115,0.12)", fg: "#47545c" };
}

function ProjectRow({
  project,
  onOpen,
  onDelete,
}: {
  project: ProjectSummary;
  onOpen: () => void;
  onDelete: () => void;
}): JSX.Element {
  const tok = statusToken(project.status);
  return (
    <div
      onClick={onOpen}
      style={{
        padding: 16,
        background: "rgba(255,255,255,0.62)",
        borderRadius: 18,
        cursor: "pointer",
        border: "1px solid rgba(87,66,44,0.08)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 12,
        transition:
          "transform 160ms ease, border-color 160ms ease, box-shadow 160ms ease",
      }}
      onMouseEnter={(e) => {
        const el = e.currentTarget as HTMLElement;
        el.style.borderColor = "rgba(212,107,54,0.55)";
        el.style.boxShadow = "0 14px 30px rgba(58,37,18,0.08)";
        el.style.transform = "translateY(-1px)";
      }}
      onMouseLeave={(e) => {
        const el = e.currentTarget as HTMLElement;
        el.style.borderColor = "rgba(87,66,44,0.08)";
        el.style.boxShadow = "none";
        el.style.transform = "none";
      }}
    >
      <div style={{ minWidth: 0, flex: 1 }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            marginBottom: 6,
            flexWrap: "wrap",
          }}
        >
          <span style={{ fontSize: 15, fontWeight: 700, color: INK }}>
            {project.name}
          </span>
          <span style={{ fontSize: 11, color: "#a0a8b0" }}>#{project.id}</span>
          <span
            style={{
              fontSize: 11,
              padding: "2px 10px",
              borderRadius: 999,
              background: tok.bg,
              color: tok.fg,
              fontWeight: 600,
            }}
          >
            {tok.label}
          </span>
        </div>
        <div
          style={{
            fontSize: 11,
            color: MUTED,
            fontFamily: "ui-monospace, 'SF Mono', Menlo, monospace",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {project.source_folder || "(未设置文件夹)"}
        </div>
      </div>
      <div
        style={{
          fontSize: 11,
          color: MUTED,
          textAlign: "right",
          flexShrink: 0,
        }}
      >
        <div>
          {project.image_count} 图 · {project.label_count} 类
        </div>
        {project.updated_at && (
          <div style={{ marginTop: 2 }}>
            {new Date(project.updated_at).toLocaleString()}
          </div>
        )}
      </div>
      <button
        onClick={(e) => {
          e.stopPropagation();
          onDelete();
        }}
        title="删除项目"
        aria-label="删除项目"
        style={{
          flexShrink: 0,
          width: 30,
          height: 30,
          padding: 0,
          background: "transparent",
          color: "#a0a8b0",
          border: "1px solid rgba(87,66,44,0.14)",
          borderRadius: 999,
          cursor: "pointer",
          fontSize: 16,
          lineHeight: 1,
        }}
        onMouseEnter={(e) => {
          const el = e.currentTarget as HTMLElement;
          el.style.background = "rgba(178,65,52,0.1)";
          el.style.borderColor = "rgba(178,65,52,0.45)";
          el.style.color = DANGER;
        }}
        onMouseLeave={(e) => {
          const el = e.currentTarget as HTMLElement;
          el.style.background = "transparent";
          el.style.borderColor = "rgba(87,66,44,0.14)";
          el.style.color = "#a0a8b0";
        }}
      >
        ×
      </button>
    </div>
  );
}

function CreateProjectModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: (pid: number) => void;
}): JSX.Element {
  const [folder, setFolder] = useState("");
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (): Promise<void> => {
    if (!folder.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const project = await createProject({
        source_folder: folder.trim(),
        name: name.trim() || undefined,
      });
      onCreated(project.id);
    } catch (e: unknown) {
      const msg =
        (e as { response?: { data?: { error?: { message?: string } } } })
          .response?.data?.error?.message ?? String(e);
      setError(msg);
    } finally {
      setBusy(false);
    }
  };

  const inputStyle = {
    width: "100%",
    padding: "10px 12px",
    fontSize: 13,
    border: "1px solid rgba(87,66,44,0.2)",
    borderRadius: 10,
    boxSizing: "border-box" as const,
    background: "rgba(255,255,255,0.85)",
    fontFamily: FONT_STACK,
    color: INK,
  };

  return (
    <Modal title="新建标注项目" onClose={onClose} width={520}>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 14,
          fontFamily: FONT_STACK,
        }}
      >
        <div>
          <label
            style={{
              display: "block",
              fontSize: 12,
              color: MUTED,
              marginBottom: 6,
              fontWeight: 600,
            }}
          >
            图片文件夹（绝对路径）
            <span style={{ color: DANGER }}> *</span>
          </label>
          <input
            type="text"
            value={folder}
            onChange={(e) => setFolder(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && folder.trim() && !busy) submit();
            }}
            placeholder="/abs/path/to/images"
            disabled={busy}
            spellCheck={false}
            autoFocus
            style={{
              ...inputStyle,
              fontFamily: "ui-monospace, 'SF Mono', Menlo, monospace",
            }}
          />
          <div style={{ fontSize: 11, color: MUTED, marginTop: 4 }}>
            创建后还能在配置弹窗里改
          </div>
        </div>
        <div>
          <label
            style={{
              display: "block",
              fontSize: 12,
              color: MUTED,
              marginBottom: 6,
              fontWeight: 600,
            }}
          >
            项目名（可选，默认用文件夹名）
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && folder.trim() && !busy) submit();
            }}
            placeholder="my-dataset"
            disabled={busy}
            style={inputStyle}
          />
        </div>
        {error && (
          <div
            style={{
              padding: "10px 12px",
              background: "rgba(178,65,52,0.1)",
              color: "#973328",
              border: "1px solid rgba(178,65,52,0.18)",
              borderRadius: 10,
              fontSize: 12,
              wordBreak: "break-word",
            }}
          >
            {error}
          </div>
        )}
        <div
          style={{
            display: "flex",
            justifyContent: "flex-end",
            gap: 10,
            marginTop: 4,
          }}
        >
          <button
            onClick={onClose}
            disabled={busy}
            style={{
              padding: "10px 18px",
              background: "rgba(255,255,255,0.7)",
              color: MUTED,
              border: "1px solid rgba(87,66,44,0.14)",
              borderRadius: 999,
              cursor: busy ? "wait" : "pointer",
              fontSize: 13,
              fontFamily: FONT_STACK,
            }}
          >
            取消
          </button>
          <button
            onClick={submit}
            disabled={busy || !folder.trim()}
            style={{
              padding: "10px 18px",
              background:
                busy || !folder.trim()
                  ? "rgba(45,143,103,0.4)"
                  : `linear-gradient(135deg, ${SUCCESS}, ${SUCCESS_DARK})`,
              color: "white",
              border: "none",
              borderRadius: 999,
              cursor: busy || !folder.trim() ? "not-allowed" : "pointer",
              fontSize: 13,
              fontWeight: 600,
              boxShadow:
                busy || !folder.trim()
                  ? "none"
                  : "0 10px 24px rgba(45,143,103,0.28)",
              fontFamily: FONT_STACK,
            }}
          >
            {busy ? "创建中…" : "创建项目"}
          </button>
        </div>
      </div>
    </Modal>
  );
}
