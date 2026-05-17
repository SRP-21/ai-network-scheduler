export function classifyRequest(url) {
  const urlLower = url.toLowerCase();
  
  if (urlLower.includes('googlevideo.com/videoplayback')) {
    return { type: 'VIDEO_CHUNK', delay: 0, priority: 10 };
  }
  if (urlLower.includes('/api/manifest') || urlLower.includes('.m3u8')) {
    return { type: 'VIDEO_MANIFEST', delay: 0, priority: 10 };
  }
  if (urlLower.includes('googleads') || urlLower.includes('pagead2') || urlLower.includes('doubleclick') || urlLower.includes('ad_status')) {
    return { type: 'AD_REQUEST', delay: 2000, priority: 0 };
  }
  if (urlLower.includes('google-analytics') || urlLower.includes('stats.g') || urlLower.includes('/ptracking') || urlLower.includes('/api/stats')) {
    return { type: 'ANALYTICS', delay: 1500, priority: 1 };
  }
  if (urlLower.includes('/vi/') || urlLower.includes('i.ytimg.com') || urlLower.includes('yt3.ggpht')) {
    return { type: 'THUMBNAIL', delay: 800, priority: 3 };
  }
  if (urlLower.includes('fonts.googleapis') || urlLower.includes('fonts.gstatic')) {
    return { type: 'FONT_CSS', delay: 600, priority: 4 };
  }
  
  return { type: 'OTHER', delay: 400, priority: 5 };
}
