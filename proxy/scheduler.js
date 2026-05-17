/**
 * scheduler.js — AI request classifier
 * Classifies URLs into priority tiers and returns delay in ms.
 */

function classifyRequest(url, host) {
  const u = (url || '').toLowerCase();
  const h = (host || '').toLowerCase();

  // VIDEO_CHUNK — highest priority, 0ms delay
  // Covers all YouTube CDN domains: googlevideo, gvt1, gvt2, gcp.gvt
  if (
    h.includes('googlevideo.com') ||
    h.includes('gvt1.com') ||
    h.includes('gvt2.com') ||
    h.includes('gcp.gvt') ||
    u.includes('/videoplayback') ||
    u.includes('mime=video') ||
    u.includes('itag=')
  ) {
    return { type: 'VIDEO_CHUNK', delay: 0, priority: 10 };
  }

  // VIDEO_MANIFEST — high priority, 0ms
  if (u.includes('/api/manifest') || u.includes('.m3u8') || u.includes('/player') || u.includes('/youtubei/v1/player')) {
    return { type: 'VIDEO_MANIFEST', delay: 0, priority: 9 };
  }

  // AD_REQUEST — lowest priority, 2000ms
  if (h.includes('googleads') || h.includes('pagead2') || h.includes('doubleclick') || h.includes('googlesyndication')) {
    return { type: 'AD_REQUEST', delay: 2000, priority: 0 };
  }

  // ANALYTICS — very low priority, 1500ms
  if (h.includes('google-analytics') || h.includes('analytics') || u.includes('/api/stats') || u.includes('/ptracking') || u.includes('/youtubei/v1/log')) {
    return { type: 'ANALYTICS', delay: 1500, priority: 1 };
  }

  // THUMBNAIL — medium priority, 800ms
  if (h.includes('i.ytimg.com') || h.includes('yt3.ggpht')) {
    return { type: 'THUMBNAIL', delay: 800, priority: 3 };
  }

  // FONT_CSS — medium priority, 600ms
  if (h.includes('fonts.googleapis') || h.includes('fonts.gstatic')) {
    return { type: 'FONT_CSS', delay: 600, priority: 4 };
  }

  // OTHER — low priority, 300ms
  return { type: 'OTHER', delay: 300, priority: 5 };
}

/**
 * Calculate the effective delay based on bandwidth setting.
 * Lower bandwidth = higher delay multiplier.
 */
function getEffectiveDelay(baseDelay, bandwidthMbps, aiMode) {
  if (!aiMode) return 0;
  if (baseDelay === 0) return 0;

  const factor = (50 - bandwidthMbps) / 50;
  return Math.max(0, Math.round(baseDelay * Math.max(0.1, factor)));
}

module.exports = { classifyRequest, getEffectiveDelay };
