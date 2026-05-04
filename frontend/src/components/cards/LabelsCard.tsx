import { useState } from "react";

import { addLabel, deleteLabel } from "../../api/projects";
import type { Project } from "../../types/project";
import { Card } from "../ui/Card";

interface Props {
  project: Project;
  onUpdated: () => void;
}

export function LabelsCard({ project, onUpdated }: Props): JSX.Element {
  const [newName, setNewName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const status = project.labels.length > 0 ? "filled" : "empty";
  const canDelete = project.status === "draft";

  const add = async (): Promise<void> => {
    if (!newName) return;
    setBusy(true);
    setError(null);
    try {
      await addLabel(project.id, newName);
      setNewName("");
      onUpdated();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  };

  const remove = async (name: string): Promise<void> => {
    setBusy(true);
    try {
      await deleteLabel(project.id, name);
      onUpdated();
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card title={`标签集（${project.labels.length}）`} status={status}>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
        {project.labels.map((l) => (
          <span
            key={l.name}
            style={{
              padding: "2px 8px",
              borderRadius: 12,
              background: l.color,
              color: "white",
              fontSize: 12,
              display: "inline-flex",
              alignItems: "center",
              gap: 4,
            }}
          >
            {l.name}
            {canDelete && (
              <button
                onClick={() => remove(l.name)}
                disabled={busy}
                style={{
                  border: "none",
                  background: "rgba(0,0,0,0.2)",
                  color: "white",
                  borderRadius: 8,
                  width: 16,
                  height: 16,
                  cursor: "pointer",
                  fontSize: 10,
                }}
              >
                ×
              </button>
            )}
          </span>
        ))}
      </div>
      <div style={{ marginTop: 8, display: "flex", gap: 4 }}>
        <input
          type="text"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") add();
          }}
          placeholder="加新标签 (按 Enter)"
          disabled={busy}
          style={{ flex: 1, padding: 4 }}
        />
        <button
          onClick={add}
          disabled={busy || !newName}
          style={{ padding: "4px 8px" }}
        >
          +
        </button>
      </div>
      {error && (
        <div style={{ color: "#e53e3e", fontSize: 12, marginTop: 4 }}>
          {error}
        </div>
      )}
    </Card>
  );
}
