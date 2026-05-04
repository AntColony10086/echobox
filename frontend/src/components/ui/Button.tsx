import type { ButtonHTMLAttributes, ReactNode } from "react";

import { COLORS, FONT_STACK, GRADIENTS } from "../../theme";

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
  { bg: string; fg: string; border: string; hoverBg: string; shadow?: string }
> = {
  primary: {
    bg: GRADIENTS.accent,
    fg: "white",
    border: "transparent",
    hoverBg: `linear-gradient(135deg, ${COLORS.accentStrong}, ${COLORS.accent})`,
    shadow: "0 8px 18px rgba(212,107,54,0.28)",
  },
  success: {
    bg: GRADIENTS.success,
    fg: "white",
    border: "transparent",
    hoverBg: `linear-gradient(135deg, ${COLORS.successDark}, ${COLORS.success})`,
    shadow: "0 8px 18px rgba(45,143,103,0.28)",
  },
  danger: {
    bg: GRADIENTS.danger,
    fg: "white",
    border: "transparent",
    hoverBg: `linear-gradient(135deg, ${COLORS.danger}, #d65a4a)`,
    shadow: "0 8px 18px rgba(178,65,52,0.28)",
  },
  ghost: {
    bg: "rgba(255,255,255,0.72)",
    fg: COLORS.ink,
    border: COLORS.cardBorder,
    hoverBg: "rgba(255,255,255,0.92)",
  },
  subtle: {
    bg: COLORS.glassBg,
    fg: COLORS.ink,
    border: COLORS.softBorder,
    hoverBg: "rgba(255,255,255,0.78)",
  },
};

const SIZES: Record<
  Size,
  { padding: string; fontSize: number; height: number }
> = {
  sm: { padding: "0 12px", fontSize: 12, height: 28 },
  md: { padding: "0 16px", fontSize: 13, height: 34 },
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
        borderRadius: 999,
        padding: s.padding,
        fontSize: s.fontSize,
        height: s.height,
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.45 : 1,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 6,
        fontWeight: 600,
        fontFamily: FONT_STACK,
        width: block ? "100%" : undefined,
        boxShadow: v.shadow,
        transition: "background 160ms ease, box-shadow 160ms ease",
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
