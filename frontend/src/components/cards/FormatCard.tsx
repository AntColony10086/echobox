import { patchFormat } from "../../api/projects";
import { COLORS, FONT_STACK, GRADIENTS } from "../../theme";
import type { ExportFormat, Project } from "../../types/project";
import { Card } from "../ui/Card";

const FORMATS: ExportFormat[] = ["coco", "yolo", "voc", "ls_json"];

interface Props {
  project: Project;
  onUpdated: (p: Project) => void;
}

export function FormatCard({ project, onUpdated }: Props): JSX.Element {
  const status = project.export_format ? "filled" : "empty";
  const select = async (fmt: ExportFormat): Promise<void> => {
    const updated = await patchFormat(project.id, fmt);
    onUpdated(updated);
  };
  return (
    <Card title="导出格式" status={status}>
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
        {FORMATS.map((fmt) => {
          const active = project.export_format === fmt;
          return (
            <button
              key={fmt}
              onClick={() => select(fmt)}
              style={{
                padding: "6px 14px",
                border: `1px solid ${active ? "transparent" : COLORS.cardBorder}`,
                borderRadius: 999,
                background: active ? GRADIENTS.accent : "rgba(255,255,255,0.7)",
                color: active ? "white" : COLORS.ink,
                cursor: "pointer",
                fontSize: 12,
                fontWeight: active ? 700 : 600,
                fontFamily: FONT_STACK,
                boxShadow: active ? "0 6px 14px rgba(212,107,54,0.24)" : "none",
              }}
            >
              {fmt.toUpperCase()}
            </button>
          );
        })}
      </div>
    </Card>
  );
}
