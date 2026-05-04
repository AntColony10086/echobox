import { useEffect, useRef } from "react";

import { ChatPanel } from "../ChatPanel";
import { Modal } from "../ui/Modal";
import { useChat } from "../../hooks/useChat";
import type { ChatMessage } from "../../types/project";

interface Props {
  pid: number;
  initialMessages: ChatMessage[];
  onClose: () => void;
  onSync: () => void | Promise<void>;
}

export function ChatModal({
  pid,
  initialMessages,
  onClose,
  onSync,
}: Props): JSX.Element {
  const chat = useChat(pid, initialMessages);

  // After each agent reply, sync project state (cards reflect tool side-effects).
  const lastLenRef = useRef<number>(initialMessages.length);
  useEffect(() => {
    if (
      chat.messages.length > lastLenRef.current &&
      !chat.sending &&
      chat.messages.length > initialMessages.length
    ) {
      lastLenRef.current = chat.messages.length;
      onSync();
    }
  }, [chat.messages.length, chat.sending, initialMessages.length, onSync]);

  return (
    <Modal title="与 Agent 对话（配置项目）" onClose={onClose} width={640}>
      <div style={{ height: "62vh", display: "flex" }}>
        <ChatPanel
          messages={chat.messages}
          sending={chat.sending}
          onSend={chat.send}
        />
      </div>
    </Modal>
  );
}
