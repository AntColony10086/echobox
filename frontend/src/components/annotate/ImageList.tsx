import type { ImageItem, ImageListResponse } from "../../types/annotation";
import type { SplitName } from "../../types/project";

interface Props {
  data: ImageListResponse;
  currentId: number | null;
  onSelect: (img: ImageItem) => void;
}

const SPLIT_COLOR: Record<SplitName, string> = {
  train: "#3182ce",
  val: "#d69e2e",
  test: "#9b5de5",
};

export function ImageList({ data, currentId, onSelect }: Props): JSX.Element {
  const total = data.items.length;
  const annotated = data.items.filter((i) => i.annotation_count > 0).length;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div
        style={{
          padding: "10px 12px 8px",
          borderBottom: "1px solid #e2e8f0",
          fontSize: 11,
          color: "#a0aec0",
          display: "flex",
          alignItems: "baseline",
          justifyContent: "space-between",
        }}
      >
        <span style={{ fontWeight: 700, color: "#2d3748", fontSize: 12 }}>
          图像列表
        </span>
        <span>
          <span style={{ color: "#48bb78", fontWeight: 700 }}>{annotated}</span>
          <span style={{ color: "#cbd5e0" }}> / </span>
          <span style={{ color: "#4a5568" }}>{total}</span>
        </span>
      </div>

      <div style={{ flex: 1, overflowY: "auto", padding: "4px 0" }}>
        {data.items.map((img, idx) => {
          const active = img.id === currentId;
          return (
            <div
              key={img.id}
              onClick={() => onSelect(img)}
              title={img.filename}
              style={{
                padding: "6px 10px 6px 8px",
                background: active ? "#ebf8ff" : "transparent",
                color: active ? "#2c5282" : "#4a5568",
                cursor: "pointer",
                borderLeft: `3px solid ${active ? "#3182ce" : "transparent"}`,
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
                  color: "#a0aec0",
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
                  fontWeight: active ? 600 : 400,
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
          padding: "8px 12px 10px",
          borderTop: "1px solid #e2e8f0",
          fontSize: 11,
          color: "#a0aec0",
          display: "flex",
          flexDirection: "column",
          gap: 6,
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
                  marginBottom: 2,
                }}
              >
                <span style={{ color: SPLIT_COLOR[s], fontWeight: 600 }}>
                  {s}
                </span>
                <span style={{ color: "#a0aec0" }}>
                  {p.annotated}/{p.total}
                </span>
              </div>
              <div
                style={{
                  height: 4,
                  borderRadius: 2,
                  background: "#edf2f7",
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
