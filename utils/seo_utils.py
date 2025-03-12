from bs4 import BeautifulSoup
from typing import Dict, List
import logging
from textblob import TextBlob
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class SEOUtils:
    @staticmethod
    def analyze_meta_tags(soup: BeautifulSoup) -> Dict:
        """Analyze meta tags for SEO"""
        try:
            meta_tags = {
                'title': soup.title.string if soup.title else None,
                'description': None,
                'keywords': None,
                'robots': None,
                'viewport': None,
                'canonical': None
            }
            
            for tag in soup.find_all('meta'):
                name = tag.get('name', '').lower()
                property = tag.get('property', '').lower()
                content = tag.get('content', '')
                
                if name == 'description' or property == 'og:description':
                    meta_tags['description'] = content
                elif name == 'keywords':
                    meta_tags['keywords'] = content
                elif name == 'robots':
                    meta_tags['robots'] = content
                elif name == 'viewport':
                    meta_tags['viewport'] = content
                    
            canonical = soup.find('link', {'rel': 'canonical'})
            if canonical:
                meta_tags['canonical'] = canonical.get('href')
                
            return meta_tags
            
        except Exception as e:
            logger.error(f"Error analyzing meta tags: {e}")
            return {}

    @staticmethod
    def analyze_headings(soup: BeautifulSoup) -> Dict:
        """Analyze heading structure"""
        try:
            headings = {f'h{i}': [] for i in range(1, 7)}
            
            for i in range(1, 7):
                for heading in soup.find_all(f'h{i}'):
                    headings[f'h{i}'].append(heading.get_text().strip())
                    
            return headings
            
        except Exception as e:
            logger.error(f"Error analyzing headings: {e}")
            return {}

    @staticmethod
    def analyze_images(soup: BeautifulSoup) -> Dict:
        """Analyze image optimization"""
        try:
            images = []
            for img in soup.find_all('img'):
                images.append({
                    'src': img.get('src'),
                    'alt': img.get('alt'),
                    'title': img.get('title'),
                    'width': img.get('width'),
                    'height': img.get('height')
                })
            return {'total': len(images), 'images': images}
        except Exception as e:
            logger.error(f"Error analyzing images: {e}")
            return {}

    @staticmethod
    def analyze_links(soup: BeautifulSoup) -> Dict:
        """Analyze link structure"""
        try:
            internal_links = []
            external_links = []
            base_domain = None
            
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href.startswith('http'):
                    domain = urlparse(href).netloc
                    if not base_domain:
                        base_domain = domain
                    if domain == base_domain:
                        internal_links.append(href)
                    else:
                        external_links.append(href)
                else:
                    internal_links.append(href)
                    
            return {
                'internal': internal_links,
                'external': external_links,
                'total_internal': len(internal_links),
                'total_external': len(external_links)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing links: {e}")
            return {}

    @staticmethod
    def analyze_content(soup: BeautifulSoup) -> Dict:
        """Analyze content quality"""
        try:
            # Get main content
            content = ' '.join([p.get_text() for p in soup.find_all('p')])
            
            # Analyze with TextBlob
            blob = TextBlob(content)
            
            return {
                'word_count': len(content.split()),
                'sentence_count': len(blob.sentences),
                'readability_score': SEOUtils._calculate_readability(content),
                'sentiment': blob.sentiment.polarity,
                'subjectivity': blob.sentiment.subjectivity,
                'keyword_density': SEOUtils._calculate_keyword_density(content)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing content: {e}")
            return {}

    @staticmethod
    def extract_structured_data(soup: BeautifulSoup) -> List[Dict]:
        """Extract and analyze structured data"""
        try:
            structured_data = []
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    data = json.loads(script.string)
                    structured_data.append(data)
                except:
                    continue
            return structured_data
        except Exception as e:
            logger.error(f"Error extracting structured data: {e}")
            return []

    @staticmethod
    def _calculate_readability(text: str) -> float:
        """Calculate Flesch reading ease score"""
        try:
            sentences = len(TextBlob(text).sentences)
            words = len(text.split())
            syllables = SEOUtils._count_syllables(text)
            
            if sentences == 0 or words == 0:
                return 0
                
            return 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
            
        except Exception as e:
            logger.error(f"Error calculating readability: {e}")
            return 0

    @staticmethod
    def _count_syllables(text: str) -> int:
        """Count syllables in text"""
        try:
            text = text.lower()
            count = 0
            vowels = "aeiouy"
            on_vowel = False
            
            for char in text:
                is_vowel = char in vowels
                if is_vowel and not on_vowel:
                    count += 1
                on_vowel = is_vowel
                
            return count
            
        except Exception as e:
            logger.error(f"Error counting syllables: {e}")
            return 0

    @staticmethod
    def _calculate_keyword_density(text: str) -> Dict[str, float]:
        """Calculate keyword density"""
        try:
            words = text.lower().split()
            total_words = len(words)
            word_freq = {}
            
            for word in words:
                if len(word) > 3:  # Skip short words
                    word_freq[word] = word_freq.get(word, 0) + 1
                    
            # Calculate density
            density = {
                word: (count / total_words) * 100 
                for word, count in word_freq.items()
            }
            
            # Sort by density
            return dict(
                sorted(density.items(), key=lambda x: x[1], reverse=True)[:10]
            )
            
        except Exception as e:
            logger.error(f"Error calculating keyword density: {e}")
            return {} 