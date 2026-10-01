import os
import ast

def get_imports(filepath):
    imports = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=filepath)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.add(f"{module}.{alias.name}" if module else alias.name)
                    imports.add(module)
    except Exception:
        pass
    return imports

all_files = []
for root, dirs, files in os.walk('app'):
    for file in files:
        if file.endswith('.py') and not file.startswith('__'):
            all_files.append(os.path.join(root, file))

all_imports = set()
for file in all_files:
    all_imports.update(get_imports(file))

# Check for unused python files
print("Potentially unreferenced files (not in any import statement):")
for file in all_files:
    module_path = file.replace('app\\', 'app.').replace('.py', '').replace('\\', '.')
    is_imported = any(module_path in imp for imp in all_imports)
    if not is_imported and 'main' not in module_path and 'router' not in module_path and 'api' not in module_path and 'tasks' not in module_path:
        print(module_path)
