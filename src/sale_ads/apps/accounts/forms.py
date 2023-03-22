import allauth.account.forms
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.core.validators import MinLengthValidator


class SignupForm(allauth.account.forms.SignupForm):
    name = get_user_model()._meta.get_field("name").formfield()


class UserSettingsForm(forms.ModelForm):
    username_field = get_user_model()._meta.get_field("username")
    (username_min_length_validator,) = filter(
        lambda validator: isinstance(validator, MinLengthValidator),
        username_field.validators,
    )
    username = username_field.formfield(
        min_length=username_min_length_validator.limit_value
    )
    del username_field, username_min_length_validator

    class Meta:
        fields = ("name", "username", "email")
        model = get_user_model()


class UserEmailForm(forms.ModelForm):
    class Meta:
        fields = ("email",)
        model = get_user_model()


class UserPhotoForm(forms.ModelForm):
    photo = get_user_model()._meta.get_field("photo").formfield()

    class Meta:
        fields = ("photo",)
        model = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = get_user_model()


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = get_user_model()
