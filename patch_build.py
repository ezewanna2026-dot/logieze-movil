import os, re, sys

def find_recipe():
    for base in ['/home/user/.venv', '/home/user', '/usr/local', '/usr', '/root', '/opt']:
        if not os.path.exists(base):
            continue
        for root, dirs, files in os.walk(base):
            if os.path.basename(root) == 'hostpython3' and '__init__.py' in files:
                if os.path.basename(os.path.dirname(root)) == 'recipes':
                    return os.path.join(root, '__init__.py')
    return None

recipe = find_recipe()
if not recipe:
    print('ERROR: hostpython3 recipe not found, cannot patch')
    sys.exit(0)

print('Found recipe:', recipe)
with open(recipe) as f:
    content = f.read()

hits = re.findall(r"version\s*=\s*'3\.[^']*'", content)
print('Current version patterns:', hits[:3])

content2 = re.sub(r"version\s*=\s*'3\.[0-9][^']*'", "version = '3.11.9'", content, count=1)
if content2 == content:
    print('WARNING: pattern not matched, printing first 20 lines:')
    for line in content.splitlines()[:20]:
        print(' ', line)
    sys.exit(0)

with open(recipe, 'w') as f:
    f.write(content2)

hits2 = re.findall(r"version\s*=\s*'3\.[^']*'", content2)
print('After patch:', hits2[:3])
print('SUCCESS: Patched hostpython3 to Python 3.11.9')
