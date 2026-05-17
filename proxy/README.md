# AI Network Scheduler — Real Proxy + Chrome Extension

A real HTTP/HTTPS MITM proxy that intercepts YouTube network requests and uses AI-based priority scheduling to improve video streaming quality. The Chrome extension provides a live 3×3 dashboard UI.

## Architecture

```
YouTube Server
      ↓ HTTPS
Node.js Proxy (localhost:8888)
      ↓ classifies every request
      ↓ delays ads/analytics/thumbnails
      ↓ passes video chunks instantly
      ↓ exposes stats at localhost:8889
Chrome Browser (proxy = 127.0.0.1:8888)
      ↓
Chrome Extension (reads stats from :8889)
      ↓
Popup Dashboard (3×3 grid, live graphs)
```

## Setup (5 minutes)

### Step 1 — Install proxy dependencies

```bash
cd proxy
npm install
```

### Step 2 — Export and trust the CA certificate

```bash
node proxy.js --export-cert
```

This creates `ca.crt` in the proxy folder.

**Windows:**
1. Double-click `ca.crt`
2. Click "Install Certificate"
3. Select "Local Machine" → Next
4. Select "Place all certificates in the following store"
5. Click Browse → select "Trusted Root Certification Authorities"
6. Click Next → Finish

**Mac:**
1. Double-click `ca.crt` → opens Keychain Access
2. Find "AI Network Scheduler CA" in login keychain
3. Double-click it → Trust → "Always Trust"

**Linux:**
```bash
sudo cp ca.crt /usr/local/share/ca-certificates/ai-proxy.crt
sudo update-ca-certificates
```

> ⚠️ This step is required for HTTPS interception. Without it, Chrome will show certificate warnings on every HTTPS site.

### Step 3 — Start the proxy

```bash
cd proxy
node proxy.js
```

You should see:
```
🚀 AI Network Scheduler Proxy
   Proxy:  http://127.0.0.1:8888
📊 Stats server running on http://localhost:8889
```

### Step 4 — Set Chrome to use the proxy

**Windows:**
1. Settings → System → Open your computer's proxy settings
2. Manual proxy setup → ON
3. Address: `127.0.0.1`  Port: `8888`
4. Save

**Mac:**
1. System Preferences → Network → Advanced → Proxies
2. Check "Web Proxy (HTTP)" and "Secure Web Proxy (HTTPS)"
3. Server: `127.0.0.1`  Port: `8888`

**Or launch Chrome with proxy flag:**
```bash
chrome --proxy-server="127.0.0.1:8888"
```

### Step 5 — Load the Chrome extension

1. Open `chrome://extensions`
2. Enable **Developer Mode** (top right toggle)
3. Click **Load Unpacked**
4. Select the `extension/` folder

### Step 6 — Demo

1. Open **two YouTube tabs** with the same video
2. Click the extension icon (puzzle piece in toolbar)
3. **Tab 1:** Toggle AI **OFF** — this is the baseline
4. **Tab 2:** Toggle AI **ON** — this gets priority scheduling
5. Set bandwidth slider to **5 Mbps**
6. Watch cells 4 and 5 in the popup diverge with real buffer data
7. Cell 7 shows live packet flow with delays applied

## File Structure

```
proxy/
├── package.json        ← npm dependencies
├── proxy.js            ← HTTP/HTTPS MITM proxy server
├── scheduler.js        ← AI request classification
└── stats_server.js     ← REST API at localhost:8889

extension/
├── manifest.json       ← Chrome MV3 manifest
├── background.js       ← Polls proxy stats, relays buffer data
├── content.js          ← Reads YouTube video buffer health
├── popup.html          ← 3×3 grid dashboard UI
├── popup.js            ← Live chart updates
└── styles.css          ← Clean white UI
```

## API Endpoints (localhost:8889)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/stats` | Full stats JSON |
| POST | `/mode` | `{ aiMode: true/false }` |
| POST | `/bandwidth` | `{ mbps: 10 }` |
| POST | `/buffer` | Buffer health from content script |
| GET | `/history` | Last 60 seconds of snapshots |

## How it works

The proxy classifies every HTTP/HTTPS request into one of 7 categories:

| Type | Delay | Priority | Example |
|------|-------|----------|---------|
| VIDEO_CHUNK | 0ms | 10/10 | `googlevideo.com/videoplayback` |
| VIDEO_MANIFEST | 0ms | 9/10 | `/api/manifest`, `.m3u8` |
| AD_REQUEST | 2000ms | 0/10 | `doubleclick.net`, `googleads` |
| ANALYTICS | 1500ms | 1/10 | `google-analytics.com` |
| THUMBNAIL | 800ms | 3/10 | `i.ytimg.com` |
| FONT_CSS | 600ms | 4/10 | `fonts.googleapis.com` |
| OTHER | 300ms | 5/10 | Everything else |

Delays are scaled by bandwidth: lower bandwidth = higher delays on non-video traffic, ensuring video chunks always get through first.

## Cleanup

When done testing, **remember to remove the proxy setting** from your OS/browser, or YouTube and other sites will stop loading.
