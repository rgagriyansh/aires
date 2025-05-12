import openalex_search
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console handler
        logging.FileHandler('test.log')  # File handler
    ]
)

logger = logging.getLogger(__name__)

def test_reference_papers():
    # Initialize the search client
    openalex = openalex_search.OpenAlexSearch(
        email="rgargriyansh36@gmail.com",
        keywords=["startup", "Manufacturing", "SME", "incubator"]
    )
    
    # Test parameters
    title = "The Role of Startups in SME Development"
    keywords = ["startup", "Manufacturing", "SME", "incubator"]
    section = "introduction"
    
    # Test get_reference_papers_content
    logger.info("Testing get_reference_papers_content...")
    results = openalex.get_reference_papers_content(keywords=keywords, title=title, section=section)
    
    # Print results
    logger.info(f"Found {len(results['content'])} papers")
    logger.info(f"Generated {len(results['citations'])} citations")
    
    # Print citations
    logger.info("\nCitations:")
    for citation in results['citations']:
        logger.info(citation)
    
    # Print paper content
    logger.info("\nPaper Content:")
    for paper in results['content']:
        logger.info(f"\nTitle: {paper.get('title', 'Unknown')}")
        logger.info(f"DOI: {paper.get('doi', 'Unknown')}")
        logger.info(f"Content preview: {paper['content'][:200]}...")

if __name__ == "__main__":
    test_reference_papers() 