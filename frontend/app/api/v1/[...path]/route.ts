import { NextRequest, NextResponse } from 'next/server';

const API_BASE = (process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || '').replace(/\/$/, '');

function buildTargetUrl(path: string[], request: NextRequest) {
  const target = new URL(`${API_BASE}/api/v1/${path.join('/')}`);
  request.nextUrl.searchParams.forEach((value, key) => {
    target.searchParams.append(key, value);
  });
  return target;
}

async function proxy(request: NextRequest, context: { params: { path: string[] } }) {
  if (!API_BASE) {
    return NextResponse.json(
      { detail: 'INTERNAL_API_URL is not configured' },
      { status: 500 },
    );
  }

  const target = buildTargetUrl(context.params.path, request);
  const requestHeaders = new Headers(request.headers);
  requestHeaders.delete('host');

  const upstream = await fetch(target, {
    method: request.method,
    headers: requestHeaders,
    body: request.method === 'GET' || request.method === 'HEAD' ? undefined : await request.text(),
    redirect: 'manual',
  });

  const responseHeaders = new Headers(upstream.headers);
  responseHeaders.delete('content-encoding');
  responseHeaders.delete('content-length');
  responseHeaders.delete('transfer-encoding');

  return new NextResponse(upstream.body, {
    status: upstream.status,
    headers: responseHeaders,
  });
}

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest, context: { params: { path: string[] } }) {
  return proxy(request, context);
}

export async function POST(request: NextRequest, context: { params: { path: string[] } }) {
  return proxy(request, context);
}

export async function PUT(request: NextRequest, context: { params: { path: string[] } }) {
  return proxy(request, context);
}

export async function PATCH(request: NextRequest, context: { params: { path: string[] } }) {
  return proxy(request, context);
}

export async function DELETE(request: NextRequest, context: { params: { path: string[] } }) {
  return proxy(request, context);
}

export async function OPTIONS(request: NextRequest, context: { params: { path: string[] } }) {
  return proxy(request, context);
}
