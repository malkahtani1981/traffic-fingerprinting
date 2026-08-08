"""End-to-end testing environment.

Runs the crawler generator, processes the captured directory dumps, and outputs
predictions using both advanced (crawler-aware) models.

    python run_pipeline.py
"""
import os

from advanced_industry_suite import AdvancedIndustrySuite
from advanced_academic_suite import AdvancedAcademicSuite


def main():
    # 1. Run the crawler script to visit links and populate local datasets
    print("[Pipeline] Step 1: Initializing Playwright crawler engine...")
    os.system("python crawler_generator.py")

    # 2. Build and run Version 1 (Industry Suite)
    print("\n[Pipeline] Step 2: Running Advanced Industry Standard (Object Chain Mapping)...")
    ind_suite = AdvancedIndustrySuite()
    ind_suite.train_baseline("dataset/training/banking_portal_crawl_1.mitm", "banking_portal")
    ind_suite.train_baseline("dataset/training/streaming_video_crawl_1.mitm", "streaming_video")
    ind_suite.train_baseline("dataset/training/wiki_news_crawl_1.mitm", "wiki_news")

    # Examine a separate iteration to evaluate accuracy performance
    ind_suite.inspect_unknown_traffic("dataset/training/banking_portal_crawl_2.mitm")

    # 3. Build and run Version 2 (Academic Suite)
    print("\n[Pipeline] Step 3: Running Advanced Academic Model (Statistical Flow Vectoring)...")
    acad_suite = AdvancedAcademicSuite()
    training_data = {
        0: ["dataset/training/banking_portal_crawl_1.mitm", "dataset/training/banking_portal_crawl_2.mitm"],
        1: ["dataset/training/streaming_video_crawl_1.mitm", "dataset/training/streaming_video_crawl_2.mitm"],
        2: ["dataset/training/wiki_news_crawl_1.mitm", "dataset/training/wiki_news_crawl_2.mitm"],
    }
    acad_suite.train_model(training_data)

    # Test ML precision against index run #3
    test_vector = acad_suite.extract_statistical_object_features(
        "dataset/training/wiki_news_crawl_3.mitm"
    ).reshape(1, -1)
    prediction = acad_suite.clf.predict(test_vector)
    confidence = max(acad_suite.clf.predict_proba(test_vector)[0]) * 100

    print(f"[Academic Result] ML Prediction: {acad_suite.labels[prediction[0]]} "
          f"({round(confidence, 2)}% Confidence)")


if __name__ == "__main__":
    main()
</content>
