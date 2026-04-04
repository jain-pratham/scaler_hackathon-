import { NextResponse } from 'next/server';

import { proxyToBackend } from '@/lib/backendProxy';

export const dynamic = 'force-dynamic';

export async function GET(request) {
  try {
    const sessionId = request.headers.get('x-session-id');

    const payload = await proxyToBackend({
      path: '/state',
      method: 'GET',
      sessionId,
    });

    return NextResponse.json(payload);
  } catch (error) {
    return NextResponse.json(
      { detail: error.message ?? 'Failed to read environment state.' },
      { status: error.status ?? 500 },
    );
  }
}

