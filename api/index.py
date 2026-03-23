from app import app

# Vercel serverless function handler
def handler(request):
    """
    Handle Vercel serverless requests for Flask app
    """
    # Get the request data
    method = request.method
    path = request.path
    headers = dict(request.headers)
    body = request.body

    # Create WSGI environ
    environ = {
        'REQUEST_METHOD': method,
        'PATH_INFO': path,
        'QUERY_STRING': request.query_string.decode('utf-8'),
        'CONTENT_TYPE': headers.get('content-type', ''),
        'CONTENT_LENGTH': str(len(body) if body else 0),
        'SERVER_NAME': 'vercel',
        'SERVER_PORT': '443',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'https',
        'wsgi.input': body,
        'wsgi.errors': None,
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
    }

    # Add headers
    for key, value in headers.items():
        environ[f'HTTP_{key.upper().replace("-", "_")}'] = value

    # Response collector
    response_data = []
    response_status = []
    response_headers = []

    def start_response(status, headers, exc_info=None):
        response_status.append(status)
        response_headers.extend(headers)

    # Call the Flask app
    result = app.wsgi_app(environ, start_response)

    # Collect response
    response_data.extend(result)

    # Return Vercel response format
    return {
        'statusCode': int(response_status[0].split()[0]),
        'headers': dict(response_headers),
        'body': b''.join(response_data).decode('utf-8')
    }