/**
 * content.js — Injected into YouTube tabs
 * Reads video buffer health every 500ms and sends to background.js.
 * Handles YouTube SPA navigation via yt-navigate-finish.
 */

let stallCount = 0;
let videoEl = null;
let pollInterval = null;

function getYouTubeQuality() {
  try {
    const ytp = document.querySelector('.html5-video-player');
    if (ytp && typeof ytp.getPlaybackQuality === 'function') {
      const q = ytp.getPlaybackQuality();
      if (q.includes('hd1080')) return '1080p';
      if (q.includes('hd720'))  return '720p';
      if (q.includes('large'))  return '480p';
      if (q.includes('medium')) return '360p';
      if (q.includes('small'))  return '240p';
      if (q.includes('tiny'))   return '144p';
    }
  } catch (e) {}
  return 'Auto';
}

function initListeners() {
  if (!videoEl) return;
  videoEl.addEventListener('waiting', () => { stallCount++; });
  videoEl.addEventListener('playing', () => {});
}

function startPolling() {
  if (pollInterval) clearInterval(pollInterval);

  pollInterval = setInterval(() => {
    const currentVideo = document.querySelector('video');
    if (currentVideo && currentVideo !== videoEl) {
      videoEl = currentVideo;
      stallCount = 0;
      initListeners();
    }

    if (!videoEl) return;
    if (!videoEl.buffered || videoEl.buffered.length === 0) return;

    const currentTime = videoEl.currentTime;
    let bufferEnd = currentTime;
    for (let i = 0; i < videoEl.buffered.length; i++) {
      if (videoEl.buffered.start(i) <= currentTime && videoEl.buffered.end(i) > currentTime) {
        bufferEnd = videoEl.buffered.end(i);
        break;
      }
    }

    const bufferHealth = Math.max(0, bufferEnd - currentTime);

    try {
      chrome.runtime.sendMessage({
        type: 'BUFFER_UPDATE',
        bufferHealth: bufferHealth,
        quality: getYouTubeQuality(),
        playbackRate: videoEl.playbackRate,
        readyState: videoEl.readyState,
        stalledCount: stallCount
      });
    } catch (e) {
      if (pollInterval) clearInterval(pollInterval);
    }
  }, 500);
}

// Handle YouTube SPA navigation
document.addEventListener('yt-navigate-finish', () => {
  videoEl = null;
  stallCount = 0;
});

startPolling();
