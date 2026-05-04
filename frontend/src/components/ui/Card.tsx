import type { ReactNode } from "react";

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
    empty: "#cbd5e0",
    filled: "#48bb78",
    error: "#e53e3e",
  }[status];
  return (
    <div
      style={{
        border: `1px solid ${borderColor}`,
        borderRadius: 8,
        padding: 16,
        marginBottom: 12,
        background: "white",
      }}
    >
      <h3 style={{ margin: "0 0 8px 0", fontSize: 14, fontWeight: 600 }}>
        {title}
      </h3>
      {children}
    </div>
  );
}
