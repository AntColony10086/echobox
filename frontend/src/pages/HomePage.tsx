import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  createProject,
  deleteProject,
  listProjects,
  type ProjectSummary,
} from "../api/projects";
import { Modal } from "../components/ui/Modal";

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
        background: "#f7fafc",
        color: "#2d3748",
        fontFamily: "system-ui",
      }}
    >
      <div style={{ maxWidth: 880, margin: "0 auto", padding: "48px 24px" }}>
        <header
          style={{
            display: "flex",
            alignItems: "flex-end",
            justifyContent: "space-between",
            marginBottom: 32,
            gap: 16,
            flexWrap: "wrap",
          }}
        >
          <div>
            <h1 style={{ margin: 0, fontSize: 28, color: "#1a202c" }}>
              echobox
            </h1>
            <p style={{ margin: "4px 0 0", color: "#718096", fontSize: 13 }}>
              多模态智能标注 Agent 平台
            </p>
          </div>
          <button
            onClick={() => setCreateOpen(true)}
            style={{
              padding: "10px 20px",
              background: "#48bb78",
              color: "white",
              border: "none",
              borderRadius: 6,
              cursor: "pointer",
              fontSize: 14,
              fontWeight: 600,
            }}
          >
            + 新建项目
          </button>
        </header>

        <h2
          style={{
            fontSize: 12,
            color: "#718096",
            marginBottom: 12,
            textTransform: "uppercase",
            letterSpacing: 0.6,
          }}
        >
          已有项目
        </h2>

        {loadError && (
          <div
            style={{
              padding: 12,
              background: "#fed7d7",
              color: "#742a2a",
              border: "1px solid #fc8181",
              borderRadius: 6,
              fontSize: 13,
            }}
          >
            {loadError}
          </div>
        )}

        {projects === null && !loadError && (
          <div style={{ color: "#a0aec0", fontSize: 13 }}>加载中…</div>
        )}

        {projects && projects.length === 0 && (
          <div
            style={{
              padding: 24,
              border: "1px dashed #cbd5e0",
              background: "white",
              borderRadius: 6,
              textAlign: "center",
              color: "#718096",
              fontSize: 13,
            }}
          >
            还没有项目，点击右上角「新建项目」开始
          </div>
        )}

        {projects && projects.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
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

function ProjectRow({
  project,
  onOpen,
  onDelete,
}: {
  project: ProjectSummary;
  onOpen: () => void;
  onDelete: () => void;
}): JSX.Element {
  const statusColor =
    project.status === "ready"
      ? "#48bb78"
      : project.status === "draft"
        ? "#ed8936"
        : "#a0aec0";
  return (
    <div
      onClick={onOpen}
      style={{
        padding: 14,
        background: "white",
        borderRadius: 6,
        cursor: "pointer",
        border: "1px solid #e2e8f0",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 12,
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLElement).style.borderColor = "#3182ce";
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLElement).style.borderColor = "#e2e8f0";
      }}
    >
      <div style={{ minWidth: 0, flex: 1 }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            marginBottom: 4,
          }}
        >
          <span style={{ fontSize: 14, fontWeight: 600, color: "#1a202c" }}>
            {project.name}
          </span>
          <span style={{ fontSize: 11, color: "#a0aec0" }}>#{project.id}</span>
          <span
            style={{
              fontSize: 10,
              padding: "1px 6px",
              borderRadius: 3,
              background: statusColor,
              color: "white",
              fontWeight: 600,
            }}
          >
            {project.status}
          </span>
        </div>
        <div
          style={{
            fontSize: 11,
            color: "#718096",
            fontFamily: "monospace",
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
          color: "#a0aec0",
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
          width: 28,
          height: 28,
          padding: 0,
          background: "transparent",
          color: "#a0aec0",
          border: "1px solid #e2e8f0",
          borderRadius: 4,
          cursor: "pointer",
          fontSize: 16,
          lineHeight: 1,
        }}
        onMouseEnter={(e) => {
          const el = e.currentTarget as HTMLElement;
          el.style.background = "#fff5f5";
          el.style.borderColor = "#e53e3e";
          el.style.color = "#e53e3e";
        }}
        onMouseLeave={(e) => {
          const el = e.currentTarget as HTMLElement;
          el.style.background = "transparent";
          el.style.borderColor = "#e2e8f0";
          el.style.color = "#a0aec0";
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

  return (
    <Modal title="新建标注项目" onClose={onClose} width={520}>
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <div>
          <label
            style={{
              display: "block",
              fontSize: 12,
              color: "#4a5568",
              marginBottom: 4,
            }}
          >
            图片文件夹（绝对路径）
            <span style={{ color: "#e53e3e" }}> *</span>
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
              width: "100%",
              padding: "8px 10px",
              fontFamily: "monospace",
              fontSize: 13,
              border: "1px solid #cbd5e0",
              borderRadius: 4,
              boxSizing: "border-box",
            }}
          />
          <div style={{ fontSize: 11, color: "#718096", marginTop: 4 }}>
            创建后还能在配置弹窗里改
          </div>
        </div>
        <div>
          <label
            style={{
              display: "block",
              fontSize: 12,
              color: "#4a5568",
              marginBottom: 4,
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
            style={{
              width: "100%",
              padding: "8px 10px",
              fontSize: 13,
              border: "1px solid #cbd5e0",
              borderRadius: 4,
              boxSizing: "border-box",
            }}
          />
        </div>
        {error && (
          <div
            style={{
              padding: 8,
              background: "#fed7d7",
              color: "#742a2a",
              borderRadius: 4,
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
            gap: 8,
            marginTop: 4,
          }}
        >
          <button
            onClick={onClose}
            disabled={busy}
            style={{
              padding: "8px 16px",
              background: "white",
              color: "#4a5568",
              border: "1px solid #cbd5e0",
              borderRadius: 4,
              cursor: busy ? "wait" : "pointer",
              fontSize: 13,
            }}
          >
            取消
          </button>
          <button
            onClick={submit}
            disabled={busy || !folder.trim()}
            style={{
              padding: "8px 16px",
              background: busy || !folder.trim() ? "#a0aec0" : "#48bb78",
              color: "white",
              border: "none",
              borderRadius: 4,
              cursor: busy || !folder.trim() ? "not-allowed" : "pointer",
              fontSize: 13,
              fontWeight: 600,
            }}
          >
            {busy ? "创建中…" : "创建项目"}
          </button>
        </div>
      </div>
    </Modal>
  );
}
