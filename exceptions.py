class EntryNotFoundException(Exception):
    def __init__(self, entry):
        self.entry = entry
        super().__init__(f"Entry {entry} not found in view_window tree")
        
class UnknownEntryTypeException(Exception):
    def __init__(self, entry):
        self.entry = entry
        super().__init__(f"Unknown entry type {entry}")

