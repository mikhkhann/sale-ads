from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

from unique_sequence_searchers import find_unique_string


class AccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form):
        user.name = form.cleaned_data["name"]
        return super().save_user(request, user, form)

    def populate_username(self, request, user):
        user_model = get_user_model()
        user.username = find_unique_string(
            user_model.USERNAME_GENERATION_CHARACTERS,
            user_model.USERNAME_GENERATION_LENGTH,
            [],
            check=self._GeneratedUsernameChecker(user),
        )

    class _GeneratedUsernameChecker:
        def __init__(self, user):
            self._user = user

        def __call__(self, username):
            previous_username = self._user.username
            try:
                self._user.username = username
                return self._user.is_generated_username_valid()
            finally:
                self._user.username = previous_username


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        user.name = data["first_name"]
        return user
