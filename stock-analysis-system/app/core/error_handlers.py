"""
Global Error Handlers
Centralized error handling for FastAPI application
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback
from typing import Union

from app.core.exceptions import (
    StockAnalysisException,
    DatabaseException,
    ExternalAPIException,
    AuthenticationException,
    AuthorizationException,
    ValidationException,
    BusinessLogicException,
    TaskException,
    AgentException,
    convert_to_http_exception
)
from app.core.logging import get_logger

logger = get_logger("error_handler")


def setup_error_handlers(app: FastAPI):
    """Setup global error handlers for the FastAPI application"""
    
    @app.exception_handler(StockAnalysisException)
    async def stock_analysis_exception_handler(request: Request, exc: StockAnalysisException):
        """Handle custom stock analysis exceptions"""
        logger.error(
            f"Stock Analysis Exception: {exc.message}",
            extra={
                "error_code": exc.error_code,
                "details": exc.details,
                "path": str(request.url),
                "method": request.method
            }
        )
        
        http_exc = convert_to_http_exception(exc)
        return JSONResponse(
            status_code=http_exc.status_code,
            content=http_exc.detail
        )
    
    @app.exception_handler(DatabaseException)
    async def database_exception_handler(request: Request, exc: DatabaseException):
        """Handle database exceptions"""
        logger.error(
            f"Database Exception: {exc.message}",
            extra={
                "error_code": exc.error_code,
                "details": exc.details,
                "path": str(request.url),
                "method": request.method
            }
        )
        
        return JSONResponse(
            status_code=503,
            content={
                "error_code": "DATABASE_ERROR",
                "message": "Database service temporarily unavailable",
                "details": {"original_error": exc.message}
            }
        )
    
    @app.exception_handler(ExternalAPIException)
    async def external_api_exception_handler(request: Request, exc: ExternalAPIException):
        """Handle external API exceptions"""
        logger.error(
            f"External API Exception: {exc.message}",
            extra={
                "error_code": exc.error_code,
                "api_name": exc.details.get("api_name", "unknown"),
                "details": exc.details,
                "path": str(request.url),
                "method": request.method
            }
        )
        
        return JSONResponse(
            status_code=502,
            content={
                "error_code": "EXTERNAL_API_ERROR",
                "message": "External service temporarily unavailable",
                "details": {
                    "api_name": exc.details.get("api_name", "unknown"),
                    "original_error": exc.message
                }
            }
        )
    
    @app.exception_handler(AuthenticationException)
    async def authentication_exception_handler(request: Request, exc: AuthenticationException):
        """Handle authentication exceptions"""
        logger.warning(
            f"Authentication Exception: {exc.message}",
            extra={
                "error_code": exc.error_code,
                "details": exc.details,
                "path": str(request.url),
                "method": request.method,
                "client_ip": request.client.host if request.client else None
            }
        )
        
        return JSONResponse(
            status_code=401,
            content={
                "error_code": "AUTHENTICATION_ERROR",
                "message": "Authentication failed",
                "details": {"original_error": exc.message}
            }
        )
    
    @app.exception_handler(AuthorizationException)
    async def authorization_exception_handler(request: Request, exc: AuthorizationException):
        """Handle authorization exceptions"""
        logger.warning(
            f"Authorization Exception: {exc.message}",
            extra={
                "error_code": exc.error_code,
                "details": exc.details,
                "path": str(request.url),
                "method": request.method,
                "client_ip": request.client.host if request.client else None
            }
        )
        
        return JSONResponse(
            status_code=403,
            content={
                "error_code": "AUTHORIZATION_ERROR",
                "message": "Access denied",
                "details": {"original_error": exc.message}
            }
        )
    
    @app.exception_handler(ValidationException)
    async def validation_exception_handler(request: Request, exc: ValidationException):
        """Handle validation exceptions"""
        logger.warning(
            f"Validation Exception: {exc.message}",
            extra={
                "error_code": exc.error_code,
                "field": exc.details.get("field"),
                "details": exc.details,
                "path": str(request.url),
                "method": request.method
            }
        )
        
        return JSONResponse(
            status_code=422,
            content={
                "error_code": "VALIDATION_ERROR",
                "message": "Invalid input data",
                "details": {
                    "field": exc.details.get("field"),
                    "original_error": exc.message
                }
            }
        )
    
    @app.exception_handler(BusinessLogicException)
    async def business_logic_exception_handler(request: Request, exc: BusinessLogicException):
        """Handle business logic exceptions"""
        logger.warning(
            f"Business Logic Exception: {exc.message}",
            extra={
                "error_code": exc.error_code,
                "operation": exc.details.get("operation"),
                "details": exc.details,
                "path": str(request.url),
                "method": request.method
            }
        )
        
        return JSONResponse(
            status_code=400,
            content={
                "error_code": "BUSINESS_LOGIC_ERROR",
                "message": "Business logic error",
                "details": {
                    "operation": exc.details.get("operation"),
                    "original_error": exc.message
                }
            }
        )
    
    @app.exception_handler(TaskException)
    async def task_exception_handler(request: Request, exc: TaskException):
        """Handle background task exceptions"""
        logger.error(
            f"Task Exception: {exc.message}",
            extra={
                "error_code": exc.error_code,
                "task_name": exc.details.get("task_name"),
                "details": exc.details,
                "path": str(request.url),
                "method": request.method
            }
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "TASK_ERROR",
                "message": "Background task failed",
                "details": {
                    "task_name": exc.details.get("task_name"),
                    "original_error": exc.message
                }
            }
        )
    
    @app.exception_handler(AgentException)
    async def agent_exception_handler(request: Request, exc: AgentException):
        """Handle AI agent exceptions"""
        logger.error(
            f"Agent Exception: {exc.message}",
            extra={
                "error_code": exc.error_code,
                "agent_name": exc.details.get("agent_name"),
                "details": exc.details,
                "path": str(request.url),
                "method": request.method
            }
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "AGENT_ERROR",
                "message": "AI agent processing failed",
                "details": {
                    "agent_name": exc.details.get("agent_name"),
                    "original_error": exc.message
                }
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        """Handle FastAPI validation errors"""
        logger.warning(
            f"Request Validation Error: {exc.errors()}",
            extra={
                "error_code": "REQUEST_VALIDATION_ERROR",
                "validation_errors": exc.errors(),
                "path": str(request.url),
                "method": request.method
            }
        )
        
        return JSONResponse(
            status_code=422,
            content={
                "error_code": "REQUEST_VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {
                    "validation_errors": exc.errors()
                }
            }
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions"""
        logger.warning(
            f"HTTP Exception: {exc.detail}",
            extra={
                "error_code": "HTTP_ERROR",
                "status_code": exc.status_code,
                "detail": exc.detail,
                "path": str(request.url),
                "method": request.method
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": "HTTP_ERROR",
                "message": exc.detail,
                "status_code": exc.status_code
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all other exceptions"""
        logger.error(
            f"Unhandled Exception: {str(exc)}",
            extra={
                "error_code": "UNHANDLED_ERROR",
                "exception_type": type(exc).__name__,
                "traceback": traceback.format_exc(),
                "path": str(request.url),
                "method": request.method
            }
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "UNHANDLED_ERROR",
                "message": "Internal server error",
                "details": {
                    "exception_type": type(exc).__name__,
                    "original_error": str(exc)
                }
            }
        )










