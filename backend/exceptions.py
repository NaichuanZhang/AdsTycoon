"""Custom exceptions for the Bid Exchange API."""

from fastapi import Request
from fastapi.responses import JSONResponse


class BidExchangeError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(BidExchangeError):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(f"{resource} '{resource_id}' not found", status_code=404)


class ConflictError(BidExchangeError):
    def __init__(self, message: str):
        super().__init__(message, status_code=409)


class ValidationError(BidExchangeError):
    def __init__(self, message: str):
        super().__init__(message, status_code=422)


async def bid_exchange_error_handler(request: Request, exc: BidExchangeError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )
