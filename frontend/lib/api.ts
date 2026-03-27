const BASE = process.env.NEXT_PUBLIC_API_URL || '';

export interface JudgeCommonRequestFields {
  sign_type: string;
  floor: number;
  area: number;
  light_type: string;
  zone: string;
  ad_type: string;
  install_subtype?: string | null;
  form_type?: string | null;
  content_type?: string | null;
  display_orientation?: string | null;
  special_zone?: string | null;
  tehranro: boolean;
  vendor_count?: number | null;
  has_sidewalk?: boolean | null;
  shop_front_width?: number | null;
  sign_width?: number | null;
  sign_height?: number | null;
  sign_area?: number | null;
  is_corner_lot?: boolean | null;
  has_front_and_rear_roads?: boolean | null;
  building_floor_count?: number | null;
  install_at_top_floor?: boolean | null;
  building_width?: number | null;
  requested_faces?: number | null;
  horizontal_distance_to_other_sign?: number | null;
  has_performance_hall?: boolean | null;
  base_width?: number | null;
  base_depth?: number | null;
  distance_from_building?: number | null;
}

export interface JudgeProjectingSignRequestFields {
  business_category?: string | null;
  height?: number | null;
  width?: number | null;
  protrusion?: number | null;
  thickness?: number | null;
  bottom_clearance?: number | null;
  top_height_from_ground?: number | null;
  face_area?: number | null;
  building_height?: number | null;
  floor_height?: number | null;
  existing_sign_count_for_business?: number | null;
  existing_sign_types?: string[];
  exception_review_approved?: boolean | null;
}

export interface JudgeRequest extends JudgeCommonRequestFields, JudgeProjectingSignRequestFields {}

export interface JudgeMaxSpec {
  area?: string | null;
  height?: string | null;
  protrusion?: string | null;
  width?: string | null;
}

export interface JudgeFeeSummary {
  base: number;
  light_weight: number;
  total: number;
}

export interface JudgeResponse {
  case_id: string;
  decision: string;
  review_type: string | null;
  administrative_action: string | null;
  safety_check: boolean;
  max_spec: JudgeMaxSpec;
  fee: JudgeFeeSummary;
  display_period: string | null;
  required_docs: string[];
  optional_docs: string[];
  provisions: { law: string; article: string; content: string; similarity: number }[];
  warnings: string[];
  matched_rule_id: string | null;
  missing_fields: string[];
  fallback_reason: string;
}

export interface ChatRequest {
  case_id: string;
  message: string;
  context?: Record<string, unknown>;
}

export interface ChatResponse {
  answer: string;
  sources?: { law: string; page?: number }[];
}

export async function judge(req: JudgeRequest): Promise<JudgeResponse> {
  const res = await fetch(`${BASE}/api/v1/judge`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const raw = await res.text();
    let message: string | null = null;
    try {
      const parsed = JSON.parse(raw) as { detail?: string | { msg?: string }[] };
      const detail = parsed.detail;
      if (typeof detail === 'string') {
        message = detail;
      }
      if (Array.isArray(detail) && detail.length > 0) {
        message = detail.map(item => item.msg).filter(Boolean).join('\n');
      }
    } catch {}
    if (message) {
      throw new Error(message);
    }
    throw new Error(raw);
  }
  return res.json();
}

export async function chat(req: ChatRequest): Promise<ChatResponse> {
  const res = await fetch(`${BASE}/api/v1/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// Admin API
export async function getRules() {
  const res = await fetch(`${BASE}/api/v1/admin/rules`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function updateRule(effectId: string, data: Record<string, unknown>) {
  const res = await fetch(`${BASE}/api/v1/admin/rules/${effectId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function deleteRule(conditionId: string) {
  const res = await fetch(`${BASE}/api/v1/admin/rules/${conditionId}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getLogs(limit = 50) {
  const res = await fetch(`${BASE}/api/v1/admin/logs?limit=${limit}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getStats() {
  const res = await fetch(`${BASE}/api/v1/admin/stats`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function ingestDocument(file: File) {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${BASE}/api/v1/admin/ingest`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
