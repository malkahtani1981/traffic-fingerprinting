# Traffic Fingerprinting Suite

A lab framework for building website traffic fingerprints from encrypted (TLS) traffic
metadata. It routes your browser through a local [mitmproxy](https://mitmproxy.org/)
instance, records the flows, and derives two kinds of fingerprints from the captured
metadata — without ever inspecting decrypted payloads.

> **Research / educational use only.** Only capture and fingerprint traffic you are
> authorized to observe (your own browsing on sites you control or that permit testing).

## Architecture

```
[ Your Browser ] ---> [ mitmproxy (Port 8080) ] ---> [ Live Internet ]
                             │
                             ▼ (Inline Python script)
                     [ matrix_dataset.csv ]
```

Your browser sends traffic through mitmproxy, which forwards it to the live internet.
An inline Python script observes every flow and writes size/timing metadata to a dataset
file. That dataset feeds the two fingerprinting suites below.

## Two fingerprinting approaches

### Version 1 — Industry standard (JA4+ style, deterministic hashing)
`industry_suite.py` and `advanced_industry_suite.py`

Modern suites moved past basic TLS 1.2 fingerprinting. They isolate stable, cleartext
protocol indicators (ALPN / HTTP version, cipher ordering, header structure, object
request order) into an exact deterministic string, then hash it. These hashes stay
static even if the target rotates session keys. Only one or two baseline runs are needed
because the signatures are deterministic.

### Version 2 — Academic (Random Forest classifier)
`academic_suite.py` and `advanced_academic_suite.py`

The academic framework targets cases where TLS fields are padded or shuffled. It extracts
a statistical vector — packet sizes, directions, relative timing, object burst
aggregates — and trains a Random Forest classifier. This needs multiple training samples
per site to establish statistical confidence.

## Install

```bash
pip install -r requirements.txt
# for the crawler-based data generator:
playwright install chromium
```

## Workflow

### 1. Capture a live dataset
Start the proxy and stream traffic to a file:

```bash
mitmdump -w traffic_capture.mitm
```

Configure your browser proxy to `127.0.0.1:8080`, visit the site variants you want to
fingerprint, then stop the proxy. `traffic_capture.mitm` now holds your raw flow
sequence.

To append a lightweight size profile per request into a CSV instead, run `capture.py` as
an inline mitmproxy addon:

```bash
mitmdump -s capture.py
```

### 2. Generate a labelled training set
Two generators are provided:

- **`train_collector.sh`** — a bash loop that fires `curl` through a temporary mitmdump
  instance, visiting 3 site targets 10 times each and writing one `.mitm` file per
  session into `dataset/training/`. Good for header/size baselines.

  ```bash
  chmod +x train_collector.sh
  ./train_collector.sh
  ```

- **`crawler_generator.py`** — a Playwright headless browser that renders each page,
  clicks a deep link, and waits for all sub-resources to load. This captures the
  cascading object-burst matrix a real browser produces, which `curl` cannot. Files land
  in `dataset/training/` as `<label>_crawl_<n>.mitm`.

  ```bash
  python crawler_generator.py
  ```

### 3. Run the pipeline
`run_pipeline.py` ties everything together: it runs the crawler, trains both advanced
suites on the generated captures, and prints predictions for held-out runs.

```bash
python run_pipeline.py
```

You can also run the baseline suites directly:

```bash
python industry_suite.py
python academic_suite.py
```

## Files

| File | Purpose |
| --- | --- |
| `capture.py` | Inline mitmproxy addon: appends per-request size profile to a CSV |
| `industry_suite.py` | V1 baseline — structural TLS/header hash fingerprint |
| `academic_suite.py` | V2 baseline — Random Forest on size/direction/timing vectors |
| `advanced_industry_suite.py` | V1 crawler-aware — deterministic object-chain hash |
| `advanced_academic_suite.py` | V2 crawler-aware — statistical object-burst vector + RF |
| `train_collector.sh` | curl-based session generator (10 runs × 3 sites) |
| `crawler_generator.py` | Playwright crawler-based session generator |
| `run_pipeline.py` | End-to-end training + evaluation wrapper |
| `live_inspect.py` | Live mitmproxy addon: prints each identified object (type/size/URL) in real time |

## Live experiment — use a VM as your browser proxy

Run the proxy on a VM, point your browser at it, and watch objects get identified in
real time as you browse. Provision the VM with the Terraform + Ansible in this repo (a
cloud VM is required — you need a public IP that accepts proxy connections).

**1. Create the VM and install the tools**

```bash
cd terraform && terraform init
terraform apply -var="cloud_provider=aws"        # or gcp | azure | do
# copy the printed ansible_inventory_line into ../ansible/inventory.ini
cd ../ansible && ansible-playbook -i inventory.ini playbook.yml
```

**2. Open the proxy port** — in your cloud firewall / security group, allow inbound TCP
`8080` from **your IP only**. Never leave it open to the world.

**3. Start the live inspector on the VM**

```bash
ssh ubuntu@<VM_PUBLIC_IP>
cd /opt/traffic-fingerprinting && source .venv/bin/activate
mitmdump -s live_inspect.py --listen-mode regular --listen-host 0.0.0.0 --listen-port 8080
```

It prints each identified object and appends rows to `identified_objects.csv`.

**4. Point your browser at the VM** — set the HTTP/HTTPS proxy to `<VM_PUBLIC_IP>:8080`
(Firefox: Settings → Network Settings → Manual proxy; enable "Also use this proxy for
HTTPS"). Firefox is easiest since its proxy is independent of the OS.

**5. Trust the mitmproxy certificate** (required to see HTTPS objects) — with the proxy
active, visit **http://mitm.it**, download the cert for your OS, and install it as a
trusted authority. Without it, HTTPS sites show cert errors and you only see `CONNECT`
metadata, not object types.

**6. Browse and watch** — visit any example site (e.g. `https://example.com`). Every
HTML, CSS, JS, image, font, and JSON object is listed live with its size as the page
loads:

```
[OBJECT #  1] HTML   |      559 B | text/html                | https://example.com/
[OBJECT #  4] IMAGE  |     8090 B | image/png                | https://.../image/png
[OBJECT #  6] JSON   |      429 B | application/json         | https://.../json
[OBJECT #  7] JS     |    87533 B | application/javascript   | https://.../jquery.min.js
```

**7. Turn a capture into a fingerprint**

```bash
mitmdump -w mysite.mitm --listen-host 0.0.0.0 --listen-port 8080
python3 -c "from advanced_industry_suite import AdvancedIndustrySuite as S; s=S(); print(s.extract_object_chain('mysite.mitm'))"
```

When finished: unset the browser proxy, remove the mitmproxy cert, and
`terraform destroy` the VM.

> **Note:** this must run on a real VM with a public IP. A path-based app proxy (such as a
> Replit preview) cannot forward the raw HTTP-proxy/CONNECT tunnel a browser needs.

## Notes on crawler operation

Switching from `curl` to Playwright means the dataset captures the burst matrix a real
browser generates while rendering a page. Even when the server rotates TLS session tickets
or shifts encryption keys on every deep link, the statistical model still fingerprints the
traffic by tracking metrics like total page weight and maximum object payload
(`max_object_loaded`).
