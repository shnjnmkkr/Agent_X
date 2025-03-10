# Agent_X

A tool for detecting and analyzing broken links with AI-powered suggestions for fixes.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure API keys in `config.py`:
```python
FIRECRAWL_API_KEY = "your-firecrawl-key"
GEMINI_API_KEY = "your-gemini-key"
```

3. Run the script:
```bash
python scan_links.py
```

## Features
- Automated link checking
- Smart wait time handling
- AI-powered fix suggestions
- Visual verification with screenshots
- Detailed JSON reports

## Structure