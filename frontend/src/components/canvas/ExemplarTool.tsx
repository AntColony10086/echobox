import { useState } from "react";
import { Layer, Rect } from "react-konva";

interface Props {
  active: boolean;
  scale: number;
  offsetX: number;
  offsetY: number;
  onDrawn: (bbox: [number, number, number, number]) => void;
}

export function ExemplarTool({
  active,
  scale,
  offsetX,
  offsetY,
  onDrawn,
}: Props): JSX.Element | null {
  const [start, setStart] = useState<{ x: number; y: number } | null>(null);
  const [end, setEnd] = useState<{ x: number; y: number } | null>(null);

  if (!active) return null;

  const onMouseDown = (e: any): void => {
    const stage = e.target.getStage();
    const pos = stage.getPointerPosition();
    if (!pos) return;
    setStart(pos);
    setEnd(pos);
  };

  const onMouseMove = (e: any): void => {
    if (!start) return;
    const stage = e.target.getStage();
    const pos = stage.getPointerPosition();
    if (!pos) return;
    setEnd(pos);
  };

  const onMouseUp = (): void => {
    if (!start || !end) {
      setStart(null);
      setEnd(null);
      return;
    }
    const x1 = Math.round((Math.min(start.x, end.x) - offsetX) / scale);
    const y1 = Math.round((Math.min(start.y, end.y) - offsetY) / scale);
    const x2 = Math.round((Math.max(start.x, end.x) - offsetX) / scale);
    const y2 = Math.round((Math.max(start.y, end.y) - offsetY) / scale);
    if (x2 - x1 >= 4 && y2 - y1 >= 4) {
      onDrawn([x1, y1, x2, y2]);
    }
    setStart(null);
    setEnd(null);
  };

  return (
    <Layer
      onMouseDown={onMouseDown}
      onMouseMove={onMouseMove}
      onMouseUp={onMouseUp}
      onTouchStart={onMouseDown}
      onTouchMove={onMouseMove}
      onTouchEnd={onMouseUp}
    >
      <Rect x={0} y={0} width={9999} height={9999} fill="rgba(0,0,0,0.01)" />
      {start && end && (
        <Rect
          x={Math.min(start.x, end.x)}
          y={Math.min(start.y, end.y)}
          width={Math.abs(end.x - start.x)}
          height={Math.abs(end.y - start.y)}
          stroke="#fbbf24"
          strokeWidth={2}
          dash={[8, 4]}
          fill="rgba(251,191,36,0.15)"
        />
      )}
    </Layer>
  );
}
