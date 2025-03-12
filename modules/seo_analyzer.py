import asyncio
from dataclasses import dataclass
from typing import List, Dict, Optional
import logging
from bs4 import BeautifulSoup
import aiohttp
from utils.seo_utils import SEOUtils
from config import SERP_API_KEY, config
import json
from urllib.parse import urljoin, urlparse
from serpapi import GoogleSearch
import ssl
import socket
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class SEOAnalysisResults:
    total_pages: int
    overall_score: float
    metrics: Dict
    recommendations: List[str]
    issues: List[Dict]

class SEOAnalyzer:
    def __init__(self):
        self.seo_utils = SEOUtils()
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

    async def analyze_website(self, url: str) -> SEOAnalysisResults:
        """Analyze website SEO"""
        try:
            # Analyze technical SEO
            technical_metrics = await self._analyze_technical_seo(url)
            
            # Analyze on-page SEO
            onpage_metrics = await self._analyze_onpage_seo(url)
            
            # Analyze performance
            performance_metrics = await self._analyze_performance(url)
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(
                technical_metrics,
                onpage_metrics,
                performance_metrics
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                technical_metrics,
                onpage_metrics,
                performance_metrics
            )
            
            # Identify issues
            issues = self._identify_issues(
                technical_metrics,
                onpage_metrics,
                performance_metrics
            )
            
            return SEOAnalysisResults(
                total_pages=technical_metrics['total_pages'],
                overall_score=overall_score,
                metrics={
                    'technical': technical_metrics,
                    'onpage': onpage_metrics,
                    'performance': performance_metrics
                },
                recommendations=recommendations,
                issues=issues
            )
            
        except Exception as e:
            logger.error(f"SEO analysis failed: {e}")
            raise

    async def analyze_competitors(self, url: str) -> Dict:
        """Analyze competitor websites"""
        try:
            # Get top competitors
            competitors = await self._get_competitors(url)
            
            # Analyze each competitor
            analyses = []
            for competitor in competitors:
                analysis = await self._analyze_competitor(competitor)
                analyses.append(analysis)
            
            # Generate competitor-based recommendations
            recommendations = self._generate_competitor_recommendations(analyses)
            
            return {
                'competitors': competitors,
                'analyses': analyses,
                'recommendations': recommendations,
                'summary': self._generate_competitor_summary(analyses)
            }
            
        except Exception as e:
            logger.error(f"Competitor analysis failed: {e}")
            return {}

    async def _analyze_technical_seo(self, url: str) -> Dict:
        """Analyze technical SEO aspects"""
        try:
            async with self.session.get(url) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Parallel execution of checks
                total_pages, robots_txt, sitemap, mobile_friendly = await asyncio.gather(
                    self._count_pages(url),
                    self._check_robots_txt(url),
                    self._check_sitemap(url),
                    self._check_mobile_friendly(url)
                )
                
                return {
                    'total_pages': total_pages,
                    'robots_txt': robots_txt,
                    'sitemap': sitemap,
                    'ssl': response.url.scheme == 'https',
                    'ssl_info': await self._check_ssl(url),
                    'mobile_friendly': mobile_friendly,
                    'structured_data': self.seo_utils.extract_structured_data(soup),
                    'server_info': await self._get_server_info(url),
                    'response_headers': dict(response.headers),
                    'load_time': response.elapsed.total_seconds()
                }
                
        except Exception as e:
            logger.error(f"Technical SEO analysis failed: {e}")
            return {}

    async def _analyze_onpage_seo(self, url: str) -> Dict:
        """Analyze on-page SEO elements"""
        try:
            async with self.session.get(url) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Analyze all on-page elements
                meta_analysis = self.seo_utils.analyze_meta_tags(soup)
                heading_analysis = self.seo_utils.analyze_headings(soup)
                image_analysis = self.seo_utils.analyze_images(soup)
                link_analysis = self.seo_utils.analyze_links(soup)
                content_analysis = self.seo_utils.analyze_content(soup)
                
                return {
                    'meta_tags': meta_analysis,
                    'headings': heading_analysis,
                    'images': image_analysis,
                    'links': link_analysis,
                    'content': content_analysis,
                    'keyword_density': self.seo_utils._calculate_keyword_density(
                        ' '.join([p.get_text() for p in soup.find_all('p')])
                    ),
                    'readability': {
                        'score': self.seo_utils._calculate_readability(
                            ' '.join([p.get_text() for p in soup.find_all('p')])
                        ),
                        'word_count': len(' '.join([p.get_text() for p in soup.find_all('p')]).split())
                    }
                }
                
        except Exception as e:
            logger.error(f"On-page SEO analysis failed: {e}")
            return {}

    async def _analyze_performance(self, url: str) -> Dict:
        """Analyze website performance"""
        try:
            performance_metrics = {}
            
            # Basic performance metrics
            async with self.session.get(url) as response:
                performance_metrics['load_time'] = response.elapsed.total_seconds()
                performance_metrics['response_size'] = len(await response.read())
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Resource counts
                performance_metrics['resources'] = {
                    'images': len(soup.find_all('img')),
                    'scripts': len(soup.find_all('script')),
                    'stylesheets': len(soup.find_all('link', rel='stylesheet')),
                    'total_resources': len(soup.find_all(['img', 'script', 'link']))
                }
                
                # Page weight analysis
                performance_metrics['page_weight'] = {
                    'html': len(html),
                    'images': await self._calculate_resource_size(soup, 'img', 'src'),
                    'scripts': await self._calculate_resource_size(soup, 'script', 'src'),
                    'stylesheets': await self._calculate_resource_size(soup, 'link', 'href')
                }
                
                # Mobile optimization
                performance_metrics['mobile_optimization'] = {
                    'viewport_meta': bool(soup.find('meta', {'name': 'viewport'})),
                    'text_compression': 'content-encoding' in response.headers,
                    'image_optimization': await self._check_image_optimization(soup)
                }
                
            return performance_metrics
            
        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
            return {}

    def _calculate_overall_score(self, technical: Dict, onpage: Dict, performance: Dict) -> float:
        """Calculate overall SEO score"""
        try:
            scores = {
                'technical': self._calculate_technical_score(technical),
                'onpage': self._calculate_onpage_score(onpage),
                'performance': self._calculate_performance_score(performance)
            }
            
            # Weighted average
            weights = {
                'technical': 0.3,
                'onpage': 0.4,
                'performance': 0.3
            }
            
            overall_score = sum(
                score * weights[category] 
                for category, score in scores.items()
            )
            
            return round(overall_score, 2)
            
        except Exception as e:
            logger.error(f"Error calculating overall score: {e}")
            return 0.0

    def _calculate_technical_score(self, technical: Dict) -> float:
        """Calculate technical SEO score"""
        score = 0
        total_checks = 0
        
        # SSL Check
        if technical.get('ssl'):
            score += 1
        total_checks += 1
        
        # Robots.txt
        if technical.get('robots_txt', {}).get('exists'):
            score += 1
        total_checks += 1
        
        # Sitemap
        if technical.get('sitemap', {}).get('exists'):
            score += 1
        total_checks += 1
        
        # Mobile Friendly
        if technical.get('mobile_friendly'):
            score += 1
        total_checks += 1
        
        # Structured Data
        if technical.get('structured_data'):
            score += 1
        total_checks += 1
        
        return (score / total_checks) * 100 if total_checks > 0 else 0

    def _calculate_onpage_score(self, onpage: Dict) -> float:
        """Calculate on-page SEO score"""
        score = 0
        total_checks = 0
        
        # Meta Tags
        meta_tags = onpage.get('meta_tags', {})
        if meta_tags.get('title') and 30 <= len(meta_tags['title']) <= 60:
            score += 1
        total_checks += 1
        
        if meta_tags.get('description') and 120 <= len(meta_tags['description']) <= 160:
            score += 1
        total_checks += 1
        
        # Headings
        headings = onpage.get('headings', {})
        if headings.get('h1') and len(headings['h1']) == 1:
            score += 1
        total_checks += 1
        
        # Content
        content = onpage.get('content', {})
        if content.get('word_count', 0) >= config.seo.MIN_WORD_COUNT:
            score += 1
        total_checks += 1
        
        if content.get('readability_score', 0) >= config.seo.MIN_READABILITY_SCORE:
            score += 1
        total_checks += 1
        
        return (score / total_checks) * 100 if total_checks > 0 else 0

    def _calculate_performance_score(self, performance: Dict) -> float:
        """Calculate performance score"""
        score = 0
        total_checks = 0
        
        # Load Time
        if performance.get('load_time', float('inf')) <= config.seo.MAX_LOAD_TIME_SEC:
            score += 1
        total_checks += 1
        
        # Page Weight
        page_weight = performance.get('page_weight', {})
        if sum(page_weight.values()) <= config.seo.MAX_PAGE_SIZE_MB * 1024 * 1024:
            score += 1
        total_checks += 1
        
        # Mobile Optimization
        mobile_opt = performance.get('mobile_optimization', {})
        if mobile_opt.get('viewport_meta'):
            score += 1
        total_checks += 1
        
        if mobile_opt.get('text_compression'):
            score += 1
        total_checks += 1
        
        if mobile_opt.get('image_optimization'):
            score += 1
        total_checks += 1
        
        return (score / total_checks) * 100 if total_checks > 0 else 0

    def _generate_recommendations(self, technical: Dict, onpage: Dict, performance: Dict) -> List[str]:
        """Generate SEO recommendations"""
        recommendations = []
        
        # Technical recommendations
        if not technical.get('ssl'):
            recommendations.append("Implement SSL/HTTPS for secure connections")
        
        if not technical.get('robots_txt', {}).get('exists'):
            recommendations.append("Create a robots.txt file")
            
        if not technical.get('sitemap', {}).get('exists'):
            recommendations.append("Generate and submit an XML sitemap")
            
        if not technical.get('mobile_friendly'):
            recommendations.append("Improve mobile responsiveness")
        
        # On-page recommendations
        meta_tags = onpage.get('meta_tags', {})
        if not meta_tags.get('title') or len(meta_tags['title']) < 30 or len(meta_tags['title']) > 60:
            recommendations.append("Optimize title tag length (30-60 characters)")
            
        if not meta_tags.get('description') or len(meta_tags['description']) < 120 or len(meta_tags['description']) > 160:
            recommendations.append("Optimize meta description length (120-160 characters)")
        
        headings = onpage.get('headings', {})
        if not headings.get('h1') or len(headings['h1']) != 1:
            recommendations.append("Implement a single H1 heading")
        
        content = onpage.get('content', {})
        if content.get('word_count', 0) < config.seo.MIN_WORD_COUNT:
            recommendations.append(f"Increase content length (minimum {config.seo.MIN_WORD_COUNT} words)")
            
        if content.get('readability_score', 0) < config.seo.MIN_READABILITY_SCORE:
            recommendations.append("Improve content readability")
        
        # Performance recommendations
        if performance.get('load_time', 0) > config.seo.MAX_LOAD_TIME_SEC:
            recommendations.append("Improve page load time")
            
        page_weight = performance.get('page_weight', {})
        if sum(page_weight.values()) > config.seo.MAX_PAGE_SIZE_MB * 1024 * 1024:
            recommendations.append("Reduce page size")
            
        mobile_opt = performance.get('mobile_optimization', {})
        if not mobile_opt.get('viewport_meta'):
            recommendations.append("Add viewport meta tag for mobile optimization")
            
        if not mobile_opt.get('text_compression'):
            recommendations.append("Enable text compression")
            
        if not mobile_opt.get('image_optimization'):
            recommendations.append("Optimize images")
        
        return recommendations

    def _identify_issues(self, technical: Dict, onpage: Dict, performance: Dict) -> List[Dict]:
        """Identify SEO issues"""
        issues = []
        
        # Technical issues
        if not technical.get('ssl'):
            issues.append({
                'type': 'technical',
                'severity': 'high',
                'message': 'SSL certificate not implemented'
            })
        
        if not technical.get('mobile_friendly'):
            issues.append({
                'type': 'technical',
                'severity': 'high',
                'message': 'Website not mobile-friendly'
            })
        
        # On-page issues
        meta_tags = onpage.get('meta_tags', {})
        if not meta_tags.get('title'):
            issues.append({
                'type': 'onpage',
                'severity': 'high',
                'message': 'Missing title tag'
            })
        
        if not meta_tags.get('description'):
            issues.append({
                'type': 'onpage',
                'severity': 'medium',
                'message': 'Missing meta description'
            })
        
        content = onpage.get('content', {})
        if content.get('word_count', 0) < config.seo.MIN_WORD_COUNT:
            issues.append({
                'type': 'onpage',
                'severity': 'medium',
                'message': f'Insufficient content length ({content.get("word_count", 0)} words)'
            })
        
        # Performance issues
        if performance.get('load_time', 0) > config.seo.MAX_LOAD_TIME_SEC:
            issues.append({
                'type': 'performance',
                'severity': 'high',
                'message': f'Slow page load time ({performance.get("load_time", 0):.2f} seconds)'
            })
        
        return issues

    async def _get_competitors(self, url: str) -> List[str]:
        """Get top competing websites"""
        try:
            # Extract domain and main keyword
            domain = urlparse(url).netloc
            async with self.session.get(url) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                main_keyword = soup.title.string if soup.title else domain
            
            # Search using SerpAPI
            params = {
                "engine": "google",
                "q": main_keyword,
                "api_key": SERP_API_KEY,
                "num": 10
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            # Filter out own domain and collect competitors
            competitors = []
            for result in results.get('organic_results', []):
                competitor_url = result.get('link', '')
                competitor_domain = urlparse(competitor_url).netloc
                if competitor_domain != domain:
                    competitors.append(competitor_url)
            
            return competitors[:5]  # Return top 5 competitors
            
        except Exception as e:
            logger.error(f"Error getting competitors: {e}")
            return []

    async def _analyze_competitor(self, url: str) -> Dict:
        """Analyze a competitor website"""
        try:
            # Analyze technical aspects
            technical = await self._analyze_technical_seo(url)
            
            # Analyze on-page elements
            onpage = await self._analyze_onpage_seo(url)
            
            # Analyze performance
            performance = await self._analyze_performance(url)
            
            return {
                'url': url,
                'metrics': {
                    'technical': technical,
                    'onpage': onpage,
                    'performance': performance
                },
                'score': self._calculate_overall_score(technical, onpage, performance)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing competitor: {e}")
            return {}

    def _generate_competitor_recommendations(self, analyses: List[Dict]) -> List[str]:
        """Generate recommendations based on competitor analysis"""
        try:
            recommendations = []
            
            if not analyses:
                return recommendations
            
            # Calculate averages
            avg_score = sum(a.get('score', 0) for a in analyses) / len(analyses)
            avg_word_count = sum(
                a.get('metrics', {}).get('onpage', {}).get('content', {}).get('word_count', 0) 
                for a in analyses
            ) / len(analyses)
            
            # Generate recommendations
            recommendations.append(
                f"Target overall SEO score of {avg_score:.2f} to match competitors"
            )
            
            recommendations.append(
                f"Aim for content length of {int(avg_word_count)} words to match competitor average"
            )
            
            # Analyze common patterns
            common_features = self._analyze_competitor_patterns(analyses)
            for feature in common_features:
                recommendations.append(f"Implement {feature} (common among competitors)")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating competitor recommendations: {e}")
            return []

    def _analyze_competitor_patterns(self, analyses: List[Dict]) -> List[str]:
        """Analyze common patterns among competitors"""
        try:
            patterns = []
            
            # Check for common structured data types
            structured_data_types = set()
            for analysis in analyses:
                technical = analysis.get('metrics', {}).get('technical', {})
                structured_data = technical.get('structured_data', [])
                for data in structured_data:
                    if '@type' in data:
                        structured_data_types.add(data['@type'])
            
            if structured_data_types:
                patterns.append(f"structured data types: {', '.join(structured_data_types)}")
            
            # Check for common content patterns
            content_patterns = {
                'has_video': 0,
                'has_images': 0,
                'has_tables': 0
            }
            
            for analysis in analyses:
                onpage = analysis.get('metrics', {}).get('onpage', {})
                content = onpage.get('content', {})
                
                if content.get('videos', 0) > 0:
                    content_patterns['has_video'] += 1
                if content.get('images', {}).get('total', 0) > 0:
                    content_patterns['has_images'] += 1
                if content.get('tables', 0) > 0:
                    content_patterns['has_tables'] += 1
            
            threshold = len(analyses) * 0.6  # 60% threshold
            for pattern, count in content_patterns.items():
                if count >= threshold:
                    patterns.append(pattern.replace('has_', ''))
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing competitor patterns: {e}")
            return []

    async def _count_pages(self, url: str) -> int:
        """Count total pages on website"""
        try:
            sitemap = await self._check_sitemap(url)
            if sitemap.get('exists'):
                return sitemap.get('url_count', 0)
            
            # Fallback to robots.txt analysis
            robots = await self._check_robots_txt(url)
            if robots.get('exists') and robots.get('sitemaps'):
                total_urls = 0
                for sitemap_url in robots['sitemaps']:
                    sitemap_data = await self._fetch_sitemap(sitemap_url)
                    total_urls += sitemap_data.get('url_count', 0)
                return total_urls
            
            return 0
            
        except Exception as e:
            logger.error(f"Error counting pages: {e}")
            return 0

    async def _check_robots_txt(self, url: str) -> Dict:
        """Check robots.txt file"""
        try:
            robots_url = urljoin(url, '/robots.txt')
            async with self.session.get(robots_url) as response:
                if response.status == 200:
                    content = await response.text()
                    return {
                        'exists': True,
                        'content': content,
                        'sitemaps': [
                            line.split(': ')[1].strip()
                            for line in content.split('\n')
                            if line.lower().startswith('sitemap:')
                        ]
                    }
                return {'exists': False}
        except Exception as e:
            logger.error(f"Error checking robots.txt: {e}")
            return {'exists': False}

    async def _check_sitemap(self, url: str) -> Dict:
        """Check XML sitemap"""
        try:
            sitemap_url = urljoin(url, '/sitemap.xml')
            async with self.session.get(sitemap_url) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'xml')
                    urls = soup.find_all('url')
                    return {
                        'exists': True,
                        'url_count': len(urls),
                        'last_modified': max(
                            (url.findNext('lastmod').text for url in urls if url.findNext('lastmod')),
                            default=None
                        )
                    }
                return {'exists': False}
        except Exception as e:
            logger.error(f"Error checking sitemap: {e}")
            return {'exists': False}

    async def _check_mobile_friendly(self, url: str) -> bool:
        """Check if website is mobile-friendly"""
        try:
            async with self.session.get(url) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Check viewport meta tag
                viewport = soup.find('meta', {'name': 'viewport'})
                if not viewport:
                    return False
                
                # Check responsive design indicators
                media_queries = any('media' in str(tag) for tag in soup.find_all('link', rel='stylesheet'))
                responsive_meta = 'width=device-width' in str(viewport)
                
                return media_queries and responsive_meta
                
        except Exception as e:
            logger.error(f"Error checking mobile-friendly: {e}")
            return False

    async def _check_ssl(self, url: str) -> Dict:
        """Check SSL certificate details"""
        try:
            hostname = urlparse(url).netloc
            context = ssl.create_default_context()
            with socket.create_connection((hostname, 443)) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    return {
                        'issuer': dict(x[0] for x in cert['issuer']),
                        'expires': cert['notAfter'],
                        'subject': dict(x[0] for x in cert['subject'])
                    }
        except Exception as e:
            logger.error(f"Error checking SSL: {e}")
            return {}

    async def _get_server_info(self, url: str) -> Dict:
        """Get server information"""
        try:
            async with self.session.get(url) as response:
                headers = response.headers
                return {
                    'server': headers.get('Server'),
                    'powered_by': headers.get('X-Powered-By'),
                    'content_type': headers.get('Content-Type'),
                    'cache_control': headers.get('Cache-Control')
                }
        except Exception as e:
            logger.error(f"Error getting server info: {e}")
            return {}

    async def _calculate_resource_size(self, soup: BeautifulSoup, tag: str, attr: str) -> int:
        """Calculate total size of resources"""
        try:
            total_size = 0
            for element in soup.find_all(tag):
                resource_url = element.get(attr)
                if resource_url:
                    try:
                        async with self.session.head(resource_url) as response:
                            total_size += int(response.headers.get('content-length', 0))
                    except:
                        continue
            return total_size
        except Exception as e:
            logger.error(f"Error calculating resource size: {e}")
            return 0

    async def _check_image_optimization(self, soup: BeautifulSoup) -> bool:
        """Check if images are optimized"""
        try:
            images = soup.find_all('img')
            if not images:
                return True
            
            optimized_count = 0
            for img in images:
                if img.get('loading') == 'lazy' or img.get('decoding') == 'async':
                    optimized_count += 1
                    
            return optimized_count / len(images) >= 0.8  # 80% threshold
            
        except Exception as e:
            logger.error(f"Error checking image optimization: {e}")
            return False