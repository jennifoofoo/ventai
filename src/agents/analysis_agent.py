# AnalysisAgent - clusters and analyzes startups
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from typing import List, Dict, Optional
import numpy as np


class AnalysisAgent:
    # Clusters startups and generates insights
    
    def __init__(self, n_clusters: int = 5):
        # n_clusters: how many clusters to create
        self.n_clusters = n_clusters
        self.status_callback = None
        self.df = None
        self.clusters = None
    
    def set_status_callback(self, callback):
        self.status_callback = callback
    
    def _update_status(self, message: str):
        if self.status_callback:
            self.status_callback(message)
    
    def analyze(self, startups: List[Dict[str, str]]) -> pd.DataFrame:
        # Main analysis function - clusters startups
        if not startups:
            self._update_status("⚠️ No startups to analyze")
            return pd.DataFrame()
        
        self._update_status(f"📊 Analyzing {len(startups)} startups...")
        
        # Convert to DataFrame
        self.df = pd.DataFrame(startups)
        
        # Remove duplicates (case-insensitive)
        self.df['name_lower'] = self.df['name'].str.lower()
        self.df = self.df.drop_duplicates(subset=['name_lower'], keep='first')
        self.df = self.df.drop(columns=['name_lower'])
        
        self._update_status(f"📊 After deduplication: {len(self.df)} unique startups")
        
        # Do clustering if we have enough data
        if len(self.df) > 1:
            self._update_status("🔬 Clustering startups by description...")
            
            try:
                # Combine name + description for clustering
                texts = (self.df['name'] + ' ' + self.df['description']).fillna('')
                
                # Vectorize text
                vectorizer = TfidfVectorizer(
                    max_features=100,
                    stop_words='english',
                    ngram_range=(1, 2),
                    min_df=1
                )
                
                n_clusters = min(self.n_clusters, len(self.df))
                
                if n_clusters > 1 and len(texts) > n_clusters:
                    X = vectorizer.fit_transform(texts)
                    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                    self.clusters = kmeans.fit_predict(X)
                    self.df['cluster'] = self.clusters
                else:
                    self.df['cluster'] = 0
                    self._update_status("⚠️ Too few startups for clustering, all assigned to cluster 0")
                
                self._update_status(f"✅ Clustering complete: {n_clusters} clusters created")
                
            except Exception as e:
                self._update_status(f"⚠️ Clustering error: {str(e)}, assigning all to cluster 0")
                self.df['cluster'] = 0
        else:
            self.df['cluster'] = 0
        
        self._update_status("✅ Analysis complete")
        return self.df
    
    def get_summary_stats(self) -> Dict:
        # Get basic stats
        if self.df is None or len(self.df) == 0:
            return {}
        
        return {
            'total_startups': len(self.df),
            'unique_countries': self.df['country'].nunique(),
            'unique_categories': self.df['category'].nunique(),
            'clusters': self.df['cluster'].nunique() if 'cluster' in self.df.columns else 0
        }
    
    def generate_insights_summary(self) -> str:
        # Generate readable insights text
        if self.df is None or len(self.df) == 0:
            return "No data available for insights."
        
        insights = []
        
        # Top categories
        if 'category' in self.df.columns:
            top_categories = self.df['category'].value_counts().head(3)
            if len(top_categories) > 0:
                cat_names = ', '.join(top_categories.index.tolist())
                insights.append(f"Most startups focus on {cat_names}")
        
        # Top countries
        if 'country' in self.df.columns:
            top_countries = self.df['country'].value_counts().head(3)
            if len(top_countries) > 0:
                country_names = ', '.join(top_countries.index.tolist())
                insights.append(f"with strong presence in {country_names}")
        
        # Cluster info
        if 'cluster' in self.df.columns:
            n_clusters = self.df['cluster'].nunique()
            if n_clusters > 1:
                insights.append(f"Clustered into {n_clusters} distinct themes")
        
        # Total count
        insights.insert(0, f"Analysis of {len(self.df)} startups reveals:")
        
        summary = '. '.join(insights) + '.'
        return summary

