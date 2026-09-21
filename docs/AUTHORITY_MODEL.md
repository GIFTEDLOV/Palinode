# Source authority model

## Stable identity and versions

`authority_id` is a stable contract-generated identity. Its current record has
an explicit lifecycle: `ACTIVE` or `REVOKED`. Each version records the
controller address, canonical HTTPS origin, verification policy, nonce, status,
and creation sequence. Evidence stores the exact authority version used at
registration; later rotation never rewrites that binding.

The v1 verification policy is `WELL_KNOWN_ADDRESS_NONCE_V1`. Registration and
rotation retrieve the canonical origin's `/.well-known/palinode.json` inside a
GenLayer nondeterministic block and require the exact Palinode version,
authority ID, version, controller address, canonical origin, nonce, and policy.
The caller supplies the origin and nonce for an initial registration, but the
live document must bind them to the registering address. A caller-selected
label is never authority proof.

## Rotation and revocation

`rotate_source_authority(authority_id, challenge_nonce)` is permissionless and
uses the canonical origin's declaration to prove the new controller. It creates
a new version, marks the prior version `SUPERSEDED`, and updates the stable
authority's current version. The previous controller cannot create or
impersonate the new version after rotation. Authority versions are stored
without a permanent lifetime count cap and exposed through bounded pages.

`revoke_source_authority(authority_id)` is restricted to the current version's
controller. Revocation lowers trust: new evidence and new authority-bound
cases fail, and authentication of old evidence cannot return `CLEARED`. It
does not erase or rewrite historical evidence and does not silently rewrite
its stored authority version or reliance status. Explicit adverse cases and
future recovery governance determine current reliance consequences.

## Trust boundary

The domain declaration is consensus input, not a cryptographic signature
invented by the application. The contract does not assume DNS, TLS, a browser,
or an unsupported signing primitive is available inside GenVM. The current
implementation rejects credentials, non-HTTPS schemes, fragments, malformed
paths, and obvious loopback/private host forms. A controlled public HTTPS
fixture is required for live end-to-end proof.
