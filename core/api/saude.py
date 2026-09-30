from rest_framework.decorators import api_view, authentication_classes, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([])
def saude(request):
    """Verificação de disponibilidade (usada pelo provedor e para "acordar" o servidor gratuito)."""
    return Response({'status': 'ok'})
