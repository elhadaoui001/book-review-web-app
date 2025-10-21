from rest_framework import routers
from django.urls import path, include
from .views import BookViewSet, LibraryUserViewSet, TransactionViewSet

router = routers.DefaultRouter()
router.register(r'books', BookViewSet, basename='book')
router.register(r'users', LibraryUserViewSet, basename='libraryuser')
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),
]
