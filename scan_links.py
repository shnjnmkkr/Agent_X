from firecrawl import FirecrawlApp
from link_repair_agent import LinkRepairAgent
import json
from config import GEMINI_API_KEY, FIRECRAWL_API_KEY
import requests

# Change this URL to scan different websites
TARGET_URL = "https://www.cognizance.org.in/"

def scan_website(url=TARGET_URL):
    print("1. Initializing Firecrawl app...")
    app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)
    
    print(f"2. Starting to crawl website: {url}")
    results = app.crawl_url(url)
    
    print("\n3. Processing links from all crawled pages...")
    broken_links = []
    context_map = {}
    
    if 'data' in results:
        total_pages = len(results['data'])
        print(f"Crawled {total_pages} pages")
        
        for page in results['data']:
            page_url = page['metadata']['url']
            print(f"\nProcessing page: {page_url}")
            
            # Extract links from markdown content
            markdown_content = page['markdown']
            links = []
            
            # Extract all URLs from the markdown content
            import re
            urls = re.findall(r'https?://[^\s\)\"\']+', markdown_content)
            
            for link in urls:
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
        print("No pages found in the crawl response")
    
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
    results = scan_website()  # This will use TARGET_URL by default
    print(f"\nScan complete. Found and processed {len(results)} broken links")