/**
 * background.js — Service worker for AI Network Scheduler (v2)
 * Polls proxy stats, forwards buffer updates with tabId.
 */

const BASE_URL   = 'http://localhost:8888/ai-scheduler';
const STATS_URL  = BASE_URL + '/stats';
const BUFFER_URL = BASE_URL + '/buffer';

// ── Poll stats from proxy ────────────────────────────────────────────
async function fetchStats() {
  try {
    const res = await fetch(STATS_URL);
    if (res.ok) {
      const data = await res.json();
      await chrome.storage.local.set({
        scheduler_stats: data,
        proxy_online: true
      });
    } else {
      await chrome.storage.local.set({ proxy_online: false });
    }
  } catch (e) {
    await chrome.storage.local.set({ proxy_online: false });
  }
}

chrome.alarms.create('fetch-stats', { periodInMinutes: 0.5 });
chrome.alarms.onAlarm.addListener(function(alarm) {
  if (alarm.name === 'fetch-stats') fetchStats();
});

chrome.runtime.onInstalled.addListener(function() { fetchStats(); });
chrome.runtime.onStartup.addListener(function() { fetchStats(); });
fetchStats();

// ── Receive buffer updates from content.js → POST to proxy with tabId ──
chrome.runtime.onMessage.addListener(function(message, sender, sendResponse) {
  if (message.type === 'BUFFER_UPDATE') {
    var tabId = sender.tab ? sender.tab.id : 0;

    fetch(BUFFER_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tabId: tabId,
        bufferHealth: message.bufferHealth,
        quality: message.quality,
        stalledCount: message.stalledCount
      })
    }).catch(function() {});

    fetchStats();
  }

  if (message.type === 'FETCH_STATS') {
    fetchStats();
  }

  // Register a tab role from popup
  if (message.type === 'REGISTER_TAB') {
    fetch(BASE_URL + '/register-tab', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tabId: message.tabId,
        role: message.role
      })
    }).then(function() { fetchStats(); }).catch(function() {});
  }
});
