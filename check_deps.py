#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIST Analiz Sistemi — Bagimlilik Dogrulama
Tum gerekli paketlerin kurulu olup olmadigini kontrol eder.
"""

import sys
import subprocess
import importlib
import os

REQUIRED_PACKAGES = [
    # Core
    ("isyatirimhisse", "isyatirimhisse"),
    ("borsapy", "borsapy"),
    ("pykap", "pykap"),
    ("pdfplumber", "pdfplumber"),
    ("talib", "TA-Lib"),
    ("evds", "evds"),
    # Stdlib (her zaman var)
    ("json", None),
    ("csv", None),
    ("re", None),
    ("os", None),
    ("sys", None),
    ("datetime", None),
    ("pathlib", None),
    ("argparse", None),
    ("glob", None),
    ("math", None),
    ("io", None),
]

OPTIONAL_PACKAGES = [
    ("fitz", "PyMuPDF"),  # pdfplumber fallback
    ("pandas", "pandas"),  # opsiyonel, bazi scriptler icin
]

def check_package(import_name, pip_name=None):
    """Paket kurulu mu kontrol et."""
    try:
        importlib.import_module(import_name)
        return True, "[OK] " + import_name
    except ImportError:
        name = pip_name or import_name
        return False, "[MISSING] " + import_name + " (kur: pip install " + name + ")"

def check_talib():
    """TA-Lib ozel kontrol (C kutuphanesi gerektirir)."""
    try:
        import talib
        return True, "[OK] talib (TA-Lib " + talib.__version__ + ")"
    except ImportError:
        return False, "[MISSING] talib (kur: pip install TA-Lib — Windows'ta bazen wheel sorunu yasani)"
    except Exception as e:
        return False, "[WARN] talib import hatasi: " + str(e)

def check_cli_tools():
    """CLI araclari kontrol et."""
    tools = [
        ("curl", "curl --version"),
        ("python", "python --version"),
        ("opencode", "opencode --version"),
        ("git", "git --version"),
    ]
    results = []
    for name, cmd in tools:
        try:
            result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0]
                results.append("[OK] " + name + ": " + version)
            else:
                results.append("[MISSING] " + name + ": bulunamadi")
        except Exception:
            results.append("[MISSING] " + name + ": bulunamadi")
    return results

def main():
    print("=" * 60)
    print("BIST ANALIZ SISTEMI — BAGIMLILIK KONTROLU")
    print("=" * 60)

    all_ok = True

    # Python paketleri
    print("\nPYTHON PAKETLERI:")
    for import_name, pip_name in REQUIRED_PACKAGES:
        if import_name == "talib":
            ok, msg = check_talib()
        else:
            ok, msg = check_package(import_name, pip_name)
        print("  " + msg)
        if not ok:
            all_ok = False

    # Opsiyonel paketler
    print("\nOPSIYONEL PAKETLER:")
    for import_name, pip_name in OPTIONAL_PACKAGES:
        ok, msg = check_package(import_name, pip_name)
        print("  " + msg)

    # CLI araclari
    print("\nCLI ARAÇLARI:")
    for msg in check_cli_tools():
        print("  " + msg)

    # Dosya yapisi
    print("\nDOSYA YAPISI:")
    required_files = [
        ".opencode/agents/haber-ajani.md",
        ".opencode/agents/hikaye-ajani.md",
        ".opencode/agents/bilanco-ajani.md",
        ".opencode/agents/teknik-ajani.md",
        ".opencode/agents/rakip-ajani.md",
        ".opencode/agents/ayi-ajani.md",
        ".opencode/commands/analiz.md",
        ".opencode/commands/haber.md",
        "KURALLAR.md",
        "analiz-arşivi/TEMPLATE.md",
        "run_analiz.py",
        "analiz-calisma/finansal_derinlik_final.py",
        "analiz-calisma/degerleme.py",
        "analiz-calisma/kap_pdf_parser.py",
    ]
    for f in required_files:
        exists = os.path.exists(f)
        print("  [" + ("OK" if exists else "MISSING") + "] " + f)
        if not exists:
            all_ok = False

    # Veri klasorleri
    print("\nVERI KLASORLERI:")
    for d in ["veri", "raporlar", "analiz-arşivi"]:
        exists = os.path.exists(d) and os.path.isdir(d)
        print("  [" + ("OK" if exists else "WILL_CREATE") + "] " + d + "/")

    print("\n" + "=" * 60)
    if all_ok:
        print("TUM BAGIMLILIKLAR HAZIR — ANALIZ BASLATILABILIR")
        print("   Komut: python run_analiz.py ASELS.IS")
    else:
        print("EKSIKLER VAR — Yukaridaki hatalari cozun")
    print("=" * 60)

    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())