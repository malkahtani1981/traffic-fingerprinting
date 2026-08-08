#!/bin/bash

# Define the target website variants you want to fingerprint
WEBSITES=("banking_portal" "streaming_video" "wiki_news")
URLS=("https://httpbin.org" "https://httpbin.org" "https://httpbin.org")

# Create a clean folder directory structure for your dataset matrices
mkdir -p dataset/training
mkdir -p dataset/testing

echo "[System] Starting automated proxy traffic generation..."

# Loop 10 times to capture 10 distinct network sessions per site variant
for iteration in {1..10}
do
    echo "--------------------------------------------"
    echo "Starting Data Capture Iteration Round: #$iteration"
    echo "--------------------------------------------"

    # Iterate through each defined site option
    for i in "${!WEBSITES[@]}"
    do
        SITE_NAME=${WEBSITES[$i]}
        TARGET_URL=${URLS[$i]}

        OUTPUT_FILE="dataset/training/${SITE_NAME}_session_${iteration}.mitm"

        echo " -> Target: ${SITE_NAME} | Fetching profile stream data..."

        # 1. Start a temporary mitmdump recording instance for this session loop.
        #    Runs on port 8081 to avoid conflicts with your main proxy tab.
        mitmdump --listen-port 8081 -w "$OUTPUT_FILE" &
        MITM_PID=$!

        # Give the proxy process a moment to bind to the port cleanly
        sleep 1

        # 2. Fire curl through the proxy to capture header lengths and payload sizes.
        #    -x sets the proxy server, -s silences progress, -L follows redirects.
        curl -x http://127.0.0.1:8081 -s -L "$TARGET_URL" -o /dev/null \
             -H "User-Agent: Mozilla/5.0 (Test-ISP-Scanner-v1)" \
             -H "Accept-Language: en-US,en;q=0.9"

        # Give the proxy a brief moment to flush buffered bytes to disk
        sleep 1

        # 3. Terminate this specific session recording process
        kill $MITM_PID
        wait $MITM_PID 2>/dev/null
    done
done

echo "[System] Data gathering complete. Files are saved in dataset/training/"
</content>
