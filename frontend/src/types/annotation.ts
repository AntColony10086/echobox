import type { Label, SplitName } from "./project";

export type AnnotationSource =
  | "user"
  | "geco2_pending"
  | "geco2_accepted"
  | "user_edited";

export interface Annotation {
  id: number;
  image_id: number;
  label: Label & { id: number };
  bbox: [number, number, number, number];
  score: number | null;
  source: AnnotationSource;
  version: number;
}

export interface ImageItem {
  id: number;
  filename: string;
  abs_path: string;
  width: number;
  height: number;
  split: SplitName;
  index_in_project: number;
  annotation_count: number;
}

export interface ImageListResponse {
  total: number;
  items: ImageItem[];
  progress: Record<SplitName, { total: number; annotated: number }>;
}

export interface PredictSimilarResponse {
  created: Annotation[];
  elapsed_ms: number;
}
