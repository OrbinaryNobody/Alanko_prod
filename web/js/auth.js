const API_URL = window.ALANKO_API_URL || 'http://localhost:8000/api';
const AUTH_TOKEN_KEY = 'authToken';
const DEFAULT_TIMEOUT_MS = 15000;

class ApiError extends Error {
  constructor(message, { status = 0, detail = null, response = null } = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
    this.response = response;
  }
}

function getTokenFromHash() {
  const rawHash = window.location.hash.replace(/^#/, '');
  const params = new URLSearchParams(rawHash);
  return params.get('authToken') || params.get('token') || null;
}

function cleanHash() {
  if (window.history.replaceState) {
    window.history.replaceState(null, '', window.location.pathname + window.location.search);
  } else {
    window.location.hash = '';
  }
}

function importHashToken() {
  const token = getTokenFromHash();
  if (token) {
    setToken(token);
    cleanHash();
  }
}

function getToken() {
  try {
    // Сначала проверяем sessionStorage (приоритет)
    const sessionToken = sessionStorage.getItem(AUTH_TOKEN_KEY);
    if (sessionToken) return sessionToken;
    
    // Если sessionStorage пуст, берем из localStorage
    const localToken = localStorage.getItem(AUTH_TOKEN_KEY);
    if (localToken) {
      // Синхронизируем обратно в sessionStorage
      sessionStorage.setItem(AUTH_TOKEN_KEY, localToken);
      return localToken;
    }
    return null;
  } catch (e) {
    console.warn('Storage access error:', e);
    return null;
  }
}

function setToken(token) {
  try {
    sessionStorage.setItem(AUTH_TOKEN_KEY, token);
    localStorage.setItem(AUTH_TOKEN_KEY, token);
  } catch (e) {
    console.warn('Storage write error:', e);
  }
}

function clearToken() {
  try {
    sessionStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(AUTH_TOKEN_KEY);
  } catch (e) {
    console.warn('Storage clear error:', e);
  }
}

importHashToken();

function requireAuth(redirectUrl = 'index.html') {
  if (!getToken()) {
    window.location.href = redirectUrl;
    throw new Error('Unauthorized');
  }
}

function redirectToLogin(redirectUrl = 'index.html') {
  clearToken();
  if (!window.location.pathname.endsWith(redirectUrl)) {
    window.location.href = redirectUrl;
  }
}

async function apiFetch(path, options = {}) {
  const token = getToken();
  const {
    auth = true,
    timeoutMs = DEFAULT_TIMEOUT_MS,
    redirectUrl = 'index.html',
    ...fetchOptions
  } = options;

  if (auth && !token) {
    redirectToLogin(redirectUrl);
    throw new ApiError('Unauthorized', { status: 401 });
  }

  const headers = new Headers(fetchOptions.headers || {});
  if (auth) headers.set('Authorization', `Bearer ${token}`);
  if (!headers.has('Accept')) headers.set('Accept', 'application/json');

  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);
  if (fetchOptions.signal) {
    fetchOptions.signal.addEventListener('abort', () => controller.abort(), { once: true });
  }

  let response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...fetchOptions,
      headers,
      signal: controller.signal,
    });
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new ApiError('Request timed out', { status: 408 });
    }
    throw new ApiError('Network request failed', { detail: error.message });
  } finally {
    window.clearTimeout(timeoutId);
  }

  if (response.status === 401 && auth) {
    redirectToLogin(redirectUrl);
    throw new ApiError('Unauthorized', { status: 401, response });
  }

  if (!response.ok) {
    let detail = null;
    try {
      const payload = await response.clone().json();
      detail = payload.detail || payload.message || null;
    } catch (_) {
      detail = null;
    }
    throw new ApiError(detail || `Request failed with status ${response.status}`, {
      status: response.status,
      detail,
      response,
    });
  }

  return response;
}

async function requestJson(path, options = {}) {
  const response = await apiFetch(path, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
  if (response.status === 204) return null;
  return response.json();
}

async function requestFormData(path, formData, options = {}) {
  const response = await apiFetch(path, { ...options, body: formData });
  if (response.status === 204) return null;
  return response.json();
}

async function requestFile(path, options = {}) {
  return apiFetch(path, options);
}

async function fetchWithAuth(path, options = {}) {
  return apiFetch(path, options);
}
