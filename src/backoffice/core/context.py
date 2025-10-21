import contextvars

request_id_ctx_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default="-"
)
user_id_ctx_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "user_id", default="-"
)
