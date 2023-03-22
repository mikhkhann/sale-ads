from copy import deepcopy
from functools import cached_property
from types import MappingProxyType

from allauth.account.utils import has_verified_email, send_email_confirmation
from allauth.account.views import LogoutView
from django.conf import settings as project_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.generic import RedirectView, UpdateView

from accounts.forms import UserEmailForm, UserPhotoForm, UserSettingsForm


class _UserSettingsView(LoginRequiredMixin, UpdateView):
    form_class = UserSettingsForm
    template_name = "accounts/settings.html"

    def get(self, request, *args, **kwargs):
        self._object = request.user
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self._object = deepcopy(request.user)
        self.object = self.get_object()
        return self._perform_post_action(request.POST["action"])

    def _perform_post_action(self, action):
        method = self._POST_ACTION_METHODS[action]
        return method(self)

    def _save(self):
        form = self.get_form()
        form.full_clean()

        # Save data if valid & new
        # User
        for field in form.errors:
            setattr(self.object, field, form.initial[field])
        self.object.save(
            update_fields=form.cleaned_data.keys() & set(form.changed_data)
        )
        # Email
        if "email" in form.cleaned_data and self.object.email != form.initial["email"]:
            self._email_object.email = self.object.email
            self._email_object.verified = False
            self._email_object.save(update_fields=["email", "verified"])

        # Send verification if valid & new
        if "email" in form.cleaned_data and self.object.email != form.initial["email"]:
            send_email_confirmation(self.request, self.object, email=self.object.email)
            verification_sent = True
        else:
            verification_sent = False

        # Update request user
        for field in form.cleaned_data.keys() & set(form.changed_data):
            setattr(self.request.user, field, getattr(self.object, field))

        # Respond
        context = self.get_context_data(form=form, verification_sent=verification_sent)
        return self.render_to_response(context)

    def _send_email_verification(self):
        email_form = self.get_form(UserEmailForm)

        # Save data if valid & new
        if email_form.is_valid() and email_form.has_changed():
            # User
            self.object.save(update_fields=["email"])
            # Email
            self._email_object.email = self.object.email
            self._email_object.verified = False
            self._email_object.save(update_fields=["email", "verified"])

        # Send verification if valid & not verified
        email_is_valid = email_form.is_valid()
        if email_is_valid and not has_verified_email(self.object, self.object.email):
            send_email_confirmation(self.request, self.object, email=self.object.email)
            verification_sent = True
        else:
            verification_sent = False

        # Update request user
        if email_form.is_valid() and email_form.has_changed():
            self.request.user.email = self.object.email

        # Respond
        output_form_data = {}
        if "email" in self.request.POST:
            output_form_data["email"] = self.request.POST["email"]
        for name in self.get_form_class()().fields.keys() - {"email"}:
            output_form_data[name] = getattr(self.object, name)
        output_form_kwargs = self.get_form_kwargs() | {"data": output_form_data}
        output_form = self.get_form_class()(**output_form_kwargs)
        context = self.get_context_data(
            form=output_form, verification_sent=verification_sent
        )
        return self.render_to_response(context)

    _POST_ACTION_METHODS = MappingProxyType(
        {"save": _save, "send_email_verification": _send_email_verification}
    )

    def get_object(self, queryset=None):
        return self._object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["domain"] = project_settings.DOMAIN
        context["email_verified"] = self._email_object.verified
        user_model = get_user_model()
        context["min_username_length"] = user_model.MIN_USERNAME_LENGTH
        username_field = user_model._meta.get_field("username")
        context["max_username_length"] = username_field.max_length
        user_ad_list_url_path = reverse(
            "ads_user_list", kwargs={"username": self.object.username}
        )
        context["user_ad_list_url_path"] = user_ad_list_url_path.rstrip("/")
        return context

    @cached_property
    def _email_object(self):
        return self.object.emailaddress_set.get()


settings = _UserSettingsView.as_view()


class _UpdateUserPhotoView(LoginRequiredMixin, UpdateView):
    form_class = UserPhotoForm
    template_name = "accounts/settings_photo.html"

    def get(self, request, *args, **kwargs):
        self._object = request.user
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self._object = deepcopy(request.user)
        return super().post(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return self._object

    def form_valid(self, form):
        self.object.save(update_fields=["photo"])
        self.request.user.photo = self.object.photo
        context = self.get_context_data(form=form)
        return self.render_to_response(context)


update_photo = _UpdateUserPhotoView.as_view()


class _LogoutView(LogoutView):
    http_method_names = ("post",)


logout = _LogoutView.as_view()


email = RedirectView.as_view(pattern_name="accounts_settings")


email_verification_sent = RedirectView.as_view(url=project_settings.HOME_URL)
