import { useCallback, useState } from "react";

export type SaveState = "idle" | "saving" | "saved" | "error";

export function useSaveState() {
  const [state, setState] = useState<SaveState>("idle");
  const [error, setError] = useState<string | null>(null);

  const wrap = useCallback(
    async <T>(fn: () => Promise<T>): Promise<T | null> => {
      setState("saving");
      setError(null);
      try {
        const result = await fn();
        setState("saved");
        return result;
      } catch (e) {
        setError(String(e));
        setState("error");
        return null;
      }
    },
    [],
  );

  return { state, error, wrap };
}
