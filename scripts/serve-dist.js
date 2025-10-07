// Minimal static file server with SPA fallback (no deps)
const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 5173;
const ROOT = path.resolve(process.env.DIST_DIR || 'apps/web/dist');
const API_PROXY = process.env.API_PROXY || 'https://api.concordbroker.com';

const mime = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.map': 'application/json; charset=utf-8',
};

function send(res, code, data, headers = {}) {
  res.writeHead(code, Object.assign({ 'Cache-Control': 'no-store' }, headers));
  res.end(data);
}

function serveFile(res, filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const type = mime[ext] || 'application/octet-stream';
  fs.readFile(filePath, (err, data) => {
    if (err) {
      send(res, 404, 'Not Found');
    } else {
      send(res, 200, data, { 'Content-Type': type });
    }
  });
}

const server = http.createServer((req, res) => {
  try {
    const [pathname, qs = ''] = (req.url || '/').split('?');
    const urlPath = decodeURIComponent(pathname);

    // Proxy API requests to target
    if (urlPath.startsWith('/api/')) {
      const targetUrl = new URL(API_PROXY);
      targetUrl.pathname = urlPath;
      targetUrl.search = qs ? `?${qs}` : '';

      const isHttps = targetUrl.protocol === 'https:';
      const client = isHttps ? https : http;

      const proxyReq = client.request(
        targetUrl,
        {
          method: req.method,
          headers: {
            ...req.headers,
            host: targetUrl.host,
          },
        },
        (proxyRes) => {
          res.writeHead(proxyRes.statusCode || 500, proxyRes.headers);
          proxyRes.pipe(res);
        }
      );
      proxyReq.on('error', () => send(res, 502, 'Bad Gateway'));
      if (req.method !== 'GET' && req.method !== 'HEAD') {
        req.pipe(proxyReq);
      } else {
        proxyReq.end();
      }
      return;
    }
    let filePath = path.join(ROOT, urlPath);

    // Prevent path traversal
    if (!filePath.startsWith(ROOT)) {
      return send(res, 403, 'Forbidden');
    }

    // If requesting a directory, serve index.html
    fs.stat(filePath, (err, stat) => {
      if (!err && stat.isDirectory()) {
        filePath = path.join(filePath, 'index.html');
      }

      fs.stat(filePath, (err2) => {
        if (!err2) {
          return serveFile(res, filePath);
        }
        // SPA fallback: serve root index.html
        const fallback = path.join(ROOT, 'index.html');
        fs.readFile(fallback, (e, data) => {
          if (e) return send(res, 404, 'Not Found');
          send(res, 200, data, { 'Content-Type': 'text/html; charset=utf-8' });
        });
      });
    });
  } catch (e) {
    send(res, 500, 'Server Error');
  }
});

server.listen(PORT, () => {
  console.log(`Serving ${ROOT} on http://localhost:${PORT}`);
});
