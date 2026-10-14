
class Response:
    def __init__(self, body='', status=200, headers=None):
        self.body = body
        self.status = f"{status} {self._status_text(status)}"
        self.headers = headers or []

    def _status_text(self, status):
        return {
            200: 'OK',
            404: 'Not Found',
        }.get(status, 'Unknown Status')