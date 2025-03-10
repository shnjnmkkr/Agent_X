from firecrawl import FirecrawlApp
from link_repair_agent import LinkRepairAgent
import json
from config import GEMINI_API_KEY, FIRECRAWL_API_KEY
import requests

def scan_website(url="LOREM IPSUM"):
    print("1. Initializing Firecrawl app...")
    app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)
    
    print(f"2. Starting to scrape website: {url}")
    results = app.scrape_url(url, params={
        'formats': ['markdown', 'links'],
        'actions': [
            {"type": "wait", "milliseconds": 5000},
            {"type": "scrape"}
        ]
    })
    
    print("\n3. Processing links...")
    broken_links = []
    context_map = {}
    
    if 'links' in results:
        print(f"Found {len(results['links'])} total links")
        markdown_content = results.get('markdown', '')
        
        for link in results['links']:
            if link.startswith(('http://', 'https://')):
                print(f"\nChecking: {link}")
                try:
                    response = requests.head(link, timeout=5)
                    status_code = response.status_code
                    print(f"Status code: {status_code}")
                    
                    if status_code >= 400:
                        print(f"Found broken link: {link}")
                        broken_links.append(link)
                        # Get surrounding context
                        try:
                            parts = markdown_content.split(link)
                            before = parts[0][-150:] if len(parts) > 0 else ""
                            after = parts[1][:150] if len(parts) > 1 else ""
                            context = f"...{before}[LINK]{after}..."
                        except:
                            context = "Context extraction failed"
                        context_map[link] = context.strip()
                except Exception as e:
                    print(f"Error checking {link}: {str(e)}")
                    broken_links.append(link)
                    context_map[link] = "Error during link check"
    else:
        print("No links found in the response")
    
    if broken_links:
        print(f"\nFound {len(broken_links)} broken links. Processing...")
        agent = LinkRepairAgent(api_key=GEMINI_API_KEY)
        try:
            repair_results = agent.process_broken_links(broken_links, context_map)
            
            print("\nSaving results to repair_report.json...")
            with open("repair_report.json", "w") as f:
                json.dump(repair_results, f, indent=2)
            
            return repair_results
        finally:
            agent.cleanup()
    else:
        print("\nNo broken links found!")
        return []

if __name__ == "__main__":
    results = scan_website()
    print(f"\nScan complete. Found and processed {len(results)} broken links")