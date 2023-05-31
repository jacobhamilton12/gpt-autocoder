import os
import json
import inspect

import fv_helpers as FV
from exceptions import EntryNotFoundException, UnknownEntryTypeException

class FilesViewer:
    def __init__(self, directory):
        self.directory = directory
        self.view_window = self.scan_directory(directory)

    def scan_directory(self, directory):
        contents = {}
        try:
            for entry in os.listdir(directory):
                path = os.path.join(directory, entry)
                if os.path.isdir(path):
                    contents[entry + '/'] = None
                else:
                    contents[entry] = None
        except FileNotFoundError:
            print("Directory not found.")
        return contents
            
    def _get_path(self, entry):
        path = [self.directory]
        for layer in entry:
            if layer.endswith(".py"):
                path.append(layer)
                break
            # remove /
            path.append(layer[:-1])
        path = "/".join(path)
        return path

    def open(self, entry):
        """open a dir/file/class/function

        Args:
            entry (list): list representing location in view_window tree
            for ex: ["dir/", "file.py", "class:myclass", "func:myfunc"]
        """
        parent = self.view_window
        path = self._get_path(entry)
        for i, layer in enumerate(entry):
            if layer not in parent:
                raise EntryNotFoundException(entry)
            if parent[layer]:
                parent = parent[layer]
                continue
            # if we didn't make it to the end of entry list
            # try to open current
            if layer != entry[-1]:
                self.open(entry[:i+1])
                continue
            # made it to bottom of tree
            if layer.endswith("/"):
                # it's a directory
                FV.open_dir(parent, layer, path)
            elif layer.endswith('.py'):
                # it's a python file
                FV.open_file(parent, layer, path)
            elif layer.startswith('class:'):
                # it's a class
                FV.open_class(parent, layer, path)
            elif layer.startswith('func:'):
                # it's a function
                if entry[-2].startswith("class:"):
                    FV.open_func(parent, layer, path, classname=entry[-2][6:])
                FV.open_func(parent, layer, path)
            elif layer == 'imports':
                FV.open_imports(parent, layer, path)
            elif layer == "static_vars":
                FV.open_static_vars(parent, layer, path, classname=entry[-2][6:])
            elif layer == "root_code":
                FV.open_root_code(parent, layer, path)
            else:
                raise UnknownEntryTypeException(entry)
            

    def close(self, entry):
        """close a dir/file/class/function

        Args:
            entry (list): list representing location in view_window tree
            for ex: ["dir/", "file.py", "class:myclass", "func:myfunc"]
        """
        parent = self.view_window
        for i, layer in enumerate(entry):
            if layer not in parent:
                raise EntryNotFoundException(entry)
            if i != len(entry) -1:
                parent = parent[layer]
                continue
            # closing
            parent[layer] = None

    def refresh_view_window(self, dictionary=None, entry=[]):
        if dictionary is None:
            dictionary = self.view_window
        for key, value in dictionary.items():
            new_entry = entry + [key]   # appending the new key to the path
            if value is not None:  # if the value is not None, recurse into it
                self.open(new_entry)   # call open on the current path
                self.refresh_view_window(value, new_entry)

    def view_window_to_string(self, d=None, indent=0):
        if d is None:
            d = self.view_window
        tree_str = ""
        for key, value in d.items():
            tree_str += '  ' * indent + str(key) + "\n"
            if isinstance(value, dict):
                tree_str += self.view_window_to_string(value, indent+1)
            else:
                tree_str += '  ' * indent + '  ' + str(value) + "\n"
        return tree_str
