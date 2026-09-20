const MATERIALITY = ['MATERIAL', 'IMMATERIAL', 'INCONCLUSIVE'] as const;
const ROOT_EFFECT = ['INVALIDATE', 'QUESTION', 'NO_CHANGE', 'INCONCLUSIVE'] as const;
const RESULT_STATUS = ['CONCLUSIVE', 'RETRYABLE', 'INCONCLUSIVE'] as const;
const REQUIRED_KEYS = ['result_status', 'change_authentic', 'same_subject', 'original_evidence_affected', 'materiality', 'root_effect', 'reason_code'];

export type SemanticResult = {
  result_status: string;
  change_authentic: boolean;
  same_subject: boolean;
  original_evidence_affected: boolean;
  materiality: (typeof MATERIALITY)[number];
  root_effect: (typeof ROOT_EFFECT)[number];
  reason_code: string;
};

export function isSemanticResult(value: unknown): value is SemanticResult {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
  const record = value as Record<string, unknown>;
  const keys = Object.keys(record);
  return keys.length === REQUIRED_KEYS.length && keys.every((key) => REQUIRED_KEYS.includes(key))
    && typeof record.result_status === 'string' && (RESULT_STATUS as readonly string[]).includes(record.result_status)
    && typeof record.change_authentic === 'boolean'
    && typeof record.same_subject === 'boolean'
    && typeof record.original_evidence_affected === 'boolean'
    && typeof record.materiality === 'string' && (MATERIALITY as readonly string[]).includes(record.materiality)
    && typeof record.root_effect === 'string' && (ROOT_EFFECT as readonly string[]).includes(record.root_effect)
    && typeof record.reason_code === 'string' && record.reason_code.length > 0;
}

export function safeSemanticResult(value: unknown) {
  return isSemanticResult(value) ? value : null;
}
