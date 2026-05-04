import { useState } from "react";

import { finalizeProject } from "../../api/projects";
import { COLORS, FONT_STACK, GRADIENTS } from "../../theme";
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

  const draftReady = project.status === "draft" && !busy;

  return (
    <Modal title={`项目配置 — ${project.name}`} onClose={onClose} width={760}>
      <div
        style={{
          fontSize: 12,
          color: COLORS.muted,
          marginBottom: 14,
          fontFamily: FONT_STACK,
        }}
      >
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
          marginTop: 18,
          display: "flex",
          alignItems: "center",
          gap: 12,
        }}
      >
        <button
          onClick={finalize}
          disabled={busy || project.status !== "draft"}
          style={{
            padding: "12px 22px",
            background: draftReady
              ? GRADIENTS.success
              : "rgba(45,143,103,0.35)",
            color: "white",
            border: "none",
            borderRadius: 999,
            cursor: draftReady ? "pointer" : "not-allowed",
            fontSize: 14,
            fontWeight: 700,
            fontFamily: FONT_STACK,
            boxShadow: draftReady
              ? "0 10px 22px rgba(45,143,103,0.28)"
              : "none",
          }}
        >
          {busy
            ? "处理中…"
            : project.status === "draft"
              ? "▶ 完成配置，开始标注"
              : "✓ 已就绪"}
        </button>
        {project.status !== "draft" && (
          <span style={{ fontSize: 12, color: COLORS.successDark }}>
            项目已就绪，可继续修改配置
          </span>
        )}
      </div>
      {finalizeError && (
        <div
          style={{
            marginTop: 10,
            padding: "10px 12px",
            background: "rgba(178,65,52,0.1)",
            color: COLORS.dangerDark,
            border: "1px solid rgba(178,65,52,0.18)",
            borderRadius: 12,
            fontSize: 12,
          }}
        >
          {finalizeError}
        </div>
      )}
    </Modal>
  );
}
