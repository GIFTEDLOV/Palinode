const UPSTREAM = 'https://studio.genlayer.com/api';

export default async function handler(request, response) {
  const cors = {
    'access-control-allow-origin': '*',
    'access-control-allow-methods': 'POST, OPTIONS',
    'access-control-allow-headers': 'content-type',
    'cache-control': 'no-store',
  };
  Object.entries(cors).forEach(([key, value]) => response.setHeader(key, value));
  if (request.method === 'OPTIONS') { response.statusCode = 204; return response.end(); }
  if (request.method !== 'POST') { response.statusCode = 405; return response.end('POST only'); }
  const chunks = [];
  for await (const chunk of request) chunks.push(chunk);
  const upstream = await fetch(UPSTREAM, { method: 'POST', headers: { 'content-type': 'application/json' }, body: Buffer.concat(chunks) });
  response.statusCode = upstream.status;
  response.setHeader('content-type', upstream.headers.get('content-type') || 'application/json');
  response.end(Buffer.from(await upstream.arrayBuffer()));
}
