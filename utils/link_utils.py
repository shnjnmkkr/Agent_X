from bs4 import BeautifulSoup, Tag
from typing import Dict, List, Optional
import logging
import aiohttp
import asyncio
from urllib.parse import urljoin, urlparse
from datetime import datetime

logger = logging.getLogger(__name__)

class LinkUtils:
    def __init__(self):
        self.wayback_url = "http://archive.org/wayback/available"
        self.archive_today_url = "https://archive.today/"
        
    def extract_link_context(self, link_tag: Tag) -> Dict:
        """Extract context information for a link"""
        context = {
            'text': link_tag.get_text(strip=True),
            'title': link_tag.get('title', ''),
            'class': ' '.join(link_tag.get('class', [])),
            'surrounding_text': self._get_surrounding_text(link_tag),
            'section': self._get_section_info(link_tag)
        }
        return context

    def _get_surrounding_text(self, tag: Tag, chars: int = 100) -> str:
        """Get text surrounding a link"""
        if not tag.parent:
            return ""
            
        full_text = tag.parent.get_text(strip=True)
        link_text = tag.get_text(strip=True)
        
        start = full_text.find(link_text)
        if start == -1:
            return ""
            
        before = full_text[max(0, start-chars):start]
        after = full_text[start+len(link_text):start+len(link_text)+chars]
        
        return f"{before} {link_text} {after}".strip()

    def _get_section_info(self, tag: Tag) -> Dict:
        """Get information about the section containing the link"""
        section = tag.find_parent(['section', 'article', 'div'])
        if not section:
            return {}
            
        return {
            'id': section.get('id', ''),
            'class': ' '.join(section.get('class', [])),
            'heading': self._find_nearest_heading(section)
        }

    def _find_nearest_heading(self, tag: Tag) -> str:
        """Find the nearest heading to a tag"""
        heading = tag.find_previous(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        return heading.get_text(strip=True) if heading else ""

    async def check_wayback_machine(self, url: str) -> Optional[str]:
        """Check if URL is available in Wayback Machine"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.wayback_url,
                    params={'url': url}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'archived_snapshots' in data and 'closest' in data['archived_snapshots']:
                            return data['archived_snapshots']['closest']['url']
            return None
        except Exception as e:
            logger.error(f"Error checking Wayback Machine: {e}")
            return None

    async def check_other_archives(self, url: str) -> List[Dict]:
        """Check other archive services"""
        archives = []
        try:
            # Check Archive.today
            archive_today = await self._check_archive_today(url)
            if archive_today:
                archives.append({
                    'url': archive_today,
                    'source': 'archive.today'
                })
            
            # Add more archive services here
            
            return archives
        except Exception as e:
            logger.error(f"Error checking other archives: {e}")
            return []

    async def _check_archive_today(self, url: str) -> Optional[str]:
        """Check if URL is available in Archive.today"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.archive_today_url}{url}"
                ) as response:
                    if response.status == 200:
                        return str(response.url)
            return None
        except Exception as e:
            logger.error(f"Error checking Archive.today: {e}")
            return None
