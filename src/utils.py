# Utility functions
import json
import os
from typing import List, Dict
from pathlib import Path


def save_results(startups: List[Dict], topic: str, output_dir: str = "data") -> str:
    # Save startups to JSON file
    os.makedirs(output_dir, exist_ok=True)
    
    # Clean up topic for filename
    safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_topic = safe_topic.replace(' ', '_')[:50]
    
    filename = f"startups_{safe_topic}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(startups, f, indent=2, ensure_ascii=False)
    
    # Also save to standard path (optional)
    try:
        extracted_path = Path(output_dir) / "startups_extracted.json"
        extracted_path.parent.mkdir(exist_ok=True)
        with open(extracted_path, 'w', encoding='utf-8') as f:
            json.dump(startups, f, indent=2, ensure_ascii=False)
    except:
        pass  # Ignore if it fails
    
    return filepath

