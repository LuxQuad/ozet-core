# -*- coding:utf-8 -*-
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Tuple, Optional, Union, Callable, Iterable, List

import safedelete.config as sd_config
import sentry_sdk
from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction, connections
from django.db.models import Max, Q, F, Count
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import ugettext, gettext_lazy as _

from user.managers import UserManager
from utils.django.models import TimeStampedModel, SafeDeleteModel


class User(AbstractBaseUser, SafeDeleteModel, TimeStampedModel):
    username = models.CharField(
        max_length=200,
        null=True,
        blank=False,
        db_index=True,
        unique=True,
        verbose_name=_('아이디')
    )
    email = models.EmailField(
        max_length=250,
        null=True,
        blank=False,
        db_index=True,
        verbose_name=_('이메일')
    )
    nickname = models.CharField(
        max_length=20,
        null=True,
        blank=False,
        db_index=True,
        unique=True,
        verbose_name=_('닉네임')
    )
    is_active = models.BooleanField(
        null=False,
        blank=False,
        default=True,
        verbose_name=_('활성화')
    )
    is_admin = models.BooleanField(
        null=False,
        blank=False,
        default=False,
        verbose_name=_('어드민')
    )

    objects = UserManager()

    USERNAME_FIELD = 'username'

    REQUIRED_FIELDS = ['nickname']

    class Meta:
        verbose_name = _('회원')
        verbose_name_plural = _('회원 목록')

        indexes = [
            models.Index(fields=['deleted', 'is_active']),
        ]

        db_table = 'account_user'

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f'<{self._meta.verbose_name.title()}: {self.nickname}>'

    @property
    def is_staff(self):
        return self.is_admin

    def get_full_name(self):
        return self.nickname

    def get_short_name(self):
        return self.nickname

    # noinspection PyMethodMayBeStatic
    def has_perm(self, perm, obj=None):
        return True

    # noinspection PyMethodMayBeStatic
    def has_module_perms(self, app_label):
        return True


class UserToken(TimeStampedModel):
    user = models.ForeignKey(
        User,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name='token_set',
        verbose_name=_('회원'),
    )
    token = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        verbose_name=_('토큰'),
        unique=True,
    )
    user_agent = models.TextField(
        null=True,
        blank=False,
        verbose_name=_('Agent'),
    )
    user_ip = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_('IP'),
    )

    class Meta:
        verbose_name = _('회원 토큰')
        verbose_name_plural = _('회원 토큰 목록')

        db_table = 'account_user_token'
