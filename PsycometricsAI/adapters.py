from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # Conectar cuenta social a usuario existente con mismo email
        email = sociallogin.account.extra_data.get('email')
        if email:
            try:
                user = User.objects.get(email=email)
                sociallogin.connect(request, user)
            except User.DoesNotExist:
                pass

    def save_user(self, request, sociallogin, form=None):
        # Crear nuevo usuario desde cuenta social
        user = super().save_user(request, sociallogin, form)

        # Asignar datos del perfil
        extra_data = sociallogin.account.extra_data
        user.first_name = extra_data.get('given_name', '')
        user.last_name = extra_data.get('family_name', '')

        # Para LinkedIn
        if not user.first_name and 'firstName' in extra_data.get('localized', {}):
            user.first_name = extra_data['localized']['firstName']
        if not user.last_name and 'lastName' in extra_data.get('localized', {}):
            user.last_name = extra_data['localized']['lastName']

        user.save()
        return user