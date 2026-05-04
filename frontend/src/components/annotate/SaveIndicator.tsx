import { useEffect, useState } from "react";

import { AlertIcon, CheckIcon, LoaderIcon, SaveIcon } from "../ui/icons";

interface Props {
  state: "idle" | "saving" | "saved" | "error";
  lastError?: string | null;
  lastElapsedMs?: number | null;
}

export function SaveIndicator({
  state,
  lastError,
  lastElapsedMs,
}: Props): JSX.Element {
  const [pulse, setPulse] = useState(false);

  useEffect(() => {
    if (state === "saved") {
      setPulse(true);
      const t = setTimeout(() => setPulse(false), 1500);
      return () => clearTimeout(t);
    }
  }, [state]);

  const presets = {
    idle: { color: "#a0aec0", icon: <SaveIcon size={12} />, label: "待编辑" },
    saving: {
      color: "#d69e2e",
      icon: <LoaderIcon size={12} />,
      label: "保存中…",
    },
    saved: {
      color: pulse ? "#48bb78" : "#a0aec0",
      icon: <CheckIcon size={12} />,
      label: "已保存",
    },
    error: {
      color: "#e53e3e",
      icon: <AlertIcon size={12} />,
      label: lastError ?? "保存失败",
    },
  } as const;
  const p = presets[state];

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        padding: "6px 10px",
        background: "white",
        border: "1px solid #e2e8f0",
        borderRadius: 6,
        fontSize: 12,
      }}
      title={state === "error" ? (lastError ?? "") : undefined}
    >
      <span
        style={{
          color: p.color,
          display: "inline-flex",
          alignItems: "center",
        }}
      >
        {p.icon}
      </span>
      <span
        style={{
          color: "#2d3748",
          flex: 1,
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}
      >
        {p.label}
      </span>
      {lastElapsedMs != null && (
        <span style={{ color: "#a0aec0", fontSize: 11 }}>
          GECO2 {lastElapsedMs}ms
        </span>
      )}
    </div>
  );
}
