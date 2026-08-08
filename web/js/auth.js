const API_URL = 'http://localhost:8000/api';
const AUTH_TOKEN_KEY = 'authToken';

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
  return localStorage.getItem(AUTH_TOKEN_KEY) || sessionStorage.getItem(AUTH_TOKEN_KEY);
}

function setToken(token) {
  localStorage.setItem(AUTH_TOKEN_KEY, token);
  sessionStorage.setItem(AUTH_TOKEN_KEY, token);
}

function clearToken() {
  localStorage.removeItem(AUTH_TOKEN_KEY);
  sessionStorage.removeItem(AUTH_TOKEN_KEY);
}

importHashToken();

function requireAuth(redirectUrl = 'index.html') {
  if (!getToken()) {
    window.location.href = redirectUrl;
    throw new Error('Unauthorized');
  }
}

async function fetchWithAuth(path, options = {}) {
  const token = getToken();
  if (!token) {
    clearToken();
    window.location.href = 'index.html';
    throw new Error('Unauthorized');
  }

  options.headers = {
    ...options.headers,
    Authorization: `Bearer ${token}`,
  };

  const response = await fetch(`${API_URL}${path}`, options);

  if (response.status === 401) {
    clearToken();
    window.location.href = 'index.html';
    throw new Error('Unauthorized');
  }

  return response;
}
