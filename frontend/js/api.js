/**
 * API client — fetch + EventSource helpers.
 */

const BASE = "/api";

async function request(method, path, body = null) {
  const opts = {
    method,
    headers: { "Content-Type": "application/json" },
  };
  if (body) opts.body = JSON.stringify(body);

  const res = await fetch(`${BASE}${path}`, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  createSimulation(
    scenario,
    numConsumers,
    numWebsites,
    numCampaigns,
    numRounds,
  ) {
    return request("POST", "/simulations", {
      scenario,
      num_consumers: numConsumers,
      num_websites: numWebsites,
      num_campaigns: numCampaigns,
      num_rounds: numRounds,
    });
  },

  getSimulation(simId) {
    return request("GET", `/simulations/${simId}`);
  },

  listSimulations() {
    return request("GET", "/simulations");
  },

  getCampaigns(simId) {
    return request("GET", `/simulations/${simId}/campaigns`);
  },

  getCampaignDetail(simId, campaignId) {
    return request("GET", `/simulations/${simId}/campaigns/${campaignId}`);
  },

  updateCampaign(simId, campaignId, data) {
    return request(
      "PUT",
      `/simulations/${simId}/campaigns/${campaignId}`,
      data,
    );
  },

  getDashboard(simId) {
    return request("GET", `/simulations/${simId}/dashboard`);
  },
};

/**
 * Connect to an SSE stream endpoint.
 * Returns { close } for cleanup.
 */
export function connectSSE(path, onEvent, onError) {
  const url = `${BASE}${path}`;

  const eventSource = new EventSource(url);

  eventSource.onmessage = (msg) => {
    try {
      const data = JSON.parse(msg.data);
      onEvent(data);
    } catch (e) {
      console.error("SSE parse error:", e, msg.data);
    }
  };

  eventSource.onerror = (err) => {
    // EventSource auto-reconnects, but if readyState is CLOSED the stream ended
    if (eventSource.readyState === EventSource.CLOSED) {
      if (onError) onError(new Error("Stream connection closed"));
    }
  };

  return {
    close() {
      eventSource.close();
    },
  };
}
