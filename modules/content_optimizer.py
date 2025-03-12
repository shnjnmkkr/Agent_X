import google.generativeai as genai
from dataclasses import dataclass
from typing import List, Dict, Optional
import logging
from utils.seo_utils import SEOUtils
from utils.vector_store import VectorStore
from config import GEMINI_API_KEY, config
import aiohttp
from bs4 import BeautifulSoup
import asyncio
from textblob import TextBlob

logger = logging.getLogger(__name__)

@dataclass
class ContentOptimizationResults:
    issues: List[Dict]
    recommendations: List[str]
    optimized_content: Dict[str, str]

class ContentOptimizer:
    def __init__(self):
        self.seo_utils = SEOUtils()
        self.vector_store = VectorStore()
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self):
        """Initialize resources"""
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def close(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None

    async def optimize_website(self, url: str) -> ContentOptimizationResults:
        """Optimize website content"""
        try:
            # Extract content
            content = await self._extract_content(url)
            
            # Analyze content
            analysis = await self._analyze_content(content)
            
            # Generate optimizations
            optimizations = await self._generate_optimizations(analysis)
            
            # Analyze competitors
            competitor_insights = await self._analyze_competitors(url)
            
            # Combine insights
            recommendations = self._generate_recommendations(
                analysis, optimizations, competitor_insights
            )
            
            return ContentOptimizationResults(
                issues=analysis['issues'],
                recommendations=recommendations,
                optimized_content=optimizations
            )
            
        except Exception as e:
            logger.error(f"Content optimization failed: {e}")
            raise

    async def _extract_content(self, url: str) -> Dict:
        """Extract content from webpage"""
        try:
            async with self.session.get(url) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract main content sections
                content = {
                    'title': soup.title.string if soup.title else '',
                    'meta_description': self.seo_utils.extract_meta_description(soup),
                    'headings': self.seo_utils.analyze_headings(soup),
                    'paragraphs': [p.get_text() for p in soup.find_all('p')],
                    'lists': [ul.get_text() for ul in soup.find_all(['ul', 'ol'])],
                    'images': self.seo_utils.analyze_images(soup),
                    'links': self.seo_utils.analyze_links(soup)
                }
                
                return content
                
        except Exception as e:
            logger.error(f"Error extracting content: {e}")
            raise

    async def _analyze_content(self, content: Dict) -> Dict:
        """Analyze content for optimization opportunities"""
        try:
            issues = []
            metrics = {}
            
            # Analyze title
            if len(content['title']) < 30 or len(content['title']) > 60:
                issues.append({
                    'type': 'title_length',
                    'message': 'Title length should be between 30-60 characters',
                    'severity': 'high'
                })
            
            # Analyze meta description
            if len(content['meta_description']) < 120 or len(content['meta_description']) > 160:
                issues.append({
                    'type': 'meta_description_length',
                    'message': 'Meta description should be between 120-160 characters',
                    'severity': 'high'
                })
            
            # Analyze content length
            total_text = ' '.join(content['paragraphs'])
            word_count = len(total_text.split())
            if word_count < config.seo.MIN_WORD_COUNT:
                issues.append({
                    'type': 'content_length',
                    'message': f'Content length ({word_count} words) is below recommended minimum',
                    'severity': 'high'
                })
            
            # Analyze readability
            blob = TextBlob(total_text)
            readability_score = self.seo_utils._calculate_readability(total_text)
            if readability_score < config.seo.MIN_READABILITY_SCORE:
                issues.append({
                    'type': 'readability',
                    'message': 'Content readability score is below recommended threshold',
                    'severity': 'medium'
                })
            
            # Analyze keyword density
            keyword_density = self.seo_utils._calculate_keyword_density(total_text)
            if max(keyword_density.values()) > config.seo.TARGET_KEYWORD_DENSITY:
                issues.append({
                    'type': 'keyword_stuffing',
                    'message': 'Possible keyword stuffing detected',
                    'severity': 'medium'
                })
            
            # Analyze heading structure
            if not content['headings'].get('h1'):
                issues.append({
                    'type': 'missing_h1',
                    'message': 'No H1 heading found',
                    'severity': 'high'
                })
            
            # Analyze image optimization
            for img in content['images']['images']:
                if not img.get('alt'):
                    issues.append({
                        'type': 'missing_alt',
                        'message': f'Missing alt text for image: {img.get("src")}',
                        'severity': 'medium'
                    })
            
            # Compile metrics
            metrics = {
                'word_count': word_count,
                'readability_score': readability_score,
                'keyword_density': keyword_density,
                'heading_count': sum(len(h) for h in content['headings'].values()),
                'image_count': content['images']['total'],
                'link_count': content['links']['total_internal'] + content['links']['total_external']
            }
            
            return {
                'issues': issues,
                'metrics': metrics,
                'content': content
            }
            
        except Exception as e:
            logger.error(f"Error analyzing content: {e}")
            raise

    async def _generate_optimizations(self, analysis: Dict) -> Dict:
        """Generate content optimizations"""
        try:
            optimizations = {}
            content = analysis['content']
            issues = analysis['issues']
            
            # Optimize title if needed
            if any(issue['type'] == 'title_length' for issue in issues):
                optimized_title = await self._optimize_title(
                    content['title'],
                    content['paragraphs'][0] if content['paragraphs'] else ''
                )
                optimizations['title'] = optimized_title
            
            # Optimize meta description if needed
            if any(issue['type'] == 'meta_description_length' for issue in issues):
                optimized_meta = await self._optimize_meta_description(
                    content['meta_description'],
                    content['paragraphs'][0] if content['paragraphs'] else ''
                )
                optimizations['meta_description'] = optimized_meta
            
            # Optimize content readability if needed
            if any(issue['type'] == 'readability' for issue in issues):
                optimized_paragraphs = await self._optimize_readability(
                    content['paragraphs']
                )
                optimizations['paragraphs'] = optimized_paragraphs
            
            # Optimize keyword usage if needed
            if any(issue['type'] == 'keyword_stuffing' for issue in issues):
                optimized_content = await self._optimize_keyword_usage(
                    '\n'.join(content['paragraphs']),
                    analysis['metrics']['keyword_density']
                )
                optimizations['content'] = optimized_content
            
            # Generate missing headings if needed
            if any(issue['type'] == 'missing_h1' for issue in issues):
                optimized_headings = await self._generate_headings(
                    content['paragraphs']
                )
                optimizations['headings'] = optimized_headings
            
            # Generate image alt texts if needed
            if any(issue['type'] == 'missing_alt' for issue in issues):
                optimized_images = await self._generate_alt_texts(
                    content['images']['images']
                )
                optimizations['images'] = optimized_images
            
            return optimizations
            
        except Exception as e:
            logger.error(f"Error generating optimizations: {e}")
            raise

    async def _analyze_competitors(self, url: str) -> List[Dict]:
        """Analyze competitor content"""
        try:
            # Get top competitors
            competitors = await self._get_competitors(url)
            
            competitor_analyses = []
            for competitor_url in competitors:
                # Extract competitor content
                content = await self._extract_content(competitor_url)
                
                # Analyze competitor content
                analysis = await self._analyze_content(content)
                
                competitor_analyses.append({
                    'url': competitor_url,
                    'metrics': analysis['metrics'],
                    'content_structure': {
                        'headings': content['headings'],
                        'sections': len(content['paragraphs']),
                        'lists': len(content['lists']),
                        'images': content['images']['total']
                    }
                })
            
            return competitor_analyses
            
        except Exception as e:
            logger.error(f"Error analyzing competitors: {e}")
            return []

    def _generate_recommendations(self, 
                                analysis: Dict, 
                                optimizations: Dict, 
                                competitor_insights: List[Dict]) -> List[str]:
        """Generate content recommendations"""
        try:
            recommendations = []
            
            # Add recommendations based on issues
            for issue in analysis['issues']:
                recommendations.append(f"Fix {issue['type']}: {issue['message']}")
            
            # Add recommendations based on competitor insights
            if competitor_insights:
                avg_competitor_words = sum(c['metrics']['word_count'] for c in competitor_insights) / len(competitor_insights)
                if analysis['metrics']['word_count'] < avg_competitor_words:
                    recommendations.append(
                        f"Increase content length to match competitor average ({int(avg_competitor_words)} words)"
                    )
                
                # Compare content structure
                avg_competitor_headings = sum(c['content_structure']['headings'] for c in competitor_insights) / len(competitor_insights)
                if analysis['metrics']['heading_count'] < avg_competitor_headings:
                    recommendations.append(
                        f"Add more section headings to match competitor average ({int(avg_competitor_headings)} headings)"
                    )
            
            # Add recommendations based on optimizations
            if 'title' in optimizations:
                recommendations.append("Implement optimized page title")
            if 'meta_description' in optimizations:
                recommendations.append("Implement optimized meta description")
            if 'paragraphs' in optimizations:
                recommendations.append("Implement readability improvements")
            if 'content' in optimizations:
                recommendations.append("Implement keyword optimization suggestions")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []

    async def _optimize_title(self, current_title: str, first_paragraph: str) -> str:
        """Optimize page title"""
        try:
            prompt = f"""
            Optimize this page title for SEO while maintaining meaning:
            Current title: {current_title}
            First paragraph: {first_paragraph}
            
            Requirements:
            - Length between 30-60 characters
            - Include main keyword
            - Be compelling and clickable
            """
            
            response = await self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error optimizing title: {e}")
            return current_title

    async def _optimize_meta_description(self, current_meta: str, first_paragraph: str) -> str:
        """Optimize meta description"""
        try:
            prompt = f"""
            Generate an optimized meta description:
            Current meta: {current_meta}
            First paragraph: {first_paragraph}
            
            Requirements:
            - Length between 120-160 characters
            - Include main keyword naturally
            - Be compelling and informative
            """
            
            response = await self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error optimizing meta description: {e}")
            return current_meta

    async def _optimize_readability(self, paragraphs: List[str]) -> List[str]:
        """Optimize content readability"""
        try:
            optimized_paragraphs = []
            
            for paragraph in paragraphs:
                prompt = f"""
                Improve the readability of this paragraph while maintaining meaning:
                {paragraph}
                
                Requirements:
                - Use shorter sentences
                - Use simpler words where possible
                - Maintain professional tone
                - Keep key information
                """
                
                response = await self.model.generate_content(prompt)
                optimized_paragraphs.append(response.text.strip())
            
            return optimized_paragraphs
            
        except Exception as e:
            logger.error(f"Error optimizing readability: {e}")
            return paragraphs

    async def _optimize_keyword_usage(self, content: str, current_density: Dict[str, float]) -> str:
        """Optimize keyword usage"""
        try:
            prompt = f"""
            Optimize keyword usage in this content:
            {content}
            
            Current keyword densities:
            {current_density}
            
            Requirements:
            - Maintain natural language
            - Keep keyword density below {config.seo.TARGET_KEYWORD_DENSITY}
            - Preserve meaning and context
            """
            
            response = await self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error optimizing keyword usage: {e}")
            return content

    async def _generate_headings(self, paragraphs: List[str]) -> Dict[str, List[str]]:
        """Generate optimized heading structure"""
        try:
            content = '\n'.join(paragraphs)
            
            prompt = f"""
            Generate an optimized heading structure for this content:
            {content}
            
            Requirements:
            - Include one H1 heading
            - Create relevant H2 and H3 subheadings
            - Use keywords naturally
            - Maintain logical hierarchy
            """
            
            response = await self.model.generate_content(prompt)
            
            # Parse the response into heading structure
            headings = {'h1': [], 'h2': [], 'h3': []}
            current_level = None
            
            for line in response.text.split('\n'):
                if line.startswith('H1:'):
                    current_level = 'h1'
                    headings['h1'].append(line.replace('H1:', '').strip())
                elif line.startswith('H2:'):
                    current_level = 'h2'
                    headings['h2'].append(line.replace('H2:', '').strip())
                elif line.startswith('H3:'):
                    current_level = 'h3'
                    headings['h3'].append(line.replace('H3:', '').strip())
            
            return headings
            
        except Exception as e:
            logger.error(f"Error generating headings: {e}")
            return {'h1': [], 'h2': [], 'h3': []}

    async def _generate_alt_texts(self, images: List[Dict]) -> List[Dict]:
        """Generate optimized alt texts for images"""
        try:
            optimized_images = []
            
            for image in images:
                if not image.get('alt'):
                    prompt = f"""
                    Generate an optimized alt text for this image:
                    Image URL: {image.get('src')}
                    Page context: {image.get('context', '')}
                    
                    Requirements:
                    - Be descriptive but concise
                    - Include relevant keywords naturally
                    - Focus on image content
                    """
                    
                    response = await self.model.generate_content(prompt)
                    image['alt'] = response.text.strip()
                
                optimized_images.append(image)
            
            return optimized_images
            
        except Exception as e:
            logger.error(f"Error generating alt texts: {e}")
            return images

    async def _get_competitors(self, url: str) -> List[str]:
        """Get top competing URLs"""
        # Implementation would use SERP API to get top ranking pages
        # For now, return empty list
        return [] 