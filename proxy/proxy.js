/**
 * proxy.js — HTTP/HTTPS Proxy with AI scheduling
 * Listens on port 8888. Classifies and delays non-video HTTP requests.
 * HTTPS connections are tunneled transparently with pre-tunnel delay.
 * Stats API is served on the SAME port at /ai-scheduler/* paths.
 */

const http = require('http');
const net = require('net');

const { classifyRequest, getEffectiveDelay } = require('./scheduler');
const { state } = require('./stats_server');

// ══════════════════════════════════════════════════════════════════════
// DELAY UTILITY
// ══════════════════════════════════════════════════════════════════════

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// ══════════════════════════════════════════════════════════════════════
// STATS TRACKING
// ══════════════════════════════════════════════════════════════════════

function trackRequest(classification, effectiveDelay, host) {
  state.intercepted++;
  state.requestsByType[classification.type] =
    (state.requestsByType[classification.type] || 0) + 1;
  state.totalDelayMs += effectiveDelay;

  if (classification.priority < 9) {
    state.bandwidthFreedMB += 0.01;
  }

  state.lastRequests.unshift({
    type: classification.type,
    url: host || 'unknown',
    delay: effectiveDelay,
    action: effectiveDelay > 0 ? '⏸' : '✅'
  });
  if (state.lastRequests.length > 10) state.lastRequests.length = 10;

  state.mlLog.unshift({
    type: classification.type,
    priority: `${classification.priority}/10`,
    action: effectiveDelay > 0 ? `DELAY ${effectiveDelay}ms` : 'PASS INSTANTLY'
  });
  if (state.mlLog.length > 5) state.mlLog.length = 5;
}

// ══════════════════════════════════════════════════════════════════════
// JSON BODY PARSER
// ══════════════════════════════════════════════════════════════════════

function readBody(req) {
  return new Promise((resolve) => {
    let body = '';
    req.on('data', (chunk) => { body += chunk; });
    req.on('end', () => {
      try { resolve(JSON.parse(body)); }
      catch (e) { resolve({}); }
    });
  });
}

// ══════════════════════════════════════════════════════════════════════
// UNIFIED HTTP SERVER — Proxy + Stats API on port 8888
// ══════════════════════════════════════════════════════════════════════

const proxyServer = http.createServer(async (clientReq, clientRes) => {
  const reqUrl = clientReq.url;
  const host = clientReq.headers.host || '';

  // Extract API path — Chrome proxy sends full URL, direct sends path only
  let apiPath = '';
  const aiIdx = reqUrl.indexOf('/ai-scheduler/');
  if (aiIdx !== -1) {
    apiPath = reqUrl.substring(aiIdx + '/ai-scheduler'.length);
  }

  // ── STATS API ─────────────────────────────────────────────────────
  if (aiIdx !== -1) {
    clientRes.setHeader('Access-Control-Allow-Origin', '*');
    clientRes.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    clientRes.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (clientReq.method === 'OPTIONS') {
      clientRes.writeHead(204);
      clientRes.end();
      return;
    }

    // GET /stats
    if (apiPath === '/stats' && clientReq.method === 'GET') {
      clientRes.writeHead(200, { 'Content-Type': 'application/json' });
      clientRes.end(JSON.stringify(state));
      return;
    }

    // POST /mode
    if (apiPath === '/mode' && clientReq.method === 'POST') {
      const body = await readBody(clientReq);
      if (typeof body.aiMode === 'boolean') {
        state.aiMode = body.aiMode;
        clientRes.writeHead(200, { 'Content-Type': 'application/json' });
        clientRes.end(JSON.stringify({ ok: true, aiMode: state.aiMode }));
      } else {
        clientRes.writeHead(400, { 'Content-Type': 'application/json' });
        clientRes.end(JSON.stringify({ error: 'Expected { aiMode: true/false }' }));
      }
      return;
    }

    // POST /bandwidth
    if (apiPath === '/bandwidth' && clientReq.method === 'POST') {
      const body = await readBody(clientReq);
      if (typeof body.mbps === 'number') {
        state.bandwidthMbps = Math.max(1, Math.min(50, body.mbps));
        clientRes.writeHead(200, { 'Content-Type': 'application/json' });
        clientRes.end(JSON.stringify({ ok: true, bandwidthMbps: state.bandwidthMbps }));
      } else {
        clientRes.writeHead(400, { 'Content-Type': 'application/json' });
        clientRes.end(JSON.stringify({ error: 'Expected { mbps: <number> }' }));
      }
      return;
    }

    // POST /register-tab — assign a tab role ("with_ai" or "without_ai")
    if (apiPath === '/register-tab' && clientReq.method === 'POST') {
      const body = await readBody(clientReq);
      if (body.tabId && (body.role === 'with_ai' || body.role === 'without_ai')) {
        // Clear any previous tab with the same role
        for (const [tid, role] of Object.entries(state.tabRoles)) {
          if (role === body.role) delete state.tabRoles[tid];
        }
        state.tabRoles[String(body.tabId)] = body.role;
        clientRes.writeHead(200, { 'Content-Type': 'application/json' });
        clientRes.end(JSON.stringify({ ok: true, tabId: body.tabId, role: body.role, allTabs: state.tabRoles }));
      } else {
        clientRes.writeHead(400, { 'Content-Type': 'application/json' });
        clientRes.end(JSON.stringify({ error: 'Expected { tabId: <number>, role: "with_ai" | "without_ai" }' }));
      }
      return;
    }

    // POST /buffer — buffer health from a specific tab
    if (apiPath === '/buffer' && clientReq.method === 'POST') {
      const body = await readBody(clientReq);
      const tabId = String(body.tabId || '');
      const role = state.tabRoles[tabId];

      if (role === 'with_ai') {
        state.bufferHealth.withAI = body.bufferHealth || 0;
        state.quality.withAI = body.quality || 'Auto';
        state.stallCount.withAI = body.stalledCount || 0;
      } else if (role === 'without_ai') {
        state.bufferHealth.withoutAI = body.bufferHealth || 0;
        state.quality.withoutAI = body.quality || 'Auto';
        state.stallCount.withoutAI = body.stalledCount || 0;
      }
      // If tab not registered, ignore silently

      clientRes.writeHead(200, { 'Content-Type': 'application/json' });
      clientRes.end(JSON.stringify({ ok: true, tabId, role: role || 'unregistered' }));
      return;
    }

    // GET /history
    if (apiPath === '/history' && clientReq.method === 'GET') {
      clientRes.writeHead(200, { 'Content-Type': 'application/json' });
      clientRes.end(JSON.stringify(state.history));
      return;
    }

    clientRes.writeHead(404);
    clientRes.end('Not found');
    return;
  }

  // ── REGULAR HTTP PROXY ────────────────────────────────────────────
  try {
    const classification = classifyRequest(reqUrl, host);
    const effectiveDelay = getEffectiveDelay(
      classification.delay, state.bandwidthMbps, state.aiMode
    );

    trackRequest(classification, effectiveDelay, host);

    if (effectiveDelay > 0) {
      await delay(effectiveDelay);
    }

    const parsed = new URL(reqUrl);
    const options = {
      hostname: parsed.hostname,
      port: parsed.port || 80,
      path: parsed.pathname + parsed.search,
      method: clientReq.method,
      headers: clientReq.headers
    };

    const proxyReq = http.request(options, (proxyRes) => {
      clientRes.writeHead(proxyRes.statusCode, proxyRes.headers);
      proxyRes.pipe(clientRes, { end: true });
    });

    proxyReq.on('error', (err) => {
      try {
        clientRes.writeHead(502);
        clientRes.end('Proxy error: ' + err.message);
      } catch (e) {}
    });

    clientReq.pipe(proxyReq, { end: true });
  } catch (err) {
    try {
      clientRes.writeHead(500);
      clientRes.end('Internal proxy error');
    } catch (e) {}
  }
});

// ══════════════════════════════════════════════════════════════════════
// HTTPS CONNECT — Transparent tunnel with classification + delay
// ══════════════════════════════════════════════════════════════════════

proxyServer.on('connect', async (req, clientSocket, head) => {
  try {
    const [hostname, port] = req.url.split(':');
    const targetPort = parseInt(port, 10) || 443;

    const classification = classifyRequest('', hostname);
    const effectiveDelay = getEffectiveDelay(
      classification.delay, state.bandwidthMbps, state.aiMode
    );

    trackRequest(classification, effectiveDelay, hostname);

    if (effectiveDelay > 0) {
      await delay(effectiveDelay);
    }

    const serverSocket = net.connect(targetPort, hostname, () => {
      clientSocket.write(
        'HTTP/1.1 200 Connection Established\r\n' +
        'Proxy-Agent: AI-Network-Scheduler\r\n' +
        '\r\n'
      );
      if (head && head.length > 0) {
        serverSocket.write(head);
      }
      serverSocket.pipe(clientSocket);
      clientSocket.pipe(serverSocket);
    });

    serverSocket.on('error', () => {
      try { clientSocket.end(); } catch (e) {}
    });

    clientSocket.on('error', () => {
      try { serverSocket.end(); } catch (e) {}
    });
  } catch (err) {
    try { clientSocket.end(); } catch (e) {}
  }
});

proxyServer.on('error', (err) => {
  console.error('Proxy server error:', err.message);
});

process.on('uncaughtException', (err) => {
  console.error('Uncaught exception:', err.message);
});

// ══════════════════════════════════════════════════════════════════════
// STARTUP
// ══════════════════════════════════════════════════════════════════════

const PROXY_PORT = 8888;

proxyServer.listen(PROXY_PORT, () => {
  console.log(`\n🚀 AI Network Scheduler Proxy`);
  console.log(`   Proxy + API:  http://127.0.0.1:${PROXY_PORT}`);
  console.log(`   Stats API:    http://127.0.0.1:${PROXY_PORT}/ai-scheduler/stats`);
  console.log(`   AI Mode: ${state.aiMode ? 'ON' : 'OFF'}`);
  console.log(`   Bandwidth: ${state.bandwidthMbps} Mbps\n`);
});

console.log('\n💡 Set your browser proxy to 127.0.0.1:8888\n');
