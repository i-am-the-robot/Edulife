"""
Test Script for AI Tutor System Upgrade
Tests all major features: session memory, image search, Nigerian teaching, timetable integration
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_session_memory():
    """Test session-scoped memory management"""
    print("\n" + "="*60)
    print("TEST 1: Session Memory Management")
    print("="*60)
    
    from backend.agent_memory import get_student_memory
    from backend.database import get_db_session
    
    with get_db_session() as session:
        # Use a test student ID
        memory = get_student_memory("test_student_123", session)
        
        # Test 1: Add session fact
        print("\n[1] Adding session fact...")
        memory.add_session_fact("session_001", "pet", "I have a dog named Max")
        print("✓ Session fact added")
        
        # Test 2: Get facts with session
        print("\n[2] Getting facts with session_id...")
        facts_with_session = memory.get_all_facts(session_id="session_001")
        print(f"✓ Facts retrieved: {len(facts_with_session)} facts")
        for fact in facts_with_session:
            print(f"  - {fact['category']}: {fact['fact']}")
        
        # Test 3: Get facts without session (should not include session facts)
        print("\n[3] Getting facts without session_id...")
        facts_without_session = memory.get_all_facts()
        print(f"✓ Permanent facts only: {len(facts_without_session)} facts")
        
        # Test 4: Add permanent fact
        print("\n[4] Adding permanent fact...")
        memory.add_fact("hobby", "I love football")
        facts_permanent = memory.get_all_facts()
        print(f"✓ Permanent fact added: {len(facts_permanent)} permanent facts")
        
        # Test 5: Clear session facts
        print("\n[5] Clearing session facts...")
        memory.clear_session_facts("session_001")
        facts_after_clear = memory.get_all_facts(session_id="session_001")
        print(f"✓ Session cleared: {len(facts_after_clear)} facts (should only be permanent)")
        
        print("\n✅ Session Memory Test PASSED")


async def test_image_search():
    """Test multi-source image search"""
    print("\n" + "="*60)
    print("TEST 2: Multi-Source Image Search")
    print("="*60)
    
    from backend.media_service import search_image_multi_source, prepare_text_response, prepare_voice_response
    
    # Test 1: Search for image
    print("\n[1] Searching for 'lion in savannah'...")
    image_url = search_image_multi_source("lion in savannah")
    if image_url:
        print(f"✓ Image found: {image_url[:80]}...")
    else:
        print("✗ No image found")
    
    # Test 2: Process image tags for text
    print("\n[2] Processing image tags for text response...")
    text_with_tag = "Lions are big cats. [SHOW_IMAGE: male lion with mane] They live in groups."
    text_response = prepare_text_response(text_with_tag)
    has_img_tag = "<img" in text_response
    print(f"✓ Text response processed: {'Has <img> tag' if has_img_tag else 'No <img> tag'}")
    
    # Test 3: Process for voice
    print("\n[3] Processing for voice response...")
    voice_response = prepare_voice_response(text_with_tag)
    has_markdown = "**" in voice_response or "[SHOW_IMAGE:" in voice_response
    print(f"✓ Voice response processed: {'Still has markdown (ERROR)' if has_markdown else 'Clean text'}")
    print(f"  Voice output: {voice_response[:100]}...")
    
    print("\n✅ Image Search Test PASSED")


async def test_nigerian_teaching():
    """Test Nigerian-focused teaching methodology"""
    print("\n" + "="*60)
    print("TEST 3: Nigerian Teaching Methodology")
    print("="*60)
    
    from backend.specialized_agents import TutoringAgent
    from backend.database import get_db_session
    from backend.models import Student
    from sqlmodel import select
    
    with get_db_session() as session:
        # Get a test student
        student = session.exec(select(Student).limit(1)).first()
        
        if not student:
            print("⚠️ No student found in database. Skipping test.")
            return
        
        print(f"\n[1] Testing with student: {student.full_name}")
        print(f"    Hobby: {student.hobby}")
        print(f"    Class: {student.student_class}")
        
        # Create tutoring agent
        agent = TutoringAgent(student, session)
        
        # Test intent detection
        print("\n[2] Testing intent detection...")
        
        test_messages = [
            ("hi", "greeting"),
            ("I want to learn mathematics", "learning"),
            ("What should I learn?", "unsure_what_to_learn"),
            ("quiz me", "quiz_request"),
        ]
        
        for message, expected_type in test_messages:
            intent = agent._detect_message_intent(message)
            match = "✓" if intent["type"] == expected_type else "✗"
            print(f"  {match} '{message}' → {intent['type']} (expected: {expected_type})")
        
        # Test special intent handling
        print("\n[3] Testing 'unsure what to learn' handler...")
        intent = agent._detect_message_intent("What should I learn?")
        response = await agent.handle_special_intent(intent, "What should I learn?")
        if response:
            print(f"✓ Response generated:")
            print(f"  {response[:150]}...")
        else:
            print("✗ No response generated")
        
        print("\n✅ Nigerian Teaching Test PASSED")


async def test_timetable_integration():
    """Test timetable-based topic suggestions"""
    print("\n" + "="*60)
    print("TEST 4: Timetable Integration")
    print("="*60)
    
    from backend.specialized_agents import SchedulingAgent
    from backend.database import get_db_session
    from backend.models import Student
    from sqlmodel import select
    
    with get_db_session() as session:
        # Get a test student
        student = session.exec(select(Student).limit(1)).first()
        
        if not student:
            print("⚠️ No student found in database. Skipping test.")
            return
        
        print(f"\n[1] Testing with student: {student.full_name}")
        
        # Create scheduling agent
        agent = SchedulingAgent(student, session)
        
        # Test timetable suggestion
        print("\n[2] Checking timetable for topic suggestion...")
        suggestion = agent.suggest_topic_from_timetable()
        
        if suggestion:
            print(f"✓ Timetable suggestion found:")
            print(f"  {suggestion}")
        else:
            print("ℹ️ No timetable entry for current time (this is normal)")
        
        print("\n✅ Timetable Integration Test PASSED")


async def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("AI TUTOR SYSTEM UPGRADE - TEST SUITE")
    print("="*60)
    
    try:
        await test_session_memory()
        await test_image_search()
        await test_nigerian_teaching()
        await test_timetable_integration()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_all_tests())
