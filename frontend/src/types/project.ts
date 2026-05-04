export type ProjectStatus = "draft" | "ready" | "annotating" | "exported";
export type ExportFormat = "coco" | "yolo" | "voc" | "ls_json";
export type SplitName = "train" | "val" | "test";
export type MessageRole = "user" | "assistant" | "tool" | "system";

export interface Label {
  name: string;
  color: string;
}

export interface ChatMessage {
  role: MessageRole;
  content: string;
  tool_call_id: string | null;
  tool_name: string | null;
  created_at?: string;
}

export interface Project {
  id: number;
  name: string;
  source_folder: string;
  workspace_path: string;
  status: ProjectStatus;
  export_format: ExportFormat | null;
  train_ratio: number;
  val_ratio: number;
  test_ratio: number;
  labels: Label[];
  image_count: number;
  messages?: ChatMessage[];
}

export interface CreateProjectRequest {
  source_folder: string;
  name?: string;
  initial_labels?: string[];
  train_val_test?: [number, number, number];
  export_format?: ExportFormat;
}
