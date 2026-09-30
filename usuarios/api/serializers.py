from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
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
