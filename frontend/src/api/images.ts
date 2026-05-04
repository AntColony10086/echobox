import { apiClient } from "./client";
import type { ImageItem, ImageListResponse } from "../types/annotation";
import type { SplitName } from "../types/project";

export async function listImages(
  pid: number,
  split?: SplitName,
): Promise<ImageListResponse> {
  const params = split ? { split } : {};
  const { data } = await apiClient.get<ImageListResponse>(
    `/projects/${pid}/images`,
    { params },
  );
  return data;
}

export async function getImage(
  iid: number,
): Promise<ImageItem & { project_id: number }> {
  const { data } = await apiClient.get(`/images/${iid}`);
  return data;
}

export function imageFileUrl(iid: number): string {
  return `/api/images/${iid}/file`;
}
