from collections import Counter

from django.db.models import ProtectedError, RestrictedError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """Transforma exclusões bloqueadas por PROTECT em 409 com mensagem clara."""
    if isinstance(exc, (ProtectedError, RestrictedError)):
        objetos = exc.protected_objects if isinstance(exc, ProtectedError) else exc.restricted_objects
        contagem = Counter(str(obj._meta.verbose_name_plural) for obj in objetos)
        vinculos = ', '.join(f'{total} {nome}' for nome, total in sorted(contagem.items()))
        return Response(
            {
                'detail': (
                    'Não é possível excluir: existem registros vinculados '
                    f'({vinculos}). Remova ou transfira esses vínculos antes.'
                ),
                'vinculos': dict(contagem),
            },
            status=status.HTTP_409_CONFLICT,
        )
    return exception_handler(exc, context)
