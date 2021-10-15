# -*- coding: utf-8 -*-
import copy

from django.db import models
from model_utils.models import TimeStampedModel as BaseTimeStampedModel
from safedelete.models import SafeDeleteModel as BaseSafeDeleteModel


class TimeStampedModel(BaseTimeStampedModel):

    def save(self, *args, **kwargs):
        # Created
        if not self.id:
            return super(TimeStampedModel, self).save(*args, **kwargs)

        if 'update_fields' not in kwargs:
            return super(TimeStampedModel, self).save(*args, **kwargs)

        if not kwargs['update_fields']:
            return super(TimeStampedModel, self).save(*args, **kwargs)

        new_kwargs = copy.deepcopy(kwargs)
        if isinstance(new_kwargs['update_fields'], tuple):
            new_kwargs['update_fields'] = list(new_kwargs['update_fields'])
        new_kwargs['update_fields'].append('modified')
        return super(TimeStampedModel, self).save(*args, **new_kwargs)

    class Meta:
        abstract = True


class SafeDeleteModel(BaseSafeDeleteModel):
    deleted = models.DateTimeField(
        editable=False,
        null=True,
        blank=True,
        default=None,
    )

    class Meta:
        abstract = True

    @property
    def is_deleted(self):
        return self.deleted is not None
