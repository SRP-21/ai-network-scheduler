/**
 * stats_server.js — Shared state + REST API helpers
 * Exports `state` object used by proxy.js.
 */

const state = {
  aiMode: false,
  bandwidthMbps: 10,
  intercepted: 0,
  requestsByType: {
    VIDEO_CHUNK: 0,
    VIDEO_MANIFEST: 0,
    AD_REQUEST: 0,
    ANALYTICS: 0,
    THUMBNAIL: 0,
    FONT_CSS: 0,
    OTHER: 0
  },
  totalDelayMs: 0,
  bandwidthFreedMB: 0,
  avgDelayMs: 0,
  lastRequests: [],
  mlLog: [],
  bufferHealth: { withoutAI: 0, withAI: 0 },
  quality:      { withoutAI: 'Auto', withAI: 'Auto' },
  stallCount:   { withoutAI: 0, withAI: 0 },
  history: [],

  // Tab registration: maps tabId → role ("with_ai" or "without_ai")
  tabRoles: {}
};

// Snapshot history every 1 second
setInterval(() => {
  state.history.push({
    time: Date.now(),
    intercepted: state.intercepted,
    requestsByType: { ...state.requestsByType },
    totalDelayMs: state.totalDelayMs,
    bandwidthFreedMB: state.bandwidthFreedMB,
    bufferHealth: { ...state.bufferHealth },
    quality: { ...state.quality },
    stallCount: { ...state.stallCount }
  });
  if (state.history.length > 60) state.history.shift();

  // Compute average delay
  if (state.intercepted > 0) {
    state.avgDelayMs = Math.round(state.totalDelayMs / state.intercepted);
  }
}, 1000);

module.exports = { state };
