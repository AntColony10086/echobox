import { useEffect, useState } from "react";

import { createExport, getDefaultExportDir } from "../../api/exports";
import type { ExportResult } from "../../api/exports";
import { COLORS, FONT_STACK, GRADIENTS } from "../../theme";
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
        // ignore
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
      <div style={{ marginBottom: 12 }}>
        <label
          style={{
            fontSize: 12,
            color: COLORS.muted,
            display: "block",
            marginBottom: 6,
            fontWeight: 600,
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
                padding: "7px 8px",
                background:
                  format === f ? GRADIENTS.accent : "rgba(255,255,255,0.7)",
                color: format === f ? "white" : COLORS.ink,
                border: `1px solid ${
                  format === f ? "transparent" : COLORS.cardBorder
                }`,
                borderRadius: 999,
                fontSize: 12,
                cursor: "pointer",
                fontWeight: format === f ? 700 : 600,
                fontFamily: FONT_STACK,
                boxShadow:
                  format === f ? "0 6px 14px rgba(212,107,54,0.24)" : "none",
              }}
            >
              {f.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      <div style={{ marginBottom: 12 }}>
        <label
          style={{
            fontSize: 12,
            color: COLORS.muted,
            display: "block",
            marginBottom: 6,
            fontWeight: 600,
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
            padding: "8px 12px",
            background: "rgba(255,255,255,0.85)",
            color: COLORS.ink,
            border: `1px solid ${COLORS.cardBorder}`,
            borderRadius: 10,
            fontSize: 12,
            fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
            boxSizing: "border-box",
            outline: "none",
          }}
        />
        <div style={{ fontSize: 11, color: COLORS.muted, marginTop: 6 }}>
          默认：项目 workspace 下的{" "}
          <code style={{ color: COLORS.ink }}>exports/</code>
          。导出会在该目录里建一个{" "}
          <code style={{ color: COLORS.ink }}>
            YYYY-MM-DDTHH-MM-SS-{format}/
          </code>{" "}
          子目录（多次导出不互相覆盖）。
        </div>
      </div>

      <label
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          fontSize: 12,
          color: COLORS.muted,
          marginBottom: 12,
        }}
      >
        <input
          type="checkbox"
          checked={includePending}
          onChange={(e) => setIncludePending(e.target.checked)}
          disabled={busy}
          style={{ accentColor: COLORS.accent }}
        />
        含 GECO2 待审核框（geco2_pending）
      </label>

      <button
        onClick={submit}
        disabled={busy}
        style={{
          width: "100%",
          padding: "10px 14px",
          background: busy ? "rgba(45,143,103,0.4)" : GRADIENTS.success,
          color: "white",
          border: "none",
          borderRadius: 999,
          fontSize: 13,
          fontWeight: 700,
          cursor: busy ? "wait" : "pointer",
          fontFamily: FONT_STACK,
          boxShadow: busy ? "none" : "0 8px 18px rgba(45,143,103,0.28)",
        }}
      >
        {busy ? "导出中…" : "▼ 导出数据集"}
      </button>

      {error && (
        <div
          style={{
            marginTop: 10,
            padding: "10px 12px",
            background: "rgba(178,65,52,0.1)",
            color: COLORS.dangerDark,
            border: "1px solid rgba(178,65,52,0.18)",
            borderRadius: 12,
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
            marginTop: 10,
            padding: "10px 12px",
            background: "rgba(45,143,103,0.1)",
            color: COLORS.successDark,
            border: "1px solid rgba(45,143,103,0.2)",
            borderRadius: 12,
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
              fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
              fontSize: 11,
              color: COLORS.ink,
            }}
          >
            {result.output_dir}
          </code>
        </div>
      )}
    </Card>
  );
}
