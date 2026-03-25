'use client';
import type { JudgeResponse } from '@/lib/api';

const DECISION_LABEL: Record<string, string> = {
  permit: '허가',
  report: '신고',
  prohibited: '설치불가',
};

const DECISION_CLASS: Record<string, string> = {
  permit: 'badge-permit',
  report: 'badge-report',
  prohibited: 'badge-prohibited',
};

const DECISION_ICON: Record<string, string> = {
  permit: '✅',
  report: '📋',
  prohibited: '🚫',
};

const ACTION_LABEL: Record<string, string> = {
  none: '행정절차 없음',
  permit: '허가',
  report: '신고',
};

const FALLBACK_LABEL: Record<string, string> = {
  none: '정상 판정',
  missing_input: '입력 부족',
  missing_rule: '규칙 미정의',
};

interface Props {
  result: JudgeResponse;
  onChatOpen: () => void;
}

export default function JudgeResult({ result, onChatOpen }: Props) {
  const specs = Object.entries(result.max_spec).filter(([, v]) => v);
  const feeTotal = result.fee.total?.toLocaleString();
  const feeBase = result.fee.base?.toLocaleString();

  return (
    <div className="card">
      <div className="result-header">
        <span className={`decision-badge ${DECISION_CLASS[result.decision] ?? 'badge-report'}`}>
          {DECISION_ICON[result.decision]} {DECISION_LABEL[result.decision] ?? result.decision}
        </span>
        {result.review_type && (
          <span className="review-tag">{result.review_type}</span>
        )}
        {result.administrative_action && (
          <span className="review-tag">{ACTION_LABEL[result.administrative_action] ?? result.administrative_action}</span>
        )}
        {result.display_period && (
          <span style={{ fontSize: 13, color: '#666' }}>표시기간: {result.display_period}</span>
        )}
      </div>

      {result.warnings.length > 0 && (
        <div className="warning-box">
          {result.warnings.map((w, i) => <p key={i}>⚠️ {w}</p>)}
        </div>
      )}

      <div className="result-grid" style={{ marginTop: 16 }}>
        {specs.length > 0 && (
          <div className="result-item">
            <h4>📏 최대 규격</h4>
            <ul>
              {specs.map(([k, v]) => (
                <li key={k}>
                  {k === 'area' ? '면적' : k === 'height' ? '높이' : k === 'protrusion' ? '돌출폭' : '폭'}: {v}
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="result-item">
          <h4>🧭 판정 메타</h4>
          <ul>
            <li>행정절차: {result.administrative_action ? (ACTION_LABEL[result.administrative_action] ?? result.administrative_action) : '해당없음'}</li>
            <li>안전점검: {result.safety_check ? '대상' : '비대상'}</li>
            <li>Fallback: {FALLBACK_LABEL[result.fallback_reason] ?? result.fallback_reason}</li>
            {result.matched_rule_id && <li>매칭 규칙 ID: {result.matched_rule_id}</li>}
          </ul>
        </div>

        {result.fee.total > 0 && (
          <div className="result-item">
            <h4>💰 수수료</h4>
            <p>{feeTotal}원</p>
            <ul style={{ marginTop: 6 }}>
              <li>기준 수수료: {feeBase}원</li>
              <li>조명 가중치: ×{result.fee.light_weight}</li>
            </ul>
          </div>
        )}

        {result.missing_fields.length > 0 && (
          <div className="result-item">
            <h4>🧩 누락 입력</h4>
            <ul>
              {result.missing_fields.map((field, i) => <li key={i}>{field}</li>)}
            </ul>
          </div>
        )}

        {result.required_docs.length > 0 && (
          <div className="result-item">
            <h4>📄 필수 서류</h4>
            <ul>
              {result.required_docs.map((d, i) => <li key={i}>{d}</li>)}
            </ul>
          </div>
        )}

        {result.optional_docs.length > 0 && (
          <div className="result-item">
            <h4>📎 선택 서류</h4>
            <ul>
              {result.optional_docs.map((d, i) => <li key={i}>{d}</li>)}
            </ul>
          </div>
        )}

        {result.provisions.length > 0 && (
          <div className="result-item full">
            <h4>📖 근거 조문</h4>
            <div className="provision-list">
              {result.provisions.map((p, i) => (
                <div className="provision-item" key={i}>
                  <strong>{p.law} {p.article}</strong>
                  {p.content && <span>{p.content.slice(0, 120)}{p.content.length > 120 ? '…' : ''}</span>}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div style={{ textAlign: 'right', marginTop: 16 }}>
        <button className="btn btn-outline btn-sm" onClick={onChatOpen}>
          💬 추가 질문하기
        </button>
      </div>
    </div>
  );
}
