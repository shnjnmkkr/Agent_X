import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
import logging
from urllib.parse import urljoin, urlparse
import google.generativeai as genai
from datetime import datetime
from utils.link_utils import LinkUtils
from utils.vector_store import VectorStore

logger = logging.getLogger(__name__)

@dataclass
class LinkStatus:
    url: str
    is_broken: bool
    status_code: Optional[int]
    error_message: Optional[str] = None
    context: Optional[Dict] = None
    last_checked: datetime = datetime.now()

@dataclass
class RepairSuggestion:
    original_url: str
    suggested_url: str
    confidence: float
    source: str
    context: Dict
    similarity_score: Optional[float] = None

class LinkManager:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.vector_store = VectorStore()
        self.link_utils = LinkUtils()
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
        self.known_good_links: Dict[str, LinkStatus] = {}

    async def initialize(self):
        """Initialize resources"""
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def close(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None

    async def scan_website(self, domain: str) -> Dict[str, LinkStatus]:
        """Comprehensive website link scanning"""
        try:
            await self.initialize()
            logger.info(f"Starting link scan for: {domain}")
            
            # Get all pages
            pages = await self._crawl_pages(domain)
            
            # Scan links from all pages
            all_links: Dict[str, LinkStatus] = {}
            link_contexts: List[Dict] = []
            
            for page in pages:
                links, contexts = await self._scan_page_links(page)
                all_links.update(links)
                link_contexts.extend(contexts)
            
            # Create vector index for link contexts
            if link_contexts:
                texts = [ctx['text'] for ctx in link_contexts]
                self.vector_store.create_index(texts, link_contexts)
                self.vector_store.save('data/link_contexts')
            
            # Update known good links
            self.known_good_links.update({
                url: status for url, status in all_links.items() 
                if not status.is_broken
            })
            
            return all_links
            
        except Exception as e:
            logger.error(f"Error scanning website: {e}")
            return {}

    async def _crawl_pages(self, domain: str) -> Set[str]:
        """Crawl website to find all pages"""
        pages = set()
        to_crawl = {domain}
        crawled = set()

        while to_crawl:
            url = to_crawl.pop()
            if url in crawled:
                continue

            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Find all internal links
                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            full_url = urljoin(url, href)
                            if urlparse(full_url).netloc == urlparse(domain).netloc:
                                to_crawl.add(full_url)
                        
                        pages.add(url)
                        
            except Exception as e:
                logger.error(f"Error crawling {url}: {e}")
            
            crawled.add(url)

        return pages

    async def _scan_page_links(self, page_url: str) -> Tuple[Dict[str, LinkStatus], List[Dict]]:
        """Scan all links on a single page"""
        links = {}
        contexts = []
        try:
            async with self.session.get(page_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    tasks = []
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        full_url = urljoin(page_url, href)
                        
                        # Get link context
                        context = self.link_utils.extract_link_context(link)
                        context['page_url'] = page_url
                        contexts.append(context)
                        
                        # Check link status
                        task = self._check_link_status(full_url, context)
                        tasks.append(task)
                    
                    # Check all links concurrently
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Process results
                    for result in results:
                        if isinstance(result, LinkStatus):
                            links[result.url] = result
                    
            return links, contexts
            
        except Exception as e:
            logger.error(f"Error scanning page {page_url}: {e}")
            return links, contexts

    async def repair_link(self, broken_link: LinkStatus) -> List[RepairSuggestion]:
        """Generate repair suggestions for a broken link"""
        try:
            suggestions = []
            
            # Check Wayback Machine
            archive_url = await self.link_utils.check_wayback_machine(broken_link.url)
            if archive_url:
                suggestions.append(RepairSuggestion(
                    original_url=broken_link.url,
                    suggested_url=archive_url,
                    confidence=0.9,
                    source="wayback_machine",
                    context={"archive": True}
                ))
            
            # Find similar links using FAISS
            if broken_link.context and 'text' in broken_link.context:
                similar_links = self.vector_store.search(broken_link.context['text'])
                for link in similar_links:
                    if link['page_url'] in self.known_good_links:
                        suggestions.append(RepairSuggestion(
                            original_url=broken_link.url,
                            suggested_url=link['page_url'],
                            confidence=1 - link['distance'],
                            source="similarity_match",
                            context=link,
                            similarity_score=link['distance']
                        ))
            
            # Generate AI suggestions
            ai_suggestions = await self._generate_ai_suggestions(broken_link)
            suggestions.extend(ai_suggestions)
            
            # Sort by confidence
            suggestions.sort(key=lambda x: x.confidence, reverse=True)
            return suggestions
            
        except Exception as e:
            logger.error(f"Error repairing link {broken_link.url}: {e}")
            return []

    async def _generate_ai_suggestions(self, broken_link: LinkStatus) -> List[RepairSuggestion]:
        """Generate repair suggestions using AI"""
        try:
            prompt = f"""
            Generate repair suggestions for this broken link:
            URL: {broken_link.url}
            Context: {broken_link.context}
            
            Consider:
            1. Similar URLs on the same domain
            2. Common URL patterns
            3. Content relevance
            
            Provide suggestions in format:
            URL: suggested_url
            Confidence: 0.0-1.0
            Reason: explanation
            """
            
            response = await self.model.generate_content(prompt)
            suggestions = []
            
            # Parse AI response and create suggestions
            lines = response.text.split('\n')
            current_suggestion = {}
            
            for line in lines:
                if line.startswith('URL:'):
                    if current_suggestion:
                        suggestions.append(RepairSuggestion(
                            original_url=broken_link.url,
                            suggested_url=current_suggestion['url'],
                            confidence=current_suggestion.get('confidence', 0.5),
                            source="ai_generated",
                            context={"reason": current_suggestion.get('reason', '')}
                        ))
                    current_suggestion = {'url': line.split('URL:')[1].strip()}
                elif line.startswith('Confidence:'):
                    current_suggestion['confidence'] = float(line.split('Confidence:')[1].strip())
                elif line.startswith('Reason:'):
                    current_suggestion['reason'] = line.split('Reason:')[1].strip()
            
            # Add last suggestion
            if current_suggestion:
                suggestions.append(RepairSuggestion(
                    original_url=broken_link.url,
                    suggested_url=current_suggestion['url'],
                    confidence=current_suggestion.get('confidence', 0.5),
                    source="ai_generated",
                    context={"reason": current_suggestion.get('reason', '')}
                ))
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating AI suggestions: {e}")
            return []

    async def _check_link_status(self, url: str, context: Dict) -> LinkStatus:
        """Check if a link is broken"""
        try:
            async with self.session.head(url, allow_redirects=True) as response:
                return LinkStatus(
                    url=url,
                    is_broken=response.status >= 400,
                    status_code=response.status,
                    context=context
                )
        except Exception as e:
            return LinkStatus(
                url=url,
                is_broken=True,
                status_code=None,
                error_message=str(e),
                context=context
            ) 