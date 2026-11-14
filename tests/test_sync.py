import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import sync_karabiner as sk  # noqa: E402

HYPER = {
    "description": "Change caps_lock to command+control+option+shift.",
    "manipulators": [{
        "type": "basic",
        "from": {"key_code": "caps_lock", "modifiers": {"optional": ["any"]}},
        "to": [{"key_code": "left_shift", "modifiers": ["left_command", "left_control", "left_option"]}],
    }],
}
OTHER = {"description": "Some app preset", "manipulators": [{"type": "basic", "from": {"key_code": "f13"}, "to": [{"key_code": "f14"}]}]}
LEGACY_HJIO = "Semicolon VIM layer — hjio arrows with native modifier propagation"


def config(rules):
    return {"profiles": [{"name": "Default profile", "selected": True, "complex_modifications": {"rules": rules}}]}


class SyncTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.target = Path(self.tmp.name) / "karabiner.json"
        self.owned = sk.load_owned_rules()
        self.ids = {r.id: r for r in self.owned}

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = sk.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def write(self, rules):
        self.target.write_text(json.dumps(config(rules)), encoding="utf-8")

    def rules(self):
        return json.loads(self.target.read_text())["profiles"][0]["complex_modifications"]["rules"]

    def test_shift_caps_goes_before_app_hyper_and_foreign_rules_untouched(self):
        self.write([HYPER, OTHER])
        code, _, _ = self.run_cli("sync", "--target", str(self.target))
        self.assertEqual(code, 0)
        rules = self.rules()
        names = [r["description"] for r in rules]
        shift_caps = self.ids["shift-caps-lock-ctrl-opt-cmd"].description
        self.assertLess(names.index(shift_caps), names.index(HYPER["description"]))
        self.assertIn(HYPER, rules)
        self.assertIn(OTHER, rules)
        self.assertEqual(names[-1], self.ids["hjio-vim-layer"].description)

    def test_legacy_hjio_is_migrated_in_place_and_toggle_kept(self):
        legacy = json.loads(json.dumps(self.ids["hjio-vim-layer"].rule))
        legacy["description"] = LEGACY_HJIO
        legacy["enabled"] = False
        self.write([HYPER, legacy, OTHER])
        self.run_cli("sync", "--target", str(self.target))
        rules = self.rules()
        names = [r["description"] for r in rules]
        self.assertNotIn(LEGACY_HJIO, names)
        hjio = rules[names.index(self.ids["hjio-vim-layer"].description)]
        self.assertIs(hjio["enabled"], False)
        self.assertEqual(names.index(hjio["description"]), 2)  # after shift-caps + hyper, before OTHER

    def test_sync_is_idempotent_and_backs_up(self):
        self.write([HYPER])
        self.run_cli("sync", "--target", str(self.target))
        first = self.target.read_text()
        self.run_cli("sync", "--target", str(self.target))
        self.assertEqual(first, self.target.read_text())
        self.assertEqual(len(list(Path(self.tmp.name).glob("karabiner.json.bak.*"))), 2)

    def test_dry_run_does_not_write(self):
        self.write([HYPER])
        before = self.target.read_text()
        code, out, _ = self.run_cli("sync", "--dry-run", "--target", str(self.target))
        self.assertEqual(code, 0)
        self.assertIn("Dry run", out)
        self.assertEqual(before, self.target.read_text())

    def test_remove_only_removes_owned(self):
        self.write([HYPER, OTHER])
        self.run_cli("sync", "--target", str(self.target))
        self.run_cli("remove", "--target", str(self.target))
        self.assertEqual(self.rules(), [HYPER, OTHER])

    def test_duplicates_are_refused(self):
        rule = self.ids["hjio-vim-layer"].rule
        self.write([rule, rule])
        code, _, err = self.run_cli("sync", "--target", str(self.target))
        self.assertEqual(code, 1)
        self.assertIn("copies", err)

    def test_warns_when_foreign_rule_takes_semicolon_first(self):
        semicolon = {"description": "foreign semicolon", "manipulators": [{"type": "basic", "from": {"key_code": "semicolon"}, "to": [{"key_code": "a"}]}]}
        self.write([semicolon])
        _, _, err = self.run_cli("sync", "--target", str(self.target))
        self.assertIn("foreign semicolon", err)
        self.assertEqual(self.rules()[0], semicolon)  # never reordered for append rules

    def test_dist_is_current(self):
        code, _, err = self.run_cli("build", "--check")
        self.assertEqual(code, 0, err)


if __name__ == "__main__":
    unittest.main()
