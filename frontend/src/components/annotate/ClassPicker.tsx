import { useState } from "react";

import { addLabel, deleteLabel } from "../../api/projects";
import type { Label } from "../../types/project";
import { Panel } from "../ui/Panel";
import { PlusIcon, TrashIcon } from "../ui/icons";

interface Props {
  pid: number;
  labels: (Label & { id: number })[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  onLabelsChanged: () => void;
}

export function ClassPicker({
  pid,
  labels,
  selectedId,
  onSelect,
  onLabelsChanged,
}: Props): JSX.Element {
  const [newName, setNewName] = useState("");
  const [busy, setBusy] = useState(false);

  const add = async (): Promise<void> => {
    if (!newName.trim()) return;
    setBusy(true);
    try {
      await addLabel(pid, newName.trim());
      setNewName("");
      onLabelsChanged();
    } finally {
      setBusy(false);
    }
  };

  return (
    <Panel
      title="类别"
      trailing={
        <span style={{ fontSize: 11, color: "#a0aec0" }}>
          {labels.length} 个
        </span>
      }
    >
      <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        {labels.map((l, idx) => {
          const isSelected = selectedId === l.id;
          const onDelete = async (e: React.MouseEvent): Promise<void> => {
            e.stopPropagation();
            if (
              !window.confirm(
                `确定删除类别 "${l.name}" 吗？\n这会同时删除该类别下的所有标注框。`,
              )
            )
              return;
            setBusy(true);
            try {
              await deleteLabel(pid, l.name, true);
              onLabelsChanged();
            } finally {
              setBusy(false);
            }
          };
          return (
            <div
              key={l.id}
              onClick={() => onSelect(l.id)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                padding: "6px 8px",
                borderRadius: 6,
                border: `1px solid ${isSelected ? l.color : "#e2e8f0"}`,
                background: isSelected ? `${l.color}14` : "white",
                cursor: "pointer",
                fontSize: 13,
                color: "#2d3748",
                userSelect: "none",
              }}
            >
              <span
                style={{
                  width: 12,
                  height: 12,
                  borderRadius: 3,
                  background: l.color,
                  flexShrink: 0,
                  boxShadow: isSelected
                    ? `0 0 0 2px white, 0 0 0 3px ${l.color}`
                    : "none",
                }}
              />
              <span
                style={{
                  flex: 1,
                  fontWeight: isSelected ? 600 : 400,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                {l.name}
              </span>
              {idx < 9 && (
                <kbd
                  style={{
                    fontSize: 10,
                    color: "#a0aec0",
                    background: "#f7fafc",
                    border: "1px solid #e2e8f0",
                    borderRadius: 3,
                    padding: "0 5px",
                    minWidth: 14,
                    textAlign: "center",
                    fontFamily:
                      "ui-monospace, SFMono-Regular, Menlo, monospace",
                  }}
                >
                  {idx + 1}
                </kbd>
              )}
              <button
                onClick={onDelete}
                disabled={busy}
                title={`删除类别 "${l.name}"`}
                aria-label={`删除类别 ${l.name}`}
                style={{
                  background: "transparent",
                  color: "#a0aec0",
                  border: "none",
                  borderRadius: 4,
                  width: 22,
                  height: 22,
                  cursor: busy ? "wait" : "pointer",
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  padding: 0,
                }}
                onMouseEnter={(e) => {
                  const el = e.currentTarget as HTMLElement;
                  el.style.color = "#e53e3e";
                  el.style.background = "#fff5f5";
                }}
                onMouseLeave={(e) => {
                  const el = e.currentTarget as HTMLElement;
                  el.style.color = "#a0aec0";
                  el.style.background = "transparent";
                }}
              >
                <TrashIcon size={13} />
              </button>
            </div>
          );
        })}
      </div>

      <div style={{ display: "flex", gap: 6, marginTop: 8 }}>
        <input
          type="text"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && add()}
          placeholder="新类别名"
          disabled={busy}
          style={{
            flex: 1,
            padding: "5px 8px",
            background: "white",
            color: "#2d3748",
            border: "1px solid #cbd5e0",
            borderRadius: 4,
            fontSize: 12,
            outline: "none",
          }}
        />
        <button
          onClick={add}
          disabled={busy || !newName.trim()}
          aria-label="添加类别"
          style={{
            background: busy || !newName.trim() ? "#edf2f7" : "#3182ce",
            color: busy || !newName.trim() ? "#a0aec0" : "white",
            border: "none",
            borderRadius: 4,
            width: 28,
            cursor: busy || !newName.trim() ? "not-allowed" : "pointer",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <PlusIcon size={14} />
        </button>
      </div>
    </Panel>
  );
}
