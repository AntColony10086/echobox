import { useEffect, useState } from "react";

export function useImageElement(src: string): HTMLImageElement | null {
  const [img, setImg] = useState<HTMLImageElement | null>(null);

  useEffect(() => {
    setImg(null);
    const el = new window.Image();
    el.onload = () => setImg(el);
    el.onerror = () => setImg(null);
    el.src = src;
    return () => {
      el.onload = null;
      el.onerror = null;
    };
  }, [src]);

  return img;
}
