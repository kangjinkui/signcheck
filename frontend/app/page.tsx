'use client';
import { useState } from 'react';
import JudgeForm from '@/components/JudgeForm';
import JudgeResult from '@/components/JudgeResult';
import ChatBot from '@/components/ChatBot';
import { judge, type JudgeRequest, type JudgeResponse } from '@/lib/api';

export default function HomePage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<JudgeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [chatOpen, setChatOpen] = useState(false);

  const handleSubmit = async (req: JudgeRequest) => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await judge(req);
      setResult(res);
      setChatOpen(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : '판정 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="main-content">
      <div className="container">
        <JudgeForm onSubmit={handleSubmit} loading={loading} />
        {error && <div className="error-msg">❌ {error}</div>}
        {result && (
          <JudgeResult
            result={result}
            onChatOpen={() => setChatOpen(true)}
          />
        )}
      </div>
      <ChatBot
        caseId={result?.case_id ?? null}
        open={chatOpen}
        onToggle={() => setChatOpen(o => !o)}
      />
    </main>
  );
}
