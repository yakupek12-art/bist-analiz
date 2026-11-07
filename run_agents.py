import subprocess
import os

# Use the actual working directory
cwd = os.getcwd()
print("CWD:", cwd)

agents = [
    ("haber-ajani", "veri/haberler.txt veri/kap_bildirim.txt", "Haber & Gundem"),
    ("bilanco-ajani", "veri/bilanco.csv veri/kap_bildirim.txt veri/finansal_derinlik.json", "Bilanco & Finansal Guc"),
    ("hikaye-ajani", "veri/haberler.txt veri/bilanco.csv veri/kap_bildirim.txt", "Hikaye & Hendek"),
    ("rakip-ajani", "veri/rakip_veri.txt veri/bilanco.csv", "Rakip & Sektor"),
    ("teknik-ajani", "veri/teknik.json veri/fiyat.json", "Teknik Analiz"),
    ("ayi-ajani", "veri/bilanco.csv veri/haberler.txt veri/kap_bildirim.txt", "Ayi / Risk"),
]

for agent_name, files, desc in agents:
    print("\n" + "=" * 50)
    print("Running: " + desc + " (" + agent_name + ")")
    print("=" * 50)
    
    flat_cmd = ["opencode", "run", "--agent", agent_name]
    for f in files.split():
        flat_cmd.extend(["-f", f])
    flat_cmd.append("Analiz et ve rapor yaz")
    
    print("Command: " + " ".join(flat_cmd))
    result = subprocess.run(flat_cmd, capture_output=True, text=True, timeout=300)
    print("STDOUT:", result.stdout[-2000:])
    print("STDERR:", result.stderr[-1000:])
    print("Return code:", result.returncode)
    
    # Save output
    with open("raporlar/" + agent_name + "-raporu.md", "w", encoding="utf-8") as f:
        f.write(result.stdout)
        if result.stderr:
            f.write("\n\nSTDERR:\n" + result.stderr)

print("\nAll agents completed!")