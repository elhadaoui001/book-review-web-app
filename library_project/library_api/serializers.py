from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Book, LibraryUser, Transaction

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'isbn', 'published_date', 'copies_available', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class LibraryUserSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = LibraryUser
        fields = ['id', 'user', 'date_of_membership', 'is_active_member']

class TransactionSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)  # will be the library profile id
    book = BookSerializer(read_only=True)

    class Meta:
        model = Transaction
        fields = ['id', 'user', 'book', 'status', 'checkout_date', 'return_date']

# Simple serializers for actions
class CheckoutSerializer(serializers.Serializer):
    book_id = serializers.IntegerField()

class ReturnSerializer(serializers.Serializer):
    transaction_id = serializers.IntegerField()

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Book, LibraryUser, Transaction

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'isbn', 'published_date', 'copies_available']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class LibraryUserSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = LibraryUser
        fields = ['id', 'user', 'date_of_membership', 'is_active_member']


class TransactionSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)
    user = LibraryUserSerializer(read_only=True)

    class Meta:
        model = Transaction
        fields = ['id', 'book', 'user', 'status', 'checkout_date', 'return_date']


class CheckoutSerializer(serializers.Serializer):
    book_id = serializers.IntegerField()


class ReturnSerializer(serializers.Serializer):
    transaction_id = serializers.IntegerField()
