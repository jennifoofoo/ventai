# ResearchAgent - fetches RSS feeds and OpenVC data
import feedparser
import requests
import json
import time
from typing import List, Dict, Optional
from pathlib import Path
import sys

# Add src to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import (
    FEEDS_BY_TOPIC, OPENVC_LOCAL_PATH, OPENVC_GITHUB_URL,
    DATA_DIR, RSS_ARTICLES_PATH
)


class ResearchAgent:
    # Fetches RSS feeds and OpenVC data
    
    def __init__(self, max_entries_per_feed: int = 30, timeout: int = 10):
        # max_entries_per_feed: how many articles per feed
        # timeout: request timeout
        self.max_entries_per_feed = max_entries_per_feed
        self.timeout = timeout
        self.status_callback = None
    
    def set_status_callback(self, callback):
        self.status_callback = callback
    
    def _update_status(self, message: str):
        if self.status_callback:
            self.status_callback(message)
    
    def _fetch_rss_feed(self, feed_url: str) -> List[Dict[str, str]]:
        # Fetch RSS feed and parse it
        articles = []
        
        try:
            self._update_status(f"📡 Fetching RSS feed: {feed_url[:60]}...")
            
            # TODO: maybe add caching here later
            feed = feedparser.parse(feed_url)
            
            if feed.bozo and feed.bozo_exception:
                # Feed parsing failed, skip it
                self._update_status(f"⚠️ RSS parsing error: {str(feed.bozo_exception)[:50]}")
                return articles
            
            entries = feed.entries[:self.max_entries_per_feed]
            
            for entry in entries:
                article = {
                    'title': entry.get('title', 'No title'),
                    'url': entry.get('link', ''),
                    'content': entry.get('summary', entry.get('description', '')),
                    'published': entry.get('published', entry.get('updated', 'Unknown')),
                    'source': feed_url
                }
                
                if article['content'] and len(article['content']) > 50:
                    articles.append(article)
            
            self._update_status(f"✅ Fetched {len(articles)} articles from RSS feed")
            
        except Exception as e:
            self._update_status(f"⚠️ Error fetching RSS feed: {str(e)[:50]}")
        
        return articles
    
    def _load_openvc_dataset(self) -> List[Dict[str, str]]:
        # Try to load OpenVC dataset from local file or GitHub
        startups = []
        
        try:
            self._update_status("📂 Loading OpenVC dataset...")
            
            # Check local file first
            if OPENVC_LOCAL_PATH.exists():
                with open(OPENVC_LOCAL_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    items = data
                elif isinstance(data, dict):
                    items = data.get('startups', data.get('data', [data]))
                else:
                    items = []
                
                for item in items:
                    if isinstance(item, dict):
                        startup = {
                            'title': item.get('name', item.get('title', 'Unknown Startup')),
                            'url': item.get('url', item.get('website', '')),
                            'content': item.get('description', item.get('summary', '')),
                            'published': item.get('founded', item.get('date', 'Unknown')),
                            'source': 'OpenVC'
                        }
                        
                        if startup['content'] and len(str(startup['content'])) > 50:
                            startups.append(startup)
                
                self._update_status(f"✅ Loaded {len(startups)} startups from local OpenVC dataset")
                
            else:
                # Fallback to GitHub
                try:
                    self._update_status("📡 Fetching OpenVC dataset from GitHub...")
                    response = requests.get(OPENVC_GITHUB_URL, timeout=self.timeout)
                    
                    if response.status_code == 200:
                        data = response.json()
                        # Process same as local file
                        if isinstance(data, list):
                            items = data
                        else:
                            items = data.get('startups', data.get('data', []))
                        
                        for item in items:
                            if isinstance(item, dict):
                                startup = {
                                    'title': item.get('name', 'Unknown Startup'),
                                    'url': item.get('url', item.get('website', '')),
                                    'content': item.get('description', item.get('summary', '')),
                                    'published': item.get('founded', 'Unknown'),
                                    'source': 'OpenVC'
                                }
                                
                                if startup['content'] and len(str(startup['content'])) > 50:
                                    startups.append(startup)
                        
                        self._update_status(f"✅ Loaded {len(startups)} startups from GitHub")
                    else:
                        self._update_status(f"⚠️ Could not fetch from GitHub: {response.status_code}")
                        
                except Exception as e:
                    self._update_status(f"⚠️ Error fetching from GitHub: {str(e)[:50]}")
            
        except Exception as e:
            self._update_status(f"⚠️ Error loading OpenVC dataset: {str(e)[:50]}")
        
        return startups
    
    def fetch_all_sources(self, feed_category: str = "General Startups", 
                         include_openvc: bool = True) -> List[Dict[str, str]]:
        # Main function to fetch RSS feeds and optionally OpenVC
        self._update_status(f"🔍 Starting multi-source data collection for '{feed_category}'...")
        all_data = []
        
        # Fetch RSS feeds for the category
        if feed_category in FEEDS_BY_TOPIC:
            feeds = FEEDS_BY_TOPIC[feed_category]
            self._update_status(f"📡 Loading {len(feeds)} feeds for '{feed_category}'...")
            
            for feed_url in feeds:
                articles = self._fetch_rss_feed(feed_url)
                all_data.extend(articles)
            
            rss_count = len(all_data)
            self._update_status(f"📰 Collected {rss_count} articles from RSS feeds")
        else:
            self._update_status(f"⚠️ Unknown category '{feed_category}', using 'General Startups'")
            feeds = FEEDS_BY_TOPIC["General Startups"]
            for feed_url in feeds:
                articles = self._fetch_rss_feed(feed_url)
                all_data.extend(articles)
        
        # Optionally add OpenVC data
        openvc_count = 0
        if include_openvc:
            startups = self._load_openvc_dataset()
            all_data.extend(startups)
            openvc_count = len(startups)
            self._update_status(f"📂 Added {openvc_count} entries from OpenVC dataset")
        
        # Save combined results
        self._save_articles(all_data)
        
        total_count = len(all_data)
        self._update_status(f"✅ Research complete: {total_count} data points collected ({rss_count} RSS + {openvc_count} OpenVC)")
        
        return all_data
    
    def _save_articles(self, articles: List[Dict[str, str]]):
        # Save articles to JSON file
        try:
            RSS_ARTICLES_PATH.parent.mkdir(exist_ok=True)
            
            with open(RSS_ARTICLES_PATH, 'w', encoding='utf-8') as f:
                json.dump(articles, f, indent=2, ensure_ascii=False)
            
            self._update_status(f"💾 Saved {len(articles)} articles to data/rss_articles.json")
            
        except Exception as e:
            self._update_status(f"⚠️ Error saving articles: {str(e)[:50]}")
