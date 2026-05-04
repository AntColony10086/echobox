import { apiClient } from "./client";
import type {
  CreateProjectRequest,
  ExportFormat,
  Project,
} from "../types/project";

export interface ProjectSummary {
  id: number;
  name: string;
  source_folder: string;
  status: string;
  image_count: number;
  label_count: number;
  updated_at: string | null;
}

export async function listProjects(): Promise<ProjectSummary[]> {
  const { data } = await apiClient.get<ProjectSummary[]>("/projects");
  return data;
}

export async function deleteProject(pid: number): Promise<void> {
  await apiClient.delete(`/projects/${pid}`);
}

export async function createProject(
  req: CreateProjectRequest,
): Promise<Project> {
  const { data } = await apiClient.post<Project>("/projects", req);
  return data;
}

export async function getProject(pid: number): Promise<Project> {
  const { data } = await apiClient.get<Project>(`/projects/${pid}`);
  return data;
}

export async function patchFolder(
  pid: number,
  folder: string,
): Promise<Project> {
  const { data } = await apiClient.patch<Project>(`/projects/${pid}/folder`, {
    folder,
  });
  return data;
}

export async function patchSplits(
  pid: number,
  train: number,
  val: number,
  test: number,
): Promise<Project> {
  const { data } = await apiClient.patch<Project>(`/projects/${pid}/splits`, {
    train,
    val,
    test,
  });
  return data;
}

export async function patchFormat(
  pid: number,
  format: ExportFormat,
): Promise<Project> {
  const { data } = await apiClient.patch<Project>(`/projects/${pid}/format`, {
    format,
  });
  return data;
}

export async function addLabel(
  pid: number,
  name: string,
  color?: string,
): Promise<{ id: number; name: string; color: string }> {
  const { data } = await apiClient.post(`/projects/${pid}/labels`, {
    name,
    color,
  });
  return data;
}

export async function deleteLabel(
  pid: number,
  name: string,
  cascade: boolean = false,
): Promise<void> {
  const params = cascade ? { cascade: true } : {};
  await apiClient.delete(
    `/projects/${pid}/labels/${encodeURIComponent(name)}`,
    {
      params,
    },
  );
}

export async function finalizeProject(
  pid: number,
): Promise<{ status: string; id: number }> {
  const { data } = await apiClient.post(`/projects/${pid}/finalize`);
  return data;
}
