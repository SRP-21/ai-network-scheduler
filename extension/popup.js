var BASE_URL  = 'http://localhost:8888/ai-scheduler';
var MODE_URL  = BASE_URL + '/mode';
var BW_URL    = BASE_URL + '/bandwidth';
var STATS_URL = BASE_URL + '/stats';
var REG_URL   = BASE_URL + '/register-tab';

function num(v) { return (typeof v === 'number' && !isNaN(v)) ? v : 0; }

document.addEventListener('DOMContentLoaded', function() {
  var toggle     = document.getElementById('ai-toggle');
  var statusText = document.getElementById('ai-status-text');
  var bwSlider   = document.getElementById('bw-slider');
  var bwValue    = document.getElementById('bw-value');
  var canvas     = document.getElementById('bar-chart');
  var ctx        = canvas.getContext('2d');

  // ── AI Toggle ─────────────────────────────────────────────────────
  toggle.addEventListener('change', function() {
    var isOn = toggle.checked;
    statusText.innerText = isOn ? 'ON' : 'OFF';
    statusText.style.color = isOn ? '#00C853' : '#D50000';
    fetch(MODE_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ aiMode: isOn })
    }).catch(function() {});
  });

  // ── Bandwidth Slider ──────────────────────────────────────────────
  bwSlider.addEventListener('input', function() {
    var val = parseInt(bwSlider.value, 10);
    bwValue.innerText = val + ' Mbps';
    fetch(BW_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mbps: val })
    }).catch(function() {});
  });

  // ── Tab Role Buttons ──────────────────────────────────────────────
  document.getElementById('btn-set-without').addEventListener('click', function() {
    chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
      if (!tabs[0]) return;
      var tabId = tabs[0].id;
      // Register via background.js (which can reach the proxy)
      chrome.runtime.sendMessage({ type: 'REGISTER_TAB', tabId: tabId, role: 'without_ai' });
      document.getElementById('btn-set-without').innerText = '✅ TAB ' + tabId + ' = WITHOUT AI';
      document.getElementById('btn-set-without').disabled = true;
    });
  });

  document.getElementById('btn-set-with').addEventListener('click', function() {
    chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
      if (!tabs[0]) return;
      var tabId = tabs[0].id;
      chrome.runtime.sendMessage({ type: 'REGISTER_TAB', tabId: tabId, role: 'with_ai' });
      document.getElementById('btn-set-with').innerText = '✅ TAB ' + tabId + ' = WITH AI';
      document.getElementById('btn-set-with').disabled = true;
    });
  });

  // ── Bar Chart ─────────────────────────────────────────────────────
  function drawChart(woBuf, woStall, woQ, waBuf, waStall, waQ) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    var labels = ['Buffer', 'Stalls', 'Q-Score'];
    function qScore(q) {
      var n = parseInt(q) || 0;
      if (n >= 1080) return 100; if (n >= 720) return 80;
      if (n >= 480) return 60; if (n >= 360) return 40;
      if (n >= 240) return 20; if (n >= 144) return 10;
      return 5;
    }
    var woData = [Math.min(30, woBuf)/30*100, Math.min(10, woStall)/10*100, qScore(woQ)];
    var waData = [Math.min(30, waBuf)/30*100, Math.min(10, waStall)/10*100, qScore(waQ)];
    var barW = 20, spacing = 60, startX = 30;
    for (var i = 0; i < labels.length; i++) {
      ctx.fillStyle = '#D50000';
      var woH = (woData[i]/100)*90;
      ctx.fillRect(startX + i*spacing, 100-woH, barW/2, woH);
      ctx.fillStyle = '#00C853';
      var waH = (waData[i]/100)*90;
      ctx.fillRect(startX + i*spacing + barW/2, 100-waH, barW/2, waH);
      ctx.fillStyle = '#333'; ctx.font = '9px system-ui';
      ctx.fillText(labels[i], startX + i*spacing - 5, 115);
    }
  }

  // ── Update UI ─────────────────────────────────────────────────────
  function updateUI(stats) {
    toggle.checked = !!stats.aiMode;
    statusText.innerText = stats.aiMode ? 'ON' : 'OFF';
    statusText.style.color = stats.aiMode ? '#00C853' : '#D50000';
    bwSlider.value = num(stats.bandwidthMbps) || 10;
    bwValue.innerText = (num(stats.bandwidthMbps) || 10) + ' Mbps';
    document.getElementById('status-mode').innerText = stats.aiMode ? 'AI ON' : 'AI OFF';
    document.getElementById('status-mode').style.color = stats.aiMode ? '#00C853' : '#D50000';
    document.getElementById('status-intercepted').innerText = num(stats.intercepted);
    document.getElementById('status-freed').innerText = num(stats.bandwidthFreedMB).toFixed(1) + ' MB';

    var bh = stats.bufferHealth || {};
    var qu = stats.quality || {};
    var sc = stats.stallCount || {};
    var woBuf = num(bh.withoutAI), woQual = qu.withoutAI || '--', woStall = num(sc.withoutAI);
    var waBuf = num(bh.withAI), waQual = qu.withAI || '--', waStall = num(sc.withAI);

    document.getElementById('wo-buffer').innerText = woBuf.toFixed(1) + 's';
    document.getElementById('wo-buffer-bar').style.width = Math.min(100, woBuf/30*100) + '%';
    document.getElementById('wo-quality').innerText = woQual;
    document.getElementById('wo-stalls').innerText = woStall;
    document.getElementById('wa-buffer').innerText = waBuf.toFixed(1) + 's';
    document.getElementById('wa-buffer-bar').style.width = Math.min(100, waBuf/30*100) + '%';
    document.getElementById('wa-quality').innerText = waQual;
    document.getElementById('wa-stalls').innerText = waStall;

    drawChart(woBuf, woStall, woQual, waBuf, waStall, waQual);

    var pf = document.getElementById('packet-flow');
    var lr = stats.lastRequests || [];
    if (lr.length > 0) {
      var h = '';
      for (var i = 0; i < lr.length; i++) {
        var r = lr[i];
        var c = r.delay > 0 ? '#f57c00' : '#1976d2';
        h += '<div style="font-size:10px;margin-bottom:2px;"><span style="color:'+c+'">['+r.type+']</span> '+r.url+' → '+Math.round(r.delay)+'ms '+r.action+'</div>';
      }
      pf.innerHTML = h;
    }

    var rbt = stats.requestsByType || {};
    document.getElementById('qs-video').innerText = num(rbt.VIDEO_CHUNK);
    document.getElementById('qs-ads').innerText = num(rbt.AD_REQUEST);
    document.getElementById('qs-analytics').innerText = num(rbt.ANALYTICS);
    document.getElementById('qs-thumbnails').innerText = num(rbt.THUMBNAIL);
    document.getElementById('qs-saved').innerText = num(stats.bandwidthFreedMB).toFixed(1) + ' MB';
    document.getElementById('qs-avg-delay').innerText = num(stats.avgDelayMs) + 'ms';

    var ml = document.getElementById('ml-output');
    var log = stats.mlLog || [];
    if (log.length > 0) {
      var m = '<div style="display:flex;font-weight:bold;font-size:9px;border-bottom:1px solid #eee;margin-bottom:4px;"><div style="width:40%">TYPE</div><div style="width:20%">PRI</div><div style="width:40%">ACTION</div></div>';
      for (var j = 0; j < log.length; j++) {
        var l = log[j];
        var ac = (l.action && l.action.indexOf('DELAY') !== -1) ? '#D50000' : '#00C853';
        m += '<div style="display:flex;font-size:10px;margin-bottom:2px;"><div style="width:40%;color:#555;">'+l.type+'</div><div style="width:20%;color:#1976d2;">'+l.priority+'</div><div style="width:40%;color:'+ac+'">'+l.action+'</div></div>';
      }
      ml.innerHTML = m;
    }
  }

  // ── Polling loop via XHR ──────────────────────────────────────────
  var iv = setInterval(function() {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', STATS_URL, true);
    xhr.timeout = 2000;
    xhr.onload = function() {
      var p = document.getElementById('status-proxy');
      if (xhr.status === 200) {
        try { var s = JSON.parse(xhr.responseText); p.innerText = '🟢 ONLINE'; p.style.color = '#00C853'; updateUI(s); }
        catch(e) { p.innerText = '🔴 Parse error'; p.style.color = '#D50000'; }
      } else { p.innerText = '🔴 OFFLINE'; p.style.color = '#D50000'; }
    };
    xhr.onerror = function() { var p = document.getElementById('status-proxy'); p.innerText = '🔴 Run: node proxy.js'; p.style.color = '#D50000'; };
    xhr.ontimeout = xhr.onerror;
    xhr.send();
  }, 500);

  window.addEventListener('unload', function() { clearInterval(iv); });
});
