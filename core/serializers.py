from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from .models import User, Contact, SpamReport
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        min_length=8,
        max_length=128,
        help_text=_('At least 8 characters')
    )
    password_confirmation = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        min_length=8,
        max_length=128
    )
    
    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'phone_number',
            'email',
            'password',
            'password_confirmation'
        )
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'phone_number': {'required': True},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirmation']:
            raise serializers.ValidationError(
                {'password_confirmation': _('Passwords do not match.')}
            )
        return attrs
    
    def validate_phone_number(self, value):
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError(
                _('A user with this phone number already exists.')
            )
        return value
    
    def validate_email(self, value):
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                _('A user with this email already exists.')
            )
        if value:
            try:
                validate_email(value)
            except ValidationError:
                raise serializers.ValidationError(
                    _('Enter a valid email address.')
                )
        return value
    
    def create(self, validated_data):
        validated_data.pop('password_confirmation')
        user = User.objects.create_user(**validated_data)
        return user

class UserLoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(
        required=True,
        help_text=_('Registered phone number')
    )
    password = serializers.CharField(
        required=True,
        style={'input_type': 'password'},
        trim_whitespace=False,
        help_text=_('Your account password')
    )
    
    def validate(self, attrs):
        phone_number = attrs.get('phone_number')
        password = attrs.get('password')
        
        if phone_number and password:
            user = authenticate(
                request=self.context.get('request'),
                phone_number=phone_number,
                password=password
            )
            
            if not user:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = _('Must include "phone_number" and "password".')
            raise serializers.ValidationError(msg, code='authorization')
            
        attrs['user'] = user
        return attrs

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'phone_number',
            'email',
            'date_joined'
        )
        read_only_fields = ('phone_number', 'date_joined')

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = (
            'id',
            'name',
            'phone_number',
            'email',
            'created_at',
            'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def validate_phone_number(self, value):
        user = self.context['request'].user
        if Contact.objects.filter(owner=user, phone_number=value).exists():
            raise serializers.ValidationError(
                _('You already have a contact with this phone number.')
            )
        return value

class SpamReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpamReport
        fields = ('phone_number',)
        
    def validate_phone_number(self, value):
        # Basic phone number validation
        if not value or not value.isdigit():
            raise serializers.ValidationError("Phone number must contain only digits")
        if len(value) < 10:
            raise serializers.ValidationError("Phone number too short")
        return value

class SearchResultSerializer(serializers.Serializer):
    id = serializers.CharField(required=False, allow_null=True)
    name = serializers.CharField(required=False, allow_null=True)
    phone_number = serializers.CharField()
    spam_likelihood = serializers.FloatField(min_value=0, max_value=1)
    is_registered = serializers.BooleanField()
    is_unknown = serializers.BooleanField(required=False, default=False)
    email = serializers.EmailField(
        required=False,
        allow_null=True,
        # Only show email if both registered AND in contacts
        read_only=True
    )