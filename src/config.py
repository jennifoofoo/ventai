# Configuration for data sources
from pathlib import Path

# Data directory
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# RSS feeds by category
FEEDS_BY_TOPIC = {
    "General Startups": [
        "https://techcrunch.com/startups/feed/",
        "https://venturebeat.com/category/startups/feed/",
        "https://sifted.eu/feed/",
        "https://www.eu-startups.com/feed/",
        "https://news.crunchbase.com/feed/",
        "https://tech.eu/feed/",
        "https://yourstory.com/feed",
        "https://startupdaily.net/feed/",
        "https://www.seedtable.com/rss"
    ],
    "AI & DeepTech": [
        "https://venturebeat.com/category/ai/feed/",
        "https://aibusiness.com/rss",
        "https://syncedreview.com/feed/",
        "https://pub.towardsai.net/feed",
        "https://www.technologyreview.com/feed/",
        "https://www.techtarget.com/searchenterpriseai/feed"
    ],
    "Fintech & SaaS": [
        "https://www.finextra.com/rss/news.aspx",
        "https://www.altfi.com/feed",
        "https://saasmag.com/feed/",
        "https://www.pymnts.com/feed/"
    ],
    "Climate & Sustainability": [
        "https://www.ctvc.co/rss/",
        "https://cleantechnica.com/feed/",
        "https://www.greenbiz.com/rss.xml",
        "https://techcrunch.com/tag/climate/feed/"
    ],
    "Health & Robotics": [
        "https://www.medtechdive.com/feeds/news/",
        "https://www.robotics247.com/rss",
        "https://www.fiercebiotech.com/rss/xml",
        "https://spectrum.ieee.org/rss/fulltext"
    ],
    "Regional / DACH / Europe": [
        "https://siliconcanals.com/feed/",
        "https://technation.io/feed/",
        "https://www.startus-insights.com/feed/",
        "https://www.businessinsider.de/rss",
        "https://www.handelsblatt.com/contentexport/feed/tech-rss"
    ]
}

# OpenVC dataset
OPENVC_LOCAL_PATH = DATA_DIR / "openvc_startups_sample.json"
OPENVC_GITHUB_URL = "https://raw.githubusercontent.com/openvc/startup-dataset/main/startup_dataset.json"

# Output files
RSS_ARTICLES_PATH = DATA_DIR / "rss_articles.json"
OPENVC_PATH = DATA_DIR / "openvc_startups.json"
RESEARCH_MERGED_PATH = DATA_DIR / "research_merged.json"
STARTUPS_EXTRACTED_PATH = DATA_DIR / "startups_extracted.json"
STARTUPS_ANALYZED_PATH = DATA_DIR / "startups_analyzed.json"
