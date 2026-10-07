#!/usr/bin/env python3
"""Parallel ranged downloader with resume (proxy-aware via urllib).
Usage: pdownload.py URL DEST [workers]"""
import sys, os, time, threading, urllib.request

def make_opener():
    # ProxyHandler() with no args reads *_proxy env vars automatically
    return urllib.request.build_opener(urllib.request.ProxyHandler(),
                                       urllib.request.HTTPSHandler())

def fetch(url, start, end, dest, idx, progress, opener):
    done = 0
    while start + done <= end:
        try:
            req = urllib.request.Request(
                url, headers={"Range": f"bytes={start+done}-{end}",
                              "User-Agent": "opendict-pipeline/1.0"})
            with opener.open(req, timeout=90) as resp:
                if resp.status not in (200, 206):
                    raise RuntimeError(f"HTTP {resp.status}")
                with open(dest, "r+b") as f:
                    while True:
                        chunk = resp.read(1 << 20)
                        if not chunk:
                            break
                        f.seek(start + done)
                        f.write(chunk)
                        done += len(chunk)
                        progress[idx] = done
            return
        except Exception as e:
            print(f"[worker {idx}] retry after error: {type(e).__name__}: {e}", flush=True)
            time.sleep(5)

def main():
    url, dest = sys.argv[1], sys.argv[2]
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    opener = make_opener()
    req = urllib.request.Request(url, method="HEAD",
                                 headers={"User-Agent": "opendict-pipeline/1.0"})
    with opener.open(req, timeout=60) as resp:
        total = int(resp.getheader("Content-Length"))
    have = os.path.getsize(dest) if os.path.exists(dest) else 0
    if have > total:
        have = 0
    if have == 0:
        open(dest, "wb").close()
    print(f"total={total} have={have} remaining={total-have}", flush=True)
    if have >= total:
        print("already complete")
        return
    remaining = total - have
    chunk = remaining // workers
    progress = [0] * workers
    threads = []
    for i in range(workers):
        s = have + i * chunk
        e = have + (i + 1) * chunk - 1 if i < workers - 1 else total - 1
        t = threading.Thread(target=fetch, args=(url, s, e, dest, i, progress, opener))
        t.start()
        threads.append(t)
    t0 = time.time()
    while any(t.is_alive() for t in threads):
        time.sleep(10)
        got = sum(progress)
        el = time.time() - t0
        rate = (got / 1e6 / el) if el > 0 else 0
        print(f"  +{got/1e6:.0f}MB / {remaining/1e6:.0f}MB  {rate:.1f} MB/s", flush=True)
    for t in threads:
        t.join()
    print(f"done: {os.path.getsize(dest)}/{total} bytes", flush=True)

if __name__ == "__main__":
    main()
