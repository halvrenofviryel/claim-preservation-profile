from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from cpp_source_capsule.adapters import inspect_ai, promptfoo
from cpp_source_capsule.core import (
    build_capsule,
    canonical_bytes,
    sha256_bytes,
    validate_profile,
    verify_capsule,
)

ROOT = Path(__file__).resolve().parents[1]
PROFILE = json.loads((ROOT / "fixtures/profiles/document-triage.json").read_text())
AGENT_SOURCE_REVISION = "claim-commons-local/synthetic-email-agent-v1"
AGENT_CURRENT_REVISION = "claim-commons-local/synthetic-email-agent-v2"
AGENT_PROFILES = {
    "ignored-stop": "agent-ignored-stop.json",
    "false-send-claim": "agent-false-send.json",
    "missing-effect-observer": "agent-missing-observer.json",
}


def capsule_for(source: Path, source_format: str, *, profile: dict | None = None):
    source_bytes = source.read_bytes()
    adapter = inspect_ai if source_format == "inspect-ai-v2" else promptfoo
    profile = deepcopy(profile or PROFILE)
    selection, measurement, source_binding, mapping_loss = adapter.admit(
        source_bytes,
        profile["selector"],
    )
    capsule = build_capsule(
        profile,
        source_format=source_format,
        source_ref=source.name,
        source_bytes=source_bytes,
        adapter_version=adapter.ADAPTER_VERSION,
        selection=selection,
        measurement=measurement,
        source_binding=source_binding,
        mapping_loss=mapping_loss,
    )
    return capsule, source_bytes


def rehash(capsule: dict) -> None:
    body = {key: deepcopy(value) for key, value in capsule.items() if key != "capsule_id"}
    capsule["capsule_id"] = sha256_bytes(canonical_bytes(body))


class CPPSourceCapsuleTests(unittest.TestCase):
    def test_inspect_complete_has_three_separate_axes(self):
        capsule, source = capsule_for(ROOT / "fixtures/inspect/complete.json", "inspect-ai-v2")
        self.assertEqual(capsule["assessment"]["evidence_finding"], "SUPPORTED")
        self.assertEqual(capsule["assessment"]["applicability"], "CURRENT")
        self.assertEqual(capsule["assessment"]["processing"], "COMPLETED")
        result = verify_capsule(capsule, source_bytes=source, current_subject_revision="model-a")
        self.assertTrue(result["valid"])
        self.assertEqual(result["verification_level"], "SOURCE_DERIVED")
        self.assertEqual(result["current_applicability"], "CURRENT")

    def test_inspect_partial_is_inconclusive(self):
        capsule, _ = capsule_for(ROOT / "fixtures/inspect/partial.json", "inspect-ai-v2")
        self.assertEqual(capsule["assessment"]["evidence_finding"], "INCONCLUSIVE")
        self.assertEqual(capsule["assessment"]["processing"], "COMPLETED")

    def test_promptfoo_measured_has_unknown_source_applicability(self):
        capsule, source = capsule_for(ROOT / "fixtures/promptfoo/measured.jsonl", "promptfoo-jsonl")
        self.assertEqual(capsule["assessment"]["evidence_finding"], "SUPPORTED")
        self.assertEqual(capsule["assessment"]["applicability"], "UNKNOWN")
        result = verify_capsule(capsule, source_bytes=source, current_subject_revision="model-a")
        self.assertTrue(result["valid"])
        self.assertEqual(result["current_applicability"], "UNKNOWN")
        self.assertTrue(result["checks"]["source_mapping_loss"])

    def test_promptfoo_failed_assertion_is_a_complete_measured_result(self):
        capsule, _ = capsule_for(ROOT / "fixtures/promptfoo/measured.jsonl", "promptfoo-jsonl")
        self.assertTrue(capsule["measurement"]["complete"])
        self.assertEqual(capsule["measurement"]["value"], 0.75)
        self.assertEqual(capsule["measurement"]["population"]["passed_rows"], 3)
        self.assertEqual(capsule["measurement"]["population"]["failed_rows"], 1)
        self.assertEqual(capsule["measurement"]["population"]["other_result_rows"], 0)
        self.assertEqual(capsule["measurement"]["population"]["measured_error_text_rows"], 1)
        self.assertEqual(capsule["measurement"]["population"]["processing_error_rows"], 0)
        self.assertEqual(capsule["assessment"]["evidence_finding"], "SUPPORTED")

    def test_promptfoo_ungraded_error_is_processing_error(self):
        source = b'{"error":"Provider failed","gradingResult":null}\n'
        selection, measurement, source_binding, mapping_loss = promptfoo.admit(
            source,
            PROFILE["selector"],
        )
        capsule = build_capsule(
            deepcopy(PROFILE),
            source_format="promptfoo-jsonl",
            source_ref="provider-error.jsonl",
            source_bytes=source,
            adapter_version=promptfoo.ADAPTER_VERSION,
            selection=selection,
            measurement=measurement,
            source_binding=source_binding,
            mapping_loss=mapping_loss,
        )
        self.assertEqual(capsule["assessment"]["evidence_finding"], "NOT_MEASURED")
        self.assertEqual(capsule["assessment"]["processing"], "ERROR")

    def test_promptfoo_mixed_measured_and_processing_error_keeps_axes_separate(self):
        source = (
            b'{"score":1,"gradingResult":{"pass":true}}\n'
            b'{"error":"Provider failed","gradingResult":null}\n'
        )
        selection, measurement, source_binding, mapping_loss = promptfoo.admit(
            source,
            PROFILE["selector"],
        )
        capsule = build_capsule(
            deepcopy(PROFILE),
            source_format="promptfoo-jsonl",
            source_ref="mixed-result-error.jsonl",
            source_bytes=source,
            adapter_version=promptfoo.ADAPTER_VERSION,
            selection=selection,
            measurement=measurement,
            source_binding=source_binding,
            mapping_loss=mapping_loss,
        )
        self.assertEqual(capsule["assessment"]["evidence_finding"], "INCONCLUSIVE")
        self.assertEqual(capsule["assessment"]["processing"], "ERROR")
        self.assertEqual(capsule["measurement"]["population"]["measured_rows"], 1)
        self.assertEqual(capsule["measurement"]["population"]["processing_error_rows"], 1)

    def test_promptfoo_rejects_unsupported_aggregate(self):
        selector = deepcopy(PROFILE["selector"])
        selector["aggregate"] = "median_score"
        with self.assertRaisesRegex(ValueError, "mean_score"):
            promptfoo.admit(b'{"score":1,"gradingResult":{"pass":true}}\n', selector)

    def test_promptfoo_requires_boolean_pass_for_a_measured_row(self):
        _, measurement, _, mapping_loss = promptfoo.admit(
            b'{"score":1,"gradingResult":{"reason":"missing pass"}}\n',
            PROFILE["selector"],
        )
        self.assertEqual(measurement["state"], "NOT_MEASURED")
        self.assertTrue(
            any(
                entry["target_path"] == "measurement.value"
                for entry in mapping_loss["unavailable"]
            )
        )

    def test_profile_rejects_nonfinite_threshold(self):
        profile = deepcopy(PROFILE)
        profile["evaluation_contract"]["criterion"]["threshold"] = float("nan")
        with self.assertRaisesRegex(ValueError, "threshold"):
            validate_profile(profile)

    def test_complete_measurement_below_stricter_threshold_is_refuted(self):
        profile = deepcopy(PROFILE)
        profile["evaluation_contract"]["criterion"]["threshold"] = 0.8
        capsule, _ = capsule_for(
            ROOT / "fixtures/inspect/complete.json",
            "inspect-ai-v2",
            profile=profile,
        )
        self.assertEqual(capsule["assessment"]["evidence_finding"], "REFUTED")

    def test_promptfoo_without_grading_is_not_measured(self):
        capsule, _ = capsule_for(ROOT / "fixtures/promptfoo/unmeasured.jsonl", "promptfoo-jsonl")
        self.assertEqual(capsule["assessment"]["evidence_finding"], "NOT_MEASURED")
        self.assertEqual(capsule["assessment"]["processing"], "COMPLETED")

    def test_unknown_current_revision_is_explicit(self):
        capsule, source = capsule_for(ROOT / "fixtures/inspect/complete.json", "inspect-ai-v2")
        result = verify_capsule(capsule, source_bytes=source)
        self.assertTrue(result["valid"])
        self.assertEqual(result["current_applicability"], "UNKNOWN")
        self.assertEqual(result["recorded_assessment"]["evidence_finding"], "SUPPORTED")

    def test_changed_revision_is_stale_without_masking_evidence_or_processing(self):
        capsule, source = capsule_for(ROOT / "fixtures/inspect/error.json", "inspect-ai-v2")
        result = verify_capsule(capsule, source_bytes=source, current_subject_revision="model-b")
        self.assertTrue(result["valid"])
        self.assertEqual(result["current_applicability"], "STALE")
        self.assertEqual(result["recorded_assessment"]["evidence_finding"], "NOT_MEASURED")
        self.assertEqual(result["recorded_assessment"]["processing"], "ERROR")

    def test_altered_source_is_rejected(self):
        capsule, source = capsule_for(ROOT / "fixtures/inspect/complete.json", "inspect-ai-v2")
        result = verify_capsule(capsule, source_bytes=source + b"\n")
        self.assertFalse(result["valid"])
        self.assertFalse(result["checks"]["source_digest"])

    def test_altered_capsule_without_rehash_is_rejected(self):
        capsule, source = capsule_for(ROOT / "fixtures/inspect/complete.json", "inspect-ai-v2")
        altered = deepcopy(capsule)
        altered["measurement"]["value"] = 0.1
        self.assertFalse(verify_capsule(altered, source_bytes=source)["valid"])

    def test_fabricated_measurement_with_rehash_is_rejected_by_source_rederivation(self):
        capsule, source = capsule_for(ROOT / "fixtures/inspect/complete.json", "inspect-ai-v2")
        forged = deepcopy(capsule)
        forged["measurement"]["value"] = 0.99
        rehash(forged)
        result = verify_capsule(forged, source_bytes=source, current_subject_revision="model-a")
        self.assertFalse(result["valid"])
        self.assertTrue(result["checks"]["capsule_digest"])
        self.assertFalse(result["checks"]["source_measurement"])

    def test_fabricated_binding_with_rehash_is_rejected_by_source_rederivation(self):
        capsule, source = capsule_for(ROOT / "fixtures/inspect/complete.json", "inspect-ai-v2")
        forged = deepcopy(capsule)
        forged["source_binding"]["subject_revision"]["source_path"] = "invented.path"
        rehash(forged)
        result = verify_capsule(forged, source_bytes=source, current_subject_revision="model-a")
        self.assertFalse(result["valid"])
        self.assertFalse(result["checks"]["source_binding"])

    def test_fabricated_mapping_loss_with_rehash_is_rejected_by_source_rederivation(self):
        capsule, source = capsule_for(ROOT / "fixtures/inspect/complete.json", "inspect-ai-v2")
        forged = deepcopy(capsule)
        forged["mapping_loss"]["omitted"] = []
        rehash(forged)
        result = verify_capsule(forged, source_bytes=source, current_subject_revision="model-a")
        self.assertFalse(result["valid"])
        self.assertTrue(result["checks"]["capsule_digest"])
        self.assertFalse(result["checks"]["source_mapping_loss"])

    def test_profile_revision_must_match_observed_inspect_model(self):
        profile = deepcopy(PROFILE)
        profile["subject"]["revision"] = "model-b"
        with self.assertRaisesRegex(ValueError, "source subject revision"):
            capsule_for(ROOT / "fixtures/inspect/complete.json", "inspect-ai-v2", profile=profile)

    def test_unsupported_adapter_version_fails_source_backed_verification(self):
        capsule, source = capsule_for(ROOT / "fixtures/inspect/complete.json", "inspect-ai-v2")
        altered = deepcopy(capsule)
        altered["source"]["adapter_version"] = "unknown"
        rehash(altered)
        result = verify_capsule(altered, source_bytes=source)
        self.assertFalse(result["valid"])
        self.assertFalse(result["checks"]["adapter_supported"])

    def test_inspect_scored_sample_mismatch_is_incomplete(self):
        data = json.loads((ROOT / "fixtures/inspect/complete.json").read_text())
        data["results"]["scores"][0]["scored_samples"] = 3
        source = json.dumps(data).encode()
        selection, measurement, _, _ = inspect_ai.admit(source, PROFILE["selector"])
        self.assertEqual(selection["unit"], "ratio")
        self.assertFalse(measurement["complete"])

    def test_capsule_only_verification_is_labeled_and_does_not_claim_source_check(self):
        capsule, _ = capsule_for(ROOT / "fixtures/inspect/complete.json", "inspect-ai-v2")
        result = verify_capsule(capsule)
        self.assertTrue(result["valid"])
        self.assertEqual(result["verification_level"], "CAPSULE_ONLY")
        self.assertEqual(result["source_bytes"], "NOT_CHECKED")
        self.assertNotIn("source_measurement", result["checks"])

    def test_explicit_source_error_is_not_an_evidence_finding(self):
        capsule, _ = capsule_for(ROOT / "fixtures/inspect/error.json", "inspect-ai-v2")
        self.assertEqual(capsule["assessment"]["evidence_finding"], "NOT_MEASURED")
        self.assertEqual(capsule["assessment"]["processing"], "ERROR")

    def test_complete_measurement_cannot_claim_incomplete_processing(self):
        capsule, source = capsule_for(ROOT / "fixtures/inspect/complete.json", "inspect-ai-v2")
        altered = deepcopy(capsule)
        altered["measurement"]["processing_complete"] = False
        rehash(altered)
        result = verify_capsule(altered, source_bytes=source)
        self.assertFalse(result["valid"])
        self.assertFalse(result["checks"]["structure"])

    def _agent_capsule(self, case_id: str, source_format: str):
        profile = json.loads(
            (ROOT / "fixtures/profiles" / AGENT_PROFILES[case_id]).read_text()
        )
        source_name = "inspect.json" if source_format == "inspect-ai-v2" else "promptfoo.jsonl"
        return capsule_for(
            ROOT / "fixtures/agent-assurance" / source_name,
            source_format,
            profile=profile,
        )

    def test_agent_claim_inspect_preserves_three_findings(self):
        expected = {
            "ignored-stop": "REFUTED",
            "false-send-claim": "REFUTED",
            "missing-effect-observer": "NOT_MEASURED",
        }
        for case_id, finding in expected.items():
            with self.subTest(case_id=case_id):
                capsule, source = self._agent_capsule(case_id, "inspect-ai-v2")
                self.assertEqual(capsule["assessment"]["evidence_finding"], finding)
                self.assertEqual(capsule["assessment"]["applicability"], "CURRENT")
                self.assertTrue(verify_capsule(capsule, source_bytes=source)["valid"])

    def test_agent_claim_promptfoo_preserves_three_findings(self):
        expected = {
            "ignored-stop": "REFUTED",
            "false-send-claim": "REFUTED",
            "missing-effect-observer": "NOT_MEASURED",
        }
        for case_id, finding in expected.items():
            with self.subTest(case_id=case_id):
                capsule, source = self._agent_capsule(case_id, "promptfoo-jsonl")
                self.assertEqual(capsule["assessment"]["evidence_finding"], finding)
                self.assertEqual(capsule["assessment"]["applicability"], "CURRENT")
                self.assertTrue(verify_capsule(capsule, source_bytes=source)["valid"])

    def test_missing_observer_keeps_evidence_and_processing_axes_separate(self):
        inspect_capsule, _ = self._agent_capsule(
            "missing-effect-observer", "inspect-ai-v2"
        )
        promptfoo_capsule, _ = self._agent_capsule(
            "missing-effect-observer", "promptfoo-jsonl"
        )
        self.assertEqual(inspect_capsule["assessment"]["evidence_finding"], "NOT_MEASURED")
        self.assertEqual(inspect_capsule["assessment"]["processing"], "COMPLETED")
        self.assertEqual(promptfoo_capsule["assessment"]["evidence_finding"], "NOT_MEASURED")
        self.assertEqual(promptfoo_capsule["assessment"]["processing"], "ERROR")

    def test_promptfoo_agent_claim_uses_structured_fields_not_error_phrase(self):
        source = (
            b'{"error":"arbitrary framework error","gradingResult":{"pass":false,"score":0},'
            b'"response":{"metadata":{"subjectRevision":"claim-commons-local/'
            b'synthetic-email-agent-v1","caseId":"missing-effect-observer",'
            b'"effectObserverAvailable":false,"outboxBefore":null,"outboxAfter":null}},'
            b'"score":0,"success":false}\n'
        )
        profile = json.loads(
            (ROOT / "fixtures/profiles/agent-missing-observer.json").read_text()
        )
        selection, measurement, source_binding, mapping_loss = promptfoo.admit(
            source,
            profile["selector"],
        )
        capsule = build_capsule(
            profile,
            source_format="promptfoo-jsonl",
            source_ref="structured.jsonl",
            source_bytes=source,
            adapter_version=promptfoo.ADAPTER_VERSION,
            selection=selection,
            measurement=measurement,
            source_binding=source_binding,
            mapping_loss=mapping_loss,
        )
        self.assertEqual(capsule["assessment"]["evidence_finding"], "NOT_MEASURED")
        self.assertEqual(capsule["assessment"]["processing"], "ERROR")

    def test_agent_claim_revision_change_is_stale_without_erasing_finding(self):
        capsule, source = self._agent_capsule("ignored-stop", "promptfoo-jsonl")
        result = verify_capsule(
            capsule,
            source_bytes=source,
            current_subject_revision=AGENT_CURRENT_REVISION,
        )
        self.assertTrue(result["valid"])
        self.assertEqual(result["recorded_assessment"]["evidence_finding"], "REFUTED")
        self.assertEqual(result["current_applicability"], "STALE")

    def test_agent_claim_source_revision_is_bound_in_both_formats(self):
        for source_format in ("inspect-ai-v2", "promptfoo-jsonl"):
            with self.subTest(source_format=source_format):
                capsule, _ = self._agent_capsule("false-send-claim", source_format)
                binding = capsule["source_binding"]["subject_revision"]
                self.assertTrue(binding["observed"])
                self.assertEqual(binding["value"], AGENT_SOURCE_REVISION)

    def test_agent_claim_duplicate_case_is_rejected(self):
        row = (
            b'{"response":{"metadata":{"subjectRevision":"claim-commons-local/'
            b'synthetic-email-agent-v1","caseId":"false-send-claim",'
            b'"effectObserverAvailable":true,"outboxBefore":0,"outboxAfter":0}}}\n'
        )
        profile = json.loads(
            (ROOT / "fixtures/profiles/agent-false-send.json").read_text()
        )
        with self.assertRaisesRegex(ValueError, "more than one"):
            promptfoo.admit(row + row, profile["selector"])

    def test_agent_claim_absent_case_is_not_measured(self):
        profile = json.loads(
            (ROOT / "fixtures/profiles/agent-false-send.json").read_text()
        )
        selector = deepcopy(profile["selector"])
        selector["case_id"] = "not-present"
        selection, measurement, binding, mapping_loss = inspect_ai.admit(
            (ROOT / "fixtures/agent-assurance/inspect.json").read_bytes(),
            selector,
        )
        self.assertEqual(measurement["state"], "NOT_MEASURED")
        self.assertTrue(measurement["processing_complete"])
        self.assertTrue(binding["subject_revision"]["observed"])
        self.assertTrue(
            any(
                item["reason"] == "SELECTED_AGENT_CASE_IS_ABSENT"
                for item in mapping_loss["unavailable"]
            )
        )


if __name__ == "__main__":
    unittest.main()
