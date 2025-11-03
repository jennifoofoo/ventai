# 🧠 VentAI – AI-Powered Venture Intelligence

VentAI is a local, open-source market and startup intelligence engine that uses AI agents and LLMs (via Ollama) to discover, extract, and analyze startups and emerging trends from global tech news and open data sources.

**Discover. Analyze. Predict. — All with AI.**

## What does it do?

The app has 4 agents that work sequentially:

1. **ResearchAgent** - Fetches RSS feeds and OpenVC data
   - 6 categories with different RSS feeds (General Startups, AI & DeepTech, Fintech & SaaS, etc.)
   - Optional OpenVC dataset from local file or GitHub
   
2. **ExtractionAgent** - Extracts startup info using Ollama (local LLM)
   - Processes articles in batches (5 at a time for better performance)
   - Filters out irrelevant articles first
   - Extracts: name, description, country, category

3. **EnrichmentAgent** (optional) - Scrapes websites for more info
   - Can be enabled but it's slower

4. **AnalysisAgent** - Clusters startups and creates visualizations
   - Uses TF-IDF and K-Means for clustering
   - Auto-generates insights

## Setup

You need:
- Python 3.11+ 
- Ollama installed and running

```bash
# Install Ollama from https://ollama.ai
ollama serve
ollama pull mistral
```

Then:

```bash
cd ventai
pip install -r requirements.txt
streamlit run app.py
```

## Usage

1. Make sure Ollama is running (`ollama serve`)
2. Start the app with `streamlit run app.py`
3. In the browser:
   - Enter a topic (e.g. "AI in Manufacturing Europe")
   - Select category (dropdown)
   - Adjust optional settings
   - Click "Run Intelligence Scan"
4. View results: table, charts, download

## RSS Feed Categories

- **General Startups** (9 feeds): TechCrunch, VentureBeat, Sifted, EU-Startups, etc.
- **AI & DeepTech** (6 feeds): VentureBeat AI, AI Business, Synced Review, etc.
- **Fintech & SaaS** (4 feeds): Finextra, AltFi, SaaS Mag, PYMNTS
- **Climate & Sustainability** (4 feeds): CTVC, CleanTechnica, GreenBiz, etc.
- **Health & Robotics** (4 feeds): MedTech Dive, Robotics 247, Fierce Biotech, etc.
- **Regional / DACH / Europe** (5 feeds): Silicon Canals, Tech Nation, Business Insider DE, etc.

## File Structure

```
ventai/
├── app.py                 # Streamlit UI
├── src/
│   ├── config.py          # RSS Feed config
│   ├── agents/            # The 4 agents
│   ├── utils.py
│   └── visualize.py
├── data/                  # Output files (gitignored)
└── requirements.txt
```

## Output

Results are saved in `data/`:
- `ventai_articles.json` - All RSS articles
- `ventai_extracted.json` - Extracted startups
- `ventai_{topic}.json` - Topic-specific results

Can also be downloaded directly from the UI.

## About VentAI

VentAI combines intelligent data collection, natural language extraction, and clustering to map startup ecosystems and venture trends in real time. It runs entirely locally using Ollama and open data sources.

## Troubleshooting

- **Ollama not found**: Make sure `ollama serve` is running
- **No results**: Check internet connection, some RSS feeds might be down
- **Enrichment too slow**: It's optional, just disable it

## License

MIT
