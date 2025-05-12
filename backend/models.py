from sqlalchemy import Column, Integer, String, ARRAY, Enum, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base
import enum

class PaperLength(str, enum.Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"

class PaperType(str, enum.Enum):
    REVIEW = "review"
    EXPERIMENTAL = "experimental"
    CONCEPTUAL = "conceptual"

class ReferenceStyle(str, enum.Enum):
    APA = "apa"
    IEEE = "ieee"
    MLA = "mla"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    firstName = Column(String, nullable=False)
    lastName = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    phone = Column(String, nullable=False)
    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    zipCode = Column(String, nullable=False)
    interests = Column(ARRAY(String), nullable=False)
    hashed_password = Column(String)
    is_active = Column(Integer, default=1)

    research_papers = relationship("ResearchPaper", back_populates="owner")

class ResearchPaper(Base):
    __tablename__ = "research_papers"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, nullable=False)
    keywords = Column(String, nullable=False)  # Store as comma-separated string
    length = Column(String, nullable=True)
    academic_field = Column(String, nullable=False)
    paper_type = Column(String, nullable=False)
    reference_style = Column(String, nullable=False)
    target_audience = Column(String, nullable=False)
    required_sections = Column(JSON, nullable=False)  # Store as JSON array
    custom_sections = Column(JSON, nullable=False)  # Store as JSON array
    additional_guidelines = Column(Text, nullable=True)
    selected_title = Column(String, nullable=False)
    current_section = Column(String, nullable=True)  # Track current section being generated
    section_content = Column(JSON, nullable=True)  # Store content for each section
    generation_status = Column(String, default="not_started")  # not_started, in_progress, completed
    edit_history = Column(JSON, nullable=True)  # Store edit history as JSON
    confirmed_sections = Column(JSON, nullable=True)  # Store confirmed sections as JSON array
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    owner = relationship("User", back_populates="research_papers") 