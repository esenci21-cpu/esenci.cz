#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract oil and blend data from BEWIT PDF catalogs.
Outputs: C:\Claude\projekty\www\esenci.cz\oleje-data.json
"""

import os
import re
import json
import pdfplumber

BASE = r'C:\Users\x2\Desktop\xx'
OUTPUT = r'C:\Claude\projekty\www\esenci.cz\oleje-data.json'

# Section headers to stop tagline detection
SECTION_HEADERS = {
    'emoční a duchovní působení', 'emocni a duchovni pusobeni',
    'historie a zajímavosti', 'historie a zajimavosti',
    'hlavní účinky', 'hlavni ucinky',
    'orac:', 'vhodné', 'vhodne',
}

# Czech-specific diacritical characters that appear in keywords but not English names
CZECH_CHARS = set('áéíóúýěščřžůÁÉÍÓÚÝĚŠČŘŽŮ')


def looks_like_header(line):
    """Check if line is a section header."""
    low = line.strip().lower()
    for h in SECTION_HEADERS:
        if low.startswith(h):
            return True
    return False


def is_czech_tagline(line):
    """Detect if a line is a Czech keywords tagline (not an English name).

    Key insight: English names with commas always use parentheses, e.g.
    'Acacia (gum arabic, Egyptian thorn)' — the commas are inside parens.
    Czech taglines: 'Jasnost, dech, meditace, klid' — commas without parens.
    So: commas + no parentheses + short = tagline.
    Also: commas + Czech diacritical chars = tagline (even if parens present, unlikely).
    """
    has_comma = ',' in line
    has_paren = '(' in line or ')' in line
    has_czech = any(c in CZECH_CHARS for c in line)
    is_short = len(line) < 70

    if not has_comma:
        return False

    # Czech diacritics + commas → definitely a tagline
    if has_czech and has_comma:
        return True

    # Commas, no parentheses, short → could be tagline or English alternate name.
    # Distinguish: Czech taglines have ≥3 comma-separated keywords.
    # English alternates like "Cypriol, Nagarmotha" or "Zedoary, white turmeric"
    # have only 1-2 comma-separated parts.
    if has_comma and not has_paren and is_short:
        parts = [p.strip() for p in line.split(',')]
        if len(parts) >= 3:  # ≥3 keywords → tagline (e.g. "Jasnost, dech, meditace, klid, regenerace")
            return True

    return False

    return False


def truncate(text, maxlen=60):
    """Truncate text to maxlen chars, at word boundary."""
    if len(text) <= maxlen:
        return text
    truncated = text[:maxlen].rsplit(',', 1)[0].rsplit(' ', 1)[0]
    return truncated.rstrip(' ,')


def extract_oils(pdf_path):
    """Extract single essential oil entries from PDF1.

    Structure per page:
      line[0] = entry number
      line[1] = Czech name
      line[2] = Latin name
      line[3] = English name OR Czech tagline (if no English name)
      line[4] = Czech tagline OR ORAC OR section header
      line[5+] = section headers and body text
    """
    entries = []
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        # Content starts at page 5 (index 4), pages 1-4 are ToC and disclaimer
        for page_idx in range(4, total_pages):
            page = pdf.pages[page_idx]
            text = page.extract_text()
            if not text:
                continue
            lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
            if not lines:
                continue

            # First line should be a page/entry number
            if not lines[0].isdigit():
                continue

            if len(lines) < 3:
                continue

            czech_name = lines[1]
            # Skip if it looks like a continuation / disclaimer page
            if len(czech_name) > 60 or czech_name.startswith('Tento'):
                continue

            tagline = ''
            fallback_sentence = ''  # first body sentence if no tagline found

            # Check line[3]: could be English name or Czech tagline
            # If line[3] is a Czech tagline (has Czech chars + commas), use it
            if len(lines) > 3 and is_czech_tagline(lines[3]):
                tagline = lines[3]
            else:
                # line[3] is the English name; look for tagline at line[4]+
                in_emo_section = False
                for candidate_idx in range(4, min(12, len(lines))):
                    candidate = lines[candidate_idx]
                    low = candidate.lower()
                    if low.startswith('orac'):
                        continue
                    if low.startswith('emo'):
                        in_emo_section = True
                        continue
                    if low.startswith('historie') or low.startswith('hlavn'):
                        break
                    if in_emo_section and not fallback_sentence:
                        # First body sentence in the emotional section
                        import re
                        first_sent = re.split(r'[.!?]', candidate)[0].strip()
                        fallback_sentence = first_sent
                        continue
                    if not in_emo_section:
                        if looks_like_header(candidate):
                            in_emo_section = True
                            continue
                        # A tagline is a Czech comma-separated keyword list
                        if is_czech_tagline(candidate):
                            tagline = candidate
                            break

            popis_raw = tagline if tagline else fallback_sentence
            entry = {
                'name': czech_name,
                'typ': 'olej',
                'popis': truncate(popis_raw, 60),
            }
            entries.append(entry)
            print(f"  OIL #{lines[0]:>3}: {czech_name[:40]!r:42} | {entry['popis'][:50]!r}")

    return entries


def extract_blends(pdf_path):
    """Extract blend entries from PDF2."""
    entries = []
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        # Content starts around page 6 (index 5); pages 1-5 are ToC/disclaimer
        for page_idx in range(5, total_pages):
            page = pdf.pages[page_idx]
            text = page.extract_text()
            if not text:
                continue
            lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
            if not lines:
                continue

            # First line = entry number
            if not lines[0].isdigit():
                continue
            if len(lines) < 3:
                continue

            code = lines[1]      # blend code e.g. "3S", "A-PAR", "AFRODITE"
            fullname = lines[2]  # full Czech/English name

            # Skip disclaimer pages
            if len(code) > 40 or code.startswith('Tento'):
                continue

            # Find description: lines[3] onwards until 'Emoce:' or end
            desc_lines = []
            for l in lines[3:]:
                low = l.lower()
                if low.startswith('emoce:') or low.startswith('pocitov'):
                    break
                if looks_like_header(l):
                    break
                desc_lines.append(l)

            description = ' '.join(desc_lines).strip()
            # Take first sentence or truncate
            first_sentence = re.split(r'[.!?]', description)[0].strip()

            entry = {
                'name': code,
                'fullname': fullname,
                'typ': 'smes',
                'popis': truncate(first_sentence, 60),
            }
            entries.append(entry)
            print(f"  BLEND #{lines[0]:>3}: {code!r:15} {fullname[:20]!r:22} | {entry['popis'][:45]!r}")

    return entries


def main():
    # Find PDFs
    files = sorted(os.listdir(BASE))
    pdfs = [f for f in files if f.endswith('.pdf')]
    print(f"Found PDFs: {pdfs}\n")

    pdf1 = os.path.join(BASE, pdfs[0])  # Jednodruhove EO
    pdf2 = os.path.join(BASE, pdfs[1])  # Smesi EO

    print("=== Extracting single oils (PDF1) ===")
    oils = extract_oils(pdf1)
    print(f"\nExtracted {len(oils)} oils.\n")

    print("=== Extracting blends (PDF2) ===")
    blends = extract_blends(pdf2)
    print(f"\nExtracted {len(blends)} blends.\n")

    all_entries = oils + blends
    print(f"Total entries: {len(all_entries)}")

    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(all_entries, f, ensure_ascii=False, indent=2)

    print(f"\nSaved to: {OUTPUT}")
    print(f"Summary: {len(oils)} oils + {len(blends)} blends = {len(all_entries)} total")


if __name__ == '__main__':
    main()
