import type { CSSProperties } from "react";

interface IconProps {
  size?: number;
  style?: CSSProperties;
  strokeWidth?: number;
}

const base = ({
  size = 16,
  style,
  children,
}: IconProps & { children: React.ReactNode }): JSX.Element => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.75}
    strokeLinecap="round"
    strokeLinejoin="round"
    style={{ flexShrink: 0, display: "inline-block", ...style }}
    aria-hidden="true"
  >
    {children}
  </svg>
);

export const CheckIcon = (p: IconProps): JSX.Element =>
  base({ ...p, children: <polyline points="20 6 9 17 4 12" /> });

export const XIcon = (p: IconProps): JSX.Element =>
  base({
    ...p,
    children: (
      <>
        <line x1="18" y1="6" x2="6" y2="18" />
        <line x1="6" y1="6" x2="18" y2="18" />
      </>
    ),
  });

export const TrashIcon = (p: IconProps): JSX.Element =>
  base({
    ...p,
    children: (
      <>
        <polyline points="3 6 5 6 21 6" />
        <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
        <path d="M10 11v6M14 11v6" />
        <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
      </>
    ),
  });

export const PlusIcon = (p: IconProps): JSX.Element =>
  base({
    ...p,
    children: (
      <>
        <line x1="12" y1="5" x2="12" y2="19" />
        <line x1="5" y1="12" x2="19" y2="12" />
      </>
    ),
  });

export const MouseIcon = (p: IconProps): JSX.Element =>
  base({
    ...p,
    children: (
      <>
        <path d="M3 3l7 19 2-8 8-2z" />
      </>
    ),
  });

export const SquareDashIcon = (p: IconProps): JSX.Element =>
  base({
    ...p,
    children: (
      <>
        <path d="M5 3a2 2 0 0 0-2 2" />
        <path d="M19 3a2 2 0 0 1 2 2" />
        <path d="M21 19a2 2 0 0 1-2 2" />
        <path d="M5 21a2 2 0 0 1-2-2" />
        <line x1="3" y1="9" x2="3" y2="15" />
        <line x1="21" y1="9" x2="21" y2="15" />
        <line x1="9" y1="3" x2="15" y2="3" />
        <line x1="9" y1="21" x2="15" y2="21" />
      </>
    ),
  });

export const ZapIcon = (p: IconProps): JSX.Element =>
  base({
    ...p,
    children: <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />,
  });

export const AlertIcon = (p: IconProps): JSX.Element =>
  base({
    ...p,
    children: (
      <>
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="8" x2="12" y2="12" />
        <line x1="12" y1="16" x2="12.01" y2="16" />
      </>
    ),
  });

export const SaveIcon = (p: IconProps): JSX.Element =>
  base({
    ...p,
    children: (
      <>
        <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
        <polyline points="17 21 17 13 7 13 7 21" />
        <polyline points="7 3 7 8 15 8" />
      </>
    ),
  });

export const LoaderIcon = (p: IconProps): JSX.Element =>
  base({
    ...p,
    children: (
      <>
        <line x1="12" y1="2" x2="12" y2="6" />
        <line x1="12" y1="18" x2="12" y2="22" />
        <line x1="4.93" y1="4.93" x2="7.76" y2="7.76" />
        <line x1="16.24" y1="16.24" x2="19.07" y2="19.07" />
        <line x1="2" y1="12" x2="6" y2="12" />
        <line x1="18" y1="12" x2="22" y2="12" />
        <line x1="4.93" y1="19.07" x2="7.76" y2="16.24" />
        <line x1="16.24" y1="7.76" x2="19.07" y2="4.93" />
      </>
    ),
  });
