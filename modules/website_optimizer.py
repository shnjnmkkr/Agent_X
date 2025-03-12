import asyncio
from dataclasses import dataclass
from typing import List, Dict, Optional
import logging
from datetime import datetime
import json
from pathlib import Path

from .content_optimizer import ContentOptimizer
from .link_manager import LinkManager
from .seo_analyzer import SEOAnalyzer
from utils.vector_store import VectorStore
from config import config

logger = logging.getLogger(__name__)

@dataclass
class OptimizationResults:
    total_pages: int
    seo_score: float
    broken_links: List[Dict]
    content_issues: List[Dict]
    performance_metrics: Dict
    recommendations: List[str]
    competitor_insights: Optional[Dict] = None

class WebsiteOptimizer:
    def __init__(self):
        self.content_optimizer = ContentOptimizer()
        self.link_manager = LinkManager()
        self.seo_analyzer = SEOAnalyzer()
        self.vector_store = VectorStore()

    async def analyze_and_optimize(self, url: str, optimization_level: str = "comprehensive") -> OptimizationResults:
        """Main method to analyze and optimize a website"""
        try:
            await self._initialize_components()
            logger.info(f"Starting comprehensive analysis for: {url}")
            
            # Run analyses concurrently
            link_task = asyncio.create_task(self.link_manager.scan_website(url))
            seo_task = asyncio.create_task(self.seo_analyzer.analyze_website(url))
            content_task = asyncio.create_task(self.content_optimizer.optimize_website(url))
            
            # Wait for all tasks to complete
            broken_links, seo_results, content_results = await asyncio.gather(
                link_task, seo_task, content_task
            )
            
            # Process broken links
            repair_suggestions = []
            if broken_links:
                repair_suggestions = await self._process_broken_links(broken_links)
                logger.info(f"Generated {len(repair_suggestions)} repair suggestions")
            
            # Generate competitor insights if comprehensive
            competitor_insights = None
            if optimization_level == "comprehensive":
                competitor_insights = await self.seo_analyzer.analyze_competitors(url)
            
            # Combine all results
            results = OptimizationResults(
                total_pages=seo_results.total_pages,
                seo_score=seo_results.overall_score,
                broken_links=[{
                    'url': url,
                    'status': status.__dict__,
                    'suggestions': [s.__dict__ for s in repair_suggestions if s.original_url == url]
                } for url, status in broken_links.items()],
                content_issues=content_results.issues,
                performance_metrics=seo_results.metrics,
                recommendations=self._combine_recommendations(
                    content_results.recommendations,
                    seo_results.recommendations
                ),
                competitor_insights=competitor_insights
            )
            
            # Generate and save report
            await self._generate_report(results, url)
            
            return results
            
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            raise
        finally:
            await self.cleanup()

    async def _process_broken_links(self, broken_links: Dict[str, Dict]) -> List[Dict]:
        """Process and generate repair suggestions for broken links"""
        repair_suggestions = []
        for url, status in broken_links.items():
            if status.get('is_broken'):
                suggestions = await self.link_manager.repair_link(status)
                repair_suggestions.extend(suggestions)
        return repair_suggestions

    def _combine_recommendations(self, content_recs: List[str], seo_recs: List[str]) -> List[str]:
        """Combine and deduplicate recommendations"""
        all_recs = set(content_recs + seo_recs)
        return sorted(list(all_recs), key=lambda x: len(x), reverse=True)

    async def _generate_report(self, results: OptimizationResults, url: str):
        """Generate detailed optimization report"""
        try:
            report = {
                "url": url,
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_pages": results.total_pages,
                    "seo_score": results.seo_score,
                    "broken_links_count": len(results.broken_links),
                    "content_issues_count": len(results.content_issues)
                },
                "details": {
                    "broken_links": results.broken_links,
                    "content_issues": results.content_issues,
                    "performance_metrics": results.performance_metrics,
                    "recommendations": results.recommendations
                }
            }
            
            if results.competitor_insights:
                report["competitor_analysis"] = results.competitor_insights
            
            # Save report
            await self._save_report(report, url)
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")

    async def _save_report(self, report: Dict, url: str):
        """Save optimization report"""
        try:
            # Create reports directory if it doesn't exist
            reports_dir = Path(config.system.DATA_DIR) / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename based on URL and timestamp
            domain = url.replace("https://", "").replace("http://", "").split("/")[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{domain}_{timestamp}.json"
            
            # Save report
            report_path = reports_dir / filename
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Report saved to: {report_path}")
            
            # Archive old reports if needed
            self._archive_old_reports(reports_dir)
            
        except Exception as e:
            logger.error(f"Error saving report: {e}")

    def _archive_old_reports(self, reports_dir: Path):
        """Archive old reports to maintain storage limits"""
        try:
            # Get all reports sorted by modification time
            reports = sorted(
                reports_dir.glob("*.json"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            # Keep only the latest N reports
            max_reports = config.system.MAX_REPORTS if hasattr(config.system, 'MAX_REPORTS') else 100
            if len(reports) > max_reports:
                # Create archive directory
                archive_dir = reports_dir / "archive"
                archive_dir.mkdir(exist_ok=True)
                
                # Move older reports to archive
                for report in reports[max_reports:]:
                    report.rename(archive_dir / report.name)
                    
        except Exception as e:
            logger.error(f"Error archiving old reports: {e}")

    async def _initialize_components(self):
        """Initialize all components"""
        try:
            await asyncio.gather(
                self.content_optimizer.initialize(),
                self.link_manager.initialize(),
                self.seo_analyzer.initialize()
            )
            logger.info("All components initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            raise

    async def cleanup(self):
        """Cleanup resources"""
        try:
            await asyncio.gather(
                self.content_optimizer.close(),
                self.link_manager.close(),
                self.seo_analyzer.close()
            )
            logger.info("All components cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def _validate_url(self, url: str) -> bool:
        """Validate URL before processing"""
        try:
            async with self.link_manager.session.head(url, allow_redirects=True) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"URL validation failed: {e}")
            return False

    def _prepare_optimization_config(self, optimization_level: str) -> Dict:
        """Prepare configuration based on optimization level"""
        base_config = {
            "analyze_competitors": False,
            "deep_content_analysis": False,
            "performance_analysis": True,
            "check_external_links": True
        }
        
        if optimization_level == "comprehensive":
            base_config.update({
                "analyze_competitors": True,
                "deep_content_analysis": True
            })
            
        return base_config

    async def get_optimization_status(self, url: str) -> Dict:
        """Get current optimization status for a URL"""
        try:
            reports_dir = Path(config.system.DATA_DIR) / "reports"
            if not reports_dir.exists():
                return {"status": "not_found"}
                
            # Find latest report for the domain
            domain = url.replace("https://", "").replace("http://", "").split("/")[0]
            reports = list(reports_dir.glob(f"report_{domain}_*.json"))
            
            if not reports:
                return {"status": "not_found"}
                
            latest_report = max(reports, key=lambda x: x.stat().st_mtime)
            
            with open(latest_report, 'r', encoding='utf-8') as f:
                report = json.load(f)
                
            return {
                "status": "found",
                "last_analyzed": report["timestamp"],
                "summary": report["summary"]
            }
            
        except Exception as e:
            logger.error(f"Error getting optimization status: {e}")
            return {"status": "error", "message": str(e)}