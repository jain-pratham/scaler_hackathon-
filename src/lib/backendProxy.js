const BACKEND_URL = process.env.PYTHON_BACKEND_URL ?? 'http://127.0.0.1:8000';
const BACKEND_TIMEOUT_MS = 5000;

export async function proxyToBackend({
  path,
  method = 'GET',
  body,
  sessionId,
}) {
  let response;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), BACKEND_TIMEOUT_MS);

  try {
    response = await fetch(`${BACKEND_URL}${path}`, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'X-Session-Id': sessionId,
      },
      cache: 'no-store',
      signal: controller.signal,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    const error = new Error(
      `Python backend is unavailable at ${BACKEND_URL}. Start FastAPI with "npm run dev:backend".`,
    );
    error.status = 503;
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }

  const payload = await response.json().catch(() => ({
    detail: 'Backend returned a non-JSON response.',
  }));

  if (!response.ok) {
    const error = new Error(payload.detail ?? 'Backend request failed.');
    error.status = response.status;
    throw error;
  }

  return payload;
}
