import { Layer } from "react-konva";

import type { Annotation } from "../../types/annotation";

import { BBoxItem } from "./BBoxItem";

interface Props {
  annotations: Annotation[];
  selectedId: number | null;
  scale: number;
  offsetX: number;
  offsetY: number;
  onSelect: (id: number | null) => void;
  onChange: (id: number, bbox: [number, number, number, number]) => void;
}

export function BBoxLayer({
  annotations,
  selectedId,
  scale,
  offsetX,
  offsetY,
  onSelect,
  onChange,
}: Props): JSX.Element {
  return (
    <Layer>
      {annotations.map((ann) => (
        <BBoxItem
          key={ann.id}
          ann={ann}
          scale={scale}
          offsetX={offsetX}
          offsetY={offsetY}
          selected={selectedId === ann.id}
          onSelect={() => onSelect(ann.id)}
          onChange={(b) => onChange(ann.id, b)}
        />
      ))}
    </Layer>
  );
}
