import { apiClient } from "./client";
import type {
  Annotation,
  AnnotationSource,
  PredictSimilarResponse,
} from "../types/annotation";

export async function listAnnotations(iid: number): Promise<Annotation[]> {
  const { data } = await apiClient.get<{ items: Annotation[] }>(
    `/images/${iid}/annotations`,
  );
  return data.items;
}

export async function predictSimilar(
  pid: number,
  iid: number,
  labelId: number,
  exemplarBbox: [number, number, number, number],
  maxPredictions = 200,
  scoreThreshold = 0.25,
): Promise<PredictSimilarResponse> {
  const { data } = await apiClient.post<PredictSimilarResponse>(
    `/projects/${pid}/images/${iid}/predict-similar`,
    {
      label_id: labelId,
      exemplar_bbox: exemplarBbox,
      max_predictions: maxPredictions,
      score_threshold: scoreThreshold,
    },
  );
  return data;
}

export async function updateAnnotation(
  aid: number,
  changes: Partial<{
    x1: number;
    y1: number;
    x2: number;
    y2: number;
    label_id: number;
    source: AnnotationSource;
  }>,
  version: number,
): Promise<Annotation> {
  const { data } = await apiClient.put<Annotation>(`/annotations/${aid}`, {
    ...changes,
    version,
  });
  return data;
}

export async function deleteAnnotation(aid: number): Promise<void> {
  await apiClient.delete(`/annotations/${aid}`);
}

export async function bulkAnnotations(
  pid: number,
  iid: number,
  action: "accept_all" | "reject_all",
): Promise<{ affected: number; action: string }> {
  const { data } = await apiClient.patch(
    `/projects/${pid}/images/${iid}/annotations/bulk`,
    { action },
  );
  return data;
}
