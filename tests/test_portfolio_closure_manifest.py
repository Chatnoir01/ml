"""Synthetic tamper tests for the closure registry, no scientific execution."""
from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT/"scripts"/"validate_research_portfolio_closure.py"
MANIFEST = ROOT/"research"/"RESEARCH_PORTFOLIO_CLOSURE_MANIFEST_20261102.json"
spec = spec_from_file_location("validate_research_portfolio_closure", SCRIPT)
assert spec is not None and spec.loader is not None
audit = module_from_spec(spec)
spec.loader.exec_module(audit)


class PortfolioRegistryValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def fixture(self):
        return deepcopy(self.source)

    def assert_rejected(self, doc, needle):
        with self.assertRaises(audit.RegistryInvalid) as context:
            audit.validate_manifest(doc)
        self.assertIn(needle, str(context.exception))

    def track(self, doc, name):
        return next(x for x in doc["workstreams"] if x["id"]==name)

    def test_actual_snapshot_is_complete_and_guarded(self):
        result = audit.validate_manifest(self.fixture())
        self.assertEqual(result["open_prs_accounted_for"], 38)
        self.assertEqual(result["workstreams"], 15)
        self.assertEqual(result["priorities"], {"P0":3,"P1":7,"P2":5})
        self.assertEqual(result["neural_2u_confirmation"], "NOT_YET_PRODUCED")

    def test_missing_legacy_draft_is_rejected(self):
        d=self.fixture()
        row=self.track(d, "phase1_sbox_search")
        row["prs"].remove(25)
        row["pr_links"].remove("https://github.com/Chatnoir01/ml/pull/25")
        self.assert_rejected(d,"records missing")

    def test_duplicate_pr_across_tracks_is_rejected(self):
        d=self.fixture()
        self.track(d,"phase2u_prospective")["prs"].append(25)
        self.track(d,"phase2u_prospective")["pr_links"].append(
            "https://github.com/Chatnoir01/ml/pull/25")
        self.assert_rejected(d,"records missing")  # 39 allocations, not 38

    def test_wrong_pr_link_rejected(self):
        d=self.fixture()
        self.track(d,"phase2s_mechanisms")["pr_links"] = [
            "https://github.com/elsewhere/private/pull/156"
        ]
        self.assert_rejected(d,"PR links changed")

    def test_cannot_authorize_merging(self):
        d=self.fixture()
        d["review_rules"]["no_merge_from_registry"] = False
        self.assert_rejected(d,"cannot authorize merges")

    def test_cannot_silently_erase_negative_result(self):
        d=self.fixture()
        d["review_rules"]["frozen_negative_is_a_result"] = False
        self.assert_rejected(d,"erase negative")

    def test_cannot_label_phase2u_neural_confirmed(self):
        d=self.fixture()
        self.track(d,"phase2u_prospective")["stage"]="demonstrator_scope_complete"
        self.assert_rejected(d,"Phase 2U promoted")

    def test_cannot_mislabel_blocked_phase2t_as_success(self):
        d=self.fixture()
        self.track(d,"phase2t_original_blocked")["stage"]="demonstrator_scope_complete"
        self.assert_rejected(d,"original v1 failure")

    def test_cannot_hide_secure_core_failing_ci(self):
        d=self.fixture()
        self.track(d,"secure_core")["stage"]="prototype_ci_green_security_open"
        self.assert_rejected(d,"Secure Core CI failures")

    def test_cannot_hide_neural_reproducibility_problem(self):
        d=self.fixture()
        self.track(d,"phase2_adaptive_repro")["stage"]="frozen_result_pr_disposition_open"
        self.assert_rejected(d,"GA/NN reproducibility")

    def test_rejects_self_dependency(self):
        d=self.fixture()
        self.track(d,"phase2s_mechanisms")["depends_on"].append("phase2s_mechanisms")
        self.assert_rejected(d,"self dependency")

    def test_rejects_cross_track_cycle(self):
        d=self.fixture()
        self.track(d,"phase2_replication")["depends_on"].append("phase2u_prospective")
        self.assert_rejected(d,"dependency cycle")

    def test_rejects_unknown_dependency(self):
        d=self.fixture()
        self.track(d,"raven_continuity")["depends_on"].append("not-an-actual-project")
        self.assert_rejected(d,"unknown workstream")

    def test_missing_exit_conditions_never_auto_closes(self):
        d=self.fixture()
        self.track(d,"tpm_security_attack")["exit"] = []
        self.assert_rejected(d,"missing exit")

    def test_missing_evidence_never_counts_as_completed(self):
        d=self.fixture()
        self.track(d,"fhe_bfv")["evidence"] = []
        self.assert_rejected(d,"missing evidence")

    def test_status_glossary_must_stay_complete(self):
        d=self.fixture()
        d["status_vocabulary"].pop("ci_failed_security_gate")
        self.assert_rejected(d,"status glossary")

    def test_priority_cannot_be_silently_reweighted(self):
        d=self.fixture()
        self.track(d,"secure_core")["priority"] = "P2"
        self.assert_rejected(d,"priority partition")

    def test_snapshot_requires_same_frozen_38(self):
        d=self.fixture()
        d["sorted_open_prs"].remove(158)
        self.assert_rejected(d,"sorted PR snapshot")


if __name__=="__main__":
    unittest.main()
