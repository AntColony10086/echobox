import { useEffect, useRef, useState } from "react";

import { COLORS, FONT_STACK, GRADIENTS } from "../theme";
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
        background: "rgba(255,250,242,0.6)",
        borderRadius: 16,
        border: `1px solid ${COLORS.softBorder}`,
        overflow: "hidden",
        fontFamily: FONT_STACK,
      }}
    >
      <div
        ref={scrollRef}
        style={{
          flex: 1,
          overflowY: "auto",
          padding: 14,
          fontSize: 13,
          minHeight: 0,
        }}
      >
        {messages.length === 0 && (
          <div style={{ color: COLORS.muted }}>
            和 Agent 对话开始你的项目。试试："扫描 /path/to/images"
          </div>
        )}
        {messages.map((m, i) => (
          <ChatBubble key={i} m={m} />
        ))}
        {sending && (
          <div style={{ color: COLORS.muted, fontStyle: "italic" }}>
            Agent 思考中…
          </div>
        )}
      </div>
      <div
        style={{
          padding: 10,
          borderTop: `1px solid ${COLORS.softBorder}`,
          display: "flex",
          gap: 8,
          background: "rgba(255,250,242,0.7)",
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
          style={{
            flex: 1,
            padding: "8px 12px",
            border: `1px solid ${COLORS.cardBorder}`,
            borderRadius: 999,
            background: "rgba(255,255,255,0.9)",
            color: COLORS.ink,
            fontSize: 13,
            fontFamily: FONT_STACK,
            outline: "none",
          }}
        />
        <button
          onClick={submit}
          disabled={sending || !input.trim()}
          style={{
            padding: "0 18px",
            height: 34,
            border: "none",
            borderRadius: 999,
            background:
              sending || !input.trim()
                ? "rgba(212,107,54,0.35)"
                : GRADIENTS.accent,
            color: "white",
            fontWeight: 600,
            fontFamily: FONT_STACK,
            fontSize: 13,
            cursor: sending || !input.trim() ? "not-allowed" : "pointer",
            boxShadow:
              sending || !input.trim()
                ? "none"
                : "0 6px 14px rgba(212,107,54,0.28)",
          }}
        >
          发送
        </button>
      </div>
    </div>
  );
}

function ChatBubble({ m }: { m: ChatMessage }): JSX.Element {
  const colors = {
    user: {
      bg: GRADIENTS.accent,
      fg: "white",
      align: "flex-end",
    },
    assistant: {
      bg: "rgba(255,255,255,0.85)",
      fg: COLORS.ink,
      align: "flex-start",
    },
    tool: {
      bg: "rgba(182,122,19,0.12)",
      fg: COLORS.warnDark,
      align: "flex-start",
    },
    system: { bg: "transparent", fg: COLORS.faint, align: "center" },
  } as const;
  const c = colors[m.role];
  return (
    <div style={{ display: "flex", justifyContent: c.align, marginBottom: 8 }}>
      <div
        style={{
          background: c.bg,
          color: c.fg,
          padding: "8px 14px",
          borderRadius: 14,
          maxWidth: "85%",
          fontFamily: m.role === "tool" ? "monospace" : FONT_STACK,
          fontSize: m.role === "tool" ? 11 : 13,
          whiteSpace: "pre-wrap",
          border:
            m.role === "assistant" ? `1px solid ${COLORS.softBorder}` : "none",
          boxShadow:
            m.role === "user" ? "0 6px 14px rgba(212,107,54,0.22)" : "none",
        }}
      >
        {m.role === "tool" && m.tool_name && (
          <div style={{ fontWeight: 700, opacity: 0.85 }}>{m.tool_name}</div>
        )}
        {m.content || (m.role === "assistant" ? "(调用工具中…)" : "")}
      </div>
    </div>
  );
}
