import os, re, glob

folder = r'C:\Claude\projekty\www\esenci.cz'

# Patterns to fix - removing bottle sniffing, keeping diffuser
replacements = [
    # "přidej X kapek do difuzéru nebo přičichni přímo z lahvičky — ..."
    # → "přidej X kapek do difuzéru — ..."
    (r' nebo přičichni přímo z lahvičky', ''),
    # "přičichni přímo z lahvičky nebo ..."
    # → just the second part
    (r'přičichni přímo z lahvičky nebo ', ''),
    # "nebo přičichni z lahvičky ..."
    (r' nebo přičichni z lahvičky[^<.]*', ''),
    # "přičichni z lahvičky nebo ..."
    (r'přičichni z lahvičky nebo ', ''),
    # standalone "přičichni z lahvičky"
    (r'přičichni z lahvičky', 'přidej 2–3 kapky do difuzéru'),
]

files = glob.glob(os.path.join(folder, '*.html'))
changed = []

for fpath in files:
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)

    if content != original:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        changed.append(os.path.basename(fpath))

print(f"Upraveno {len(changed)} souborů:")
for f in changed:
    print(f"  {f}")
