class AppError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class BlueskyFetchError(AppError):
    def __init__(self, message: str, status_code: int = 422):
        super().__init__(message, status_code)


class SearchError(AppError):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message, status_code)


class SynthesisError(AppError):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message, status_code)
