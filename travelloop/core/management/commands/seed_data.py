"""
Management command to seed the database with sample data.
Usage: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from core.models import (
    User, Trip, ItinerarySection, Activity,
    PackingCategory, PackingItem, TripNote,
    CommunityPost, Destination,
)
from datetime import date, time


class Command(BaseCommand):
    help = 'Seeds the database with sample Travelloop data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding destinations...')
        destinations = [
            ('Paris, France', 'City of Lights — world-class museums, iconic landmarks, and gourmet dining', 'city', 4.9, ['Romantic', 'Culture', 'Food']),
            ('Tokyo, Japan', 'A mesmerizing blend of ancient temples and futuristic technology', 'city', 4.8, ['Adventure', 'Tech', 'Food']),
            ('Bali, Indonesia', 'Tropical paradise with rice terraces, temples, and pristine beaches', 'nature', 4.7, ['Nature', 'Beach', 'Spiritual']),
            ('Santorini, Greece', 'Stunning white-washed villages perched on volcanic cliffs', 'city', 4.9, ['Luxury', 'Beach', 'Views']),
            ('Rome, Italy', 'Eternal City — ancient ruins, art masterpieces, and Italian cuisine', 'culture', 4.8, ['History', 'Culture', 'Food']),
            ('Dubai, UAE', 'Futuristic skyline meets desert adventures and luxury shopping', 'city', 4.6, ['Luxury', 'Shopping', 'Adventure']),
            ('New York, USA', 'The city that never sleeps — Broadway, Central Park, and world cuisine', 'city', 4.7, ['Nightlife', 'Culture', 'Food']),
            ('Swiss Alps', 'Majestic mountain landscapes for skiing, hiking, and scenic railways', 'nature', 4.9, ['Nature', 'Adventure', 'Scenic']),
            ('Machu Picchu, Peru', 'Ancient Incan citadel high in the Andes mountains', 'culture', 4.9, ['History', 'Adventure', 'Nature']),
            ('Maldives', 'Crystal-clear waters and overwater villas in the Indian Ocean', 'nature', 4.8, ['Luxury', 'Beach', 'Relaxation']),
        ]
        for name, desc, cat, rating, tags in destinations:
            Destination.objects.get_or_create(
                name=name,
                defaults={
                    'description': desc, 'category': cat,
                    'rating': rating, 'tags': tags,
                    'image': f'assets/images/{name.split(",")[0].split(" ")[0].lower()}.png',
                }
            )

        self.stdout.write(self.style.SUCCESS(
            f'OK Seeded {Destination.objects.count()} destinations'
        ))

        # Create admin user if not exists
        admin, created = User.objects.get_or_create(
            email='admin@travelloop.com',
            defaults={
                'first_name': 'Admin', 'last_name': '',
                'role': 'admin', 'avatar_initial': 'A',
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS('OK Created admin user (admin@travelloop.com / admin123)'))

        self.stdout.write(self.style.SUCCESS('Done! Database seeding complete!'))
