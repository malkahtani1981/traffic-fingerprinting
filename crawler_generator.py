"""Crawler-based data generator (replaces the curl loop).

Uses Playwright to open a real headless browser behind a per-session mitmdump proxy,
navigate to a target, click a deep link like an organic user, and wait for all
sub-resources (objects) to finish loading. This captures the cascading asset-load
sequence that curl cannot.

Install:
    pip install playwright
    playwright install chromium
"""
import os
import time
import subprocess

from playwright.sync_api import sync_playwright

TARGET_SITES = {
    "banking_portal": "https://httpbin.org",
    "streaming_video": "https://httpbin.org",
    "wiki_news": "https://httpbin.org",  # Generates multiple deep links to click
}


def capture_crawled_session(site_label, url, iteration):
    output_file = f"dataset/training/{site_label}_crawl_{iteration}.mitm"
    print(f"\n[Crawler] Recording session for {site_label} (Run #{iteration})...")

    # 1. Start a temporary headless mitmdump recorder for this specific crawl session
    proxy_port = "8082"
    mitm_process = subprocess.Popen(
        ["mitmdump", "--listen-port", proxy_port, "-w", output_file],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    time.sleep(1.5)  # Wait for proxy socket to bind safely

    # 2. Use Playwright to mimic a real browsing crawler and request internal objects
    with sync_playwright() as p:
        # Launch browser routed through our isolated proxy session
        browser = p.chromium.launch(
            headless=True,
            args=[f"--proxy-server=http://127.0.0.1:{proxy_port}"],
        )
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        try:
            # Navigate and wait until the network goes quiet (all objects loaded)
            page.goto(url, wait_until="networkidle", timeout=10000)

            # --- Crawl / deep interaction layer ---
            first_internal_link = page.locator("a").first
            if first_internal_link.count() > 0:
                print("   -> Clicking internal object link to crawl deeper...")
                first_internal_link.click(no_wait_after=True)
                page.wait_for_load_state("networkidle", timeout=5000)

        except Exception as e:
            print(f"   -> Navigation warning (handled): {e}")

        browser.close()

    # 3. Kill the proxy recorder to finalize writing data vectors to disk
    mitm_process.terminate()
    mitm_process.wait()


if __name__ == "__main__":
    os.makedirs("dataset/training", exist_ok=True)

    for round_num in range(1, 4):  # 3 baseline runs per site variation
        for label, target_url in TARGET_SITES.items():
            capture_crawled_session(label, target_url, round_num)
</content>
