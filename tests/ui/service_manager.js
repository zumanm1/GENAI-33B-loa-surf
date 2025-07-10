/* Mocha root hooks to ensure the application services are running before UI tests.
   Automatically starts them via start_services.sh if needed and tears them down when done. */

const { execSync, spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const BACKEND = 'http://127.0.0.1:5050';
const FRONTEND = 'http://127.0.0.1:5051';
const AI = 'http://127.0.0.1:5052';

async function isUp(url) {
  try {
    const res = await fetch(url, { method: 'GET', mode: 'cors', cache: 'no-store' });
    return res.status === 200;
  } catch (_) {
    return false;
  }
}

async function waitAllHealthy(timeoutMs = 30000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    if (await isUp(`${BACKEND}/api/health`) && (await fetch(FRONTEND)).status === 200 && (await isUp(`${AI}/health`))) {
      return true;
    }
    await new Promise(r => setTimeout(r, 1000));
  }
  return false;
}

let spawnedPids = [];

exports.mochaHooks = {
  async beforeAll() {
    this.timeout(60000);
    // Quick health check
    const healthy = await waitAllHealthy(10000);
    if (healthy) {
      console.log('Services already healthy – reusing.');
      return;
    }

    console.log('Starting services via start_services.sh…');
    const scriptPath = path.join(__dirname, '..', '..', 'start_services.sh');
    try {
      const out = execSync(scriptPath, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'inherit'] });
      console.log(out);
      const m = out.match(/kill\s+([0-9\s]+)/);
      if (m) spawnedPids = m[1].trim().split(/\s+/);
    } catch (e) {
      console.error('Failed to run start_services.sh', e);
      throw e;
    }

    if (!(await waitAllHealthy())) {
      throw new Error('Services failed to become healthy in time');
    }
  },

  async afterAll() {
    if (spawnedPids.length) {
      console.log('Killing spawned services: ', spawnedPids.join(' '));
      try {
        execSync(`kill -9 ${spawnedPids.join(' ')}`);
      } catch (e) {
        console.warn('Error killing pids', e.message);
      }
    }
  }
};
