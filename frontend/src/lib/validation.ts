import { NODE_TYPES, RELATIONSHIPS } from '../config';

export function required(value: string, label: string) { return value.trim() ? null : `${label} is required.`; }
export function hexDigest(value: string) { return /^[0-9a-f]{64}$/i.test(value.trim()) ? null : 'SHA-256 must be exactly 64 hexadecimal characters.'; }
export function positiveInteger(value: string, label: string, max?: number) {
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed <= 0) return `${label} must be a positive integer.`;
  if (max !== undefined && parsed > max) return `${label} must be at most ${max}.`;
  return null;
}
export function httpsUrl(value: string, label: string) {
  try { const url = new URL(value); return url.protocol === 'https:' ? null : `${label} must use HTTPS.`; } catch { return `${label} must be a valid HTTPS URL.`; }
}
export function nodeId(value: string, label = 'Node ID') { return /^[0-9a-f]{64}$/i.test(value.trim()) ? null : `${label} must be a 64-character hexadecimal ID.`; }
export function authorityId(value: string) { return nodeId(value, 'Authority ID'); }
export function caseId(value: string) { return nodeId(value, 'Case ID'); }
export function supportedNodeType(value: string) { return (NODE_TYPES as readonly string[]).includes(value) ? null : 'Unsupported node type.'; }
export function supportedRelationship(value: string) { return (RELATIONSHIPS as readonly string[]).includes(value) ? null : 'Unsupported relationship.'; }
export function firstError(...errors: Array<string | null | undefined>) { return errors.find(Boolean) || null; }
