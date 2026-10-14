class Blueprint:
    def __init__(self, name, import_name):
        self.name = name
        self.import_name = import_name
        self.routes = []

    def route(self, path, methods=['GET']):
        def decorator(func):
            self.routes.append((path, func, methods))
            return func
        return decorator

    def register(self, app, url_prefix):
        for path, func, methods in self.routes:
            app.router.add_route(f"{url_prefix}{path}", func, methods)
