"""
RAG Service for School Syllabus Integration
Provides context-aware AI responses based on school curriculum
INCLUDES ADAPTIVE CONTENT PRESENTATION FOR SPECIAL NEEDS (INVISIBLE TO STUDENT)
"""
from typing import Optional, List
from sqlmodel import Session, select

from .models import School, Student, SupportType

def get_syllabus_context(student: Student, session: Session, subject: Optional[str] = None) -> str:
    """
    Get relevant syllabus context for a student based on their school
    ADAPTS CONTENT PRESENTATION BASED ON SUPPORT TYPE (INVISIBLE)
    Returns formatted context to include in AI prompts
    """
    # 1. Check Schedule First (User Request)
    next_topic = get_next_scheduled_topic(student.id, session)
    
    # 2. Get School Syllabus (if available)
    school_syllabus = ""
    school = student.school
    if school and school.syllabus_text:
        school_syllabus = school.syllabus_text

    # 3. Get System Fallback Syllabus
    system_syllabus = get_system_syllabus(student.student_class, subject)
    
    # Determine which context to use
    final_context = ""
    context_source = ""
    
    if subject:
        # If subject is specific, try to find it in school syllabus first
        if school_syllabus:
            extracted = extract_subject_context(school_syllabus, subject)
            if extracted != school_syllabus: # Found specific section
                final_context = extracted
                context_source = "School Syllabus"
        
        # If not found in school syllabus (or no school syllabus), use system fallback
        if not final_context and system_syllabus:
            final_context = system_syllabus
            context_source = "International Standard Curriculum"
            
    else:
        # General context (e.g. "what should I learn?")
        # Priority: Schedule > School > System
        if next_topic:
            final_context = f"Scheduled Topic: {next_topic}"
            context_source = "Student Schedule"
        elif school_syllabus:
            final_context = school_syllabus[:2000]
            context_source = "School Syllabus"
        else:
            final_context = system_syllabus
            context_source = "International Standard Curriculum"
    
    # Adapt content based on support type (INVISIBLE TO STUDENT)
    final_context = adapt_content_for_support_type(final_context, student.support_type)
    
    # Format context for AI prompt with adaptive instructions
    formatted_context = f"""
SCHOOL CURRICULUM CONTEXT ({context_source}):
School: {school.name if school else 'Not Enrolled'}
Grade Levels: {school.grade_levels if school else 'N/A'}
Student Grade: {student.student_class}

Syllabus/Topic Content:
{final_context[:2500]} 

TEACHING INSTRUCTIONS:
1. Base your teaching on this curriculum content
2. If the user asks "What can we learn?", propose topics from the content above.
3. Use age-appropriate language for {student.student_class}
4. Connect to student's hobby: {student.hobby}
5. Don't mention the children disabilities or their grade.
{get_support_specific_instructions(student.support_type)}
"""
    
    return formatted_context

def get_next_scheduled_topic(student_id: int, session: Session) -> Optional[str]:
    """
    Get the next scheduled topic for the student
    """
    from .models import Timetable # Deferred import to avoid circular dependency
    from datetime import datetime
    
    # Find next session
    # For now, just finding any entry for today/tomorrow as a proxy
    # In a real app, this would query by day_of_week and time
    # This is a simplified "next topic" logic
    schedule = session.exec(select(Timetable).where(Timetable.student_id == student_id)).first()
    if schedule and schedule.activity_type == "study" and schedule.subject:
         return f"{schedule.subject}: {schedule.focus_topic or 'General Review'}"
    return None

def get_system_syllabus(grade: str, subject: Optional[str] = None) -> str:
    """
    Fallback International Standard Curriculum
    """
    # Simple hardcoded map for Hackathon purposes
    # Expand this for production
    
    curriculum_map = {
        "JSS1": {
            "mathematics": "Whole Numbers, Basic Geometry, Fractions, Decimals, Algebra Introduction",
            "science": "Living Things, Matter, Energy, Forces, Earth and Space",
            "english": "Parts of Speech, Essay Writing, Comprehension, oral English",
            "general": "Basic Math, Intro to Science, English Grammar"
        },
        "JSS2": {
            "mathematics": "Algebraic Expressions, Linear Equations, Geometry (Angles), Statistics",
            "science": "Cells, Ecosystems, Periodic Table (Intro), Light and Sound",
            "english": "Narrative Writing, Poetry, Advanced Grammar, Literature",
            "general": "Algebra, Basic Biology, Creative Writing"
        },
        "JSS3": {
            "mathematics": "Quadratic Equations, Trig Ratios, Probability, Circle Geometry",
            "science": "Reproduction, Heredity, Chemical Reactions, Electricity",
            "english": "Persuasive Writing, Drama Analysis, Summary Writing",
            "general": "Geometry, Physics Intro, Literature Analysis"
        },
        "SSS1": {
             "mathematics": "Logarithms, Sets, Logical Reasoning, Trig Graphs",
             "science": "Physics (Motion), Chemistry (Atomic Structure), Biology (Classification)",
             "english": "Argumentative Essays, Speech Writing, Lexis and Structure",
             "general": "Advanced Algebra, Core Science Principles"
        }
    }
    
    # Normalize grade
    normalized_grade = "JSS1" # Default
    if "7" in grade or "jss1" in grade.lower(): normalized_grade = "JSS1"
    elif "8" in grade or "jss2" in grade.lower(): normalized_grade = "JSS2"
    elif "9" in grade or "jss3" in grade.lower(): normalized_grade = "JSS3"
    elif "10" in grade or "sss1" in grade.lower(): normalized_grade = "SSS1"
    
    grade_content = curriculum_map.get(normalized_grade, curriculum_map["JSS1"])
    
    if subject and subject.lower() in grade_content:
        return grade_content[subject.lower()]
    
    return grade_content.get("general", str(grade_content))

def adapt_content_for_support_type(content: str, support_type: SupportType) -> str:
    """
    Adapt syllabus content presentation based on support type
    INVISIBLE ADAPTATION - Never mentions the support type
    """
    if support_type == SupportType.DYSLEXIA:
        # Simplify complex sentences, break into smaller chunks
        # Focus on key concepts, reduce text density
        return simplify_for_dyslexia(content)
    
    elif support_type == SupportType.DOWN_SYNDROME:
        # Extract only core concepts, very simple language
        # Remove abstract concepts, focus on concrete examples
        return simplify_for_down_syndrome(content)
    
    elif support_type == SupportType.AUTISM:
        # Keep structure clear and predictable
        # Remove ambiguous language, make everything explicit
        return structure_for_autism(content)
    
    # Standard - return as is
    return content

def simplify_for_dyslexia(content: str) -> str:
    """
    Simplify content for students with dyslexia
    - Break long paragraphs into shorter ones
    - Focus on key points
    - Reduce text density
    """
    # Split into sentences
    sentences = content.replace('. ', '.\n').split('\n')
    
    # Keep sentences under 20 words, group into small paragraphs
    simplified = []
    current_para = []
    
    for sentence in sentences:
        words = sentence.split()
        if len(words) > 20:
            # Break long sentence into parts
            mid = len(words) // 2
            current_para.append(' '.join(words[:mid]) + '.')
            current_para.append(' '.join(words[mid:]))
        else:
            current_para.append(sentence)
        
        # Create paragraph every 2-3 sentences
        if len(current_para) >= 3:
            simplified.append(' '.join(current_para))
            current_para = []
    
    if current_para:
        simplified.append(' '.join(current_para))
    
    return '\n\n'.join(simplified)

def simplify_for_down_syndrome(content: str) -> str:
    """
    Simplify content for students with Down syndrome
    - Extract only main topics
    - Use very simple language
    - Focus on concrete, practical concepts
    """
    # Extract topic headings and first sentence of each section
    lines = content.split('\n')
    simplified = []
    
    for i, line in enumerate(lines):
        # Keep headings (usually shorter, capitalized)
        if len(line) < 50 and (line.isupper() or line.istitle()):
            simplified.append(line)
        # Keep first sentence of paragraphs
        elif line and i > 0 and not lines[i-1]:
            first_sentence = line.split('.')[0] + '.'
            if len(first_sentence.split()) < 15:  # Keep only short sentences
                simplified.append(first_sentence)
    
    return '\n'.join(simplified[:10])  # Limit to 10 key points

def structure_for_autism(content: str) -> str:
    """
    Structure content for students with autism
    - Clear, predictable structure
    - Explicit organization
    - No ambiguous language
    """
    # Add clear structure markers
    sections = content.split('\n\n')
    structured = []
    
    for i, section in enumerate(sections, 1):
        # Add explicit numbering and structure
        structured.append(f"Topic {i}:\n{section}")
    
    return '\n\n'.join(structured)

def get_support_specific_instructions(support_type: SupportType) -> str:
    """
    Get teaching instructions specific to support type
    NEVER MENTIONS THE SUPPORT TYPE TO MAINTAIN INCLUSIVITY
    """
    if support_type == SupportType.DYSLEXIA:
        return """5. Use clear, simple sentences
6. Break complex ideas into small steps
7. Use visual descriptions and analogies
8. Repeat key concepts in different ways"""
    
    elif support_type == SupportType.DOWN_SYNDROME:
        return """5. Use very simple, concrete language
6. Focus on one concept at a time
7. Use real-world examples they can relate to
8. Provide extra encouragement and patience"""
    
    elif support_type == SupportType.AUTISM:
        return """5. Be clear and literal in explanations
6. Provide structured, predictable responses
7. Use specific examples, avoid abstract metaphors
8. Be consistent in teaching approach"""
    
    return """5. Use age-appropriate language
6. Make learning engaging and fun
7. Encourage questions and curiosity"""

def extract_subject_context(syllabus_text: str, subject: str) -> str:
    """
    Extract subject-specific content from syllabus
    Simple keyword-based extraction (can be enhanced with embeddings later)
    """
    # Convert to lowercase for matching
    syllabus_lower = syllabus_text.lower()
    subject_lower = subject.lower()
    
    # Common subject keywords
    subject_keywords = {
        "mathematics": ["math", "mathematics", "arithmetic", "algebra", "geometry", "calculus"],
        "science": ["science", "biology", "chemistry", "physics", "nature"],
        "english": ["english", "language", "reading", "writing", "literature"],
        "history": ["history", "social studies", "geography"],
        "art": ["art", "music", "drama", "creative"]
    }
    
    # Find matching keywords
    keywords = subject_keywords.get(subject_lower, [subject_lower])
    
    # Split syllabus into sections (by paragraphs or headings)
    sections = syllabus_text.split('\n\n')
    
    # Find relevant sections
    relevant_sections = []
    for section in sections:
        section_lower = section.lower()
        if any(keyword in section_lower for keyword in keywords):
            relevant_sections.append(section)
    
    if relevant_sections:
        return '\n\n'.join(relevant_sections)
    
    # If no specific match, return full syllabus
    return syllabus_text

def chunk_syllabus(syllabus_text: str, chunk_size: int = 500) -> List[str]:
    """
    Split syllabus into chunks for better context management
    Useful for future vector embedding implementation
    """
    # Split by paragraphs first
    paragraphs = syllabus_text.split('\n\n')
    
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) < chunk_size:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def search_syllabus(syllabus_text: str, query: str, top_k: int = 3) -> List[str]:
    """
    Simple keyword-based search in syllabus
    Returns top_k most relevant chunks
    Can be enhanced with semantic search using embeddings
    """
    chunks = chunk_syllabus(syllabus_text)
    query_lower = query.lower()
    
    # Score chunks based on keyword overlap
    scored_chunks = []
    for chunk in chunks:
        chunk_lower = chunk.lower()
        # Count query word occurrences
        score = sum(1 for word in query_lower.split() if word in chunk_lower)
        scored_chunks.append((score, chunk))
    
    # Sort by score and return top_k
    scored_chunks.sort(reverse=True, key=lambda x: x[0])
    return [chunk for score, chunk in scored_chunks[:top_k] if score > 0]

# Future enhancement: Vector embeddings for semantic search
# def embed_syllabus(syllabus_text: str) -> List[float]:
#     """Generate embeddings for syllabus chunks using sentence transformers"""
#     pass
#
# def semantic_search(query: str, syllabus_embeddings: List[float]) -> List[str]:
#     """Perform semantic search using cosine similarity"""
#     pass
