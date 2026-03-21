from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def print_summary(stats, hotspots):
    print_basic_stats(stats)
    print_language_stats(stats["lang_stats"])
    print_top_files(stats["top_files"])
    print_python_stats(stats["all_files"])
    print_hotspots(hotspots)
    
def print_basic_stats(stats):
    console.print("\n")
    console.print(Panel(f"[bold green]Total Files:[/bold green] {stats['total_files']} | [bold green]Total LOC:[/bold green] {stats['total_loc']}", title="Codebase Summary"))

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

def print_hotspots(hotspots):
    if not hotspots:
        console.print("\n[bold green]No hotspots detected![/bold green] 🎉\n")
        return
        
    table = Table(title="🔥 Code Hotspots (High Complexity/Size)")
    table.add_column("File", style="cyan")
    table.add_column("Issues", style="red")
    table.add_column("LOC", justify="right", style="green")
    
    # Show top 10 hotspots max
    for h in hotspots[:10]:
        table.add_row(h['path'], "\n".join(h['reasons']), str(h['loc']))
        
    console.print(table)
    console.print("\n")
