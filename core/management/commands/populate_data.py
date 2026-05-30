from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Contact, SpamReport
from faker import Faker
import random
from datetime import timedelta
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Populates the database with sample data'
    
    def handle(self, *args, **options):
        fake = Faker()
        
        # Create admin user
        admin = User.objects.create_superuser(
            phone_number='9999999999',
            password='admin123',
            first_name='Admin',
            last_name='User',
            email='admin@example.com'
        )
        
        # Create regular users
        for _ in range(50):
            try:
                user = User.objects.create_user(
                    phone_number=fake.numerify('##########'),
                    password='testpass123',
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    email=fake.email() if random.random() > 0.3 else None,
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating user: {e}'))
                continue
        
        # Create contacts for users
        users = User.objects.all()
        for user in users:
            for _ in range(random.randint(0, 20)):
                try:
                    Contact.objects.create(
                        owner=user,
                        name=fake.name(),
                        phone_number=fake.numerify('##########'),
                        email=fake.email() if random.random() > 0.5 else None,
                    )
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error creating contact: {e}'))
                    continue
        
        # Create spam reports
        all_phone_numbers = list(User.objects.exclude(
            phone_number='9999999999'
        ).values_list('phone_number', flat=True)) + list(
            Contact.objects.values_list('phone_number', flat=True)
        )
        
        for _ in range(100):
            phone = random.choice(all_phone_numbers)
            reporter = random.choice(users)
            
            # Ensure reporter is not reporting their own number
            if phone != reporter.phone_number:
                try:
                    SpamReport.objects.get_or_create(
                        reporter=reporter,
                        phone_number=phone,
                        defaults={'created_at': timezone.now() - timedelta(days=random.randint(0, 30))}
                    )
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error creating spam report: {e}'))
                    continue
        
        self.stdout.write(self.style.SUCCESS('Successfully populated the database'))