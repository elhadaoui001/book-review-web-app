from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction as db_transaction
from django.db.models import F

from .models import Book, LibraryUser, Transaction
from .serializers import (
    BookSerializer,
    LibraryUserSerializer,
    TransactionSerializer,
    CheckoutSerializer,
    ReturnSerializer,
)
from .permissions import IsAdminOrReadOnly

class BookViewSet(viewsets.ModelViewSet):
    """
    CRUD for books. Filtering by availability, title, author, isbn via query params.
    """
    queryset = Book.objects.all().order_by('title')
    serializer_class = BookSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        available = self.request.query_params.get('available')
        title = self.request.query_params.get('title')
        author = self.request.query_params.get('author')
        isbn = self.request.query_params.get('isbn')

        if available is not None:
            if available.lower() in ['1', 'true', 'yes']:
                qs = qs.filter(copies_available__gt=0)
            else:
                qs = qs.filter(copies_available__lte=0)

        if title:
            qs = qs.filter(title__icontains=title)
        if author:
            qs = qs.filter(author__icontains=author)
        if isbn:
            qs = qs.filter(isbn__icontains=isbn)

        return qs

class LibraryUserViewSet(viewsets.ModelViewSet):
    """
    Admin-only CRUD for library user profiles.
    """
    queryset = LibraryUser.objects.select_related('user').all()
    serializer_class = LibraryUserSerializer
    permission_classes = [IsAdminOrReadOnly]

class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only list of transactions. Includes custom actions for checkout and return.
    """
    queryset = Transaction.objects.select_related('user', 'book').all().order_by('-checkout_date')
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # staff sees all; normal users see their own transactions
        user = self.request.user
        if user.is_staff:
            return super().get_queryset()
        try:
            profile = user.library_profile
        except LibraryUser.DoesNotExist:
            return Transaction.objects.none()
        return self.queryset.filter(user=profile)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def checkout(self, request):
        """
        POST /api/transactions/checkout/  { "book_id": <id> }
        Authenticated user checks out a book.
        """
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        book_id = serializer.validated_data['book_id']

        # get the library profile of the current user
        try:
            lib_profile = request.user.library_profile
        except LibraryUser.DoesNotExist:
            return Response({'detail': 'Library profile not found.'}, status=status.HTTP_400_BAD_REQUEST)

        with db_transaction.atomic():
            # lock the selected book row
            book = get_object_or_404(Book.objects.select_for_update(), id=book_id)

            if book.copies_available <= 0:
                return Response({'detail': 'No copies available.'}, status=status.HTTP_400_BAD_REQUEST)

            # Ensure the user does not already have an active checkout for this book
            already = Transaction.objects.filter(user=lib_profile, book=book, status=Transaction.CHECKED_OUT).exists()
            if already:
                return Response({'detail': 'You already have this book checked out.'}, status=status.HTTP_400_BAD_REQUEST)

            # Create transaction
            txn = Transaction.objects.create(user=lib_profile, book=book, status=Transaction.CHECKED_OUT, checkout_date=timezone.now())

            # Decrement copies atomically
            Book.objects.filter(id=book.id).update(copies_available=F('copies_available') - 1)

            # Refresh txn and book for response
            txn.refresh_from_db()
            book.refresh_from_db()

        return Response(TransactionSerializer(txn).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated], url_path='return')
    def return_book(self, request):
        """
        POST /api/transactions/return/  { "transaction_id": <id> }
        Return a checked-out book. Only the borrower or staff can return.
        """
        serializer = ReturnSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        txn_id = serializer.validated_data['transaction_id']

        with db_transaction.atomic():
            txn = get_object_or_404(Transaction.objects.select_for_update(), id=txn_id)

            if txn.status != Transaction.CHECKED_OUT:
                return Response({'detail': 'This transaction is not an active checkout.'}, status=status.HTTP_400_BAD_REQUEST)

            # Check permission: borrower or staff
            if not (request.user.is_staff or txn.user.user == request.user):
                return Response({'detail': 'You do not have permission to return this book.'}, status=status.HTTP_403_FORBIDDEN)

            # mark returned
            txn.status = Transaction.RETURNED
            txn.return_date = timezone.now()
            txn.save(update_fields=['status', 'return_date'])

            # increment the book copies
            Book.objects.filter(id=txn.book.id).update(copies_available=F('copies_available') + 1)

            txn.refresh_from_db()
            txn.book.refresh_from_db()

        return Response(TransactionSerializer(txn).data, status=status.HTTP_200_OK)

