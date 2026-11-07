import subprocess
result = subprocess.run([r"C:\Users\PC\AppData\Local\Programs\opencode\bin\opencode.exe", "agent", "list"], capture_output=True, text=True, timeout=30)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)