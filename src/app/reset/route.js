import { NextResponse } from 'next/server';

import { proxyToBackend } from '@/lib/backendProxy';

export const dynamic = 'force-dynamic';

export async function POST(request) {
  try {
    const sessionId = request.headers.get('x-session-id');
    let body = {};
    try {
      const text = await request.text();
      if (text) {
        body = JSON.parse(text);
      }
    } catch (e) {
      // Ignore invalid JSON format
    }

    const payload = await proxyToBackend({
      path: '/reset',
      method: 'POST',
      body,
      sessionId,
    });

    return NextResponse.json(payload);
  } catch (error) {
    return NextResponse.json(
      { detail: error.message ?? 'Failed to reset environment.' },
      { status: error.status ?? 500 },
    );
  }
}
