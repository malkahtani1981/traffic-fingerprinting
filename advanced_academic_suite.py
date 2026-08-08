"""Version 2 (crawler-aware) — Statistical object profiling via ML.

A crawler triggers a flurry of multi-threaded requests, so packet bursts blend together.
This suite slices the session into an object-burst array and tracks aggregate metrics
(total transfer size, max object size, directional/frequency stats), then trains a
Random Forest classifier on those vectors.
"""
from mitmproxy.io import FlowReader
import numpy as np
from sklearn.ensemble import RandomForestClassifier


class AdvancedAcademicSuite:
    def __init__(self):
        self.clf = RandomForestClassifier(n_estimators=100)
        self.labels = {0: "banking_portal", 1: "streaming_video", 2: "wiki_news"}

    def extract_statistical_object_features(self, mitm_file):
        """Transform a full multi-page crawl into a statistical footprint vector."""
        object_sizes = []
        time_deltas = []
        last_t = None

        with open(mitm_file, "rb") as f:
            for flow in FlowReader(f).stream():
                if flow.response:
                    # Sizes of individual internal components (images, JS, assets)
                    body_size = len(flow.response.raw_content)
                    object_sizes.append(body_size)

                    t = flow.response.timestamp_end
                    time_deltas.append(t - last_t if last_t else 0.0)
                    last_t = t

        if not object_sizes:
            return np.zeros(6)

        # Object statistical aggregates
        total_page_weight = sum(object_sizes)
        max_object_loaded = max(object_sizes)
        avg_object_size = np.mean(object_sizes)
        total_objects_counted = len(object_sizes)
        avg_burst_delay = np.mean(time_deltas) if time_deltas else 0
        variance_of_objects = np.var(object_sizes) if len(object_sizes) > 1 else 0

        # Describes *what kind* of assets live inside the link
        return np.array([total_page_weight, max_object_loaded, avg_object_size,
                         total_objects_counted, avg_burst_delay, variance_of_objects])

    def train_model(self, file_map):
        X, y = [], []
        for label_idx, paths in file_map.items():
            for p in paths:
                vector = self.extract_statistical_object_features(p)
                X.append(vector)
                y.append(label_idx)
        self.clf.fit(np.array(X), np.array(y))
        print("[Academic Model] Machine Learning thresholds locked onto crawler metrics.")
