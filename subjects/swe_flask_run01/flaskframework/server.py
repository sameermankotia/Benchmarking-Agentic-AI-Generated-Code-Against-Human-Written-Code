"""
Built-in development server.
"""

import socket
import threading
from wsgiref.simple_server import make_server, WSGIServer, WSGIRequestHandler
from typing import Callable


class QuietWSGIRequestHandler(WSGIRequestHandler):
    """A WSGI request handler that can be made quiet."""
    
    def log_message(self, format, *args):
        """Override to control logging."""
        if getattr(self.server, 'quiet', False):
            return
        super().log_message(format, *args)


def run_simple(hostname: str, port: int, application: Callable, 
               use_reloader: bool = False, use_debugger: bool = False,
               use_evalex: bool = True, extra_files=None, reloader_interval: int = 1,
               reloader_type: str = 'auto', threaded: bool = False,
               processes: int = 1, request_handler=None, static_files=None,
               passthrough_errors: bool = False, ssl_context=None, quiet: bool = False):
    """Run a WSGI application with a simple development server."""
    
    if request_handler is None:
        request_handler = QuietWSGIRequestHandler
    
    # Create the server
    server = make_server(hostname, port, application, 
                        server_class=WSGIServer,
                        handler_class=request_handler)
    
    # Set quiet mode
    server.quiet = quiet
    
    print(f" * Running on http://{hostname}:{port}/")
    print(" * Press CTRL+C to quit")
    
    try:
        if threaded:
            # Run in threaded mode
            server_thread = threading.Thread(target=server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
            try:
                while True:
                    threading.Event().wait(1)
            except KeyboardInterrupt:
                pass
        else:
            server.serve_forever()
    except KeyboardInterrupt:
        print("\n * Shutting down...")
    finally:
        server.shutdown()
        server.server_close()
