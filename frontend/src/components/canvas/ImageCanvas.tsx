import { useRef, type ReactNode } from "react";
import { Layer, Rect, Stage, Text, Image as KImage } from "react-konva";

import { useImageElement } from "../../hooks/useImageElement";

interface Props {
  src: string;
  imageWidth: number;
  imageHeight: number;
  containerWidth: number;
  containerHeight: number;
  /** Multiplier applied on top of the fit-to-container scale. 1.0 = fit. */
  zoom?: number;
  children?: (ctx: {
    scale: number;
    offsetX: number;
    offsetY: number;
  }) => ReactNode;
}

export function ImageCanvas({
  src,
  imageWidth,
  imageHeight,
  containerWidth,
  containerHeight,
  zoom = 1,
  children,
}: Props): JSX.Element {
  const img = useImageElement(src);
  const stageRef = useRef<any>(null);

  // Guard against zero/negative container dimensions during initial mount.
  const safeW = Math.max(100, containerWidth);
  const safeH = Math.max(100, containerHeight);
  const safeImgW = Math.max(1, imageWidth);
  const safeImgH = Math.max(1, imageHeight);

  // Stage occupies (containerW * zoom) by (containerH * zoom) and is wrapped in
  // a scrollable div. Pan is native browser scroll.
  const stageW = safeW * zoom;
  const stageH = safeH * zoom;

  const scale = Math.min(stageW / safeImgW, stageH / safeImgH, zoom);
  const displayW = safeImgW * scale;
  const displayH = safeImgH * scale;
  const offsetX = (stageW - displayW) / 2;
  const offsetY = (stageH - displayH) / 2;

  return (
    <div
      style={{
        width: safeW,
        height: safeH,
        overflow: "auto",
        background: "#edf2f7",
      }}
    >
      <Stage
        ref={stageRef}
        width={stageW}
        height={stageH}
        style={{ background: "#edf2f7" }}
      >
        <Layer>
          {img ? (
            <KImage
              image={img}
              x={offsetX}
              y={offsetY}
              width={displayW}
              height={displayH}
            />
          ) : (
            <>
              <Rect
                x={offsetX}
                y={offsetY}
                width={displayW}
                height={displayH}
                fill="white"
                stroke="#cbd5e0"
                strokeWidth={1}
                dash={[8, 4]}
              />
              <Text
                x={offsetX}
                y={offsetY + displayH / 2 - 8}
                width={displayW}
                align="center"
                text={`图像加载中…\n${src}`}
                fontSize={12}
                fill="#718096"
              />
            </>
          )}
        </Layer>
        {children && children({ scale, offsetX, offsetY })}
      </Stage>
    </div>
  );
}
