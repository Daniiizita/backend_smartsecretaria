from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class LoginOuEmailBackend(ModelBackend):
    """Autentica pelo login (username) ou, se não houver, pelo email.

    O login tem prioridade. O email é comparado sem diferenciar maiúsculas e
    só é aceito quando pertence a uma única conta.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        if username is None or password is None:
            return None

        identificador = username.strip()
        user = UserModel._default_manager.filter(username=identificador).first()
        if user is None and '@' in identificador:
            contas = list(UserModel._default_manager.filter(email__iexact=identificador)[:2])
            user = contas[0] if len(contas) == 1 else None

        if user is None:
            # Mesmo custo de hash de quando a conta existe: não revela quais logins existem.
            UserModel().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
