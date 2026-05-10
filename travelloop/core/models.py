from django.db import models
from django.contrib.auth.hashers import make_password, check_password as django_check_password
from django.utils import timezone
import uuid
import random


# ──────────────────────────────────────────────────
#  User & Auth
# ──────────────────────────────────────────────────

ROLE_CHOICES = [
    ('traveler', 'Traveler'),
    ('admin', 'Admin'),
]

MOOD_CHOICES = [
    ('adventure', 'Adventure'),
    ('luxury', 'Luxury'),
    ('nature', 'Nature'),
    ('budget', 'Budget'),
    ('nightlife', 'Nightlife'),
]

TRIP_STATUS_CHOICES = [
    ('upcoming', 'Upcoming'),
    ('ongoing', 'Ongoing'),
    ('completed', 'Completed'),
]


class User(models.Model):
    """Custom user model (same pattern as reference Humanloop repo)."""
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True, default='')
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='traveler')
    phone = models.CharField(max_length=20, blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    country = models.CharField(max_length=100, blank=True, default='')
    avatar_initial = models.CharField(max_length=5, blank=True, default='')
    is_active = models.BooleanField(default=True)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return django_check_password(raw_password, self.password)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role})"


# ──────────────────────────────────────────────────
#  Trip
# ──────────────────────────────────────────────────

class PasswordResetOTP(models.Model):
    """Stores 6-digit OTPs for password reset via email."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_codes')
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        db_table = 'password_reset_otps'
        ordering = ['-created_at']

    @staticmethod
    def generate_otp():
        return str(random.randint(100000, 999999))

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at

    def __str__(self):
        return f"OTP for {self.user.email} — {'valid' if self.is_valid() else 'expired'}"



class Trip(models.Model):
    """A travel trip created by a user."""
    name = models.CharField(max_length=300)
    destination = models.CharField(max_length=200)
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES, default='adventure')
    start_date = models.DateField()
    end_date = models.DateField()
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=TRIP_STATUS_CHOICES, default='upcoming')
    image = models.CharField(max_length=300, blank=True, default='')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trips')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'trips'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.status})"


# ──────────────────────────────────────────────────
#  Itinerary Section (belongs to a Trip)
# ──────────────────────────────────────────────────

class ItinerarySection(models.Model):
    """A section within a trip's itinerary."""
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True, default='')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'itinerary_sections'
        ordering = ['order', 'start_date']

    def __str__(self):
        return f"{self.title} — {self.trip.name}"


# ──────────────────────────────────────────────────
#  Activity (belongs to an ItinerarySection)
# ──────────────────────────────────────────────────

ACTIVITY_ICON_CHOICES = [
    ('plane', 'Flight'),
    ('car', 'Transport'),
    ('bed', 'Hotel'),
    ('landmark', 'Landmark'),
    ('utensils', 'Restaurant'),
    ('palette', 'Museum'),
    ('ship', 'Cruise'),
    ('shopping-bag', 'Shopping'),
    ('church', 'Temple/Church'),
    ('wine', 'Dining'),
    ('camera', 'Photography'),
    ('umbrella', 'Beach'),
    ('mountain', 'Hiking'),
]


class Activity(models.Model):
    """A single activity within an itinerary section."""
    section = models.ForeignKey(ItinerarySection, on_delete=models.CASCADE, related_name='activities')
    name = models.CharField(max_length=300)
    time_start = models.TimeField(null=True, blank=True)
    time_end = models.TimeField(null=True, blank=True)
    expense = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    icon = models.CharField(max_length=30, choices=ACTIVITY_ICON_CHOICES, default='landmark')
    day_number = models.IntegerField(default=1)
    date = models.DateField(null=True, blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        db_table = 'activities'
        ordering = ['day_number', 'order', 'time_start']

    def __str__(self):
        return f"{self.name} (Day {self.day_number})"


# ──────────────────────────────────────────────────
#  Packing Checklist
# ──────────────────────────────────────────────────

class PackingCategory(models.Model):
    """A category of packing items (e.g. Documents, Clothing)."""
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='packing_categories')
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default='box')
    order = models.IntegerField(default=0)

    class Meta:
        db_table = 'packing_categories'
        ordering = ['order']

    def __str__(self):
        return f"{self.name} — {self.trip.name}"


class PackingItem(models.Model):
    """A single item in a packing category."""
    category = models.ForeignKey(PackingCategory, on_delete=models.CASCADE, related_name='items')
    text = models.CharField(max_length=200)
    is_packed = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        db_table = 'packing_items'
        ordering = ['order']

    def __str__(self):
        return f"{'✓' if self.is_packed else '○'} {self.text}"


# ──────────────────────────────────────────────────
#  Trip Notes / Journal
# ──────────────────────────────────────────────────

class TripNote(models.Model):
    """A note attached to a trip."""
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='notes')
    title = models.CharField(max_length=300)
    body = models.TextField(blank=True, default='')
    day_label = models.CharField(max_length=50, blank=True, default='')  # e.g. "Day 1"
    stop = models.CharField(max_length=100, blank=True, default='')  # e.g. "Paris"
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'trip_notes'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


# ──────────────────────────────────────────────────
#  Community Posts
# ──────────────────────────────────────────────────

class CommunityPost(models.Model):
    """A post in the community feed."""
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    trip = models.ForeignKey(Trip, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    trip_name = models.CharField(max_length=200, blank=True, default='')
    text = models.TextField()
    likes = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'community_posts'
        ordering = ['-created_at']

    def __str__(self):
        return f"Post by {self.author.first_name} — {self.created_at.date()}"


class PostComment(models.Model):
    """A comment on a community post."""
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'post_comments'
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.first_name}"


# ──────────────────────────────────────────────────
#  Destinations / Search
# ──────────────────────────────────────────────────

class Destination(models.Model):
    """A searchable city or activity."""
    CATEGORY_CHOICES = [
        ('city', 'City'),
        ('activity', 'Activity'),
        ('nature', 'Nature'),
        ('food', 'Food & Dining'),
        ('culture', 'Culture'),
    ]
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    image = models.CharField(max_length=300, blank=True, default='')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='city')
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=0)
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'destinations'
        ordering = ['-rating']

    def __str__(self):
        return self.name


# ──────────────────────────────────────────────────
#  Notification
# ──────────────────────────────────────────────────

class Notification(models.Model):
    """A notification for a user."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    icon = models.CharField(max_length=50, default='bell')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


# ──────────────────────────────────────────────────
#  Audit Log (Admin)
# ──────────────────────────────────────────────────

class AuditLog(models.Model):
    """Admin audit trail."""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=200)
    details = models.TextField(blank=True, default='')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action} by {self.user}"


# ──────────────────────────────────────────────────
#  Invoice / Expense Billing
# ──────────────────────────────────────────────────

PAYMENT_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('paid', 'Paid'),
    ('failed', 'Failed'),
    ('refunded', 'Refunded'),
]

PAYMENT_METHOD_CHOICES = [
    ('razorpay', 'Razorpay'),
    ('stripe', 'Stripe'),
    ('manual', 'Manual'),
]


class Invoice(models.Model):
    """Invoice / billing record for a trip."""
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='invoices')
    invoice_number = models.CharField(max_length=50, unique=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=5)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='USD')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='manual')
    payment_id = models.CharField(max_length=200, blank=True, default='')
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'invoices'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.invoice_number} — {self.trip.name}"

    def recalculate(self):
        self.subtotal = sum(e.amount for e in self.items.all())
        self.tax_amount = self.subtotal * self.tax_percent / 100
        self.grand_total = self.subtotal + self.tax_amount - self.discount
        self.save()


class ExpenseItem(models.Model):
    """A single expense line item in an invoice."""
    CATEGORY_CHOICES = [
        ('hotel', 'Hotel'), ('travel', 'Travel'), ('food', 'Food'),
        ('activity', 'Activity'), ('transport', 'Transport'),
        ('shopping', 'Shopping'), ('insurance', 'Insurance'), ('other', 'Other'),
    ]
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='other')
    description = models.CharField(max_length=300)
    quantity = models.CharField(max_length=50, default='1')
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'expense_items'
        ordering = ['id']

    def __str__(self):
        return f"{self.category}: {self.description}"
