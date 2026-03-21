import subprocess
import tempfile
import atexit
import shutil
import os

def clone_repo(url: str, depth: int = 1) -> str:
    """Clones a github url to a temp directory and returns the path."""
    temp_dir = tempfile.mkdtemp(prefix="codebase_analyzer_")
    
    # Register cleanup
    def cleanup():
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass
                
    atexit.register(cleanup)
    
    print(f"Cloning {url} into temporary directory...")
    # Use subprocess to run git clone
    cmd = ["git", "clone", url, temp_dir]
    if depth > 0:
        cmd.extend(["--depth", str(depth)])
        
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to clone repository: {result.stderr}")
        
    return temp_dir
