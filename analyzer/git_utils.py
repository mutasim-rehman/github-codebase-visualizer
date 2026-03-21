import subprocess
import tempfile
import atexit
import shutil
import os
import re

def parse_github_url(url: str):
    """Parses a github url and returns the base repo url and branch (if any)."""
    url = url.rstrip('/')
    match = re.search(r"^(https?://github\.com/[^/]+/[^/]+)", url)
    if not match:
        return url, None
        
    base_url = match.group(1)
    if base_url.endswith(".git"):
        base_url = base_url[:-4]
        
    branch_match = re.search(r"/(?:tree|blob)/([^/]+)", url)
    branch = branch_match.group(1) if branch_match else None
    
    return base_url, branch

def clone_repo(url: str, depth: int = 1) -> str:
    """Clones a github url to a temp directory and returns the path."""
    base_url, branch = parse_github_url(url)
    
    temp_dir = tempfile.mkdtemp(prefix="codebase_analyzer_")
    
    # Register cleanup
    def cleanup():
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass
                
    atexit.register(cleanup)
    
    print(f"Cloning {base_url} into temporary directory...")
    # Use subprocess to run git clone
    cmd = ["git", "clone", base_url, temp_dir]
    if branch:
        cmd.extend(["-b", branch])
    if depth > 0:
        cmd.extend(["--depth", str(depth)])
        
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to clone repository: {result.stderr}")
        
    return temp_dir
