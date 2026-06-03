const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function fetchJson(path) {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  return response.json();
}

export function getMetrics(storeId) {
  return fetchJson(`/stores/${storeId}/metrics`);
}

export function getFunnel(storeId) {
  return fetchJson(`/stores/${storeId}/funnel`);
}

export function getHeatmap(storeId) {
  return fetchJson(`/stores/${storeId}/heatmap`);
}

export function getAnomalies(storeId) {
  return fetchJson(`/stores/${storeId}/anomalies`);
}

export function getHealth() {
  return fetchJson('/health');
}
