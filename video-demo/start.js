/**
 * start.js — Launcher for both video servers
 * Downloads video if needed, then starts both servers.
 */

const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const VIDEO_PATH = path.join(__dirname, 'video.mp4');

async function main() {
  console.log('\n🎬 AI Network Scheduler — Video Demo\n');

  // Step 1: Check for video
  if (!fs.existsSync(VIDEO_PATH) || fs.statSync(VIDEO_PATH).size < 1000000) {
    console.log('📥 Video not found. Downloading Big Buck Bunny...\n');
    try {
      execSync('node download_video.js', { cwd: __dirname, stdio: 'inherit' });
    } catch (e) {
      console.error('\n❌ Failed to download video. Please download manually.');
      console.error('   Place video.mp4 in: ' + __dirname);
      process.exit(1);
    }
    console.log('');
  } else {
    console.log('✅ video.mp4 found (' + (fs.statSync(VIDEO_PATH).size / (1024 * 1024)).toFixed(1) + ' MB)\n');
  }

  // Step 2: Start both servers
  const throttled = spawn('node', ['server_throttled.js'], {
    cwd: __dirname,
    stdio: 'inherit'
  });

  const fast = spawn('node', ['server_fast.js'], {
    cwd: __dirname,
    stdio: 'inherit'
  });

  // Step 3: Print instructions
  setTimeout(() => {
    console.log('\n────────────────────────────────────────');
    console.log('  Demo page: file:///' + path.join(__dirname, 'demo.html').replace(/\\/g, '/'));
    console.log('  Or just open demo.html in your browser');
    console.log('────────────────────────────────────────\n');
  }, 500);

  // Handle cleanup
  process.on('SIGINT', () => {
    throttled.kill();
    fast.kill();
    process.exit(0);
  });

  process.on('exit', () => {
    throttled.kill();
    fast.kill();
  });
}

main();
