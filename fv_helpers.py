import ast
import astunparse
import inspect
import os

from exceptions import EntryNotFoundException

def open_dir(parent, layer, path):
    """open a directory and add its contents to the view_window tree

    Args:
        parent (dict): parent dictionary in view_window tree
        layer (str): name of the directory to open
    """
    print(f"open dir path {path}")
    if not os.path.isdir(path):
        raise EntryNotFoundException(f'Directory "{path}" not found')
    # List the contents of the directory, including hidden files
    contents = os.listdir(path)
    # Initialize the directory's dictionary
    parent[layer] = {}
    # Add the contents of the directory to the dictionary
    for item in contents:
        # Full path to the item
        full_item_path = os.path.join(path, item)
        # If the item is a directory, append a slash to its name
        if os.path.isdir(full_item_path):
            item += '/'
        parent[layer][item] = None

def open_file(parent, layer, filepath):
    """Parses the Python file and adds its structure to the view window."""
    with open(filepath, 'r') as file:
        content = file.read()

    # parse the file content into an AST
    tree = ast.parse(content)

    # add an entry for imports
    parent[layer] = {"imports": None, "root_code": None}

    # iterate over immediate child nodes and add entries for functions and classes
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef):
            # it's a function
            parent[layer][f"func:{node.name}"] = None
        elif isinstance(node, ast.ClassDef):
            # it's a class
            parent[layer][f"class:{node.name}"] = None


def open_imports(parent, layer, filepath):
    """Adds import information to the view window."""
    with open(filepath, 'r') as file:
        content = file.read()

    # parse the file content into an AST
    tree = ast.parse(content)
    # iterate over immediate child nodes and add entries for imports
    for node in ast.iter_child_nodes(tree):
        if parent[layer] is None:
            parent[layer] = ""
        if isinstance(node, ast.Import):
            for alias in node.names:
                parent[layer] += f"import {alias.name}\n"
        elif isinstance(node, ast.ImportFrom):
            parent[layer] += f"from {node.module} import "
            parent[layer] += ', '.join([alias.name for alias in node.names]) + "\n"
            
def open_root_code(parent, layer, filepath):
    """Parses the Python file and adds its root level code to the view window."""

    # Parse the file into an AST
    with open(filepath, 'r') as file:
        tree = ast.parse(file.read())

    root_code = []
    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.Import, ast.ImportFrom)):
            # Convert the node back into Python source code
            source_code = ast.unparse(node)
            root_code.append(source_code)
    parent[layer] = root_code

        
def open_class(parent, layer, filepath):
    """Parses the Python class and adds its structure to the view window."""
    # 'class:' needs to be removed to get the class name
    classname = layer[6:]  
    with open(filepath, 'r') as file:
        content = file.read()

    # parse the file content into an AST
    tree = ast.parse(content)
    parent[layer] = {"inherits": None, "static_vars": None}

    # walk the AST and find the target class
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == classname:

            # add entries for methods
            for sub_node in ast.iter_child_nodes(node):
                if isinstance(sub_node, ast.FunctionDef):
                    if any(isinstance(dec, ast.Attribute) and dec.attr == 'staticmethod' for dec in sub_node.decorator_list):
                        parent[layer][f"func:static:{sub_node.name}"] = None
                    else:
                        parent[layer][f"func:{sub_node.name}"] = None

            # add entries for inherited classes
            if node.bases:
                parent[layer]["inherits"] = ", ".join(node.bases)
            break
        
def open_static_vars(parent, layer, filepath, classname):
    """Parses the Python class and adds its static variables to the view window."""

    # Parse the file into an AST
    with open(filepath, 'r') as file:
        tree = ast.parse(file.read())

    node = find_class(classname, tree)
    static_vars = []
    for subnode in ast.iter_child_nodes(node):
        if isinstance(subnode, ast.Assign):
            # Parse each assignment and add it to the static_vars list
            for target in subnode.targets:
                static_vars.append(f"{target.id} = {ast.unparse(subnode.value)}")
    parent[layer] = static_vars


def find_class(classname, tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == classname:
            return node
    return None

def open_func(parent, layer, filepath, classname=None):
    """Opens a function and adds its content to the view window."""

    # Extract function name from layer
    func_name = layer.split(":")[1]
    func_name = func_name.replace("static:", "")

    # Parse the file into an AST
    with open(filepath, 'r') as file:
        tree = ast.parse(file.read())

    # If classname is specified, find the class in the AST first
    if classname:
        node = find_class(classname, tree)
        for subnode in ast.iter_child_nodes(node):
            if isinstance(subnode, ast.FunctionDef) and subnode.name == func_name:
                func_lines = astunparse.unparse(subnode)
                parent[layer] = func_lines
                return

    # If no classname is specified, or the class was not found,
    # find the function in the AST directly
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            func_lines = astunparse.unparse(node)
            parent[layer] = func_lines
            return


    # Function not found in file
    raise EntryNotFoundException(f"Function {func_name} not found in {filepath}")

