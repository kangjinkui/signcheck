'use client';
import { useState } from 'react';
import type { JudgeRequest } from '@/lib/api';

const SIGN_TYPES = [
  '돌출간판', '벽면이용간판',
  '옥상간판', '지주이용간판', '입간판', '공연간판',
  '현수막', '애드벌룬', '애드벌룬(지면)', '창문이용광고물',
];

const WALL_SIGN_SUBTYPES = [
  ['wall_sign_general_under_5f', '5층 이하 일반 벽면이용간판'],
  ['wall_sign_top_building', '건물 상단간판'],
] as const;

const ZONES = [
  '일반상업지역', '중심상업지역', '근린상업지역',
  '준공업지역', '일반주거지역', '준주거지역',
];

function roundArea(value: number): number {
  return Math.round(value * 100) / 100;
}

function calculateArea(width?: number | null, height?: number | null): number | null {
  if (typeof width !== 'number' || typeof height !== 'number' || width <= 0 || height <= 0) {
    return null;
  }
  return roundArea(width * height);
}

function syncAreaFromSignSize(prev: JudgeRequest, next: Partial<JudgeRequest>): JudgeRequest {
  const merged = { ...prev, ...next };
  const calculatedArea = calculateArea(merged.sign_width, merged.sign_height);

  if (calculatedArea === null) {
    return merged;
  }

  if (merged.install_subtype === 'wall_sign_general_under_5f') {
    return {
      ...merged,
      sign_area: calculatedArea,
      area: calculatedArea,
    };
  }

  return {
    ...merged,
    area: calculatedArea,
  };
}

function syncAreaFromProjectingSize(prev: JudgeRequest, next: Partial<JudgeRequest>): JudgeRequest {
  const merged = { ...prev, ...next };
  const calculatedArea = calculateArea(merged.width, merged.height);

  if (calculatedArea === null) {
    return merged;
  }

  return {
    ...merged,
    area: calculatedArea,
  };
}

const defaultForm: JudgeRequest = {
  sign_type: '돌출간판',
  floor: 1,
  area: 5,
  light_type: 'none',
  zone: '일반상업지역',
  ad_type: 'self',
  install_subtype: null,
  form_type: null,
  content_type: null,
  display_orientation: null,
  special_zone: null,
  tehranro: false,
  vendor_count: null,
  has_sidewalk: true,
  shop_front_width: null,
  sign_width: null,
  sign_height: null,
  sign_area: null,
  is_corner_lot: false,
  has_front_and_rear_roads: false,
  building_floor_count: null,
  install_at_top_floor: null,
  building_width: null,
  requested_faces: null,
  horizontal_distance_to_other_sign: null,
  has_performance_hall: null,
  base_width: null,
  base_depth: null,
  distance_from_building: null,
  business_category: '',
  height: 3,
  width: 1,
  protrusion: 1,
  thickness: 0.3,
  bottom_clearance: 3,
  top_height_from_ground: 5,
  face_area: 1,
  building_height: 20,
  floor_height: 3.5,
  existing_sign_count_for_business: 0,
  existing_sign_types: [],
  exception_review_approved: false,
};

function applySignTypeDefaults(prev: JudgeRequest, nextSignType: string): JudgeRequest {
  if (nextSignType === '벽면이용간판') {
    return {
      ...applyWallSubtypeDefaults(prev, prev.install_subtype ?? 'wall_sign_general_under_5f'),
      sign_type: nextSignType,
    };
  }

  const base: JudgeRequest = {
    ...prev,
    sign_type: nextSignType,
    install_subtype: null,
    form_type: null,
    content_type: null,
    display_orientation: null,
    vendor_count: null,
    shop_front_width: null,
    sign_width: null,
    sign_height: null,
    sign_area: null,
    building_floor_count: null,
    install_at_top_floor: null,
    building_width: null,
    requested_faces: null,
    horizontal_distance_to_other_sign: null,
    has_performance_hall: null,
    base_width: null,
    base_depth: null,
    distance_from_building: null,
  };

  switch (nextSignType) {
    case '돌출간판':
      return {
        ...base,
        area: prev.area || 3,
        business_category: prev.business_category || '일반음식점',
        height: prev.height ?? 3,
        width: prev.width ?? 1,
        protrusion: prev.protrusion ?? 1,
        thickness: prev.thickness ?? 0.3,
        bottom_clearance: prev.bottom_clearance ?? 3,
        top_height_from_ground: prev.top_height_from_ground ?? 5,
        face_area: prev.face_area ?? 1,
        building_height: prev.building_height ?? 20,
        floor_height: prev.floor_height ?? 3.5,
        existing_sign_count_for_business: prev.existing_sign_count_for_business ?? 0,
        has_sidewalk: prev.has_sidewalk ?? true,
        exception_review_approved: prev.exception_review_approved ?? false,
      };
    case '옥상간판':
      return {
        ...base,
        area: prev.area || 8,
        sign_height: prev.sign_height ?? 3,
        building_height: prev.building_height ?? 20,
        building_floor_count: prev.building_floor_count ?? 5,
        horizontal_distance_to_other_sign: prev.horizontal_distance_to_other_sign ?? 10,
      };
    case '지주이용간판':
      return {
        ...base,
        area: prev.area || 8,
        vendor_count: prev.vendor_count ?? 1,
        sign_height: prev.sign_height ?? 4,
      };
    case '입간판':
      return {
        ...base,
        sign_width: prev.sign_width ?? 0.6,
        sign_height: prev.sign_height ?? 1.2,
        area: calculateArea(prev.sign_width ?? 0.6, prev.sign_height ?? 1.2) ?? 0.72,
        has_sidewalk: prev.has_sidewalk ?? true,
        base_width: prev.base_width ?? 0.5,
        base_depth: prev.base_depth ?? 0.5,
        distance_from_building: prev.distance_from_building ?? 0,
      };
    case '공연간판':
      return {
        ...base,
        area: prev.area || 3,
        vendor_count: prev.vendor_count ?? 1,
        protrusion: prev.protrusion ?? 0.8,
        sign_width: prev.sign_width ?? 3,
        building_width: prev.building_width ?? 10,
        has_performance_hall: prev.has_performance_hall ?? false,
      };
    case '현수막':
      return {
        ...base,
        sign_width: prev.sign_width ?? 5,
        sign_height: prev.sign_height ?? 1,
        area: calculateArea(prev.sign_width ?? 5, prev.sign_height ?? 1) ?? 5,
      };
    case '애드벌룬':
      return {
        ...base,
        area: prev.area || 10,
        sign_height: prev.sign_height ?? 10,
        building_height: prev.building_height ?? 20,
      };
    case '애드벌룬(지면)':
      return {
        ...base,
        area: prev.area || 10,
        sign_height: prev.sign_height ?? 10,
      };
    case '창문이용광고물':
      return {
        ...base,
        sign_width: prev.sign_width ?? 2,
        sign_height: prev.sign_height ?? 1,
        area: calculateArea(prev.sign_width ?? 2, prev.sign_height ?? 1) ?? 2,
      };
    default:
      return base;
  }
}

function applyWallSubtypeDefaults(prev: JudgeRequest, nextSubtype: string): JudgeRequest {
  if (nextSubtype === 'wall_sign_general_under_5f') {
    const signWidth = prev.sign_width ?? 8;
    const signHeight = prev.sign_height ?? 0.45;
    const signArea = calculateArea(signWidth, signHeight) ?? prev.sign_area ?? prev.area ?? 4.5;
    return {
      ...prev,
      install_subtype: nextSubtype,
      form_type: prev.form_type ?? 'solid',
      content_type: null,
      display_orientation: null,
      shop_front_width: prev.shop_front_width ?? 10,
      sign_width: signWidth,
      sign_height: signHeight,
      sign_area: signArea,
      area: signArea,
      is_corner_lot: prev.is_corner_lot ?? false,
      has_front_and_rear_roads: prev.has_front_and_rear_roads ?? false,
      building_floor_count: null,
      install_at_top_floor: null,
      building_width: null,
      requested_faces: null,
    };
  }

  const signWidth = prev.sign_width ?? 8;
  const signHeight = prev.sign_height ?? 1;
  return {
    ...prev,
    install_subtype: nextSubtype,
    form_type: 'solid',
    content_type: prev.content_type ?? 'building_name',
    display_orientation: prev.display_orientation ?? 'horizontal',
    shop_front_width: null,
    sign_width: signWidth,
    sign_height: signHeight,
    sign_area: null,
    area: signWidth * signHeight,
    is_corner_lot: false,
    has_front_and_rear_roads: false,
    building_floor_count: prev.building_floor_count ?? 5,
    install_at_top_floor: prev.install_at_top_floor ?? true,
    building_width: prev.building_width ?? 20,
    requested_faces: prev.requested_faces ?? 1,
  };
}

interface Props {
  onSubmit: (req: JudgeRequest) => void;
  loading: boolean;
}

export default function JudgeForm({ onSubmit, loading }: Props) {
  const [form, setForm] = useState<JudgeRequest>(defaultForm);
  const isProjectingSign = form.sign_type === '돌출간판';
  const isWallSign = form.sign_type === '벽면이용간판';
  const isWallGeneral =
    form.sign_type === '벽면이용간판' && form.install_subtype === 'wall_sign_general_under_5f';
  const isWallTop =
    form.sign_type === '벽면이용간판' && form.install_subtype === 'wall_sign_top_building';
  const usesGenericHeightSpec = [
    '옥상간판', '지주이용간판', '입간판', '현수막', '애드벌룬', '애드벌룬(지면)', '창문이용광고물',
  ].includes(form.sign_type);
  const usesGenericWidthSpec = ['입간판', '현수막', '창문이용광고물'].includes(form.sign_type);
  const usesGenericProtrusionSpec = form.sign_type === '공연간판';
  const needsBalloonBuildingHeight = form.sign_type === '애드벌룬';
  const isRooftopSign = form.sign_type === '옥상간판';
  const isStandingSign = form.sign_type === '입간판';
  const isPerformanceSign = form.sign_type === '공연간판';
  const hasAutoArea =
    isProjectingSign ||
    isWallSign ||
    (usesGenericHeightSpec && usesGenericWidthSpec);

  const genericHeightLabel = {
    '옥상간판': '간판 높이 (m)',
    '지주이용간판': '간판 높이 (m)',
    '입간판': '간판 윗부분 높이 (m)',
    '현수막': '세로 길이 (m)',
    '애드벌룬': '애드벌룬 높이 (m)',
    '애드벌룬(지면)': '애드벌룬 높이 (m)',
    '창문이용광고물': '세로 길이 (m)',
  }[form.sign_type];

  const genericWidthLabel = {
    '입간판': '간판 가로 (m)',
    '현수막': '가로 길이 (m)',
    '창문이용광고물': '가로 길이 (m)',
  }[form.sign_type];

  const set = (field: keyof JudgeRequest, value: unknown) =>
    setForm(prev => ({ ...prev, [field]: value }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(form);
  };

  return (
    <form onSubmit={handleSubmit} className="card">
      <p className="card-title">광고물 정보 입력</p>
      <div className="form-grid">
        <div className="form-group">
          <label>광고물 유형</label>
          <select
            value={form.sign_type}
            onChange={e => {
              const nextSignType = e.target.value;
              setForm(prev => applySignTypeDefaults(prev, nextSignType));
            }}
          >
            {SIGN_TYPES.map(t => <option key={t}>{t}</option>)}
          </select>
        </div>

        {isWallSign && (
          <div className="form-group">
            <label>벽면 하위 유형</label>
            <select
              value={form.install_subtype ?? 'wall_sign_general_under_5f'}
              onChange={e => {
                const nextSubtype = e.target.value;
                setForm(prev => applyWallSubtypeDefaults(prev, nextSubtype));
              }}
            >
              {WALL_SIGN_SUBTYPES.map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </div>
        )}

        <div className="form-group">
          <label>용도지역</label>
          <select value={form.zone} onChange={e => set('zone', e.target.value)}>
            {ZONES.map(z => <option key={z}>{z}</option>)}
          </select>
        </div>

        <div className="form-group">
          <label>설치 층수</label>
          <input type="number" min={1} max={100} value={form.floor}
            onChange={e => { const v = parseInt(e.target.value); if (!isNaN(v)) set('floor', v); }}
            onBlur={e => { if (!e.target.value || parseInt(e.target.value) < 1) set('floor', 1); }} />
        </div>

        <div className="form-group">
          <label>{isWallGeneral ? '간판 면적 (㎡)' : '면적 (㎡)'}</label>
          <input
            type="number"
            min={0.1}
            step={0.1}
            value={isWallGeneral ? (form.sign_area ?? '') : form.area}
            readOnly={hasAutoArea}
            disabled={hasAutoArea}
            onChange={e => {
              const nextValue = parseFloat(e.target.value) || 0.1;
              if (isWallGeneral) {
                setForm(prev => ({ ...prev, sign_area: nextValue, area: nextValue }));
                return;
              }
              set('area', nextValue);
            }}
          />
        </div>

        {isWallGeneral && (
          <>
            <div className="form-group">
              <label>형태</label>
              <select
                value={form.form_type ?? 'solid'}
                onChange={e => set('form_type', e.target.value)}
              >
                <option value="solid">입체형</option>
                <option value="plate">판류형</option>
              </select>
            </div>

            <div className="form-group">
              <label>업소 가로폭 (m)</label>
              <input
                type="number"
                min={0.1}
                step={0.1}
                value={form.shop_front_width ?? ''}
                onChange={e => set('shop_front_width', parseFloat(e.target.value) || null)}
              />
            </div>

            <div className="form-group">
              <label>간판 가로 (m)</label>
              <input
                type="number"
                min={0.1}
                step={0.1}
                value={form.sign_width ?? ''}
                onChange={e =>
                  setForm(prev => syncAreaFromSignSize(prev, { sign_width: parseFloat(e.target.value) || null }))
                }
              />
            </div>

            <div className="form-group">
              <label>간판 세로 (m)</label>
              <input
                type="number"
                min={0.1}
                step={0.01}
                value={form.sign_height ?? ''}
                onChange={e =>
                  setForm(prev => syncAreaFromSignSize(prev, { sign_height: parseFloat(e.target.value) || null }))
                }
              />
            </div>

            <div className="form-group full">
              <label>수량 특례</label>
              <div className="checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={form.is_corner_lot === true}
                    onChange={e => set('is_corner_lot', e.target.checked)}
                  />
                  곡각지점
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={form.has_front_and_rear_roads === true}
                    onChange={e => set('has_front_and_rear_roads', e.target.checked)}
                  />
                  전후면 도로 접면
                </label>
              </div>
            </div>
          </>
        )}

        {isWallTop && (
          <>
            <div className="form-group">
              <label>형태</label>
              <select value="solid" disabled>
                <option value="solid">입체형만 허용</option>
              </select>
            </div>

            <div className="form-group">
              <label>표시 내용</label>
              <select
                value={form.content_type ?? 'building_name'}
                onChange={e => set('content_type', e.target.value)}
              >
                <option value="building_name">건물명</option>
                <option value="business_name">상호</option>
                <option value="symbol">상징 도형</option>
              </select>
            </div>

            <div className="form-group">
              <label>표시 방향</label>
              <select
                value={form.display_orientation ?? 'horizontal'}
                onChange={e => set('display_orientation', e.target.value)}
              >
                <option value="horizontal">가로형</option>
                <option value="vertical">세로형</option>
              </select>
            </div>

            <div className="form-group">
              <label>건물 층수</label>
              <input
                type="number"
                min={4}
                value={form.building_floor_count ?? ''}
                onChange={e => set('building_floor_count', parseInt(e.target.value) || null)}
              />
            </div>

            <div className="form-group">
              <label>건물 가로폭 (m)</label>
              <input
                type="number"
                min={0.1}
                step={0.1}
                value={form.building_width ?? ''}
                onChange={e => set('building_width', parseFloat(e.target.value) || null)}
              />
            </div>

            <div className="form-group">
              <label>건물 높이 (m)</label>
              <input
                type="number"
                min={0.1}
                step={0.1}
                value={form.building_height ?? ''}
                onChange={e => set('building_height', parseFloat(e.target.value) || null)}
              />
            </div>

            <div className="form-group">
              <label>신청 면 수</label>
              <input
                type="number"
                min={1}
                max={3}
                value={form.requested_faces ?? ''}
                onChange={e => set('requested_faces', parseInt(e.target.value) || null)}
              />
            </div>

            <div className="form-group">
              <label>간판 가로 (m)</label>
              <input
                type="number"
                min={0.1}
                step={0.1}
                value={form.sign_width ?? ''}
                onChange={e =>
                  setForm(prev => syncAreaFromSignSize(prev, { sign_width: parseFloat(e.target.value) || null }))
                }
              />
            </div>

            <div className="form-group">
              <label>간판 세로 (m)</label>
              <input
                type="number"
                min={0.1}
                step={0.1}
                value={form.sign_height ?? ''}
                onChange={e =>
                  setForm(prev => syncAreaFromSignSize(prev, { sign_height: parseFloat(e.target.value) || null }))
                }
              />
            </div>

            <div className="form-group full">
              <label>설치 위치</label>
              <div className="checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={form.install_at_top_floor === true}
                    onChange={e => set('install_at_top_floor', e.target.checked)}
                  />
                  최상단 설치
                </label>
              </div>
            </div>
          </>
        )}

        <div className="form-group full">
          <label>조명 종류</label>
          <div className="radio-group">
            {[['none', '없음'], ['internal', '내부조명'], ['neon_digital', '디지털/네온']].map(([v, l]) => (
              <label key={v}>
                <input type="radio" name="light_type" value={v}
                  checked={form.light_type === v} onChange={() => set('light_type', v)} />
                {l}
              </label>
            ))}
          </div>
        </div>

        <div className="form-group full">
          <label>광고 종류</label>
          <div className="radio-group">
            <label>
              <input type="radio" name="ad_type" value="self"
                checked={form.ad_type === 'self'} onChange={() => set('ad_type', 'self')} />
              자사광고
            </label>
            <label>
              <input type="radio" name="ad_type" value="third_party"
                checked={form.ad_type === 'third_party'} onChange={() => set('ad_type', 'third_party')} />
              타사광고
            </label>
          </div>
        </div>

        <div className="form-group full">
          <label>추가 조건</label>
          <div className="checkbox-group">
            <label>
              <input type="checkbox" checked={form.tehranro}
                onChange={e => {
                  const checked = e.target.checked;
                  setForm(prev => ({
                    ...prev,
                    tehranro: checked,
                    special_zone: checked ? 'tehranro' : null,
                  }));
                }} />
              테헤란로 접면
            </label>
            <label>
              <input type="checkbox"
                checked={form.has_sidewalk === true}
                onChange={e => set('has_sidewalk', e.target.checked)} />
              보도 접면
            </label>
          </div>
        </div>

        {isProjectingSign && (
          <>
            <div className="form-group">
              <label>세로 길이 (m)</label>
              <input
                type="number"
                min={0.1}
                step={0.1}
                value={form.height ?? ''}
                onChange={e =>
                  setForm(prev => syncAreaFromProjectingSize(prev, { height: parseFloat(e.target.value) || null }))
                }
              />
            </div>

            <div className="form-group">
              <label>가로 길이 (m)</label>
              <input
                type="number"
                min={0.1}
                step={0.1}
                value={form.width ?? ''}
                onChange={e =>
                  setForm(prev => syncAreaFromProjectingSize(prev, { width: parseFloat(e.target.value) || null }))
                }
              />
            </div>

            <div className="form-group">
              <label>돌출폭 (m)</label>
              <input
                type="number"
                min={0.1}
                step={0.1}
                value={form.protrusion ?? ''}
                onChange={e => set('protrusion', parseFloat(e.target.value) || null)}
              />
            </div>

            <div className="form-group">
              <label>두께 (m)</label>
              <input
                type="number"
                min={0.01}
                step={0.01}
                value={form.thickness ?? ''}
                onChange={e => set('thickness', parseFloat(e.target.value) || null)}
              />
            </div>

            <div className="form-group">
              <label>지면 이격 (m)</label>
              <input
                type="number"
                min={0.1}
                step={0.1}
                value={form.bottom_clearance ?? ''}
                onChange={e => set('bottom_clearance', parseFloat(e.target.value) || null)}
              />
            </div>

            <div className="form-group">
              <label>상단 높이 (지면 기준 m)</label>
              <input
                type="number"
                min={0.1}
                step={0.1}
                value={form.top_height_from_ground ?? ''}
                onChange={e => set('top_height_from_ground', parseFloat(e.target.value) || null)}
              />
            </div>

            <div className="form-group">
              <label>1면 면적 (㎡)</label>
              <input
                type="number"
                min={0.1}
                step={0.1}
                value={form.face_area ?? ''}
                onChange={e => set('face_area', parseFloat(e.target.value) || null)}
              />
            </div>

            <div className="form-group">
              <label>건물 높이 (m)</label>
              <input
                type="number"
                min={0.1}
                step={0.1}
                value={form.building_height ?? ''}
                onChange={e => set('building_height', parseFloat(e.target.value) || null)}
              />
            </div>

            <div className="form-group">
              <label>층고 (m)</label>
              <input
                type="number"
                min={0.1}
                step={0.1}
                value={form.floor_height ?? ''}
                onChange={e => set('floor_height', parseFloat(e.target.value) || null)}
              />
            </div>

            <div className="form-group">
              <label>기설치 간판 수</label>
              <input
                type="number"
                min={0}
                value={form.existing_sign_count_for_business ?? 0}
                onChange={e => set('existing_sign_count_for_business', parseInt(e.target.value) || 0)}
              />
            </div>

            <div className="form-group full">
              <label>기설치 간판 종류 (쉼표 구분)</label>
              <input
                type="text"
                value={(form.existing_sign_types ?? []).join(', ')}
                onChange={e =>
                  set(
                    'existing_sign_types',
                    e.target.value
                      .split(',')
                      .map(value => value.trim())
                      .filter(Boolean),
                  )
                }
                placeholder="예: 벽면이용간판, 돌출간판"
              />
            </div>

            <div className="form-group full">
              <label>심의 특례 승인</label>
              <div className="radio-group">
                <label>
                  <input
                    type="radio"
                    name="exception_review_approved"
                    checked={form.exception_review_approved === true}
                    onChange={() => set('exception_review_approved', true)}
                  />
                  승인
                </label>
                <label>
                  <input
                    type="radio"
                    name="exception_review_approved"
                    checked={form.exception_review_approved === false}
                    onChange={() => set('exception_review_approved', false)}
                  />
                  미승인
                </label>
              </div>
            </div>
          </>
        )}

        {['지주이용간판', '공연간판'].includes(form.sign_type) && (
          <div className="form-group">
            <label>연립 업체 수</label>
            <input type="number" min={1} value={form.vendor_count ?? ''}
              onChange={e => set('vendor_count', parseInt(e.target.value) || null)} />
          </div>
        )}

        {isRooftopSign && (
          <>
            <div className="form-group">
              <label>건물 층수</label>
              <input
                type="number"
                min={1}
                value={form.building_floor_count ?? ''}
                onChange={e => set('building_floor_count', parseInt(e.target.value) || null)}
              />
            </div>
            <div className="form-group">
              <label>건물 높이 (m)</label>
              <input
                type="number"
                min={0.1}
                step={0.1}
                value={form.building_height ?? ''}
                onChange={e => set('building_height', parseFloat(e.target.value) || null)}
              />
            </div>
            <div className="form-group">
              <label>최근접 옥상간판 수평거리 (m)</label>
              <input
                type="number"
                min={0}
                step={0.1}
                value={form.horizontal_distance_to_other_sign ?? ''}
                onChange={e => set('horizontal_distance_to_other_sign', parseFloat(e.target.value) || null)}
              />
            </div>
          </>
        )}

        {isStandingSign && (
          <>
            <div className="form-group">
              <label>바닥면 가로 (m)</label>
              <input
                type="number"
                min={0.01}
                step={0.01}
                value={form.base_width ?? ''}
                onChange={e => set('base_width', parseFloat(e.target.value) || null)}
              />
            </div>
            <div className="form-group">
              <label>바닥면 세로 (m)</label>
              <input
                type="number"
                min={0.01}
                step={0.01}
                value={form.base_depth ?? ''}
                onChange={e => set('base_depth', parseFloat(e.target.value) || null)}
              />
            </div>
            <div className="form-group">
              <label>건물면으로부터 거리 (m)</label>
              <input
                type="number"
                min={0}
                step={0.1}
                value={form.distance_from_building ?? ''}
                onChange={e => set('distance_from_building', parseFloat(e.target.value) || null)}
              />
            </div>
          </>
        )}

        {isPerformanceSign && (
          <>
            <div className="form-group">
              <label>벽면 가로폭 (m)</label>
              <input
                type="number"
                min={0.1}
                step={0.1}
                value={form.building_width ?? ''}
                onChange={e => set('building_width', parseFloat(e.target.value) || null)}
              />
            </div>
            <div className="form-group full">
              <label>공연장 여부</label>
              <div className="radio-group">
                <label>
                  <input
                    type="radio"
                    name="has_performance_hall"
                    checked={form.has_performance_hall === true}
                    onChange={() => set('has_performance_hall', true)}
                  />
                  공연장 있음
                </label>
                <label>
                  <input
                    type="radio"
                    name="has_performance_hall"
                    checked={form.has_performance_hall === false}
                    onChange={() => set('has_performance_hall', false)}
                  />
                  공연장 없음
                </label>
              </div>
            </div>
          </>
        )}

        {usesGenericHeightSpec && (
          <div className="form-group">
            <label>{genericHeightLabel}</label>
            <input
              type="number"
              min={0.1}
              step={0.1}
              value={form.sign_height ?? ''}
              onChange={e =>
                setForm(prev => syncAreaFromSignSize(prev, { sign_height: parseFloat(e.target.value) || null }))
              }
            />
          </div>
        )}

        {usesGenericWidthSpec && (
          <div className="form-group">
            <label>{genericWidthLabel}</label>
            <input
              type="number"
              min={0.1}
              step={0.1}
              value={form.sign_width ?? ''}
              onChange={e =>
                setForm(prev => syncAreaFromSignSize(prev, { sign_width: parseFloat(e.target.value) || null }))
              }
            />
          </div>
        )}

        {usesGenericProtrusionSpec && (
          <div className="form-group">
            <label>돌출폭 (m)</label>
            <input
              type="number"
              min={0.01}
              step={0.01}
              value={form.protrusion ?? ''}
              onChange={e => set('protrusion', parseFloat(e.target.value) || null)}
            />
          </div>
        )}

        {needsBalloonBuildingHeight && (
          <div className="form-group">
            <label>건물 높이 (m)</label>
            <input
              type="number"
              min={0.1}
              step={0.1}
              value={form.building_height ?? ''}
              onChange={e => set('building_height', parseFloat(e.target.value) || null)}
            />
          </div>
        )}
      </div>

      <div className="submit-row">
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? '판정 중...' : '판정하기'}
        </button>
      </div>
    </form>
  );
}
