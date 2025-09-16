from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
import time
from typing import Callable

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Custom error handling middleware"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Log successful requests
            process_time = time.time() - start_time
            logger.info(
                f"{request.method} {request.url} - "
                f"Status: {response.status_code} - "
                f"Duration: {process_time:.2f}s"
            )
            
            return response
            
        except HTTPException as e:
            # Log HTTP exceptions
            process_time = time.time() - start_time
            logger.warning(
                f"{request.method} {request.url} - "
                f"HTTP Error {e.status_code}: {e.detail} - "
                f"Duration: {process_time:.2f}s"
            )
            
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": True,
                    "message": e.detail,
                    "status_code": e.status_code,
                    "path": str(request.url)
                }
            )
            
        except RequestValidationError as e:
            # Log validation errors
            process_time = time.time() - start_time
            logger.warning(
                f"{request.method} {request.url} - "
                f"Validation Error: {str(e)} - "
                f"Duration: {process_time:.2f}s"
            )
            
            return JSONResponse(
                status_code=422,
                content={
                    "error": True,
                    "message": "Validation error",
                    "details": e.errors(),
                    "status_code": 422,
                    "path": str(request.url)
                }
            )
            
        except Exception as e:
            # Log unexpected errors
            process_time = time.time() - start_time
            logger.error(
                f"{request.method} {request.url} - "
                f"Unexpected Error: {str(e)} - "
                f"Duration: {process_time:.2f}s",
                exc_info=True
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": True,
                    "message": "Internal server error",
                    "status_code": 500,
                    "path": str(request.url)
                }
            )