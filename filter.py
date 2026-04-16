import os
import json
import feedparser
from newspaper import Article
from transformers import pipeline
from tqdm import tqdm

OUTPUT_FILE = "test_filtered_news.json"

class Filter:
    def __init__(self):
        self.LABELS = [
            "geopolitics",
            "business/economics",
            "technology",
            "sports",
            "entertainment"
        ]
        self.RSS_FEEDS = [
            "https://feeds.bbci.co.uk/news/world/rss.xml", # get all the rss feed links from 'feeds.py', one link used for testing purpose
        ]
        self.THRESHOLD = 0.3

        self.classifier = None

    def get_classifier(self):
        if self.classifier is None:
            self.classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=0
            )
        return self.classifier

    def remove_duplicates(self,articles):
        if not os.path.exists(OUTPUT_FILE):
            return articles
        
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            data=json.load(f)

        existing_urls ={article["url"] for article in data}

        filtered_articles = [
            article for article in articles
            if article["url"] not in existing_urls
        ]

        return filtered_articles

    def fetch_articles(self):
        articles=[]
        seen_urls=set()

        for url in self.RSS_FEEDS:
            feed = feedparser.parse(url)

            for entry in feed.entries:
                link = entry.get("link")

                if link and link not in seen_urls:
                    seen_urls.add(link)

                    article_data={
                        "url": link,
                        "title": entry.get("title", ""),
                        "published": entry.get("published", ""),
                        "source": feed.feed.get("title")
                    }

                    articles.append(article_data)

        #Check for duplicates
        remove_duplicates=self.remove_duplicates(articles)

        return remove_duplicates
    
    def extract_article_details(self,article_meta):
        url = article_meta["url"]

        try:
            article=Article(url)
            article.download()
            article.parse()

            text=article.text.strip()

            if len(text.split()) < 100:
                return None

            return {
                "url": url,
                "title": article.title if article.title else article_meta.get("title", ""),
                "text": text,
                "publish_date": str(article.publish_date) if article.publish_date else article_meta.get("published", ""),
                "source": article_meta.get("source", "")
            }
        
        except Exception as e:
            print(f"Error processing {url}: {e}")
            return None
        
    def extract_articles(self,articles_meta):
        extracted_articles = []

        for meta in tqdm(articles_meta, desc="Extracting articles"):
            article = self.extract_article_details(meta)

            if article:
                extracted_articles.append(article)

        return extracted_articles

        
    def prepare_input_text(self,title, text, max_words=300):
        # Take first 300 words from article
        words = text.split()
        truncated_text = " ".join(words[:max_words])
        
        # Combine title + truncated article
        input_text = f"{title}. {truncated_text}"
        
        return input_text
    
    def loop_classify_article(self,article, classifier, LABELS, THRESHOLD):
        input_text = self.prepare_input_text(article["title"], article["text"])

        result = self.get_classifier()(input_text, self.LABELS)

        top_label = result["labels"][0]
        top_score = result["scores"][0]

        # Determine if it's geopolitics
        is_geopolitics = (top_label == "geopolitics") and (top_score > THRESHOLD)

        return {
            "label": top_label,
            "score": float(top_score),
            "is_geopolitics": is_geopolitics
        }
    
    def classify_articles(self,articles):
        processed_articles = []
        for article in tqdm(articles, desc="Filtering Geopolitical articles"):
            classification = self.loop_classify_article(
                article,
                self.classifier,
                self.LABELS,
                self.THRESHOLD
            )
            
            # Merge article data + classification
            enriched_article = {
                **article,
                "classification": classification
            }
            
            processed_articles.append(enriched_article)


        geopolitical_articles=[
            article for article in processed_articles
            if article["classification"]["is_geopolitics"]
        ]

        return geopolitical_articles
    
    def save_articles(self,articles):
        if os.path.exists(OUTPUT_FILE):
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                existing_data=json.load(f)
        else:
            existing_data=[]

        existing_data.extend(articles)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)

        return articles

    def run_pipeline(self, rss_urls):
        articles_meta = self.fetch_articles(rss_urls)
        extracted_articles = self.extract_articles(articles_meta)
        classified_articles = self.classify_articles(extracted_articles)
        saved_articles=self.save_articles(classified_articles)

        return saved_articles