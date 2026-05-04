import type { ReactNode } from "react";

import { COLORS } from "../../theme";

interface Props {
  title: string;
  status?: "empty" | "filled" | "error";
  children: ReactNode;
}

export function Card({
  title,
  status = "empty",
  children,
}: Props): JSX.Element {
  const borderColor = {
    empty: COLORS.cardBorder,
    filled: "rgba(45,143,103,0.55)",
    error: "rgba(178,65,52,0.55)",
  }[status];
  return (
    <div
      style={{
        border: `1px solid ${borderColor}`,
        borderRadius: 18,
        padding: 16,
        marginBottom: 12,
        background: COLORS.cardBg,
        boxShadow: "0 8px 24px rgba(58,37,18,0.06)",
        backdropFilter: "blur(12px)",
      }}
    >
      <h3
        style={{
          margin: "0 0 10px 0",
          fontSize: 13,
          fontWeight: 700,
          color: COLORS.accentStrong,
          letterSpacing: 0.4,
          textTransform: "uppercase",
        }}
      >
        {title}
      </h3>
      {children}
    </div>
  );
}
