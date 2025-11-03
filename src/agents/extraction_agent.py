# ExtractionAgent - extracts startup info using Ollama
import subprocess
import json
import re
from typing import List, Dict, Optional

CHUNK_SIZE = 5  # Process 5 articles at once (could be configurable)


class ExtractionAgent:
    # Extracts startup info from articles using Ollama
    
    def __init__(self, model: str = "mistral"):
        # model: which ollama model to use (default: mistral)
        self.model = model
        self.status_callback = None
    
    def set_status_callback(self, callback):
        self.status_callback = callback
    
    def _update_status(self, message: str):
        if self.status_callback:
            self.status_callback(message)
    
    def _call_ollama(self, prompt: str) -> str:
        # Call ollama via subprocess
        try:
            # Make sure it's a string
            if isinstance(prompt, bytes):
                prompt = prompt.decode('utf-8')
            
            process = subprocess.run(
                ["ollama", "run", self.model],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=120,  # Longer timeout for batches
                encoding='utf-8'
            )
            
            if process.returncode != 0:
                raise Exception(f"Ollama error: {process.stderr}")
            
            return process.stdout.strip()
            
        except subprocess.TimeoutExpired:
            raise Exception("Ollama request timed out")
        except FileNotFoundError:
            raise Exception("Ollama not found. Please install Ollama and ensure 'ollama serve' is running.")
        except UnicodeDecodeError as e:
            raise Exception(f"Encoding error: {str(e)}")
    
    def _extract_json_from_response(self, response: str) -> Optional[List[Dict]]:
        # Try to extract JSON from ollama response
        json_pattern = r'\[.*?\]'
        matches = re.findall(json_pattern, response, re.DOTALL)
        
        for match in matches:
            try:
                match = match.strip()
                data = json.loads(match)
                if isinstance(data, list) and len(data) > 0:
                    return data
            except:
                continue
        
        # Fallback: try whole response
        try:
            data = json.loads(response.strip())
            if isinstance(data, list):
                return data
        except:
            pass
        
        return None
    
    def extract_startups(self, articles: List[Dict[str, str]], topic: str) -> List[Dict[str, str]]:
        # Main extraction function - processes articles in batches
        self._update_status("🤖 Starting batch extraction with Ollama...")
        
        # Filter out irrelevant articles before processing
        original_count = len(articles)
        # Basic keyword filtering - could be improved
        keywords = ["startup", "company", "ai", "software", "tech", "business", "venture", "funding", "raised"]
        articles = [
            a for a in articles
            if any(
                kw in a.get("content", "").lower() or 
                kw in a.get("summary", "").lower() or 
                kw in a.get("title", "").lower()
                for kw in keywords
            )
        ]
        
        filtered_count = len(articles)
        filter_message = f"🔎 Pre-filter: {filtered_count}/{original_count} relevant articles kept after filtering."
        print(filter_message)
        self._update_status(filter_message)
        
        # If no articles remain, return gracefully
        if not articles:
            no_articles_message = "⚠️ No relevant articles found. Skipping extraction."
            print(no_articles_message)
            self._update_status(no_articles_message)
            return []
        
        self._update_status(f"🧠 ExtractionAgent: Processing {CHUNK_SIZE} articles per batch...")
        
        all_startups = []
        # Calculate how many batches we need
        total_batches = (len(articles) + CHUNK_SIZE - 1) // CHUNK_SIZE
        
        # Process articles in batches
        for batch_idx in range(0, len(articles), CHUNK_SIZE):
            chunk = articles[batch_idx:batch_idx + CHUNK_SIZE]
            batch_num = (batch_idx // CHUNK_SIZE) + 1
            
            self._update_status(f"📦 Processing batch {batch_num}/{total_batches} ({len(chunk)} articles)...")
            
            # Build content for this batch
            content_parts = []
            for article in chunk:
                content = article.get('content', '')
                if isinstance(content, bytes):
                    try:
                        content = content.decode('utf-8')
                    except:
                        content = content.decode('utf-8', errors='ignore')
                
                content = str(content)[:1500].strip()  # Limit length
                
                if content:
                    title = article.get('title', 'Unknown')[:100]
                    content_parts.append(f"Article: {title}\n{content}")
            
            # Join all articles with separator
            text_block = "\n\n---\n\n".join(content_parts)
            
            # Create batch prompt
            prompt = f"""You are a startup analyst.
From the following startup news summaries, extract companies related to "{topic}".
Return only JSON array:
[{{"name":"", "description":"", "country":"", "category":""}}]

If no startups are found, return an empty list: []

Texts:
{text_block}

JSON:"""
            
            try:
                response = self._call_ollama(prompt)
                startups = self._extract_json_from_response(response)
                
                if startups:
                    batch_count = 0
                    for startup in startups:
                        if isinstance(startup, dict) and startup.get('name'):
                            # Clean up the data
                            cleaned = {
                                'name': str(startup.get('name', 'Unknown')).strip(),
                                'description': str(startup.get('description', '')).strip(),
                                'country': str(startup.get('country', 'Unknown')).strip(),
                                'category': str(startup.get('category', 'Other')).strip()
                            }
                            all_startups.append(cleaned)
                            batch_count += 1
                    
                    self._update_status(f"✅ Batch {batch_num}: Found {batch_count} startups")
                else:
                    self._update_status(f"⚠️ Batch {batch_num}: No startups found")
                    
            except Exception as e:
                self._update_status(f"❌ Extraction error for batch {batch_num}: {str(e)[:50]}")
                continue
        
        self._update_status(f"✅ Extraction complete: {len(all_startups)} total startups extracted from {len(articles)} articles")
        return all_startups
