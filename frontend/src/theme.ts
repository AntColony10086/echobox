export const FONT_STACK =
  "'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif";

export const PAGE_BG =
  "radial-gradient(circle at top left, rgba(212,107,54,0.14), transparent 28%), radial-gradient(circle at 100% 0, rgba(45,143,103,0.12), transparent 24%), linear-gradient(135deg, #f4efe6, #f7f2ea 45%, #e6dcc8)";

export const CANVAS_BG =
  "linear-gradient(45deg, rgba(31,42,51,0.03) 25%, transparent 25%), linear-gradient(-45deg, rgba(31,42,51,0.03) 25%, transparent 25%), linear-gradient(45deg, transparent 75%, rgba(31,42,51,0.03) 75%), linear-gradient(-45deg, transparent 75%, rgba(31,42,51,0.03) 75%), #f8f4ec";

export const COLORS = {
  ink: "#1f2a33",
  muted: "#5d6b73",
  faint: "#a0a8b0",
  accent: "#d46b36",
  accentStrong: "#b14c1e",
  success: "#2d8f67",
  successDark: "#166447",
  warn: "#b67a13",
  warnDark: "#865d10",
  danger: "#b24134",
  dangerDark: "#973328",
  cardBg: "rgba(255,250,242,0.84)",
  glassBg: "rgba(255,255,255,0.62)",
  cardBorder: "rgba(87,66,44,0.14)",
  softBorder: "rgba(87,66,44,0.08)",
  cardShadow: "0 24px 60px rgba(58,37,18,0.12)",
  rowShadow: "0 14px 30px rgba(58,37,18,0.08)",
} as const;

export const GRADIENTS = {
  accent: `linear-gradient(135deg, ${COLORS.accent}, ${COLORS.accentStrong})`,
  success: `linear-gradient(135deg, ${COLORS.success}, ${COLORS.successDark})`,
  danger: `linear-gradient(135deg, #d65a4a, ${COLORS.danger})`,
} as const;

export const RADII = {
  sm: 10,
  md: 18,
  lg: 28,
  pill: 999,
} as const;
