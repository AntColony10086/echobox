import { patchFormat } from "../../api/projects";
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
        {FORMATS.map((fmt) => (
          <button
            key={fmt}
            onClick={() => select(fmt)}
            style={{
              padding: "4px 10px",
              border: "1px solid #cbd5e0",
              borderRadius: 4,
              background: project.export_format === fmt ? "#3182ce" : "white",
              color: project.export_format === fmt ? "white" : "#2d3748",
              cursor: "pointer",
            }}
          >
            {fmt.toUpperCase()}
          </button>
        ))}
      </div>
    </Card>
  );
}
