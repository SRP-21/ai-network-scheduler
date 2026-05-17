/**
 * server_throttled.js — Port 3001 — WITHOUT AI
 * Serves video.mp4 with a hard bandwidth cap.
 * Throttle rate is adjustable via POST /set-bandwidth.
 */

const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(cors());
app.use(express.json());

const VIDEO_PATH = path.join(__dirname, 'video.mp4');

// ── Throttle config (adjustable at runtime) ─────────────────────────
let BANDWIDTH_CAP_BYTES_PER_SEC = 200 * 1024; // 200 KB/s default
const CHUNK_SIZE = 4 * 1024; // 4KB per chunk — tight control

// ── Stats ───────────────────────────────────────────────────────────
const stats = {
  bytesServed: 0,
  currentSpeedKbps: 0,
  bufferStalls: 0,
  activeConnections: 0
};

// Speed tracking: bytes sent in the last second
let bytesThisSecond = 0;
setInterval(() => {
  stats.currentSpeedKbps = Math.round((bytesThisSecond / 1024) * 10) / 10;
  bytesThisSecond = 0;
}, 1000);

// ── GET /stats ──────────────────────────────────────────────────────
app.get('/stats', (req, res) => {
  res.json({
    ...stats,
    bandwidthCapKbps: Math.round(BANDWIDTH_CAP_BYTES_PER_SEC / 1024)
  });
});

// ── POST /set-bandwidth ─────────────────────────────────────────────
app.post('/set-bandwidth', (req, res) => {
  const kbps = parseInt(req.body.kbps, 10);
  if (kbps && kbps >= 50 && kbps <= 5000) {
    BANDWIDTH_CAP_BYTES_PER_SEC = kbps * 1024;
    console.log('  ⚙️  Bandwidth cap changed to ' + kbps + ' KB/s');
    res.json({ ok: true, bandwidthCapKbps: kbps });
  } else {
    res.status(400).json({ error: 'kbps must be 50-5000' });
  }
});

// ── GET /video — throttled streaming with Range support ─────────────
app.get('/video', (req, res) => {
  if (!fs.existsSync(VIDEO_PATH)) {
    return res.status(404).send('video.mp4 not found. Run: node download_video.js');
  }

  const stat = fs.statSync(VIDEO_PATH);
  const fileSize = stat.size;
  const range = req.headers.range;

  let start = 0;
  let end = fileSize - 1;

  // Anti-cache + anti-buffer headers
  var antiHeaders = {
    'Content-Type': 'video/mp4',
    'Accept-Ranges': 'bytes',
    'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
    'Pragma': 'no-cache',
    'Expires': '0',
    'X-Accel-Buffering': 'no'
  };

  if (range) {
    const parts = range.replace(/bytes=/, '').split('-');
    start = parseInt(parts[0], 10);
    end = parts[1] ? parseInt(parts[1], 10) : fileSize - 1;
    end = Math.min(end, fileSize - 1);

    antiHeaders['Content-Range'] = 'bytes ' + start + '-' + end + '/' + fileSize;
    antiHeaders['Content-Length'] = (end - start + 1);
    res.writeHead(206, antiHeaders);
  } else {
    antiHeaders['Content-Length'] = fileSize;
    res.writeHead(200, antiHeaders);
  }

  stats.activeConnections++;

  const stream = fs.createReadStream(VIDEO_PATH, {
    start: start,
    end: end,
    highWaterMark: CHUNK_SIZE
  });

  let destroyed = false;

  function sendChunks() {
    if (destroyed) return;

    let chunk;
    while ((chunk = stream.read()) !== null) {
      if (destroyed) return;

      const ok = res.write(chunk);
      const chunkLen = chunk.length;
      stats.bytesServed += chunkLen;
      bytesThisSecond += chunkLen;

      if (!ok) {
        // Backpressure: wait for drain
        res.once('drain', sendChunks);
        return;
      }

      // Throttle: schedule next read after delay
      // 4KB chunks at 200 KB/s = (4096 / 204800) * 1000 = 20ms per chunk
      const delayMs = (CHUNK_SIZE / BANDWIDTH_CAP_BYTES_PER_SEC) * 1000;
      stream.pause();
      setTimeout(() => {
        if (!destroyed) {
          stream.resume();
          sendChunks();
        }
      }, delayMs);
      return;
    }
  }

  stream.on('readable', sendChunks);

  stream.on('end', () => {
    if (!destroyed) {
      destroyed = true;
      stats.activeConnections = Math.max(0, stats.activeConnections - 1);
      res.end();
    }
  });

  stream.on('error', () => {
    if (!destroyed) {
      destroyed = true;
      stats.activeConnections = Math.max(0, stats.activeConnections - 1);
      res.end();
    }
  });

  req.on('close', () => {
    if (!destroyed) {
      destroyed = true;
      stream.destroy();
      stats.activeConnections = Math.max(0, stats.activeConnections - 1);
    }
  });
});

const PORT = 3001;
app.listen(PORT, () => {
  console.log('❌ WITHOUT AI server: http://localhost:' + PORT);
  console.log('   Bandwidth cap: ' + Math.round(BANDWIDTH_CAP_BYTES_PER_SEC / 1024) + ' KB/s');
  console.log('   Chunk size: ' + CHUNK_SIZE + ' bytes');
});
