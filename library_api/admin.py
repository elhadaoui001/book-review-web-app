# follow prompts for username/email/password
from django.contrib import admin
from .models import Book, LibraryUser, Transaction

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title','author','isbn','copies_available','published_date')
    search_fields = ('title','author','isbn')

@admin.register(LibraryUser)
class LibraryUserAdmin(admin.ModelAdmin):
    list_display = ('user','date_of_membership','is_active_member')
    search_fields = ('user__username','user__email')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('book','user','status','checkout_date','return_date')
    list_filter = ('status',)
    search_fields = ('book__title','user__user__username')
