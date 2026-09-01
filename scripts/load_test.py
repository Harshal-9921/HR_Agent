import urllib.request, time
from concurrent.futures import ThreadPoolExecutor

URL = "http://localhost/"

def hit(_):
    t0 = time.time()
    try:
        with urllib.request.urlopen(URL, timeout=10) as r:
            r.read()
        return (True, time.time() - t0)
    except Exception:
        return (False, time.time() - t0)

for n in (10, 25, 50):
    with ThreadPoolExecutor(max_workers=n) as ex:
        t0 = time.time()
        results = list(ex.map(hit, range(n)))
        total = time.time() - t0
    ok = sum(1 for r in results if r[0])
    avg = sum(r[1] for r in results) / len(results)
    print(f"{n} concurrent -> {ok}/{n} succeeded, total {total:.2f}s, avg response {avg:.2f}s")