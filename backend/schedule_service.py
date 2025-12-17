"""
AI Schedule Generation Function
Generates personalized weekly study schedule based on syllabus
"""
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Initialize Groq client
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL")

# Only initialize if API key is set
groq_client = None
if GROQ_API_KEY and GROQ_API_KEY != "your_groq_api_key_here":
    from groq import Groq
    groq_client = Groq(api_key=GROQ_API_KEY)

# Nigerian Curriculum Standards - Class-Level Topic Mapping
CLASS_LEVEL_STANDARDS = {
    # --- PRIMARY SCHOOL ---
    "Primary 1": {
        "English": ["Alphabet recognition", "Phonics and letter sounds", "Simple three-letter words", "Basic sentence construction", "Oral English"],
        "Mathematics": ["Numbers 1-100", "Counting", "Basic Addition and Subtraction", "Shapes", "Patterns", "Measurement"],
        "Science": ["Parts of the body", "Our senses", "Living and non-living things", "Plants and animals", "Personal hygiene", "Safety"],
        "Social Studies": ["Myself and family", "My home and school", "Community", "Basic needs", "Safety rules", "Days and months"]
    },
    "Primary 2": {
        "English": ["Reading simple sentences", "Spelling common words", "Nouns, pronouns, verbs", "Punctuation", "Composition (3-5 sentences)"],
        "Mathematics": ["Numbers 1-500", "2-digit Addition/Subtraction", "Intro to Multiplication", "Money", "Time", "2D and 3D shapes"],
        "Science": ["Food and nutrition", "Air, water, soil", "Simple machines", "Weather and seasons", "Animals and habitats"],
        "Social Studies": ["Neighborhood", "Occupations", "Transportation", "Nigerian culture", "Good citizenship"]
    },
    "Primary 3": {
        "English": ["Reading comprehension", "Parts of speech", "Tenses", "Composition (paragraphs)", "Letter writing (informal)", "Spelling"],
        "Mathematics": ["Numbers to 1,000", "Four basic operations", "Fractions", "Measurement", "Money problems", "Perimeter and area"],
        "Science": ["Human body systems", "Energy (light, heat, sound)", "Magnets and electricity", "Rocks and soil", "Life cycles", "Pollution"],
        "Social Studies": ["Communities", "National symbols", "Government and leadership", "Natural resources", "Festivals", "Road safety"]
    },
    "Primary 4": {
        "English": ["Advanced comprehension", "Grammar (adverbs, prepositions)", "Composition (narrative)", "Letter writing", "Summary writing"],
        "Mathematics": ["Numbers to 10,000", "Basic operations", "Fractions and decimals", "Percentages", "Area and perimeter", "Data handling"],
        "Science": ["Reproductive system", "States of matter", "Forces and motion", "Electricity", "Solar system", "Diseases"],
        "Social Studies": ["Nigerian history", "Map reading", "Economic activities", "Cultural diversity", "Rights and responsibilities"]
    },
    "Primary 5": {
        "English": ["Complex comprehension", "Advanced grammar", "Essay writing", "Speech writing", "Debates", "Literature"],
        "Mathematics": ["Numbers to 1,000,000", "Fractions/Decimals/Percentages", "Ratio and proportion", "Simple interest", "Angles", "Statistics"],
        "Science": ["Cells and tissues", "Photosynthesis", "Heat and temperature", "Chemical changes", "Machines", "Space exploration"],
        "Social Studies": ["Colonial history", "Government structure", "International organizations", "Trade", "Population", "Democracy"]
    },
    "Primary 6": {
        "English": ["Advanced reading", "Complex grammar", "Formal letters", "Report writing", "Literature", "Exam techniques"],
        "Mathematics": ["Large numbers operations", "Advanced fractions/decimals", "Intro to Algebra", "Geometry", "Data interpretation", "Word problems"],
        "Science": ["Human body (review)", "Acids, bases, salts", "Work and energy", "Electronics", "Ecology", "JSS prep"],
        "Social Studies": ["Independence", "West African history", "World geography", "Economic development", "Social problems", "Citizenship"]
    },

    # --- JUNIOR SECONDARY SCHOOL ---
    "JSS 1": {
        "Mathematics": ["Whole Numbers", "Basic Operations", "Fractions/Decimals", "Intro to Algebra", "Basic Geometry", "Measurement", "Statistics"],
        "English": ["Parts of Speech", "Reading Comprehension", "Vocabulary", "Essay Writing", "Letter Writing", "Oral English"],
        "Science": ["Living Things", "Matter", "Energy", "Simple Machines", "Human Body", "Classification"],
        "Social Studies": ["History and Culture", "Geography", "Civic Education", "Family"],
        "Business Studies": ["Intro to Business", "Factors of Production", "Office Practice"],
        "Basic Technology": ["Materials", "Technical Drawing", "Safety"]
    },
    "JSS 2": {
        "Mathematics": ["Algebraic Expressions", "Angles and Triangles", "Quadrilaterals", "Ratio/Proportion", "Statistics", "Coordinate Geometry", "Mensuration"],
        "English": ["Advanced Grammar", "Comprehension", "Composition", "Speech Work", "Literature", "Formal Writing"],
        "Science": ["Chemical Reactions", "Force/Motion/Energy", "Electricity", "Reproduction", "Ecosystem", "Solar System"],
        "Social Studies": ["Government/Politics", "Economic Activities", "Map Reading", "Social Issues"],
        "Business Studies": ["Office Equipment", "Banking", "Marketing"],
        "Basic Technology": ["Woodwork/Metalwork", "Electrical Circuits", "Building Construction"]
    },
    "JSS 3": {
        "Mathematics": ["Linear Equations", "Quadratic Equations", "Pythagoras Theorem", "Circle Theorems", "Trigonometry", "Probability", "Logical Reasoning"],
        "English": ["Advanced Composition", "Critical Reading", "Literature Analysis", "Debate", "Report Writing", "Exam Techniques"],
        "Science": ["Acids/Bases/Salts", "Organic Chemistry Basics", "Laws of Motion", "Work/Energy/Power", "Genetics", "Environmental Science"],
        "Social Studies": ["Constitution/Democracy", "International Relations", "Economic Development", "Contemporary Issues"],
        "Business Studies": ["Business Law", "Consumer Protection", "Entrepreneurship"],
        "Basic Technology": ["Electronics", "technical Drawing", "Energy Transmission"]
    },

    # --- SENIOR SECONDARY SCHOOL (SS 1) ---
    "SS 1": {
        "Mathematics": ["Surds and Indices", "Logarithms", "Sequence and Series", "Quadratic Equations", "Trigonometry", "Sets/Probability"],
        "English": ["Summary Writing", "Comprehension", "Oral English", "Essay Writing", "Letter Writing", "Literature"],
        "Civic Education": ["Democracy", "Constitutionalism", "Human Rights"],
        
        # Science Stream
        "Biology": ["Cell Biology", "Classification", "Nutrition", "Transport Systems", "Respiration"],
        "Chemistry": ["Particulate Matter", "Atomic Structure", "Chemical Equations", "Acids/Bases", "Periodic Table"],
        "Physics": ["Measurement", "Motion", "Force/Energy", "Waves"],
        
        # Arts/Commercial
        "Government": ["Political Systems", "Nigerian Government", "Constitutions"],
        "Economics": ["Basic Concepts", "Production", "Demand/Supply", "Market Structures"],
        "Literature": ["Drama", "Prose", "Poetry", "Literary Appreciation"],
        "Commerce": ["Trade", "Documents", "Distribution", "Business Organizations"],
        "Accounting": ["Double Entry", "Bookkeeping", "Ledgers", "Trial Balance"]
    },

    # --- SENIOR SECONDARY SCHOOL (SS 2) ---
    "SS 2": {
        "Mathematics": ["Differentiation", "Integration Basics", "Linear Programming", "Advanced Statistics", "Coordinate Geometry", "Trig Identities"],
        "English": ["Advanced Summary", "Oral Literature", "Idiomatic Expressions", "Argumentative Essays", "Formal Applications"],
        "Civic Education": ["Rule of Law", "Elections", "Public Service"],
        
        # Science Stream
        "Biology": ["Genetics", "Ecology", "Reproductive Systems", "Growth"],
        "Chemistry": ["Hydrocarbons", "Alcohols/Acids", "Reaction Rates", "Equilibrium", "Electrochemistry"],
        "Physics": ["Electricity/Magnetism", "Heat/Thermodynamics", "Modern Physics"],
        
        # Arts/Commercial
        "Government": ["Political Parties", "Public Admin", "International Relations", "Federalism"],
        "Economics": ["National Income", "Money/Banking", "International Trade", "Public Finance"],
        "Literature": ["Classical Drama", "African Prose", "Poetry Analysis", "Literary Devices"],
        "Commerce": ["Banking", "Insurance", "Warehousing", "International Trade"],
        "Accounting": ["Manufacturing Accounts", "Partnerships", "Company Accounts", "Financial Statements"]
    },

    # --- SENIOR SECONDARY SCHOOL (SS 3) ---
    "SS 3": {
        "Mathematics": ["Revision (All Topics)", "Advanced Problem Solving", "Calculus Applications", "Advanced Trigonometry", "Exam Practice"],
        "English": ["Exam Practice", "Advanced Oral English", "Essay Mastery", "Literary Devices", "Past Questions"],
        "Civic Education": ["Governance Structures", "Political Issues", "Democratic Principles"],
        
        # Science Stream
        "Biology": ["Ecology/Environment", "Evolution", "Practical Techniques", "Exam Prep"],
        "Chemistry": ["Organic Chemistry", "Industrial Chemistry", "Analysis", "Exam Prep"],
        "Physics": ["Advanced Mechanics", "Electronics", "Modern Physics", "Exam Prep"],
        
        # Arts/Commercial
        "Government": ["Comparative Politics", "Nigerian Political System", "International Orgs"],
        "Economics": ["Applied Economics", "Nigerian Economy", "Data Interpretation"],
        "Literature": ["Set Texts Analysis", "Comparative Literature", "Critical Essays"],
        "Commerce": ["E-commerce", "Business Case Studies", "Commercial Law", "Exam Prep"],
        "Accounting": ["Advanced Company Accounts", "Accounting Standards", "Public Sector Acct"]
    }
}


def get_class_level_topics(student_class: str, syllabus_content: str) -> dict:
    """
    Extract class-appropriate topics from syllabus based on student's class level.
    
    Args:
        student_class: Student's class (e.g., "JSS 1", "JSS 2")
        syllabus_content: School's syllabus text
        
    Returns:
        dict: Subject-to-topics mapping for the class level
    """
    # Normalize class name for matching
    # Examples: "JSS 1", "JSS1", "Primary 4", "Grade 4"
    normalized_input = student_class.strip().upper()
    
    # helper to find key case-insensitively
    def find_key(search_term):
        for key in CLASS_LEVEL_STANDARDS.keys():
            if key.upper() == search_term:
                return CLASS_LEVEL_STANDARDS[key]
        return None

    # 1. Exact or simple normalized match
    match = find_key(normalized_input)
    if match: return match
    
    # 2. Handle Variations (removal of spaces)
    match = find_key(normalized_input.replace(" ", ""))
    if match: return match
    
    # 3. Specific Level Detection
    
    # PRIMARY
    if "PRIMARY" in normalized_input or "PRY" in normalized_input or "GRADE" in normalized_input or "BASIC" in normalized_input:
        # Extract number
        import re
        num_match = re.search(r'\d+', normalized_input)
        if num_match:
            level = num_match.group()
            key = f"Primary {level}"
            if key in CLASS_LEVEL_STANDARDS:
                return CLASS_LEVEL_STANDARDS[key]
        # Default Primary
        return CLASS_LEVEL_STANDARDS.get("Primary 1")
        
    # JSS / JUNIOR
    if "JSS" in normalized_input or "JUNIOR" in normalized_input:
        num_match = re.search(r'\d+', normalized_input)
        if num_match:
            level = num_match.group()
            key = f"JSS {level}"
            if key in CLASS_LEVEL_STANDARDS:
                return CLASS_LEVEL_STANDARDS[key]
        return CLASS_LEVEL_STANDARDS.get("JSS 1")

    # SS / SENIOR
    if "SS" in normalized_input or "SENIOR" in normalized_input:
        num_match = re.search(r'\d+', normalized_input)
        if num_match:
            level = num_match.group()
            key = f"SS {level}"
            if key in CLASS_LEVEL_STANDARDS:
                return CLASS_LEVEL_STANDARDS[key]
        return CLASS_LEVEL_STANDARDS.get("SS 1")
    
    # Fallback to JSS 1 if completely unknown
    return CLASS_LEVEL_STANDARDS["JSS 1"]


def generate_ai_schedule(student, syllabus_content: str, assignments: list, weak_subjects: list, performance_levels: dict = None, session=None) -> dict:
    """
    Generate AI-powered weekly study schedule
    
    Args:
        student: Student model instance
        syllabus_content: Text content of school syllabus
        assignments: List of upcoming assignments with deadlines
        weak_subjects: List of subjects where student needs improvement
        performance_levels: Dict with struggling/developing/proficient/mastery subjects
        session: Database session for Agent access
        
    Returns:
        dict: Weekly schedule with daily study sessions
    """
    if not groq_client:
        # Return mock schedule if Groq not configured
        return generate_mock_schedule()
    
    # Default performance levels if not provided
    if performance_levels is None:
        performance_levels = {
            "struggling": weak_subjects,
            "developing": [],
            "proficient": [],
            "mastery": []
        }
    
    # AGENTIC OPTIMIZATION
    agent_insights = ""
    if session:
        try:
            from .specialized_agents import SchedulingAgent
            agent = SchedulingAgent(student, session)
            
            # 1. Optimize Time Allocation
            # Get all subjects from performance levels
            all_subjects = []
            for sub_list in performance_levels.values():
                all_subjects.extend(sub_list)
            if not all_subjects: all_subjects = ["Mathematics", "English", "Science"]
            
            optimization = agent.optimize_study_time(
                subjects=list(set(all_subjects)),
                available_hours_per_day=1.5, # 90 mins typically
                priority_subjects=weak_subjects
            )
            
            # 2. Burnout Check
            burnout_check = agent.prevent_burnout({
                "hours_today": 2, # Estimate
                "sessions_today": 4,
                "consecutive_days": 5
            })
            
            # 3. Best Time
            best_time = agent.suggest_best_study_time()
            
            agent_insights = f"""
AGENTIC INSIGHTS (Use these to Refine Schedule):
- Recommended Daily Allocations: {json.dumps(optimization.get('daily_schedule', {}))} minutes
- Burnout Risk: {burnout_check.get('burnout_risk', 'low')} ({', '.join(burnout_check.get('recommendations', []))})
- Evaluation: The student studies best in the {best_time}.
- Strategy: {optimization.get('optimization_strategy', 'balanced')}
"""
        except Exception as e:
            print(f"Agent optimization failed: {e}")
            agent_insights = "Agent insights unavailable."

    # Determine age-appropriate guidelines
    age = student.age
    if age < 12:
        age_guidance = """
- Use simple, relatable examples from everyday Nigerian life
- Keep explanations short and engaging
- Use basic vocabulary and shorter sentences
- Include more frequent breaks and variety
- Focus on concrete, hands-on learning concepts"""
    elif age < 15:
        age_guidance = """
- Use intermediate complexity with real-world applications
- Balance abstract concepts with practical examples
- Use age-appropriate Nigerian cultural references
- Encourage critical thinking and problem-solving
- Build on foundational knowledge systematically"""
    else:
        age_guidance = """
- Use advanced concepts and abstract reasoning
- Include complex problem-solving and analysis
- Reference current events and real-world applications
- Encourage independent research and deeper exploration
- Prepare for higher education and career readiness"""
    
    # Build performance context
    performance_context = f"""
PERFORMANCE LEVELS:
- Struggling (needs foundational review): {', '.join(performance_levels.get('struggling', [])) or 'None'}
- Developing (needs practice): {', '.join(performance_levels.get('developing', [])) or 'None'}
- Proficient (ready for advancement): {', '.join(performance_levels.get('proficient', [])) or 'None'}
- Mastery (ready for challenges): {', '.join(performance_levels.get('mastery', [])) or 'None'}

LEARNING PRIORITIES:
1. For STRUGGLING subjects: Focus on foundational concepts, use simple examples, build confidence
2. For DEVELOPING subjects: Provide practice exercises, reinforce understanding, gradual progression
3. For PROFICIENT subjects: Introduce advanced topics, deepen understanding, connect concepts
4. For MASTERY subjects: Provide challenging problems, encourage exploration, advanced applications
"""
    
    # Get class-level appropriate topics
    class_topics = get_class_level_topics(student.student_class, syllabus_content)
    
    # Build class-level curriculum context
    curriculum_topics = "\n".join([
        f"- {subject}: {', '.join(topics)}"
        for subject, topics in class_topics.items()
    ])
    
    # Build topic sequencing rules
    sequencing_rules = """
TOPIC SEQUENCING RULES (CRITICAL - FOLLOW STRICTLY):
1. For STRUGGLING subjects:
   - Start with the FIRST/EARLIEST topics in the curriculum list
   - Use foundational, prerequisite concepts
   - Build confidence before advancing
   - Example: If struggling in Math, start with "Whole Numbers" before "Algebra"

2. For DEVELOPING subjects:
   - Use MIDDLE topics from the curriculum list
   - Reinforce core concepts with practice
   - Gradual progression to intermediate topics

3. For PROFICIENT subjects:
   - Use LATER/ADVANCED topics from the curriculum list
   - Introduce challenging concepts
   - Connect multiple topics together

4. For MASTERY subjects:
   - Use the MOST ADVANCED topics from the curriculum list
   - Provide extension activities and challenges
   - Encourage independent exploration

5. SPIRAL LEARNING:
   - Revisit topics with increasing complexity each week
   - Connect topics across subjects when possible
   - Build on previously mastered concepts

6. ASSIGNMENT ALIGNMENT:
   - Prioritize topics related to upcoming assignments
   - Schedule assignment prep 2-3 days before due date
   - Allocate extra time for assignment-related topics
"""

    prompt = f"""You are the Academic Scheduler at a UNICEF-partnered International School in Nigeria.
    MISSION: Create a balanced, effective study schedule for {student.full_name} ({student.age} yrs, {student.student_class}) that prioritizes well-being AND performance.

    STUDENT META-DATA:
    - Personality: {student.personality.value}
    - Interests: {student.hobby}
    - Engagement Tier: {engagement_metrics.get('activity_level', 'moderate') if 'engagement_metrics' in locals() else 'moderate'}
    - Struggling Subjects: {', '.join(weak_subjects) if weak_subjects else 'None'}
    
    {agent_insights}

    {performance_context}
    
    GUIDELINES (INTERNATIONAL STANDARD):
    1. **Well-being First**: If Burnout Risk is HIGH, schedule 'Light Review' or 'Creative Study' instead of intense work.
    2. **Strategic Focus**:
       - 'Struggling' subjects get 10-15 min daily micro-sessions (prevent overwhelming).
       - 'Mastery' subjects get "Challenge Problems" once a week.
    3. **Contextual Learning**: Use {student.hobby} as a theme for breaks or creative sessions.
    4. **Age-Appropriate**:
       - {student.age} yrs old = Max 30 min blocks.
       - Use "Study" for older kids, "Learning Time" for younger.
    5. **Nigerian Context**:
       - Include 'Revision' on Friday afternoons.
       - Respect common break times.
       
    SYLLABUS FOCUS:
    {curriculum_topics}
    
    UPCOMING TASKS:
    {json.dumps([{'title': a.get('title'), 'due_date': str(a.get('due_date')), 'subject': a.get('subject', 'General')} for a in assignments], indent=2)}

    OUTPUT FORMAT (JSON ONLY):
    {{
      "monday": [
        {{"time": "5:00 PM", "duration": 30, "subject": "Math", "topic": "...", "type": "study", "priority": "high"}},
        {{"time": "5:30 PM", "duration": 15, "subject": null, "topic": "Brain Break", "type": "break", "priority": null}}
      ],
      ... (tuesday to friday)
    }}
    
    Return ONLY valid JSON. No markdown formatting."""

    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000
        )
        
        schedule_text = response.choices[0].message.content.strip()
        
        # Extract JSON from response
        if "```json" in schedule_text:
            schedule_text = schedule_text.split("```json")[1].split("```")[0].strip()
        elif "```" in schedule_text:
            schedule_text = schedule_text.split("```")[1].split("```")[0].strip()
            
        schedule = json.loads(schedule_text)
        return schedule
        
    except Exception as e:
        print(f"Error generating AI schedule: {e}")
        return generate_mock_schedule()


def generate_mock_schedule() -> dict:
    """Generate a mock schedule for testing"""
    return {
        "monday": [
            {"time": "5:00 PM", "duration": 30, "subject": "Mathematics", "topic": "Algebra Review", "type": "study", "priority": "high"},
            {"time": "5:30 PM", "duration": 15, "subject": None, "topic": "Break", "type": "break", "priority": None},
            {"time": "5:45 PM", "duration": 30, "subject": "Science", "topic": "Biology Basics", "type": "study", "priority": "high"},
            {"time": "6:15 PM", "duration": 15, "subject": None, "topic": "Break", "type": "break", "priority": None},
            {"time": "6:30 PM", "duration": 30, "subject": "English", "topic": "Reading Practice", "type": "study", "priority": "medium"}
        ],
        "tuesday": [
            {"time": "5:00 PM", "duration": 30, "subject": "History", "topic": "World History", "type": "study", "priority": "medium"},
            {"time": "5:30 PM", "duration": 15, "subject": None, "topic": "Break", "type": "break", "priority": None},
            {"time": "5:45 PM", "duration": 30, "subject": "Mathematics", "topic": "Geometry", "type": "study", "priority": "high"},
            {"time": "6:15 PM", "duration": 15, "subject": None, "topic": "Break", "type": "break", "priority": None},
            {"time": "6:30 PM", "duration": 30, "subject": "Science", "topic": "Chemistry", "type": "study", "priority": "high"}
        ],
        "wednesday": [
            {"time": "5:00 PM", "duration": 30, "subject": "English", "topic": "Grammar", "type": "study", "priority": "medium"},
            {"time": "5:30 PM", "duration": 15, "subject": None, "topic": "Break", "type": "break", "priority": None},
            {"time": "5:45 PM", "duration": 30, "subject": "Geography", "topic": "Physical Geography", "type": "study", "priority": "low"},
            {"time": "6:15 PM", "duration": 15, "subject": None, "topic": "Break", "type": "break", "priority": None},
            {"time": "6:30 PM", "duration": 30, "subject": "Mathematics", "topic": "Assignment Prep", "type": "assignment", "priority": "high"}
        ],
        "thursday": [
            {"time": "5:00 PM", "duration": 30, "subject": "Science", "topic": "Physics", "type": "study", "priority": "high"},
            {"time": "5:30 PM", "duration": 15, "subject": None, "topic": "Break", "type": "break", "priority": None},
            {"time": "5:45 PM", "duration": 30, "subject": "History", "topic": "Local History", "type": "study", "priority": "medium"},
            {"time": "6:15 PM", "duration": 15, "subject": None, "topic": "Break", "type": "break", "priority": None},
            {"time": "6:30 PM", "duration": 30, "subject": "English", "topic": "Writing Practice", "type": "study", "priority": "medium"}
        ],
        "friday": [
            {"time": "5:00 PM", "duration": 30, "subject": "Mathematics", "topic": "Week Review", "type": "review", "priority": "medium"},
            {"time": "5:30 PM", "duration": 15, "subject": None, "topic": "Break", "type": "break", "priority": None},
            {"time": "5:45 PM", "duration": 30, "subject": "Science", "topic": "Week Review", "type": "review", "priority": "medium"},
            {"time": "6:15 PM", "duration": 30, "subject": None, "topic": "Free Time / Hobbies", "type": "break", "priority": None}
        ]
    }


def create_and_save_schedule(session, student) -> dict:
    """
    Orchestrate data gathering, generation, and persistence of AI schedule.
    Can be used by API endpoints and Agents.
    """
    from .models import Task, TestResult, School, Timetable, ChatHistory
    from sqlmodel import select, func, delete
    from datetime import datetime, timezone, timedelta

    # 1. GATHER DATA
    # Get school syllabus
    school = session.get(School, student.school_id)
    syllabus_content = school.syllabus_text if school and school.syllabus_text else """
    Mathematics: Algebra, Geometry, Statistics
    Science: Biology, Chemistry, Physics
    English: Grammar, Literature, Writing
    History: World History, Local History
    Geography: Physical Geography, Human Geography
    """
    
    # Get upcoming assignments
    upcoming_assignments = session.exec(select(Task).where(
        (Task.student_id == student.id) &
        (Task.status != "completed") &
        (Task.due_date >= datetime.now(timezone.utc))
    ).order_by(Task.due_date)).all()
    
    assignments_data = [
        {
            "title": task.title,
            "due_date": task.due_date,
            "subject": "General" 
        }
        for task in upcoming_assignments
    ]
    
    # Identify performance levels based on test performance
    test_results = session.exec(select(TestResult).where(
        TestResult.student_id == student.id
    )).all()
    
    subject_performance = {}
    for result in test_results:
        subject = result.subject
        if subject not in subject_performance:
            subject_performance[subject] = {"correct": 0, "total": 0}
        subject_performance[subject]["total"] += 1
        if result.is_correct:
            subject_performance[subject]["correct"] += 1
    
    # Calculate performance levels
    performance_levels = {
        "struggling": [],    # < 40%
        "developing": [],    # 40-60%
        "proficient": [],    # 60-80%
        "mastery": []        # 80%+
    }
    
    for subject, perf in subject_performance.items():
        if perf["total"] > 0:
            success_rate = perf["correct"] / perf["total"]
            if success_rate < 0.4:
                performance_levels["struggling"].append(subject)
            elif success_rate < 0.6:
                performance_levels["developing"].append(subject)
            elif success_rate < 0.8:
                performance_levels["proficient"].append(subject)
            else:
                performance_levels["mastery"].append(subject)
    
    weak_subjects = performance_levels["struggling"] + performance_levels["developing"]
    
    # Calculate engagement metrics
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_sessions = session.exec(
        select(func.count(func.distinct(ChatHistory.session_id))).where(
            (ChatHistory.student_id == student.id) &
            (ChatHistory.timestamp >= seven_days_ago)
        )
    ).one()
    
    recent_active_days = session.exec(
        select(func.count(func.distinct(func.date(ChatHistory.timestamp)))).where(
            (ChatHistory.student_id == student.id) &
            (ChatHistory.timestamp >= seven_days_ago)
        )
    ).one()
    
    subject_engagement = {}
    subject_stats = session.exec(
        select(
            ChatHistory.subject,
            func.count(ChatHistory.id).label('message_count')
        ).where(
            (ChatHistory.student_id == student.id) &
            (ChatHistory.subject.isnot(None))
        ).group_by(ChatHistory.subject)
    ).all()
    
    for subject, count in subject_stats:
        subject_engagement[subject] = count
    
    engagement_metrics = {
        "recent_sessions": recent_sessions,
        "active_days_last_week": recent_active_days,
        "subject_engagement": subject_engagement,
        "activity_level": "high" if recent_active_days >= 5 else "moderate" if recent_active_days >= 3 else "low"
    }

    # 2. GENERATE SCHEDULE
    schedule = generate_ai_schedule(
        student=student,
        syllabus_content=syllabus_content,
        assignments=assignments_data,
        weak_subjects=weak_subjects,
        performance_levels=performance_levels,
        session=session
    )

    # 3. PERSIST TO DATABASE
    try:
        # Clear existing
        session.exec(delete(Timetable).where(Timetable.student_id == student.id))
        
        # Add new
        for day, sessions in schedule.items():
            for sess in sessions:
                new_entry = Timetable(
                    student_id=student.id,
                    day_of_week=day,
                    start_time=sess.get("time"),
                    end_time=str(sess.get("duration")) + " min",
                    subject=sess.get("subject") or "Break",
                    focus_topic=sess.get("topic"),
                    activity_type=sess.get("type", "study"),
                    description=f"Priority: {sess.get('priority')}"
                )
                session.add(new_entry)
        
        session.commit()
    except Exception as e:
        print(f"Error persisting schedule in service: {e}")
        # Continue to return the schedule even if persistence fails slightly (though commit failure is critical)

    return {
        "schedule": schedule,
        "performance_levels": performance_levels,
        "engagement_metrics": engagement_metrics,
        "weak_subjects": weak_subjects,
        "upcoming_assignments_count": len(assignments_data)
    }
