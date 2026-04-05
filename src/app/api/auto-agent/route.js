import { NextResponse } from 'next/server';

import { proxyToBackend } from '@/lib/backendProxy';

export const dynamic = 'force-dynamic';

export async function POST(request) {
  try {
    const sessionId = request.headers.get('x-session-id');
    const body = await request.json().catch(() => ({}));

    const payload = await proxyToBackend({
      path: '/agent/auto',
      method: 'POST',
      body,
      sessionId,
    });

    return NextResponse.json(payload);
  } catch (error) {
    return NextResponse.json(
      { detail: error.message ?? 'Failed to run the auto agent.' },
      { status: error.status ?? 500 },
    );
  }
}

