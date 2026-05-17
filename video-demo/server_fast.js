/**
 * server_fast.js — Port 3002 — WITH AI
 * Serves video.mp4 at full speed, no throttling.
 */

const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(cors());

const VIDEO_PATH = path.join(__dirname, 'video.mp4');

// ── Stats ───────────────────────────────────────────────────────────
const stats = {
  bytesServed: 0,
  currentSpeedKbps: 0,
  bufferStalls: 0,
  activeConnections: 0
};

let bytesThisSecond = 0;
setInterval(() => {
  stats.currentSpeedKbps = Math.round((bytesThisSecond / 1024) * 10) / 10;
  bytesThisSecond = 0;
}, 1000);

// ── GET /stats ──────────────────────────────────────────────────────
app.get('/stats', (req, res) => {
  res.json(stats);
});

// ── GET /video — full speed streaming with Range support ────────────
app.get('/video', (req, res) => {
  if (!fs.existsSync(VIDEO_PATH)) {
    return res.status(404).send('video.mp4 not found. Run: node download_video.js');
  }

  const stat = fs.statSync(VIDEO_PATH);
  const fileSize = stat.size;
  const range = req.headers.range;

  let start = 0;
  let end = fileSize - 1;

  if (range) {
    const parts = range.replace(/bytes=/, '').split('-');
    start = parseInt(parts[0], 10);
    end = parts[1] ? parseInt(parts[1], 10) : fileSize - 1;
    end = Math.min(end, fileSize - 1);

    res.writeHead(206, {
      'Content-Range': 'bytes ' + start + '-' + end + '/' + fileSize,
      'Accept-Ranges': 'bytes',
      'Content-Length': (end - start + 1),
      'Content-Type': 'video/mp4',
      'Cache-Control': 'no-store'
    });
  } else {
    res.writeHead(200, {
      'Content-Length': fileSize,
      'Content-Type': 'video/mp4',
      'Accept-Ranges': 'bytes',
      'Cache-Control': 'no-store'
    });
  }

  stats.activeConnections++;

  const stream = fs.createReadStream(VIDEO_PATH, { start, end });

  stream.on('data', (chunk) => {
    stats.bytesServed += chunk.length;
    bytesThisSecond += chunk.length;
  });

  stream.pipe(res);

  stream.on('end', () => {
    stats.activeConnections = Math.max(0, stats.activeConnections - 1);
  });

  stream.on('error', () => {
    stats.activeConnections = Math.max(0, stats.activeConnections - 1);
    res.end();
  });

  req.on('close', () => {
    stream.destroy();
    stats.activeConnections = Math.max(0, stats.activeConnections - 1);
  });
});

const PORT = 3002;
app.listen(PORT, () => {
  console.log('✅ WITH AI server:    http://localhost:' + PORT);
  console.log('   Bandwidth: UNLIMITED');
});
