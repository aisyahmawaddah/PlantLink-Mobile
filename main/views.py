from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
import json
import requests

PLANTFEED_LOGIN_URL = "https://kourtney-bottlelike-earthly.ngrok-free.dev/plantlink/Login/"

@csrf_exempt
def home(request):
    return render(request, 'home.html')

# ── WEBSITE ROUTES ────────────────────────────────────────────────────────────

@csrf_exempt
def logPlantFeed(request):
    """Website login: calls PlantFeed, sets cookies, redirects to /mychannel/"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        if not email or not password:
            return render(request, 'logPlantFeed.html', {'error': 'Email and password required'})

        try:
            pf_response = requests.post(
                PLANTFEED_LOGIN_URL,
                json={'email': email, 'password': password},
                headers={
                    'Content-Type': 'application/json',
                    'ngrok-skip-browser-warning': 'true'
                },
                timeout=10
            )
        except requests.RequestException:
            return render(request, 'logPlantFeed.html', {'error': 'Cannot reach PlantFeed. Try again.'})

        if pf_response.status_code == 200:
            user_data = pf_response.json()
            response = redirect('/mychannel/')
            response.set_cookie('userid', str(user_data.get('userid', '')))
            response.set_cookie('username', user_data.get('username', ''))
            response.set_cookie('email', user_data.get('email', ''))
            return response
        else:
            return render(request, 'logPlantFeed.html', {'error': 'Invalid credentials'})
    return render(request, 'logPlantFeed.html')

def logout(request):
    response = redirect('/login/')
    response.delete_cookie('userid')
    response.delete_cookie('username')
    response.delete_cookie('email')
    return response

def profile(request):
    return render(request, 'profile.html')

# ── MOBILE API ROUTES ─────────────────────────────────────────────────────────

@csrf_exempt
def api_login(request):
    """Mobile login: calls PlantFeed, returns real user JSON"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        if not email or not password:
            return JsonResponse({'error': 'Email and password are required'}, status=400)

        pf_response = requests.post(
            PLANTFEED_LOGIN_URL,
            json={'email': email, 'password': password},
            headers={
                'Content-Type': 'application/json',
                'ngrok-skip-browser-warning': 'true'
            },
            timeout=10
        )

        if pf_response.status_code == 200:
            user_data = pf_response.json()
            return JsonResponse({'message': 'Login successful', 'user': user_data})
        else:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)

    except requests.RequestException as e:
        return JsonResponse({'error': f'Cannot reach PlantFeed: {str(e)}'}, status=503)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)

@csrf_exempt
def api_logout(request):
    return JsonResponse({'message': 'Logged out successfully'})

@csrf_exempt
def api_profile(request):
    userid = request.COOKIES.get('userid', '')
    username = request.COOKIES.get('username', '')
    email = request.COOKIES.get('email', '')
    return JsonResponse({'user': {'userid': userid, 'username': username, 'email': email}})
