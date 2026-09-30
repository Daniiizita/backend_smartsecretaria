from django.conf import settings
from rest_framework.throttling import SimpleRateThrottle


class LoginRateThrottle(SimpleRateThrottle):
    """Limita tentativas de login (e troca de senha) por IP, contra força bruta.

    A taxa vem de settings.LOGIN_THROTTLE_RATE (variável LOGIN_THROTTLE_RATE),
    lida a cada requisição para poder ser ajustada por ambiente.
    """

    scope = 'login'

    def get_rate(self):
        return getattr(settings, 'LOGIN_THROTTLE_RATE', '10/min')

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}
