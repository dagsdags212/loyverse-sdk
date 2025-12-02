class APIError(Exception):
    def __init__(self, status_code: int, payload) -> None:
        self.status_code = status_code
        self.payload = payload
        super().__init__(f"Loyverse API Error {status_code}: {payload}")
