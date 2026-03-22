from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.text import Text

console = Console()

def print_summary(stats, hotspots):
    print_basic_stats(stats)
    print_tree(stats["all_files"])
    print_language_stats(stats["lang_stats"])
    print_top_files(stats["top_files"])
    print_duplicates(stats.get("duplicates", []))
    print_priority_fixes(hotspots)
    print_hotspots(hotspots)
    
def print_basic_stats(stats):
    console.print("\n")
    summary_text = (
        f"[bold green]Total Files:[/bold green] {stats['total_files']} | "
        f"[bold green]App LOC:[/bold green] {stats['total_loc']} | "
        f"[dim]Generated/Vendor LOC: {stats.get('generated_loc', 0)}[/dim]"
    )
    console.print(Panel(summary_text, title="Codebase Summary"))

def print_language_stats(lang_stats):
    table = Table(title="Language Distribution")
    table.add_column("Language", style="cyan")
    table.add_column("Files", justify="right", style="magenta")
    table.add_column("LOC", justify="right", style="green")
    
    # Sort by LOC
    sorted_langs = sorted(lang_stats.items(), key=lambda x: x[1]['loc'], reverse=True)
    
    for lang, metrics in sorted_langs:
        table.add_row(lang, str(metrics['files']), str(metrics['loc']))
        
    console.print(table)
    
def print_tree(all_files):
    """Renders a color-coded hierarchical directory tree."""
    # Build a set of duplicate paths for fast lookup
    dup_paths = set()
    # We need the duplicates list; reconstruct from all_files if needed
    # (It's already embedded as a flag inside file dicts if added)
    # We'll rely on duplicate_of key injected into files during traversal. 
    # For now, detect by checking if file was seen twice - we'll use a simpler approach:
    # build from stats duplicates list instead, which is passed via all_files side-channel
    # Actually we only have all_files here. Let's mark duplicate paths via a separate set.
    # We embed is_duplicate on the file dict in core.py, handled below.
    
    # Build nested dict representing the tree structure
    tree_data = {}
    for f in all_files:
        parts = f["path"].replace("\\", "/").split("/")
        node = tree_data
        for part in parts:
            node = node.setdefault(part, {})
        node["__file__"] = f

    def _get_label(name, file_info=None):
        if file_info is None:
            # Directory
            return Text(f"📁 {name}/", style="bold blue")
        
        loc = file_info.get("loc", 0)
        is_generated = file_info.get("is_generated", False)
        is_duplicate = file_info.get("is_duplicate", False)
        
        badge = f" [{loc} LOC]"
        
        if is_duplicate:
            style = "yellow"
            icon = "⚠ "
        elif is_generated:
            style = "dim"
            icon = "⚙ "
        elif loc > 1000:
            style = "bold red"
            icon = "🔴 "
        elif loc > 500:
            style = "bold yellow"
            icon = "🟡 "
        else:
            style = "green"
            icon = "🟢 "
        
        return Text(f"{icon}{name}{badge}", style=style)

    def _build_rich_tree(node, rich_node):
        for key, value in sorted(node.items()):
            if key == "__file__":
                continue
            file_info = value.get("__file__")
            if file_info is not None and len(value) == 1:
                # It's a leaf file
                rich_node.add(_get_label(key, file_info))
            else:
                # It's a directory
                branch = rich_node.add(_get_label(key))
                _build_rich_tree(value, branch)
    
    root = Tree(Text("📦 Project Root", style="bold white"))
    _build_rich_tree(tree_data, root)
    
    console.print("")
    console.print(Panel(
        "[green]🟢 Normal[/green]  [yellow]🟡 >500 LOC[/yellow]  [red]🔴 >1000 LOC[/red]  [yellow]⚠  Duplicate[/yellow]  [dim]⚙  Generated[/dim]",
        title="File Tree",
        subtitle="Color Legend"
    ))
    console.print(root)
    console.print("")

def print_top_files(top_files):
    table = Table(title="Top 5 Largest Files")
    table.add_column("File", style="cyan")
    table.add_column("LOC", justify="right", style="green")
    table.add_column("Language", style="magenta")
    
    for f in top_files:
        table.add_row(f['path'], str(f['loc']), f['lang'])
        
    console.print(table)
    
def print_python_stats(all_files):
    # Filter Python files to list their functions, classes and dependencies
    py_files = [f for f in all_files if f.get("lang") == "Python" and f.get("ast_metrics")]
    if not py_files:
        return
        
    table = Table(title="Python Files Breakdown")
    table.add_column("File", style="cyan")
    table.add_column("Classes", justify="right", style="blue")
    table.add_column("Functions", justify="right", style="blue")
    table.add_column("Dependencies", style="yellow")
    
    for f in sorted(py_files, key=lambda x: x['loc'], reverse=True)[:10]: # Top 10 Python files to not spam output
        ast = f["ast_metrics"]
        deps = ", ".join(ast["imports"]) if ast["imports"] else "-"
        # limit deps string size if it's too long
        if len(deps) > 40:
            deps = deps[:37] + "..."
        table.add_row(f['path'], str(ast['classes']), str(ast['functions']), deps)
        
    console.print(table)

def print_duplicates(duplicates):
    if not duplicates:
        return
    table = Table(title="Duplicate Files Detection")
    table.add_column("Duplicate Path", style="yellow")
    table.add_column("Original Path", style="cyan")
    
    for d in duplicates[:10]:
        table.add_row(d["path"], d["duplicate_of"])
        
    console.print(table)

def print_priority_fixes(hotspots):
    # Filter only High Risk items
    priority = [h for h in hotspots if h.get("risk_level") == "High"]
    if not priority:
        console.print("\n[bold green]No Priority Fixes needed![/bold green] 🎉\n")
        return
        
    table = Table(title="🚨 Priority Fixes (Actionable Insights)")
    table.add_column("File", style="cyan")
    table.add_column("Risk", style="red bold")
    table.add_column("Action Items", style="yellow")
    
    for p in priority[:5]:
        table.add_row(p['path'], p['risk_level'], "\n".join(p['reasons']))
        
    console.print(table)
    console.print("\n")

def print_hotspots(hotspots):
    # Show medium risk hotspots since high risk are handled by priority
    medium = [h for h in hotspots if h.get("risk_level", "Medium") == "Medium"]
    if not medium:
        return
        
    table = Table(title="🔥 Code Hotspots (Medium Risk)")
    table.add_column("File", style="cyan")
    table.add_column("Issues", style="red")
    table.add_column("LOC", justify="right", style="green")
    
    # Show top 5 medium hotspots max
    for h in medium[:5]:
        table.add_row(h['path'], "\n".join(h['reasons']), str(h['loc']))
        
    console.print(table)
    console.print("\n")
