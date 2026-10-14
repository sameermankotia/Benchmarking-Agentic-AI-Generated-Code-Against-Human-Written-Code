class Blueprint:
    def __init__(self, name, import_name, url_prefix=None):
        self.name = name
        self.import_name = import_name
        self.url_prefix = url_prefix
        self.routes = {}

    def route(self, path, methods=None):
        if methods is None:
            methods = ['GET']

        def decorator(func):
            self.routes[(path, tuple(methods))] = func
            return func

        return decorator

    def register(self, app):
        for (path, methods), handler in self.routes.items():
            full_path = f"{self.url_prefix}{path}" if self.url_prefix else path
            app.routes[(full_path, methods)] = handler