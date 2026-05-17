/**
 * download_video.js — Downloads Big Buck Bunny MP4 to ./video.mp4
 * Skips if file already exists. Uses only built-in Node.js modules.
 */

const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');

const VIDEO_URL = 'https://download.blender.org/peach/bigbuckbunny_movies/big_buck_bunny_720p_h264.mov';
const OUTPUT_PATH = path.join(__dirname, 'video.mp4');

function download(url) {
  return new Promise((resolve, reject) => {
    const proto = url.startsWith('https') ? https : http;
    proto.get(url, (res) => {
      // Follow redirects
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        console.log('  Following redirect...');
        return download(res.headers.location).then(resolve).catch(reject);
      }

      if (res.statusCode !== 200) {
        return reject(new Error('HTTP ' + res.statusCode));
      }

      const totalBytes = parseInt(res.headers['content-length'], 10) || 0;
      let downloadedBytes = 0;
      const file = fs.createWriteStream(OUTPUT_PATH);

      res.on('data', (chunk) => {
        downloadedBytes += chunk.length;
        file.write(chunk);
        if (totalBytes > 0) {
          const pct = ((downloadedBytes / totalBytes) * 100).toFixed(1);
          const mb = (downloadedBytes / (1024 * 1024)).toFixed(1);
          const totalMb = (totalBytes / (1024 * 1024)).toFixed(1);
          process.stdout.write(`\r  Downloading: ${pct}% (${mb}/${totalMb} MB)`);
        }
      });

      res.on('end', () => {
        file.end();
        console.log('\n✅ Download complete: ' + OUTPUT_PATH);
        console.log('   Size: ' + (downloadedBytes / (1024 * 1024)).toFixed(1) + ' MB');
        resolve();
      });

      res.on('error', reject);
    }).on('error', reject);
  });
}

async function main() {
  if (fs.existsSync(OUTPUT_PATH)) {
    const stat = fs.statSync(OUTPUT_PATH);
    if (stat.size > 1000000) {
      console.log('✅ video.mp4 already exists (' + (stat.size / (1024 * 1024)).toFixed(1) + ' MB) — skipping download');
      return;
    }
  }

  console.log('📥 Downloading Big Buck Bunny...');
  console.log('   From: ' + VIDEO_URL);
  await download(VIDEO_URL);
}

main().catch((err) => {
  console.error('❌ Download failed:', err.message);
  process.exit(1);
});

module.exports = main;
