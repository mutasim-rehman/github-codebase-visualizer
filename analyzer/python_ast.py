import ast

def analyze_python_file(filepath: str):
    """Parses a Python file and returns AST metrics."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
    except Exception:
        return None
        
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
        
    class Visitor(ast.NodeVisitor):
        def __init__(self):
            self.current_nesting = 0
            self.max_nesting = 0
            self.classes = 0
            self.functions = 0
            self.longest_func = {"name": None, "loc": 0}
            self.imports = set()
            
        def visit_ClassDef(self, node):
            self.classes += 1
            self.generic_visit(node)
            
        def visit_FunctionDef(self, node):
            self.functions += 1
            # Calculate length
            loc = node.end_lineno - node.lineno + 1 if hasattr(node, "end_lineno") and node.end_lineno else 0
            if loc > self.longest_func["loc"]:
                self.longest_func = {"name": node.name, "loc": loc}
            self.generic_visit(node)
            
        def visit_AsyncFunctionDef(self, node):
            self.visit_FunctionDef(node)
            
        def visit_Import(self, node):
            for alias in node.names:
                self.imports.add(alias.name.split('.')[0])
            self.generic_visit(node)
            
        def visit_ImportFrom(self, node):
            if node.module:
                self.imports.add(node.module.split('.')[0])
            self.generic_visit(node)
            
        def visit_For(self, node):
            self._track_nesting(node)
        def visit_While(self, node):
            self._track_nesting(node)
        def visit_If(self, node):
            self._track_nesting(node)
        def visit_Try(self, node):
            self._track_nesting(node)
        def visit_With(self, node):
            self._track_nesting(node)
            
        def _track_nesting(self, node):
            self.current_nesting += 1
            if self.current_nesting > self.max_nesting:
                self.max_nesting = self.current_nesting
            self.generic_visit(node)
            self.current_nesting -= 1
            
    visitor = Visitor()
    visitor.visit(tree)
    
    return {
        "classes": visitor.classes,
        "functions": visitor.functions,
        "max_nesting": visitor.max_nesting,
        "longest_function": visitor.longest_func,
        "imports": list(visitor.imports)
    }
