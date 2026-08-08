"""Inline mitmproxy addon.

Run with:  mitmdump -s capture.py

The response() hook fires automatically every time the browser finishes receiving
data through the proxy. Each flow's size profile is appended to proxy_fingerprints.csv
so it can be used as a lightweight dataset.
"""
import time


def response(flow):
    """Triggered whenever a response is received through the proxy."""
    request_size = len(flow.request.raw_content or b"")
    response_size = len(flow.response.raw_content or b"")
    url = flow.request.pretty_url

    # Save the size profile straight to a CSV for your dataset
    with open("proxy_fingerprints.csv", "a") as f:
        f.write(f"{url},{request_size},{response_size},{time.time()}\n")
