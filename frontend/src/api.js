const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';
const STUDENT_ID = import.meta.env.VITE_STUDENT_ID ?? 'sumin';

async function request(path, { role = 'student', method = 'GET', body } = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      'X-Role': role,
      'X-Student-Id': STUDENT_ID,
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const message = data?.error?.message ?? `Request failed: ${response.status}`;
    throw new Error(message);
  }
  return data;
}

export function getTodaySession(date) {
  const query = date ? `?date=${date}` : '';
  return request(`/session/today${query}`);
}

export function getItem(itemId) {
  return request(`/items/${itemId}`);
}

export function submitAttempt(payload) {
  return request('/attempts', {
    method: 'POST',
    body: payload,
  });
}

export function submitReflection(payload) {
  return request('/reflections', {
    method: 'POST',
    body: payload,
  });
}

export function getMastery() {
  return request('/mastery');
}

export function getParentSummary() {
  return request('/parent/weekly-summary', { role: 'parent' });
}

export function markParentSummarySent() {
  return request('/parent/weekly-summary/sent', {
    role: 'parent',
    method: 'POST',
    body: {},
  });
}

export function getOperatorItems() {
  return request('/operator/items', { role: 'operator' });
}

export function getOperatorItem(itemId) {
  return request(`/operator/items/${itemId}`, { role: 'operator' });
}

export function getOperatorAttempts() {
  return request('/operator/attempts', { role: 'operator' });
}

export function getOperatorWeaknessReport() {
  return request('/operator/weakness-report', { role: 'operator' });
}

export function getOperatorUnmatchedPaths() {
  return request('/operator/unmatched-paths', { role: 'operator' });
}
