import os, glob

folder = r'C:\Claude\projekty\www\esenci.cz'
old = '<li><a href="./temata.html">Témata</a></li>'
new = '<li><a href="./temata.html">Témata</a></li>\n        <li><a href="./jak-pouzivat.html">Jak používat</a></li>'

files = glob.glob(os.path.join(folder, '*.html'))
changed = []

for fpath in files:
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    if old in content and 'jak-pouzivat.html' not in content:
        content = content.replace(old, new)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        changed.append(os.path.basename(fpath))

print(f"Upraveno {len(changed)} souborů:")
for f in changed:
    print(f"  {f}")
