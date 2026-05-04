import { useEffect } from "react";
import type { ReactNode } from "react";

import { COLORS, FONT_STACK } from "../../theme";

interface Props {
  title: string;
  onClose: () => void;
  children: ReactNode;
  width?: number | string;
}

export function Modal({
  title,
  onClose,
  children,
  width = 720,
}: Props): JSX.Element {
  useEffect(() => {
    const onKey = (e: KeyboardEvent): void => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        background:
          "radial-gradient(circle at 30% 20%, rgba(212,107,54,0.18), transparent 40%), rgba(31,42,51,0.55)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
        backdropFilter: "blur(2px)",
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: "#fbf6ec",
          color: COLORS.ink,
          width,
          maxWidth: "92vw",
          maxHeight: "88vh",
          borderRadius: 22,
          boxShadow: "0 30px 80px rgba(58,37,18,0.35)",
          border: `1px solid ${COLORS.cardBorder}`,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          fontFamily: FONT_STACK,
        }}
      >
        <header
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "14px 18px",
            borderBottom: `1px solid ${COLORS.softBorder}`,
            background: "rgba(255,250,242,0.7)",
          }}
        >
          <h2 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>{title}</h2>
          <button
            onClick={onClose}
            aria-label="关闭"
            style={{
              background: "transparent",
              border: "none",
              fontSize: 22,
              cursor: "pointer",
              color: COLORS.muted,
              padding: "0 6px",
              lineHeight: 1,
            }}
          >
            ×
          </button>
        </header>
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: 18,
            minHeight: 0,
          }}
        >
          {children}
        </div>
      </div>
    </div>
  );
}
