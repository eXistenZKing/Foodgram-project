from django.http import HttpResponseForbidden


class IPRestrictMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Получение IP-адреса клиента
        client_ip = request.META['REMOTE_ADDR']
        allowed_ips = ['195.181.175.175']

        if client_ip not in allowed_ips:
            return HttpResponseForbidden('Доступ запрещен')

        response = self.get_response(request)
        return response
