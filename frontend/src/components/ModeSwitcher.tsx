import { useNavigate } from "react-router-dom";

type Mode = "projects" | "viewer";

const TABS: Array<{ key: Mode; label: string; path: string }> = [
  { key: "projects", label: "工作台 · Workbench", path: "/" },
  { key: "viewer", label: "预览 · Viewer", path: "/viewer" },
];

export function ModeSwitcher({ current }: { current: Mode }): JSX.Element {
  const navigate = useNavigate();
  return (
    <div
      role="tablist"
      style={{
        display: "inline-flex",
        padding: 4,
        background: "rgba(255,255,255,0.7)",
        border: "1px solid rgba(87,66,44,0.14)",
        borderRadius: 999,
        boxShadow: "0 8px 24px rgba(58,37,18,0.06)",
        gap: 4,
      }}
    >
      {TABS.map((tab) => {
        const active = tab.key === current;
        return (
          <button
            key={tab.key}
            role="tab"
            aria-selected={active}
            onClick={() => {
              if (!active) navigate(tab.path);
            }}
            style={{
              padding: "8px 18px",
              borderRadius: 999,
              border: "none",
              cursor: active ? "default" : "pointer",
              fontSize: 13,
              fontWeight: 600,
              color: active ? "white" : "#4a5568",
              background: active
                ? "linear-gradient(135deg, #d46b36, #b14c1e)"
                : "transparent",
              boxShadow: active ? "0 4px 12px rgba(212,107,54,0.32)" : "none",
              transition: "background 160ms ease, color 160ms ease",
            }}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
