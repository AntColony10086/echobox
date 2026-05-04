import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "success" | "danger" | "ghost" | "subtle";
type Size = "sm" | "md";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  block?: boolean;
  leading?: ReactNode;
  trailing?: ReactNode;
  children?: ReactNode;
}

const VARIANTS: Record<
  Variant,
  { bg: string; fg: string; border: string; hoverBg: string }
> = {
  primary: {
    bg: "#3182ce",
    fg: "white",
    border: "#3182ce",
    hoverBg: "#2b6cb0",
  },
  success: {
    bg: "#48bb78",
    fg: "white",
    border: "#48bb78",
    hoverBg: "#38a169",
  },
  danger: {
    bg: "#e53e3e",
    fg: "white",
    border: "#e53e3e",
    hoverBg: "#c53030",
  },
  ghost: {
    bg: "white",
    fg: "#2d3748",
    border: "#cbd5e0",
    hoverBg: "#f7fafc",
  },
  subtle: {
    bg: "#edf2f7",
    fg: "#2d3748",
    border: "#edf2f7",
    hoverBg: "#e2e8f0",
  },
};

const SIZES: Record<
  Size,
  { padding: string; fontSize: number; height: number }
> = {
  sm: { padding: "0 8px", fontSize: 12, height: 26 },
  md: { padding: "0 12px", fontSize: 13, height: 32 },
};

export function Button({
  variant = "ghost",
  size = "md",
  block = false,
  leading,
  trailing,
  children,
  disabled,
  style,
  onMouseEnter,
  onMouseLeave,
  ...rest
}: Props): JSX.Element {
  const v = VARIANTS[variant];
  const s = SIZES[size];

  return (
    <button
      {...rest}
      disabled={disabled}
      style={{
        background: v.bg,
        color: v.fg,
        border: `1px solid ${v.border}`,
        borderRadius: 6,
        padding: s.padding,
        fontSize: s.fontSize,
        height: s.height,
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.5 : 1,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 6,
        fontWeight: 500,
        width: block ? "100%" : undefined,
        transition: "background 120ms",
        ...style,
      }}
      onMouseEnter={(e) => {
        if (!disabled) {
          (e.currentTarget as HTMLElement).style.background = v.hoverBg;
        }
        onMouseEnter?.(e);
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLElement).style.background = v.bg;
        onMouseLeave?.(e);
      }}
    >
      {leading}
      {children}
      {trailing}
    </button>
  );
}
