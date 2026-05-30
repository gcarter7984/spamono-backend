from django.db.models import (
    Count, 
    Q, 
    F, 
    ExpressionWrapper, 
    FloatField,
    OuterRef,  # Add this
    Subquery,   # Add this
    Value,      # Add this
    Case,       # Add this
    When,       # Add this
)
from django.db.models.functions import Concat, Coalesce, Lower  # Add Coalesce here
from django.db import models  # For models.IntegerField
from .models import User, Contact, SpamReport

class SearchService:
    def search_by_name(query, current_user):
        query = query.strip().lower()
        if not query or len(query) < 2:
            return []

        # Get all phone numbers in current user's contacts
        my_contacts_numbers = set(
            Contact.objects.filter(owner=current_user)
            .values_list('phone_number', flat=True)
        )

        # Spam likelihood calculation
        spam_subquery = SpamReport.objects.filter(
            phone_number=OuterRef('phone_number')
        ).values('phone_number').annotate(
            count=Count('id')
        ).values('count')
        total_reports = SpamReport.objects.count() or 1

        # Base queryset for registered users
        registered_users = User.objects.annotate(
            full_name=Concat('first_name', Value(' '), 'last_name'),
            lower_full_name=Lower(Concat('first_name', Value(' '), 'last_name')),
            spam_likelihood=ExpressionWrapper(
                Coalesce(Subquery(spam_subquery), 0) / total_reports,
                output_field=FloatField()
            ),
            is_in_my_contacts=Case(
                When(phone_number__in=my_contacts_numbers, then=True),
                default=False,
                output_field=models.BooleanField()
            )
        )

        # Base queryset for contacts
        contacts = Contact.objects.annotate(
            lower_name=Lower('name'),
            spam_likelihood=ExpressionWrapper(
                Coalesce(Subquery(spam_subquery), 0) / total_reports,
                output_field=FloatField()
            )
        )

        # Process both start-with and contains matches
        results = []

        # 1. Process names STARTING with query
        # Registered users
        start_users = registered_users.filter(
            lower_full_name__startswith=query
        ).annotate(
            match_type=Value('start'),
            is_registered=Value(True)
        ).values(
            'id', 'full_name', 'phone_number', 'email',
            'spam_likelihood', 'is_registered', 'is_in_my_contacts', 'match_type'
        )

        # Contacts (excluding registered users)
        start_contacts = contacts.exclude(
            phone_number__in=User.objects.values('phone_number')
        ).filter(
            lower_name__startswith=query
        ).annotate(
            match_type=Value('start'),
            is_registered=Value(False)
        ).values(
            'id', 'name', 'phone_number',
            'spam_likelihood', 'is_registered', 'match_type'
        )

        # 2. Process names CONTAINING but NOT STARTING with query
        # Registered users
        contain_users = registered_users.filter(
            lower_full_name__contains=query
        ).exclude(
            lower_full_name__startswith=query
        ).annotate(
            match_type=Value('contain'),
            is_registered=Value(True)
        ).values(
            'id', 'full_name', 'phone_number', 'email',
            'spam_likelihood', 'is_registered', 'is_in_my_contacts', 'match_type'
        )

        # Contacts (excluding registered users and start matches)
        contain_contacts = contacts.exclude(
            phone_number__in=User.objects.values('phone_number')
        ).filter(
            lower_name__contains=query
        ).exclude(
            lower_name__startswith=query
        ).annotate(
            match_type=Value('contain'),
            is_registered=Value(False)
        ).values(
            'id', 'name', 'phone_number',
            'spam_likelihood', 'is_registered', 'match_type'
        )

        # Combine and process all results
        for group in [start_users, start_contacts, contain_users, contain_contacts]:
            for item in group:
                result = {
                    'id': item['id'],
                    'name': item.get('full_name') or item['name'],
                    'phone_number': item['phone_number'],
                    'spam_likelihood': item['spam_likelihood'],
                    'is_registered': item['is_registered'],
                    'match_priority': 0 if item['match_type'] == 'start' else 1
                }

                # Email visibility rules
                if item['is_registered']:
                    result['email'] = item['email'] if item.get('is_in_my_contacts', False) else None
                else:
                    result['email'] = None

                results.append(result)

        # Final ordering:
        # 1. Start matches before contain matches
        # 2. Registered users before contacts for same match type
        return sorted(results, key=lambda x: (
            x['match_priority'],  # start matches first
            0 if x['is_registered'] else 1,  # registered first
            x['name'].lower()  # alphabetical
        ))
    
    @staticmethod
    def search_by_phone(phone_number, current_user):
        # Calculate spam likelihood (works for any number)
        spam_count = SpamReport.objects.filter(
            phone_number=phone_number
        ).count()
        total_reports = SpamReport.objects.count() or 1
        spam_likelihood = spam_count / total_reports

        # Check if registered user
        registered_user = User.objects.filter(
            phone_number=phone_number
        ).first()

        if registered_user:
            is_in_my_contacts = Contact.objects.filter(
                owner=current_user,
                phone_number=phone_number
            ).exists()
            
            return [{
                'id': str(registered_user.id),
                'name': f"{registered_user.first_name} {registered_user.last_name}",
                'phone_number': registered_user.phone_number,
                'email': registered_user.email if is_in_my_contacts else None,
                'spam_likelihood': spam_likelihood,
                'is_registered': True
            }]

        # Check if in any contacts
        contacts = Contact.objects.filter(
            phone_number=phone_number
        ).values(
            'id', 'name', 'phone_number'
        ).annotate(
            is_registered=Value(False),
            spam_likelihood=Value(spam_likelihood, output_field=FloatField())
        )

        if contacts.exists():
            return [{
                **contact,
                'email': None  # Never show email for unregistered numbers
            } for contact in contacts]

        # For completely unknown numbers
        return [{
            'phone_number': phone_number,
            'spam_likelihood': spam_likelihood,
            'is_registered': False,
            'is_unknown': True  # Flag for completely unknown numbers
        }]

class SpamReportService:
    @staticmethod
    def report_spam(reporter, phone_number):
        """
        Report any phone number as spam with these rules:
        1. Can report any number (registered, in contacts, or unknown)
        2. Can't report your own number
        3. Can't report the same number multiple times
        4. Updates spam count for registered users
        """
        # Validate phone number format (basic check)
        if not phone_number or not isinstance(phone_number, str) or not phone_number.isdigit():
            raise ValueError("Invalid phone number format")

        # Check if reporter is trying to report their own number
        if reporter.phone_number == phone_number:
            raise ValueError("You cannot report your own number as spam")

        # Check if already reported by this user
        if SpamReport.objects.filter(
            reporter=reporter,
            phone_number=phone_number
        ).exists():
            raise ValueError("You have already reported this number")

        # Create the report
        report = SpamReport.objects.create(
            reporter=reporter,
            phone_number=phone_number
        )

        # Update spam count if it's a registered user
        user = User.objects.filter(phone_number=phone_number).first()
        if user:
            user.spam_reported = SpamReport.objects.filter(
                phone_number=phone_number
            ).count()
            user.save()

        return report