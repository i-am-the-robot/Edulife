
import ast
import traceback

file_path = r"c:\Users\PC\Desktop\Hackaton Success\EduLife -Working 1 - Copy\backend\agent_coordinator.py"

try:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    ast.parse(content)
    print("Syntax is valid.")
except SyntaxError as e:
    print(f"Syntax Error: {e}")
    print(f"Line: {e.lineno}")
    print(f"Text: {e.text}")
except Exception as e:
    traceback.print_exc()
