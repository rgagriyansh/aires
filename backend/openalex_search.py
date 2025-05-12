import requests
import json
import os
from typing import List, Dict, Optional, Any
from datetime import datetime
from urllib.parse import urlparse
import time
import PyPDF2
import io
import logging
import uuid
from openai import OpenAI
from itertools import combinations
from dotenv import load_dotenv
from humanizer import AIHumanizer

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class OpenAlexSearch:
    def __init__(self, email: str = "rgargriyansh36@gmail.com", keywords: List[str] = None, title: str = None):
        self.base_url = "https://api.openalex.org"
        self.email = email
        self.keywords = keywords or []
        self.title = title
        self.backend_dir = os.path.dirname(os.path.abspath(__file__))
        self.download_dir = os.path.join(self.backend_dir, "papers")
        self.references_file = "references.txt"
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.openai_api_key)
        self.humanizer = AIHumanizer()
        
        # Create papers directory if it doesn't exist
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
            logger.info(f"Created papers directory: {self.download_dir}")

    def create_unique_download_dir(self) -> str:
        """Create a unique directory for each paper request"""
        # Create a unique directory name using timestamp and UUID
        unique_dir = f"papers_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        download_dir = os.path.join(self.backend_dir, unique_dir)
        
        # Create the directory if it doesn't exist
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
            logger.info(f"Created unique download directory: {download_dir}")
        
        return download_dir

    def download_paper(self, url: str, title: str) -> Optional[str]:
        """Download a paper and return the local file path"""
        try:
            logger.info(f"Attempting to download paper: {title}")
            logger.debug(f"Download URL: {url}")
            
            # Clean the title to create a valid filename
            clean_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title)
            clean_title = clean_title[:100]  # Limit filename length
            
            # Get file extension from URL
            parsed_url = urlparse(url)
            filename = f"{clean_title}{os.path.splitext(parsed_url.path)[1]}"
            if not filename.endswith('.pdf'):
                filename += '.pdf'
            
            filepath = os.path.join(self.download_dir, filename)
            logger.debug(f"Target filepath: {filepath}")
            
            # Download the file
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Successfully downloaded paper to: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error downloading {url}: {str(e)}")
            return None

    def extract_text_from_pdf(self, filepath: str) -> str:
        """Extract text from a PDF file"""
        try:
            with open(filepath, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            logger.error(f"Error extracting text from {filepath}: {str(e)}")
            return ""

    def search_works(self, 
                    keyword: str,
                    per_page: int = 25,
                    page: int = 1) -> Dict:
        """
        Search for works using a single keyword
        
        Args:
            keyword: The keyword to search for
            per_page: Number of results per page (max 200)
            page: Page number to retrieve
            
        Returns:
            Dictionary containing search results
        """
        logger.info(f"Searching for papers with keyword: {keyword}")
        params = {
            "mailto": self.email,
            "per-page": per_page,
            "page": page,
            "search": keyword
        }
            
        logger.debug(f"Search parameters: {params}")
        response = requests.get(f"{self.base_url}/works", params=params)
        results = response.json()
        logger.info(f"Found {len(results.get('results', []))} papers")
        return results

    def get_download_links(self, work: Dict) -> List[Dict]:
        """Get all available download links for a work"""
        logger.debug(f"Getting download links for work: {work.get('title', 'Unknown title')}")
        download_links = []
        
        # Check primary location
        primary_location = work.get("primary_location", {})
        if primary_location:
            landing_url = primary_location.get("landing_page_url")
            pdf_url = primary_location.get("pdf_url")
            if landing_url:
                download_links.append({
                    "type": "Primary Location",
                    "url": landing_url,
                    "is_pdf": False
                })
            if pdf_url:
                download_links.append({
                    "type": "Primary Location PDF",
                    "url": pdf_url,
                    "is_pdf": True
                })
        
        # Check all locations
        locations = work.get("locations", [])
        for loc in locations:
            if not loc:  # Skip if location is None
                continue
                
            landing_url = loc.get("landing_page_url")
            pdf_url = loc.get("pdf_url")
            source = loc.get("source", {})
            source_name = source.get("display_name", "Unknown Source") if source else "Unknown Source"
            
            if landing_url:
                download_links.append({
                    "type": f"{source_name} Landing Page",
                    "url": landing_url,
                    "is_pdf": False
                })
            if pdf_url:
                download_links.append({
                    "type": f"{source_name} PDF",
                    "url": pdf_url,
                    "is_pdf": True
                })
        
        # Check open access information
        oa_info = work.get("open_access", {})
        if oa_info.get("is_oa") and oa_info.get("oa_url"):
            download_links.append({
                "type": "Open Access URL",
                "url": oa_info["oa_url"],
                "is_pdf": False
            })
        
        logger.info(f"Total download links found: {len(download_links)}")
        return download_links

    def get_section_keywords(self, section: str, base_keywords: List[str]) -> List[str]:
        """Get section-specific keywords based on the section type"""
        section_keywords = {
            'introduction': base_keywords,
            'related_work': base_keywords + ['existing methods', 'previous studies', 'literature review'],
            'methodology': base_keywords + ['techniques', 'approach', 'model', 'framework'],
            'results': base_keywords + ['dataset', 'evaluation', 'metrics', 'accuracy', 'performance'],
            'conclusion': base_keywords + ['future work', 'limitations', 'impact', 'implications']
        }
        return section_keywords.get(section.lower(), base_keywords)

    def get_paper_details(self, work: Dict) -> Dict:
        """Extract relevant details from a work"""
        doi = work.get("doi", "")
        if doi and isinstance(doi, str):
            doi = doi.replace("https://doi.org/", "")
        
        return {
            "title": work.get("title", "No title"),
            "abstract": work.get("abstract", ""),
            "doi": doi,
            "publication_year": work.get("publication_year", ""),
            "authors": [author["author"]["display_name"] for author in work.get("authorships", [])],
            "keywords": [concept["display_name"] for concept in work.get("concepts", [])],
            "citations": work.get("cited_by_count", 0),
            "url": work.get("primary_location", {}).get("landing_page_url", "")
        }

    def get_chatgpt_analysis(self, papers: List[Dict], title: str, section: str) -> str:
        """Get analysis from ChatGPT based on the papers found"""
        try:
            # Prepare the prompt with more specific instructions
            papers_text = "\n\n".join([
                f"Title: {paper['title']}\n"
                f"Authors: {', '.join(paper['authors'])}\n"
                f"Year: {paper['publication_year']}\n"
                f"Abstract: {paper['abstract']}\n"
                f"Keywords: {', '.join(paper['keywords'])}\n"
                f"Citations: {paper['citations']}\n"
                f"DOI: {paper['doi']}"
                for paper in papers
            ])
            
            prompt = f"""
            I am writing a research paper with the title: "{title}"
            
            I need help with the {section} section. Here are some relevant papers I found:
            
            {papers_text}
            
            Please analyze these papers and provide:
            1. A summary of the key findings and trends, focusing only on papers that are directly relevant to my research topic
            2. How these relevant papers relate to my research topic, being selective and only discussing papers that provide meaningful insights
            3. Any gaps in the literature that my research could address, based on the most relevant papers
            4. Key citations and references I should include in my {section}
            
            Please:
            - Only use references that are directly relevant to my research topic
            - Focus on recent papers (last 5-10 years) unless older papers are seminal works
            - Prioritize papers that match multiple keywords from my research
            - Exclude papers that are only tangentially related
            - Be selective in choosing references to maintain focus and relevance
            
            Please format your response in a clear, academic style suitable for a research paper.
            """
            
            # Call ChatGPT API using the new client
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a research paper assistant helping to analyze academic papers and provide insights for writing a research paper. Be selective in choosing references and focus only on papers that are directly relevant to the research topic."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Get the ChatGPT response
            chatgpt_response = response.choices[0].message.content
            
            # Humanize the response
            try:
                humanized_response = self.humanizer.humanize(chatgpt_response)
                return humanized_response.humanized_text
            except Exception as e:
                logger.error(f"Error humanizing ChatGPT response: {str(e)}")
                return chatgpt_response  # Return original response if humanization fails
            
        except Exception as e:
            logger.error(f"Error getting ChatGPT analysis: {str(e)}")
            return "Error getting analysis from ChatGPT"

    def get_reference_papers_content(self, keywords: List[str], title: str, section: str) -> Dict[str, Any]:
        """Get content from reference papers for a specific section using a hierarchical search strategy."""
        try:
            target_paper_count = 40  # Target number of papers to find
            processed_papers = []
            seen_paper_ids = set()  # Track unique papers
            
            # First search by title
            logger.info(f"Searching for papers with title: {title}")
            title_results = self.search_works(keyword=title, per_page=25)
            for paper in title_results.get("results", []):
                if len(processed_papers) >= target_paper_count:
                    break
                    
                paper_id = paper.get("id")
                if paper_id and paper_id not in seen_paper_ids:
                    try:
                        paper_details = self.get_paper_details(paper)
                        processed_papers.append(paper_details)
                        seen_paper_ids.add(paper_id)
                        logger.info(f"Added paper by title match: {paper_details['title']}")
                    except Exception as e:
                        logger.error(f"Error processing paper: {str(e)}")
                        continue
            
            # Then search by keywords in hierarchical order
            for required_keywords in range(len(keywords), 0, -1):
                if len(processed_papers) >= target_paper_count:
                    break
                    
                # Generate all combinations of the required number of keywords
                keyword_combinations = list(combinations(keywords, required_keywords))
                
                for keyword_combo in keyword_combinations:
                    if len(processed_papers) >= target_paper_count:
                        break
                        
                    # Create search query with all keywords in the combination
                    search_query = " AND ".join(f'"{keyword}"' for keyword in keyword_combo)
                    logger.info(f"Searching with keywords: {search_query}")
                    
                    # Search for papers
                    papers = self.search_works(keyword=search_query, per_page=25)
                    results = papers.get("results", [])
                    
                    # Process new papers
                    for paper in results:
                        if len(processed_papers) >= target_paper_count:
                            break
                            
                        paper_id = paper.get("id")
                        if paper_id and paper_id not in seen_paper_ids:
                            try:
                                paper_details = self.get_paper_details(paper)
                                processed_papers.append(paper_details)
                                seen_paper_ids.add(paper_id)
                                logger.info(f"Added paper: {paper_details['title']} (matched {required_keywords} keywords)")
                            except Exception as e:
                                logger.error(f"Error processing paper: {str(e)}")
                                continue
            
            logger.info(f"Total unique papers found: {len(processed_papers)}")
            
            # Get ChatGPT analysis with more specific instructions
            chatgpt_response = self.get_chatgpt_analysis(processed_papers, title, section)
            
            return {
                'papers': processed_papers,
                'analysis': chatgpt_response
            }
            
        except Exception as e:
            logger.error(f"Error in get_reference_papers_content: {str(e)}")
            return {
                'papers': [],
                'analysis': None
            }

    def format_citation(self, paper: Dict, citation_index: int) -> str:
        """Format a citation for a given paper"""
        title = paper.get("title", "No title")
        authors = [author["author"]["display_name"] for author in paper.get("authorships", [])]
        year = paper.get("publication_year", "n.d.")
        doi = paper.get("doi", "").replace("https://doi.org/", "")
        
        # Format citation in IEEE style
        citation = f"[{citation_index}] {', '.join(authors)}, \"{title},\" "
        if paper.get("primary_location", {}).get("source", {}).get("display_name"):
            citation += f"in {paper['primary_location']['source']['display_name']}, "
        citation += f"vol. {paper.get('volume', 'n.d.')}, no. {paper.get('issue', 'n.d.')}, "
        citation += f"pp. {paper.get('first_page', 'n.d.')}-{paper.get('last_page', 'n.d.')}, "
        citation += f"{year}."
        if doi:
            citation += f" doi: {doi}"
        
        return citation 

    def process_results(self, results: Dict, citation_style: str = "APA"):
        """Process search results, download papers, and save references"""
        if not results.get("results"):
            print("No results found")
            return
            
        # Clear existing references file
        with open(self.references_file, 'w', encoding='utf-8') as f:
            f.write("References\n")
            f.write("=" * 80 + "\n")
        
        for work in results["results"]:
            title = work.get("title", "No title")
            print(f"\nProcessing: {title}")
            
            # Save reference
            self.save_reference(work, citation_style)
            
            # Try to download paper
            download_links = self.get_download_links(work)
            pdf_links = [link for link in download_links if link["is_pdf"]]
            
            if pdf_links:
                print("Downloading paper...")
                for link in pdf_links:
                    filepath = self.download_paper(link["url"], title)
                    if filepath:
                        print(f"Downloaded to: {filepath}")
                        break
            else:
                print("No PDF download links available")
            
            # Add a small delay to avoid overwhelming servers
            time.sleep(1)

    def save_reference(self, work: Dict, citation_style: str = "APA"):
        """Save a reference to the references file"""
        citation = self.format_reference(work, citation_style)
        download_links = self.get_download_links(work)
        
        with open(self.references_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{citation}\n")
            if download_links:
                f.write("Download Links:\n")
                for link in download_links:
                    f.write(f"- {link['type']}: {link['url']}\n")
            f.write("-" * 80 + "\n")

    def format_reference(self, work: Dict, style: str = "APA") -> str:
        """
        Format a work into a citation in the specified style
        
        Args:
            work: The work object from OpenAlex
            style: Citation style (APA, MLA, Chicago)
            
        Returns:
            Formatted citation string
        """
        # Safely get all required fields with defaults
        authors = [author["author"]["display_name"] for author in work.get("authorships", [])]
        title = work.get("title", "No title")
        publication_year = work.get("publication_year", "n.d.")
        doi = work.get("doi", "")
        journal = self.get_journal_info(work)
        volume = work.get("biblio", {}).get("volume", "")
        issue = work.get("biblio", {}).get("issue", "")
        pages = work.get("biblio", {}).get("first_page", "")
        
        # Clean up DOI
        if doi and doi.startswith("https://doi.org/"):
            doi = doi.replace("https://doi.org/", "")
        
        if style == "APA":
            # Format: Author, A. A., & Author, B. B. (Year). Title of article. Journal Name, Volume(Issue), pages. https://doi.org/xx.xxx/yyyy
            author_str = ", ".join(authors) if authors else "Anonymous"
            citation = f"{author_str} ({publication_year}). {title}. {journal}"
            if volume:
                citation += f", {volume}"
                if issue:
                    citation += f"({issue})"
            if pages:
                citation += f", {pages}"
            if doi:
                citation += f". https://doi.org/{doi}"
            else:
                citation += "."
            return citation
        elif style == "MLA":
            # Format: Author, A. A., and B. B. Author. "Title of Article." Journal Name, vol. Volume, no. Issue, Year, pp. Pages.
            author_str = ", ".join(authors) if authors else "Anonymous"
            citation = f"{author_str}. \"{title}.\" {journal}"
            if volume:
                citation += f", vol. {volume}"
                if issue:
                    citation += f", no. {issue}"
            citation += f", {publication_year}"
            if pages:
                citation += f", pp. {pages}"
            citation += "."
            return citation
        else:  # Chicago
            # Format: Author, A. A., and B. B. Author. "Title of Article." Journal Name Volume, no. Issue (Year): Pages.
            author_str = ", ".join(authors) if authors else "Anonymous"
            citation = f"{author_str}. \"{title}.\" {journal}"
            if volume:
                citation += f" {volume}"
                if issue:
                    citation += f", no. {issue}"
            citation += f" ({publication_year})"
            if pages:
                citation += f": {pages}"
            citation += "."
            return citation

    def search_and_download_papers(self, target_count: int = 20, max_pages: int = 20, papers_per_page: int = 50) -> Dict[str, Any]:
        """
        Search for papers using each keyword sequentially and download up to target_count PDFs.
        Distributes downloads evenly across keywords.
        
        Args:
            target_count: Number of papers to download (default: 20)
            max_pages: Maximum number of pages to search per keyword (default: 20)
            papers_per_page: Number of papers per page (default: 50)
            
        Returns:
            Dictionary containing search results and statistics
        """
        if not self.keywords:
            logger.warning("No keywords provided for search")
            return {
                "total_papers_checked": 0,
                "total_papers_downloaded": 0,
                "downloaded_papers": [],
                "failed_downloads": [],
                "references_file": self.references_file,
                "download_dir": self.download_dir
            }

        logger.info(f"Starting download for up to {target_count} papers using keywords: {self.keywords}")
        total_papers_checked = 0
        total_papers_downloaded = 0
        downloaded_papers = []
        failed_downloads = []
        rate_limit_delay = 2  # seconds between API calls

        # Calculate papers per keyword
        papers_per_keyword = max(1, target_count // len(self.keywords))
        logger.info(f"Will try to download {papers_per_keyword} papers per keyword")

        try:
            # Loop through each keyword one by one
            for keyword in self.keywords:
                keyword_downloads = 0
                page = 1
                
                while keyword_downloads < papers_per_keyword and page <= max_pages:
                    try:
                        logger.info(f"Searching for '{keyword}' - page {page}...")
                        # Search with only the current keyword
                        results = self.search_works(keyword=keyword, per_page=papers_per_page, page=page)
                        papers = results.get("results", [])
                        num_found = len(papers)
                        logger.info(f"Found {num_found} papers on this page")
                        total_papers_checked += num_found

                        if not papers:
                            logger.warning(f"No more papers found for keyword '{keyword}'")
                            break

                        # Try downloading each paper
                        for work in papers:
                            if keyword_downloads >= papers_per_keyword:
                                break
                                
                            try:
                                title = work.get("title", "No title")
                                download_links = self.get_download_links(work)
                                pdf_links = [link for link in download_links if link.get("is_pdf")]

                                if pdf_links:
                                    downloaded = False
                                    for link in pdf_links:
                                        try:
                                            filepath = self.download_paper(link["url"], title)
                                            if filepath:
                                                downloaded_papers.append({
                                                    "title": title,
                                                    "filepath": filepath,
                                                    "doi": work.get("doi", "").replace("https://doi.org/", ""),
                                                    "keyword": keyword
                                                })
                                                total_papers_downloaded += 1
                                                keyword_downloads += 1
                                                downloaded = True
                                                logger.info(f"Downloaded {keyword_downloads}/{papers_per_keyword} for keyword '{keyword}': {title}")
                                                break
                                        except Exception as e:
                                            logger.error(f"Error downloading paper {title}: {str(e)}")
                                            continue
                                            
                                    if not downloaded:
                                        failed_downloads.append(title)
                                        logger.warning(f"Failed to download paper: {title}")
                                else:
                                    failed_downloads.append(title)
                                    logger.warning(f"No PDF links found for paper: {title}")
                                    
                            except Exception as e:
                                logger.error(f"Error processing paper: {str(e)}")
                                continue

                        page += 1
                        time.sleep(rate_limit_delay)  # Rate limiting

                    except Exception as e:
                        logger.error(f"Error searching page {page} for keyword '{keyword}': {str(e)}")
                        break

        except Exception as e:
            logger.error(f"Unexpected error in search_and_download_papers: {str(e)}")

        # Summary
        logger.info("\nSearch Summary:")
        logger.info(f"Total papers checked: {total_papers_checked}")
        logger.info(f"Successfully downloaded: {total_papers_downloaded}")
        logger.info(f"Failed downloads: {len(failed_downloads)}")
        logger.info(f"References saved to: {self.references_file}")
        logger.info(f"Downloaded papers are in: {self.download_dir}")

        if total_papers_downloaded < target_count:
            logger.warning(f"Could only download {total_papers_downloaded} out of {target_count} requested papers")

        return {
            "total_papers_checked": total_papers_checked,
            "total_papers_downloaded": total_papers_downloaded,
            "downloaded_papers": downloaded_papers,
            "failed_downloads": failed_downloads,
            "references_file": self.references_file,
            "download_dir": self.download_dir
        }

    def improve_section_with_chatgpt(self, section_content: str, section_name: str, paper_title: str, keywords: List[str]) -> str:
        """
        Send section content to ChatGPT for improvement
        
        Args:
            section_content: The current content of the section
            section_name: Name of the section (e.g., 'abstract', 'introduction')
            paper_title: Title of the paper
            keywords: List of keywords for context
            
        Returns:
            Improved section content
        """
        try:
            # Create the prompt for ChatGPT
            prompt = f"""
            Please improve the following {section_name} section of a research paper.
            
            Paper Title: {paper_title}
            Keywords: {', '.join(keywords)}
            
            Current {section_name}:
            {section_content}
            
            Please:
            1. Improve the clarity and coherence
            2. Ensure proper academic writing style
            3. Maintain the original meaning
            4. Keep the length similar
            5. Add relevant citations if needed
            
            Return only the improved {section_name}, without any additional text or explanations.
            """
            
            # Call ChatGPT API
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a research paper editor. Improve the given section while maintaining its academic style and original meaning."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Extract and return the improved content
            improved_content = response.choices[0].message.content.strip()
            return improved_content
            
        except Exception as e:
            logger.error(f"Error improving section with ChatGPT: {str(e)}")
            return section_content  # Return original content if there's an error

    def process_section_edit(self, paper_id: str, section_name: str, current_content: str) -> Dict[str, Any]:
        """
        Process a section edit request
        
        Args:
            paper_id: ID of the paper
            section_name: Name of the section being edited
            current_content: Current content of the section
            
        Returns:
            Dictionary containing the improved content and status
        """
        try:
            # Get paper details from database
            paper = db.query(ResearchPaper).filter(ResearchPaper.id == paper_id).first()
            if not paper:
                return {"status": "error", "message": "Paper not found"}
            
            # Get keywords from paper
            keywords = paper.keywords.split(",") if paper.keywords else []
            
            # Improve the section using ChatGPT
            improved_content = self.improve_section_with_chatgpt(
                section_content=current_content,
                section_name=section_name,
                paper_title=paper.selected_title,
                keywords=keywords
            )
            
            return {
                "status": "success",
                "improved_content": improved_content,
                "section": section_name
            }
            
        except Exception as e:
            logger.error(f"Error processing section edit: {str(e)}")
            return {"status": "error", "message": str(e)}

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # Console handler
            logging.FileHandler('app.log')  # File handler
        ]
    )

    # Initialize the search client
    searcher = OpenAlexSearch(
        email="rgargriyansh36@gmail.com",
        keywords=["startup", "Manufacturing", "SME", "incubator"]
    )
    
    # Search for papers and get analysis
    results = searcher.get_reference_papers_content(
        keywords=["startup", "Manufacturing", "SME", "incubator"],
        title="The Role of Startups in SME Development",
        section="introduction"
    )
    
    # Print results
    print("\nFound Papers:")
    for paper in results['papers']:
        print(f"\nTitle: {paper['title']}")
        print(f"Authors: {', '.join(paper['authors'])}")
        print(f"Year: {paper['publication_year']}")
        print(f"DOI: {paper['doi']}")
    
    print("\nChatGPT Analysis:")
    print(results['analysis'])

if __name__ == "__main__":
    main() 