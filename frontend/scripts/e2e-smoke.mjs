/* global console, fetch, process, URL */
const baseUrl = process.env.PALINODE_BASE_URL || 'http://127.0.0.1:4173';
const routes = ['/', '/app', '/app/graph', '/app/evidence', '/app/evidence/successor', '/app/decisions', '/app/revocations', '/app/recoveries', '/app/authorities', '/app/activity', '/app/proof', '/app/integrate', '/docs'];
const results = [];

for (const route of routes) {
  const response = await fetch(new URL(route, baseUrl));
  if (!response.ok) throw new Error(`${route}: HTTP ${response.status}`);
  const body = await response.text();
  if (!body.includes('<div id="root"></div>')) throw new Error(`${route}: application shell missing`);
  results.push({ route, status: response.status });
}

console.log(JSON.stringify({ baseUrl, routes: results, result: 'PASS' }, null, 2));
