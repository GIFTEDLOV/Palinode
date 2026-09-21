export default function handler(_req, res) {
  const body = `{"fixture":"PALINODE reviewer mutable evidence","record":"mutable-v4","subject":"fixture-reviewer-mutable-001","version":"B","statement":"The controlled condition was NOT satisfied."}`;
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  res.setHeader('Vercel-CDN-Cache-Control', 'no-store');
  res.status(200).send(body);
}
