import { useState } from "react";

import { finalizeProject } from "../../api/projects";
import { FolderCard } from "../cards/FolderCard";
import { FormatCard } from "../cards/FormatCard";
import { ImageInventoryCard } from "../cards/ImageInventoryCard";
import { LabelsCard } from "../cards/LabelsCard";
import { SplitCard } from "../cards/SplitCard";
import { Modal } from "../ui/Modal";
import { ExportPanel } from "./ExportPanel";
import type { Project } from "../../types/project";

interface Props {
  project: Project;
  onUpdated: (p: Project) => void;
  onRefetch: () => unknown | Promise<unknown>;
  onReady: () => void;
  onClose: () => void;
}

export function SetupModal({
  project,
  onUpdated,
  onRefetch,
  onReady,
  onClose,
}: Props): JSX.Element {
  const [finalizeError, setFinalizeError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const finalize = async (): Promise<void> => {
    setFinalizeError(null);
    setBusy(true);
    try {
      const res = await finalizeProject(project.id);
      if (res.status === "ready") {
        onReady();
        onClose();
      }
    } catch (e: unknown) {
      const msg =
        (
          e as {
            response?: {
              data?: { error?: { detail?: { errors?: string[] } } };
            };
          }
        ).response?.data?.error?.detail?.errors?.join("; ") ?? String(e);
      setFinalizeError(msg);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal title={`项目配置 — ${project.name}`} onClose={onClose} width={760}>
      <div style={{ fontSize: 12, color: "#718096", marginBottom: 12 }}>
        project_id={project.id} · status={project.status}
      </div>
      <FolderCard project={project} onUpdated={onUpdated} />
      <ImageInventoryCard project={project} />
      <SplitCard project={project} onUpdated={onUpdated} />
      <LabelsCard project={project} onUpdated={onRefetch} />
      <FormatCard project={project} onUpdated={onUpdated} />
      <ExportPanel pid={project.id} projectFormat={project.export_format} />
      <div
        style={{
          marginTop: 16,
          display: "flex",
          alignItems: "center",
          gap: 12,
        }}
      >
        <button
          onClick={finalize}
          disabled={busy || project.status !== "draft"}
          style={{
            padding: "10px 20px",
            background:
              project.status === "draft" && !busy ? "#48bb78" : "#a0aec0",
            color: "white",
            border: "none",
            borderRadius: 6,
            cursor:
              project.status === "draft" && !busy ? "pointer" : "not-allowed",
            fontSize: 14,
            fontWeight: 600,
          }}
        >
          {busy
            ? "处理中…"
            : project.status === "draft"
              ? "▶ 完成配置，开始标注"
              : "✓ 已就绪"}
        </button>
        {project.status !== "draft" && (
          <span style={{ fontSize: 12, color: "#48bb78" }}>
            项目已就绪，可继续修改配置
          </span>
        )}
      </div>
      {finalizeError && (
        <div
          style={{
            marginTop: 8,
            padding: 8,
            background: "#fed7d7",
            color: "#742a2a",
            borderRadius: 4,
            fontSize: 12,
          }}
        >
          {finalizeError}
        </div>
      )}
    </Modal>
  );
}
