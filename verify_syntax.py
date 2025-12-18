
import os
import ast

def check_syntax(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            source = f.read()
        ast.parse(source)
        print(f"OK: {filename}")
        return True
    except SyntaxError as e:
        print(f"ERROR: {filename} - {e}")
        return False
    except Exception as e:
        print(f"ERROR: {filename} - {e}")
        return False

files_to_check = [
    "backend/main.py",
    "backend/chat_router.py",
    "backend/specialized_agents.py",
    "backend/agent_coordinator.py",
    "backend/agent_memory.py",
    "backend/ai_service.py"
]

all_passed = True
print("Starting Syntax Check...")
for f in files_to_check:
    if os.path.exists(f):
        if not check_syntax(f):
            all_passed = False
    else:
        print(f"MISSING: {f}")

if all_passed:
    print("SUCCESS: All files passed syntax check.")
else:
    print("FAILURE: Syntax errors found.")
