
import os

file_path = r"c:\Users\PC\Desktop\Hackaton Success\EduLife -Working 1 - Copy\backend\specialized_agents.py"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# We expect the error around line 400 (0-indexed 399)
# 400: Generate a warm, helpful response now:
# 401: """
# 402: - Casual chat ...

# Let's match by content logic to be safe, searching around index 390-410
start_idx = 390
end_idx = 415

target_line_1 = "Generate a warm, helpful response now:"
target_line_2 = '"""'

found_idx = -1

for i in range(start_idx, end_idx):
    line = lines[i].strip()
    if line == target_line_1:
         # Check next line
         if lines[i+1].strip() == target_line_2:
             print(f"Found target at line {i+1}: {lines[i]}")
             found_idx = i
             break

if found_idx != -1:
    # Remove found_idx and found_idx+1
    print(f"Removing line {found_idx+1}: {lines[found_idx]}")
    print(f"Removing line {found_idx+2}: {lines[found_idx+1]}")
    
    # Slice: Keep everything before, skip 2, keep everything after
    new_lines = lines[:found_idx] + lines[found_idx+2:]
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print("Successfully patched file.")
else:
    print("Could not find the specific lines to remove. Aborting to avoid damage.")
    # Debug output
    print("Dumping lines 395-405 for inspection:")
    for j in range(395, 405):
        if j < len(lines):
            print(f"{j+1}: {lines[j]}")
