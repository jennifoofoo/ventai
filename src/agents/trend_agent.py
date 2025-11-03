# TrendAgent - Analyzes trends from multiple sources
import pandas as pd
import requests
import datetime
from typing import List, Dict, Optional
import time

try:
    from pytrends.request import TrendReq
    PTRENDS_AVAILABLE = True
except ImportError:
    PTRENDS_AVAILABLE = False
    print("⚠️ pytrends not available. Install with: pip install pytrends")


class TrendAgent:
    """Analyzes trend signals from Google Trends, GitHub, and Reddit."""
    
    def __init__(self, keywords: List[str], status_callback=None):
        """
        Initialize TrendAgent with keywords to analyze.
        
        Args:
            keywords: List of keywords/topics to track
            status_callback: Optional callback function for status updates
        """
        self.keywords = [k.strip().lower() for k in keywords if k.strip()]
        self.data = {}
        self.status_callback = status_callback
        if len(self.keywords) > 5:
            self.keywords = self.keywords[:5]  # Limit to 5 keywords for API limits
    
    def set_status_callback(self, callback):
        """Set callback function for status updates."""
        self.status_callback = callback
    
    def _log(self, message: str):
        """Log status message."""
        if self.status_callback:
            self.status_callback(message)
        print(message)
    
    def fetch_google_trends(self) -> pd.DataFrame:
        """
        Fetch Google Trends data for the keywords.
        
        Returns:
            DataFrame with columns: date, keyword, interest, source
        """
        if not PTRENDS_AVAILABLE:
            self._log("⚠️ pytrends not installed. Skipping Google Trends.")
            return pd.DataFrame(columns=['date', 'keyword', 'interest', 'source'])
        
        if not self.keywords:
            return pd.DataFrame(columns=['date', 'keyword', 'interest', 'source'])
        
        try:
            self._log("🔍 Fetching Google Trends data...")
            pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25))
            pytrends.build_payload(self.keywords, timeframe='today 3-m', geo='')
            
            df = pytrends.interest_over_time()
            if df.empty:
                self._log("⚠️ No Google Trends data available")
                return pd.DataFrame(columns=['date', 'keyword', 'interest', 'source'])
            
            # Reset index to get date as column
            df = df.reset_index()
            # Remove 'isPartial' column if present
            if 'isPartial' in df.columns:
                df = df.drop(columns=['isPartial'])
            
            # Melt to long format
            id_vars = ['date']
            value_vars = [col for col in df.columns if col != 'date']
            df = df.melt(id_vars=id_vars, value_vars=value_vars, 
                        var_name='keyword', value_name='interest')
            df['source'] = 'Google Trends'
            
            self._log(f"✅ Fetched Google Trends data for {len(df)} data points")
            return df
            
        except Exception as e:
            self._log(f"⚠️ Error fetching Google Trends: {str(e)}")
            return pd.DataFrame(columns=['date', 'keyword', 'interest', 'source'])
    
    def fetch_github_topics(self) -> pd.DataFrame:
        """
        Fetch GitHub repository data for keywords.
        
        Returns:
            DataFrame with columns: keyword, repo, stars, created, source
        """
        if not self.keywords:
            return pd.DataFrame(columns=['keyword', 'repo', 'stars', 'created', 'source'])
        
        try:
            self._log("💻 Checking GitHub repositories...")
            results = []
            
            for kw in self.keywords:
                try:
                    # Search for repositories with topic matching keyword
                    url = f"https://api.github.com/search/repositories?q={kw}&sort=updated&order=desc&per_page=10"
                    headers = {'Accept': 'application/vnd.github.v3+json'}
                    
                    resp = requests.get(url, headers=headers, timeout=10)
                    if resp.status_code == 200:
                        items = resp.json().get("items", [])
                        for item in items:
                            results.append({
                                "keyword": kw,
                                "repo": item.get("name", ""),
                                "full_name": item.get("full_name", ""),
                                "stars": item.get("stargazers_count", 0),
                                "created": item.get("created_at", ""),
                                "url": item.get("html_url", ""),
                                "description": item.get("description", ""),
                                "source": "GitHub"
                            })
                    elif resp.status_code == 403:
                        self._log(f"⚠️ GitHub API rate limit reached. Skipping GitHub data.")
                        break
                    else:
                        self._log(f"⚠️ GitHub API error for '{kw}': {resp.status_code}")
                    
                    # Small delay to avoid rate limiting
                    time.sleep(0.5)
                    
                except Exception as e:
                    self._log(f"⚠️ Error fetching GitHub data for '{kw}': {str(e)}")
                    continue
            
            df = pd.DataFrame(results)
            if not df.empty:
                self._log(f"✅ Fetched {len(df)} GitHub repositories")
            else:
                self._log("⚠️ No GitHub data found")
            return df
            
        except Exception as e:
            self._log(f"⚠️ Error in GitHub fetch: {str(e)}")
            return pd.DataFrame(columns=['keyword', 'repo', 'stars', 'created', 'source'])
    
    def fetch_reddit_trends(self) -> pd.DataFrame:
        """
        Fetch Reddit mentions using Pushshift API.
        
        Returns:
            DataFrame with columns: keyword, title, created, score, source
        """
        if not self.keywords:
            return pd.DataFrame(columns=['keyword', 'title', 'created', 'score', 'source'])
        
        try:
            self._log("🗞️ Gathering Reddit mentions...")
            results = []
            
            for kw in self.keywords:
                try:
                    # Pushshift API endpoint
                    url = f"https://api.pushshift.io/reddit/search/submission/"
                    params = {
                        'q': kw,
                        'after': '90d',  # Last 90 days
                        'size': 100,
                        'sort': 'score',
                        'sort_type': 'desc'
                    }
                    
                    resp = requests.get(url, params=params, timeout=10)
                    if resp.status_code == 200:
                        items = resp.json().get("data", [])
                        for item in items:
                            created_utc = item.get("created_utc", 0)
                            if created_utc:
                                created_dt = datetime.datetime.fromtimestamp(created_utc)
                            else:
                                created_dt = datetime.datetime.now()
                            
                            results.append({
                                "keyword": kw,
                                "title": item.get("title", "")[:200],  # Truncate long titles
                                "created": created_dt,
                                "score": item.get("score", 0),
                                "subreddit": item.get("subreddit", ""),
                                "url": item.get("url", ""),
                                "source": "Reddit"
                            })
                    elif resp.status_code == 429:
                        self._log(f"⚠️ Pushshift API rate limit. Skipping Reddit data.")
                        break
                    else:
                        self._log(f"⚠️ Pushshift API error for '{kw}': {resp.status_code}")
                    
                    # Small delay to avoid rate limiting
                    time.sleep(0.5)
                    
                except Exception as e:
                    self._log(f"⚠️ Error fetching Reddit data for '{kw}': {str(e)}")
                    continue
            
            df = pd.DataFrame(results)
            if not df.empty:
                self._log(f"✅ Fetched {len(df)} Reddit mentions")
            else:
                self._log("⚠️ No Reddit data found")
            return df
            
        except Exception as e:
            self._log(f"⚠️ Error in Reddit fetch: {str(e)}")
            return pd.DataFrame(columns=['keyword', 'title', 'created', 'score', 'source'])
    
    def run(self) -> pd.DataFrame:
        """
        Run all trend analysis and return combined results.
        
        Returns:
            Combined DataFrame with all trend data
        """
        self._log("📈 Starting trend analysis...")
        
        # Fetch from all sources
        google_df = self.fetch_google_trends()
        github_df = self.fetch_github_topics()
        reddit_df = self.fetch_reddit_trends()
        
        # Combine results
        dataframes = []
        if not google_df.empty:
            dataframes.append(google_df)
        if not github_df.empty:
            dataframes.append(github_df)
        if not reddit_df.empty:
            dataframes.append(reddit_df)
        
        if dataframes:
            combined = pd.concat(dataframes, ignore_index=True)
            self._log(f"✅ Trend analysis complete! Total data points: {len(combined)}")
            return combined
        else:
            self._log("⚠️ No trend data collected")
            return pd.DataFrame()

