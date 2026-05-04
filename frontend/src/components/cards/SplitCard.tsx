import { useState } from "react";

import { patchSplits } from "../../api/projects";
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

  return (
    <Card
      title={`Train / Val / Test 切分 (sum=${sum.toFixed(3)})`}
      status={status}
    >
      <div
        style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}
      >
        {[
          { label: "train", value: train, set: setTrain },
          { label: "val", value: val, set: setVal },
          { label: "test", value: test, set: setTest },
        ].map(({ label, value, set }) => (
          <label key={label} style={{ fontSize: 12 }}>
            {label}
            <input
              type="number"
              step="0.05"
              min="0"
              max="1"
              value={value}
              onChange={(e) => set(parseFloat(e.target.value) || 0)}
              onBlur={submit}
              style={{ width: "100%", padding: 4 }}
            />
          </label>
        ))}
      </div>
      {error && (
        <div style={{ color: "#e53e3e", fontSize: 12, marginTop: 4 }}>
          {error}
        </div>
      )}
    </Card>
  );
}
