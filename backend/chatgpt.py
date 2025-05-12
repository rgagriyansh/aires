from openai import OpenAI
from typing import Dict, Any
import os
import logging
from dotenv import load_dotenv
import re
from humanizer import AIHumanizer

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logger.error("OPENAI_API_KEY not found in environment variables")
    raise ValueError("OPENAI_API_KEY environment variable is required")

client = OpenAI(api_key=api_key)
humanizer = AIHumanizer()

def create_research_paper_prompt(paper_data: Dict[str, Any]) -> str:
    """Create a detailed prompt for research paper generation."""
    prompt = f"""Generate a comprehensive research paper with the following specifications:

Topic: {paper_data['topic']}
Keywords: {', '.join(paper_data['keywords'])}
Length: {paper_data['length']}
Academic Field: {paper_data['academic_field']}
Paper Type: {paper_data['paper_type']}
Reference Style: {paper_data['reference_style']}
Target Audience: {paper_data.get('target_audience', 'Academic researchers')}

Required Sections:
{', '.join(paper_data['sections'])}

Additional Guidelines:
{paper_data.get('guidelines', 'None provided')}

Please generate a well-structured research paper that:
1. Follows academic writing standards
2. Includes proper citations in the specified reference style
3. Maintains a logical flow between sections
4. Incorporates the provided keywords naturally
5. Is appropriate for the target audience
6. Adheres to the specified length requirements

Format the output with clear section headers and proper academic formatting."""

    return prompt

async def generate_paper_titles(paper_data: dict) -> list:
    """
    Generate potential titles for a research paper based on the provided specifications.
    
    Args:
        paper_data (dict): Dictionary containing paper specifications
        
    Returns:
        list: List of generated paper titles
    """
    try:
        # Create a prompt for title generation
        prompt = f"""Generate 5 potential research paper titles based on the following specifications:
        
        Topic: {paper_data['topic']}
        Keywords: {', '.join(paper_data['keywords'])}
        Academic Field: {paper_data.get('academic_field', 'General')}
        Paper Type: {paper_data.get('paper_type', 'Research')}
        Target Audience: {paper_data.get('target_audience', 'Academic')}
        
        Please provide 5 distinct, professional, and engaging titles that reflect the research focus.
        Format the response as a list of titles, one per line."""

        # Make the API call
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a research paper title generator. Generate professional, academic titles."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )

        # Extract and clean the titles
        titles_text = response.choices[0].message.content
        titles = [title.strip() for title in titles_text.split('\n') if title.strip()]
        
        return titles[:5]  # Ensure we return exactly 5 titles

    except Exception as e:
        print(f"Error generating titles: {str(e)}")
        raise

async def generate_research_paper(paper_data: dict) -> str:
    """
    Generate a research paper based on the provided specifications.
    
    Args:
        paper_data (dict): Dictionary containing paper specifications
        
    Returns:
        str: Generated research paper content
    """
    try:
        # Create a detailed prompt for paper generation
        prompt = f"""Generate a research paper with the following specifications:
        
        Topic: {paper_data['topic']}
        Keywords: {', '.join(paper_data['keywords'])}
        Length: {paper_data.get('length', 'Medium')}
        Academic Field: {paper_data.get('academic_field', 'General')}
        Paper Type: {paper_data.get('paper_type', 'Research')}
        Reference Style: {paper_data.get('reference_style', 'APA')}
        Target Audience: {paper_data.get('target_audience', 'Academic')}
        Required Sections: {', '.join(paper_data.get('required_sections', []))}
        Custom Sections: {', '.join(paper_data.get('custom_sections', []))}
        Additional Guidelines: {paper_data.get('additional_guidelines', 'None')}
        
        Please generate a comprehensive research paper following academic writing standards
        and the specified formatting requirements."""

        # Make the API call
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an academic research paper generator. Generate high-quality, well-structured research papers."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"Error generating research paper: {str(e)}")
        raise

async def generate_abstract(paper_data: dict) -> str:
    """
    Generate the abstract section of the research paper.
    
    Args:
        paper_data (dict): Dictionary containing paper specifications
        
    Returns:
        str: Generated abstract content
    """
    try:
        prompt = f"""Generate an abstract for a research paper with the following specifications:
        
        Title: {paper_data['selected_title']}
        Topic: {paper_data['topic']}
        Keywords: {', '.join(paper_data['keywords'])}
        Academic Field: {paper_data.get('academic_field', 'General')}
        Paper Type: {paper_data.get('paper_type', 'Research')}
        
        The abstract should include:
        1. A brief introduction about the topic
        2. Identification of gaps or problems in existing literature
        3. Explanation of how this research addresses those gaps
        4. Key findings or results
        
        Keep the abstract concise and within 250 words.
        Follow academic writing standards and maintain a professional tone."""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an academic researcher writing an abstract for a research paper."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"Error generating abstract: {str(e)}")
        raise

def get_section_prompt(section_name: str, paper_data: dict, previous_sections: dict) -> str:
    """Get a specific prompt for each section type."""
    base_info = f"""Generate the {section_name} section for a research paper with the following details:
Topic: {paper_data['topic']}
Keywords: {', '.join(paper_data['keywords'])}
Length: {paper_data.get('length', 'Medium')}
Academic Field: {paper_data.get('academic_field', 'General')}
Paper Type: {paper_data.get('paper_type', 'Research')}
Reference Style: {paper_data.get('reference_style', 'APA')}
Target Audience: {paper_data.get('target_audience', 'Academic')}

Previous sections: {', '.join(previous_sections.keys()) if previous_sections else 'None'}

Please ensure the section:
1. Maintains consistency with previous sections
2. Uses proper academic language
3. Follows the specified reference style
4. Is appropriate for the target audience
5. Aligns with the paper's objectives
6. Maintains professional tone
"""

    section_prompts = {
        'abstract': f"""Generate an abstract that:
1. Provides a concise overview of the research topic
2. States the research problem and objectives
3. Briefly describes the methodology
4. Summarizes key findings
5. Concludes with the significance of the research
6. Should be between 150-250 words
7. Follow {paper_data.get('reference_style', 'APA')} style guidelines""",

        'introduction': f"""Generate an introduction section that:
1. Provides background information on the research topic
2. Clearly states the research problem and its significance
3. Reviews relevant literature and identifies gaps
4. States the research objectives and questions
5. Outlines the structure of the paper
6. Maintains a logical flow from general to specific
7. Includes proper citations in {paper_data.get('reference_style', 'APA')} style
8. Focus on recent trends and importance of the topic""",

        'literature_review': f"""Generate a literature review section that:
1. Critically analyzes existing research on the topic
2. Organizes literature thematically or chronologically
3. Identifies gaps in current research
4. Shows how this research builds on previous work
5. Synthesizes findings from multiple sources
6. Includes proper citations in {paper_data.get('reference_style', 'APA')} style
7. Maintains academic tone and objectivity
8. Focus on existing methods and previous studies""",

        'methodology': f"""Generate a methodology section that:
1. Clearly describes the research design
2. Details data collection methods
3. Explains sampling techniques
4. Describes data analysis procedures
5. Addresses ethical considerations
6. Justifies methodological choices
7. Includes proper citations for methods used
8. Focus on techniques, approaches, and frameworks""",

        'results': f"""Generate a results section that:
1. Presents findings clearly and objectively
2. Uses appropriate tables and figures
3. Organizes results logically
4. Includes statistical analysis if applicable
5. Highlights key findings
6. Maintains consistency with methodology
7. Avoids interpretation or discussion
8. Focus on evaluation metrics and performance""",

        'discussion': f"""Generate a discussion section that:
1. Interprets the results
2. Compares findings with previous research
3. Explains unexpected results
4. Addresses limitations
5. Suggests implications for practice
6. Proposes future research directions
7. Maintains academic tone and objectivity
8. Focus on implications and impact""",

        'conclusion': f"""Generate a conclusion section that:
1. Summarizes key findings
2. Restates research significance
3. Addresses research objectives
4. Highlights contributions to the field
5. Suggests practical applications
6. Maintains consistency with previous sections
7. Provides a strong closing statement
8. Focus on future work and limitations"""
    }
    
    # Get the specific prompt for the section, or use a default if not found
    specific_prompt = section_prompts.get(section_name.lower(), f"""Generate the {section_name} section that:
1. Follows academic writing standards
2. Maintains consistency with previous sections
3. Includes proper citations if needed
4. Is appropriate for the target audience
5. Aligns with the paper's objectives
6. Uses {paper_data.get('reference_style', 'APA')} style
7. Maintains professional tone""")
    
    return f"{base_info}\n{specific_prompt}"

async def generate_section(paper_data: dict, section_name: str, previous_sections: dict) -> str:
    """Generate content for a specific section of the paper"""
    try:
        # Get the prompt for this section
        section_prompt = get_section_prompt(section_name, paper_data, previous_sections)
        
        # Add reference papers content to the prompt if available
        if "reference_papers" in paper_data and paper_data["reference_papers"]:
            section_prompt += paper_data["reference_papers"]
        
        # Generate the content
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert academic writer helping to write a research paper. Use the provided references appropriately and maintain academic rigor. When citing references, use the format [number] where number is the reference number."},
                {"role": "user", "content": section_prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        
        # Extract references used in this section
        references_used = set(re.findall(r'\[(\d+)\]', content))
        
        # Store references in paper data
        if "references_used" not in paper_data:
            paper_data["references_used"] = set()
        paper_data["references_used"].update(references_used)
        
        # Humanize the content
        try:
            humanized_response = humanizer.humanize(content)
            return humanized_response.humanized_text
        except Exception as e:
            logger.error(f"Error humanizing section content: {str(e)}")
            return content  # Return original content if humanization fails
            
    except Exception as e:
        logger.error(f"Error generating section {section_name}: {str(e)}")
        raise 