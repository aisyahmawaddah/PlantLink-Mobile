from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
import json
import requests
import jwt
from datetime import datetime, timedelta
from django.conf import settings

# ─── WEBSITE VIEWS (render HTML templates) ───────────────────────────────────

def home(request):
    return render(request, 'home.html')

def logPlantFeed(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not email or not password:
            return render(request, 'logPlantFeed.html', {'warning_message': True})

        try:
            response = HttpResponseRedirect(reverse('home'))
            response.set_cookie('username', 'hafiy')
            response.set_cookie('email', 'hafiy@gmail.com')
            response.set_cookie('userlevel', 'manager')
            response.set_cookie('userid', '1')
            response.set_cookie('name', 'Hafiy Hakimi')
            return response
        except Exception:
            return render(request, 'logPlantFeed.html', {'warning_message': True})
    else:
        return render(request, 'logPlantFeed.html')

def logout(request):
    response = redirect('logPlantFeed')
    response.delete_cookie('username')
    response.delete_cookie('email')
    response.delete_cookie('userlevel')
    response.delete_cookie('userid')
    response.delete_cookie('name')
    return response

def profile(request):
    if 'username' in request.COOKIES:
        return render(request, 'profile.html')
    else:
        return redirect('logPlantFeed')

# ─── MOBILE API VIEWS (return JSON) ─────────────────────────────────────────

JWT_SECRET_KEY = settings.SECRET_KEY
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_TIME = timedelta(hours=1)

@csrf_exempt
def api_login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')
            if not email or not password:
                return JsonResponse({'error': 'Email and password are required'}, status=400)
            if email == 'hafiy@gmail.com' and password == 'hafiyhakimi11':
                return JsonResponse({
                    'message': 'Login successful',
                    'user': {
                        'username': 'hafiy',
                        'email': 'hafiy@gmail.com',
                        'userlevel': 'manager',
                        'userid': 1,
                        'name': 'Hafiy Hakimi',
                    }
                })
            return JsonResponse({'error': 'Invalid credentials'}, status=401)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def api_logout(request):
    return JsonResponse({'message': 'Logged out successfully'}, status=200)

@csrf_exempt
def api_profile(request):
    user_data = {
        'username': 'hafiy',
        'email': 'hafiy@gmail.com',
        'userlevel': 'manager',
        'userid': 1,
        'name': 'Hafiy'
    }
    return JsonResponse({'user': user_data}, status=200)
