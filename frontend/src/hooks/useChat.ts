import { useCallback, useState } from "react";

import { streamChat } from "../api/chat";
import type { ChatMessage } from "../types/project";

export function useChat(pid: number, initial: ChatMessage[]) {
  const [messages, setMessages] = useState<ChatMessage[]>(initial);
  const [sending, setSending] = useState(false);

  const send = useCallback(
    async (content: string): Promise<void> => {
      setMessages((prev) => [
        ...prev,
        { role: "user", content, tool_call_id: null, tool_name: null },
      ]);
      setSending(true);
      try {
        for await (const event of streamChat(pid, content)) {
          if (event.type === "message") {
            setMessages((prev) => [...prev, event.data]);
          } else if (event.type === "done") {
            break;
          }
        }
      } finally {
        setSending(false);
      }
    },
    [pid],
  );

  return { messages, sending, send, setMessages };
}
