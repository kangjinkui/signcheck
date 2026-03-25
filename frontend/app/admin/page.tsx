'use client';
import { useState, useEffect, useCallback } from 'react';
import { getRules, getLogs, getStats, deleteRule, ingestDocument } from '@/lib/api';

type Tab = 'rules' | 'logs' | 'stats';

interface RuleRow {
  condition: {
    id: string; sign_type: string; floor_min: number | null; floor_max: number | null;
    zone: string | null; ad_type: string | null; priority: number;
  };
  effect: {
    id: string; decision: string; review_type: string | null;
    max_area: number | null; max_height: number | null;
    max_protrusion: number | null; max_width: number | null;
    display_period: string | null; warnings: string[];
  };
}

interface LogRow {
  id: string; decision: string; fee: number | null;
  input: Record<string, unknown>; created_at: string | null;
}

interface Stats {
  total: number;
  by_decision: Record<string, number>;
  by_sign_type: Record<string, number>;
}

const DECISION_CLASS: Record<string, string> = {
  permit: 'tag-permit', report: 'tag-report', prohibited: 'tag-prohibited',
};
const DECISION_KO: Record<string, string> = {
  permit: '허가', report: '신고', prohibited: '불가',
};

export default function AdminPage() {
  const [tab, setTab] = useState<Tab>('rules');
  const [rules, setRules] = useState<RuleRow[]>([]);
  const [logs, setLogs] = useState<LogRow[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (tab === 'rules') setRules(await getRules());
      else if (tab === 'logs') setLogs(await getLogs(100));
      else setStats(await getStats());
    } catch (e) {
      setError(e instanceof Error ? e.message : '데이터 로드 실패');
    } finally {
      setLoading(false);
    }
  }, [tab]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleIngest = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      await ingestDocument(file);
      alert(`"${file.name}" 임베딩이 완료되었습니다.`);
    } catch (err) {
      alert(err instanceof Error ? err.message : '임베딩 실패');
    }
    e.target.value = '';
  };

  const handleDelete = async (conditionId: string, signType: string) => {
    if (!confirm(`"${signType}" 규칙을 삭제하시겠습니까?`)) return;
    try {
      await deleteRule(conditionId);
      setRules(prev => prev.filter(r => r.condition.id !== conditionId));
    } catch (e) {
      alert(e instanceof Error ? e.message : '삭제 실패');
    }
  };

  return (
    <main style={{ padding: '24px 0 60px' }}>
      <div className="container">
        <div className="card">
          <p className="card-title">관리자 대시보드</p>

          <div className="section-tabs">
            {(['rules', 'logs', 'stats'] as Tab[]).map(t => (
              <button key={t} className={`tab-btn ${tab === t ? 'active' : ''}`}
                onClick={() => setTab(t)}>
                {t === 'rules' ? '규칙 관리' : t === 'logs' ? '판정 로그' : '통계'}
              </button>
            ))}
            <div style={{ marginLeft: 'auto', display: 'flex', gap: 8, alignItems: 'center' }}>
              <label className="btn btn-outline btn-sm" style={{ cursor: 'pointer' }}>
                📥 법령 임베딩
                <input type="file" accept=".pdf,.txt,.docx" style={{ display: 'none' }}
                  onChange={handleIngest} />
              </label>
              <button className="btn btn-outline btn-sm" onClick={loadData}>새로고침</button>
            </div>
          </div>

          {error && <div className="error-msg">❌ {error}</div>}
          {loading && <p className="loading">로딩 중...</p>}

          {!loading && tab === 'rules' && (
            <div style={{ overflowX: 'auto' }}>
              <table>
                <thead>
                  <tr>
                    <th>간판 유형</th>
                    <th>층수</th>
                    <th>용도지역</th>
                    <th>광고종류</th>
                    <th>우선순위</th>
                    <th>판정</th>
                    <th>심의</th>
                    <th>최대 규격</th>
                    <th>표시기간</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {rules.map((r) => {
                    const c = r.condition; const e = r.effect;
                    const floor = c.floor_min || c.floor_max
                      ? `${c.floor_min ?? ''}~${c.floor_max ?? ''}층`
                      : '-';
                    const spec = [
                      e.max_area && `${e.max_area}㎡`,
                      e.max_height && `H${e.max_height}m`,
                      e.max_protrusion && `돌${e.max_protrusion}m`,
                    ].filter(Boolean).join(' / ') || '-';
                    return (
                      <tr key={c.id}>
                        <td><strong>{c.sign_type}</strong></td>
                        <td>{floor}</td>
                        <td>{c.zone || '-'}</td>
                        <td>{c.ad_type === 'self' ? '자사' : c.ad_type === 'third_party' ? '타사' : '-'}</td>
                        <td style={{ textAlign: 'center' }}>{c.priority}</td>
                        <td>
                          <span className={`tag ${DECISION_CLASS[e.decision] ?? ''}`}>
                            {DECISION_KO[e.decision] ?? e.decision}
                          </span>
                        </td>
                        <td>{e.review_type || '-'}</td>
                        <td style={{ fontSize: 12 }}>{spec}</td>
                        <td>{e.display_period || '-'}</td>
                        <td>
                          <button className="btn btn-danger btn-sm"
                            onClick={() => handleDelete(c.id, c.sign_type)}>
                            삭제
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              {rules.length === 0 && !loading && <p className="loading">규칙 데이터가 없습니다.</p>}
            </div>
          )}

          {!loading && tab === 'logs' && (
            <div style={{ overflowX: 'auto' }}>
              <table>
                <thead>
                  <tr>
                    <th>일시</th>
                    <th>간판 유형</th>
                    <th>판정</th>
                    <th>수수료</th>
                    <th>층수/면적</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map(log => {
                    const inp = log.input || {};
                    return (
                      <tr key={log.id}>
                        <td style={{ fontSize: 12, color: '#888' }}>
                          {log.created_at ? new Date(log.created_at).toLocaleString('ko-KR') : '-'}
                        </td>
                        <td>{String(inp.sign_type || '-')}</td>
                        <td>
                          <span className={`tag ${DECISION_CLASS[log.decision] ?? ''}`}>
                            {DECISION_KO[log.decision] ?? log.decision}
                          </span>
                        </td>
                        <td>{log.fee ? `${log.fee.toLocaleString()}원` : '-'}</td>
                        <td>{String(inp.floor || '-')}층 / {String(inp.area || '-')}㎡</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              {logs.length === 0 && !loading && <p className="loading">판정 로그가 없습니다.</p>}
            </div>
          )}

          {!loading && tab === 'stats' && stats && (
            <>
              <div className="stat-grid">
                <div className="stat-box">
                  <h3>총 판정 수</h3>
                  <p>{stats.total}</p>
                </div>
                {Object.entries(stats.by_decision).map(([k, v]) => (
                  <div className="stat-box" key={k}>
                    <h3>{DECISION_KO[k] ?? k}</h3>
                    <p>{v}</p>
                  </div>
                ))}
              </div>
              <p className="card-title" style={{ marginTop: 8 }}>유형별 판정 수</p>
              <table>
                <thead><tr><th>광고물 유형</th><th>건수</th></tr></thead>
                <tbody>
                  {Object.entries(stats.by_sign_type)
                    .sort(([, a], [, b]) => b - a)
                    .map(([k, v]) => (
                      <tr key={k}><td>{k}</td><td>{v}</td></tr>
                    ))}
                </tbody>
              </table>
            </>
          )}
        </div>
      </div>
    </main>
  );
}
