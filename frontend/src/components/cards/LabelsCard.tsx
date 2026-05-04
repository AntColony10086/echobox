import { useState } from "react";

import { addLabel, deleteLabel } from "../../api/projects";
import { COLORS, FONT_STACK, GRADIENTS } from "../../theme";
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
              padding: "4px 12px",
              borderRadius: 999,
              background: l.color,
              color: "white",
              fontSize: 12,
              fontWeight: 600,
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
              boxShadow: "0 4px 10px rgba(58,37,18,0.12)",
            }}
          >
            {l.name}
            {canDelete && (
              <button
                onClick={() => remove(l.name)}
                disabled={busy}
                style={{
                  border: "none",
                  background: "rgba(0,0,0,0.25)",
                  color: "white",
                  borderRadius: 999,
                  width: 18,
                  height: 18,
                  cursor: "pointer",
                  fontSize: 11,
                  padding: 0,
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                ×
              </button>
            )}
          </span>
        ))}
      </div>
      <div style={{ marginTop: 12, display: "flex", gap: 6 }}>
        <input
          type="text"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") add();
          }}
          placeholder="加新标签 (按 Enter)"
          disabled={busy}
          style={{
            flex: 1,
            padding: "6px 10px",
            background: "rgba(255,255,255,0.85)",
            color: COLORS.ink,
            border: `1px solid ${COLORS.cardBorder}`,
            borderRadius: 999,
            fontSize: 12,
            fontFamily: FONT_STACK,
            outline: "none",
          }}
        />
        <button
          onClick={add}
          disabled={busy || !newName}
          style={{
            padding: "6px 14px",
            background:
              busy || !newName ? "rgba(212,107,54,0.35)" : GRADIENTS.accent,
            color: "white",
            border: "none",
            borderRadius: 999,
            cursor: busy || !newName ? "not-allowed" : "pointer",
            fontSize: 13,
            fontWeight: 700,
            fontFamily: FONT_STACK,
            boxShadow:
              busy || !newName ? "none" : "0 6px 14px rgba(212,107,54,0.28)",
          }}
        >
          +
        </button>
      </div>
      {error && (
        <div
          style={{
            color: COLORS.dangerDark,
            fontSize: 12,
            marginTop: 8,
            padding: "8px 10px",
            background: "rgba(178,65,52,0.1)",
            border: "1px solid rgba(178,65,52,0.18)",
            borderRadius: 8,
          }}
        >
          {error}
        </div>
      )}
    </Card>
  );
}
