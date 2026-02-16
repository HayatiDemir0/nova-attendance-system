"""
Admin Ayrı Session Middleware
=============================
Django admin (/admin/) için farklı bir session cookie kullanır.
Bu sayede aynı tarayıcıda:
  - /admin/ → 'yoklama_admin_sessionid' cookie'si
  - Diğer sayfalar → 'yoklama_sessionid' cookie'si (settings'teki SESSION_COOKIE_NAME)

İki ayrı oturum paralel çalışır, birbirini ezmez.
"""

from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware


ADMIN_SESSION_COOKIE = 'yoklama_admin_sessionid'


class AdminSessionMiddleware(SessionMiddleware):
    """
    /admin/ path'i için ayrı session cookie kullanan middleware.
    Normal SessionMiddleware'in yerine geçer.
    """

    def _is_admin_path(self, path):
        """URL /admin/ ile başlıyorsa True döner"""
        return path.startswith('/admin/')

    def process_request(self, request):
        # Admin path'i ise cookie adını geçici olarak değiştir
        if self._is_admin_path(request.path):
            original_cookie_name = settings.SESSION_COOKIE_NAME
            settings.SESSION_COOKIE_NAME = ADMIN_SESSION_COOKIE
            super().process_request(request)
            settings.SESSION_COOKIE_NAME = original_cookie_name
        else:
            super().process_request(request)

    def process_response(self, request, response):
        if self._is_admin_path(request.path):
            original_cookie_name = settings.SESSION_COOKIE_NAME
            settings.SESSION_COOKIE_NAME = ADMIN_SESSION_COOKIE
            response = super().process_response(request, response)
            settings.SESSION_COOKIE_NAME = original_cookie_name
        else:
            response = super().process_response(request, response)
        return response