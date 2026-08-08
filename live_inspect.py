"""Live object inspector — mitmproxy addon.

Run:  mitmdump -s live_inspect.py --listen-port 8080

For every response that passes through the proxy it prints the identified object:
its category (html/css/js/image/font/json/other), content-type, request + response
sizes, and the URL. It also appends the same rows to identified_objects.csv so the
capture doubles as a dataset. No decrypted payload is inspected — only metadata.
"""
import time

CATEGORIES = [
    ("html", ("text/html", "application/xhtml")),
    ("css", ("text/css",)),
    ("js", ("javascript", "ecmascript")),
    ("json", ("application/json",)),
    ("image", ("image/",)),
    ("font", ("font/", "application/font", "application/vnd.ms-fontobject")),
    ("video", ("video/",)),
    ("audio", ("audio/",)),
]


def classify(content_type: str) -> str:
    ct = (content_type or "").lower()
    for label, needles in CATEGORIES:
        if any(n in ct for n in needles):
            return label
    return "other"


_count = 0


def response(flow):
    global _count
    _count += 1
    ct = flow.response.headers.get("Content-Type", "unknown").split(";")[0]
    category = classify(ct)
    req_size = len(flow.request.raw_content or b"")
    res_size = len(flow.response.raw_content or b"")
    url = flow.request.pretty_url

    print(f"[OBJECT #{_count:>3}] {category.upper():<6} | {res_size:>8} B | "
          f"{ct:<28} | {url}")

    with open("identified_objects.csv", "a") as f:
        f.write(f"{_count},{category},{ct},{req_size},{res_size},{time.time()},{url}\n")
