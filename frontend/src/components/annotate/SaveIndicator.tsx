import { useEffect, useState } from "react";

import { COLORS } from "../../theme";
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
    idle: {
      color: COLORS.faint,
      icon: <SaveIcon size={12} />,
      label: "待编辑",
    },
    saving: {
      color: COLORS.warn,
      icon: <LoaderIcon size={12} />,
      label: "保存中…",
    },
    saved: {
      color: pulse ? COLORS.success : COLORS.faint,
      icon: <CheckIcon size={12} />,
      label: "已保存",
    },
    error: {
      color: COLORS.danger,
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
        padding: "8px 12px",
        background: "rgba(255,255,255,0.7)",
        border: `1px solid ${COLORS.cardBorder}`,
        borderRadius: 999,
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
          color: COLORS.ink,
          flex: 1,
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}
      >
        {p.label}
      </span>
      {lastElapsedMs != null && (
        <span style={{ color: COLORS.faint, fontSize: 11 }}>
          GECO2 {lastElapsedMs}ms
        </span>
      )}
    </div>
  );
}
