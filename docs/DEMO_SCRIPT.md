# PALINODE 2–3 minute demo script

## Goal

Show that PALINODE does not merely store provenance. It determines whether
changed evidence matters, traces the typed blast radius, and recovers through a
new immutable successor without rewriting history.

## Before starting

Open:

- Live app: https://palinode-app.vercel.app
- Proof page: `/app/proof`
- Studionet contract: `0x9c9d1993cd938846D1163Bba9AA81AC6d165de88`

Use the existing canonical records. Do not submit writes during the demo.

## Run of show

### 1. Landing — 15 seconds

Say: “Decisions inherit weaknesses from the evidence beneath them. PALINODE
tracks what changes and what must be reconsidered.” Point to the visual chain:
Evidence → Claim → Decision, then to the withdrawal and recovery path.

### 2. Global graph — 15 seconds

Open `/app/graph`. Identify the Evidence, Claim, and Decision nodes. Point out
that edges are typed and that graph state is read from the frozen contract, not
from a presentation database.

### 3. Evidence V1 — 20 seconds

Open the V1 evidence record. Show:

- Source authentication: `CLEARED`.
- Current reliance: `ACTIVE` before impact, then the recorded adverse state.
- Authority version, canonical URI, digest, byte length, history, and lineage.

Say: “Authentication answers whether the committed source identity was
retrieved and matched. It does not promise that reliance can never change.”

### 4. Revocation command center — 25 seconds

Open the recorded revocation case. Show the immutable notice identity and the
structured consensus result:

`CONCLUSIVE` / `MATERIAL` / `INVALIDATE` / `MATERIAL_WITHDRAWAL`.

Emphasize: “Opening a case did not invalidate the evidence. Consensus answered
the bounded materiality question first.”

### 5. Blast radius — 20 seconds

Open the blast-radius view or focused graph. Show the actual typed effects:

- Claim → `QUESTIONED`.
- Decision → `QUARANTINED`.

Explain that typed propagation is not blanket descendant invalidation.

### 6. Evidence V2 and recovery — 25 seconds

Open the successor evidence and recovery command center. Show V2 as
independently `CLEARED`, the explicit V1 → V2 lineage, and the recovery result:

`CONCLUSIVE` / `SUPERSEDE` / `RECOVERY_RESOLVED_SUPERSEDE`.

### 7. Historical guarantee — 15 seconds

Return to V1. Point out:

- V1 still exists.
- The original revocation case still exists.
- Authentication remains `CLEARED`.
- Current reliance is `SUPERSEDED`.

Say: “PALINODE resolves a current cause without pretending the earlier record
never existed.”

### 8. Proof & Security — 20 seconds

Open `/app/proof`. Show Studionet, chain `61999`, the frozen contract address,
source SHA-256, freeze commit, recorded test gates, active-cause composition,
bounded propagation, and finality-safe transaction model.

Close with: “The contract is frozen; the frontend is a derived read and write
surface over the canonical Studionet state.”
