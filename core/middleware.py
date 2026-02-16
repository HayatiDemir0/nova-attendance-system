class AdminSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin'):
            request.session.cookie_name = 'admin_sessionid'
        else:
            request.session.cookie_name = 'sessionid'
        response = self.get_response(request)
        return response
