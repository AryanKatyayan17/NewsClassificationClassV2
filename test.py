import time
import threading
from filter import Filter
from classify import Classify

def run_pipeline():
    start = Filter()

    feeds = start.fetch_articles()
    articles = start.extract_articles(feeds)
    geopolitical_articles = start.classify_articles(articles)

    saved_geopolitical_articles = start.save_articles(geopolitical_articles)

    if not saved_geopolitical_articles:
        print("No new articles found. Skipping threat classification.")
        return

    print(f"New articles to classify: {len(saved_geopolitical_articles)}")

    test = Classify()

    labelled_news_data = test.label_article(saved_geopolitical_articles)

    test.save_articles(labelled_news_data)

def background_worker():
    while True:
        print("\n--- Running News Pipeline ---\n")
        
        try:
            run_pipeline()
        except Exception as e:
            print(f"Pipeline error: {e}")

        print("\n--- Sleeping for 15 minutes ---\n")
        time.sleep(900)  # 900 seconds = 15 minutes

if __name__ == "__main__":
    worker_thread = threading.Thread(target=background_worker, daemon=True)
    worker_thread.start()

    print("Pipeline running in background...")

    while True:
        time.sleep(1)