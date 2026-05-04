import { useState } from "react";

import { patchSplits } from "../../api/projects";
import { COLORS, FONT_STACK } from "../../theme";
import type { Project } from "../../types/project";
import { Card } from "../ui/Card";

interface Props {
  project: Project;
  onUpdated: (p: Project) => void;
}

export function SplitCard({ project, onUpdated }: Props): JSX.Element {
  const [train, setTrain] = useState(project.train_ratio);
  const [val, setVal] = useState(project.val_ratio);
  const [test, setTest] = useState(project.test_ratio);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sum = train + val + test;
  const valid = Math.abs(sum - 1.0) < 1e-6;
  const status = valid ? "filled" : "error";

  const submit = async (): Promise<void> => {
    if (!valid || busy) return;
    setBusy(true);
    setError(null);
    try {
      const updated = await patchSplits(project.id, train, val, test);
      onUpdated(updated);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  };

  const inputStyle = {
    width: "100%",
    padding: "6px 10px",
    background: "rgba(255,255,255,0.85)",
    color: COLORS.ink,
    border: `1px solid ${COLORS.cardBorder}`,
    borderRadius: 8,
    fontSize: 13,
    fontFamily: FONT_STACK,
    outline: "none",
    boxSizing: "border-box" as const,
    marginTop: 4,
  };

  return (
    <Card
      title={`Train / Val / Test 切分 (sum=${sum.toFixed(3)})`}
      status={status}
    >
      <div
        style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}
      >
        {[
          { label: "train", value: train, set: setTrain },
          { label: "val", value: val, set: setVal },
          { label: "test", value: test, set: setTest },
        ].map(({ label, value, set }) => (
          <label
            key={label}
            style={{ fontSize: 12, color: COLORS.muted, fontWeight: 600 }}
          >
            {label}
            <input
              type="number"
              step="0.05"
              min="0"
              max="1"
              value={value}
              onChange={(e) => set(parseFloat(e.target.value) || 0)}
              onBlur={submit}
              style={inputStyle}
            />
          </label>
        ))}
      </div>
      {error && (
        <div
          style={{
            color: COLORS.dangerDark,
            fontSize: 12,
            marginTop: 8,
            padding: "8px 10px",
            background: "rgba(178,65,52,0.1)",
            border: "1px solid rgba(178,65,52,0.18)",
            borderRadius: 8,
          }}
        >
          {error}
        </div>
      )}
    </Card>
  );
}
