import os
from pathlib import Path

# Common ignore directories
IGNORE_DIRS = {".git", "node_modules", ".next", "venv", "__pycache__", ".venv", "env", ".idea", ".vscode", "dist", "build"}

# Common ignore extensions
IGNORE_EXTS = {".csv", ".txt"}

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
    lang_stats = {}
    file_list = []

    for path in root.rglob("*"):
        if path.is_file() and not is_ignored(path):
            ext = path.suffix.lower()
            if ext in IGNORE_EXTS:
                continue
                
            total_files += 1
            lang = LANG_MAP.get(ext, "Other")
            
            try:
                with open(path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    loc = len(lines)
            except UnicodeDecodeError:
                continue # Skip binary files
                
            total_loc += loc
            
            if lang not in lang_stats:
                lang_stats[lang] = {"files": 0, "loc": 0}
            lang_stats[lang]["files"] += 1
            lang_stats[lang]["loc"] += loc
            
            file_list.append({"path": str(path.relative_to(root)), "loc": loc, "lang": lang, "full_path": str(path)})
            
    # Top 5 largest files
    file_list.sort(key=lambda x: x["loc"], reverse=True)
    top_files = file_list[:5]
    
    return {
        "total_files": total_files,
        "total_loc": total_loc,
        "lang_stats": lang_stats,
        "top_files": top_files,
        "all_files": file_list
    }
