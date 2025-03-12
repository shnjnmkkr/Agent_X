import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, List
import argparse
from pathlib import Path

from modules.website_optimizer import WebsiteOptimizer
from config import config
from utils import configure_utils, UtilsConfig

# Configure logging
logging.basicConfig(
    level=config.system.LOG_LEVEL,
    format=config.system.LOG_FORMAT,
    handlers=[
        logging.FileHandler(f"{config.system.LOG_DIR}/snapseo_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class SnapSEO:
    def __init__(self):
        self.optimizer = WebsiteOptimizer()
        
    async def optimize_website(self, url: str, optimization_level: str = "comprehensive") -> Dict:
        """
        Main entry point for website optimization
        
        Args:
            url: Website URL to optimize
            optimization_level: Level of optimization (basic/comprehensive)
        
        Returns:
            Dictionary containing optimization results
        """
        try:
            logger.info(f"Starting {optimization_level} optimization for: {url}")
            
            # Run optimization
            results = await self.optimizer.analyze_and_optimize(
                url=url,
                optimization_level=optimization_level
            )
            
            # Log results summary
            logger.info(f"Optimization completed for {url}")
            logger.info(f"Total pages analyzed: {results.total_pages}")
            logger.info(f"SEO score: {results.seo_score}")
            logger.info(f"Broken links found: {len(results.broken_links)}")
            
            return results.__dict__
            
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            raise
        
    async def cleanup(self):
        """Cleanup resources"""
        await self.optimizer.cleanup()

async def main(args):
    """Main execution function"""
    try:
        # Initialize SnapSEO
        snap_seo = SnapSEO()
        
        # Configure utils
        configure_utils(UtilsConfig(debug_mode=args.debug))
        
        # Run optimization
        results = await snap_seo.optimize_website(
            url=args.url,
            optimization_level=args.level
        )
        
        # Save results if specified
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            import json
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to: {output_path}")
        
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        raise
    finally:
        await snap_seo.cleanup()

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="SnapSEO: Autonomous Web Intelligence System")
    
    parser.add_argument(
        "url",
        help="Website URL to optimize"
    )
    
    parser.add_argument(
        "--level",
        choices=["basic", "comprehensive"],
        default="comprehensive",
        help="Optimization level"
    )
    
    parser.add_argument(
        "--output",
        help="Path to save results JSON"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    return parser.parse_args()

if __name__ == "__main__":
    # Parse arguments
    args = parse_arguments()
    
    # Run main function
    asyncio.run(main(args)) 