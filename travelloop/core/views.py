"""
Views for Travelloop — page views + JSON API endpoints.
Pattern follows the Humanloop reference repo (DevNovaOps/Humanloop).
"""
import json
from datetime import date, timedelta
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.db.models import Sum, Count, Q
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from .models import (
    User, Trip, ItinerarySection, Activity,
    PackingCategory, PackingItem, TripNote,
    CommunityPost, PostComment, Destination,
    Notification, AuditLog, PasswordResetOTP,
    Invoice, ExpenseItem,
)


# ═══════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════

def get_session_user(request):
    uid = request.session.get('user_id')
    if not uid:
        return None
    try:
        return User.objects.get(id=uid, is_active=True)
    except User.DoesNotExist:
        return None


def login_required_json(view_func):
    def wrapper(request, *args, **kwargs):
        user = get_session_user(request)
        if not user:
            return JsonResponse({'error': 'Not authenticated'}, status=401)
        request.user_obj = user
        return view_func(request, *args, **kwargs)
    return wrapper


def login_required_page(view_func):
    def wrapper(request, *args, **kwargs):
        user = get_session_user(request)
        if not user:
            return redirect('login')
        request.user_obj = user
        return view_func(request, *args, **kwargs)
    return wrapper


def get_client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    return xff.split(',')[0] if xff else request.META.get('REMOTE_ADDR')


def log_action(user, action, details='', request=None):
    AuditLog.objects.create(
        user=user, action=action, details=details,
        ip_address=get_client_ip(request) if request else None,
    )


# ═══════════════════════════════════════════════════
#  PAGE VIEWS  (render HTML templates)
# ═══════════════════════════════════════════════════

def page_index(request):
    return render(request, 'index.html')


def page_login(request):
    return render(request, 'login.html')


def page_register(request):
    return render(request, 'register.html')


def page_forgot_password(request):
    return render(request, 'forgot-password.html')


def page_verify_otp(request):
    return render(request, 'verify-otp.html')


def page_reset_password(request):
    return render(request, 'reset-password.html')


@login_required_page
def page_dashboard(request):
    return render(request, 'dashboard.html')


@login_required_page
def page_trips(request):
    return render(request, 'trips.html')


@login_required_page
def page_create_trip(request):
    return render(request, 'create-trip.html')


@login_required_page
def page_build_itinerary(request):
    return render(request, 'build-itinerary.html')


@login_required_page
def page_itinerary_view(request):
    return render(request, 'itinerary-view.html')


@login_required_page
def page_profile(request):
    return render(request, 'profile.html')


@login_required_page
def page_search(request):
    return render(request, 'search.html')


@login_required_page
def page_community(request):
    return render(request, 'community.html')


@login_required_page
def page_packing(request):
    return render(request, 'packing.html')


@login_required_page
def page_notes(request):
    return render(request, 'notes.html')


@login_required_page
def page_admin_panel(request):
    if request.user_obj.role != 'admin':
        return redirect('dashboard')
    return render(request, 'admin.html')


# ═══════════════════════════════════════════════════
#  AUTH APIs
# ═══════════════════════════════════════════════════

@csrf_exempt
@require_POST
def api_register(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    first_name = data.get('firstName', '').strip()
    last_name = data.get('lastName', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not all([first_name, email, password]):
        return JsonResponse({'error': 'First name, email and password are required'}, status=400)

    if User.objects.filter(email=email).exists():
        return JsonResponse({'error': 'Email already registered'}, status=409)

    user = User(first_name=first_name, last_name=last_name, email=email)
    user.set_password(password)
    user.avatar_initial = first_name[0].upper()
    user.save()

    log_action(user, 'User registered', f'{email}', request)

    request.session['user_id'] = user.id
    return JsonResponse({
        'success': True,
        'user': {
            'id': user.id, 'firstName': user.first_name,
            'lastName': user.last_name, 'email': user.email,
            'role': user.role,
        }
    }, status=201)


@csrf_exempt
@require_POST
def api_login(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    try:
        user = User.objects.get(email=email, is_active=True)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Invalid email or password'}, status=401)

    if not user.check_password(password):
        return JsonResponse({'error': 'Invalid email or password'}, status=401)

    request.session['user_id'] = user.id
    log_action(user, 'User logged in', '', request)

    return JsonResponse({
        'success': True,
        'user': {
            'id': user.id, 'firstName': user.first_name,
            'lastName': user.last_name, 'email': user.email,
            'role': user.role, 'phone': user.phone,
            'city': user.city, 'country': user.country,
        }
    })


@csrf_exempt
def api_logout(request):
    uid = request.session.get('user_id')
    if uid:
        try:
            user = User.objects.get(id=uid)
            log_action(user, 'User logged out', '', request)
        except User.DoesNotExist:
            pass
    request.session.flush()
    return JsonResponse({'success': True})


@csrf_exempt
@require_POST
def api_forgot_password(request):
    """Send a 6-digit OTP to the user's email."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    email = data.get('email', '').strip().lower()
    if not email:
        return JsonResponse({'error': 'Email is required'}, status=400)

    try:
        user = User.objects.get(email=email, is_active=True)
    except User.DoesNotExist:
        # Don't reveal if email exists
        return JsonResponse({'success': True, 'message': 'If this email exists, an OTP has been sent.'})

    # Invalidate old OTPs
    PasswordResetOTP.objects.filter(user=user, is_used=False).update(is_used=True)

    # Generate new OTP
    otp_code = PasswordResetOTP.generate_otp()
    PasswordResetOTP.objects.create(
        user=user,
        otp=otp_code,
        expires_at=timezone.now() + timedelta(minutes=10),
    )

    # Send email
    try:
        send_mail(
            subject='Travelloop — Password Reset OTP',
            message=f'Your password reset OTP is: {otp_code}\n\nThis code expires in 10 minutes.\nIf you did not request this, please ignore this email.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=f'''
            <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:32px;background:#0a192f;border-radius:16px;color:#f8fafc;">
                <div style="text-align:center;margin-bottom:24px;">
                    <h1 style="color:#06b6d4;margin:0;">Travelloop</h1>
                    <p style="color:#94a3b8;margin:4px 0 0;">Password Reset</p>
                </div>
                <div style="background:rgba(6,182,212,0.08);border:1px solid rgba(6,182,212,0.2);border-radius:12px;padding:24px;text-align:center;">
                    <p style="margin:0 0 12px;color:#94a3b8;">Your OTP code is:</p>
                    <div style="font-size:36px;font-weight:bold;letter-spacing:8px;color:#06b6d4;">{otp_code}</div>
                    <p style="margin:12px 0 0;color:#94a3b8;font-size:13px;">Expires in 10 minutes</p>
                </div>
                <p style="text-align:center;color:#64748b;font-size:12px;margin-top:24px;">If you didn\'t request this, ignore this email.</p>
            </div>
            ''',
            fail_silently=False,
        )
    except Exception as e:
        return JsonResponse({'error': f'Failed to send email: {str(e)}'}, status=500)

    log_action(user, 'Password reset OTP sent', email, request)
    return JsonResponse({'success': True, 'message': 'OTP sent to your email.'})


@csrf_exempt
@require_POST
def api_verify_otp(request):
    """Verify the OTP and return a reset token."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    email = data.get('email', '').strip().lower()
    otp_code = data.get('otp', '').strip()

    if not email or not otp_code:
        return JsonResponse({'error': 'Email and OTP are required'}, status=400)

    try:
        user = User.objects.get(email=email, is_active=True)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Invalid OTP'}, status=400)

    otp_obj = PasswordResetOTP.objects.filter(
        user=user, otp=otp_code, is_used=False
    ).order_by('-created_at').first()

    if not otp_obj or not otp_obj.is_valid():
        return JsonResponse({'error': 'Invalid or expired OTP'}, status=400)

    # Mark OTP as used
    otp_obj.is_used = True
    otp_obj.save()

    # Store email in session for reset step
    request.session['reset_email'] = email
    request.session['reset_verified'] = True

    return JsonResponse({'success': True, 'message': 'OTP verified successfully.'})


@csrf_exempt
@require_POST
def api_reset_password(request):
    """Reset the password after OTP verification."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    email = data.get('email', '').strip().lower() or request.session.get('reset_email', '')
    new_password = data.get('password', '')

    if not email or not new_password:
        return JsonResponse({'error': 'Email and new password are required'}, status=400)

    if len(new_password) < 8:
        return JsonResponse({'error': 'Password must be at least 8 characters'}, status=400)

    if not request.session.get('reset_verified'):
        return JsonResponse({'error': 'OTP verification required first'}, status=403)

    try:
        user = User.objects.get(email=email, is_active=True)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    user.set_password(new_password)
    user.save()

    # Clear session reset data
    request.session.pop('reset_email', None)
    request.session.pop('reset_verified', None)

    log_action(user, 'Password reset', email, request)
    return JsonResponse({'success': True, 'message': 'Password updated successfully.'})


# ═══════════════════════════════════════════════════
#  PROFILE API
# ═══════════════════════════════════════════════════

@csrf_exempt
@login_required_json
def api_profile(request):
    user = request.user_obj
    if request.method == 'GET':
        trips_count = Trip.objects.filter(created_by=user).count()
        return JsonResponse({
            'id': user.id, 'firstName': user.first_name,
            'lastName': user.last_name, 'email': user.email,
            'phone': user.phone, 'city': user.city,
            'country': user.country, 'role': user.role,
            'tripsCount': trips_count,
        })
    elif request.method == 'PUT':
        data = json.loads(request.body)
        user.first_name = data.get('firstName', user.first_name)
        user.last_name = data.get('lastName', user.last_name)
        user.phone = data.get('phone', user.phone)
        user.city = data.get('city', user.city)
        user.country = data.get('country', user.country)
        user.save()
        log_action(user, 'Profile updated', '', request)
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Method not allowed'}, status=405)


# ═══════════════════════════════════════════════════
#  DASHBOARD STATS API
# ═══════════════════════════════════════════════════

@login_required_json
def api_dashboard_stats(request):
    user = request.user_obj
    trips = Trip.objects.filter(created_by=user)
    total = trips.count()
    ongoing = trips.filter(status='ongoing').count()
    upcoming = trips.filter(status='upcoming').count()
    completed = trips.filter(status='completed').count()
    total_budget = trips.aggregate(s=Sum('budget'))['s'] or 0
    total_spent = Activity.objects.filter(
        section__trip__created_by=user
    ).aggregate(s=Sum('expense'))['s'] or 0
    return JsonResponse({
        'totalTrips': total, 'ongoing': ongoing,
        'upcoming': upcoming, 'completed': completed,
        'totalBudget': float(total_budget),
        'totalSpent': float(total_spent),
    })


# ═══════════════════════════════════════════════════
#  TRIPS API
# ═══════════════════════════════════════════════════

@csrf_exempt
@login_required_json
def api_trips(request):
    user = request.user_obj
    if request.method == 'GET':
        trips = Trip.objects.filter(created_by=user)
        status_filter = request.GET.get('status')
        if status_filter:
            trips = trips.filter(status=status_filter)
        search = request.GET.get('search', '')
        if search:
            trips = trips.filter(name__icontains=search)
        result = []
        for t in trips:
            cities = list(t.sections.values_list('title', flat=True))
            result.append({
                'id': t.id, 'name': t.name, 'destination': t.destination,
                'mood': t.mood, 'startDate': str(t.start_date),
                'endDate': str(t.end_date), 'budget': float(t.budget),
                'currency': t.currency, 'status': t.status, 'image': t.image,
                'cities': cities, 'citiesCount': len(cities),
            })
        return JsonResponse({'trips': result})

    elif request.method == 'POST':
        data = json.loads(request.body)
        trip = Trip.objects.create(
            name=data.get('name', 'My Trip'),
            destination=data.get('destination', ''),
            mood=data.get('mood', 'adventure'),
            start_date=data.get('startDate', date.today()),
            end_date=data.get('endDate', date.today()),
            budget=data.get('budget', 0),
            currency=data.get('currency', 'USD'),
            status='upcoming',
            image=data.get('image', ''),
            created_by=user,
        )
        log_action(user, 'Trip created', trip.name, request)
        return JsonResponse({'success': True, 'tripId': trip.id}, status=201)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
@login_required_json
def api_trip_detail(request, trip_id):
    user = request.user_obj
    trip = get_object_or_404(Trip, id=trip_id, created_by=user)

    if request.method == 'GET':
        sections = []
        for s in trip.sections.all():
            activities = [{
                'id': a.id, 'name': a.name, 'icon': a.icon,
                'timeStart': str(a.time_start) if a.time_start else '',
                'timeEnd': str(a.time_end) if a.time_end else '',
                'expense': float(a.expense), 'dayNumber': a.day_number,
            } for a in s.activities.all()]
            sections.append({
                'id': s.id, 'title': s.title, 'description': s.description,
                'startDate': str(s.start_date) if s.start_date else '',
                'endDate': str(s.end_date) if s.end_date else '',
                'budget': float(s.budget), 'activities': activities,
            })
        total_spent = Activity.objects.filter(
            section__trip=trip
        ).aggregate(s=Sum('expense'))['s'] or 0
        return JsonResponse({
            'id': trip.id, 'name': trip.name, 'destination': trip.destination,
            'mood': trip.mood, 'startDate': str(trip.start_date),
            'endDate': str(trip.end_date), 'budget': float(trip.budget),
            'status': trip.status, 'totalSpent': float(total_spent),
            'sections': sections,
        })

    elif request.method == 'PUT':
        data = json.loads(request.body)
        trip.name = data.get('name', trip.name)
        trip.destination = data.get('destination', trip.destination)
        trip.mood = data.get('mood', trip.mood)
        trip.status = data.get('status', trip.status)
        if data.get('startDate'):
            trip.start_date = data['startDate']
        if data.get('endDate'):
            trip.end_date = data['endDate']
        if data.get('budget') is not None:
            trip.budget = data['budget']
        trip.save()
        return JsonResponse({'success': True})

    elif request.method == 'DELETE':
        name = trip.name
        trip.delete()
        log_action(user, 'Trip deleted', name, request)
        return JsonResponse({'success': True})

    return JsonResponse({'error': 'Method not allowed'}, status=405)


# ═══════════════════════════════════════════════════
#  ITINERARY SECTIONS API
# ═══════════════════════════════════════════════════

@csrf_exempt
@login_required_json
def api_sections(request, trip_id):
    user = request.user_obj
    trip = get_object_or_404(Trip, id=trip_id, created_by=user)

    if request.method == 'GET':
        sections = [{
            'id': s.id, 'title': s.title, 'description': s.description,
            'startDate': str(s.start_date) if s.start_date else '',
            'endDate': str(s.end_date) if s.end_date else '',
            'budget': float(s.budget), 'order': s.order,
        } for s in trip.sections.all()]
        return JsonResponse({'sections': sections})

    elif request.method == 'POST':
        data = json.loads(request.body)
        section = ItinerarySection.objects.create(
            trip=trip, title=data.get('title', 'New Section'),
            description=data.get('description', ''),
            start_date=data.get('startDate'),
            end_date=data.get('endDate'),
            budget=data.get('budget', 0),
            order=data.get('order', trip.sections.count()),
        )
        return JsonResponse({'success': True, 'sectionId': section.id}, status=201)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
@login_required_json
def api_section_detail(request, trip_id, section_id):
    user = request.user_obj
    section = get_object_or_404(
        ItinerarySection, id=section_id, trip__id=trip_id, trip__created_by=user
    )
    if request.method == 'PUT':
        data = json.loads(request.body)
        section.title = data.get('title', section.title)
        section.description = data.get('description', section.description)
        if data.get('startDate'):
            section.start_date = data['startDate']
        if data.get('endDate'):
            section.end_date = data['endDate']
        if data.get('budget') is not None:
            section.budget = data['budget']
        section.save()
        return JsonResponse({'success': True})
    elif request.method == 'DELETE':
        section.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Method not allowed'}, status=405)


# ═══════════════════════════════════════════════════
#  ACTIVITIES API
# ═══════════════════════════════════════════════════

@csrf_exempt
@login_required_json
def api_activities(request, trip_id, section_id):
    user = request.user_obj
    section = get_object_or_404(
        ItinerarySection, id=section_id, trip__id=trip_id, trip__created_by=user
    )
    if request.method == 'GET':
        acts = [{
            'id': a.id, 'name': a.name, 'icon': a.icon,
            'timeStart': str(a.time_start) if a.time_start else '',
            'timeEnd': str(a.time_end) if a.time_end else '',
            'expense': float(a.expense), 'dayNumber': a.day_number,
        } for a in section.activities.all()]
        return JsonResponse({'activities': acts})
    elif request.method == 'POST':
        data = json.loads(request.body)
        act = Activity.objects.create(
            section=section, name=data.get('name', ''),
            icon=data.get('icon', 'landmark'),
            time_start=data.get('timeStart') or None,
            time_end=data.get('timeEnd') or None,
            expense=data.get('expense', 0),
            day_number=data.get('dayNumber', 1),
            date=data.get('date') or None,
            order=data.get('order', section.activities.count()),
        )
        return JsonResponse({'success': True, 'activityId': act.id}, status=201)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


# ═══════════════════════════════════════════════════
#  PACKING API
# ═══════════════════════════════════════════════════

@csrf_exempt
@login_required_json
def api_packing(request, trip_id):
    user = request.user_obj
    trip = get_object_or_404(Trip, id=trip_id, created_by=user)
    if request.method == 'GET':
        categories = []
        for cat in trip.packing_categories.all():
            items = [{'id': i.id, 'text': i.text, 'isPacked': i.is_packed}
                     for i in cat.items.all()]
            categories.append({
                'id': cat.id, 'name': cat.name, 'icon': cat.icon, 'items': items,
            })
        return JsonResponse({'categories': categories})
    elif request.method == 'POST':
        data = json.loads(request.body)
        cat_name = data.get('category', 'Other')
        cat, _ = PackingCategory.objects.get_or_create(
            trip=trip, name=cat_name,
            defaults={'icon': data.get('icon', 'box')}
        )
        item = PackingItem.objects.create(
            category=cat, text=data.get('text', ''),
            is_packed=data.get('isPacked', False),
        )
        return JsonResponse({'success': True, 'itemId': item.id}, status=201)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
@login_required_json
def api_packing_toggle(request, trip_id, item_id):
    user = request.user_obj
    item = get_object_or_404(
        PackingItem, id=item_id, category__trip__id=trip_id,
        category__trip__created_by=user,
    )
    if request.method == 'PUT':
        data = json.loads(request.body)
        item.is_packed = data.get('isPacked', not item.is_packed)
        item.save()
        return JsonResponse({'success': True, 'isPacked': item.is_packed})
    elif request.method == 'DELETE':
        item.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Method not allowed'}, status=405)


# ═══════════════════════════════════════════════════
#  NOTES API
# ═══════════════════════════════════════════════════

@csrf_exempt
@login_required_json
def api_notes(request, trip_id):
    user = request.user_obj
    trip = get_object_or_404(Trip, id=trip_id, created_by=user)
    if request.method == 'GET':
        notes = [{
            'id': n.id, 'title': n.title, 'body': n.body,
            'dayLabel': n.day_label, 'stop': n.stop,
            'createdAt': n.created_at.isoformat(),
        } for n in trip.notes.all()]
        return JsonResponse({'notes': notes})
    elif request.method == 'POST':
        data = json.loads(request.body)
        note = TripNote.objects.create(
            trip=trip, title=data.get('title', ''),
            body=data.get('body', ''),
            day_label=data.get('dayLabel', ''),
            stop=data.get('stop', ''),
            created_by=user,
        )
        return JsonResponse({'success': True, 'noteId': note.id}, status=201)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
@login_required_json
def api_note_detail(request, trip_id, note_id):
    user = request.user_obj
    note = get_object_or_404(TripNote, id=note_id, trip__id=trip_id, created_by=user)
    if request.method == 'PUT':
        data = json.loads(request.body)
        note.title = data.get('title', note.title)
        note.body = data.get('body', note.body)
        note.day_label = data.get('dayLabel', note.day_label)
        note.stop = data.get('stop', note.stop)
        note.save()
        return JsonResponse({'success': True})
    elif request.method == 'DELETE':
        note.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Method not allowed'}, status=405)


# ═══════════════════════════════════════════════════
#  COMMUNITY API
# ═══════════════════════════════════════════════════

@csrf_exempt
@login_required_json
def api_community(request):
    user = request.user_obj
    if request.method == 'GET':
        posts = CommunityPost.objects.select_related('author').all()[:50]
        result = [{
            'id': p.id,
            'author': f'{p.author.first_name} {p.author.last_name}'.strip(),
            'initials': (p.author.first_name[0] + (p.author.last_name[0] if p.author.last_name else '')).upper(),
            'tripName': p.trip_name or (p.trip.name if p.trip else ''),
            'text': p.text, 'likes': p.likes,
            'comments': p.comments_count,
            'createdAt': p.created_at.isoformat(),
        } for p in posts]
        return JsonResponse({'posts': result})
    elif request.method == 'POST':
        data = json.loads(request.body)
        post = CommunityPost.objects.create(
            author=user, text=data.get('text', ''),
            trip_name=data.get('tripName', ''),
        )
        return JsonResponse({'success': True, 'postId': post.id}, status=201)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
@login_required_json
def api_community_like(request, post_id):
    post = get_object_or_404(CommunityPost, id=post_id)
    post.likes += 1
    post.save()
    return JsonResponse({'success': True, 'likes': post.likes})


# ═══════════════════════════════════════════════════
#  SEARCH / DESTINATIONS API
# ═══════════════════════════════════════════════════

@login_required_json
def api_destinations(request):
    q = request.GET.get('q', '')
    cat = request.GET.get('category', '')
    qs = Destination.objects.all()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))
    if cat and cat != 'all':
        qs = qs.filter(category=cat)
    result = [{
        'id': d.id, 'name': d.name, 'description': d.description,
        'image': d.image, 'category': d.category,
        'rating': float(d.rating), 'tags': d.tags,
    } for d in qs[:50]]
    return JsonResponse({'destinations': result})


# ═══════════════════════════════════════════════════
#  ADMIN APIs
# ═══════════════════════════════════════════════════

@login_required_json
def api_admin_users(request):
    user = request.user_obj
    if user.role != 'admin':
        return JsonResponse({'error': 'Forbidden'}, status=403)
    users = User.objects.all().order_by('-created_at')
    result = [{
        'id': u.id, 'name': f'{u.first_name} {u.last_name}'.strip(),
        'email': u.email, 'role': u.role,
        'isActive': u.is_active,
        'tripsCount': u.trips.count(),
        'joinedAt': u.created_at.isoformat(),
    } for u in users]
    return JsonResponse({'users': result})


@csrf_exempt
@login_required_json
def api_admin_toggle_user(request, user_id):
    admin = request.user_obj
    if admin.role != 'admin':
        return JsonResponse({'error': 'Forbidden'}, status=403)
    target = get_object_or_404(User, id=user_id)
    target.is_active = not target.is_active
    target.save()
    action = 'activated' if target.is_active else 'deactivated'
    log_action(admin, f'User {action}', target.email, request)
    return JsonResponse({'success': True, 'isActive': target.is_active})


@login_required_json
def api_admin_stats(request):
    if request.user_obj.role != 'admin':
        return JsonResponse({'error': 'Forbidden'}, status=403)
    return JsonResponse({
        'totalUsers': User.objects.count(),
        'activeTrips': Trip.objects.filter(status='ongoing').count(),
        'totalTrips': Trip.objects.count(),
        'totalPosts': CommunityPost.objects.count(),
    })


# ═══════════════════════════════════════════════════
#  NOTIFICATIONS API
# ═══════════════════════════════════════════════════

@login_required_json
def api_notifications(request):
    user = request.user_obj
    notifs = Notification.objects.filter(user=user)[:20]
    result = [{
        'id': n.id, 'title': n.title, 'message': n.message,
        'icon': n.icon, 'isRead': n.is_read,
        'createdAt': n.created_at.isoformat(),
    } for n in notifs]
    return JsonResponse({'notifications': result})


# ═══════════════════════════════════════════════════
#  HEALTH CHECK
# ═══════════════════════════════════════════════════

def api_health(request):
    return JsonResponse({'status': 'ok', 'app': 'travelloop'})


# ═══════════════════════════════════════════════════
#  AI SUGGESTION (Groq llama-3.1-8b-instant)
# ═══════════════════════════════════════════════════

@csrf_exempt
@login_required_json
def api_ai_suggest(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)
    data = json.loads(request.body)
    prompt_type = data.get('type', 'itinerary')
    destination = data.get('destination', '')
    days = data.get('days', 3)
    mood = data.get('mood', 'adventure')
    extra = data.get('extra', '')
    system_msg = "You are a world-class travel planner. Give concise, practical suggestions. Respond in JSON format when asked."
    if prompt_type == 'itinerary':
        user_msg = f"Create a {days}-day {mood} itinerary for {destination}. Include morning, afternoon, evening for each day. Return JSON array with keys: day, morning, afternoon, evening, tip."
    elif prompt_type == 'packing':
        user_msg = f"Suggest a packing list for a {days}-day {mood} trip to {destination}. Group by category. Return JSON array with keys: category, items."
    elif prompt_type == 'budget':
        user_msg = f"Estimate daily budget for {destination} ({mood}, {days} days). Return JSON with keys: daily, total, currency, tips."
    else:
        user_msg = extra or f"Give 5 travel tips for {destination}."
    try:
        from groq import Groq
        client = Groq(api_key=settings.GROQ_API_KEY)
        completion = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}],
            temperature=0.7, max_tokens=2048,
        )
        text = completion.choices[0].message.content
        import re
        m = re.search(r'[\[\{].*[\]\}]', text, re.DOTALL)
        if m:
            try:
                return JsonResponse({'success': True, 'data': json.loads(m.group()), 'raw': text})
            except json.JSONDecodeError:
                pass
        return JsonResponse({'success': True, 'data': None, 'raw': text})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ═══════════════════════════════════════════════════
#  INVOICE PAGE
# ═══════════════════════════════════════════════════

@login_required_page
def page_invoices(request):
    return render(request, 'invoices.html')


# ═══════════════════════════════════════════════════
#  INVOICE / EXPENSE APIs
# ═══════════════════════════════════════════════════

@csrf_exempt
@login_required_json
def api_invoices(request):
    user = request.user_obj
    if request.method == 'GET':
        trip_id = request.GET.get('trip_id')
        qs = Invoice.objects.filter(created_by=user).select_related('trip')
        if trip_id:
            qs = qs.filter(trip_id=trip_id)
        result = [{
            'id': inv.id, 'invoiceNumber': inv.invoice_number,
            'tripId': inv.trip_id, 'tripName': inv.trip.name, 'destination': inv.trip.destination,
            'startDate': str(inv.trip.start_date), 'endDate': str(inv.trip.end_date),
            'subtotal': float(inv.subtotal), 'taxPercent': float(inv.tax_percent),
            'taxAmount': float(inv.tax_amount), 'discount': float(inv.discount),
            'grandTotal': float(inv.grand_total), 'currency': inv.currency,
            'paymentStatus': inv.payment_status, 'paymentMethod': inv.payment_method,
            'createdAt': inv.created_at.isoformat(),
            'items': [{'id': i.id, 'category': i.category, 'description': i.description,
                       'quantity': i.quantity, 'unitCost': float(i.unit_cost), 'amount': float(i.amount)}
                      for i in inv.items.all()],
        } for inv in qs]
        return JsonResponse({'invoices': result})
    elif request.method == 'POST':
        data = json.loads(request.body)
        trip = get_object_or_404(Trip, id=data.get('tripId'), created_by=user)
        import random, string
        inv_num = f"INV-{trip.destination[:3].upper()}-{''.join(random.choices(string.digits, k=5))}"
        inv = Invoice.objects.create(
            trip=trip, invoice_number=inv_num, created_by=user,
            currency=trip.currency, tax_percent=data.get('taxPercent', 5),
            discount=data.get('discount', 0),
        )
        for item_data in data.get('items', []):
            uc = float(item_data.get('unitCost', 0))
            qs = item_data.get('quantity', '1')
            try:
                qn = float(qs.split()[0])
            except (ValueError, IndexError):
                qn = 1
            ExpenseItem.objects.create(
                invoice=inv, category=item_data.get('category', 'other'),
                description=item_data.get('description', ''), quantity=qs,
                unit_cost=uc, amount=uc * qn,
            )
        inv.recalculate()
        return JsonResponse({'success': True, 'invoiceId': inv.id, 'invoiceNumber': inv.invoice_number}, status=201)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
@login_required_json
def api_invoice_detail(request, invoice_id):
    user = request.user_obj
    inv = get_object_or_404(Invoice, id=invoice_id, created_by=user)
    if request.method == 'GET':
        items = [{'id': i.id, 'category': i.category, 'description': i.description,
                  'quantity': i.quantity, 'unitCost': float(i.unit_cost), 'amount': float(i.amount)}
                 for i in inv.items.all()]
        return JsonResponse({
            'id': inv.id, 'invoiceNumber': inv.invoice_number,
            'tripId': inv.trip_id, 'tripName': inv.trip.name, 'destination': inv.trip.destination,
            'startDate': str(inv.trip.start_date), 'endDate': str(inv.trip.end_date),
            'subtotal': float(inv.subtotal), 'taxPercent': float(inv.tax_percent),
            'taxAmount': float(inv.tax_amount), 'discount': float(inv.discount),
            'grandTotal': float(inv.grand_total), 'currency': inv.currency,
            'paymentStatus': inv.payment_status, 'items': items,
        })
    elif request.method == 'PUT':
        data = json.loads(request.body)
        for k in ('paymentStatus', 'discount', 'taxPercent'):
            if k in data:
                setattr(inv, {'paymentStatus': 'payment_status', 'taxPercent': 'tax_percent'}.get(k, k), data[k])
        inv.save()
        inv.recalculate()
        return JsonResponse({'success': True})
    elif request.method == 'DELETE':
        inv.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
@login_required_json
def api_expense_item(request, invoice_id):
    user = request.user_obj
    inv = get_object_or_404(Invoice, id=invoice_id, created_by=user)
    if request.method == 'POST':
        data = json.loads(request.body)
        uc = float(data.get('unitCost', 0))
        qs = data.get('quantity', '1')
        try:
            qn = float(qs.split()[0])
        except (ValueError, IndexError):
            qn = 1
        item = ExpenseItem.objects.create(
            invoice=inv, category=data.get('category', 'other'),
            description=data.get('description', ''), quantity=qs,
            unit_cost=uc, amount=uc * qn,
        )
        inv.recalculate()
        return JsonResponse({'success': True, 'itemId': item.id}, status=201)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
@login_required_json
def api_expense_item_delete(request, invoice_id, item_id):
    user = request.user_obj
    inv = get_object_or_404(Invoice, id=invoice_id, created_by=user)
    item = get_object_or_404(ExpenseItem, id=item_id, invoice=inv)
    if request.method == 'DELETE':
        item.delete()
        inv.recalculate()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Method not allowed'}, status=405)


# ═══════════════════════════════════════════════════
#  PAYMENT GATEWAY APIs
# ═══════════════════════════════════════════════════

@csrf_exempt
@login_required_json
def api_payment_create(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)
    data = json.loads(request.body)
    inv = get_object_or_404(Invoice, id=data.get('invoiceId'), created_by=request.user_obj)
    amount = int(inv.grand_total * 100)
    method = data.get('method', 'razorpay')
    amount = max(amount, 100)  # minimum charge

    if method == 'razorpay':
        try:
            import razorpay
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            order = client.order.create({
                'amount': amount, 'currency': inv.currency or 'INR',
                'receipt': inv.invoice_number,
            })
            inv.payment_method = 'razorpay'
            inv.payment_id = order['id']
            inv.save()
            return JsonResponse({'success': True, 'orderId': order['id'], 'amount': amount,
                                 'currency': inv.currency or 'INR', 'key': settings.RAZORPAY_KEY_ID,
                                 'invoiceNumber': inv.invoice_number})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Razorpay error: {str(e)}'}, status=400)

    elif method == 'stripe':
        try:
            import stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            currency_code = (inv.currency or 'usd').lower()
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{'price_data': {'currency': currency_code,
                                            'product_data': {'name': f'Invoice {inv.invoice_number} — {inv.trip.name}'},
                                            'unit_amount': amount}, 'quantity': 1}],
                mode='payment',
                success_url=request.build_absolute_uri('/invoices/') + f'?paid={inv.id}',
                cancel_url=request.build_absolute_uri('/invoices/') + f'?cancelled={inv.id}',
            )
            inv.payment_method = 'stripe'
            inv.payment_id = session.id
            inv.save()
            return JsonResponse({'success': True, 'sessionId': session.id, 'url': session.url,
                                 'publishableKey': settings.STRIPE_PUBLISHABLE_KEY})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Stripe error: {str(e)}'}, status=400)

    return JsonResponse({'error': 'Unknown payment method'}, status=400)


@csrf_exempt
@login_required_json
def api_payment_verify(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)
    data = json.loads(request.body)
    inv = get_object_or_404(Invoice, id=data.get('invoiceId'), created_by=request.user_obj)
    method = data.get('method', inv.payment_method)
    if method == 'razorpay':
        import razorpay
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id': data.get('razorpay_order_id', ''),
                'razorpay_payment_id': data.get('razorpay_payment_id', ''),
                'razorpay_signature': data.get('razorpay_signature', ''),
            })
            inv.payment_status = 'paid'
            inv.payment_id = data.get('razorpay_payment_id', inv.payment_id)
            inv.save()
            return JsonResponse({'success': True, 'status': 'paid'})
        except Exception:
            inv.payment_status = 'failed'
            inv.save()
            return JsonResponse({'success': False, 'status': 'failed'}, status=400)
    elif method == 'stripe':
        inv.payment_status = 'paid'
        inv.save()
        return JsonResponse({'success': True, 'status': 'paid'})
    return JsonResponse({'error': 'Unknown method'}, status=400)
