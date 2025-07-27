from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.messages import get_messages
from django.conf import settings
from .models import HouseListing, ScheduleVisit, Notification
from django.http import JsonResponse, HttpResponse
from django.core.mail import send_mail
from django.db.models import Q
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.db import transaction

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import joblib
import logging
import os

# Set up logging
logger = logging.getLogger(__name__)

# Load model
try:
    model = joblib.load('my_new_model.pkl')
except Exception as e:
    logger.error(f"Error loading model: {str(e)}")
    model = None

# Load dataset
try:
    housing_data = pd.read_excel(r'C:\Users\Asus\OneDrive\Desktop\kathmandu\HousePricePrediction\HousePricePrediction\kathmandudataset.xlsx')
except Exception as e:
    logger.error(f"Error loading dataset: {str(e)}")
    housing_data = None

def load_evaluation_metrics():
    try:
        metrics_path = os.path.join(settings.BASE_DIR, 'model_evaluation.txt')
        with open(metrics_path, 'r') as f:
            metrics = {}
            for line in f.readlines():
                if ':' in line:
                    key, value = line.split(':', 1)
                    metrics[key.strip()] = value.strip()
            return metrics
    except Exception as e:
        logger.error(f"Error loading evaluation metrics: {str(e)}")
        return None

# Notification utilities
def create_notification(user, message, link='', notification_type='info'):
    Notification.objects.create(
        user=user,
        message=message,
        link=link,
        notification_type=notification_type
    )
    logger.info(f"Notification created for user {user.username}: {message}")
    if notification_type in ['alert', 'important']:
        try:
            send_mail(
                'New Notification',
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True,
            )
        except Exception as e:
            logger.error(f"Failed to send email notification: {str(e)}")

# Core pages
def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html', {
        'title': 'About Our Service',
        'description': 'This application predicts house prices using machine learning...'
    })

def contact(request):
    if request.method == 'POST':
        messages.success(request, "Your message has been sent successfully!")
        return redirect('contact')
    return render(request, 'contact.html')

# Auth
def login_view(request):
    # Clear any existing messages
    storage = get_messages(request)
    for message in storage:
        pass  # This consumes the messages
    
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            unread_count = Notification.objects.filter(user=user, is_read=False).count()
            if unread_count > 0:
                messages.info(request, f"You have {unread_count} unread notifications")
            return redirect(request.GET.get('next', 'home'))
        else:
            return render(request, 'registration/login.html', {'form': {}, 'login_page': True})

    return render(request, 'registration/login.html', {'form': {}, 'login_page': False})

def logout_view(request):
    storage = get_messages(request)
    for message in storage:
        pass
    logout(request)
    messages.success(request, "You have been logged in.")
    return redirect('login')

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('predict')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            create_notification(
                user=user,
                message="Welcome to our platform! Get started by exploring house listings.",
                link='/listings/',
                notification_type='welcome'
            )
            messages.success(request, "Account created successfully!")
            return redirect('predict')
    else:
        form = UserCreationForm()

    return render(request, 'registration/signup.html', {'form': form})

# Prediction
@login_required(login_url='login')
def predict(request):
    return render(request, 'home.html')

@login_required(login_url='login')
def result(request):
    if not model or housing_data is None:
        messages.error(request, "Prediction system not available")
        return redirect('home')

    try:
        # Now expecting 7 inputs
        inputs = [float(request.GET.get(f'n{i}', 0)) for i in range(1, 9)]

        # Enforce minimum value for Avg. Area Income (first input)
        MIN_INCOME = 75000
        if inputs[0] < MIN_INCOME:
            messages.warning(request, f"Average area income must be at least NPR {MIN_INCOME:,}")
            return redirect('predict')

        if any(x <= 0 for x in inputs):
            messages.warning(request, "Only positive numbers are allowed")
            return redirect('predict')


        # Clamp inputs to training min/max
        for i, col in enumerate([
            'Avg. Area Income', 'Avg. Area House Age',
            'Avg. Area Number of Rooms', 'Avg. Area Number of Bedrooms',
            'Area Population', 'Build-up Area', 'Land Area', 'Floor'
        ]):
            min_val = housing_data[col].min()
            max_val = housing_data[col].max()
            if inputs[i] < min_val:
                inputs[i] = min_val
            elif inputs[i] > max_val:
                inputs[i] = max_val

        inputs[7] = int(round(inputs[7])) 

        raw_pred = model.predict([inputs])[0]
        prediction = max(0, round(raw_pred, 2))  # Clamp to zero
        logger.info(f"Prediction inputs: {inputs}, output: {prediction}")

        df = housing_data.copy()
        df['distance'] = np.sqrt(
            (df['Avg. Area Income'] - inputs[0]) ** 2 +
            (df['Avg. Area House Age'] - inputs[1]) ** 2 +
            (df['Avg. Area Number of Rooms'] - inputs[2]) ** 2 +
            (df['Avg. Area Number of Bedrooms'] - inputs[3]) ** 2 +
            (df['Area Population'] - inputs[4]) ** 2 +
            (df['Build-up Area'] - inputs[5]) ** 2 +         
            (df['Land Area'] - inputs[6]) ** 2 +               
            (df['Floor'] - inputs[7]) ** 2
        )
        closest_row = df.loc[df['distance'].idxmin()]
        address = closest_row['Address']

        lower_bound = prediction * 0.9
        upper_bound = prediction * 1.1

        similar_rows = df[(df['Price'] >= lower_bound) & (df['Price'] <= upper_bound)].sort_values('distance').head(5)

        similar_predictions = []
        for _, row in similar_rows.iterrows():
            similar_predictions.append({
                'price': f"Npr {row['Price']:,.2f}",
                'address': row['Address'],
                'bedrooms': row['Avg. Area Number of Bedrooms'],
                'rooms': row['Avg. Area Number of Rooms'],
                'population': row['Area Population'],
                'buildup_area': row['Build-up Area'],    
                'land_area': row['Land Area'],          
            })

        # Example: Find houses with the same number of rooms, bedrooms, and house age
        rooms = inputs[2]
        bedrooms = inputs[3]
        house_age = inputs[1]

        matches = housing_data[
            (housing_data['Avg. Area Number of Rooms'] == rooms) &
            (housing_data['Avg. Area Number of Bedrooms'] == bedrooms) &
            (housing_data['Avg. Area House Age'] == house_age)
        ]

        print(matches[['Avg. Area Number of Rooms', 'Avg. Area Number of Bedrooms', 'Avg. Area House Age', 'Price']])

        metrics = load_evaluation_metrics()

        return render(request, 'predict.html', {
            'result': f"Npr {prediction:,.2f}",
            'inputs': inputs,
            'address': address,
            'metrics': metrics,
            'similar_predictions': similar_predictions
        })

    except ValueError:
        messages.error(request, "Please enter valid numbers")
        return redirect('predict')

    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        messages.error(request, "Prediction failed")
        return redirect('predict')


# Heatmap
@login_required(login_url='login')
def show_heatmap(request):
    try:
        df = housing_data.copy()
        corr = df.corr(numeric_only=True)

        plt.figure(figsize=(10, 8))
        sns.heatmap(corr, annot=True, cmap='coolwarm', fmt='.2f')
        plt.title('Feature Correlation Heatmap')

        heatmap_path = os.path.join(settings.BASE_DIR, 'static', 'heatmap.png')
        plt.savefig(heatmap_path)
        plt.close()

        return render(request, 'heatmap.html', {'heatmap_url': '/static/heatmap.png'})

    except Exception as e:
        logger.error(f"Heatmap generation failed: {str(e)}")
        messages.error(request, "Unable to generate heatmap.")
        return redirect('predict')

# Listings
@login_required(login_url='login')
def listings_view(request):
    query = request.GET.get('q', '')
    listings = HouseListing.objects.filter(on_sale=True)
    
    if query:
        listings = listings.filter(
            Q(title__icontains=query) |
            Q(location__icontains=query) |
            Q(description__icontains=query)
        )
    
    return render(request, 'listings.html', {
        'listings': listings,
        'search_query': query
    })

@login_required
def mark_for_sale(request, pk):
    house = get_object_or_404(HouseListing, pk=pk)
    house.on_sale = True
    house.save()
    messages.success(request, "House marked for sale successfully")
    return redirect('listings')

@login_required(login_url='login')
def house_detail(request, pk):
    house = get_object_or_404(HouseListing, pk=pk)
    has_pending_visit = ScheduleVisit.objects.filter(
        house=house,
        user=request.user,
        status='pending'
    ).exists()
    
    return render(request, 'house_detail.html', {
        'house': house,
        'has_pending_visit': has_pending_visit
    })

# Visit Scheduling
@login_required
def schedule_visit(request, house_id):
    house = get_object_or_404(HouseListing, id=house_id)

    if request.method == 'POST':
        visit_date_str = request.POST.get('visit_date')
        visit_time_str = request.POST.get('visit_time', '12:00')
        message = request.POST.get('message', '')

        try:
            visit_datetime = datetime.strptime(
                f"{visit_date_str} {visit_time_str}",
                "%Y-%m-%d %H:%M"
            )

            if visit_datetime.date() < datetime.now().date():
                messages.error(request, "Cannot schedule visits in the past.")
                return redirect('house_detail', pk=house.id)

            # Prevent duplicate visits within 10 seconds
            recent_visit = ScheduleVisit.objects.filter(
                house=house,
                user=request.user,
                scheduled_at__gte=datetime.now() - timedelta(seconds=10)
            ).exists()

            if recent_visit:
                messages.warning(request, "You already submitted a visit request just now.")
                return redirect('house_detail', pk=house.id)

            existing_visit = ScheduleVisit.objects.filter(
                house=house,
                user=request.user,
                status='pending'
            ).first()

            if existing_visit:
                messages.warning(request, "You already have a pending visit request for this property.")
                return redirect('house_detail', pk=house.id)

            with transaction.atomic():
                visit = ScheduleVisit.objects.create(
                    house=house,
                    user=request.user,
                    visit_date=visit_date_str,
                    visit_time=visit_time_str,
                    message=message,
                    status='pending'
                )

              # Notify admins
            admin_users = User.objects.filter(is_staff=True)
            admin_message = f"New visit request for {house.title} from {request.user.username}"

            for admin in admin_users:
                create_notification(
                    user=admin,
                    message=admin_message,
                    link=f'/admin/HousePricePrediction/schedulevisit/{visit.id}/change/',
                    notification_type='alert'
                )


            # Notify the user with a friendly link
            create_notification(
                user=request.user,
                message=f"Your visit request for {house.title} has been submitted and is pending approval.",
                link='/notifications/',
                notification_type='info'
            )

            messages.success(request, "Visit scheduled successfully. Waiting for admin approval.")
            return redirect('house_detail', pk=house.id)

        except ValueError as e:
            logger.error(f"Error parsing date/time: {str(e)}")
            messages.error(request, "Invalid date or time format.")
            return redirect('house_detail', pk=house.id)

    return redirect('house_detail', pk=house.id)
# Admin Views
@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_visit_approvals(request):
    status_filter = request.GET.get('status', 'pending')
    visits = ScheduleVisit.objects.all().order_by('visit_date')
    
    if status_filter == 'pending':
        visits = visits.filter(status='pending')
    elif status_filter == 'upcoming':
        visits = visits.filter(
            status='approved',
            visit_date__gte=datetime.now().date()
        )
    elif status_filter == 'completed':
        visits = visits.filter(
            Q(status='completed') |
            Q(status='rejected') |
            Q(status='cancelled') |
            Q(visit_date__lt=datetime.now().date())
        )
    
    return render(request, 'admin_visits.html', {
        'visits': visits,
        'status_filter': status_filter,
        'now': datetime.now().date()
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def approve_visit(request, visit_id):
    if request.method == 'POST':
        visit = get_object_or_404(ScheduleVisit, id=visit_id)
        admin_notes = request.POST.get('admin_notes', '')

        visit.status = 'approved'
        visit.admin_notes = admin_notes
        visit.save()

        message = f"Your visit to {visit.house.title} on {visit.visit_date} at {visit.visit_time} was approved!"
        create_notification(
            user=visit.user,
            message=message,
            link='/notifications/',
            notification_type='success'
        )

        messages.success(request, "Visit approved and notification sent.")
        return redirect('admin_visit_approvals')
    return redirect('admin_visit_approvals')

@login_required
@user_passes_test(lambda u: u.is_staff)
def reject_visit(request, visit_id):
    if request.method == 'POST':
        visit = get_object_or_404(ScheduleVisit, id=visit_id)
        admin_notes = request.POST.get('admin_notes', '')

        visit.status = 'rejected'
        visit.admin_notes = admin_notes
        visit.save()

        message = f"Your visit to {visit.house.title} was rejected. Reason: {admin_notes}"
        create_notification(
            user=visit.user,
            message=message,
            link='/notifications/',  # better fallback for users
            notification_type='alert'
        )

        messages.success(request, "Visit rejected and notification sent.")
        return redirect('admin_visit_approvals')
    return redirect('admin_visit_approvals')

# Notification Views
@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return render(request, 'notification_list.html', {
        'notifications': notifications,
        'now': datetime.now()
    })

@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect(notification.link) if notification.link else redirect('notifications')

@login_required
def clear_notifications(request):
    if request.method == 'POST':
        # Delete all notifications for the user
        Notification.objects.filter(user=request.user).delete()

        # Create a new notification for the user only
        create_notification(
            user=request.user,
            message="You have cleared all your notifications.",
            notification_type='info'
        )

        # If request was via AJAX, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})

        messages.success(request, "All notifications cleared.")
    
    return redirect('notifications')

# AJAX endpoints
@login_required
def check_visit_status(request, house_id):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        house = get_object_or_404(HouseListing, id=house_id)
        visits = ScheduleVisit.objects.filter(
            house=house,
            user=request.user
        ).order_by('-scheduled_at')
        
        if visits.exists():
            latest_visit = visits.first()
            return JsonResponse({
                'status': latest_visit.status,
                'admin_notes': latest_visit.admin_notes,
                'visit_date': latest_visit.visit_date.strftime('%Y-%m-%d'),
                'visit_time': str(latest_visit.visit_time) if latest_visit.visit_time else ''
            })
    
    return JsonResponse({'status': 'none'})

@login_required
def check_notifications(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
        recent_notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:5]
        
        notifications_data = [{
            'message': n.message,
            'is_read': n.is_read,
            'created_at': n.created_at.strftime('%b %d, %H:%M'),
            'link': n.link if n.link else '#'
        } for n in recent_notifications]
        
        return JsonResponse({
            'unread_count': unread_count,
            'notifications': notifications_data
        })
    return JsonResponse({})