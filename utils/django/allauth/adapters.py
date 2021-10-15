# -*- coding: utf-8 -*-
import json
import uuid

from allauth.account import app_settings as account_settings
from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.adapter import get_adapter as get_account_adapter
from allauth.socialaccount import providers
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.providers.apple.views import AppleOAuth2Adapter as BaseAppleOAuth2Adapter
from allauth.socialaccount.providers.facebook.views import (
    FacebookProvider,
    FacebookOAuth2Adapter as BaseFacebookOAuth2Adapter,
    GRAPH_API_URL as FB_GRAPH_API_URL,
    compute_appsecret_proof as fb_compute_appsecret_proof,
)
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter as BaseGoogleOAuth2Adapter
from allauth.socialaccount.providers.kakao.views import KakaoOAuth2Adapter as BaseKakaoOAuth2Adapter
from allauth.socialaccount.providers.naver.views import NaverOAuth2Adapter as BaseNaverOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Error
from allauth.utils import get_user_model
from django import forms
from django.db import transaction
from django.utils.translation import gettext as _

from utils.django.allauth.mixins import SessionAdapterMixin
from utils.text import get_random_tag


class AccountAdapter(DefaultAccountAdapter):
    def clean_username(self, username, shallow=False):
        """
        Validates the username. You can hook into this if you want to
        (dynamically) restrict what usernames can be chosen.
        """
        for validator in account_settings.USERNAME_VALIDATORS:
            validator(username)

        # TODO: Add regexp support to USERNAME_BLACKLIST
        username_blacklist_lower = [ub.lower()
                                    for ub in account_settings.USERNAME_BLACKLIST]
        if username.lower() in username_blacklist_lower:
            raise forms.ValidationError(
                self.error_messages['username_blacklisted'])
        return username


class SocialAccountAdapter(DefaultSocialAccountAdapter):

    def populate_user(self,
                      request,
                      sociallogin,
                      data):
        super(SocialAccountAdapter, self).populate_user(request, sociallogin, data)
        user = sociallogin.user
        account = sociallogin.account
        user.username = f'chatie_{str(uuid.uuid4()).replace("-", "")}'
        return user

    def save_user(self, request, sociallogin, form=None):
        """
        Saves a newly signed up social login. In case of auto-signup,
        the signup form is not available.
        """
        user = sociallogin.user
        if not user.nickname:
            user_cls = get_user_model()
            while True:
                user.nickname = f'{_("유저")}#{get_random_tag(5)}'
                if not user_cls.objects.filter(nickname=user.nickname).exists():
                    break

        # TODO: Remove Legacy (transaction, is_registration)
        with transaction.atomic():
            user.set_unusable_password()
            if form:
                get_account_adapter().save_user(request, user, form)
            else:
                get_account_adapter().populate_username(request, user)
            sociallogin.connect(request, user)
            user.is_registration = True
            return user


class KakaoOAuth2Adapter(SessionAdapterMixin, BaseKakaoOAuth2Adapter):

    def complete_login(self, request, app, token, **kwargs):
        session = self.get_session()
        headers = {'Authorization': 'Bearer {0}'.format(token.token)}
        resp = session.get(self.profile_url, headers=headers)
        resp.raise_for_status()
        extra_data = resp.json()
        return self.get_provider().sociallogin_from_response(request,
                                                             extra_data)


class NaverOAuth2Adapter(SessionAdapterMixin, BaseNaverOAuth2Adapter):

    def complete_login(self, request, app, token, **kwargs):
        session = self.get_session()
        headers = {'Authorization': 'Bearer {0}'.format(token.token)}
        resp = session.get(self.profile_url, headers=headers)
        resp.raise_for_status()
        extra_data = resp.json().get('response')
        return self.get_provider().sociallogin_from_response(request,
                                                             extra_data)


class FacebookOAuth2Adapter(SessionAdapterMixin, BaseFacebookOAuth2Adapter):

    def complete_login(self, request, app, access_token, **kwargs):
        session = self.get_session()
        provider = providers.registry.by_id(FacebookProvider.id, request)
        resp = session.get(
            FB_GRAPH_API_URL + '/me',
            params={
                'fields': ','.join(provider.get_fields()),
                'access_token': access_token.token,
                'appsecret_proof': fb_compute_appsecret_proof(app, access_token)
            })
        resp.raise_for_status()
        extra_data = resp.json()
        return provider.sociallogin_from_response(request, extra_data)


class GoogleOAuth2Adapter(SessionAdapterMixin, BaseGoogleOAuth2Adapter):

    def complete_login(self, request, app, token, **kwargs):
        session = self.get_session()
        resp = session.get(self.profile_url,
                           params={'access_token': token.token,
                                   'alt': 'json'})
        resp.raise_for_status()
        extra_data = resp.json()
        login = self.get_provider().sociallogin_from_response(request, extra_data)
        return login


class AppleOAuth2Adapter(SessionAdapterMixin, BaseAppleOAuth2Adapter):

    def _get_apple_public_key(self, kid):
        session = self.get_session()
        response = session.get(self.public_key_url)
        response.raise_for_status()
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            raise OAuth2Error("Error retrieving apple public key.") from e

        for d in data["keys"]:
            if d["kid"] == kid:
                return d
