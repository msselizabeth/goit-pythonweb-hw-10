import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from app.db.db_connection import session_manager
from app.api.contacts import router as contacts_router
from app.api.auth import router as auth_router
from app.api.users import router as users_router, limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown.

    Closes the database session manager when the app shuts down.

    :param app: The FastAPI application instance.
    """
    yield
    await session_manager.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(contacts_router, prefix="/api")

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Add an X-Process-Time header showing how long the request took.

    :param request: Incoming HTTP request.
    :param call_next: The next handler in the middleware chain.
    :return: The response, with the processing time header added.
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Format HTTPException responses as a consistent error JSON shape.

    :param request: Incoming HTTP request.
    :param exc: The raised HTTPException.
    :return: A JSON response with error details.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status": exc.status_code},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Format request validation errors as a consistent error JSON shape.

    :param request: Incoming HTTP request.
    :param exc: The raised validation error.
    :return: A JSON response with validation error details.
    """
    return JSONResponse(
        status_code=422,
        content={"error": "Validation error", "details": exc.errors()},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all handler for unhandled exceptions.

    :param request: Incoming HTTP request.
    :param exc: The unhandled exception.
    :return: A generic 500 error response.
    """
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )


@app.get("/api/health")
async def healthcheck():
    """
    Simple healthcheck endpoint.

    :return: A status message confirming the API is running.
    """
    return {"status": "ok"}