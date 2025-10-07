#!/usr/bin/env node
// Fetch Railway public service URL for a project using Railway API
// Usage:
//   RAILWAY_TOKEN=xxxxx node scripts/get-railway-url.cjs 05f5fbf4-f31c-4bdb-9022-3e987dd80fdb > RAILWAY_PUBLIC_URL.txt

const https = require('https');

const token = process.env.RAILWAY_TOKEN || process.env.RAILWAY_API;
const projectId = process.argv[2];
if (!token || !projectId) {
  console.error('Usage: RAILWAY_TOKEN=<token> node scripts/get-railway-url.cjs <projectId>');
  process.exit(2);
}

const query = `
  query Project($id: String!) {
    project(id: $id) {
      id
      name
      services {
        id
        name
        domains { name }
        deployments(last: 5) {
          edges { node { id url status } }
        }
      }
    }
  }
`;

function request(body) {
  return new Promise((resolve, reject) => {
    const req = https.request(
      {
        hostname: 'backboard.railway.app',
        path: '/graphql/v2',
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      },
      (res) => {
        let data = '';
        res.on('data', (d) => (data += d));
        res.on('end', () => {
          try {
            const json = JSON.parse(data);
            resolve(json);
          } catch (e) {
            reject(e);
          }
        });
      }
    );
    req.on('error', reject);
    req.write(JSON.stringify(body));
    req.end();
  });
}

(async () => {
  try {
    const resp = await request({ query, variables: { id: projectId } });
    if (resp.errors) {
      console.error('Railway API error:', resp.errors[0]?.message || 'unknown error');
      process.exit(1);
    }
    const services = resp?.data?.project?.services || [];
    // Prefer custom domain, else *.railway.app, else latest deployment url
    for (const s of services) {
      const domains = s.domains || [];
      // Any non-internal domain
      const custom = domains.find((d) => d.name && !d.name.endsWith('.internal'));
      if (custom) {
        console.log((custom.name.startsWith('http') ? '' : 'https://') + custom.name);
        return;
      }
      // *.railway.app
      const rail = domains.find((d) => d.name && d.name.includes('.railway.app'));
      if (rail) {
        console.log((rail.name.startsWith('http') ? '' : 'https://') + rail.name);
        return;
      }
      // Fallback: latest deployment URL
      const edges = s.deployments?.edges || [];
      const urls = edges.map((e) => e.node?.url).filter(Boolean);
      if (urls.length) {
        console.log(urls[0]);
        return;
      }
    }
    console.error('No public Railway URL found for project');
    process.exit(1);
  } catch (e) {
    console.error('Request failed:', e.message);
    process.exit(1);
  }
})();

