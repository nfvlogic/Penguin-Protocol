"""Different answers on every new game.

The tickets in tickets.py are the 'classic' version (seed 0, used by the tests). For any other seed,
levels_for(seed) copies them and re-rolls the data and the answers of the tickets listed in VARIANTS:
ports, versions, counts, file names, IP addresses... The seed is saved with your progress, so a game keeps
the same answers until you start a new one. Passwords do not depend on the seed.
"""
import copy
import random

from .core import HOME
from .tickets import LEVELS
from .tickets_data import (TST_CONFIG, gen_access, gen_costs, gen_deploy_log, gen_export, gen_incident, gen_migrations,
                           gen_sprint, gen_test_report, gen_traffic)


def swap(lv, old, new):
    """Replace a text everywhere in a ticket: files (names and content), answers, hint, texts."""
    def fix(x):
        if isinstance(x, str):
            return x.replace(old, new)
        if isinstance(x, tuple):
            return tuple(fix(i) for i in x)
        return x
    lv["files"] = {fix(k): fix(v) for k, v in lv["files"].items()}
    lv["answer"] = fix(lv["answer"])
    lv["hint"] = fix(lv["hint"])
    lv["brief"] = [fix(t) for t in lv["brief"]]
    lv["done"] = fix(lv["done"])
    if lv["parts"]:
        lv["parts"] = [(fix(q), fix(g) if not callable(g) else g) for q, g in lv["parts"]]


def swap_files(lv, files):
    lv["files"] = files


def pick_other(rng, options, current):
    return rng.choice([o for o in options if o != current])


# ------------------------------------------------------------------ the variants (one per ticket name)
def v_port(rng, lv):
    swap(lv, "5050", str(rng.randrange(5100, 6000)))


def v_tst_db(rng, lv):
    swap(lv, "atlas-db-02", f"atlas-db-{rng.choice([2, 4, 5, 6, 7, 8]):02d}")


def v_db_name(rng, lv):
    swap(lv, "atlas_dev", rng.choice(["atlas_local", "atlas_sandbox", "atlas_work", "atlas_main"]))


def v_rules(rng, lv):
    swap(lv, "g2-310", f"g{rng.randint(3, 6)}-{rng.randint(100, 999)}")
    swap(lv, "g1-100", f"g{rng.randint(1, 2)}-{rng.randint(10, 99)}")


def v_blocker(rng, lv):
    swap(lv, "approvals.py", rng.choice(["signoff.py", "gatekeeper.py", "reviews.py", "sign_off.py"]))


def v_app_log(rng, lv):
    swap(lv, "/requests/new", rng.choice(["/gates/approve", "/projects/create", "/reports/export", "/users/invite"]))


def v_deploy(rng, lv):
    version = f"v1.{rng.randint(5, 9)}.{rng.randint(0, 9)}"
    previous = pick_other(rng, [f"v1.{a}.{b}" for a in range(3, 5) for b in range(10)], version)
    lv["files"]["deploy.log"] = gen_deploy_log(version, previous)
    lv["answer"] = version


def v_tests(rng, lv):
    failed, xfailed = rng.randint(4, 9), rng.randint(2, 5)
    lv["files"]["test_report.txt"] = gen_test_report(failed, xfailed, rng)
    lv["answer"] = str(failed)


def v_secret(rng, lv):
    pool = ["__init__.py", "auth.py", "sso.py", "tokens.py", "session.py", "admin.py", "mailer.py"]
    n = rng.randint(2, 5)
    files = {f"atlas/app/{name}": 'key = config["SECRET_KEY"]' for name in rng.sample(pool, n)}
    files.update({"atlas/app/routes.py": "def projects():\n    return list_projects()",
                  "atlas/app/templates/admin.html": "<p>Rotate SECRET_KEY every 90 days</p>",
                  "atlas/tests/test_auth.py": 'SECRET_KEY = "test"', "atlas/docs/security.md": "The SECRET_KEY must never be committed.",
                  "atlas/.env": "SECRET_KEY=change-me"})
    lv["files"], lv["answer"] = files, str(n)


def v_migrations(rng, lv):
    dup = f"{rng.randint(5, 40):04d}"
    lv["files"]["migrations_list.txt"] = gen_migrations(dup, rng)
    lv["answer"] = dup


def v_access(rng, lv):
    endpoints = ["/api/requests", "/api/projects", "/api/gates"]
    broken = rng.choice(endpoints)
    others = [e for e in endpoints if e != broken]
    rng.shuffle(others)
    lv["files"]["access.log"] = gen_access(broken, tuple(others), rng)
    lv["answer"] = broken


def v_export(rng, lv):
    rows = gen_export(rng)
    lv["files"]["tickets_export.csv"] = "\r\n".join(rows)
    opens = str(sum(r.endswith(",open") for r in rows))
    lv["parts"] = [(lv["parts"][0][0], lambda g, rows=rows: g.fs.d.get(HOME + "/clean.csv", "\r").split("\n") == rows),
                   (lv["parts"][1][0], opens)]


def v_diff(rng, lv):
    name = rng.choice(["POOL_SIZE", "CACHE_TTL", "SESSION_MINUTES", "MAX_UPLOAD_MB"])
    base = {"POOL_SIZE": 5, "CACHE_TTL": 30, "SESSION_MINUTES": 30, "MAX_UPLOAD_MB": 20}
    pv = base[name] + rng.choice([5, 10, 15, 25])
    values_prd = dict(base, **{name: pv})
    values_tst = dict(base)

    def body(host, db, debug, values):
        return f'DB_HOST = "{host}"\nDB_NAME = "{db}"\nDEBUG = {debug}\n' + "\n".join(f"{k} = {v}" for k, v in values.items())
    lv["files"] = {"atlas/config/tst.py": body("atlas-db-02", "atlas_tst", True, values_tst),
                   "atlas/config/prd.py": body("atlas-db-03", "atlas", False, values_prd)}
    lv["parts"] = [(lv["parts"][0][0], name), (lv["parts"][1][0], str(pv))]


def v_move_db(rng, lv):
    old = f"atlas-db-{rng.choice([2, 4, 5, 6]):02d}"
    new = rng.choice(["atlas-db-new", "atlas-db-green", "atlas-db-v2"])
    original = TST_CONFIG.replace("atlas-db-02", old)
    expected = original.replace(old, new)
    swap(lv, "atlas-db-02", old)
    swap(lv, "atlas-db-new", new)
    lv["files"]["atlas/config/tst.py"] = original
    lv["checks"] = [
        ("tst.py.bak is a copy of the original", lambda g: g.fs.d.get(HOME + "/atlas/config/tst.py.bak") == original),
        (f"tst.py uses {new} in both lines and nothing else changed", lambda g: g.fs.d.get(HOME + "/atlas/config/tst.py") == expected),
        ("prd.py was not touched", lambda g: "atlas-db-03/atlas\"" in g.fs.d.get(HOME + "/atlas/config/prd.py", ""))]


def v_traffic(rng, lv):
    top = rng.choice(["10.20.30.52", "10.20.30.71", "10.20.30.88", "10.20.30.93"])
    rows = gen_traffic(rng, top)
    count = str(sum(r.split()[3] == "404" for r in rows))
    total = str(sum(int(r.split()[4][:-2]) for r in rows if r.startswith(top + " ")))
    lv["files"]["traffic.log"] = "\n".join(rows)
    lv["parts"] = [(lv["parts"][0][0], count), (lv["parts"][1][0], top), (lv["parts"][2][0], total)]
    lv["hint"] = lv["hint"].replace("10.20.30.66", top)


def v_costs(rng, lv):
    rows = gen_costs(rng)
    prd = sum(int(r.split(",")[2]) for r in rows[1:] if r.split(",")[1] == "prd")
    by = {}
    for r in rows[1:]:
        service, _, value = r.split(",")
        by[service] = by.get(service, 0) + int(value)
    ranked = sorted(by.values(), reverse=True)
    if ranked[0] == ranked[1]:                    # keep one clear winner
        top = max(by, key=by.get)
        rows = [r + "0" if r.startswith(top + ",") and r.endswith(",tst") and False else r for r in rows]
        by[top] += 10
        rows.append(f"{top},prd,10")
        prd += 10
    lv["files"]["costs.csv"] = "\n".join(rows)
    lv["parts"] = [(lv["parts"][0][0], str(prd)), (lv["parts"][1][0], max(by, key=by.get))]


def v_incident(rng, lv):
    errors = rng.randint(4, 10)      # the generated log has room for 10 errors at most
    lv["files"] = gen_incident("atlas-db-02", errors)
    lv["answer"] = str(errors)


def v_disk(rng, lv):
    names = rng.sample(["uploads", "cache", "exports", "media", "backups", "thumbs", "reports"], 4)
    big, decoy, other, empty = names
    unit = rng.choice([40000, 50000, 60000])
    files = {**{f"data/{decoy}/d{i}.bin": "x" * 9000 for i in range(1, 6)},
             **{f"data/{big}/b{i}.bin": "x" * unit for i in (1, 2)},
             **{f"data/{other}/o{i}.csv": "x" * 5000 for i in (1, 2, 3)}, f"data/{empty}/": ""}
    size = (4096 + 2 * -(-unit // 4096) * 4096) // 1024
    lv["files"] = files
    lv["parts"] = [(lv["parts"][0][0], big), (lv["parts"][1][0], str(size))]
    lv["hint"] = "du -s data/* | sort -n -r | head -n 1"


def v_sprint(rng, lv):
    workflow, biggest = rng.randint(8, 14), rng.choice([20, 21, 34])
    text = gen_sprint(workflow, biggest, rng)
    lines = [l for l in text.splitlines() if ",workflow," in l]
    from .tickets_data import wf_check
    lv["files"]["sprint.csv"] = text
    lv["parts"] = [(lv["parts"][0][0], str(workflow)), (lv["parts"][1][0], str(biggest)),
                   (lv["parts"][2][0], wf_check(lines))]


VARIANTS = {
    "Run Atlas locally": v_port, "Which database does TST use?": v_tst_db, "App fails to start": v_db_name,
    "Which gate rules are active?": v_rules, "Release blocker hunt": v_blocker, "500 errors on TST": v_app_log,
    "What is deployed on TST?": v_deploy, "Failing unit tests": v_tests, "Who reads the secret key?": v_secret,
    "Migration conflict": v_migrations, "Which endpoint is broken?": v_access, "Export from Windows": v_export,
    "TST is not like PRD": v_diff, "Move TST to the new database": v_move_db, "Who keeps asking for missing pages?": v_traffic,
    "Cloud costs per environment": v_costs, "Slow database incident": v_incident, "Who ate the disk?": v_disk,
    "Sprint review numbers": v_sprint,
}


def levels_for(seed):
    """The 50 tickets for a game. Seed 0 is the classic version used by the tests."""
    if not seed:
        return LEVELS
    levels = copy.deepcopy(LEVELS)
    for lv in levels:
        variant = VARIANTS.get(lv["name"])
        if variant:
            variant(random.Random(f"{seed}:{lv['name']}"), lv)
    return levels
