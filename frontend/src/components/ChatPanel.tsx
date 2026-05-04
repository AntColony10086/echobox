import { useEffect, useRef, useState } from "react";

import type { ChatMessage } from "../types/project";

interface Props {
  messages: ChatMessage[];
  sending: boolean;
  onSend: (content: string) => void;
}

export function ChatPanel({ messages, sending, onSend }: Props): JSX.Element {
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  const submit = (): void => {
    if (!input.trim() || sending) return;
    onSend(input.trim());
    setInput("");
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        flex: 1,
        height: "100%",
        minHeight: 0,
        background: "#f7fafc",
        borderLeft: "1px solid #e2e8f0",
      }}
    >
      <div
        ref={scrollRef}
        style={{
          flex: 1,
          overflowY: "auto",
          padding: 12,
          fontSize: 13,
          minHeight: 0,
        }}
      >
        {messages.length === 0 && (
          <div style={{ color: "#a0aec0" }}>
            和 Agent 对话开始你的项目。试试："扫描 /path/to/images"
          </div>
        )}
        {messages.map((m, i) => (
          <ChatBubble key={i} m={m} />
        ))}
        {sending && (
          <div style={{ color: "#718096", fontStyle: "italic" }}>
            Agent 思考中…
          </div>
        )}
      </div>
      <div
        style={{
          padding: 8,
          borderTop: "1px solid #e2e8f0",
          display: "flex",
          gap: 6,
        }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
          placeholder="对 Agent 说话…"
          disabled={sending}
          style={{ flex: 1, padding: 6 }}
        />
        <button onClick={submit} disabled={sending || !input.trim()}>
          发送
        </button>
      </div>
    </div>
  );
}

function ChatBubble({ m }: { m: ChatMessage }): JSX.Element {
  const colors = {
    user: { bg: "#3182ce", fg: "white", align: "flex-end" },
    assistant: { bg: "#e2e8f0", fg: "#2d3748", align: "flex-start" },
    tool: { bg: "#fefcbf", fg: "#5a4307", align: "flex-start" },
    system: { bg: "transparent", fg: "#a0aec0", align: "center" },
  } as const;
  const c = colors[m.role];
  return (
    <div style={{ display: "flex", justifyContent: c.align, marginBottom: 8 }}>
      <div
        style={{
          background: c.bg,
          color: c.fg,
          padding: "6px 10px",
          borderRadius: 8,
          maxWidth: "85%",
          fontFamily: m.role === "tool" ? "monospace" : "inherit",
          fontSize: m.role === "tool" ? 11 : 13,
          whiteSpace: "pre-wrap",
        }}
      >
        {m.role === "tool" && m.tool_name && (
          <div style={{ fontWeight: 700, opacity: 0.8 }}>{m.tool_name}</div>
        )}
        {m.content || (m.role === "assistant" ? "(调用工具中…)" : "")}
      </div>
    </div>
  );
}
