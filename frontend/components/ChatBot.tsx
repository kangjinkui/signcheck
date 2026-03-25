'use client';
import { useState, useRef, useEffect } from 'react';
import { chat } from '@/lib/api';

interface Message {
  role: 'ai' | 'user';
  text: string;
}

interface Props {
  caseId: string | null;
  open: boolean;
  onToggle: () => void;
}

export default function ChatBot({ caseId, open, onToggle }: Props) {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'ai', text: '판정 결과에 대해 궁금한 점이 있으면 질문해 주세요.' },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || !caseId) return;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text }]);
    setLoading(true);
    try {
      const res = await chat({ case_id: caseId, message: text });
      setMessages(prev => [...prev, { role: 'ai', text: res.answer }]);
    } catch {
      setMessages(prev => [...prev, { role: 'ai', text: '오류가 발생했습니다. 다시 시도해 주세요.' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  return (
    <div className="chat-panel">
      <button className="chat-toggle" onClick={onToggle}>
        <span>💬 추가 질문</span>
        <span>{open ? '▼' : '▲'}</span>
      </button>
      {open && (
        <div className="chat-body">
          <div className="chat-messages">
            {messages.map((m, i) => (
              <div key={i} className={`chat-bubble ${m.role}`}>{m.text}</div>
            ))}
            {loading && <div className="chat-bubble ai">답변 생성 중...</div>}
            <div ref={bottomRef} />
          </div>
          <div className="chat-input-row">
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder={caseId ? '질문을 입력하세요...' : '판정 후 질문 가능합니다'}
              disabled={!caseId || loading}
            />
            <button className="btn btn-primary btn-sm" onClick={sendMessage}
              disabled={!caseId || loading || !input.trim()}>
              전송
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
