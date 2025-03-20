from functools import wraps
from flask import request, current_app
from debug_config import log_error, log_info
import time

def debug_route(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        request_id = request.headers.get('X-Request-ID', 'unknown')
        
        log_info(f"Route called: {request.path}", {
            "method": request.method,
            "request_id": request_id,
            "args": request.args,
            "headers": dict(request.headers)
        })

        try:
            result = f(*args, **kwargs)
            execution_time = time.time() - start_time
            
            log_info(f"Route completed: {request.path}", {
                "execution_time": execution_time,
                "request_id": request_id
            })
            
            return result
        except Exception as e:
            log_error(e, {
                "route": request.path,
                "request_id": request_id,
                "method": request.method
            })
            raise

    return decorated_function 