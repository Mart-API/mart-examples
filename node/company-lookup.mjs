import { pathToFileURL } from 'node:url';

export async function companyLookup(url) {
  const key = process.env.MART_API_KEY?.trim();
  if (!key) throw new Error('Set MART_API_KEY before making a request.');
  let parsed;
  try { parsed = new URL(url); } catch { throw new Error('Provide a public LinkedIn company URL.'); }
  if (parsed.protocol !== 'https:' || !['linkedin.com', 'www.linkedin.com'].includes(parsed.hostname)
      || !/^\/company\/[^/]+/.test(parsed.pathname) || parsed.username || parsed.password || parsed.port) {
    throw new Error('Use a public https://www.linkedin.com/company/... URL.');
  }
  const params = new URLSearchParams({ type: 'company', url });
  const response = await fetch(`https://api.mart.dev/v1/linkedin?${params}`, {
    headers: { 'x-api-key': key, Accept: 'application/json' },
    signal: AbortSignal.timeout(30_000),
    redirect: 'error',
  });
  if (!response.ok) {
    const delay = response.headers.get('Retry-After');
    throw new Error(`Mart returned HTTP ${response.status}.${delay ? ` Retry-After: ${delay}.` : ''}`);
  }
  return response.json();
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    console.log(JSON.stringify(await companyLookup(process.argv[2]), null, 2));
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
