"""Checks for the web edition (web/). There is no browser here, so these are contract tests:
the page, the script and the game must agree with each other. Run: cd tests && python -m unittest test_web -v
"""
import contextlib
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
WEB = os.path.join(ROOT, "web")


def read(name):
    with open(os.path.join(WEB, name), encoding="utf-8") as f:
        return f.read()


HTML, JS, CSS, SW = read("index.html"), read("app.js"), read("style.css"), read("sw.js")


def game_output(level, commands=(), final=False):
    """What the real game prints (plain text) when running these commands on a ticket."""
    os.environ["PENGUIN_SAVE"] = os.path.join(tempfile.mkdtemp(), "save.json")
    os.environ["PENGUIN_SEED"] = "0"
    from penguin.core import plain
    from penguin.shell import Shell
    sh = Shell()
    sh.fresh, sh.start_expert = False, False
    sh.width = lambda: 80
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        sh.start_level(level)
        for cmd in commands:
            sh.execute(cmd)
        if final:
            from penguin.tickets import TOTAL
            sh.level = TOTAL
            sh.complete()
    return plain(buf.getvalue())


class PageAndScript(unittest.TestCase):
    def test_every_id_the_script_uses_exists_in_the_page(self):
        ids = set(re.findall(r'\$\("([\w-]+)"\)', JS)) | set(re.findall(r'getElementById\("([\w-]+)"\)', JS))
        page = set(re.findall(r'\bid="([\w-]+)"', HTML))
        self.assertEqual(sorted(ids - page), [])

    def test_the_terminal_row_keeps_the_keys_a_shell_needs(self):
        keys = re.findall(r'data-k="([^"]*)"', HTML)
        for k in ["Kbd", "Tab", "^C", "^D", "|", "&gt;", "&lt;", "~", "/", "-", "$", "&quot;", "'", "Up", "Down"]:
            self.assertIn(k, keys)

    def test_the_text_box_does_not_open_the_phone_keyboard_by_default(self):
        self.assertRegex(HTML, r'<textarea id="input"[^>]*inputmode="none"')

    def test_the_input_font_is_16px_so_ios_does_not_zoom(self):
        self.assertRegex(CSS, r"#input\s*\{[^}]*font-size:16px")

    def test_keyboard_pages_have_the_standard_letters_and_digits(self):
        pages = dict(re.findall(r'(abc|num|sym): \[(.*?)\]', JS))
        letters = "".join(re.findall(r'"([^"]*)"', pages["abc"]))
        self.assertEqual(sorted(letters), sorted("qwertyuiopasdfghjklzxcvbnm"))
        self.assertTrue(set("0123456789") <= set(pages["num"]))

    def test_service_worker_caches_files_that_exist(self):
        core = re.search(r"const CORE = \[(.*?)\]", SW).group(1)
        for name in re.findall(r'"([^"]+)"', core):
            if name not in ("./", "penguin.zip"):          # the zip is built by tools/build_web.py
                self.assertTrue(os.path.exists(os.path.join(WEB, name)), name)

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_scripts_parse(self):
        for name in ("app.js", "sw.js"):
            r = subprocess.run(["node", "--check", os.path.join(WEB, name)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)


class ScriptReadsTheGame(unittest.TestCase):
    """The completion readout is triggered by text the Python game prints."""

    @classmethod
    def regex(cls, var):
        m = re.search(r"const %s = /(.+?)/[a-z]*\.(?:exec|test)\((?:text|plain)\)" % var, JS)
        assert m, var
        return re.compile(m.group(1))

    def test_objective_line_is_found_and_parsed(self):
        out = game_output(1, ["cat welcome.txt", "cd atlas", "cat README.md"])
        port = re.search(r"--port (\d+)", game_output(1, ["cat atlas/README.md"])).group(1)
        out = game_output(1, ["submit " + port])
        m = self.regex("m").search(out)
        self.assertIsNotNone(m, out)
        self.assertEqual((m.group(1), m.group(2)), ("Front Door", "ATL-101"))

    def test_final_mission_line_is_found(self):
        self.assertIsNotNone(self.regex("final").search(game_output(60, final=True)))

    def test_a_wrong_answer_does_not_trigger_the_readout(self):
        self.assertIsNone(self.regex("m").search(game_output(1, ["submit 1"])))


class GameMessages(unittest.TestCase):
    def test_answer_missions_say_how_to_submit(self):
        self.assertIn("submit ANSWER", game_output(1))

    def test_requirements_are_reported_as_they_are_met(self):
        out = game_output(4, ["cd atlas/app/features", "mkdir -p launch_date/templates", "touch launch_date/routes.py"])
        self.assertIn("Requirement met (1/4)", out)
        self.assertIn("Requirement met (2/4)", out)

    def test_first_mission_coaches_one_step_at_a_time_without_giving_the_answer(self):
        out = game_output(1, ["ls"])
        self.assertIn("Type  ls", out)
        self.assertIn("cat welcome.txt", out)
        self.assertNotIn("cd atlas", out)
        out = game_output(1, ["ls", "cat welcome.txt", "cd atlas", "cat README.md"])
        self.assertIn("submit NUMBER", out)
        port = re.search(r"--port (\d+)", out).group(1)
        self.assertNotIn("submit " + port, out.split("Found the port number")[-1])

    def test_coaching_stops_after_the_first_mission(self):
        self.assertNotIn("Pip:", game_output(2, ["ls"]))

    def test_next_mission_is_announced_after_a_completion(self):
        port = re.search(r"--port (\d+)", game_output(1, ["cat atlas/README.md"])).group(1)
        self.assertIn("ATL-102  Operation", game_output(1, ["submit " + port]))     # the next card follows


if __name__ == "__main__":
    unittest.main()
