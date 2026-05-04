import { apiClient } from "./client";
import type { ExportFormat, SplitName } from "../types/project";

export interface ExportResult {
  export_id: string;
  format: ExportFormat;
  output_dir: string;
  files: string[];
  stats: {
    total_images: number;
    total_annotations: number;
    by_split: Record<string, { images: number; annotations: number }>;
  };
  elapsed_ms: number;
}

export async function getDefaultExportDir(pid: number): Promise<string> {
  const { data } = await apiClient.get<{ default_output_dir: string }>(
    `/projects/${pid}/exports/default-dir`,
  );
  return data.default_output_dir;
}

export async function createExport(
  pid: number,
  opts: {
    format?: ExportFormat;
    output_dir?: string;
    include_pending?: boolean;
    splits?: SplitName[];
  } = {},
): Promise<ExportResult> {
  const body: Record<string, unknown> = {};
  if (opts.format) body.format = opts.format;
  if (opts.output_dir) body.output_dir = opts.output_dir;
  if (opts.include_pending !== undefined)
    body.include_pending = opts.include_pending;
  if (opts.splits) body.splits = opts.splits;

  const { data } = await apiClient.post<ExportResult>(
    `/projects/${pid}/exports`,
    body,
  );
  return data;
}
