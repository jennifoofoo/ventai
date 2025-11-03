# EnrichmentAgent - scrapes websites for more info
import requests
from bs4 import BeautifulSoup
import time
from typing import List, Dict, Optional


class EnrichmentAgent:
    # Optionally enriches startup data from websites
    
    def __init__(self, timeout: int = 5):
        # timeout: request timeout
        self.timeout = timeout
        self.status_callback = None
    
    def set_status_callback(self, callback):
        self.status_callback = callback
    
    def _update_status(self, message: str):
        if self.status_callback:
            self.status_callback(message)
    
    def _scrape_website_description(self, url: str) -> Optional[str]:
        # Try to scrape description from website
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            # Try /about pages
            about_urls = [
                url.rstrip('/') + '/about',
                url.rstrip('/') + '/about-us',
                url.rstrip('/') + '/company',
            ]
            urls_to_try = [url] + about_urls
            
            for attempt_url in urls_to_try:
                try:
                    response = requests.get(attempt_url, headers=headers, timeout=self.timeout, allow_redirects=True)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Remove script and style elements
                        for script in soup(["script", "style", "nav", "header", "footer"]):
                            script.decompose()
                        
                        description = None
                        
                        # Try meta description
                        meta_desc = soup.find('meta', property='og:description')
                        if meta_desc:
                            description = meta_desc.get('content', '')
                        
                        # Try paragraphs
                        if not description or len(description) < 50:
                            paragraphs = soup.find_all('p')
                            for p in paragraphs:
                                text = p.get_text(strip=True)
                                if len(text) > 100 and len(text) < 500:
                                    description = text
                                    break
                        
                        # Fallback
                        if not description or len(description) < 50:
                            text = soup.get_text(separator=' ', strip=True)
                            description = text[:300].strip()
                        
                        if description and len(description) > 50:
                            return description[:500]  # Limit length
                    
                except Exception:
                    continue
            
            return None
            
        except Exception as e:
            self._update_status(f"⚠️ Error scraping {url[:50]}: {str(e)[:30]}")
            return None
    
    def enrich_startups(self, startups: List[Dict[str, str]]) -> List[Dict[str, str]]:
        # Enrich startups by scraping their websites
        self._update_status("🌐 Starting website enrichment...")
        enriched = []
        
        for idx, startup in enumerate(startups, 1):
            url = startup.get('url', '')
            
            # Skip if no URL or already has good description
            if not url or (startup.get('description') and len(startup.get('description', '')) > 100):
                enriched.append(startup)
                continue
            
            self._update_status(f"🔍 Enriching {idx}/{len(startups)}: {startup.get('name', 'Unknown')[:40]}...")
            
            description = self._scrape_website_description(url)
            
            if description:
                startup['description'] = description
                startup['enriched'] = True
                self._update_status(f"✅ Enriched {startup.get('name', 'Unknown')[:40]}")
            else:
                startup['enriched'] = False
                self._update_status(f"⚠️ Could not enrich {startup.get('name', 'Unknown')[:40]}")
            
            enriched.append(startup)
            
            # Be polite with rate limiting
            time.sleep(0.5)
        
        enriched_count = sum(1 for s in enriched if s.get('enriched', False))
        self._update_status(f"✅ Enrichment complete: {enriched_count}/{len(startups)} startups enriched")
        
        return enriched

