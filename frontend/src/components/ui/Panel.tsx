import type { ReactNode } from "react";

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
        background: "white",
        border: "1px solid #e2e8f0",
        borderRadius: 8,
        marginBottom: 12,
        ...style,
      }}
    >
      {title && (
        <header
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "8px 12px",
            borderBottom: "1px solid #edf2f7",
          }}
        >
          <span
            style={{
              fontSize: 11,
              fontWeight: 600,
              letterSpacing: 0.6,
              textTransform: "uppercase",
              color: "#718096",
            }}
          >
            {title}
          </span>
          {trailing && (
            <span style={{ fontSize: 12, color: "#2d3748" }}>{trailing}</span>
          )}
        </header>
      )}
      <div style={{ padding: noPadding ? 0 : 12 }}>{children}</div>
    </section>
  );
}
