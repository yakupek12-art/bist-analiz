import os

# Find the actual path
base_path = r"C:\Users\PC\OneDrive\Belgeler\Varsayılan Proje"
file_path = os.path.join(base_path, "parallel_agents.py")

print(f"Using path: {file_path}")
print(f"Exists: {os.path.exists(file_path)}")

with open(file_path, 'rb') as f:
    content = f.read()

# Find the function
idx = content.find(b'def _build_delta')
if idx >= 0:
    end_idx = content.find(b'def _extract_kap_notes')
    if end_idx == -1:
        end_idx = idx + 600
    print(f"Found at index {idx}")
    print(f"End index: {end_idx}")
    print(f"Content length: {len(content)}")
    print(repr(content[idx:idx+500]))
else:
    print("Function not found!")