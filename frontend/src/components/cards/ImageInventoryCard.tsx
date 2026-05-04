import type { Project } from "../../types/project";
import { Card } from "../ui/Card";

interface Props {
  project: Project;
}

export function ImageInventoryCard({ project }: Props): JSX.Element {
  const status = project.image_count > 0 ? "filled" : "empty";
  return (
    <Card title="图像清单" status={status}>
      <div style={{ fontSize: 14 }}>
        总图像数：<b>{project.image_count}</b>
        <div style={{ marginTop: 4, color: "#718096", fontSize: 12 }}>
          扫描和整理由 Agent 执行 —— 在聊天里说"扫描这个文件夹"。
        </div>
      </div>
    </Card>
  );
}
