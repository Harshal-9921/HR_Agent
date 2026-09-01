import os
import json
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

BASE_URL = os.environ.get("LOAD_TEST_BASE_URL", "http://localhost")
USERNAME = os.environ.get("LOAD_TEST_USERNAME")
PASSWORD = os.environ.get("LOAD_TEST_PASSWORD")

if not USERNAME or not PASSWORD:
    print("Set LOAD_TEST_USERNAME and LOAD_TEST_PASSWORD environment variables first.")
    raise SystemExit(1)


def do_login():
    t0 = time.time()
    data = json.dumps({"username": USERNAME, "password": PASSWORD}).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/api/auth/login",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            body = json.loads(r.read())
            return True, time.time() - t0, body.get("access_token")
    except Exception as e:
        return False, time.time() - t0, None


def do_authed_get(token, path):
    t0 = time.time()
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            r.read()
            return True, time.time() - t0
    except Exception:
        return False, time.time() - t0


def run_phase(label, fn, n):
    with ThreadPoolExecutor(max_workers=n) as ex:
        t0 = time.time()
        results = list(ex.map(fn, range(n)))
        total = time.time() - t0
    oks = [r for r in results if r[0]]
    times = [r[1] for r in results]
    print(
        f"{label} | n={n:>3} | {len(oks)}/{n} succeeded | "
        f"avg={sum(times)/len(times):.2f}s | max={max(times):.2f}s | wall={total:.2f}s"
    )


print("=== Phase A: Login endpoint concurrency ===")
for n in (10, 25, 50, 100):
    run_phase("LOGIN", lambda _: do_login(), n)

print()
print("=== Phase B: Authenticated read endpoint concurrency ===")
ok, _, token = do_login()
if not ok or not token:
    print("Could not obtain a token for Phase B — skipping.")
else:
    for n in (10, 25, 50, 100):
        run_phase("READ ", lambda _: do_authed_get(token, "/api/content/"), n)