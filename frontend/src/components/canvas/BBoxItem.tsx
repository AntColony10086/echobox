import { useEffect, useRef } from "react";
import { Group, Rect, Text, Transformer } from "react-konva";

import type { Annotation } from "../../types/annotation";

interface Props {
  ann: Annotation;
  scale: number;
  offsetX: number;
  offsetY: number;
  selected: boolean;
  onSelect: () => void;
  onChange: (bbox: [number, number, number, number]) => void;
}

export function BBoxItem({
  ann,
  scale,
  offsetX,
  offsetY,
  selected,
  onSelect,
  onChange,
}: Props): JSX.Element {
  const [x1, y1, x2, y2] = ann.bbox;
  const dx = offsetX + x1 * scale;
  const dy = offsetY + y1 * scale;
  const dw = (x2 - x1) * scale;
  const dh = (y2 - y1) * scale;
  const isPending = ann.source === "geco2_pending";
  const stroke = ann.label.color;
  const fade = isPending ? 0.5 : 1.0;
  const lowConfidence = ann.score !== null && ann.score < 0.5;

  // Refs needed for Transformer to attach to the bbox.
  const rectRef = useRef<any>(null);
  const trRef = useRef<any>(null);

  // Wire the Transformer to the rect whenever selection toggles on.
  useEffect(() => {
    if (selected && rectRef.current && trRef.current) {
      trRef.current.nodes([rectRef.current]);
      trRef.current.getLayer()?.batchDraw();
    }
  }, [selected]);

  // Convert canvas-coordinate bbox back to image coordinates and emit onChange.
  const emitChange = (
    canvasX: number,
    canvasY: number,
    canvasW: number,
    canvasH: number,
  ): void => {
    const ix1 = Math.round((canvasX - offsetX) / scale);
    const iy1 = Math.round((canvasY - offsetY) / scale);
    const ix2 = Math.round((canvasX + canvasW - offsetX) / scale);
    const iy2 = Math.round((canvasY + canvasH - offsetY) / scale);
    onChange([
      Math.min(ix1, ix2),
      Math.min(iy1, iy2),
      Math.max(ix1, ix2),
      Math.max(iy1, iy2),
    ]);
  };

  return (
    <>
      <Group x={dx} y={dy}>
        <Rect
          ref={rectRef}
          width={dw}
          height={dh}
          stroke={stroke}
          strokeWidth={selected ? 3 : 2}
          dash={isPending ? [6, 4] : undefined}
          opacity={fade * (lowConfidence ? 0.7 : 1.0)}
          fill={selected ? `${stroke}33` : undefined}
          draggable={selected}
          onClick={onSelect}
          onTap={onSelect}
          onDragEnd={(e) => {
            const node = e.target;
            const newCanvasX = dx + node.x();
            const newCanvasY = dy + node.y();
            // reset drag offset so React re-render lines back up cleanly
            node.x(0);
            node.y(0);
            emitChange(newCanvasX, newCanvasY, dw, dh);
          }}
          onTransformEnd={() => {
            const node = rectRef.current;
            if (!node) return;
            const sx = node.scaleX();
            const sy = node.scaleY();
            const newCanvasX = dx + node.x();
            const newCanvasY = dy + node.y();
            const newCanvasW = Math.max(4, node.width() * sx);
            const newCanvasH = Math.max(4, node.height() * sy);
            // bake transform: clear scale + offset before next render
            node.scaleX(1);
            node.scaleY(1);
            node.x(0);
            node.y(0);
            emitChange(newCanvasX, newCanvasY, newCanvasW, newCanvasH);
          }}
        />
        <Text
          text={`${ann.label.name}${
            ann.score !== null ? ` ${ann.score.toFixed(2)}` : ""
          }`}
          fontSize={11}
          fill="white"
          x={2}
          y={-14}
          padding={2}
          listening={false}
        />
      </Group>
      {selected && (
        <Transformer
          ref={trRef}
          rotateEnabled={false}
          keepRatio={false}
          ignoreStroke
          flipEnabled={false}
          enabledAnchors={[
            "top-left",
            "top-center",
            "top-right",
            "middle-left",
            "middle-right",
            "bottom-left",
            "bottom-center",
            "bottom-right",
          ]}
          anchorSize={9}
          anchorStroke={stroke}
          anchorFill="white"
          borderStroke={stroke}
          borderDash={[4, 4]}
          boundBoxFunc={(_oldBox, newBox) => {
            // Prevent collapse to invisible
            if (newBox.width < 4 || newBox.height < 4) return _oldBox;
            return newBox;
          }}
        />
      )}
    </>
  );
}
