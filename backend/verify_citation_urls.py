import urllib.request
import urllib.error
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

with open("backend/canonical_curriculum.json", "r", encoding="utf-8") as f:
    data = json.load(f)

sources = data.get("sources", [])
print(f"Total Sources to verify: {len(sources)}")

results = []
for s in sources:
    url = s["url"]
    sid = s["source_id"]
    title = s["title"]
    status_code = None
    error_msg = None
    
    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            status_code = resp.getcode()
    except urllib.error.HTTPError as e:
        status_code = e.code
    except Exception as e:
        error_msg = str(e)
        
    print(f"[{sid}] {status_code} | {url} | {error_msg or 'OK'}")
    results.append({
        "id": sid,
        "title": title,
        "url": url,
        "status": status_code,
        "error": error_msg
    })

print("\n--- Summary ---")
failed = [r for r in results if r["status"] not in (200, 301, 302, 307, 308, 403)]
for f in failed:
    print(f"FAIL: {f['id']} - {f['url']} -> {f['status']} {f['error']}")
