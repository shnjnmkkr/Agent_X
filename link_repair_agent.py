from google import genai
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
import requests
import os
import json
from datetime import datetime

class LinkRepairAgent:
    def __init__(self, api_key):
        # Initialize Gemini client
        self.client = genai.Client(api_key=api_key)
        
        # Setup headless Chrome
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920,1080")
        self.browser = webdriver.Chrome(options=chrome_options)
        
    def verify_broken_link(self, url):
        try:
            print(f"\nVerifying: {url}")
            
            # First try a HEAD request to check status
            response = requests.head(url, timeout=5)
            status_code = response.status_code
            
            # If it's a broken link, get the full page
            if status_code >= 400:
                response = requests.get(url, timeout=10)
                self.browser.get(url)
                
                # Wait for error page to load
                WebDriverWait(self.browser, 10).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
                
                # Take full page screenshot
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_url = url.replace('://', '_').replace('/', '_')
                screenshot_path = f"screenshots/error_{timestamp}_{safe_url}.png"
                
                # Create screenshots directory if it doesn't exist
                os.makedirs("screenshots", exist_ok=True)
                self.browser.save_screenshot(screenshot_path)
                
                return {
                    "url": url,
                    "status_code": status_code,
                    "screenshot_path": screenshot_path,
                    "is_broken": True,
                    "error_page_title": self.browser.title,
                    "error_message": response.text[:200]  # First 200 chars of error page
                }
            
            return {
                "url": url,
                "status_code": status_code,
                "is_broken": False
            }
                
        except Exception as e:
            print(f"Error verifying {url}: {str(e)}")
            return {
                "url": url,
                "status_code": 0,
                "error": str(e),
                "is_broken": True
            }

    def get_replacement_suggestions(self, url, context, status_code):
        prompt = {
            "broken_link": {
                "url": url,
                "status_code": status_code,
                "context": context
            },
            "instructions": """
            Analyze this link and provide:
            1. Is this a broken link? (true/false)
            2. Three specific suggestions to:
               - Replace with a working URL
               - Modify the content
               - Alternative action
            3. Brief explanation of likely cause
            
            Keep response concise and focused.
            """
        }
        
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=json.dumps(prompt)
            )
            return response.text
        except Exception as e:
            print(f"Gemini API Error: {str(e)}")
            return json.dumps({
                "is_broken": True,
                "suggestions": [],
                "reason": f"Error analyzing link: {str(e)}"
            })

    def process_broken_links(self, broken_links, context_map):
        """Process list of broken links and generate report"""
        results = []
        for link in broken_links:
            verification = self.verify_broken_link(link)
            
            if verification["is_broken"]:
                suggestions = self.get_replacement_suggestions(
                    link,
                    context_map.get(link, "No context available"),
                    verification["status_code"]
                )
                # Parse suggestions if it's JSON string
                try:
                    verification["suggestions"] = json.loads(suggestions)
                except json.JSONDecodeError:
                    verification["suggestions"] = suggestions
            
            results.append(verification)
        
        return results

    def cleanup(self):
        self.browser.quit() 