import sys
import os
import asyncio
from sqlmodel import Session, select, create_engine

# Path setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# Windows Unicode Fix
sys.stdout.reconfigure(encoding='utf-8')

from backend.models import Student
from backend.agent_coordinator import AgentCoordinator
from backend.specialized_agents import MotivationAgent

# Connect to DB
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "database.db")
engine = create_engine(f"sqlite:///{db_path}")

async def test_async_agents():
    print("Testing Async Agents...")
    
    with Session(engine) as session:
        student = session.exec(select(Student)).first()
        if not student:
            print("No student found. Skipping.")
            return

        print(f"Student: {student.full_name}")
        
        # 1. Test Coordinator Instantiation
        coordinator = AgentCoordinator(student, session)
        print("Coordinator initialized.")
        
        # 2. Test Motivation Agent Async Method
        print("Testing MotivationAgent.analyze_sentiment (Async)...")
        # Ensure we are using AsyncGroq (though we can't fully mock API without key, it should at least run logic)
        sentiment = await coordinator.motivation_agent.analyze_sentiment("I am so frustrated with math!")
        print(f"Sentiment Result: {sentiment}")
        
        # 3. Test Full Coordination (Mocking or reducing scope)
        # We won't run full coordination as it triggers many calls, but we can try a simple check
        # print("Testing Full Coordination...")
        # res = await coordinator.handle_student_question("Help with photosnthesis", "Science")
        # print("Coordination Result:", res.keys())

    print("Async Test Complete.")

if __name__ == "__main__":
    asyncio.run(test_async_agents())
