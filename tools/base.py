class Tool:
    """One capability the model may call. Subclass, set the three attributes, implement run()."""
    name: str = ""
    description: str = ""
    parameters: dict = {}          # JSON-schema properties; all treated as required

    def run(self, **kwargs):
        raise NotImplementedError

    def schema(self):
        return {"type": "function", "function": {
            "name": self.name, "description": self.description,
            "parameters": {"type": "object", "properties": self.parameters,
                           "required": list(self.parameters)}}}
