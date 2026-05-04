import type { ChatMessage } from "../types/project";

export type ChatEvent =
  | { type: "message"; data: ChatMessage }
  | { type: "done" };

export async function* streamChat(
  pid: number,
  content: string,
): AsyncGenerator<ChatEvent, void, unknown> {
  const resp = await fetch(`/api/projects/${pid}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  if (!resp.ok || !resp.body) {
    throw new Error(`chat failed: ${resp.status}`);
  }
  const reader = resp.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let idx;
    while ((idx = buffer.indexOf("\n\n")) >= 0) {
      const chunk = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      const line = chunk.trim();
      if (!line.startsWith("data:")) continue;
      const payload = line.slice(5).trim();
      try {
        const event = JSON.parse(payload) as ChatEvent;
        yield event;
        if (event.type === "done") return;
      } catch {
        // skip malformed
      }
    }
  }
}
