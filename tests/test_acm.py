"""acm tests. They run in a fake home folder and never touch real accounts or ~/.acm.

    python3 -m unittest discover -s tests
"""
import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACM = os.path.join(ROOT, "bin", "acm")
STATUSLINE = os.path.join(ROOT, "bin", "acm-statusline")
SEOUL = ZoneInfo("Asia/Seoul")

ULTRA_TEXT = """You are currently using your subscription to power your Claude Code usage

Current week (all models): 3% used · resets Nov 8 at 12:59am (Asia/Seoul)
Current week (Fable): 0% used · resets Nov 8 at 1am (Asia/Seoul)

What's contributing to your usage?
Approximate · sessions on this machine only · shares overlap
"""

LIMITED_TEXT = """You are currently using your subscription to power your Claude Code usage

Current session: 42% used · resets Nov 2 at 3:59pm (Asia/Seoul)
Current week (all models): 61% used · resets Jan 5, 2027 at 9am (Asia/Seoul)
Current week (Sonnet only): 10% used
"""


def seoul(*args):
    return datetime(*args, tzinfo=SEOUL).timestamp()


class AcmCase(unittest.TestCase):
    """Reload acm with a fake HOME and ACM_HOME."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="acm-test-")
        self.home = os.path.join(self.tmp, "home")
        os.makedirs(os.path.join(self.home, ".claude"))
        self.env_backup = dict(os.environ)
        os.environ["HOME"] = self.home
        os.environ["ACM_HOME"] = os.path.join(self.home, ".acm")
        for key in ("ANTHROPIC_MODEL", "ACM_POLL_INTERVAL", "ACM_USAGE_BAND"):
            os.environ.pop(key, None)
        loader = importlib.machinery.SourceFileLoader("acm_under_test", ACM)
        spec = importlib.util.spec_from_loader("acm_under_test", loader)
        self.acm = importlib.util.module_from_spec(spec)
        loader.exec_module(self.acm)
        os.makedirs(self.acm.USAGE_DIR)
        os.makedirs(self.acm.POLL_DIR)
        self.sessions = []
        self.acm.running_sessions = lambda data, with_cwd=True: self.sessions
        self.acm.registered_pids = lambda name: set()
        self.acm.claude_pids = lambda: []
        self.cwd = os.getcwd()
        os.chdir(self.home)

    def tearDown(self):
        os.chdir(self.cwd)
        os.environ.clear()
        os.environ.update(self.env_backup)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def login(self, name, email):
        """Put the account in a signed-in state."""
        if name == "cl1":
            path = os.path.join(self.home, ".claude.json")
        else:
            d = os.path.join(self.home, f".claude-{name}")
            os.makedirs(d, exist_ok=True)
            path = os.path.join(d, ".claude.json")
        with open(path, "w") as f:
            json.dump({"oauthAccount": {"emailAddress": email}}, f)

    def accounts(self, names, publisher=None):
        data = {"mode": "usage", "order": list(names), "last": None,
                "accounts": {n: {"dir": None if n == "cl1" else os.path.join(self.home, f".claude-{n}")} for n in names}}
        if publisher:
            data["publisher"] = {"enabled": True, "account": publisher}
        for n in names:
            self.login(n, f"{n}@example.com")
        self.acm.save_json(self.acm.ACCOUNTS_FILE, data)
        self.acm.remember_emails(data)
        return data

    def statusline(self, name, **windows):
        rec = {"account": name, "updated_at": int(time.time())}
        rec.update(windows)
        self.acm.save_json(os.path.join(self.acm.USAGE_DIR, f"{name}.json"), rec)

    def polled(self, name, at=None, scoped=(), **windows):
        at = int(at or time.time())
        usage = {"updated_at": at, "scoped": [dict(s, at=at) for s in scoped]}
        usage.update({k: dict(v, at=at) for k, v in windows.items()})
        self.acm.save_json(os.path.join(self.acm.POLL_DIR, f"{name}.json"), {"usage": usage, "next_at": time.time() + 999})


class ParseUsageText(AcmCase):
    def test_ultra_account(self):
        now = seoul(2026, 11, 2, 12, 0)
        got = self.acm.parse_usage_text(ULTRA_TEXT, now)
        self.assertNotIn("five_hour", got)
        self.assertEqual(got["seven_day"], {"used_percentage": 3.0, "resets_at": seoul(2026, 11, 8, 0, 59)})
        self.assertEqual(got["scoped"], [{"used_percentage": 0.0, "resets_at": seoul(2026, 11, 8, 1, 0), "name": "Fable"}])

    def test_limited_account_with_year_and_no_reset(self):
        now = seoul(2026, 11, 2, 12, 0)
        got = self.acm.parse_usage_text(LIMITED_TEXT, now)
        self.assertEqual(got["five_hour"], {"used_percentage": 42.0, "resets_at": seoul(2026, 11, 2, 15, 59)})
        self.assertEqual(got["seven_day"]["resets_at"], seoul(2027, 1, 5, 9, 0))
        self.assertEqual(got["scoped"], [{"used_percentage": 10.0, "resets_at": None, "name": "Sonnet only"}])

    def test_other_reset_shapes(self):
        now = seoul(2026, 11, 2, 12, 0)
        self.assertEqual(self.acm.parse_reset("Nov 8, 7:59am (Asia/Seoul)", now), seoul(2026, 11, 8, 7, 59))
        self.assertEqual(self.acm.parse_reset("Nov 8 at 7:59\u202fAM (Asia/Seoul)", now), seoul(2026, 11, 8, 7, 59))
        # With only a time, it is today, or tomorrow if that time has passed
        self.assertEqual(self.acm.parse_reset("3:59pm (Asia/Seoul)", now), seoul(2026, 11, 2, 15, 59))
        self.assertEqual(self.acm.parse_reset("9am (Asia/Seoul)", now), seoul(2026, 11, 3, 9, 0))
        self.assertIsNone(self.acm.parse_reset("soon", now))

    def test_failure_text(self):
        self.assertIsNone(self.acm.parse_usage_text("Failed to load usage data: 401", time.time()))
        self.assertIsNone(self.acm.parse_usage_text("", time.time()))


class AccountUsage(AcmCase):
    def test_five_hour_dropped_after_reset_is_zero_not_ultra(self):
        now = time.time()
        # Even when a reset drops the window from the statusline input, the wrapper keeps the last window as is
        self.statusline("cl1", five_hour={"used_percentage": 80, "resets_at": now - 60, "at": now - 600},
                        seven_day={"used_percentage": 20, "resets_at": now + 86400, "at": now})
        u = self.acm.account_usage("cl1", now)
        self.assertEqual(u["five"], 0.0)
        self.assertIsNone(u["five_reset"])
        self.assertEqual(u["seven"], 20.0)

    def test_no_five_hour_window_means_no_limit(self):
        now = time.time()
        self.statusline("cl1", seven_day={"used_percentage": 20, "resets_at": now + 86400})
        self.assertIsNone(self.acm.account_usage("cl1", now)["five"])
        # Older wrappers wrote a dropped window as null
        self.statusline("cl1", five_hour=None, seven_day={"used_percentage": 20, "resets_at": now + 86400})
        self.assertIsNone(self.acm.account_usage("cl1", now)["five"])

    def test_five_hour_not_seen_for_a_day_means_no_limit(self):
        now = time.time()
        self.statusline("cl1", five_hour={"used_percentage": 10, "resets_at": now - 2 * 86400, "at": now - 2 * 86400},
                        seven_day={"used_percentage": 20, "resets_at": now + 86400, "at": now})
        self.assertIsNone(self.acm.account_usage("cl1", now)["five"])

    def test_newer_source_wins_per_window_and_scoped_comes_from_poll(self):
        now = time.time()
        self.statusline("cl1", seven_day={"used_percentage": 20, "resets_at": now + 86400, "at": now - 900})
        self.polled("cl1", at=now - 60, seven_day={"used_percentage": 25, "resets_at": now + 86400},
                    scoped=[{"name": "Fable", "used_percentage": 50, "resets_at": now + 3600}])
        u = self.acm.account_usage("cl1", now)
        self.assertEqual(u["seven"], 25.0)
        self.assertEqual([(s["short"], s["pct"]) for s in u["scoped"]], [("Fable", 50.0)])


class StatuslineWrapper(AcmCase):
    def run_statusline(self, payload):
        env = dict(os.environ, ACM_ACCOUNT="cl1", ACM_LABEL="t")
        subprocess.run(["sh", STATUSLINE], input=json.dumps(payload), text=True, env=env, capture_output=True, check=True)
        return self.acm.read_json(os.path.join(self.acm.USAGE_DIR, "cl1.json"))

    @unittest.skipUnless(shutil.which("jq"), "jq is not installed")
    def test_keeps_dropped_window_with_its_time(self):
        first = self.run_statusline({"model": {"id": "claude-fable-5-1"}, "rate_limits": {
            "five_hour": {"used_percentage": 40, "resets_at": 1000},
            "seven_day": {"used_percentage": 12, "resets_at": 2000000000}}})
        second = self.run_statusline({"rate_limits": {"seven_day": {"used_percentage": 13, "resets_at": 2000000000}}})
        self.assertEqual(second["five_hour"], first["five_hour"])
        self.assertEqual(second["seven_day"]["used_percentage"], 13)
        self.assertEqual(second["model"], "claude-fable-5-1")

    @unittest.skipUnless(shutil.which("jq"), "jq is not installed")
    def test_unknown_account_falls_back_to_config_dir(self):
        # A session started before the accounts were set up again still carries an old id that is not in the list
        self.accounts(["cl1", "cl2"])
        env = dict(os.environ, ACM_ACCOUNT="acc1", ACM_LABEL="t")
        env.pop("CLAUDE_CONFIG_DIR", None)
        payload = json.dumps({"rate_limits": {"seven_day": {"used_percentage": 7, "resets_at": 2000000000}}})
        subprocess.run(["sh", STATUSLINE], input=payload, text=True, env=env, capture_output=True, check=True)
        self.assertFalse(os.path.exists(os.path.join(self.acm.USAGE_DIR, "acc1.json")))
        self.assertEqual(self.acm.read_json(os.path.join(self.acm.USAGE_DIR, "cl1.json"))["seven_day"]["used_percentage"], 7)
        env["CLAUDE_CONFIG_DIR"] = os.path.join(self.home, ".claude-cl2")
        subprocess.run(["sh", STATUSLINE], input=payload, text=True, env=env, capture_output=True, check=True)
        self.assertTrue(os.path.exists(os.path.join(self.acm.USAGE_DIR, "cl2.json")))

    @unittest.skipUnless(shutil.which("jq"), "jq is not installed")
    def test_drops_legacy_null_and_ignores_empty_input(self):
        self.statusline("cl1", five_hour=None, seven_day={"used_percentage": 5})
        rec = self.run_statusline({"rate_limits": {"seven_day": {"used_percentage": 6, "resets_at": 5}}})
        self.assertNotIn("five_hour", rec)
        again = self.run_statusline({})
        self.assertEqual(again, rec)


class Pick(AcmCase):
    def test_weekly_reset_soon_wins(self):
        now = time.time()
        data = self.accounts(["cl1", "cl2"])
        self.polled("cl1", seven_day={"used_percentage": 40, "resets_at": now + 6 * 86400})
        self.polled("cl2", seven_day={"used_percentage": 70, "resets_at": now + 2 * 3600})
        self.assertEqual(self.acm.pick(data, "usage")[0], "cl2")

    def test_equal_resets_prefers_lower_usage(self):
        now = time.time()
        data = self.accounts(["cl1", "cl2"])
        self.polled("cl1", seven_day={"used_percentage": 30, "resets_at": now + 3 * 86400})
        self.polled("cl2", seven_day={"used_percentage": 10, "resets_at": now + 3 * 86400})
        self.assertEqual(self.acm.pick(data, "usage")[0], "cl2")

    def test_sessions_break_ties_inside_band(self):
        now = time.time()
        data = self.accounts(["cl1", "cl2"])
        self.polled("cl1", seven_day={"used_percentage": 20, "resets_at": now + 3 * 86400})
        self.polled("cl2", seven_day={"used_percentage": 21, "resets_at": now + 3 * 86400})
        self.sessions = [{"account": "cl1", "pid": 1}, {"account": "cl1", "pid": 2}]
        self.assertEqual(self.acm.pick(data, "usage")[0], "cl2")
        self.polled("cl2", seven_day={"used_percentage": 40, "resets_at": now + 3 * 86400})
        self.assertEqual(self.acm.pick(data, "usage")[0], "cl1")

    def test_model_scoped_limit_only_for_that_model(self):
        now = time.time()
        data = self.accounts(["cl1", "cl2"])
        self.polled("cl1", seven_day={"used_percentage": 10, "resets_at": now + 3 * 86400},
                    scoped=[{"name": "Fable", "used_percentage": 99, "resets_at": now + 3 * 86400}])
        self.polled("cl2", seven_day={"used_percentage": 50, "resets_at": now + 3 * 86400},
                    scoped=[{"name": "Fable", "used_percentage": 5, "resets_at": now + 3 * 86400}])
        self.assertEqual(self.acm.pick(data, "usage", "claude-fable-5-1")[0], "cl2")
        self.assertEqual(self.acm.pick(data, "usage", "opus")[0], "cl1")

    def test_five_hour_headroom_counts(self):
        now = time.time()
        data = self.accounts(["cl1", "cl2"])
        week = {"used_percentage": 10, "resets_at": now + 3 * 86400}
        self.polled("cl1", seven_day=week, five_hour={"used_percentage": 80, "resets_at": now + 3600})
        self.polled("cl2", seven_day=week, five_hour={"used_percentage": 10, "resets_at": now + 3600})
        self.assertEqual(self.acm.pick(data, "usage")[0], "cl2")

    def test_reserved_account_held_and_kept_last(self):
        now = time.time()
        data = self.accounts(["cl1", "cl2"], publisher="cl1")
        os.makedirs(self.acm.PUBLISHER_DIR, exist_ok=True)
        self.polled("cl1", seven_day={"used_percentage": 84, "resets_at": now + 3 * 86400})
        self.polled("cl2", seven_day={"used_percentage": 90, "resets_at": now + 3 * 86400})
        # Below the 85% reserve threshold, the primary account is compared like any other
        self.assertEqual(self.acm.pick(data, "usage")[0], "cl1")
        self.polled("cl1", seven_day={"used_percentage": 86, "resets_at": now + 3 * 86400})
        self.assertEqual(self.acm.pick(data, "usage")[0], "cl2")
        # When both are blocked, use the one that is not the primary account
        self.polled("cl2", seven_day={"used_percentage": 99, "resets_at": now + 3 * 86400})
        name, why = self.acm.pick(data, "usage")
        self.assertEqual(name, "cl2")
        self.assertIn("near their limit", why)
        # Once the other account has nothing left, the primary account still has some, so it is used
        self.polled("cl2", seven_day={"used_percentage": 100, "resets_at": now + 3 * 86400})
        self.assertEqual(self.acm.pick(data, "usage")[0], "cl1")
        # When none has anything left, the primary account still comes last
        self.polled("cl1", seven_day={"used_percentage": 100, "resets_at": now + 3 * 86400})
        self.assertEqual(self.acm.pick(data, "usage")[0], "cl2")


class SessionModel(AcmCase):
    def test_order(self):
        self.statusline("cl1", model="claude-sonnet-5-5")
        self.assertEqual(self.acm.session_model([]), "claude-sonnet-5-5")
        with open(os.path.join(self.home, ".claude", "settings.json"), "w") as f:
            json.dump({"model": "opus"}, f)
        self.assertEqual(self.acm.session_model([]), "opus")
        proj = os.path.join(self.home, "proj", ".claude")
        os.makedirs(proj)
        with open(os.path.join(proj, "settings.local.json"), "w") as f:
            json.dump({"model": "haiku"}, f)
        self.assertEqual(self.acm.session_model([], cwd=os.path.dirname(proj)), "haiku")
        os.environ["ANTHROPIC_MODEL"] = "sonnet"
        self.assertEqual(self.acm.session_model([]), "sonnet")
        self.assertEqual(self.acm.session_model(["-c", "--model", "fable"]), "fable")
        self.assertEqual(self.acm.session_model(["--model=fable"]), "fable")
        self.assertEqual(self.acm.session_model(["--", "--model", "x"]), "sonnet")


class Flags(AcmCase):
    def test_add_flag(self):
        add = self.acm.add_flag
        self.assertEqual(add(["-c"], "--disallowedTools", "Artifact", ","), ["--disallowedTools", "Artifact", "-c"])
        self.assertEqual(add(["--disallowedTools", "Bash", "-c"], "--disallowedTools", "Artifact", ","),
                         ["--disallowedTools", "Bash,Artifact", "-c"])
        self.assertEqual(add(["--append-system-prompt=a"], "--append-system-prompt", "b", "\n\n"),
                         ["--append-system-prompt=a\n\nb"])
        self.assertEqual(add(["--", "--disallowedTools", "x"], "--disallowedTools", "A", ","),
                         ["--disallowedTools", "A", "--", "--disallowedTools", "x"])

    def test_bundled_claude(self):
        ext = os.path.join(self.tmp, ".vscode", "extensions", "anthropic.claude-code-2.1.316-darwin-arm64", "resources")
        os.makedirs(ext)
        path = os.path.join(ext, "claude")
        loose = os.path.join(self.tmp, "claude-setup.sh")
        for p in (path, loose):
            with open(p, "w") as f:
                f.write("#!/bin/sh\n")
        self.assertFalse(self.acm.bundled_claude(path))
        os.chmod(path, 0o755)
        os.chmod(loose, 0o755)
        self.assertTrue(self.acm.bundled_claude(path))
        # An executable outside the extension folder may be a path passed as a prompt, so it is not run
        self.assertFalse(self.acm.bundled_claude(loose))
        self.assertFalse(self.acm.bundled_claude("claude"))
        self.assertFalse(self.acm.bundled_claude("-c"))


class VSCodeSettings(AcmCase):
    JSONC = """// user settings {
{
    "editor.fontSize": 13, // font size
    /* multi-line
       comment */
    "url": "https://example.com/*not-a-comment*/",
    "list": [1, 2,],
}
"""

    def test_jsonc_load(self):
        got = self.acm.jsonc_load(self.JSONC)
        self.assertEqual(got, {"editor.fontSize": 13, "url": "https://example.com/*not-a-comment*/", "list": [1, 2]})
        self.assertEqual(self.acm.jsonc_load("  // empty\n"), {})

    def test_write_and_remove_keep_original_text(self):
        for original in (self.JSONC, "{}", "{\n}\n", '{"a":1}'):
            path = os.path.join(self.tmp, "settings.json")
            with open(path, "w") as f:
                f.write(original)
            self.acm.write_vscode_wrapper(path, "/x/acm")
            self.assertEqual(self.acm.vscode_wrapper(path), "/x/acm")
            self.assertTrue(self.acm.remove_vscode_wrapper(path, "/x/acm"))
            with open(path) as f:
                self.assertEqual(f.read(), original)

    def test_setup_and_undo(self):
        os.makedirs(os.path.join(self.home, ".cursor", "extensions", "anthropic.claude-code-2.1.316"))
        settings = os.path.join(self.acm.VSCODE_APP_SUPPORT, "Cursor", "User", "settings.json")
        run = self.acm.SetupRun("yes")
        self.acm.setup_vscode(run)
        self.assertEqual(self.acm.vscode_wrapper(settings), self.acm.ACM_BIN)
        self.assertEqual(run.todo, [])
        self.acm.setup_undo()
        self.assertFalse(os.path.exists(settings))

    def test_other_wrapper_is_left_alone(self):
        os.makedirs(os.path.join(self.home, ".vscode", "extensions", "anthropic.claude-code-2.1.316"))
        settings = os.path.join(self.acm.VSCODE_APP_SUPPORT, "Code", "User", "settings.json")
        os.makedirs(os.path.dirname(settings))
        with open(settings, "w") as f:
            json.dump({self.acm.VSCODE_KEY: "/opt/mine"}, f)
        run = self.acm.SetupRun("yes")
        self.acm.setup_vscode(run)
        self.assertEqual(self.acm.vscode_wrapper(settings), "/opt/mine")
        self.assertEqual(len(run.todo), 1)


class Poll(AcmCase):
    def fake_claude(self, usage_text):
        """Fake claude that answers /usage with usage_text and records token refresh requests in calls."""
        bindir = os.path.join(self.tmp, "bin")
        os.makedirs(bindir, exist_ok=True)
        self.calls = os.path.join(self.tmp, "calls")
        script = f"""#!/bin/sh
echo "$CLAUDE_CONFIG_DIR $ACM_ROLE $2" >> {self.calls}
if [ "$2" = "/usage" ]; then
  printf '%s' {json.dumps(json.dumps({"result": usage_text}))}
fi
"""
        path = os.path.join(bindir, "claude")
        with open(path, "w") as f:
            f.write(script)
        os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR)
        os.environ["PATH"] = bindir + os.pathsep + os.environ.get("PATH", "")

    def test_poll_reads_usage_through_claude(self):
        self.fake_claude(ULTRA_TEXT)
        data = self.accounts(["cl1", "cl2"])
        done = self.acm.run_poll(data)
        self.assertEqual(sorted(done), ["cl1", "cl2"])
        u = self.acm.account_usage("cl2", time.time())
        self.assertEqual(u["seven"] if u["seven_reset"] else 3.0, 3.0)
        self.assertEqual([s["short"] for s in u["scoped"]], ["Fable"])
        self.assertEqual(u["source"], "/usage")
        with open(self.calls) as f:
            lines = f.read().split("\n")
        self.assertIn(f"{os.path.join(self.home, '.claude-cl2')} poll /usage", lines)
        # Not claimed again until the next poll
        self.assertEqual(self.acm.run_poll(data), [])

    def test_failure_starts_token_refresh_once(self):
        self.fake_claude("Failed to load usage data: Request failed with status code 401")
        data = self.accounts(["cl1"])
        self.acm.run_poll(data)
        state = self.acm.read_json(os.path.join(self.acm.POLL_DIR, "cl1.json"))
        self.assertIn("started a token refresh", state["note"])
        self.acm.run_poll(data, force=True)
        state = self.acm.read_json(os.path.join(self.acm.POLL_DIR, "cl1.json"))
        self.assertIn("auth login", state["note"])
        time.sleep(0.5)
        with open(self.calls) as f:
            self.assertEqual(sum(1 for line in f if "token-refresh" in line), 1)

    def test_rate_limit_backs_off_without_refresh(self):
        self.fake_claude("Failed to load usage data: Request failed with status code 429")
        data = self.accounts(["cl1"])
        self.acm.run_poll(data)
        state = self.acm.read_json(os.path.join(self.acm.POLL_DIR, "cl1.json"))
        self.assertGreaterEqual(state["next_at"] - time.time(), self.acm.POLL_FAIL_MIN - 5)
        self.assertNotIn("refresh_at", state)


class SharedFolders(AcmCase):
    def test_relocate_moves_and_links(self):
        self.accounts(["cl1", "cl2"])
        projects = os.path.join(self.home, ".claude", "projects")
        os.makedirs(os.path.join(projects, "p"))
        problems = self.acm.relocate_shared(fix=True)
        self.assertTrue(os.path.islink(projects))
        self.assertEqual(os.path.realpath(projects), os.path.realpath(os.path.join(self.acm.STORE_DIR, "projects")))
        self.assertTrue(os.path.isdir(os.path.join(self.acm.STORE_DIR, "projects", "p")))
        self.assertTrue(any("and linked it" in p for p in problems))
        self.assertEqual(self.acm.relocate_shared(), [])


class StatuslineInstall(AcmCase):
    """The original statusline command stays as the wrapper argument in settings.json, never in a separate unprotected file."""

    ORIGINAL = "bash '/Users/x/.claude/statusline command.sh' --짧게"

    def settings(self, command=None, extra='  "theme": "dark"'):
        path = os.path.join(self.home, ".claude", "settings.json")
        line = f'  "statusLine": {{"type": "command", "command": {json.dumps(command, ensure_ascii=False)}}},\n' if command else ""
        with open(path, "w") as f:
            f.write("{\n" + line + extra + "\n}\n")
        return path

    def command(self, path):
        return (self.acm.read_json(path).get("statusLine") or {}).get("command")

    def test_install_wraps_and_uninstall_restores_exactly(self):
        path = self.settings(self.ORIGINAL)
        with open(path) as f:
            before = f.read()
        self.acm.cmd_install_statusline({}, [])
        wrapped = self.command(path)
        self.assertEqual(shlex.split(wrapped), [self.acm.STATUSLINE_TAP, self.ORIGINAL])
        self.acm.cmd_install_statusline({}, [])
        self.assertEqual(self.command(path), wrapped)
        self.acm.cmd_uninstall_statusline({}, [])
        with open(path) as f:
            self.assertEqual(f.read(), before)

    def planted(self, text="echo planted"):
        """A statusline command planted in ~/.acm, which a session can write without asking."""
        os.makedirs(self.acm.STATE_DIR, exist_ok=True)
        path = os.path.join(self.acm.STATE_DIR, "statusline-inner")
        with open(path, "w") as f:
            f.write(text)
        return path

    def test_planted_inner_file_never_reaches_settings(self):
        path = self.settings(self.acm.STATUSLINE_TAP)
        self.planted()
        run = self.acm.SetupRun("check")
        self.acm.doctor_statusline(run, {"accounts": {}}, [])
        self.assertFalse(run.todo)
        self.acm.cmd_install_statusline({}, [])
        self.assertEqual(self.command(path), self.acm.STATUSLINE_TAP)
        self.acm.cmd_uninstall_statusline({}, [])
        self.assertNotIn("statusLine", self.acm.read_json(path))

    def test_install_without_settings_file_creates_it(self):
        path = os.path.join(self.home, ".claude", "settings.json")
        if os.path.exists(path):
            os.remove(path)
        self.acm.cmd_install_statusline({}, [])
        self.assertEqual(self.command(path), self.acm.STATUSLINE_TAP)
        self.assertFalse([n for n in os.listdir(os.path.dirname(path)) if ".acm-bak-" in n])

    def test_no_statusline_installs_bare_and_uninstall_removes(self):
        path = self.settings()
        self.acm.cmd_install_statusline({}, [])
        self.assertEqual(self.command(path), self.acm.STATUSLINE_TAP)
        self.acm.cmd_uninstall_statusline({}, [])
        self.assertNotIn("statusLine", self.acm.read_json(path))

    @unittest.skipUnless(shutil.which("jq"), "jq is not installed")
    def test_wrapper_runs_its_argument_not_the_legacy_file(self):
        self.planted()
        env = dict(os.environ, ACM_ACCOUNT="cl1", ACM_LABEL="t")

        def run(command):
            return subprocess.run(["sh", "-c", command], input="{}", text=True, env=env,
                                  capture_output=True).stdout
        self.assertEqual(run(shlex.quote(STATUSLINE) + " " + shlex.quote("printf 'a b\\nsecond'")), "[t] a b\nsecond")
        self.assertEqual(run(shlex.quote(STATUSLINE)), "[t]\n")


class PublisherScope(AcmCase):
    """The publisher session handles only files under inbox and its own scratchpad."""

    def write(self, rel, text="<!doctype html><p>x</p>"):
        path = os.path.join(self.home, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(text)
        return path

    def guard(self, tool, sid="sess-1", **tool_input):
        return self.acm.publisher_guard_problem({"tool_name": tool, "tool_input": tool_input,
                                                 "cwd": self.acm.PUBLISHER_DIR, "session_id": sid})

    def test_stage_rejects_secrets_and_non_web_files(self):
        page = self.write("work/report/page.html")
        self.assertIsNone(self.acm.stage_problem(page))
        self.assertIn("~/.ssh", self.acm.stage_problem(self.write(".ssh/key.html")))
        self.assertIn("~/.acm", self.acm.stage_problem(self.write(".acm/accounts.json", "{}")))
        self.assertIn("~/Library", self.acm.stage_problem(self.write("Library/App/state.json", "{}")))
        self.assertIn("hidden files", self.acm.stage_problem(self.write("work/report/.env", "TOKEN=1")))
        self.assertIn(".pem", self.acm.stage_problem(self.write("work/report/cert.pem", "-----")))
        self.assertIn("does not exist", self.acm.stage_problem(os.path.join(self.home, "work/none.html")))
        link = os.path.join(self.home, "work/report/innocent.html")
        os.symlink(os.path.join(self.home, ".ssh/key.html"), link)
        self.assertIn("~/.ssh", self.acm.stage_problem(link))
        # Hidden folders deep inside a project, and hard links to secret files, are refused too
        self.assertIn(".secrets", self.acm.stage_problem(self.write("work/app/.secrets/sa.json", "{}")))
        hard = os.path.join(self.home, "work/report/key.txt")
        os.link(self.write(".ssh/id_rsa.txt", "KEY"), hard)
        self.assertIn("hard links", self.acm.stage_problem(hard))
        self.assertIn("hard links", self.acm.copy_staged(hard, os.path.join(self.tmp, "out.txt")))

    def test_stage_keeps_relative_layout(self):
        page = self.write("work/report/page.html")
        js = self.write("work/report/assets/app.js", "1")
        outside = self.write("work/other/x.css", "a{}")
        self.assertTrue(any("same folder as the first file" in p for p in self.acm.stage_problems([page, outside])))
        staged = self.acm.stage_files([page, js])
        self.assertEqual([rel for _, rel in staged], ["page.html", os.path.join("assets", "app.js")])
        root = os.path.dirname(staged[0][0])
        self.assertEqual(os.path.dirname(root), self.acm.PUBLISHER_INBOX)
        self.assertEqual(staged[1][0], os.path.join(root, "assets", "app.js"))
        with open(staged[1][0]) as f:
            self.assertEqual(f.read(), "1")

    def test_prune_drops_old_staged_folders(self):
        self.acm.stage_files([self.write("work/a.html")])
        old = self.acm.stage_files([self.write("work/b.html")])[0][0]
        old_dir = os.path.dirname(old)
        past = time.time() - self.acm.STAGE_KEEP - 10
        os.utime(old_dir, (past, past))
        self.acm.prune_inbox()
        self.assertFalse(os.path.exists(old_dir))
        self.assertEqual(len(os.listdir(self.acm.PUBLISHER_INBOX)), 1)

    def test_guard_reads_only_inbox_and_own_scratchpad(self):
        staged = self.acm.stage_files([self.write("work/page.html")])[0][0]
        self.assertIsNone(self.guard("Read", file_path=staged))
        self.assertIsNotNone(self.guard("Read", file_path=self.write(".ssh/id_rsa", "k")))
        self.assertIsNotNone(self.guard("Read", file_path=os.path.join(self.acm.PUBLISHER_INBOX, "..", "ROLE.md")))
        # A link inside inbox that points outside is blocked
        link = os.path.join(self.acm.PUBLISHER_INBOX, "link.html")
        os.symlink(self.write(".ssh/key.html"), link)
        self.assertIsNotNone(self.guard("Read", file_path=link))
        self.acm.CLAUDE_TMP = os.path.join(self.tmp, "claude-tmp")
        mine = os.path.join(self.acm.CLAUDE_TMP, "-proj", "sess-1", "scratchpad", "live.html")
        theirs = os.path.join(self.acm.CLAUDE_TMP, "-proj", "sess-2", "scratchpad", "live.html")
        for p in (mine, theirs):
            os.makedirs(os.path.dirname(p))
            open(p, "w").close()
        self.assertIsNone(self.guard("Read", file_path=mine))
        self.assertIsNotNone(self.guard("Read", file_path=theirs))
        self.assertIsNone(self.guard("ListAgents"))

    def test_guard_reads_own_live_copy_for_update(self):
        # Before an update, Artifact read saves the live version to <session ID>/tool-results/artifact-* next to the transcript file
        projects = os.path.join(self.home, ".claude", "projects", "-proj")

        def guard(tool, transcript=os.path.join(projects, "sess-1.jsonl"), **tool_input):
            event = {"tool_name": tool, "tool_input": tool_input, "cwd": self.acm.PUBLISHER_DIR, "session_id": "sess-1"}
            if transcript is not None:
                event["transcript_path"] = transcript
            return self.acm.publisher_guard_problem(event)

        mine = self.write(".claude/projects/-proj/sess-1/tool-results/artifact-d01b-1793682370-8418.html")
        results = os.path.dirname(mine)
        self.assertIsNone(guard("Read", file_path=mine, offset=1, limit=1499))
        self.assertIsNotNone(guard("Read", transcript=None, file_path=mine))
        self.assertIsNotNone(guard("Read", transcript="-proj/sess-1.jsonl", file_path=mine))
        self.assertIsNotNone(guard("Read", transcript=os.path.join(projects, "sess-1"), file_path=mine))
        # Another session's copy, a result file not named artifact-, and subfolders are blocked
        self.assertIsNotNone(guard("Read", file_path=self.write(".claude/projects/-proj/sess-2/tool-results/artifact-a.html")))
        self.assertIsNotNone(guard("Read", file_path=self.write(".claude/projects/-proj/sess-1/tool-results/toolu_01.txt", "k")))
        self.assertIsNotNone(guard("Read", file_path=self.write(".claude/projects/-proj/sess-1/tool-results/x/artifact-a.html")))
        self.assertIsNotNone(guard("Read", file_path=os.path.join(projects, "sess-1.jsonl")))
        # .. is refused even if the path leads back into its own folder
        self.assertIsNotNone(guard("Read", file_path=os.path.join(results, "..", "tool-results", os.path.basename(mine))))
        # A link named artifact- that points outside is blocked
        link = os.path.join(results, "artifact-link.html")
        os.symlink(self.write(".ssh/key.html"), link)
        self.assertIsNotNone(guard("Read", file_path=link))
        # The copy is only readable and is not accepted as a publish path
        self.assertIsNotNone(guard("Artifact", file_path=mine, url="u"))
        staged = self.acm.stage_files([self.write("work/page.html")])[0][0]
        self.assertIsNotNone(guard("Artifact", file_path=staged, url="u", files={"live.html": mine}))
        self.assertIsNone(guard("Artifact", file_path=staged, url="u"))

    def test_guard_artifact_paths_and_actions(self):
        staged = self.acm.stage_files([self.write("work/page.html"), self.write("work/a.js", "1")])
        page, js = staged[0][0], staged[1][0]
        secret = self.write(".aws/credentials.json", "{}")
        self.assertIsNone(self.guard("Artifact", file_path=page, icon="doc"))
        self.assertIsNone(self.guard("Artifact", file_path=page, files={"a.js": js, "logo.svg": {"artifact": "u", "path": "x"}}))
        self.assertIsNone(self.guard("Artifact", file_path=os.path.relpath(page, self.acm.PUBLISHER_DIR)))
        self.assertIsNotNone(self.guard("Artifact", file_path=secret))
        self.assertIsNotNone(self.guard("Artifact", file_path=page, files={"c.json": secret}))
        self.assertIsNotNone(self.guard("Artifact", file_path=page, files={"c.json": {"from": secret}}))
        self.assertIsNotNone(self.guard("Artifact", url="u", asset=True, file_paths=[secret]))
        self.assertIsNotNone(self.guard("Artifact", file_path="credentials.json", root=os.path.dirname(secret)))
        # files accepts only known shapes. An unknown shape may hold a local path, so it is blocked
        self.assertIsNone(self.guard("Artifact", file_path=page, files={"old.js": None}))
        self.assertIsNone(self.guard("Artifact", file_path=page, files=[{"path": js}]))
        for files in ([secret], {"c.json": {"path": secret}}, {"c.json": [secret]}, secret, [{"from": secret}]):
            self.assertIsNotNone(self.guard("Artifact", file_path=page, files=files), files)
        self.assertIsNone(self.guard("Artifact", action="read", url="u"))
        self.assertIsNotNone(self.guard("Artifact", action="read", url="u", out_dir=self.home))
        for action in ("delete", "pin", "unpin"):
            self.assertIsNotNone(self.guard("Artifact", action=action, url="u"))

    def test_stage_sees_home_through_case_and_data_volume_paths(self):
        secret = self.write(".acm/accounts.json", "{}")
        real = os.path.realpath(secret)
        variants = [real.replace("/home/", "/HOME/"), "/System/Volumes/Data" + real]
        lib = self.write("Library/App/state.json", "{}")
        variants.append(os.path.realpath(lib).replace("/Library/", "/library/"))
        tried = 0
        for v in variants:
            if os.path.exists(v):
                tried += 1
                self.assertIsNotNone(self.acm.stage_problem(v), v)
        if not tried:
            self.skipTest("case-sensitive file system, so another path cannot reach the same file")

    def test_guard_allows_only_listed_tools_and_actions(self):
        staged = self.acm.stage_files([self.write("work/page.html")])[0][0]
        self.assertIsNone(self.guard("SendMessage", to="x", message="y"))
        self.assertIsNone(self.guard("ToolSearch", query="select:SendMessage"))
        for tool in ("ArtifactData", "ArtifactComments", "Bash", "mcp__x__y"):
            self.assertIsNotNone(self.guard(tool), tool)
        for action in ("list", "open", "quickstart"):
            self.assertIsNotNone(self.guard("Artifact", action=action), action)
        self.assertIsNotNone(self.guard("Artifact", file_path=staged, url="u", force=True))
        self.assertIsNotNone(self.guard("Artifact", file_path=staged, capabilities={}))

    def test_guard_rejects_dotdot_and_paths_outside_under_either_base(self):
        staged = self.acm.stage_files([self.write("work/page.html")])[0][0]
        root = os.path.dirname(staged)
        nested = os.path.join(root, "a", "b")
        os.makedirs(nested)
        # A path inside inbox relative to root, but climbing up to home relative to the working folder
        self.assertIsNotNone(self.guard("Artifact", root=nested, file_path="../../page.html"))
        self.assertIsNotNone(self.guard("Artifact", file_path=os.path.join(root, "..", os.path.basename(root), "page.html")))
        self.assertIsNotNone(self.guard("Artifact", root=root, file_path="page.html"))

    def test_guard_blocks_when_inbox_is_a_link(self):
        staged = self.acm.stage_files([self.write("work/page.html")])[0][0]
        self.assertIsNone(self.guard("Read", file_path=staged))
        moved = os.path.join(self.home, "elsewhere")
        os.rename(self.acm.PUBLISHER_INBOX, moved)
        os.symlink(moved, self.acm.PUBLISHER_INBOX)
        self.assertIsNotNone(self.guard("Read", file_path=staged))
        self.acm.prune_inbox(now=time.time() + 10 * self.acm.STAGE_KEEP)
        self.assertTrue(os.listdir(moved))

    def test_stage_refuses_path_swapped_after_check(self):
        # Simulate a path switched to a secret file after passing the check, by skipping the check
        secret = self.write(".ssh/key.html", "SECRET")
        link = os.path.join(self.home, "work", "page.html")
        os.makedirs(os.path.dirname(link), exist_ok=True)
        os.symlink(secret, link)
        self.acm.stage_problems = lambda paths: []
        with self.assertRaises(SystemExit):
            self.acm.stage_files([link])
        for root, _, files in os.walk(self.acm.PUBLISHER_INBOX):
            for f in files:
                with open(os.path.join(root, f)) as fh:
                    self.assertNotIn("SECRET", fh.read())

    def test_stage_skips_duplicate_paths(self):
        page = self.write("work/page.html")
        self.assertEqual(len(self.acm.stage_files([page, page])), 1)

    def test_stage_files_are_private(self):
        staged = self.acm.stage_files([self.write("work/page.html")])[0][0]
        self.assertEqual(stat.S_IMODE(os.stat(staged).st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(os.stat(self.acm.PUBLISHER_INBOX).st_mode), 0o700)

    def test_guard_hook_blocks_with_exit_2_and_fails_closed(self):
        def run(stdin):
            return subprocess.run([sys.executable, ACM, "publisher", "guard"], input=stdin, text=True,
                                  capture_output=True, env=os.environ.copy())
        secret = self.write(".ssh/id_rsa", "k")
        blocked = run(json.dumps({"tool_name": "Read", "tool_input": {"file_path": secret}, "session_id": "s"}))
        self.assertEqual(blocked.returncode, 2)
        self.assertIn("outside inbox", blocked.stderr)
        self.assertEqual(run("not json").returncode, 2)
        staged = self.acm.stage_files([self.write("work/page.html")])[0][0]
        self.assertEqual(run(json.dumps({"tool_name": "Read", "tool_input": {"file_path": staged}})).returncode, 0)

    def test_publisher_settings_runs_this_guard(self):
        hook = json.loads(self.acm.publisher_settings())["hooks"]["PreToolUse"][0]
        settings = json.loads(self.acm.publisher_settings())
        self.assertIs(settings["disableAllHooks"], False)
        self.assertEqual(hook["matcher"], "*")
        command = hook["hooks"][0]["command"]
        self.assertTrue(command.endswith("publisher guard || exit 2"))
        self.assertIn(f"ACM_HOME={self.acm.STATE_DIR}", command)
        staged = self.acm.stage_files([self.write("work/page.html")])[0][0]
        event = json.dumps({"tool_name": "Read", "tool_input": {"file_path": staged}})

        def run(**env):
            return subprocess.run(["sh", "-c", command], input=event, text=True, capture_output=True,
                                  env=dict(os.environ, **env)).returncode
        self.assertEqual(run(), 0)
        # Blocks even if acm dies at import
        self.assertEqual(run(ACM_USAGE_BAND="x"), 2)


class Resume(AcmCase):
    """Continue a session stopped at its limit on another account, using the primary account only below its reserve threshold."""

    SID = "0b9f3c2e-1111-4222-8333-944455556666"
    WEEK = 2000000000

    def setUp(self):
        super().setUp()
        self.data = self.accounts(["cl1", "cl2"], publisher="cl1")
        self.acm.refresh_usage = lambda *a, **k: []
        self.launched = []
        self.acm.launch = lambda data, argv, binary=None, reason=None: self.launched.append((argv, reason, os.getcwd()))
        self.project = os.path.join(self.home, "work", "proj")
        os.makedirs(self.project)

    def usage(self, cl1, cl2):
        self.polled("cl1", seven_day={"used_percentage": cl1, "resets_at": self.WEEK})
        self.polled("cl2", seven_day={"used_percentage": cl2, "resets_at": self.WEEK})

    def env_of(self, account):
        d = self.acm.config_dir(self.data["accounts"][account])
        return {"CLAUDE_CONFIG_DIR": d} if d else {}

    def hit(self, account="cl2", error="rate_limit", sid=None):
        return self.acm.hook_stop_failure({"session_id": sid or self.SID, "cwd": self.project, "error": error,
                                           "last_assistant_message": "API Error: Rate limit reached"},
                                          env=self.env_of(account))

    def test_reserve_cap_is_85(self):
        self.assertEqual(self.acm.RESERVE_SEVEN_DAY_CAP, 85)

    def test_hook_records_only_rate_limits(self):
        self.assertIsNone(self.hit(error="overloaded"))
        self.assertIsNone(self.hit(sid="../../x"))
        self.assertIsNone(self.acm.hook_stop_failure(
            {"session_id": self.SID, "cwd": self.acm.PUBLISHER_DIR, "error": "rate_limit"}, env={}))
        self.assertEqual(self.acm.limited_sessions(), [])
        self.assertIn("acm resume", self.hit())
        rec = self.acm.limited_sessions()[0]
        self.assertEqual((rec["session_id"], rec["account"], rec["cwd"]), (self.SID, "cl2", self.project))

    def test_hook_command_prints_terminal_sequence_and_never_fails(self):
        def run(stdin):
            return subprocess.run([sys.executable, ACM, "hook", "stop-failure"], input=stdin, text=True,
                                  capture_output=True, env=dict(os.environ, CLAUDE_CONFIG_DIR=self.env_of("cl2")["CLAUDE_CONFIG_DIR"]))
        out = run(json.dumps({"session_id": self.SID, "cwd": self.project, "error": "rate_limit"}))
        self.assertEqual(out.returncode, 0)
        self.assertTrue(json.loads(out.stdout)["terminalSequence"].startswith("\x1b]9;acm: "))
        bad = run("not json")
        self.assertEqual((bad.returncode, bad.stdout), (0, ""))
        self.assertNotIn("Traceback", bad.stderr)

    def test_resume_moves_to_reserved_account_under_its_cap(self):
        self.usage(cl1=84, cl2=99)
        self.hit()
        self.acm.cmd_resume(self.data, [])
        argv, reason, cwd = self.launched[0]
        self.assertEqual(argv, ["-a", "cl1", "--resume", self.SID])
        self.assertIn("continuing", reason)
        self.assertEqual(os.path.realpath(cwd), os.path.realpath(self.project))
        self.assertEqual(self.acm.limited_sessions(), [])

    def test_resume_refuses_reserved_account_over_85(self):
        self.usage(cl1=86, cl2=99)
        self.hit()
        with self.assertRaises(SystemExit):
            self.acm.cmd_resume(self.data, [])
        self.assertEqual(self.launched, [])
        # The record stays, so it can be used again after the reset or with an explicit account
        self.assertEqual(len(self.acm.limited_sessions()), 1)
        self.acm.cmd_resume(self.data, ["-a", "cl1"])
        self.assertEqual(self.launched[0][0][:2], ["-a", "cl1"])

    def test_reserved_account_session_moves_to_other_account(self):
        self.usage(cl1=99, cl2=40)
        self.hit(account="cl1")
        self.acm.cmd_resume(self.data, [])
        self.assertEqual(self.launched[0][0][:2], ["-a", "cl2"])

    def break_login(self, name):
        now = int(time.time())
        path = os.path.join(self.acm.POLL_DIR, f"{name}.json")
        state = self.acm.read_json(path)
        state.update(ok_at=now - 3600, refresh_at=now - 120, fail_at=now - 60, note="could not read /usage")
        self.acm.save_json(path, state)
        login = self.acm.claude_json_path(self.data["accounts"][name])
        os.utime(login, (now - 3600, now - 3600))
        return login

    def test_resume_skips_account_whose_login_is_broken(self):
        self.usage(cl1=99, cl2=10)
        self.break_login("cl2")
        self.hit(account="cl1")
        with self.assertRaises(SystemExit):
            self.acm.cmd_resume(self.data, [])
        self.assertEqual(self.launched, [])
        name, why = self.acm.pick(self.data, "usage", exclude={"cl1"}, strict=True)
        self.assertIsNone(name)
        self.assertIn("acm -a cl2 auth login", why)
        # New session picks stay as they are. The login screen appears, so the user can sign in again right there
        self.assertEqual(self.acm.pick(self.data, "usage")[0], "cl2")

    def test_login_is_trusted_again_after_relogin(self):
        self.usage(cl1=10, cl2=10)
        login = self.break_login("cl2")
        self.assertTrue(self.acm.login_broken(self.data, "cl2"))
        snap = self.acm.status_snapshot(self.data)
        self.assertTrue(next(a for a in snap["accounts"] if a["id"] == "cl2")["login_broken"])
        # Signing in again changes .claude.json. Even before the next poll, the login is not treated as broken
        os.utime(login, None)
        self.assertFalse(self.acm.login_broken(self.data, "cl2"))

    def test_same_claude_account_is_not_a_place_to_resume(self):
        self.usage(cl1=99, cl2=10)
        self.login("cl2", "cl1@example.com")
        self.hit(account="cl1")
        name, why = self.acm.pick(self.data, "usage", exclude={"cl1"}, strict=True)
        self.assertIsNone(name)
        self.assertIn("same Claude account", why)
        with self.assertRaises(SystemExit):
            self.acm.cmd_resume(self.data, [])
        self.assertEqual(self.launched, [])

    def test_resume_waits_until_session_is_closed(self):
        self.usage(cl1=10, cl2=99)
        self.hit()
        self.acm.open_session_pid = lambda data, sid: 4242
        with self.assertRaises(SystemExit):
            self.acm.cmd_resume(self.data, [])
        self.assertEqual(self.launched, [])

    def test_session_that_kept_going_is_not_offered(self):
        self.hit()
        transcript = os.path.join(self.home, "t.jsonl")
        open(transcript, "w").close()
        path = os.path.join(self.acm.LIMITED_DIR, f"{self.SID}.json")
        rec = self.acm.read_json(path)
        rec.update(transcript=transcript, at=int(time.time()) - 3 * self.acm.LIMITED_GRACE)
        self.acm.save_json(path, rec)
        self.assertEqual(self.acm.limited_sessions(), [])

    def test_setup_adds_hook_beside_existing_and_undo_removes_only_ours(self):
        path = os.path.join(self.home, ".claude", "settings.json")
        theirs = {"hooks": {"StopFailure": [{"hooks": [{"type": "command", "command": "/x/cc-status"}]}]}, "theme": "dark"}
        with open(path, "w") as f:
            json.dump(theirs, f, indent=2)
        self.acm.setup_resume_hook(self.acm.SetupRun("yes"))
        settings = self.acm.read_json(path)
        self.assertTrue(self.acm.resume_hook_installed(settings))
        self.assertEqual(settings["hooks"]["StopFailure"][0], theirs["hooks"]["StopFailure"][0])
        self.assertEqual(settings["hooks"]["StopFailure"][1]["matcher"], "rate_limit")
        self.acm.setup_resume_hook(self.acm.SetupRun("yes"))
        self.assertEqual(len(self.acm.read_json(path)["hooks"]["StopFailure"]), 2)
        self.acm.undo_resume_hook()
        self.assertEqual(self.acm.read_json(path), theirs)


class SameLogin(AcmCase):
    """The browser approved with an account already signed in, so two acm accounts became the same Claude account."""

    def setUp(self):
        super().setUp()
        self.data = self.accounts(["cl1", "cl2"], publisher="cl1")
        self.login("cl2", "cl1@example.com")
        self.acm.refresh_usage = lambda *a, **k: []
        self.acm.remember_emails(self.data)

    def test_duplicate_is_left_out_of_assignment_and_reserve_holds(self):
        self.assertEqual(self.acm.same_login(self.data), {"cl2": "cl1"})
        # Even if the primary account is over its reserve threshold, picks do not leak to another name of the same account
        self.polled("cl1", seven_day={"used_percentage": 90, "resets_at": 2000000000})
        self.polled("cl2", seven_day={"used_percentage": 10, "resets_at": 2000000000})
        self.assertEqual(self.acm.pick(self.data, "usage")[0], "cl1")

    def test_status_and_setup_report_it(self):
        snap = self.acm.status_snapshot(self.data)
        rows = {a["id"]: a for a in snap["accounts"]}
        self.assertEqual((rows["cl1"]["same_as"], rows["cl2"]["same_as"]), (None, "cl1"))
        run = self.acm.SetupRun("check")
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.acm.setup_accounts(run)
        self.assertIn("same Claude account", out.getvalue())
        self.assertTrue(any("acm -a cl2 auth login" in t for t in run.todo))

    def test_account_uuid_wins_over_email(self):
        path = self.acm.claude_json_path(self.data["accounts"]["cl2"])
        self.acm.save_json(path, {"oauthAccount": {"emailAddress": "cl1@example.com", "accountUuid": "other"}})
        self.acm.save_json(self.acm.claude_json_path(self.data["accounts"]["cl1"]),
                           {"oauthAccount": {"emailAddress": "cl1@example.com", "accountUuid": "mine"}})
        self.assertEqual(self.acm.same_login(self.data), {})


class SameOrg(AcmCase):
    """Different Claude accounts tied to one organization are only reported, and picks stay as they are."""

    def org_login(self, name, uuid, org):
        path = self.acm.claude_json_path(self.data["accounts"][name])
        self.acm.save_json(path, {"oauthAccount": {"emailAddress": f"{name}@corp.example", "accountUuid": uuid,
                                                   "organizationUuid": org, "organizationName": "Corp"}})

    def setUp(self):
        super().setUp()
        self.data = self.accounts(["cl1", "cl2", "cl3"])
        self.acm.refresh_usage = lambda *a, **k: []

    def test_accounts_in_one_org_are_reported(self):
        self.org_login("cl1", "u1", "org-a")
        self.org_login("cl2", "u2", "org-a")
        self.org_login("cl3", "u3", "org-b")
        self.assertEqual(self.acm.same_org(self.data), {"org-a": ("Corp", ["cl1", "cl2"])})
        snap = self.acm.status_snapshot(self.data)
        self.assertEqual({a["id"]: a["same_org"] for a in snap["accounts"]}, {"cl1": ["cl2"], "cl2": ["cl1"], "cl3": []})
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.acm.cmd_status(self.data, [])
        self.assertIn("same organization Corp", out.getvalue())

    def test_same_login_is_not_an_org_match(self):
        self.org_login("cl1", "u1", "org-a")
        self.org_login("cl2", "u1", "org-a")
        self.assertEqual(self.acm.same_org(self.data), {})


class StatusBeforeFirstRead(AcmCase):
    """An account whose usage has never been read is not assumed to be an Ultra account with no 5h limit."""

    def setUp(self):
        super().setUp()
        self.data = self.accounts(["cl1", "cl2"])
        self.acm.refresh_usage = lambda *a, **k: []

    def status(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.acm.cmd_status(self.data, [])
        return out.getvalue()

    def test_no_reads_make_no_ultra_claim(self):
        self.assertNotIn("Ultra", self.status())
        # With only one account read, another account may have a 5h window, so the reason for hiding the column is not assumed either
        self.polled("cl1", seven_day={"used_percentage": 10, "resets_at": 2000000000})
        self.assertNotIn("5H column is hidden", self.status())
        self.polled("cl2", seven_day={"used_percentage": 20, "resets_at": 2000000000})
        self.assertIn("5H column is hidden", self.status())

    def test_unread_row_is_blank_not_unlimited(self):
        self.polled("cl1", five_hour={"used_percentage": 30, "resets_at": 2000000000},
                    seven_day={"used_percentage": 10, "resets_at": 2000000000})
        out = self.status()
        row = next(line for line in out.splitlines() if line.startswith("cl2 "))
        self.assertNotIn("none", row)
        self.assertNotIn("Ultra", out)

    def test_new_id_counts_after_existing_accounts(self):
        self.assertEqual(self.acm.next_account_id(self.accounts(["cl1"])), "cl2")
        # Installs upgraded from 0.2.0 keep their acc ids. The third account is cl3
        legacy = {"order": ["acc1", "acc2"], "accounts": {"acc1": {"dir": None}, "acc2": {"dir": "/x"}}}
        self.assertEqual(self.acm.next_account_id(legacy), "cl3")

    def test_second_claude_account_points_to_setup(self):
        data = self.accounts(["cl1"])
        with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()):
            self.acm.cmd_add(data, ["cl2"])
        self.assertIn("acm setup", out.getvalue())

    def test_add_rejects_ids_that_leave_their_folder(self):
        # The id goes into paths like ~/.acm/run/<id>. With .., it could delete files in ~/.acm
        for bad in ("..", "a/b", "x;open -a Calculator", "", "a" * 33):
            data = self.accounts(["cl1"])
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                self.acm.cmd_add(data, [bad])
            self.assertNotIn(bad, data["accounts"])


class Processes(AcmCase):
    """Session accounts are told apart by the environment the kernel hands out, not ps strings, and other users' claude is not counted."""

    def test_proc_env_separates_arguments_from_environment(self):
        env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "ACM_TEST_MARK": "a b"}
        # The kernel gives no environment for system binaries in /bin and /usr/bin, so start Python as the child
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)",
                                  "CLAUDE_CONFIG_DIR=/wrong", "ACM_ROLE=poll"], env=env)
        try:
            for _ in range(50):
                got = self.acm.proc_env(child.pid)
                if got and "ACM_TEST_MARK" in got:
                    break
                time.sleep(0.05)
            self.assertEqual(got.get("ACM_TEST_MARK"), "a b")
            self.assertNotIn("CLAUDE_CONFIG_DIR", got)
            self.assertNotIn("ACM_ROLE", got)
        finally:
            child.kill()
            child.wait()
        if os.getuid() != 0:
            self.assertIsNone(self.acm.proc_env(1))

    def fresh_module(self):
        loader = importlib.machinery.SourceFileLoader("acm_processes", ACM)
        spec = importlib.util.spec_from_loader("acm_processes", loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        return mod

    def test_sessions_follow_config_dir_and_skip_other_users(self):
        data = self.accounts(["cl1", "cl2"])
        mod = self.fresh_module()
        me, other = os.getuid(), os.getuid() + 1
        rows = [(100, 1, me, "01:00", "/opt/homebrew/bin/claude"), (101, 100, me, "00:30", "claude"),
                (200, 1, other, "02:00", "claude"), (300, 1, me, "00:10", "claude"), (400, 1, me, "00:05", "claude")]

        def quick_run(cmd, timeout=10):
            if cmd[:2] != ["ps", "-axo"]:
                return ""
            if cmd[2] == "pid=,uid=,comm=":
                return "".join(f"{r[0]} {r[2]} {r[4]}\n" for r in rows)
            return "".join(" ".join(map(str, r)) + "\n" for r in rows)
        mod.quick_run = quick_run
        # 400 is my process, but its environment could not be read. It is not counted as the default account
        envs = {100: {"CLAUDE_CONFIG_DIR": data["accounts"]["cl2"]["dir"], "ACM_ACCOUNT": "cl1"},
                300: {"ACM_ROLE": "poll"}}
        mod.proc_info = lambda pid: ([], envs[pid]) if pid in envs else None
        sessions = mod.running_sessions(data, with_cwd=False)
        self.assertEqual(sorted((x["pid"], x["account"]) for x in sessions), [(100, "cl2"), (400, None)])
        self.assertEqual(sorted(mod.claude_pids()), [100, 101, 300, 400])

    def test_codex_sessions_follow_codex_home(self):
        data = self.accounts(["cl1"])
        cx2 = os.path.join(self.home, ".codex-cx2")
        data["accounts"].update({"cx1": {"tool": "codex", "dir": None}, "cx2": {"tool": "codex", "dir": cx2}})
        data["order"] += ["cx1", "cx2"]
        mod = self.fresh_module()
        me = os.getuid()
        rows = [(500, 1, me, "00:20", "/opt/homebrew/bin/codex"), (501, 500, me, "00:10", "codex"),
                (502, 1, me, "01:00", "codex"), (503, 1, me, "00:05", "codex"), (504, 1, me, "00:01", "codex"),
                (600, 1, me, "00:30", "claude")]
        mod.quick_run = lambda cmd, timeout=10: "".join(" ".join(map(str, r)) + "\n" for r in rows) if cmd[:2] == ["ps", "-axo"] else ""
        # 502 is an app-server daemon codex left running, and 504 is acm's usage poll, so neither is a session
        infos = {500: (["codex"], {}), 502: (["codex", "app-server", "--listen"], {}),
                 503: (["codex", "resume"], {"CODEX_HOME": cx2, "ACM_CODEX_ACCOUNT": "cx2"}),
                 504: (["codex", "app-server"], {"ACM_ROLE": "poll"}), 600: (["claude"], {})}
        mod.proc_info = lambda pid: infos.get(pid)
        got = sorted((x["pid"], x["tool"], x["account"], x["via"]) for x in mod.running_sessions(data, with_cwd=False))
        self.assertEqual(got, [(500, "codex", "cx1", "codex"), (503, "codex", "cx2", "acm"), (600, "claude", "cl1", "claude")])


class AccountsFile(AcmCase):
    """Code that edits accounts.json re-reads the file and changes only its own part."""

    def test_remember_emails_keeps_changes_made_meanwhile(self):
        stale = self.accounts(["cl1", "cl2"])
        # Another acm changed last and mode in the meantime
        self.acm.update_accounts(lambda d: d.update(last="cl2", mode="rr"))
        self.login("cl2", "new@example.com")
        self.acm.remember_emails(stale)
        saved = self.acm.load_accounts()
        self.assertEqual((saved["last"], saved["mode"]), ("cl2", "rr"))
        self.assertEqual(saved["accounts"]["cl2"]["email"], "new@example.com")
        self.assertEqual(stale["accounts"]["cl2"]["email"], "new@example.com")

    def test_label_and_mode_do_not_drop_each_other(self):
        stale = self.accounts(["cl1", "cl2"])
        self.acm.update_accounts(lambda d: d.update(mode="rr"))
        with contextlib.redirect_stdout(io.StringIO()):
            self.acm.cmd_label(stale, ["cl2", "personal"])
        saved = self.acm.load_accounts()
        self.assertEqual((saved["mode"], saved["accounts"]["cl2"]["label"]), ("rr", "personal"))


class Upgrade(AcmCase):
    def test_output_stays_in_order_through_a_pipe(self):
        # acm prints "Pulling" before git pull. Through a pipe, that line used to come out after install.sh's output
        git = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "init.defaultBranch=main"]
        origin, src = os.path.join(self.tmp, "origin"), os.path.join(self.tmp, "src")
        subprocess.run(git + ["init", "-q", origin], check=True)
        with open(os.path.join(origin, "install.sh"), "w") as f:
            f.write("echo installed\n")
        subprocess.run(git + ["-C", origin, "add", "."], check=True)
        subprocess.run(git + ["-C", origin, "commit", "-qm", "c"], check=True)
        subprocess.run(git + ["clone", "-q", origin, src], check=True)
        self.acm.save_json(self.acm.INSTALL_FILE, {"source": src, "no_app": True})
        out = subprocess.run([sys.executable, ACM, "upgrade"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, env=os.environ, cwd=self.home).stdout
        lines = out.splitlines()
        self.assertIn(f"Pulling {src}", lines, out)
        self.assertIn("installed", lines, out)
        self.assertLess(lines.index(f"Pulling {src}"), lines.index("installed"), out)


class Resilience(AcmCase):
    """A defect in acm or odd input must never keep claude from starting."""

    def test_removed_publisher_account_falls_back(self):
        data = self.accounts(["cl1", "cl2"], publisher="cl2")
        self.acm.cmd_rm(data, ["cl2"])
        data = self.acm.load_accounts()
        self.assertNotIn("account", data["publisher"])
        # A missing primary account left by an older acm also falls back to the first account
        data["publisher"]["account"] = "gone"
        self.assertEqual(self.acm.publisher_conf(data), (True, "cl1"))
        self.assertIn("cl1", self.acm.session_rules(data, "cl1", True, False))

    def test_no_logged_in_account_launches_first(self):
        data = self.accounts(["cl1", "cl2"])
        os.remove(os.path.join(self.home, ".claude.json"))
        os.remove(os.path.join(self.home, ".claude-cl2", ".claude.json"))
        self.acm.remember_emails(data)
        data = self.acm.load_accounts()
        for acc in data["accounts"].values():
            acc.pop("email", None)
        name, why = self.acm.pick(data, "usage")
        self.assertEqual(name, "cl1")
        self.assertIn("no signed-in account", why)

    def test_unreadable_claude_json_is_left_alone(self):
        data = self.accounts(["cl1", "cl2"])
        path = os.path.join(self.home, ".claude-cl2", ".claude.json")
        with open(path, "w") as f:
            f.write('{"oauthAccount": {"emailAddress": "cl2@exam')
        self.acm.sync_claude_json(data["accounts"]["cl2"])
        with open(path) as f:
            self.assertIn("cl2@exam", f.read())

    def test_odd_settings_and_usage_values_do_not_crash(self):
        os.makedirs(os.path.join(self.home, "repo", ".claude"))
        with open(os.path.join(self.home, "repo", ".claude", "settings.json"), "w") as f:
            f.write("[1]")
        self.acm.session_model([], cwd=os.path.join(self.home, "repo"))
        now = time.time()
        self.assertEqual(self.acm.window_pct({"used_percentage": "n/a", "resets_at": "soon"}, now), 0.0)
        self.assertEqual(self.acm.window_pct({"used_percentage": "42", "resets_at": now + 60}, now), 42.0)
        self.assertIsNone(self.acm.window_reset({"resets_at": "soon"}, now))

    def test_launch_error_falls_back_to_plain_claude(self):
        calls = []

        def boom(data, argv, binary=None, **kw):
            raise RuntimeError("bug")
        self.acm.launch = boom
        real_execv, real_execvp = os.execv, os.execvp
        os.execv = lambda path, args: calls.append(("execv", path, args))
        os.execvp = lambda path, args: calls.append(("execvp", path, args))
        try:
            self.acm.safe_launch(["-a", "cl2", "--rr", "-c"], "/x/claude")
            self.acm.safe_launch(["-p", "hi"])
        finally:
            os.execv, os.execvp = real_execv, real_execvp
        self.assertEqual(calls[0], ("execv", "/x/claude", ["/x/claude", "-c"]))
        self.assertEqual(calls[1][2][1:], ["-p", "hi"])


def free_limits(reset=2000000000, allowed=False):
    snap = {"limitId": "codex", "limitName": None, "primary": {"usedPercent": 100, "windowDurationMins": 43200,
                                                                 "resetsAt": reset},
            "secondary": None, "planType": "free", "rateLimitReachedType": "rate_limit_reached"}
    return {"ordinaryUsageAllowed": allowed, "rateLimits": snap, "rateLimitsByLimitId": {"codex": snap},
            "accountId": "acct-1"}


FREE_ACCOUNT = {"account": {"type": "chatgpt", "email": "me@example.com", "planType": "free"},
                "requiresOpenaiAuth": True, "workspaceRouting": {"chatgptAccountId": "acct-1"}}

# Fake codex that answers account/read and account/rateLimits/read. Returns the CODEX_HOME folder name as the email local part
FAKE_CODEX = r"""#!%(python)s
import json, os, sys
home = os.path.basename(os.environ.get("CODEX_HOME", "root"))
if sys.argv[1:] != ["app-server"]:
    sys.exit(2)
for line in sys.stdin:
    msg = json.loads(line)
    if "id" not in msg:
        continue
    method = msg["method"]
    if method == "initialize":
        result = {"userAgent": "fake"}
    elif method == "account/read":
        if os.path.exists(os.path.join(os.environ.get("CODEX_HOME", ""), "logged-out")):
            result = {"account": None, "requiresOpenaiAuth": True}
        else:
            result = {"account": {"type": "chatgpt", "email": home + "@example.com", "planType": "plus"},
                      "workspaceRouting": {"chatgptAccountId": "id-" + home}}
    else:
        result = {"ordinaryUsageAllowed": True, "rateLimits": {"limitId": "codex",
                  "primary": {"usedPercent": 40, "windowDurationMins": 300, "resetsAt": 2000000000},
                  "secondary": {"usedPercent": 20, "windowDurationMins": 10080, "resetsAt": 2000000000},
                  "planType": "plus"}}
    # Put a notification before each response to check that responses are matched by id
    sys.stdout.write(json.dumps({"method": "account/updated", "params": {}}) + "\n")
    sys.stdout.write(json.dumps({"id": msg["id"], "result": result}) + "\n")
    sys.stdout.flush()
"""


class Codex(AcmCase):
    """Codex accounts are picked only among Codex accounts, and usage is read with codex app-server."""

    def setUp(self):
        super().setUp()
        self.root = os.path.join(self.home, ".codex")
        os.makedirs(os.path.join(self.root, "sessions", "2026"))
        os.makedirs(os.path.join(self.root, "app-server-daemon"))
        os.makedirs(os.path.join(self.root, "tmp"))
        for name in ("auth.json", "config.toml", "hooks.json", "history.jsonl", "state_5.sqlite", "state_5.sqlite-wal"):
            with open(os.path.join(self.root, name), "w") as f:
                f.write("{}")
        self.acm.refresh_usage = lambda *a, **k: []

    def codex_accounts(self, claude=("cl1",), codex=("cx1", "cx2"), publisher=None):
        data = self.accounts(list(claude), publisher=publisher)
        for n in codex:
            d = None if n == "cx1" else os.path.join(self.home, f".codex-{n}")
            os.makedirs(d or self.root, exist_ok=True)
            with open(os.path.join(d or self.root, "auth.json"), "w") as f:
                f.write("{}")
            data["accounts"][n] = {"tool": "codex", "dir": d, "email": f"{n}@chatgpt.test"}
            data["order"].append(n)
        self.acm.save_json(self.acm.ACCOUNTS_FILE, data)
        return data

    def codex_polled(self, name, windows, allowed=None, plan="plus"):
        at = int(time.time())
        rec = {"tool": "codex", "updated_at": at, "plan": plan, "allowed": allowed, "scoped": [],
               "windows": [dict(w, at=at) for w in windows]}
        self.acm.save_json(os.path.join(self.acm.POLL_DIR, f"{name}.json"), {"usage": rec, "next_at": time.time() + 999})

    def test_free_plan_has_one_thirty_day_window(self):
        rec, ident = self.acm.parse_codex_usage({"account/read": FREE_ACCOUNT, "account/rateLimits/read": free_limits()}, 100)
        self.assertEqual(rec["windows"], [{"used_percentage": 100.0, "resets_at": 2000000000.0, "window_minutes": 43200.0, "at": 100}])
        self.assertEqual((rec["plan"], rec["allowed"]), ("free", False))
        self.assertEqual(ident, {"email": "me@example.com", "plan": "free", "account_id": "acct-1"})
        u = self.acm.codex_usage(rec, time.time())
        self.assertEqual((u["five"], u["seven"], u["seven_name"], u["seven_window"]), (None, 100.0, "30d", 30 * 86400))
        self.assertTrue(u["denied"])
        self.assertTrue(self.acm.score_account(u, None, time.time(), 95, 98)[1])

    def test_paid_plan_windows_and_passed_reset(self):
        now = time.time()
        rec = {"tool": "codex", "updated_at": int(now), "allowed": False, "windows": [
            {"used_percentage": 40, "resets_at": now + 3600, "window_minutes": 300},
            {"used_percentage": 20, "resets_at": now + 86400, "window_minutes": 10080}]}
        u = self.acm.codex_usage(rec, now)
        self.assertEqual((u["five"], u["seven"], u["seven_name"]), (40, 20, "Week"))
        self.assertEqual(self.acm.fmt_u(u), "5h 40% · Week 20%")
        # After a block is reported, the account is usable again once all windows have reset
        u = self.acm.codex_usage(rec, now + 2 * 86400)
        self.assertEqual((u["five"], u["seven"], u["denied"]), (0.0, 0.0, False))

    def test_pick_stays_inside_each_tool(self):
        data = self.codex_accounts(claude=("cl1", "cl2"), publisher="cl1")
        os.makedirs(self.acm.PUBLISHER_DIR, exist_ok=True)
        self.polled("cl1", seven_day={"used_percentage": 10, "resets_at": 2000000000})
        self.polled("cl2", seven_day={"used_percentage": 90, "resets_at": 2000000000})
        self.codex_polled("cx1", [{"used_percentage": 100, "resets_at": 2000000000, "window_minutes": 43200}], allowed=False)
        self.codex_polled("cx2", [{"used_percentage": 50, "resets_at": 2000000000, "window_minutes": 10080}])
        self.assertEqual(self.acm.pick(data, "usage")[0], "cl1")
        name, why = self.acm.pick(data, "usage", tool="codex")
        self.assertEqual(name, "cx2")
        self.assertIn("Week 50%", why)
        # rr also remembers the last account separately for each tool
        self.acm.set_last_pick(data, "codex", "cx2")
        self.assertEqual(self.acm.pick(data, "rr", tool="codex")[0], "cx1")
        self.assertIsNone(self.acm.load_accounts()["last"])

    def test_all_blocked_skips_account_codex_refuses(self):
        # cx1 is refused by Codex until its 30-day reset. cx2 is past the 95% 5h cap but still has 3% left.
        # Past the caps both scores used to be 0, so rotation order picked cx1, which cannot start a session
        now = time.time()
        data = self.codex_accounts()
        self.codex_polled("cx1", [{"used_percentage": 100, "resets_at": now + 20 * 86400, "window_minutes": 43200}],
                          allowed=False, plan="free")
        self.codex_polled("cx2", [{"used_percentage": 97, "resets_at": now + 3600, "window_minutes": 300},
                                  {"used_percentage": 15, "resets_at": now + 5 * 86400, "window_minutes": 10080}])
        name, why = self.acm.pick(data, "usage", tool="codex")
        self.assertEqual(name, "cx2")
        self.assertIn("near their limit", why)
        # Once cx2 has nothing left either, it still wins because its 5h window resets long before cx1's 30 days
        self.codex_polled("cx2", [{"used_percentage": 100, "resets_at": now + 3600, "window_minutes": 300},
                                  {"used_percentage": 16, "resets_at": now + 5 * 86400, "window_minutes": 10080}],
                          allowed=False)
        self.assertEqual(self.acm.pick(data, "usage", tool="codex")[0], "cx2")
        # If cx1 frees up first, it is the one
        self.codex_polled("cx1", [{"used_percentage": 100, "resets_at": now + 600, "window_minutes": 43200}],
                          allowed=False, plan="free")
        self.assertEqual(self.acm.pick(data, "usage", tool="codex")[0], "cx1")

    def test_pick_without_codex_accounts_stops(self):
        data = self.accounts(["cl1"])
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.acm.pick(data, "usage", tool="codex")

    def test_claude_plan_is_remembered_and_shown(self):
        data = self.codex_accounts()
        path = os.path.join(self.home, ".claude.json")
        with open(path, "w") as f:
            json.dump({"oauthAccount": {"emailAddress": "me@example.com", "planDisplayName": "Ultra"}}, f)
        snap = self.acm.status_snapshot(data)
        cl1 = next(a for a in snap["accounts"] if a["id"] == "cl1")
        self.assertEqual((cl1["email"], cl1["plan"]), ("me@example.com", "Ultra"))
        self.assertEqual(self.acm.load_accounts()["accounts"]["cl1"]["plan"], "Ultra")
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.acm.cmd_status(data, [])
        self.assertRegex(out.getvalue(), r"cl1 .*me@example.com +Ultra")
        # Signing out also clears the plan
        with open(path, "w") as f:
            json.dump({}, f)
        self.acm.remember_emails(data)
        saved = self.acm.load_accounts()["accounts"]["cl1"]
        self.assertEqual((saved.get("email"), "plan" in saved), (None, False))

    def test_same_email_resolves_claude_first(self):
        data = self.codex_accounts()
        self.login("cl1", "me@example.com")
        data["accounts"]["cx1"]["email"] = "me@example.com"
        self.acm.remember_emails(data)
        self.assertEqual(self.acm.resolve(data, "me"), "cl1")
        self.assertEqual(self.acm.resolve(data, "me", "codex"), "cx1")

    def test_links_share_root_but_keep_login_daemon_and_wal(self):
        acc = {"tool": "codex", "dir": os.path.join(self.home, ".codex-cx2")}
        self.assertEqual(self.acm.sync_codex_links("cx2", acc), [])
        d = acc["dir"]
        for name in ("config.toml", "hooks.json", "sessions", "state_5.sqlite"):
            self.assertEqual(os.readlink(os.path.join(d, name)), os.path.join(self.root, name))
        for name in ("auth.json", "state_5.sqlite-wal", "app-server-daemon", "tmp"):
            self.assertFalse(os.path.lexists(os.path.join(d, name)), name)
        # When moving the DB of a folder in use, the WAL that is not merged yet moves along
        old = {"tool": "codex", "dir": os.path.join(self.home, ".codex-old")}
        os.makedirs(old["dir"])
        for name in ("state_5.sqlite", "state_5.sqlite-wal"):
            with open(os.path.join(old["dir"], name), "w") as f:
                f.write("old")
        self.assertEqual(len(self.acm.sync_codex_links("old", old, fix=True)), 1)
        parked = sorted(os.listdir(os.path.join(old["dir"], ".acm-drift")))
        self.assertEqual(len(parked), 2)
        self.assertEqual(parked[1], parked[0] + "-wal")
        self.assertTrue(parked[0].startswith("state_5.sqlite."))
        self.assertFalse(os.path.lexists(os.path.join(old["dir"], "state_5.sqlite-wal")))

    def test_account_folder_is_made_even_without_root(self):
        shutil.rmtree(self.root)
        acc = {"tool": "codex", "dir": os.path.join(self.home, ".codex-new")}
        self.assertEqual(self.acm.sync_codex_links("new", acc), [])
        self.assertTrue(os.path.isdir(acc["dir"]))

    def test_same_login_needs_same_email_and_workspace(self):
        data = self.codex_accounts(codex=("cx1", "cx2", "cx3"))
        for n, email in (("cx1", "a@team.test"), ("cx2", "b@team.test"), ("cx3", "a@team.test")):
            data["accounts"][n].update(email=email, account_id="ws-1")
        # Another person in the same team workspace is not the same login
        self.assertEqual(self.acm.same_login(data), {"cx3": "cx1"})

    def test_logout_clears_codex_identity(self):
        data = self.codex_accounts()
        data["accounts"]["cx2"].update(plan="plus", account_id="ws-2")
        self.acm.save_json(self.acm.ACCOUNTS_FILE, data)
        os.remove(os.path.join(self.home, ".codex-cx2", "auth.json"))
        self.acm.remember_emails(data)
        saved = self.acm.load_accounts()["accounts"]["cx2"]
        self.assertEqual({k: saved.get(k) for k in ("email", "plan", "account_id")}, {"email": None, "plan": None, "account_id": None})
        self.assertIsNone(self.acm.account_identity(saved))

    def test_fallback_keeps_the_forced_accounts_tool(self):
        self.codex_accounts()
        self.acm.codex_bin = lambda: "/fake/codex"
        calls = []

        def boom(data, argv, binary=None, **kw):
            raise RuntimeError("bug")
        self.acm.launch = boom
        real = os.execv
        os.execv = lambda path, args: calls.append((path, args))
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                self.acm.safe_launch(["-a", "cx2", "resume"])
        finally:
            os.execv = real
        self.assertEqual(calls, [("/fake/codex", ["/fake/codex", "resume"])])

    def test_add_registers_root_and_adopts_logged_in_folder(self):
        data = self.accounts(["cl1"])
        work = os.path.join(self.home, ".codex-work")
        os.makedirs(work)
        # A folder that is not signed in is not taken as an account
        os.makedirs(os.path.join(self.home, ".codex-backup"))
        for name in ("auth.json", "history.jsonl"):
            with open(os.path.join(work, name), "w") as f:
                f.write("work")
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.acm.cmd_add(data, ["--codex"])
        data = self.acm.load_accounts()
        self.assertEqual(data["accounts"]["cx1"], {"tool": "codex", "dir": None})
        self.assertEqual(data["accounts"]["work"], {"tool": "codex", "dir": work})
        self.assertNotIn("backup", data["accounts"])
        # history.jsonl that Codex made is moved aside, and the ~/.codex side is linked. Login data stays as is
        self.assertTrue(os.path.islink(os.path.join(work, "history.jsonl")))
        self.assertEqual(len(os.listdir(os.path.join(work, ".acm-drift"))), 1)
        with open(os.path.join(work, "auth.json")) as f:
            self.assertEqual(f.read(), "work")
        with contextlib.redirect_stdout(io.StringIO()):
            self.acm.cmd_add(data, ["--codex"])
        # After cx1 and work, the third Codex account is cx3
        self.assertEqual(self.acm.load_accounts()["accounts"]["cx3"]["dir"], os.path.join(self.home, ".codex-cx3"))

    def test_hook_trust_is_mirrored_once_into_extra_accounts(self):
        root_hooks = os.path.join(self.root, "hooks.json")
        conf = os.path.join(self.root, "config.toml")
        with open(conf, "w") as f:
            f.write('[tui]\nx = true\n\n[hooks.state]\n\n'
                    f'[hooks.state."{root_hooks}:session_start:0:0"]\ntrusted_hash = "sha256:aa"\nenabled = true\n\n'
                    f'[hooks.state."{root_hooks}:session_end:0:0"]\ntrusted_hash = "sha256:bb"\n'
                    '[projects."/work"]\ntrust_level = "trusted"')
        os.chmod(conf, 0o600)
        cx2 = {"tool": "codex", "dir": os.path.join(self.home, ".codex-cx2")}
        cx3 = {"tool": "codex", "dir": os.path.join(self.home, ".codex-cx3")}
        mine3 = os.path.join(cx3["dir"], "hooks.json")
        with open(conf, "a") as f:
            f.write(f'\n[hooks.state."{mine3}:session_start:0:0"]\ntrusted_hash = "sha256:old"\n')
        with contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(self.acm.sync_codex_links("cx2", cx2), [])
            self.acm.sync_codex_links("cx3", cx3)
        self.assertIn("as trusted for this account", err.getvalue())
        with open(conf) as f:
            text = f.read()
        mine2 = os.path.join(cx2["dir"], "hooks.json")
        self.assertIn(f'[hooks.state."{mine2}:session_start:0:0"]\ntrusted_hash = "sha256:aa"\nenabled = true\n', text)
        self.assertIn(f'[hooks.state."{mine2}:session_end:0:0"]\ntrusted_hash = "sha256:bb"\n', text)
        # Existing account records stay as they are even with a different hash. Only missing ones are added
        self.assertEqual(text.count(f'"{mine3}:session_start:0:0"'), 1)
        self.assertIn('trusted_hash = "sha256:old"', text)
        self.assertIn(f'[hooks.state."{mine3}:session_end:0:0"]', text)
        self.assertEqual(stat.S_IMODE(os.stat(conf).st_mode), 0o600)
        self.assertTrue(os.path.islink(os.path.join(cx2["dir"], "config.toml")))
        self.assertFalse(self.acm.mirror_hook_trust(cx2))
        # If config.toml is kept per account, nothing is written to the root file
        cx4 = {"tool": "codex", "dir": os.path.join(self.home, ".codex-cx4")}
        os.makedirs(cx4["dir"])
        open(os.path.join(cx4["dir"], "config.toml"), "w").close()
        with contextlib.redirect_stdout(io.StringIO()):
            self.acm.sync_codex_links("cx4", cx4)
        self.assertFalse(self.acm.mirror_hook_trust(cx4))
        with open(conf) as f:
            self.assertNotIn(".codex-cx4", f.read())

    def test_hook_trust_mirror_never_breaks_config(self):
        root_hooks = os.path.join(self.root, "hooks.json")
        dotfiles = os.path.join(self.tmp, "dotfiles")
        os.makedirs(dotfiles)
        real_conf = os.path.join(dotfiles, "codex.toml")
        conf = os.path.join(self.root, "config.toml")
        os.unlink(conf)
        os.symlink(real_conf, conf)
        # An indented next table, a record with a multi-line value, a record without a hash, and a last record that ends without a newline
        with open(real_conf, "w") as f:
            f.write(f'[hooks.state."{root_hooks}:a:0:0"]\ntrusted_hash = "sha256:aa"\n\n'
                    '  [projects."/work"]\n  trust_level = "trusted"\n\n'
                    f'[hooks.state."{root_hooks}:b:0:0"]\ntrusted_hash = "sha256:bb"\nextra = [\n  1,\n]\n\n'
                    f'[hooks.state."{root_hooks}:c:0:0"]\nenabled = false\n\n'
                    f'[hooks.state."{root_hooks}:d:0:0"]\nenabled = true\ntrusted_hash = "sha256:dd"')
        cx2 = {"tool": "codex", "dir": os.path.join(self.home, ".codex-cx2")}
        open(os.path.join(self.root, ".acm-config.1.toml"), "w").close()
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(self.acm.sync_codex_links("cx2", cx2), [])
        # The link stays, and the write goes to the file it points to. Temp files are not linked into account folders
        self.assertTrue(os.path.islink(conf))
        self.assertFalse(os.path.lexists(os.path.join(cx2["dir"], ".acm-config.1.toml")))
        with open(real_conf) as f:
            text = f.read()
        mine = os.path.join(cx2["dir"], "hooks.json")
        self.assertEqual(text.count('[projects."/work"]'), 1)
        self.assertIn(f'[hooks.state."{mine}:a:0:0"]\ntrusted_hash = "sha256:aa"\n', text)
        self.assertNotIn(f'"{mine}:b:0:0"', text)
        self.assertNotIn(f'"{mine}:c:0:0"', text)
        self.assertIn(f'[hooks.state."{mine}:d:0:0"]\nenabled = true\ntrusted_hash = "sha256:dd"\n', text)
        self.assertIn('trusted_hash = "sha256:dd"\n\n[hooks.state', text)
        try:
            import tomllib
        except ImportError:
            return
        with open(real_conf, "rb") as f:
            self.assertIn(f"{mine}:d:0:0", tomllib.load(f)["hooks"]["state"])

    def test_status_waits_only_for_first_poll_after_login(self):
        data = self.codex_accounts()
        del data["accounts"]["cx2"]["email"]
        self.acm.save_json(self.acm.ACCOUNTS_FILE, data)
        calls = []

        def fake_poll(name, acc):
            # Reading worked, but there is no email, as with API key login
            calls.append(name)
            self.acm.save_json(os.path.join(self.acm.POLL_DIR, f"{name}.json"),
                               {"next_at": time.time() - 1, "ok_at": int(time.time()) + 1})
        self.acm.poll_account = fake_poll
        self.acm.status_snapshot(data)
        self.acm.status_snapshot(data)
        self.assertEqual(calls, ["cx2"])
        # After signing in again, it waits once more
        auth = os.path.join(self.home, ".codex-cx2", "auth.json")
        later = time.time() + 10
        os.utime(auth, (later, later))
        self.acm.status_snapshot(data)
        self.assertEqual(calls, ["cx2", "cx2"])

    def test_logged_out_codex_hides_old_plan(self):
        data = self.codex_accounts()
        self.codex_polled("cx2", [{"used_percentage": 10, "resets_at": 2000000000, "window_minutes": 10080}], plan="plus")
        os.unlink(os.path.join(self.home, ".codex-cx2", "auth.json"))
        snap = self.acm.status_snapshot(data)
        cx2 = next(a for a in snap["accounts"] if a["id"] == "cx2")
        self.assertEqual((cx2["email"], cx2["plan"]), (None, None))

    def test_poll_reads_app_server_and_remembers_account(self):
        data = self.codex_accounts()
        bindir = os.path.join(self.tmp, "bin")
        os.makedirs(bindir)
        fake = os.path.join(bindir, "codex")
        with open(fake, "w") as f:
            f.write(FAKE_CODEX % {"python": sys.executable})
        os.chmod(fake, 0o755)
        os.environ["PATH"] = bindir + os.pathsep + os.environ.get("PATH", "")
        open(os.path.join(self.home, ".codex-cx2", "logged-out"), "w").close()
        self.assertEqual(sorted(self.acm.run_poll(data, force=True)), ["cl1", "cx1", "cx2"])
        saved = self.acm.load_accounts()["accounts"]
        self.assertEqual((saved["cx1"]["email"], saved["cx1"]["plan"], saved["cx1"]["account_id"]),
                         (".codex@example.com", "plus", "id-.codex"))
        u = self.acm.account_usage("cx1", time.time())
        self.assertEqual((u["five"], u["seven"], u["source"]), (40, 20, "app-server"))
        self.assertIn("not signed in", self.acm.poll_note("cx2"))

    def test_status_waits_for_new_codex_login(self):
        data = self.codex_accounts()
        del data["accounts"]["cx2"]["email"]
        self.acm.save_json(self.acm.ACCOUNTS_FILE, data)
        calls = []

        def fake_poll(name, acc):
            calls.append(name)
            self.acm.remember_codex_identity(name, {"email": "new@chatgpt.test", "plan": "free", "account_id": "id-new"})
            self.codex_polled(name, [{"used_percentage": 0, "resets_at": 2000000000, "window_minutes": 43200}], plan="free")
        self.acm.poll_account = fake_poll
        snap = self.acm.status_snapshot(data)
        cx2 = next(a for a in snap["accounts"] if a["id"] == "cx2")
        self.assertEqual((calls, cx2["email"], cx2["plan"]), (["cx2"], "new@chatgpt.test", "free"))
        # Once the email is known, it does not wait again
        self.acm.status_snapshot(data)
        self.assertEqual(calls, ["cx2"])

    def test_status_groups_tools_and_names_window(self):
        data = self.codex_accounts()
        self.codex_polled("cx1", [{"used_percentage": 100, "resets_at": 2000000000, "window_minutes": 43200}],
                          allowed=False, plan="free")
        snap = self.acm.status_snapshot(data)
        self.assertEqual(snap["tools"], ["claude", "codex"])
        self.assertEqual(snap["next_by_tool"]["codex"]["id"], "cx2")
        cx1 = next(a for a in snap["accounts"] if a["id"] == "cx1")
        self.assertEqual((cx1["tool"], cx1["plan"], cx1["seven_day"]["name"], cx1["denied"]), ("codex", "free", "30d", True))
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.acm.cmd_status(data, [])
        text = out.getvalue()
        for part in ("[Claude]", "[Codex]", "30d 100%", "Next pick for Codex:", "cannot be used now"):
            self.assertIn(part, text)

    def test_launch_codex_sets_codex_home(self):
        data = self.codex_accounts()
        self.acm.codex_bin = lambda: "/fake/codex"
        calls = []

        class Exec(Exception):
            pass

        def execve(path, args, env):
            calls.append((path, args, env))
            raise Exec()
        real = os.execve
        os.execve = execve
        try:
            with self.assertRaises(Exec):
                self.acm.launch(data, ["-a", "cx2", "resume", "abc"])
            with self.assertRaises(Exec):
                self.acm.launch(self.acm.load_accounts(), [], tool="codex")
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                self.acm.launch(self.acm.load_accounts(), ["-a", "cx1"], tool="claude")
        finally:
            os.execve = real
        path, args, env = calls[0]
        self.assertEqual((path, args[1:]), ("/fake/codex", ["resume", "abc"]))
        self.assertEqual((env["CODEX_HOME"], env["ACM_CODEX_ACCOUNT"]), (os.path.join(self.home, ".codex-cx2"), "cx2"))
        self.assertTrue(os.path.islink(os.path.join(self.home, ".codex-cx2", "config.toml")))
        self.assertNotIn("CODEX_HOME", calls[1][2])
        self.assertEqual(calls[1][2]["ACM_CODEX_ACCOUNT"], "cx1")

    def test_bare_acm_asks_only_on_a_terminal(self):
        data = self.codex_accounts()

        class Tty(io.StringIO):
            def isatty(self):
                return True
        real_in, real_err = sys.stdin, sys.stderr
        try:
            sys.stderr = Tty()
            for answer, want in (("2\n", "codex"), ("\n", "claude"), ("codex\n", "codex"), ("", "claude")):
                sys.stdin = Tty(answer)
                self.assertEqual(self.acm.ask_tool(data), want)
            os.environ["TERMINAL_EMULATOR"] = "JetBrains-JediTerm"
            sys.stdin = Tty("2\n")
            self.assertEqual(self.acm.ask_tool(data), "claude")
        finally:
            sys.stdin, sys.stderr = real_in, real_err
        self.assertEqual(self.acm.ask_tool(data), "claude")
        self.assertIn('acm codex "$@"', self.acm.SHELL_INIT)
        self.assertIn('acm claude "$@"', self.acm.SHELL_INIT)

    @unittest.skipUnless(shutil.which("jq"), "jq is not installed")
    def test_statusline_never_maps_to_codex_root(self):
        data = {"mode": "usage", "order": ["cx1", "cl1"], "last": None,
                "accounts": {"cx1": {"tool": "codex", "dir": None}, "cl1": {"dir": None}}}
        self.acm.save_json(self.acm.ACCOUNTS_FILE, data)
        env = {k: v for k, v in os.environ.items() if k not in ("ACM_ACCOUNT", "CLAUDE_CONFIG_DIR")}
        subprocess.run(["sh", STATUSLINE], input=json.dumps({"rate_limits": {"seven_day": {"used_percentage": 7, "resets_at": 5}}}),
                       text=True, env=env, capture_output=True, check=True)
        self.assertTrue(os.path.exists(os.path.join(self.acm.USAGE_DIR, "cl1.json")))
        self.assertFalse(os.path.exists(os.path.join(self.acm.USAGE_DIR, "cx1.json")))


if __name__ == "__main__":
    unittest.main()
