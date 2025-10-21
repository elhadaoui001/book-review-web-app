# library_api/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import LibraryUser

@receiver(post_save, sender=User)
def create_library_profile(sender, instance, created, **kwargs):
    if created:
        LibraryUser.objects.create(user=instance)
