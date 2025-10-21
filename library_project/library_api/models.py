from django.conf import settings
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Book(models.Model):
    title = models.CharField(max_length=300)
    author = models.CharField(max_length=200)
    isbn = models.CharField(max_length=20, unique=True)
    published_date = models.DateField(null=True, blank=True)
    copies_available = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} — {self.author}"

class LibraryUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='library_profile')
    date_of_membership = models.DateField(default=timezone.now)
    is_active_member = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username

class Transaction(models.Model):
    CHECKED_OUT = 'OUT'
    RETURNED = 'RETURNED'

    STATUS_CHOICES = [
        (CHECKED_OUT, 'Checked Out'),
        (RETURNED, 'Returned'),
    ]

    user = models.ForeignKey(LibraryUser, on_delete=models.CASCADE, related_name='transactions')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='transactions')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=CHECKED_OUT)
    checkout_date = models.DateTimeField(default=timezone.now)
    return_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        # There can be many records over time; business logic will prevent duplicate active OUT records.
        indexes = [
            models.Index(fields=['user','book','status']),
        ]

    def __str__(self):
        return f"{self.book.title} - {self.user.user.username} ({self.status})"
