
class Blueprint:
    def __init__(self, name, url_prefix):
        self.name = name
        self.url_prefix = url_prefix
        self.routes = []

    def route(self, path, methods=None):
        def decorator(func):
            self.routes.append((path, func, methods))
            return func
        return decorator

    def register(self, app):
        for path, func, methods in self.routes:
            app.router.add_route(self.url_prefix + path, func, methods)