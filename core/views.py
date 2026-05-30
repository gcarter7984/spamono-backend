from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.translation import gettext_lazy as _
from .models import User, Contact, SpamReport
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    ContactSerializer,
    SpamReportSerializer,
    SearchResultSerializer
)
from .services import SearchService, SpamReportService
from rest_framework.permissions import IsAuthenticated
from .permissions import IsOwnerOrReadOnly

class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserProfileSerializer(user).data
        }
        
        headers = self.get_success_headers(serializer.data)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)

class UserLoginView(APIView):
    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserProfileSerializer(user).data
        })

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user

class ContactListView(generics.ListCreateAPIView):
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Contact.objects.filter(owner=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class ContactDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field = 'id'
    
    def get_queryset(self):
        return Contact.objects.filter(owner=self.request.user)
    
class ReportSpamView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SpamReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            SpamReportService.report_spam(
                reporter=request.user,
                phone_number=serializer.validated_data['phone_number']
            )
            return Response(
                {'status': 'success', 'message': 'Number reported as spam'},
                status=status.HTTP_201_CREATED
            )
        except ValueError as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'status': 'error', 'message': 'Failed to report spam'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# In your views.py
class SearchByNameView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        
        if not query:
            return Response(
                {'error': 'Search query parameter "q" is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            results = SearchService.search_by_name(query, request.user)
            serializer = SearchResultSerializer(results, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SearchByPhoneView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        phone_number = request.query_params.get('phone', '').strip()
        if not phone_number:
            return Response(
                {'detail': _('Phone number is required.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        results = SearchService.search_by_phone(phone_number, request.user)
        serializer = SearchResultSerializer(results, many=True)
        return Response(serializer.data)