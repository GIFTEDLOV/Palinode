import { createReadStream } from 'node:fs';
import { stat } from 'node:fs/promises';
import http from 'node:http';
import path from 'node:path';

const root = path.resolve(process.cwd(), 'dist');
const port = Number(process.env.PALINODE_LOCAL_PORT || 4175);
const upstreamRpc = process.env.PALINODE_UPSTREAM_RPC || 'https://studio.genlayer.com/api';
const contentTypes = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.ico': 'image/x-icon' };
function send(res, status, body, type = 'text/plain; charset=utf-8') { res.writeHead(status, { 'content-type': type }); res.end(body); }
async function proxyRpc(req, res) {
  const chunks = []; for await (const chunk of req) chunks.push(chunk);
  const upstream = await fetch(upstreamRpc, { method: 'POST', headers: { 'content-type': 'application/json' }, body: Buffer.concat(chunks) });
  res.writeHead(upstream.status, { 'content-type': upstream.headers.get('content-type') || 'application/json', 'access-control-allow-origin': '*' });
  res.end(Buffer.from(await upstream.arrayBuffer()));
}
const server = http.createServer(async (req, res) => {
  try {
    if (req.url === '/api/rpc' && req.method === 'POST') return await proxyRpc(req, res);
    if (req.url === '/api/rpc' && req.method === 'OPTIONS') return send(res, 204, '');
    const requested = decodeURIComponent((req.url || '/').split('?')[0]);
    const candidate = path.resolve(root, `.${requested === '/' ? '/index.html' : requested}`);
    const safe = candidate.startsWith(root) ? candidate : path.join(root, 'index.html');
    const target = await stat(safe).then((value) => value.isFile() ? safe : path.join(root, 'index.html')).catch(() => path.join(root, 'index.html'));
    const extension = path.extname(target);
    res.writeHead(200, { 'content-type': contentTypes[extension] || 'application/octet-stream' });
    createReadStream(target).pipe(res);
  } catch (error) { send(res, 502, error instanceof Error ? error.message : 'Local relay failure'); }
});
server.listen(port, '127.0.0.1', () => console.log(`PALINODE local production server: http://127.0.0.1:${port}`));
