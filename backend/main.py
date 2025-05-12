from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from sqlalchemy.orm import Session
import models
from database import engine, get_db
import uuid
import os
import logging
import traceback
from dotenv import load_dotenv
from chatgpt import create_research_paper_prompt, generate_research_paper, generate_paper_titles, generate_abstract, generate_section
from models import ResearchPaper
import json
from openai import OpenAI
from datetime import datetime
from openalex_search import OpenAlexSearch
import re

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# OpenAlex singleton instance
_openalex_instance = None

def get_openalex() -> OpenAlexSearch:
    """Get or create the OpenAlexSearch instance"""
    global _openalex_instance
    if _openalex_instance is None:
        _openalex_instance = OpenAlexSearch()
    return _openalex_instance

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console handler
        logging.FileHandler('app.log')  # File handler
    ]
)
logger = logging.getLogger(__name__)

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Add CORS middleware with more permissive settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins during development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# User models and endpoints
class UserCreate(BaseModel):
    firstName: str
    lastName: str
    email: str
    phone: str
    address: str
    city: str
    state: str
    zipCode: str
    interests: List[str]

    class Config:
        from_attributes = True

# Research Paper models
class ResearchPaperRequest(BaseModel):
    topic: str
    keywords: List[str]
    length: str
    academic_field: str
    paper_type: str
    sections: List[str]
    reference_style: str
    guidelines: Optional[str] = None
    target_audience: Optional[str] = None

class ResearchPaperResponse(BaseModel):
    paper_id: str
    status: str
    generated_content: Optional[str] = None

class TitleRequest(BaseModel):
    topic: str
    keywords: List[str]
    length: Optional[str] = None
    academic_field: Optional[str] = None
    paper_type: Optional[str] = None
    reference_style: Optional[str] = None
    target_audience: Optional[str] = None
    required_sections: Optional[List[str]] = None
    custom_sections: Optional[List[str]] = None
    additional_guidelines: Optional[str] = None

class AbstractEditRequest(BaseModel):
    paper_id: str
    abstract: str
    edit_instructions: str

class EditHistoryItem(BaseModel):
    timestamp: str
    instructions: str
    previous_content: str
    new_content: str

class SectionGenerationRequest(BaseModel):
    section: str

class SectionConfirmationRequest(BaseModel):
    section: str

class SectionEditRequest(BaseModel):
    paper_id: str
    section_name: str
    current_content: str
    edit_instructions: str

# User endpoints
@app.get("/")
async def root():
    return {"message": "Hello from FastAPI backend!"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/users")
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if email already exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    db_user = models.User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return {"message": "User created successfully", "user": db_user}

@app.get("/api/users")
async def get_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return {"users": users}

# Research Paper endpoints
@app.post("/api/research-papers/titles")
async def generate_titles(request: TitleRequest):
    try:
        logger.debug(f"Received title generation request: {request.dict()}")
        
        # Validate required fields
        if not request.topic:
            raise ValueError("Topic is required")
        if not request.keywords:
            raise ValueError("Keywords are required")
            
        # Prepare data for title generation
        title_data = {
            "topic": request.topic,
            "keywords": request.keywords,
            "length": request.length or "medium",
            "academic_field": request.academic_field or "general",
            "paper_type": request.paper_type or "research",
            "reference_style": request.reference_style or "APA",
            "target_audience": request.target_audience or "academic",
            "required_sections": request.required_sections or [],
            "custom_sections": request.custom_sections or [],
            "additional_guidelines": request.additional_guidelines or ""
        }
        
        # Generate titles
        titles = await generate_paper_titles(title_data)
        logger.debug(f"Generated titles: {titles}")
        
        return {"titles": titles}
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating titles: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/research-papers/start")
async def start_paper_generation(paper_data: dict, db: Session = Depends(get_db)):
    try:
        # Ensure there's at least one section to work with
        if not paper_data["required_sections"] and not paper_data["custom_sections"]:
            raise ValueError("At least one section (required or custom) must be selected")
            
        # Use custom section as first section if no required sections are selected
        first_section = paper_data["required_sections"][0] if paper_data["required_sections"] else paper_data["custom_sections"][0]
        
        # Create new research paper record
        paper = ResearchPaper(
            topic=paper_data["topic"],
            keywords=",".join(paper_data["keywords"]) if isinstance(paper_data["keywords"], list) else paper_data["keywords"],
            length=paper_data["length"],
            academic_field=paper_data["academic_field"],
            paper_type=paper_data["paper_type"],
            reference_style=paper_data["reference_style"],
            target_audience=paper_data["target_audience"],
            required_sections=paper_data["required_sections"],
            custom_sections=paper_data["custom_sections"],
            additional_guidelines=paper_data["additional_guidelines"],
            selected_title=paper_data["selected_title"],
            generation_status="in_progress",
            current_section=first_section,  # Use the determined first section
            section_content={}
        )
        
        # Add paper to session
        db.add(paper)
        db.flush()
        
        # Only generate abstract if it's the first required section
        if paper.current_section == "abstract":
            abstract_content = await generate_abstract(paper_data)
            paper.section_content = {"abstract": abstract_content}
        
        db.commit()
        
        return {
            "paper_id": str(paper.id),
            "current_section": paper.current_section,
            "status": "in_progress"
        }
    except Exception as e:
        if 'db' in locals():
            db.rollback()
        logger.error(f"Error starting paper generation: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'db' in locals():
            db.close()

@app.post("/api/research-papers/{paper_id}/generate-next")
async def generate_next_section(paper_id: str, db: Session = Depends(get_db)):
    try:
        # Get the paper
        paper = db.query(ResearchPaper).filter(ResearchPaper.id == paper_id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        # Get the next section to generate
        all_sections = paper.required_sections + paper.custom_sections
        current_index = all_sections.index(paper.current_section) if paper.current_section in all_sections else -1
        next_section = all_sections[current_index + 1] if current_index + 1 < len(all_sections) else None
        
        if not next_section:
            paper.generation_status = "completed"
            db.commit()
            return {
                "status": "completed",
                "message": "All sections have been generated"
            }
        
        # Generate the next section
        section_content = await generate_section(
            paper_data={
                "topic": paper.topic,
                "keywords": paper.keywords.split(","),
                "length": paper.length,
                "academic_field": paper.academic_field,
                "paper_type": paper.paper_type,
                "reference_style": paper.reference_style,
                "target_audience": paper.target_audience,
                "selected_title": paper.selected_title
            },
            section_name=next_section,
            previous_sections=paper.section_content
        )
        
        # Update paper with new section
        paper.section_content[next_section] = section_content
        paper.current_section = next_section
        db.commit()
        
        return {
            "current_section": next_section,
            "content": section_content,
            "next_section": all_sections[current_index + 2] if current_index + 2 < len(all_sections) else None
        }
    except Exception as e:
        if 'db' in locals():
            db.rollback()
        logger.error(f"Error generating next section: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'db' in locals():
            db.close()

@app.get("/api/research-papers", response_model=List[ResearchPaperResponse])
async def get_research_papers(db: Session = Depends(get_db)):
    papers = db.query(ResearchPaper).all()
    return papers

@app.get("/api/research-papers/{paper_id}", response_model=ResearchPaperResponse)
async def get_research_paper(paper_id: str, db: Session = Depends(get_db)):
    try:
        paper = db.query(ResearchPaper).filter(ResearchPaper.paper_id == paper_id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Research paper not found")
        return ResearchPaperResponse(
            paper_id=paper.paper_id,
            status=paper.status,
            generated_content=paper.generated_content
        )
    except Exception as e:
        logger.error(f"Error retrieving paper: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/research-papers/{paper_id}/edit-abstract")
async def edit_abstract(paper_id: str, request: AbstractEditRequest, db: Session = Depends(get_db)):
    try:
        # Get the paper
        paper = db.query(ResearchPaper).filter(ResearchPaper.id == paper_id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        # Create a prompt for editing the abstract
        prompt = f"""Please edit the following abstract based on these instructions:

Abstract to edit:
{request.abstract}

Edit instructions:
{request.edit_instructions}

Previous edit history:
{json.dumps(paper.edit_history or [], indent=2) if paper.edit_history else "No previous edits"}

Please provide the edited abstract that:
1. Maintains academic writing standards
2. Follows the specified reference style ({paper.reference_style})
3. Is appropriate for the target audience ({paper.target_audience})
4. Incorporates the requested changes
5. Maintains proper formatting and structure
6. Takes into account previous edits and feedback

Return only the edited abstract text."""

        # Generate the edited abstract
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an academic editor helping to improve research paper abstracts."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )

        edited_abstract = response.choices[0].message.content

        # Create new edit history item
        new_edit = EditHistoryItem(
            timestamp=datetime.now().isoformat(),
            instructions=request.edit_instructions,
            previous_content=request.abstract,
            new_content=edited_abstract
        )

        # Update paper with new abstract and edit history
        current_history = paper.edit_history or []
        current_history.append(new_edit.dict())
        
        paper.section_content = {"abstract": edited_abstract}
        paper.edit_history = current_history
        db.commit()

        return {
            "edited_abstract": edited_abstract,
            "status": "success",
            "edit_history": current_history
        }

    except Exception as e:
        if 'db' in locals():
            db.rollback()
        logger.error(f"Error editing abstract: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'db' in locals():
            db.close()

@app.get("/api/research-papers/{paper_id}/edit-history")
async def get_edit_history(paper_id: str, db: Session = Depends(get_db)):
    try:
        paper = db.query(ResearchPaper).filter(ResearchPaper.id == paper_id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        return {
            "edit_history": paper.edit_history or []
        }
    except Exception as e:
        logger.error(f"Error retrieving edit history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/research-papers/{paper_id}/confirm-abstract")
async def confirm_abstract(paper_id: str, db: Session = Depends(get_db)):
    try:
        # Get the paper
        paper = db.query(ResearchPaper).filter(ResearchPaper.id == paper_id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        # Update the paper status to indicate abstract is confirmed
        paper.generation_status = "abstract_confirmed"
        db.commit()

        return {
            "status": "success",
            "message": "Abstract confirmed successfully"
        }

    except Exception as e:
        if 'db' in locals():
            db.rollback()
        logger.error(f"Error confirming abstract: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'db' in locals():
            db.close()

@app.post("/api/research-papers/{paper_id}/generate-section")
async def generate_section_content(paper_id: str, request: SectionGenerationRequest, db: Session = Depends(get_db)):
    try:
        logger.info(f"Generating section for paper {paper_id}, section: {request.section}")
        paper = db.query(ResearchPaper).filter(ResearchPaper.id == paper_id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        logger.info(f"Found paper with title: {paper.selected_title}, keywords: {paper.keywords}")
        
        # Get reference papers content for the specific section
        logger.info("Starting reference paper search and download")
        reference_papers = get_openalex().get_reference_papers_content(
            keywords=paper.keywords.split(",") if paper.keywords else [],
            title=paper.selected_title,
            section=request.section
        )
        logger.info(f"Found {len(reference_papers['papers'])} reference papers for section {request.section}")

        # Create prompt with reference papers content
        reference_content = ""
        if reference_papers["papers"]:
            reference_content = "\n\nHere are some relevant reference papers for this section:\n"
            for ref_paper in reference_papers["papers"]:
                reference_content += f"\nTitle: {ref_paper['title']}\n"
                reference_content += f"Authors: {', '.join(ref_paper['authors'])}\n"
                reference_content += f"Abstract: {ref_paper['abstract']}\n"
            reference_content += "\nPlease use these references in your response and cite them appropriately."
            logger.info("Added reference papers to the prompt")
        else:
            logger.warning("No reference papers found or downloaded")

        # Generate the section content
        logger.info("Generating section content with references")
        section_content = await generate_section(
            paper_data={
                "topic": paper.topic,
                "keywords": paper.keywords.split(",") if paper.keywords else [],
                "length": paper.length,
                "academic_field": paper.academic_field,
                "paper_type": paper.paper_type,
                "reference_style": paper.reference_style,
                "target_audience": paper.target_audience,
                "selected_title": paper.selected_title,
                "reference_papers": reference_content
            },
            section_name=request.section,
            previous_sections=paper.section_content or {}
        )

        # Update the paper with the new section content while preserving existing content
        current_content = paper.section_content or {}
        current_content[request.section] = section_content
        
        # Initialize references section if it doesn't exist
        if "references" not in current_content:
            current_content["references"] = "\n\n## References\n\n"
        
        # Update references section with any new references
        if reference_papers["papers"]:
            references_section = current_content.get("references", "\n\n## References\n\n")
            for ref_paper in reference_papers["papers"]:
                # Format citation using available paper details
                citation = f"{', '.join(ref_paper['authors'])} ({ref_paper['publication_year']}). {ref_paper['title']}. "
                if ref_paper['doi']:
                    citation += f"DOI: {ref_paper['doi']}"
                # Check if reference already exists in the references section
                if citation not in references_section:
                    references_section += f"{citation}\n\n"
            current_content["references"] = references_section
        
        paper.section_content = current_content
        paper.current_section = request.section
        db.commit()

        logger.info(f"Successfully generated section {request.section}")

        return {
            "content": section_content,
            "status": "success",
            "all_sections": current_content,
            "references": current_content["references"]  # Return the updated references section
        }

    except Exception as e:
        if 'db' in locals():
            db.rollback()
        logger.error(f"Error generating section: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'db' in locals():
            db.close()

@app.post("/api/research-papers/{paper_id}/confirm-section")
async def confirm_section(paper_id: str, request: SectionConfirmationRequest, db: Session = Depends(get_db)):
    try:
        paper = db.query(ResearchPaper).filter(ResearchPaper.id == paper_id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        # Update the paper status
        confirmed_sections = paper.confirmed_sections or []
        if request.section not in confirmed_sections:
            confirmed_sections.append(request.section)
            paper.confirmed_sections = confirmed_sections

        # Check if all sections are confirmed
        if set(confirmed_sections) == set(paper.required_sections):
            paper.generation_status = "completed"
        else:
            paper.generation_status = "in_progress"

        db.commit()

        return {
            "status": "success",
            "message": f"Section {request.section} confirmed successfully",
            "next_section": next((s for s in paper.required_sections if s not in confirmed_sections), None)
        }

    except Exception as e:
        if 'db' in locals():
            db.rollback()
        logger.error(f"Error confirming section: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'db' in locals():
            db.close()

@app.post("/api/research-papers/{paper_id}/edit-section")
async def edit_section(paper_id: str, request: SectionEditRequest, db: Session = Depends(get_db)):
    try:
        # Get the paper
        paper = db.query(ResearchPaper).filter(ResearchPaper.id == paper_id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        # Create a prompt for editing the section
        prompt = f"""Please edit the following {request.section_name} section based on these instructions:

Section to edit:
{request.current_content}

Edit instructions:
{request.edit_instructions}

Previous edit history:
{json.dumps(paper.edit_history or [], indent=2) if paper.edit_history else "No previous edits"}

Please provide the edited section that:
1. Maintains academic writing standards
2. Follows the specified reference style ({paper.reference_style})
3. Is appropriate for the target audience ({paper.target_audience})
4. Incorporates the requested changes
5. Maintains proper formatting and structure
6. Takes into account previous edits and feedback
7. Maintains consistency with other sections of the paper

Return only the edited section text."""

        # Generate the edited section
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": f"You are an academic editor helping to improve research paper {request.section_name} sections."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )

        improved_content = response.choices[0].message.content

        # Create new edit history item
        new_edit = EditHistoryItem(
            timestamp=datetime.now().isoformat(),
            instructions=request.edit_instructions,
            previous_content=request.current_content,
            new_content=improved_content
        )

        # Update paper with new section content and edit history
        current_history = paper.edit_history or []
        current_history.append(new_edit.dict())
        
        section_content = paper.section_content or {}
        section_content[request.section_name] = improved_content
        paper.section_content = section_content
        paper.edit_history = current_history
        db.commit()

        return {
            "improved_content": improved_content,
            "status": "success",
            "edit_history": current_history
        }

    except Exception as e:
        if 'db' in locals():
            db.rollback()
        logger.error(f"Error editing section: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 