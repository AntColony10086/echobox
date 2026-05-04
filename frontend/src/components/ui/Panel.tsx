import type { ReactNode } from "react";

import { COLORS } from "../../theme";

interface Props {
  title?: string;
  trailing?: ReactNode;
  children: ReactNode;
  noPadding?: boolean;
  style?: React.CSSProperties;
}

export function Panel({
  title,
  trailing,
  children,
  noPadding = false,
  style,
}: Props): JSX.Element {
  return (
    <section
      style={{
        background: COLORS.cardBg,
        border: `1px solid ${COLORS.cardBorder}`,
        borderRadius: 18,
        marginBottom: 12,
        boxShadow: "0 8px 24px rgba(58,37,18,0.06)",
        backdropFilter: "blur(12px)",
        ...style,
      }}
    >
      {title && (
        <header
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "10px 14px",
            borderBottom: `1px solid ${COLORS.softBorder}`,
          }}
        >
          <span
            style={{
              fontSize: 11,
              fontWeight: 700,
              letterSpacing: 0.6,
              textTransform: "uppercase",
              color: COLORS.accentStrong,
            }}
          >
            {title}
          </span>
          {trailing && (
            <span style={{ fontSize: 12, color: COLORS.ink }}>{trailing}</span>
          )}
        </header>
      )}
      <div style={{ padding: noPadding ? 0 : 14 }}>{children}</div>
    </section>
  );
}
