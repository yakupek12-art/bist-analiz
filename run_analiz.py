#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIST Paralel Çoklu-Ajan Finansal Analiz Sistemi
Ana giriş noktası - Paralel Agent + Template Rapor
"""

import asyncio
import sys
import os
import argparse

# Proje yolu
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parallel_agents import main

if __name__ == "__main__":
    asyncio.run(main())