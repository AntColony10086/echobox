import { useEffect, useState } from "react";

import { createExport, getDefaultExportDir } from "../../api/exports";
import type { ExportResult } from "../../api/exports";
import type { ExportFormat } from "../../types/project";
import { Card } from "../ui/Card";

interface Props {
  pid: number;
  projectFormat: ExportFormat | null;
}

const FORMATS: ExportFormat[] = ["coco", "yolo", "voc", "ls_json"];

export function ExportPanel({ pid, projectFormat }: Props): JSX.Element {
  const [defaultDir, setDefaultDir] = useState<string>("");
  const [outputDir, setOutputDir] = useState<string>("");
  const [format, setFormat] = useState<ExportFormat>(projectFormat ?? "coco");
  const [includePending, setIncludePending] = useState<boolean>(false);
  const [busy, setBusy] = useState<boolean>(false);
  const [result, setResult] = useState<ExportResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDefaultExportDir(pid)
      .then((d) => {
        setDefaultDir(d);
        setOutputDir((cur) => cur || d);
      })
      .catch(() => {
        // ignore — placeholder will just be empty
      });
  }, [pid]);

  const submit = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const r = await createExport(pid, {
        format,
        output_dir:
          outputDir && outputDir !== defaultDir ? outputDir : undefined,
        include_pending: includePending,
      });
      setResult(r);
    } catch (e: unknown) {
      const msg =
        (e as { response?: { data?: { error?: { message?: string } } } })
          .response?.data?.error?.message ?? String(e);
      setError(msg);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card title="导出数据集">
      <div style={{ marginBottom: 10 }}>
        <label
          style={{
            fontSize: 12,
            color: "#4a5568",
            display: "block",
            marginBottom: 4,
          }}
        >
          格式
        </label>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr 1fr 1fr",
            gap: 6,
          }}
        >
          {FORMATS.map((f) => (
            <button
              key={f}
              onClick={() => setFormat(f)}
              disabled={busy}
              style={{
                padding: "6px 8px",
                background: format === f ? "#3182ce" : "white",
                color: format === f ? "white" : "#4a5568",
                border: `1px solid ${format === f ? "#3182ce" : "#cbd5e0"}`,
                borderRadius: 4,
                fontSize: 12,
                cursor: "pointer",
                fontWeight: format === f ? 700 : 400,
              }}
            >
              {f.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      <div style={{ marginBottom: 10 }}>
        <label
          style={{
            fontSize: 12,
            color: "#4a5568",
            display: "block",
            marginBottom: 4,
          }}
        >
          输出目录（绝对路径，~ 自动展开）
        </label>
        <input
          type="text"
          value={outputDir}
          onChange={(e) => setOutputDir(e.target.value)}
          placeholder={defaultDir || "/abs/path/to/output"}
          disabled={busy}
          spellCheck={false}
          style={{
            width: "100%",
            padding: "6px 8px",
            background: "white",
            color: "#2d3748",
            border: "1px solid #cbd5e0",
            borderRadius: 4,
            fontSize: 12,
            fontFamily: "monospace",
            boxSizing: "border-box",
          }}
        />
        <div style={{ fontSize: 11, color: "#718096", marginTop: 4 }}>
          默认：项目 workspace 下的{" "}
          <code style={{ color: "#4a5568" }}>exports/</code>
          。导出会在该目录里建一个{" "}
          <code style={{ color: "#4a5568" }}>
            YYYY-MM-DDTHH-MM-SS-{format}/
          </code>{" "}
          子目录（多次导出不互相覆盖）。
        </div>
      </div>

      <label
        style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          fontSize: 12,
          color: "#4a5568",
          marginBottom: 10,
        }}
      >
        <input
          type="checkbox"
          checked={includePending}
          onChange={(e) => setIncludePending(e.target.checked)}
          disabled={busy}
        />
        含 GECO2 待审核框（geco2_pending）
      </label>

      <button
        onClick={submit}
        disabled={busy}
        style={{
          width: "100%",
          padding: "8px 12px",
          background: busy ? "#a0aec0" : "#48bb78",
          color: "white",
          border: "none",
          borderRadius: 4,
          fontSize: 13,
          fontWeight: 700,
          cursor: busy ? "wait" : "pointer",
        }}
      >
        {busy ? "导出中…" : "▼ 导出数据集"}
      </button>

      {error && (
        <div
          style={{
            marginTop: 8,
            padding: 8,
            background: "#fed7d7",
            color: "#742a2a",
            borderRadius: 4,
            fontSize: 12,
            wordBreak: "break-word",
          }}
        >
          {error}
        </div>
      )}

      {result && (
        <div
          style={{
            marginTop: 8,
            padding: 8,
            background: "#c6f6d5",
            color: "#22543d",
            borderRadius: 4,
            fontSize: 12,
            wordBreak: "break-all",
          }}
        >
          ✓ 导出完成（{result.elapsed_ms} ms）
          <br />
          <span style={{ fontWeight: 700 }}>
            {result.stats.total_images}
          </span>{" "}
          张图，
          <span style={{ fontWeight: 700 }}>
            {result.stats.total_annotations}
          </span>{" "}
          个标注
          <br />
          <code
            style={{
              fontFamily: "monospace",
              fontSize: 11,
              color: "#1a202c",
            }}
          >
            {result.output_dir}
          </code>
        </div>
      )}
    </Card>
  );
}
