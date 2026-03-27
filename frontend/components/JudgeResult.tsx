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

const FIELD_LABEL: Record<string, string> = {
  install_subtype: '벽면 하위 유형',
  form_type: '형태',
  content_type: '표시 내용',
  display_orientation: '표시 방향',
  business_category: '업종',
  height: '세로 길이',
  width: '가로 길이',
  protrusion: '돌출폭',
  thickness: '두께',
  bottom_clearance: '지면 이격',
  top_height_from_ground: '상단 높이',
  face_area: '1면 면적',
  building_height: '건물 높이',
  floor_height: '층고',
  existing_sign_count_for_business: '기설치 간판 수',
  has_sidewalk: '보도 접면 여부',
  exception_review_approved: '심의 특례 승인 여부',
  shop_front_width: '업소 가로폭',
  sign_width: '간판 가로',
  sign_height: '간판 세로/높이',
  sign_area: '간판 면적',
  is_corner_lot: '곡각지점 여부',
  has_front_and_rear_roads: '전후면 도로 접면 여부',
  building_floor_count: '건물 층수',
  install_at_top_floor: '최상단 설치 여부',
  building_width: '건물 가로폭',
  requested_faces: '신청 면 수',
  horizontal_distance_to_other_sign: '최근접 옥상간판 수평거리',
  vendor_count: '연립 업체 수',
  has_performance_hall: '공연장 여부',
  base_width: '바닥면 가로',
  base_depth: '바닥면 세로',
  distance_from_building: '건물면으로부터 거리',
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
              {result.missing_fields.map((field, i) => (
                <li key={i}>{FIELD_LABEL[field] ?? field}</li>
              ))}
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
