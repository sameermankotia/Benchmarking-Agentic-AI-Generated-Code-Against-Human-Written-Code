class Router:
    def __init__(self):
        self.routes = []

    def add_route(self, path, func, methods):
        self.routes.append((path, func, methods))

    def dispatch(self, request):
        for path, func, methods in self.routes:
            if request.path == path and request.method in methods:
                return func()
        return Response("Not Found", status=404)
