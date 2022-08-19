from django.db import models


class CreatedModel(models.Model):
    """Абстрактная модель, добавляет дату"""
    pub_date = models.DateTimeField(
        'Дата создания',
        auto_now_add=True,
    )

    class Meta:
        """"Это абстрактная модель"""
        abstract = True
        ordering = ('-pub_date',)
