import { COLORS } from "../../theme";
import type { ImageItem, ImageListResponse } from "../../types/annotation";
import type { SplitName } from "../../types/project";

interface Props {
  data: ImageListResponse;
  currentId: number | null;
  onSelect: (img: ImageItem) => void;
}

const SPLIT_COLOR: Record<SplitName, string> = {
  train: "#d46b36",
  val: "#b67a13",
  test: "#7e57c2",
};

export function ImageList({ data, currentId, onSelect }: Props): JSX.Element {
  const total = data.items.length;
  const annotated = data.items.filter((i) => i.annotation_count > 0).length;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div
        style={{
          padding: "12px 14px 10px",
          borderBottom: `1px solid ${COLORS.softBorder}`,
          fontSize: 11,
          color: COLORS.muted,
          display: "flex",
          alignItems: "baseline",
          justifyContent: "space-between",
        }}
      >
        <span style={{ fontWeight: 700, color: COLORS.ink, fontSize: 12 }}>
          图像列表
        </span>
        <span>
          <span style={{ color: COLORS.successDark, fontWeight: 700 }}>
            {annotated}
          </span>
          <span style={{ color: COLORS.faint }}> / </span>
          <span style={{ color: COLORS.ink }}>{total}</span>
        </span>
      </div>

      <div style={{ flex: 1, overflowY: "auto", padding: "6px 0" }}>
        {data.items.map((img, idx) => {
          const active = img.id === currentId;
          return (
            <div
              key={img.id}
              onClick={() => onSelect(img)}
              title={img.filename}
              style={{
                padding: "7px 12px 7px 10px",
                background: active
                  ? "linear-gradient(90deg, rgba(212,107,54,0.16), rgba(212,107,54,0.04))"
                  : "transparent",
                color: active ? COLORS.accentStrong : COLORS.ink,
                cursor: "pointer",
                borderLeft: `3px solid ${
                  active ? COLORS.accent : "transparent"
                }`,
                display: "flex",
                alignItems: "center",
                gap: 8,
                fontSize: 12,
                lineHeight: 1.4,
              }}
            >
              <span
                style={{
                  width: 26,
                  flexShrink: 0,
                  textAlign: "right",
                  color: COLORS.faint,
                  fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
                  fontSize: 10,
                }}
              >
                {idx + 1}
              </span>
              <span
                style={{
                  width: 6,
                  height: 6,
                  borderRadius: "50%",
                  background: SPLIT_COLOR[img.split],
                  flexShrink: 0,
                }}
                title={img.split}
              />
              <span
                style={{
                  flex: 1,
                  minWidth: 0,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                  direction: "rtl",
                  textAlign: "left",
                  fontWeight: active ? 700 : 500,
                }}
              >
                {img.filename}
              </span>
            </div>
          );
        })}
      </div>

      <div
        style={{
          padding: "10px 14px 12px",
          borderTop: `1px solid ${COLORS.softBorder}`,
          fontSize: 11,
          color: COLORS.muted,
          display: "flex",
          flexDirection: "column",
          gap: 8,
        }}
      >
        {(["train", "val", "test"] as const).map((s) => {
          const p = data.progress[s];
          const pct = p.total > 0 ? (p.annotated / p.total) * 100 : 0;
          return (
            <div key={s}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  marginBottom: 3,
                }}
              >
                <span style={{ color: SPLIT_COLOR[s], fontWeight: 700 }}>
                  {s}
                </span>
                <span style={{ color: COLORS.faint }}>
                  {p.annotated}/{p.total}
                </span>
              </div>
              <div
                style={{
                  height: 5,
                  borderRadius: 999,
                  background: "rgba(87,66,44,0.08)",
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    width: `${pct}%`,
                    height: "100%",
                    background: SPLIT_COLOR[s],
                    transition: "width 200ms",
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
