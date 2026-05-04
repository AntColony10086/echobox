import { useState } from "react";

import { patchFolder } from "../../api/projects";
import type { Project } from "../../types/project";
import { Card } from "../ui/Card";

interface Props {
  project: Project;
  onUpdated: (p: Project) => void;
}

export function FolderCard({ project, onUpdated }: Props): JSX.Element {
  const [value, setValue] = useState(project.source_folder);
  const [busy, setBusy] = useState(false);

  const status = project.source_folder ? "filled" : "empty";

  const submit = async (): Promise<void> => {
    if (!value || value === project.source_folder) return;
    setBusy(true);
    try {
      const updated = await patchFolder(project.id, value);
      onUpdated(updated);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card title="源文件夹" status={status}>
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onBlur={submit}
        placeholder="/abs/path/to/images"
        disabled={busy}
        style={{ width: "100%", padding: 6, fontFamily: "monospace" }}
      />
    </Card>
  );
}
