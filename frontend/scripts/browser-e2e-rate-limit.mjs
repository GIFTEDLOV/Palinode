/* global process */
import { spawn } from 'node:child_process';
import path from 'node:path';

const child = spawn(process.execPath, [path.join(process.cwd(), 'scripts', 'browser-qa.mjs')], {
  stdio: 'inherit',
  env: { ...process.env, PALINODE_SUITE: 'deterministic', PALINODE_TARGET: 'local', PALINODE_SIMULATE_429: 'once', PALINODE_RATE_LIMIT_ONLY: 'true', PALINODE_SUMMARY_FILE: path.join(process.cwd(), '..', 'artifacts', 'browser-qa', 'rate-limit-summary.json') },
});
child.on('exit', (code, signal) => process.exit(code ?? (signal ? 1 : 0)));
