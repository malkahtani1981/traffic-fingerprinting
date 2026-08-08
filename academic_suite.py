"""Version 2 — Academic (Random Forest classifier matrix).

Targets situations where TLS fields might be randomly padded or shuffled. Extracts a
vector of sizes, directions, and relative timing to feed a Random Forest classifier.
"""
from mitmproxy.io import FlowReader
from sklearn.ensemble import RandomForestClassifier
import numpy as np


class AcademicFingerprintSuite:
    def __init__(self):
        self.classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.label_mapping = {0: "banking_portal", 1: "streaming_video", 2: "wiki_news"}

    def extract_flow_features(self, pcap_mitm_file):
        """
        Convert the flow sequence into a consistent multi-dimensional matrix.
        Isolates packet size, direction, and timing deltas.
        """
        features = []
        last_time = None

        with open(pcap_mitm_file, "rb") as f:
            reader = FlowReader(f)
            for flow in reader.stream():
                # Directional payloads
                req_size = len(flow.request.raw_content) if flow.request else 0
                res_size = len(flow.response.raw_content) if flow.response else 0

                # Statistical timing parameters
                current_time = flow.request.timestamp_start if flow.request else 0
                time_delta = (current_time - last_time) if last_time else 0.0
                last_time = current_time

                # [request size, response size, inter-arrival delta]
                features.extend([req_size, res_size, round(time_delta, 4)])

                if len(features) >= 15:  # Fix to exactly 5 session iterations (15 elements)
                    break

        # Pad with zeros if the sequence ended early to keep matrix shape stable
        while len(features) < 15:
            features.append(0)

        return np.array(features)

    def train_academic_model(self, sample_files_dict):
        """
        Train the Random Forest model on multiple session arrays.
        sample_files_dict format: { 0: ["bank_1.mitm", "bank_2.mitm"], 1: [...] }
        """
        X_train = []
        y_train = []

        for label_idx, file_list in sample_files_dict.items():
            for file_path in file_list:
                vector = self.extract_flow_features(file_path)
                X_train.append(vector)
                y_train.append(label_idx)

        self.classifier.fit(np.array(X_train), np.array(y_train))
        print("[Academic Model] Statistical training thresholds successfully locked.")

    def examine_live_traffic(self, unknown_mitm_file):
        """Run the vector through statistical checks to determine the matching target."""
        vector = self.extract_flow_features(unknown_mitm_file).reshape(1, -1)

        prediction = self.classifier.predict(vector)[0]
        probabilities = self.classifier.predict_proba(vector)[0]
        confidence = round(probabilities[prediction] * 100, 2)

        print("\n[ML Analysis Results]")
        print(f" -> Predicted Target Variant: {self.label_mapping[prediction]}")
        print(f" -> Mathematical Confidence Threshold: {confidence}%")


# --- Initializing execution framework ---
if __name__ == "__main__":
    suite_v2 = AcademicFingerprintSuite()

    # Build the training sample array mappings using the generated file names.
    # training_data_map = {
    #     0: [f"dataset/training/banking_portal_session_{x}.mitm" for x in range(1, 11)],
    #     1: [f"dataset/training/streaming_video_session_{x}.mitm" for x in range(1, 11)],
    #     2: [f"dataset/training/wiki_news_session_{x}.mitm" for x in range(1, 11)],
    # }
    # suite_v2.train_academic_model(training_data_map)

    print("[System] Academic Suite initialized using Machine Learning feature scaling arrays.")
</content>
