import { useState } from "react";

import { addLabel, deleteLabel } from "../../api/projects";
import { COLORS, FONT_STACK, GRADIENTS } from "../../theme";
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
        <span style={{ fontSize: 11, color: COLORS.muted }}>
          {labels.length} 个
        </span>
      }
    >
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
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
                padding: "8px 10px",
                borderRadius: 12,
                border: `1px solid ${isSelected ? l.color : COLORS.cardBorder}`,
                background: isSelected
                  ? `${l.color}1f`
                  : "rgba(255,255,255,0.7)",
                cursor: "pointer",
                fontSize: 13,
                color: COLORS.ink,
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
                    ? `0 0 0 2px #fbf6ec, 0 0 0 3px ${l.color}`
                    : "none",
                }}
              />
              <span
                style={{
                  flex: 1,
                  fontWeight: isSelected ? 700 : 500,
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
                    color: COLORS.muted,
                    background: "rgba(255,255,255,0.7)",
                    border: `1px solid ${COLORS.cardBorder}`,
                    borderRadius: 4,
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
                  color: COLORS.faint,
                  border: "none",
                  borderRadius: 999,
                  width: 24,
                  height: 24,
                  cursor: busy ? "wait" : "pointer",
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  padding: 0,
                }}
                onMouseEnter={(e) => {
                  const el = e.currentTarget as HTMLElement;
                  el.style.color = COLORS.danger;
                  el.style.background = "rgba(178,65,52,0.1)";
                }}
                onMouseLeave={(e) => {
                  const el = e.currentTarget as HTMLElement;
                  el.style.color = COLORS.faint;
                  el.style.background = "transparent";
                }}
              >
                <TrashIcon size={13} />
              </button>
            </div>
          );
        })}
      </div>

      <div style={{ display: "flex", gap: 6, marginTop: 10 }}>
        <input
          type="text"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && add()}
          placeholder="新类别名"
          disabled={busy}
          style={{
            flex: 1,
            padding: "6px 10px",
            background: "rgba(255,255,255,0.85)",
            color: COLORS.ink,
            border: `1px solid ${COLORS.cardBorder}`,
            borderRadius: 999,
            fontSize: 12,
            outline: "none",
            fontFamily: FONT_STACK,
          }}
        />
        <button
          onClick={add}
          disabled={busy || !newName.trim()}
          aria-label="添加类别"
          style={{
            background:
              busy || !newName.trim()
                ? "rgba(212,107,54,0.35)"
                : GRADIENTS.accent,
            color: "white",
            border: "none",
            borderRadius: 999,
            width: 32,
            height: 28,
            cursor: busy || !newName.trim() ? "not-allowed" : "pointer",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow:
              busy || !newName.trim()
                ? "none"
                : "0 6px 14px rgba(212,107,54,0.28)",
          }}
        >
          <PlusIcon size={14} />
        </button>
      </div>
    </Panel>
  );
}
