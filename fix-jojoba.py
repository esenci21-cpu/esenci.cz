import re
import glob

jojoba_link = '(např. <a href="https://bewit.love/produkt/bio-jojoba-oil?i=3fqlzp0xrllj7" target="_blank" rel="noopener">jojobový</a>)'

def replace_in_produkt_jak(content):
    def replacer(m):
        return m.group(0).replace('v nosném oleji', 'v nosném oleji ' + jojoba_link)
    pattern = r'<p class="produkt-jak">.*?</p>'
    return re.sub(pattern, replacer, content, flags=re.DOTALL)

for filepath in glob.glob('*.html'):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = replace_in_produkt_jak(content)

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            f.write(new_content)
        print(f'Upraveno: {filepath}')

print('Hotovo')
