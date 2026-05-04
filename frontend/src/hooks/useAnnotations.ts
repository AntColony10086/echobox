import { useCallback, useEffect, useState } from "react";

import {
  bulkAnnotations,
  deleteAnnotation,
  listAnnotations,
  predictSimilar,
  updateAnnotation,
} from "../api/annotations";
import type { Annotation } from "../types/annotation";

export function useAnnotations(pid: number, iid: number | null) {
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [lastElapsedMs, setLastElapsedMs] = useState<number | null>(null);
  const [predictBusy, setPredictBusy] = useState(false);

  const refetch = useCallback(async (): Promise<void> => {
    if (iid == null) return;
    const items = await listAnnotations(iid);
    setAnnotations(items);
  }, [iid]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  const drawExemplar = useCallback(
    async (
      labelId: number,
      bbox: [number, number, number, number],
      scoreThreshold: number = 0.25,
    ): Promise<void> => {
      if (iid == null) return;
      setPredictBusy(true);
      try {
        const res = await predictSimilar(
          pid,
          iid,
          labelId,
          bbox,
          200,
          scoreThreshold,
        );
        setLastElapsedMs(res.elapsed_ms);
        await refetch();
      } finally {
        setPredictBusy(false);
      }
    },
    [pid, iid, refetch],
  );

  const updateBbox = useCallback(
    async (
      aid: number,
      bbox: [number, number, number, number],
      version: number,
    ): Promise<void> => {
      const updated = await updateAnnotation(
        aid,
        { x1: bbox[0], y1: bbox[1], x2: bbox[2], y2: bbox[3] },
        version,
      );
      setAnnotations((prev) => prev.map((a) => (a.id === aid ? updated : a)));
    },
    [],
  );

  const accept = useCallback(
    async (aid: number, version: number): Promise<void> => {
      const updated = await updateAnnotation(
        aid,
        { source: "geco2_accepted" },
        version,
      );
      setAnnotations((prev) => prev.map((a) => (a.id === aid ? updated : a)));
    },
    [],
  );

  const changeLabel = useCallback(
    async (aid: number, labelId: number, version: number): Promise<void> => {
      const updated = await updateAnnotation(
        aid,
        { label_id: labelId },
        version,
      );
      setAnnotations((prev) => prev.map((a) => (a.id === aid ? updated : a)));
    },
    [],
  );

  const remove = useCallback(async (aid: number): Promise<void> => {
    await deleteAnnotation(aid);
    setAnnotations((prev) => prev.filter((a) => a.id !== aid));
  }, []);

  const acceptAll = useCallback(async (): Promise<void> => {
    if (iid == null) return;
    await bulkAnnotations(pid, iid, "accept_all");
    await refetch();
  }, [pid, iid, refetch]);

  const rejectAll = useCallback(async (): Promise<void> => {
    if (iid == null) return;
    await bulkAnnotations(pid, iid, "reject_all");
    await refetch();
  }, [pid, iid, refetch]);

  return {
    annotations,
    predictBusy,
    lastElapsedMs,
    drawExemplar,
    updateBbox,
    accept,
    changeLabel,
    remove,
    acceptAll,
    rejectAll,
    refetch,
  };
}
