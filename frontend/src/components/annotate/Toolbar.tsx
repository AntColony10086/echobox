import { Button } from "../ui/Button";
import { Panel } from "../ui/Panel";
import {
  CheckIcon,
  MouseIcon,
  SquareDashIcon,
  TrashIcon,
  XIcon,
} from "../ui/icons";

type Mode = "select" | "exemplar";

interface Props {
  mode: Mode;
  onModeChange: (m: Mode) => void;
  onAcceptAll: () => void;
  onRejectAll: () => void;
  onDelete: () => void;
  hasSelection: boolean;
  hasPending: boolean;
  predictBusy: boolean;
}

export function Toolbar({
  mode,
  onModeChange,
  onAcceptAll,
  onRejectAll,
  onDelete,
  hasSelection,
  hasPending,
  predictBusy,
}: Props): JSX.Element {
  return (
    <>
      <Panel title="模式">
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 6,
          }}
        >
          <ModeButton
            active={mode === "exemplar"}
            disabled={predictBusy}
            onClick={() => onModeChange("exemplar")}
            icon={<SquareDashIcon size={14} />}
            label="画框"
            shortcut="E"
          />
          <ModeButton
            active={mode === "select"}
            disabled={predictBusy}
            onClick={() => onModeChange("select")}
            icon={<MouseIcon size={14} />}
            label="编辑"
            shortcut="V"
          />
        </div>
      </Panel>

      <Panel title="操作">
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <Button
            variant="success"
            block
            disabled={!hasPending}
            leading={<CheckIcon size={14} />}
            onClick={onAcceptAll}
          >
            全部接受
          </Button>
          <Button
            variant="ghost"
            block
            disabled={!hasPending}
            leading={<XIcon size={14} />}
            onClick={onRejectAll}
          >
            全部拒绝
          </Button>
          <Button
            variant="ghost"
            block
            disabled={!hasSelection}
            leading={<TrashIcon size={14} />}
            onClick={onDelete}
          >
            删除选中
            <kbd
              style={{
                fontSize: 10,
                color: "#a0aec0",
                marginLeft: 4,
                fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
              }}
            >
              Del
            </kbd>
          </Button>
        </div>
      </Panel>
    </>
  );
}

function ModeButton({
  active,
  disabled,
  onClick,
  icon,
  label,
  shortcut,
}: {
  active: boolean;
  disabled: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
  shortcut: string;
}): JSX.Element {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 6,
        padding: "8px 6px",
        background: active ? "#3182ce" : "white",
        color: active ? "white" : "#2d3748",
        border: `1px solid ${active ? "#3182ce" : "#cbd5e0"}`,
        borderRadius: 6,
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.5 : 1,
        fontSize: 12,
        fontWeight: active ? 600 : 500,
        position: "relative",
      }}
    >
      {icon}
      <span>{label}</span>
      <kbd
        style={{
          fontSize: 10,
          marginLeft: 2,
          color: active ? "rgba(255,255,255,0.8)" : "#a0aec0",
          fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
        }}
      >
        {shortcut}
      </kbd>
    </button>
  );
}
