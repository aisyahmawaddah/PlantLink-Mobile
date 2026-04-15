from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import requests
from datetime import timedelta

# ── PlantFeed Login URL ────────────────────────────────────────────────────
PLANTFEED_LOGIN_URL = "https://kourtney-bottlelike-earthly.ngrok-free.dev/plantlink/Login/"

# ── WEBSITE VIEWS (HTML) ───────────────────────────────────────────────────

def home(request):
    return render(request, 'home.html')

def logPlantFeed(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not email or not password:
            return render(request, 'logPlantFeed.html', {'warning_message': True})

        try:
            response = requests.post(
                PLANTFEED_LOGIN_URL,
                json={'email': email, 'password': password},
                headers={
                    'Content-Type': 'application/json',
                    'ngrok-skip-browser-warning': 'true'
                },
                timeout=10
            )
            response_data = response.json()
            user_details = response_data.get('user', {})
            username = user_details.get('username', '')

            if username:
                resp = HttpResponseRedirect(reverse('home'))
                resp.set_cookie('username', username)
                resp.set_cookie('email', user_details.get('email', ''))
                resp.set_cookie('userlevel', user_details.get('userlevel', ''))
                resp.set_cookie('userid', str(user_details.get('userid', '')))
                resp.set_cookie('name', user_details.get('name', ''))
                return resp
            else:
                return render(request, 'logPlantFeed.html', {'warning_message': True})

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

# ── MOBILE API VIEWS (JSON) ────────────────────────────────────────────────

@csrf_exempt
def api_login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')

            if not email or not password:
                return JsonResponse({'error': 'Email and password are required'}, status=400)

            response = requests.post(
                PLANTFEED_LOGIN_URL,
                json={'email': email, 'password': password},
                headers={
                    'Content-Type': 'application/json',
                    'ngrok-skip-browser-warning': 'true'
                },
                timeout=10
            )
            response_data = response.json()
            user_details = response_data.get('user', {})
            username = user_details.get('username', '')

            if username:
                return JsonResponse({
                    'message': 'Login successful',
                    'user': {
                        'username': username,
                        'email': user_details.get('email', ''),
                        'userlevel': user_details.get('userlevel', ''),
                        'userid': str(user_details.get('userid', '')),
                        'name': user_details.get('name', ''),
                    }
                }, status=200)
            else:
                return JsonResponse({'error': 'Invalid credentials'}, status=401)

        except requests.exceptions.Timeout:
            return JsonResponse({'error': 'Authentication server timed out'}, status=504)
        except requests.exceptions.RequestException:
            return JsonResponse({'error': 'Cannot reach authentication server'}, status=503)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON payload'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def api_logout(request):
    return JsonResponse({'message': 'Logged out successfully'}, status=200)

@csrf_exempt
def api_profile(request):
    return JsonResponse({'message': 'Profile endpoint'}, status=200)
