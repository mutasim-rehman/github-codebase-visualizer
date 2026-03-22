import os
import hashlib
import re
from pathlib import Path

JS_IMPORT_RE = re.compile(r'(?:import\s+.*?\s+from\s+[\'"](.*?)[\'"]|require\([\'"](.*?)[\'"]\))')

# Common ignore directories
IGNORE_DIRS = {".git", "node_modules", ".next", "venv", "__pycache__", ".venv", "env", ".idea", ".vscode", "dist", "build"}

# Common ignore extensions
IGNORE_EXTS = {".csv", ".txt", ".map"}

IGNORE_FILES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml"}

# Basic extension mapping
LANG_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "React",
    ".ts": "TypeScript",
    ".tsx": "React TypeScript",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "SASS",
    ".java": "Java",
    ".cpp": "C++",
    ".c": "C",
    ".h": "C/C++ Header",
    ".hpp": "C++ Header",
    ".cs": "C#",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".sh": "Shell",
    ".md": "Markdown",
    ".json": "JSON",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".xml": "XML",
    ".ipynb": "Jupyter Notebook",
    ".sql": "SQL",
    ".vue": "Vue",
    ".svelte": "Svelte"
}

def is_ignored(path: Path) -> bool:
    for part in path.parts:
        if part in IGNORE_DIRS:
            return True
    return False

def analyze_directory(root_path: str):
    root = Path(root_path)
    total_files = 0
    total_loc = 0
    generated_loc = 0
    lang_stats = {}
    file_list = []
    file_hashes = {}
    duplicates = []

    for path in root.rglob("*"):
        if path.is_file() and not is_ignored(path):
            ext = path.suffix.lower()
            if ext in IGNORE_EXTS or ext == ".ipynb":
                continue
                
            total_files += 1
            lang = LANG_MAP.get(ext, "Other")
            
            is_generated = path.name in IGNORE_FILES or path.name.endswith(".min.js") or path.name.endswith(".min.css") or (ext == ".json" and path.stat().st_size > 500 * 1024)
            
            file_imports = []
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    lines = content.splitlines()
                    loc = len(lines)
                    f_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
                    
                    if lang in ["JavaScript", "TypeScript", "React", "React TypeScript", "Vue", "Svelte"]:
                        for match in JS_IMPORT_RE.finditer(content):
                            imp = match.group(1) or match.group(2)
                            if imp:
                                file_imports.append(imp)
                        file_imports = list(set(file_imports))
            except UnicodeDecodeError:
                continue # Skip binary files
                
            # Identical duplicate detection
            is_duplicate = False
            if f_hash in file_hashes:
                is_duplicate = True
                duplicates.append({"path": str(path.relative_to(root)), "duplicate_of": file_hashes[f_hash]})
            else:
                # Require at least 5 lines to be considered a meaningful duplicate
                if loc > 5 and not is_generated:
                    file_hashes[f_hash] = str(path.relative_to(root))
                    
            if loc > 10000:
                is_generated = True
                
            if is_generated:
                generated_loc += loc
            else:
                total_loc += loc
            
            if lang not in lang_stats:
                lang_stats[lang] = {"files": 0, "loc": 0}
            lang_stats[lang]["files"] += 1
            if not is_generated:
                lang_stats[lang]["loc"] += loc
            
            file_list.append({"path": str(path.relative_to(root)), "loc": loc, "lang": lang, "full_path": str(path), "is_generated": is_generated, "is_duplicate": is_duplicate, "imports": file_imports})
            
    # Top 5 largest files
    file_list.sort(key=lambda x: x["loc"], reverse=True)
    top_files = file_list[:5]
    
    return {
        "total_files": total_files,
        "total_loc": total_loc,
        "generated_loc": generated_loc,
        "lang_stats": lang_stats,
        "top_files": top_files,
        "all_files": file_list,
        "duplicates": duplicates
    }
