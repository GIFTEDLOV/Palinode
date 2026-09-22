/* global process */
import { spawn } from 'node:child_process';
import path from 'node:path';

const child = spawn(process.execPath, [path.join(process.cwd(), 'scripts', 'browser-qa.mjs')], {
  stdio: 'inherit',
  env: { ...process.env, PALINODE_SUITE: 'deterministic', PALINODE_TARGET: 'local', PALINODE_SUMMARY_FILE: path.join(process.cwd(), '..', 'artifacts', 'browser-qa', 'deterministic-summary.json') },
});
child.on('exit', (code, signal) => process.exit(code ?? (signal ? 1 : 0)));
