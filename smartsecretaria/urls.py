"""
URL configuration for smartsecretaria project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from core.throttling import LoginRateThrottle
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [

    path('admin/', admin.site.urls),

    #API Token
    path('api/token/', TokenObtainPairView.as_view(throttle_classes=[LoginRateThrottle]), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Logout: invalida o refresh token informado.
    path('api/token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),


    #API Routes
    path('api/aluno/', include('aluno.api.urls')),
    path('api/calendario/', include('calendario.api.urls')),
    path('api/documentos/', include('documentos.api.urls')),
    path('api/logs/', include('logs.api.urls')),
    path('api/matricula/', include('matricula.api.urls')),
    path('api/notificacoes/', include('notificacoes.api.urls')),
    path('api/permissoes/', include('permissoes.api.urls')),
    path('api/professor/', include('professor.api.urls')),
    path('api/turma/', include('turma.api.urls')),
    path('api/usuarios/', include('usuarios.api.urls')),
    path('api/dashboard/', include('core.api.urls')),
    path('api/disciplina/', include('disciplina.api.urls')),
    

    #API Documentacao
    path('api-auth/', include('rest_framework.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)








