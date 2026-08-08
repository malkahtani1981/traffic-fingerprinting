"""Playwright-driven live crawl for the object-identification experiment.

This is the browser-based counterpart to the curl demo. Instead of firing individual
curl requests through the proxy, it launches a real headless Chromium routed through the
running `live_inspect.py` mitmdump proxy and browses like an organic user: it loads each
target page, waits for the network to go quiet (all sub-objects fetched), then clicks the
first internal link to crawl one level deeper. Every object the browser pulls -- HTML,
CSS, JS, images, fonts, JSON -- streams through the proxy and is identified live.

Usage:
    # Terminal 1 -- start the live inspector (prints each identified object)
    mitmdump -s live_inspect.py --listen-host 0.0.0.0 --listen-port 8080

    # Terminal 2 -- drive a real browser through it
    pip install playwright && playwright install chromium
    python live_crawl.py                      # uses default proxy 127.0.0.1:8080
    python live_crawl.py --proxy <VM_IP>:8080 --sites https://example.com https://httpbin.org/html

On a provisioned VM, point --proxy at the VM's public IP so the crawl exercises the same
path a real browser would.
"""
import argparse
import sys

from playwright.sync_api import sync_playwright

DEFAULT_SITES = [
    "https://example.com",
    "https://httpbin.org/html",
    "https://httpbin.org/json",
]


def crawl(proxy: str, sites: list[str], deep: bool) -> None:
    print(f"[live_crawl] routing a headless Chromium through http://{proxy}")
    print(f"[live_crawl] watch the mitmdump terminal for identified objects\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[f"--proxy-server=http://{proxy}"],
        )
        # ignore_https_errors lets the crawl work even before the mitmproxy CA is trusted
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        for url in sites:
            print(f"[live_crawl] visiting {url}")
            try:
                page.goto(url, wait_until="networkidle", timeout=15000)

                if deep:
                    link = page.locator("a").first
                    if link.count() > 0:
                        print("   -> clicking first internal link to crawl deeper...")
                        link.click(no_wait_after=True)
                        page.wait_for_load_state("networkidle", timeout=8000)
            except Exception as e:  # noqa: BLE001 - navigation timeouts are expected/handled
                print(f"   -> navigation warning (handled): {e}")

        browser.close()

    print("\n[live_crawl] done -- see the mitmdump output / identified_objects.csv")


def main() -> int:
    parser = argparse.ArgumentParser(description="Playwright live crawl through the proxy")
    parser.add_argument("--proxy", default="127.0.0.1:8080", help="host:port of the running mitmdump")
    parser.add_argument("--sites", nargs="+", default=DEFAULT_SITES, help="URLs to browse")
    parser.add_argument("--no-deep", action="store_true", help="skip clicking internal links")
    args = parser.parse_args()

    crawl(args.proxy, args.sites, deep=not args.no_deep)
    return 0


if __name__ == "__main__":
    sys.exit(main())
