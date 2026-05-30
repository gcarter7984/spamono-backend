from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import uuid

class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError(_('The Phone Number must be set'))
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, phone_number, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
            
        return self.create_user(phone_number, password, **extra_fields)

class User(AbstractUser):
    phone_number = models.CharField(
        _('phone number'),
        max_length=15,
        unique=True,
        help_text=_('Required. 15 characters or fewer. Digits only.')
    )
    email = models.EmailField(_('email address'), blank=True, null=True)
    spam_reported = models.PositiveIntegerField(default=0)
    
    username = None
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = UserManager()
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['first_name', 'last_name']),
        ]
    
    def clean(self):
        super().clean()
        if self.email:
            try:
                validate_email(self.email)
            except ValidationError:
                raise ValidationError({'email': _('Enter a valid email address.')})
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.phone_number})"

class Contact(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('name'), max_length=255)
    phone_number = models.CharField(_('phone number'), max_length=15)
    email = models.EmailField(_('email address'), blank=True, null=True)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='contacts',
        verbose_name=_('owner')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('contact')
        verbose_name_plural = _('contacts')
        unique_together = ('owner', 'phone_number')
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['name']),
            models.Index(fields=['owner', 'phone_number']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.phone_number})"

class SpamReport(models.Model):
    reporter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='spam_reports',
        verbose_name=_('reporter')
    )
    phone_number = models.CharField(_('phone number'), max_length=15)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('spam report')
        verbose_name_plural = _('spam reports')
        unique_together = ('reporter', 'phone_number')
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['reporter', 'phone_number']),
        ]
    
    def __str__(self):
        return f"Spam report for {self.phone_number} by {self.reporter}"