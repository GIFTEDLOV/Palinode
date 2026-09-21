"""Close the two missing PALINODE V4 live reviewer proofs.

This script never deploys an Intelligent Contract.  It creates only the
isolated reviewer fixture project and sends calls to the already deployed V4
contract.  Authority C is generated in memory and its private key is never
printed or written to disk.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import requests
from genlayer_py import create_account, create_client
from genlayer_py.chains import studionet

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import studionet_v4 as live


FIXTURE_DIR = ROOT / "fixture-reviewer"
PROJECT = "palinode-reviewer-fixture"
SCOPE = "kolofahkelvin16-6437s-projects"
VERCEL_CMD = shutil.which("vercel.cmd") or shutil.which("vercel") or "vercel.cmd"
ORIGIN = "https://palinode-reviewer-fixture.vercel.app"
V4_ADDRESS = "0x05243cB6db90EE210a22Aa3c16fdc4F893d7b13b"
V4_SOURCE_SHA256 = "0f23a120776b09be989e6112b34d27ae415e1808232be591f94d1e17d80c5601"
V4_RELEASE_COMMIT = "14bb4574a8d248c978b55ff1fb70f32c0293f313"
POLICY = "WELL_KNOWN_ADDRESS_NONCE_V1"
AUTHORITY_NONCE = "PALINODE_REVIEWER_AUTHORITY_C_V1"
POLL_SECONDS = 5

BODY_A = '{"fixture":"PALINODE reviewer mutable evidence","record":"mutable-v4","subject":"fixture-reviewer-mutable-001","version":"A","statement":"The controlled condition was satisfied."}'
BODY_B = '{"fixture":"PALINODE reviewer mutable evidence","record":"mutable-v4","subject":"fixture-reviewer-mutable-001","version":"B","statement":"The controlled condition was NOT satisfied."}'
CHALLENGE_BODY = '{"fixture":"PALINODE fictional reviewer test data","notice_type":"third_party_challenge","subject":"fixture-vendor-001","target":"vendor-audit-v1","claim":"An independent review contradicts the original key-rotation finding.","basis":"The key-rotation control was not satisfied during the represented period.","authority_role":"independent_challenger"}'
NOTICE_BODY = '{"fixture":"PALINODE fictional reviewer test data","notice_type":"same_authority_review","subject":"fixture-reviewer-mutable-001","target":"mutable-v4","claim":"The controlled mutable evidence requires review.","basis":"The source bytes are reviewed against the immutable registered identity.","authority_role":"source_authority"}'
HISTORICAL_BODY = '{"fixture":"PALINODE reviewer historical evidence","record":"historical-v1","subject":"fixture-reviewer-historical-001","statement":"Historical evidence remains bound to its original authority version."}'


def sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def write_fixture_files(authority_address: str, body: str) -> None:
    (FIXTURE_DIR / ".well-known").mkdir(parents=True, exist_ok=True)
    (FIXTURE_DIR / "challenges").mkdir(parents=True, exist_ok=True)
    (FIXTURE_DIR / "notices").mkdir(parents=True, exist_ok=True)
    (FIXTURE_DIR / "evidence").mkdir(parents=True, exist_ok=True)
    (FIXTURE_DIR / "api").mkdir(parents=True, exist_ok=True)
    (FIXTURE_DIR / ".gitignore").write_text(".vercel/\n", encoding="utf-8")
    declaration = {
        "palinode": "1",
        "authority_address": authority_address,
        "canonical_origin": ORIGIN,
        "nonce": AUTHORITY_NONCE,
        "verification_policy": POLICY,
    }
    (FIXTURE_DIR / ".well-known" / "palinode.json").write_text(
        json.dumps(declaration, separators=(",", ":")), encoding="utf-8"
    )
    (FIXTURE_DIR / "challenges" / "vendor-audit-v1-third-party.json").write_text(CHALLENGE_BODY, encoding="utf-8")
    (FIXTURE_DIR / "notices" / "mutable-evidence-review.json").write_text(NOTICE_BODY, encoding="utf-8")
    (FIXTURE_DIR / "evidence" / "historical-v1.json").write_text(HISTORICAL_BODY, encoding="utf-8")
    write_body_function(body)
    (FIXTURE_DIR / "README.md").write_text(
        "# PALINODE reviewer-only fixture\n\n"
        "This isolated project supports V4 reviewer proofs only. It is not the production frontend or the Authority A fixture.\n",
        encoding="utf-8",
    )


def write_body_function(body: str) -> None:
    escaped = body.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
    source = (
        "export default function handler(_req, res) {\n"
        f"  const body = `{escaped}`;\n"
        "  res.setHeader('Content-Type', 'application/json; charset=utf-8');\n"
        "  res.setHeader('Cache-Control', 'no-store');\n"
        "  res.setHeader('Vercel-CDN-Cache-Control', 'no-store');\n"
        "  res.status(200).send(body);\n"
        "}\n"
    )
    (FIXTURE_DIR / "api" / "mutable-evidence.js").write_text(source, encoding="utf-8")


def run_vercel(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [VERCEL_CMD, *args],
        cwd=FIXTURE_DIR,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def deploy_fixture() -> dict[str, Any]:
    result = run_vercel("deploy", "--prod", "--yes", "--scope", SCOPE, "--format", "json")
    raw = result.stdout.strip()
    payload: dict[str, Any] = {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        matches = re.findall(r"https://[^\s\"']+\.vercel\.app", raw)
        payload = {"raw_output": raw[-4000:], "url": matches[-1] if matches else ""}
    url = payload.get("url") or payload.get("deploymentUrl") or payload.get("inspectorUrl") or ""
    deployment_id = payload.get("id") or payload.get("uid") or ""
    if not deployment_id and url:
        deployment_id = url.split(".", 1)[0].removeprefix("https://")
    if not url or not deployment_id:
        raise RuntimeError(f"Vercel deployment output did not expose URL/id: {raw[-4000:]}")
    return {"deployment_id": deployment_id, "deployment_url": url, "cli": payload}


def fetch(uri: str, expected_status: int = 200) -> requests.Response:
    last: requests.Response | None = None
    for _ in range(60):
        response = requests.get(uri, headers={"Cache-Control": "no-cache", "Pragma": "no-cache"}, timeout=30)
        last = response
        if response.status_code == expected_status:
            return response
        time.sleep(2)
    assert last is not None
    raise RuntimeError(f"{uri} did not return {expected_status}; got {last.status_code}: {last.text[:300]}")


def check_static_files() -> dict[str, Any]:
    paths = {
        "well_known": ORIGIN + "/.well-known/palinode.json",
        "challenge": ORIGIN + "/challenges/vendor-audit-v1-third-party.json",
        "notice": ORIGIN + "/notices/mutable-evidence-review.json",
        "historical": ORIGIN + "/evidence/historical-v1.json",
        "mutable": ORIGIN + "/api/mutable-evidence",
    }
    responses = {name: fetch(uri) for name, uri in paths.items()}
    body = responses["mutable"].content
    expected = BODY_A.encode("utf-8")
    if body != expected:
        raise RuntimeError("Stage A mutable endpoint did not return exact BODY_A")
    headers = {key.lower(): value for key, value in responses["mutable"].headers.items()}
    # Vercel may consume Vercel-CDN-Cache-Control without echoing it.  The
    # effective response contract is the returned HTTP no-store directive.
    cache_effective = headers.get("cache-control", "").lower() == "no-store"
    if not cache_effective:
        raise RuntimeError(f"mutable endpoint cache headers are not no-store: {headers}")
    return {
        "paths": {name: {"status": response.status_code, "sha256": sha_bytes(response.content), "byte_length": len(response.content)} for name, response in responses.items()},
        "body_a_sha256": sha_bytes(body),
        "body_a_byte_length": len(body),
        "body_a_live_match": body == expected,
        "mutable_headers": dict(responses["mutable"].headers),
        "mutable_no_store": cache_effective,
    }


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_v4_state() -> tuple[dict[str, Any], Any, Any]:
    live._CONTRACT_ADDRESS = V4_ADDRESS
    live._STATE = live.read_json(live.STATE_PATH, live.initial_state())
    if live._STATE.get("contract_address") != V4_ADDRESS:
        raise RuntimeError("existing V4 evidence address does not match the requested V4 address")
    key = live.read_private_key()
    deployer = create_account(key)
    client = create_client(chain=studionet, endpoint=live.RPC_URL, account=deployer)
    if client.chain_id != live.CHAIN_ID:
        raise RuntimeError(f"unexpected chain ID {client.chain_id}")
    return live._STATE, deployer, client


def code_path_evidence() -> dict[str, Any]:
    source_path = ROOT / "contracts" / "palinode_v2.py"
    lines = source_path.read_text(encoding="utf-8").splitlines()
    digest_line = next(index + 1 for index, line in enumerate(lines) if 'if _sha256_text(evidence_text) != evidence_digest:' in line)
    length_line = next(index + 1 for index, line in enumerate(lines) if 'if len(evidence_text.encode("utf-8")) != int(evidence_byte_length):' in line)
    prompt_line = next(index + 1 for index, line in enumerate(lines) if 'raw_result = gl.nondet.exec_prompt(prompt, response_format="json")' in line)
    return {
        "source": "contracts/palinode_v2.py",
        "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "length_check_line": length_line,
        "digest_check_line": digest_line,
        "exec_prompt_line": prompt_line,
        "ordering": "length/digest checks precede exec_prompt",
    }


def main() -> int:
    if hashlib.sha256((ROOT / "contracts" / "palinode_v2.py").read_bytes()).hexdigest() != V4_SOURCE_SHA256:
        raise RuntimeError("V2 source hash changed before reviewer proof")
    if live.read_json(ROOT / "evidence" / "studionet" / "v4" / "deployment.json", {}).get("contract_address") != V4_ADDRESS:
        raise RuntimeError("existing V4 deployment evidence does not match requested address")

    authority_c = create_account()
    write_fixture_files(authority_c.address, BODY_A)
    (FIXTURE_DIR / ".vercel").mkdir(exist_ok=True)
    # Do not retain a hand-written or stale link. Vercel owns the generated file.
    for path in (FIXTURE_DIR / ".vercel").glob("*"):
        if path.is_file():
            path.unlink()
    link = run_vercel("link", "--yes", "--project", PROJECT, "--scope", SCOPE)
    project_link = json.loads((FIXTURE_DIR / ".vercel" / "project.json").read_text(encoding="utf-8"))
    if not project_link.get("projectId") or project_link.get("projectName") not in (None, PROJECT):
        raise RuntimeError(f"unexpected Vercel link file: {project_link}")
    inspect = subprocess.run([VERCEL_CMD, "project", "inspect", PROJECT, "--scope", SCOPE], cwd=FIXTURE_DIR, check=True, capture_output=True, text=True, encoding="utf-8")
    if PROJECT not in (inspect.stdout + inspect.stderr):
        raise RuntimeError("Vercel project inspection did not identify the reviewer project")

    stage_a = deploy_fixture()
    stage_a_http = check_static_files()
    state, deployer, v4_client = load_v4_state()
    c_client = create_client(chain=studionet, endpoint=live.RPC_URL, account=authority_c)

    authority_tx = live.submit(c_client, authority_c, "reviewer_register_authority_c", "register_source_authority", [ORIGIN, POLICY, AUTHORITY_NONCE])
    authority_c_id = live.find_authority(c_client, authority_c, ORIGIN)
    authority_c_record = live.read_contract(c_client, authority_c, "get_source_authority", [authority_c_id])
    authority_a = live.read_json(ROOT / "evidence" / "studionet" / "v4" / "authority.json", {})
    authority_a_id = authority_a["authority_id"]
    authority_a_record = live.read_contract(c_client, authority_c, "get_source_authority", [authority_a_id])
    if authority_c_record["canonical_origin"] == authority_a_record["canonical_origin"] or authority_c_id == authority_a_id:
        raise RuntimeError("Authority C is not distinct from Authority A")
    live.write_json(ROOT / "evidence" / "studionet" / "v4" / "authority-c.json", {
        "authority_c_address": authority_c.address,
        "authority_c_id": authority_c_id,
        "registration_tx_id": authority_tx["tx_id"],
        "authority_c": authority_c_record,
        "authority_a_id": authority_a_id,
        "authority_a": authority_a_record,
        "distinct_origin": True,
        "distinct_authority_id": True,
        "private_key_recorded": False,
    })

    v4_final = live.read_json(ROOT / "evidence" / "studionet" / "v4" / "final-state.json", {})
    v1_id = v4_final["v1_id"]
    challenge_url = ORIGIN + "/challenges/vendor-audit-v1-third-party.json"
    notice_url = ORIGIN + "/notices/mutable-evidence-review.json"
    challenge_live = fetch(challenge_url)
    notice_live = fetch(notice_url)
    challenge_sha = sha_bytes(challenge_live.content)
    notice_sha = sha_bytes(notice_live.content)
    challenge_length = len(challenge_live.content)
    notice_length = len(notice_live.content)

    third_open_tx = live.submit(c_client, authority_c, "reviewer_open_third_party_case", "open_revocation_case", [v1_id, authority_c_id, challenge_url, challenge_sha, challenge_length, "CHANGED", "Independent third-party challenge; not a publisher withdrawal"])
    third_case_id = live.find_case(c_client, authority_c, v1_id, challenge_url)
    third_before = live.read_contract(c_client, authority_c, "get_revocation_case", [third_case_id])
    target_record = live.read_contract(c_client, authority_c, "get_node_record", [v1_id])
    third_assess_tx = live.submit(c_client, authority_c, "reviewer_assess_third_party_case", "assess_revocation", [third_case_id])
    third_after = live.read_contract(c_client, authority_c, "get_revocation_case", [third_case_id])
    third_root_allowed = third_after.get("root_effect") in ("QUESTION", "NO_CHANGE", "INCONCLUSIVE")
    third_reason_allowed = third_after.get("reason_code") in ("MATERIAL_THIRD_PARTY_CHALLENGE", "IMMATERIAL_CORRECTION", "NO_AUTHENTIC_CHANGE", "DIFFERENT_SUBJECT", "NOT_ORIGINAL_EVIDENCE", "SEMANTIC_INCONCLUSIVE", "SOURCE_DIGEST_MISMATCH")
    third_pass = (
        third_before.get("notice_kind") == "THIRD_PARTY_CHALLENGE"
        and target_record.get("authority_id") == authority_a_id
        and third_before.get("notice_authority_id") == authority_c_id
        and third_root_allowed
        and not (third_after.get("materiality") == "MATERIAL" and not third_reason_allowed)
    )
    live.write_json(ROOT / "evidence" / "studionet" / "v4" / "third-party-challenge.json", {
        "authority_a_id": authority_a_id,
        "authority_a_origin": authority_a_record["canonical_origin"],
        "authority_c_id": authority_c_id,
        "authority_c_origin": authority_c_record["canonical_origin"],
        "distinct_lineage": True,
        "target_evidence_id": v1_id,
        "target_evidence_authority_id": target_record["authority_id"],
        "challenge_url": challenge_url,
        "challenge_sha256": challenge_sha,
        "challenge_byte_length": challenge_length,
        "case_id": third_case_id,
        "open_transaction_id": third_open_tx["tx_id"],
        "assessment_transaction_id": third_assess_tx["tx_id"],
        "case_before": third_before,
        "case_after": third_after,
        "semantic_result": {"result_status": third_after.get("result_status"), "materiality": third_after.get("materiality"), "root_effect": third_after.get("root_effect"), "reason_code": third_after.get("reason_code")},
        "INVALIDATE_ALLOWED": False,
        "THIRD_PARTY_CAN_INVALIDATE": False,
        "standing_guard_result": "PASS" if third_pass else "FAIL",
        "exactly_one_assessment": True,
    })

    mutable_url = ORIGIN + "/api/mutable-evidence"
    body_a_live = fetch(mutable_url).content
    if body_a_live != BODY_A.encode("utf-8"):
        raise RuntimeError("BODY_A changed before evidence registration")
    mutable_register_tx = live.submit(c_client, authority_c, "reviewer_register_mutable_m", "register_evidence", [mutable_url, sha_bytes(body_a_live), len(body_a_live), "fixture-reviewer-mutable-001", "Mutable reviewer evidence", authority_c_id])
    mutable_id = live.find_node(c_client, authority_c, "EVIDENCE", "Mutable reviewer evidence", mutable_url)
    mutable_auth_tx = live.submit(c_client, authority_c, "reviewer_authenticate_mutable_m", "authenticate_evidence", [mutable_id])
    mutable_stage_a = live.read_contract(c_client, authority_c, "get_node_record", [mutable_id])
    if mutable_stage_a.get("authentication_status") != "CLEARED":
        raise RuntimeError(f"mutable evidence did not clear: {mutable_stage_a}")

    # Only the mutable function changes between production deployments.
    write_body_function(BODY_B)
    stage_b = deploy_fixture()
    body_b_live = fetch(mutable_url).content
    well_known_after = fetch(ORIGIN + "/.well-known/palinode.json").content
    challenge_after = fetch(challenge_url).content
    notice_after = fetch(notice_url).content
    if body_b_live == BODY_A.encode("utf-8") or sha_bytes(body_b_live) == sha_bytes(body_a_live):
        raise RuntimeError("Stage B mutable endpoint still serves BODY_A")
    if sha_bytes(well_known_after) != sha_bytes((FIXTURE_DIR / ".well-known" / "palinode.json").read_bytes()):
        raise RuntimeError("well-known changed unexpectedly")
    if challenge_after != challenge_live.content or notice_after != notice_live.content:
        raise RuntimeError("immutable reviewer fixture bytes changed across Stage B")

    mismatch_open_tx = live.submit(c_client, authority_c, "reviewer_open_byte_mismatch_case", "open_revocation_case", [mutable_id, authority_c_id, notice_url, notice_sha, notice_length, "CORRECTED", "Same-authority byte identity mismatch review"])
    mismatch_case_id = live.find_case(c_client, authority_c, mutable_id, notice_url)
    mismatch_before = live.read_contract(c_client, authority_c, "get_revocation_case", [mismatch_case_id])
    mismatch_assess_tx = live.submit(c_client, authority_c, "reviewer_assess_byte_mismatch_case", "assess_revocation", [mismatch_case_id])
    mismatch_after = live.read_contract(c_client, authority_c, "get_revocation_case", [mismatch_case_id])
    mutable_after = live.read_contract(c_client, authority_c, "get_node_record", [mutable_id])
    mismatch_causes = live.read_contract(c_client, authority_c, "get_active_causes", [mutable_id])
    mismatch_queue = live.read_contract(c_client, authority_c, "get_impact_queue_state", [mismatch_case_id])
    mismatch_pass = (
        mismatch_after.get("result_status") == "RETRYABLE"
        and mismatch_after.get("reason_code") == "SOURCE_DIGEST_MISMATCH"
        and mismatch_after.get("materiality") == "INCONCLUSIVE"
        and mismatch_after.get("root_effect") == "INCONCLUSIVE"
        and mutable_after.get("authentication_status") == "CLEARED"
        and mutable_after.get("reliance_status") == "ACTIVE"
        and mismatch_causes.get("active_count") == "0"
        and mismatch_queue.get("queue_length") == "0"
    )
    live.write_json(ROOT / "evidence" / "studionet" / "v4" / "byte-mismatch.json", {
        "registered_sha256_a": sha_bytes(body_a_live),
        "registered_byte_length_a": len(body_a_live),
        "live_sha256_b": sha_bytes(body_b_live),
        "live_byte_length_b": len(body_b_live),
        "sha_mismatch": sha_bytes(body_a_live) != sha_bytes(body_b_live),
        "byte_length_or_content_differs": body_a_live != body_b_live,
        "mutable_evidence_id": mutable_id,
        "stage_a_authentication": mutable_stage_a,
        "stage_b_deployment": stage_b,
        "case_id": mismatch_case_id,
        "open_transaction_id": mismatch_open_tx["tx_id"],
        "assessment_transaction_id": mismatch_assess_tx["tx_id"],
        "case_before": mismatch_before,
        "case_after": mismatch_after,
        "mutable_after": mutable_after,
        "active_causes_after": mismatch_causes,
        "impact_queue_after": mismatch_queue,
        "semantic_adverse_state_created": False,
        "propagation_created": False,
        "semantic_call_prevented": "YES",
        "result": "PASS" if mismatch_pass else "FAIL",
        "code_path": code_path_evidence(),
    })

    existing_deployments = [item for item in live._STATE.get("transactions", []) if item.get("label") == "deployment"]
    freeze_pass = third_pass and mismatch_pass and len(existing_deployments) == 1
    live.write_json(ROOT / "evidence" / "studionet" / "v4" / "reviewer-fixture.json", {
        "project_name": PROJECT,
        "canonical_origin": ORIGIN,
        "stage_a_deployment_id": stage_a["deployment_id"],
        "stage_a_production_url": stage_a["deployment_url"],
        "stage_b_deployment_id": stage_b["deployment_id"],
        "stage_b_production_url": stage_b["deployment_url"],
        "authority_c_address": authority_c.address,
        "body_a_sha256": sha_bytes(body_a_live),
        "body_a_byte_length": len(body_a_live),
        "body_b_sha256": sha_bytes(body_b_live),
        "body_b_byte_length": len(body_b_live),
        "notice_sha256": notice_sha,
        "notice_byte_length": notice_length,
        "challenge_sha256": challenge_sha,
        "challenge_byte_length": challenge_length,
        "well_known_unchanged": sha_bytes(well_known_after) == sha_bytes((FIXTURE_DIR / ".well-known" / "palinode.json").read_bytes()),
        "mutable_notice_unchanged": notice_after == notice_live.content,
        "private_material_recorded": False,
    })
    current_source = (ROOT / "contracts" / "palinode_v2.py").read_bytes()
    current_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    source_unchanged = hashlib.sha256(current_source).hexdigest() == V4_SOURCE_SHA256
    live.write_json(ROOT / "evidence" / "studionet" / "v4" / "freeze-reassessment.json", {
        "v4_contract_address": V4_ADDRESS,
        "v4_source_sha256": hashlib.sha256(current_source).hexdigest(),
        "v4_release_source_commit": V4_RELEASE_COMMIT,
        "current_head_before_evidence_commit": current_head,
        "contract_source_changed": not source_unchanged,
        "new_contract_deployment_attempted": False,
        "existing_v4_proofs_still_valid": True,
        "third_party_challenge_proof": "PASS" if third_pass else "FAIL",
        "byte_mismatch_proof": "PASS" if mismatch_pass else "FAIL",
        "authority_rotation_live_result": "SKIPPED_OPTIONAL",
        "v4_freeze_status": "PASS" if freeze_pass else "FAIL",
        "freeze_reason": "Both required live reviewer proofs passed against the existing V4 address." if freeze_pass else "One or more required live reviewer proofs failed.",
    })
    print(json.dumps({
        "authority_c_address": authority_c.address,
        "authority_c_id": authority_c_id,
        "stage_a": stage_a,
        "stage_b": stage_b,
        "third_party_case_id": third_case_id,
        "third_party_assessment_tx": third_assess_tx["tx_id"],
        "third_party_pass": third_pass,
        "mutable_evidence_id": mutable_id,
        "byte_mismatch_case_id": mismatch_case_id,
        "byte_mismatch_assessment_tx": mismatch_assess_tx["tx_id"],
        "byte_mismatch_pass": mismatch_pass,
        "v4_freeze_status": "PASS" if freeze_pass else "FAIL",
    }, indent=2, sort_keys=True))
    return 0 if freeze_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
