from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from core.permissions import tipos_de_conta_gerenciaveis
from ..models import CustomUser


class CustomUserSerializer(serializers.ModelSerializer):
    # A senha só entra pela API; nunca é devolvida, nem mesmo como hash.
    password = serializers.CharField(
        write_only=True,
        required=False,
        style={'input_type': 'password'},
    )

    class Meta:
        model = CustomUser
        # Lista explícita: novos campos do modelo não são expostos por acidente.
        # groups e user_permissions ficam de fora para não permitir escalar privilégios.
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'tipo',
            'is_active',
            'is_staff',
            'is_superuser',
            'last_login',
            'date_joined',
            'password',
        ]
        read_only_fields = ['is_staff', 'is_superuser', 'last_login', 'date_joined']

    def validate_tipo(self, value):
        request = self.context.get('request')
        tipos = tipos_de_conta_gerenciaveis(request.user) if request else None
        if tipos is not None and value not in tipos:
            raise serializers.ValidationError(
                'Você não tem permissão para atribuir este tipo de conta.'
            )
        return value

    def validate_email(self, value):
        # O email também serve de login, então não pode se repetir entre contas.
        email = (value or '').strip()
        if email:
            repetidos = CustomUser.objects.filter(email__iexact=email)
            if self.instance is not None:
                repetidos = repetidos.exclude(pk=self.instance.pk)
            if repetidos.exists():
                raise serializers.ValidationError('Já existe uma conta com este email.')
        return email

    def validate(self, attrs):
        password = attrs.get('password')
        if password is not None:
            # Aplica os AUTH_PASSWORD_VALIDATORS do settings.
            user = self.instance or CustomUser(
                **{k: v for k, v in attrs.items() if k != 'password'}
            )
            try:
                validate_password(password, user=user)
            except DjangoValidationError as exc:
                raise serializers.ValidationError({'password': list(exc.messages)})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = CustomUser(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save(update_fields=['password'])
        return user


class TrocarSenhaSerializer(serializers.Serializer):
    """Troca da própria senha: exige a senha atual e altera apenas a senha."""

    senha_atual = serializers.CharField(write_only=True, style={'input_type': 'password'})
    nova_senha = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate_senha_atual(self, value):
        if not self.context['request'].user.check_password(value):
            raise serializers.ValidationError('Senha atual incorreta.')
        return value

    def validate_nova_senha(self, value):
        try:
            validate_password(value, user=self.context['request'].user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['nova_senha'])
        user.save(update_fields=['password'])
        return user
