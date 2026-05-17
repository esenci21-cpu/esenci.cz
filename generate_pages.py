#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generator for essential oil HTML pages.
Reads PDF content, parses sections, and generates HTML files.
"""

import json
import os
import pdfplumber
import re

OUT_DIR = r"C:\Claude\projekty\www\esenci.cz"
SINGLE_PDF = r"C:\Users\x2\Desktop\xx\0_Jednodruhové EO_interaktivní.pdf"
BLENDS_PDF = r"C:\Users\x2\Desktop\xx\0_Směsi EO_interaktivni.pdf"

# Load data
with open(os.path.join(OUT_DIR, "bewit-urls.json"), encoding="utf-8") as f:
    bewit_urls = json.load(f)

with open(os.path.join(OUT_DIR, "oleje-data.json"), encoding="utf-8") as f:
    oleje_data = json.load(f)

# Build lookup maps
# bewit by name
bewit_by_name = {}
for item in bewit_urls:
    bewit_by_name[item["text"].strip()] = item

# oleje by name
oleje_by_name = {}
for item in oleje_data:
    oleje_by_name[item["name"].strip()] = item

# Garbled Czech chars fix map
# The PDF uses Windows-1250 but is being read as Latin-1 or something similar
# Build a fix map based on common patterns
FIX_MAP = {
    # These replacements fix common garbled Czech text from the PDF
    'á': 'á', 'č': 'č', 'ď': 'ď', 'é': 'é', 'ě': 'ě',
    'í': 'í', 'ň': 'ň', 'ó': 'ó', 'ř': 'ř', 'š': 'š',
    'ť': 'ť', 'ú': 'ú', 'ů': 'ů', 'ý': 'ý', 'ž': 'ž',
    'Á': 'Á', 'Č': 'Č', 'Ď': 'Ď', 'É': 'É', 'Ě': 'Ě',
    'Í': 'Í', 'Ň': 'Ň', 'Ó': 'Ó', 'Ř': 'Ř', 'Š': 'Š',
    'Ť': 'Ť', 'Ú': 'Ú', 'Ů': 'Ů', 'Ý': 'Ý', 'Ž': 'Ž',
}

def fix_czech(text):
    """The PDF text is already correct Unicode from pdfplumber — just return it."""
    if text is None:
        return ""
    return text

def extract_page_text(pdf_path, page_index):
    """Extract text from a specific page (0-indexed)."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if page_index >= len(pdf.pages):
                return None
            page = pdf.pages[page_index]
            text = page.extract_text()
            if text:
                return fix_czech(text)
            return None
    except Exception as e:
        print(f"  Error extracting page {page_index}: {e}")
        return None

def parse_single_oil(text, fallback_popis=""):
    """Parse sections from a single oil PDF page."""
    if not text:
        return {}

    lines = text.split('\n')

    result = {
        'hlavni_ucinky': [],
        'emocni': '',
        'psychicke': '',
        'pouziti': [],
        'kombinace': '',
        'historie': '',
    }

    # Find sections by keywords
    current_section = None
    section_lines = {
        'emocni': [],
        'psychicke': [],
        'hlavni': [],
        'pouziti': [],
        'kombinace': [],
        'historie': [],
    }

    for line in lines:
        line = line.strip()
        if not line:
            continue

        lo = line.lower()

        # Detect section headers
        if 'emoční' in lo and 'působen' in lo:
            current_section = 'emocni'
            continue
        elif 'psychick' in lo and ('působen' in lo or 'energetick' in lo):
            current_section = 'psychicke'
            continue
        elif 'hlavní účinky' in lo or 'hlavni ucinky' in lo:
            current_section = 'hlavni'
            continue
        elif 'použití v praxi' in lo or 'pouziti v praxi' in lo or 'použití' in lo:
            current_section = 'pouziti'
            continue
        elif 'kombinace' in lo or 'vhodné kombinace' in lo or 'vhodna kombinace' in lo:
            current_section = 'kombinace'
            continue
        elif 'historie' in lo or 'zajímavosti' in lo or 'zajimavosti' in lo:
            current_section = 'historie'
            continue

        if current_section and current_section in section_lines:
            # Skip lines that look like page numbers or oil names
            if re.match(r'^\d+$', line):
                continue
            section_lines[current_section].append(line)

    # Process sections
    if section_lines['emocni']:
        result['emocni'] = ' '.join(section_lines['emocni'])

    if section_lines['psychicke']:
        result['psychicke'] = ' '.join(section_lines['psychicke'])

    if section_lines['hlavni']:
        result['hlavni_ucinky'] = [l.lstrip('-•·◦▪▸▹►→').strip()
                                    for l in section_lines['hlavni']
                                    if l.strip().startswith('-') or len(l.strip()) > 3]

    if section_lines['pouziti']:
        result['pouziti'] = [l.lstrip('-•·◦▪▸▹►→').strip()
                              for l in section_lines['pouziti']
                              if l.strip().startswith('-') or len(l.strip()) > 3]

    if section_lines['kombinace']:
        # Usually just a list of oil names on one or two lines
        result['kombinace'] = ', '.join([l.strip() for l in section_lines['kombinace'] if l.strip()])

    if section_lines['historie']:
        result['historie'] = ' '.join(section_lines['historie'])

    # Use fallback popis if sections are empty
    if not result['emocni'] and not result['psychicke']:
        result['emocni'] = fallback_popis

    return result


def parse_blend(text, fallback_popis=""):
    """Parse sections from a blend PDF page."""
    if not text:
        return {}

    lines = text.split('\n')

    result = {
        'popis_kratky': '',
        'emoce': '',
        'pocitove': '',
        'pouziti': [],
        'kombinace': '',
    }

    current_section = None
    section_lines = {
        'popis': [],
        'emoce': [],
        'pocitove': [],
        'pouziti': [],
        'kombinace': [],
    }

    # First pass: get the short description (usually after name lines, before sections)
    in_intro = True
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        lo = line_stripped.lower()

        # Detect section headers - must be the whole line or start of line followed by ':'
        if lo.startswith('emoce:') or lo.rstrip(':') == 'emoce':
            current_section = 'emoce'
            in_intro = False
            # Check if there's content on the same line after 'Emoce:'
            after = re.sub(r'^[Ee]moce[:\s]*', '', line_stripped).strip()
            if after:
                section_lines['emoce'].append(after)
            continue
        elif lo.startswith('pocitov') and (lo.startswith('pocitov') and len(lo) < 30 or ':' in lo):
            current_section = 'pocitove'
            in_intro = False
            after = re.sub(r'^[Pp]ocitov[ěe]?[:\s]*', '', line_stripped).strip()
            if after:
                section_lines['pocitove'].append(after)
            continue
        elif (lo.startswith('použití') or lo.startswith('pouziti')) and len(lo) < 40:
            current_section = 'pouziti'
            in_intro = False
            continue
        elif (lo.startswith('kombinace') or lo.startswith('doporučen')) and len(lo) < 40:
            current_section = 'kombinace'
            in_intro = False
            continue

        # Skip page number lines and name repetitions at top
        if re.match(r'^\d+$', line_stripped):
            continue

        if current_section is None:
            # This is still the intro/description area
            # Skip the first 3 lines (page num, name, sometimes repeated name)
            if in_intro and len(section_lines['popis']) < 20:
                section_lines['popis'].append(line_stripped)
        elif current_section in section_lines:
            section_lines[current_section].append(line_stripped)

    # The popis lines include name + description - skip name lines (first 1-3 lines)
    popis_lines = section_lines['popis']
    # Remove numeric lines and likely name lines (short uppercase lines)
    clean_popis = []
    for l in popis_lines:
        if re.match(r'^\d+$', l):
            continue
        if l.isupper() and len(l) < 30:  # likely a name/code
            continue
        clean_popis.append(l)

    if clean_popis:
        result['popis_kratky'] = ' '.join(clean_popis)

    if section_lines['emoce']:
        result['emoce'] = ' '.join(section_lines['emoce'])

    if section_lines['pocitove']:
        result['pocitove'] = ' '.join(section_lines['pocitove'])

    if section_lines['pouziti']:
        result['pouziti'] = [l.lstrip('-•·◦▪▸▹►→').strip()
                              for l in section_lines['pouziti']
                              if l.strip()]

    if section_lines['kombinace']:
        result['kombinace'] = ', '.join([l.strip() for l in section_lines['kombinace'] if l.strip()])

    # Fallback
    if not result['popis_kratky']:
        result['popis_kratky'] = fallback_popis
    if not result['emoce']:
        result['emoce'] = fallback_popis

    return result


def rewrite_ucinky(items):
    """Rewrite technical bullet points into natural Czech."""
    result = []
    for item in items:
        if not item.strip():
            continue
        # Already natural enough - just capitalize and clean
        item = item.strip()
        if item:
            # Capitalize first letter
            item = item[0].upper() + item[1:] if len(item) > 1 else item.upper()
            result.append(item)
    return result[:6]  # max 6 items


def shorten_text(text, max_sentences=3):
    """Take at most max_sentences sentences from text."""
    if not text:
        return ""
    # Split by sentence-ending punctuation
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return ' '.join(sentences[:max_sentences])


def generate_html_single(name, latin, slug, url, typ, popis, parsed, fullname=None):
    """Generate HTML for a single oil."""

    display_name = fullname or name

    # Hero keywords from popis
    hero_desc = popis if popis else f"Přírodní esenciální olej BEWIT"

    # "Pro koho je" section - from emotional/psychic content
    pro_koho_text = parsed.get('emocni', '') or parsed.get('psychicke', '') or popis
    pro_koho_text = shorten_text(pro_koho_text, 3)
    if not pro_koho_text:
        pro_koho_text = f"Tento olej ocení každý, kdo hledá přírodní podporu a harmonii."

    # Main effects
    ucinky = rewrite_ucinky(parsed.get('hlavni_ucinky', []))
    if not ucinky:
        # Generate from popis keywords
        keywords = [k.strip() for k in popis.split(',') if k.strip()]
        ucinky = [k[0].upper() + k[1:] for k in keywords[:5] if k]

    ucinky_html = '\n'.join([
        f'        <li style="display:flex; gap:0.75rem;"><span style="color:var(--orange);">✦</span><span>{u}</span></li>'
        for u in ucinky
    ])

    # How to use
    pouziti = parsed.get('pouziti', [])
    if not pouziti:
        pouziti = [
            f"Přidejte 3–5 kapek do difuzéru a nechte vůni naplnit prostor",
            f"Smíchejte 5 kapek s 30 ml nosného oleje a naneste masáží na pokožku",
            f"Přidejte 3–4 kapky do koupele spolu s lžící smetany nebo mýdla",
        ]
    else:
        pouziti = pouziti[:4]

    pouziti_html = '\n'.join([
        f'        <li style="display:flex; gap:0.75rem;"><span style="color:var(--orange);">💧</span><span>{p}</span></li>'
        for p in pouziti
    ])

    # Combinations
    kombinace = parsed.get('kombinace', '')
    if not kombinace:
        kombinace = "Levandule · Bergamot · Kadidlo · Pomeranč"
    else:
        kombinace = ' · '.join([k.strip() for k in kombinace.split(',') if k.strip()])

    # History/Did you know
    historie = parsed.get('historie', '')
    if not historie:
        historie = f"{display_name} je ceněný přírodní olej s dlouhou tradicí v aromaterapii a přírodní medicíně."
    else:
        historie = shorten_text(historie, 2)

    # Latin subtitle
    latin_html = f'      <p class="hero-subtitle" style="font-style:italic; color:var(--text-light);">{latin}</p>' if latin else ''

    html = f'''<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{display_name} — esenciální olej | Esenci.cz</title>
  <meta name="description" content="{display_name} — {hero_desc}. Přírodní esenciální olej BEWIT.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Playfair+Display:ital,wght@0,700;1,400;1,700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="./style.css">
  <script defer src="https://cloud.umami.is/script.js" data-website-id="d27b85f2-d2a8-42a9-81e3-b542b755bde2"></script>
</head>
<body>

<!-- ── Navbar ── -->
<nav class="navbar">
  <div class="nav-inner">
    <a href="./index.html" class="logo">
      <span class="logo-main">Esence</span>
      <span class="logo-sub">z přírody</span>
    </a>
    <div class="nav-right">
      <ul class="nav-links" id="navLinks">
        <li><a href="./index.html">Úvod</a></li>
        <li><a href="./temata.html">Témata</a></li>
        <li><a href="./jak-pouzivat.html">Jak používat</a></li>
        <li><a href="./katalog.html">Oleje A-Z</a></li>
        <li><a href="./pruvodce.html">Průvodkyně</a></li>
        <li><a href="./blog.html">Blog</a></li>
      </ul>
      <a href="https://mybewit.com/r/3fqlzp0xrllj7" target="_blank" rel="noopener" title="Registrace zdarma — slevy až 50 % na vybrané produkty" style="margin-left:1rem; background:var(--orange); color:#fff; padding:0.3rem 0.75rem; border-radius:20px; font-size:0.78rem; text-decoration:none; white-space:nowrap; font-weight:500;">Výhody BEWIT →</a>
      <a href="./katalog.html" class="btn-back" style="margin-left:1rem;">← Oleje A–Z</a>
      <button class="nav-toggle" id="navToggle" aria-label="Menu">
        <span></span><span></span><span></span>
      </button>
    </div>
  </div>
</nav>

<!-- ── Hero ── -->
<section class="hero">
  <div class="hero-inner">
    <div class="hero-text">
      <p style="font-size:0.82rem; color:var(--orange); font-weight:500; margin:0 0 0.5rem;">🌿 Jednodruhový olej</p>
      <h1 class="hero-title">{display_name}</h1>
{latin_html}
      <p class="hero-desc" style="color:var(--dark);">
        {hero_desc}
      </p>
    </div>
    <div class="hero-image">
      <img src="./images/jak_pouzivat.png" alt="{display_name} esenciální olej" style="object-position: center center;">
    </div>
  </div>
</section>

<!-- ── Obsah ── -->
<section style="padding:3rem 0; background:#fff;">
  <div class="section-inner" style="max-width:760px;">

    <!-- Pro koho je -->
    <div style="background:#FFFBF0; border-radius:1rem; padding:1.5rem; margin-bottom:2rem;">
      <h2 style="font-family:var(--font-h); font-size:1.2rem; color:var(--dark); margin-bottom:0.75rem;">Pro koho je {display_name}?</h2>
      <p style="color:var(--dark); line-height:1.75; margin:0;">
        {pro_koho_text}
      </p>
    </div>

    <!-- Účinky -->
    <div style="margin-bottom:2rem;">
      <h2 style="font-family:var(--font-h); font-size:1.2rem; color:var(--dark); margin-bottom:1rem;">Na co pomáhá</h2>
      <ul style="list-style:none; padding:0; margin:0; display:flex; flex-direction:column; gap:0.6rem;">
{ucinky_html}
      </ul>
    </div>

    <!-- Jak použít -->
    <div style="margin-bottom:2rem;">
      <h2 style="font-family:var(--font-h); font-size:1.2rem; color:var(--dark); margin-bottom:1rem;">💧 Jak použít</h2>
      <ul style="list-style:none; padding:0; margin:0; display:flex; flex-direction:column; gap:0.6rem;">
{pouziti_html}
      </ul>
    </div>

    <!-- Kombinace -->
    <div style="background:#F3F6EE; border-radius:1rem; padding:1.25rem 1.5rem; margin-bottom:2rem;">
      <h2 style="font-family:var(--font-h); font-size:1.1rem; color:var(--dark); margin-bottom:0.5rem;">🌿 Skvěle se kombinuje s</h2>
      <p style="color:var(--text-light); margin:0;">{kombinace}</p>
    </div>

    <!-- Zajímavost -->
    <div style="margin-bottom:2.5rem;">
      <h2 style="font-family:var(--font-h); font-size:1.1rem; color:var(--dark); margin-bottom:0.5rem;">📖 Věděli jste?</h2>
      <p style="color:var(--text-light); line-height:1.75; margin:0;">
        {historie}
      </p>
    </div>

    <!-- BEWIT odkaz -->
    <div style="background:var(--cream-dk); border-radius:1rem; padding:2rem; text-align:center; border:1px solid var(--border);">
      <a href="{url}" target="_blank" rel="noopener" class="btn-orange" style="font-size:1rem; padding:0.75rem 2rem;">
        Chcete {display_name} vyzkoušet? →
      </a>
      <p style="font-size:0.8rem; color:var(--text-light); margin:0.75rem 0 0;">Jako registrovaný zákazník získáte slevu až 50 % na vybrané produkty.</p>
    </div>

  </div>
</section>

<!-- ── Disclaimer ── -->
<p style="text-align:center; font-size:0.8rem; color:#8a7a6a; padding:0.75rem 1rem; background:var(--cream);">
  Informace na této stránce mají výhradně informační charakter. Esenciální oleje nejsou náhradou lékařské péče.
</p>

<!-- ── Footer ── -->
<footer class="footer">
  <div class="footer-botanical">🌿 ✦ 🌸 ✦ 🌿</div>
  <p class="footer-quote">„Tady nejde o výkon ani dokonalost. Jen o návrat k sobě."</p>
  <p class="footer-heart">♥</p>
  <p class="footer-copy">© 2026 esenci.cz</p>
</footer>

<script>
  const toggle = document.getElementById('navToggle');
  const links  = document.getElementById('navLinks');
  toggle.addEventListener('click', () => links.classList.toggle('open'));
</script>
</body>
</html>'''
    return html


def generate_html_blend(name, slug, url, popis, fullname, parsed):
    """Generate HTML for a blend."""

    display_name = fullname or name
    hero_desc = parsed.get('popis_kratky', '') or popis
    hero_desc = shorten_text(hero_desc, 2)
    if not hero_desc:
        hero_desc = popis or f"Prémiová směs esenciálních olejů BEWIT"

    # Emotional section
    emocni = parsed.get('emoce', '') or parsed.get('pocitove', '') or popis
    emocni = shorten_text(emocni, 3)
    if not emocni:
        emocni = f"Tato směs podporuje emoční rovnováhu a vnitřní pohodu."

    # Effects - derive from popis keywords or blend description
    pouziti_raw = parsed.get('pouziti', [])
    pouziti = pouziti_raw[:4] if pouziti_raw else []

    if not pouziti:
        pouziti = [
            f"Přidejte 3–5 kapek do difuzéru a nechte vůni pracovat",
            f"Naneste zředěné s nosným olejem na potřebná místa nebo chodidla",
            f"Použijte v koupeli s lžící smetany nebo přírodního mýdla",
        ]

    pouziti_html = '\n'.join([
        f'        <li style="display:flex; gap:0.75rem;"><span style="color:var(--orange);">💧</span><span>{p}</span></li>'
        for p in pouziti
    ])

    # Main benefits - from popis
    popis_keywords = [k.strip() for k in popis.split(',') if k.strip()]
    if not popis_keywords:
        popis_keywords = ['Přírodní podpora', 'Emoční harmonie', 'Vnitřní rovnováha']
    ucinky_html = '\n'.join([
        f'        <li style="display:flex; gap:0.75rem;"><span style="color:var(--orange);">✦</span><span>{k[0].upper() + k[1:] if k else k}</span></li>'
        for k in popis_keywords[:5]
    ])

    kombinace = parsed.get('kombinace', '')
    if kombinace:
        kombinace = ' · '.join([k.strip() for k in kombinace.split(',') if k.strip()])
    else:
        kombinace = "Levandule · Kadidlo · Bergamot · Pomeranč"

    pocitove = parsed.get('pocitove', '')
    if not pocitove:
        pocitove = f"Směs {display_name} přináší pocit vnitřní rovnováhy a klidu."
    else:
        pocitove = shorten_text(pocitove, 2)

    html = f'''<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{display_name} — směs esenciálních olejů | Esenci.cz</title>
  <meta name="description" content="{display_name} — {shorten_text(popis, 1)}. Prémiová směs BEWIT.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Playfair+Display:ital,wght@0,700;1,400;1,700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="./style.css">
  <script defer src="https://cloud.umami.is/script.js" data-website-id="d27b85f2-d2a8-42a9-81e3-b542b755bde2"></script>
</head>
<body>

<!-- ── Navbar ── -->
<nav class="navbar">
  <div class="nav-inner">
    <a href="./index.html" class="logo">
      <span class="logo-main">Esence</span>
      <span class="logo-sub">z přírody</span>
    </a>
    <div class="nav-right">
      <ul class="nav-links" id="navLinks">
        <li><a href="./index.html">Úvod</a></li>
        <li><a href="./temata.html">Témata</a></li>
        <li><a href="./jak-pouzivat.html">Jak používat</a></li>
        <li><a href="./katalog.html">Oleje A-Z</a></li>
        <li><a href="./pruvodce.html">Průvodkyně</a></li>
        <li><a href="./blog.html">Blog</a></li>
      </ul>
      <a href="https://mybewit.com/r/3fqlzp0xrllj7" target="_blank" rel="noopener" title="Registrace zdarma — slevy až 50 % na vybrané produkty" style="margin-left:1rem; background:var(--orange); color:#fff; padding:0.3rem 0.75rem; border-radius:20px; font-size:0.78rem; text-decoration:none; white-space:nowrap; font-weight:500;">Výhody BEWIT →</a>
      <a href="./katalog.html" class="btn-back" style="margin-left:1rem;">← Oleje A–Z</a>
      <button class="nav-toggle" id="navToggle" aria-label="Menu">
        <span></span><span></span><span></span>
      </button>
    </div>
  </div>
</nav>

<!-- ── Hero ── -->
<section class="hero">
  <div class="hero-inner">
    <div class="hero-text">
      <p style="font-size:0.82rem; color:var(--orange); font-weight:500; margin:0 0 0.5rem;">🧴 Směs</p>
      <h1 class="hero-title">{display_name}</h1>
      <p class="hero-desc" style="color:var(--dark);">
        {hero_desc}
      </p>
    </div>
    <div class="hero-image">
      <img src="./images/jak_pouzivat.png" alt="{display_name} směs esenciálních olejů" style="object-position: center center;">
    </div>
  </div>
</section>

<!-- ── Obsah ── -->
<section style="padding:3rem 0; background:#fff;">
  <div class="section-inner" style="max-width:760px;">

    <!-- Pro koho je -->
    <div style="background:#FFFBF0; border-radius:1rem; padding:1.5rem; margin-bottom:2rem;">
      <h2 style="font-family:var(--font-h); font-size:1.2rem; color:var(--dark); margin-bottom:0.75rem;">Pro koho je {display_name}?</h2>
      <p style="color:var(--dark); line-height:1.75; margin:0;">
        {emocni}
      </p>
    </div>

    <!-- Účinky -->
    <div style="margin-bottom:2rem;">
      <h2 style="font-family:var(--font-h); font-size:1.2rem; color:var(--dark); margin-bottom:1rem;">Na co pomáhá</h2>
      <ul style="list-style:none; padding:0; margin:0; display:flex; flex-direction:column; gap:0.6rem;">
{ucinky_html}
      </ul>
    </div>

    <!-- Jak použít -->
    <div style="margin-bottom:2rem;">
      <h2 style="font-family:var(--font-h); font-size:1.2rem; color:var(--dark); margin-bottom:1rem;">💧 Jak použít</h2>
      <ul style="list-style:none; padding:0; margin:0; display:flex; flex-direction:column; gap:0.6rem;">
{pouziti_html}
      </ul>
    </div>

    <!-- Kombinace -->
    <div style="background:#F3F6EE; border-radius:1rem; padding:1.25rem 1.5rem; margin-bottom:2rem;">
      <h2 style="font-family:var(--font-h); font-size:1.1rem; color:var(--dark); margin-bottom:0.5rem;">🌿 Skvěle se kombinuje s</h2>
      <p style="color:var(--text-light); margin:0;">{kombinace}</p>
    </div>

    <!-- Zajímavost -->
    <div style="margin-bottom:2.5rem;">
      <h2 style="font-family:var(--font-h); font-size:1.1rem; color:var(--dark); margin-bottom:0.5rem;">📖 Věděli jste?</h2>
      <p style="color:var(--text-light); line-height:1.75; margin:0;">
        {pocitove}
      </p>
    </div>

    <!-- BEWIT odkaz -->
    <div style="background:var(--cream-dk); border-radius:1rem; padding:2rem; text-align:center; border:1px solid var(--border);">
      <a href="{url}" target="_blank" rel="noopener" class="btn-orange" style="font-size:1rem; padding:0.75rem 2rem;">
        Chcete {display_name} vyzkoušet? →
      </a>
      <p style="font-size:0.8rem; color:var(--text-light); margin:0.75rem 0 0;">Jako registrovaný zákazník získáte slevu až 50 % na vybrané produkty.</p>
    </div>

  </div>
</section>

<!-- ── Disclaimer ── -->
<p style="text-align:center; font-size:0.8rem; color:#8a7a6a; padding:0.75rem 1rem; background:var(--cream);">
  Informace na této stránce mají výhradně informační charakter. Esenciální oleje nejsou náhradou lékařské péče.
</p>

<!-- ── Footer ── -->
<footer class="footer">
  <div class="footer-botanical">🌿 ✦ 🌸 ✦ 🌿</div>
  <p class="footer-quote">„Tady nejde o výkon ani dokonalost. Jen o návrat k sobě."</p>
  <p class="footer-heart">♥</p>
  <p class="footer-copy">© 2026 esenci.cz</p>
</footer>

<script>
  const toggle = document.getElementById('navToggle');
  const links  = document.getElementById('navLinks');
  toggle.addEventListener('click', () => links.classList.toggle('open'));
</script>
</body>
</html>'''
    return html


def get_latin_name(text):
    """Try to extract Latin name from the PDF text (usually line 2 or 3)."""
    if not text:
        return ""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    # Skip page number line
    filtered = [l for l in lines if not re.match(r'^\d+$', l)]
    # Latin names typically look like "Genus species" - two capitalized words or contain space
    # Usually appears in first 3 lines
    for i, line in enumerate(filtered[:4]):
        # Skip if it matches the Czech name (has Czech diacritics or is keyword list)
        if i == 0:
            continue  # Skip Czech name
        # Check if it looks like a Latin binomial
        words = line.split()
        if len(words) >= 2 and words[0][0].isupper():
            # If line 2 looks different from line 1 and isn't all-caps
            if not line.isupper() and len(line) < 50:
                # Might be Latin name OR English name
                # Latin names usually contain at least one non-Czech-diacritic word
                return line
    return ""


# Main processing
generated = []
errors = []

print("Loading PDFs...")

# Pre-load all single oil pages
single_pages = {}
print("Extracting single oil pages...")
with pdfplumber.open(SINGLE_PDF) as pdf:
    total_single = len(pdf.pages)
    for bewit in bewit_urls:
        if bewit['source'] == 'single_oils':
            page_num = bewit['page']  # 1-indexed page number
            pdf_index = page_num - 1  # convert to 0-indexed
            if pdf_index < total_single:
                page = pdf.pages[pdf_index]
                raw = page.extract_text()
                if raw:
                    fixed = fix_czech(raw)
                    single_pages[page_num] = fixed

print(f"Extracted {len(single_pages)} single oil pages")

# Pre-load all blend pages
blend_pages = {}
print("Extracting blend pages...")
with pdfplumber.open(BLENDS_PDF) as pdf:
    total_blends = len(pdf.pages)
    for bewit in bewit_urls:
        if bewit['source'] == 'blends':
            page_num = bewit['page']
            pdf_index = page_num - 1
            if pdf_index < total_blends:
                page = pdf.pages[pdf_index]
                raw = page.extract_text()
                if raw:
                    fixed = fix_czech(raw)
                    blend_pages[page_num] = fixed

print(f"Extracted {len(blend_pages)} blend pages")

# Now generate HTML files
count = 0
skipped = []

for bewit in bewit_urls:
    name = bewit['text'].strip()
    slug = bewit['slug']
    url = bewit['url']
    source = bewit['source']
    page_num = bewit['page']

    # Skip Bergamot (already exists)
    if name == 'Bergamot':
        print(f"  Skipping Bergamot (already exists)")
        skipped.append(name)
        continue

    # Get oleje data
    oil_data = oleje_by_name.get(name, {})
    typ = oil_data.get('typ', 'olej' if source == 'single_oils' else 'smes')
    popis = oil_data.get('popis', '')
    fullname = oil_data.get('fullname', name)

    if source == 'single_oils':
        # Single oil
        filename = f"olej-{slug}.html"
        filepath = os.path.join(OUT_DIR, filename)

        text = single_pages.get(page_num, '')
        parsed = parse_single_oil(text, popis)

        # Try to get Latin name from PDF
        latin = get_latin_name(text)

        html = generate_html_single(name, latin, slug, url, typ, popis, parsed, fullname=name)

    else:
        # Blend
        filename = f"smes-{slug}.html"
        filepath = os.path.join(OUT_DIR, filename)

        text = blend_pages.get(page_num, '')
        parsed = parse_blend(text, popis)

        html = generate_html_blend(name, slug, url, popis, fullname, parsed)

    # Write file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)

    count += 1
    generated.append({'name': name, 'file': filename, 'source': source})

    if count % 50 == 0:
        print(f"  Progress: {count} files generated...")

print(f"\nDone! Generated {count} HTML files")
print(f"Skipped: {skipped}")

# Save generation log
with open(os.path.join(OUT_DIR, '_generated_pages.json'), 'w', encoding='utf-8') as f:
    json.dump(generated, f, ensure_ascii=False, indent=2)

print(f"Log saved to _generated_pages.json")
