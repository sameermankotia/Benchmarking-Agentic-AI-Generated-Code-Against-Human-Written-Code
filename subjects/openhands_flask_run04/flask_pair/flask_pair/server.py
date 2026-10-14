from wsgiref.simple_server import make_server

def run_dev_server(app, host, port):
    with make_server(host, port, app) as server:
        print(f"Running on http://{host}:{port}/ (Press CTRL+C to quit)")
        server.serve_forever()
