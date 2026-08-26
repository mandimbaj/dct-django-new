import os


class ForceHostMiddleware:
    """Force le host public quand la requête arrive via l'Application Gateway,
    qui réécrit le Host en af-aho-datacapturetool.azurewebsites.net."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.public_host = os.environ.get('PUBLIC_HOST', '')

    def __call__(self, request):
        if self.public_host and request.get_host().endswith('azurewebsites.net'):
            request.META['HTTP_HOST'] = self.public_host
            request.META['HTTP_X_FORWARDED_PROTO'] = 'https'
        return self.get_response(request)