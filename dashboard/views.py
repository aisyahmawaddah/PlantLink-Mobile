from datetime import datetime, time
import os
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import joblib
import pandas as pd
import requests
from plantlink.mongo_setup import connect_to_mongodb
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from dashboard.serializers import ChannelSerializer
from bson import ObjectId
import json

import pytz

def index(request):
    return HttpResponse("dashboard")

def convert_objectid_to_str(data):
    if isinstance(data, list):
        return [convert_objectid_to_str(item) for item in data]
    elif isinstance(data, dict):
        return {key: convert_objectid_to_str(value) for key, value in data.items()}
    elif isinstance(data, ObjectId):
        return str(data)
    return data

def get_channel_statistics(request):
    if request.method == 'GET':
        try:
            db, collection = connect_to_mongodb('Channel', 'dashboard')
            total_channels = collection.count_documents({})
            total_sensors = sum([
                len(channel.get('sensor', []))
                for channel in collection.find({}, {'sensor': 1})
            ])
            public_channels = collection.count_documents({'privacy': 'public'})
            return JsonResponse({
                "totalChannels": total_channels,
                "totalSensors": total_sensors,
                "publicChannels": public_channels
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

class ChannelList(APIView):
    def get(self, request):
        db, collection = connect_to_mongodb('Channel', 'dashboard')
        if collection is not None:
            channels = list(collection.find())
            channels = convert_objectid_to_str(channels)
            serializer = ChannelSerializer(channels, many=True)
            return Response(serializer.data)
        else:
            return Response({"error": "Failed to connect to MongoDB"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        serializer = ChannelSerializer(data=request.data)
        if serializer.is_valid():
            db, collection = connect_to_mongodb('Channel', 'dashboard')
            if collection is not None:
                collection.insert_one(serializer.validated_data)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({"error": "Failed to connect to MongoDB"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
def create_channel(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            channel_name = data.get('channel_name')
            description = data.get('description')
            location = data.get('location')
            privacy = data.get('privacy')
            if not channel_name or not description or not location or not privacy:
                return JsonResponse({'error': 'Missing required fields'}, status=400)
            db, collection = connect_to_mongodb('Channel', 'dashboard')
            if collection.find_one({"channel_name": channel_name}):
                return JsonResponse({'error': 'A channel with this name already exists.'}, status=400)
            now = datetime.now()
            formatted_date = now.strftime("%d/%m/%Y")
            channel = {
                "channel_name": channel_name,
                "description": description,
                "location": location,
                "privacy": privacy,
                "date_created": formatted_date,
                "date_modified": formatted_date,
                "allow_API": "",
                "API_KEY": "",
                "user_id": "",
                "sensor": []
            }
            collection.insert_one(channel)
            return JsonResponse({'message': 'Channel created successfully'}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def update_channel(request, channel_id):
    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            channel_name = data.get('channel_name')
            if not channel_name:
                return JsonResponse({'error': 'Channel name is required.'}, status=400)
            db, collection = connect_to_mongodb('Channel', 'dashboard')
            existing_channel = collection.find_one({
                "channel_name": channel_name,
                "_id": {"$ne": ObjectId(channel_id)}
            })
            if existing_channel:
                return JsonResponse({'error': 'A channel with this name already exists.'}, status=400)
            now = datetime.now()
            formatted_date = now.strftime("%d/%m/%Y")
            result = collection.update_one(
                {"_id": ObjectId(channel_id)},
                {"$set": {
                    "channel_name": data.get('channel_name'),
                    "description": data.get('description'),
                    "location": data.get('location'),
                    "privacy": data.get('privacy'),
                    "date_modified": formatted_date
                }}
            )
            if result.matched_count == 0:
                return JsonResponse({'error': 'Channel not found'}, status=404)
            return JsonResponse({'message': 'Channel updated successfully'}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def delete_channel(request, channel_id):
    if request.method == 'DELETE':
        try:
            db, collection = connect_to_mongodb('Channel', 'dashboard')
            result = collection.delete_one({"_id": ObjectId(channel_id)})
            if result.deleted_count == 0:
                return JsonResponse({'error': 'Channel not found'}, status=404)
            return JsonResponse({'message': 'Channel deleted successfully'}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def load_trained_model():
    model_path = os.path.join('static', 'dashboard', 'best_random_forest_model.pkl')
    if os.path.exists(model_path):
        try:
            model = joblib.load(model_path)
            return model
        except Exception as e:
            print("Error loading the trained model:", str(e))
            return None
    else:
        print("Model file not found.")
        return None

def getDashboardData(request, channel_id):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})
        if channel:
            API_KEY = channel.get('API_KEY', '')
            if not API_KEY:
                return JsonResponse({"success": False, "error": "No API_KEY found for the channel"})
            ph_values = []
            timestamps = []
            rainfall_values = []
            rainfall_timestamps = []
            humid_values = []
            temp_values = []
            nitrogen_values = []
            potassium_values = []
            phosphorous_values = []
            timestamps_humid_temp = []
            timestamps_NPK = []
            updated_sensor_array = []
            db_humid_temp, collection_humid_temp = connect_to_mongodb('sensor', 'DHT11')
            if db_humid_temp is not None and collection_humid_temp is not None:
                humid_temp_data = collection_humid_temp.find_one({"API_KEY": API_KEY})
                if humid_temp_data:
                    updated_sensor_array.append({
                        "sensor_id": str(humid_temp_data.get('_id')),
                        "sensor_type": "DHT11",
                        "sensor_data_count": len(humid_temp_data.get('sensor_data', []))
                    })
                    for data_point in humid_temp_data.get('sensor_data', []):
                        humid_values.append(data_point.get('humidity_value', ''))
                        temp_values.append(data_point.get('temperature_value', ''))
                        timestamp_obj = data_point.get('timestamp', datetime.utcnow())
                        formatted_timestamp = timestamp_obj.astimezone(pytz.utc).strftime('%d-%m-%Y')
                        timestamps_humid_temp.append(formatted_timestamp)
            db_NPK, collection_NPK = connect_to_mongodb('sensor', 'NPK')
            if db_NPK is not None and collection_NPK is not None:
                NPK_data = collection_NPK.find_one({"API_KEY": API_KEY})
                if NPK_data:
                    updated_sensor_array.append({
                        "sensor_id": str(NPK_data.get('_id')),
                        "sensor_type": "NPK",
                        "sensor_data_count": len(NPK_data.get('sensor_data', []))
                    })
                    for data_point in NPK_data.get('sensor_data', []):
                        nitrogen_values.append(data_point.get('nitrogen_value', ''))
                        phosphorous_values.append(data_point.get('phosphorous_value', ''))
                        potassium_values.append(data_point.get('potassium_value', ''))
                        timestamp_obj = data_point.get('timestamp', datetime.utcnow())
                        formatted_timestamp = timestamp_obj.astimezone(pytz.utc).strftime('%d-%m-%Y')
                        timestamps_NPK.append(formatted_timestamp)
            db_ph, collection_ph = connect_to_mongodb('sensor', 'PHSensor')
            if db_ph is not None and collection_ph is not None:
                ph_data = collection_ph.find_one({"API_KEY": API_KEY})
                if ph_data:
                    updated_sensor_array.append({
                        "sensor_id": str(ph_data.get('_id')),
                        "sensor_type": "PHSensor",
                        "sensor_data_count": len(ph_data.get('sensor_data', []))
                    })
                    for data_point in ph_data.get('sensor_data', []):
                        ph_values.append(data_point.get('ph_value', ''))
                        timestamp_obj = data_point.get('timestamp', datetime.utcnow())
                        formatted_timestamp = timestamp_obj.astimezone(pytz.utc).strftime('%d-%m-%Y')
                        timestamps.append(formatted_timestamp)
            db_rainfall, collection_rainfall = connect_to_mongodb('sensor', 'rainfall')
            if db_rainfall is not None and collection_rainfall is not None:
                rainfall_data = collection_rainfall.find_one({"API_KEY": API_KEY})
                if rainfall_data:
                    updated_sensor_array.append({
                        "sensor_id": str(rainfall_data.get('_id')),
                        "sensor_type": "DHT11",
                        "sensor_data_count": len(rainfall_data.get('sensor_data', []))
                    })
                    for data_point in rainfall_data.get('sensor_data', []):
                        rainfall_values.append(data_point.get('rainfall_value', ''))
                        timestamp_obj = data_point.get('timestamp', datetime.utcnow())
                        formatted_timestamp = timestamp_obj.astimezone(pytz.utc).strftime('%d-%m-%Y')
                        rainfall_timestamps.append(formatted_timestamp)
            collection.update_one({"_id": _id}, {"$set": {"sensor": updated_sensor_array}})
            context = {
                "channel_id": channel_id,
                "ph_values": ph_values,
                "timestamps": timestamps,
                "rainfall_values": rainfall_values,
                "rainfall_timestamps": rainfall_timestamps,
                "humid_values": humid_values,
                "temp_values": temp_values,
                "timestamps_humid_temp": timestamps_humid_temp,
                "nitrogen_values": nitrogen_values,
                "phosphorous_values": phosphorous_values,
                "potassium_values": potassium_values,
                "timestamps_NPK": timestamps_NPK,
                "API": API_KEY,
            }
            phosphorous_value = phosphorous_values
            if humid_values or ph_values or rainfall_values or nitrogen_values or potassium_values or phosphorous_value or temp_values:
                model = load_trained_model()
                if model:
                    input_data = {
                        'N': float(nitrogen_values[-1]) if nitrogen_values else 0.0,
                        'P': float(potassium_values[-1]) if potassium_values else 0.0,
                        'K': float(phosphorous_values[-1]) if phosphorous_values else 0.0,
                        'temperature': float(temp_values[-1]) if temp_values else 0.0,
                        'humidity': float(humid_values[-1]) if humid_values else 0.0,
                        'ph': float(ph_values[-1]) if ph_values else 0.0,
                        'rainfall': float(rainfall_values[-1]) if rainfall_values else 0.0,
                    }
                    input_df = pd.DataFrame([input_data])
                    prediction = model.predict(input_df)
                    probabilities = model.predict_proba(input_df)
                    labels = model.classes_
                    crop_recommendations = [
                        {"crop": label, "accuracy": prob * 100}
                        for label, prob in zip(labels, probabilities[0])
                    ]
                    crop_recommendations.sort(key=lambda x: x["accuracy"], reverse=True)
                    context["crop_recommendations"] = crop_recommendations
            return JsonResponse(context)
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")
        return JsonResponse({"success": False, "error": "Database connection error"})

def render_embed_code(request, channel_id):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})
        if channel:
            channel_privacy = channel.get('privacy', '')
            if channel_privacy == "public":
                channel_name = channel.get('channel_name', '')
                description = channel.get('description', '')
                API_KEY = channel.get('API_KEY', '')
                soil_location = channel.get("location", '')
                graph_count = 0
                if API_KEY:
                    dht_db, dht_collection = connect_to_mongodb('sensor', 'DHT11')
                    if dht_db is not None and dht_collection is not None:
                        if dht_collection.find_one({"API_KEY": API_KEY}):
                            graph_count += 2
                    NPK_db, NPK_collection = connect_to_mongodb('sensor', 'NPK')
                    if NPK_db is not None and NPK_collection is not None:
                        if NPK_collection.find_one({"API_KEY": API_KEY}):
                            graph_count += 3
                    ph_db, ph_collection = connect_to_mongodb('sensor', 'PHSensor')
                    if ph_db is not None and ph_collection is not None:
                        if ph_collection.find_one({"API_KEY": API_KEY}):
                            graph_count += 1
                    rainfall_db, rainfall_collection = connect_to_mongodb('sensor', 'rainfall')
                    if rainfall_db is not None and rainfall_collection is not None:
                        if rainfall_collection.find_one({"API_KEY": API_KEY}):
                            graph_count += 1
                context = {
                    "channel_name": channel_name,
                    "description": description,
                    "channel_id": channel_id,
                    "API": API_KEY,
                    "graph_count": graph_count,
                    "soil_location": soil_location
                }
                return render(request, 'embed_dashboard.html', context)
            else:
                return JsonResponse({"success": False, "error": "Dashboard is not public"})
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")


@csrf_exempt
def share_channel(request, channel_id):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')

    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})
        if channel:
            # Read plantfeed_user_id from Flutter request body (default "1" for backward compat)
            plantfeed_user_id = "1"
            if request.body:
                try:
                    body = json.loads(request.body)
                    plantfeed_user_id = str(body.get('plantfeed_user_id', '1'))
                except (json.JSONDecodeError, KeyError):
                    pass

            plantfeed_link = settings.PLANTFEED_BASE_URL + "/group/PlantLink-Graph-API"
            plantlink_base = settings.PLANTLINK_BASE_URL
            channel_name = channel.get('channel_name', 'Unknown Channel')

            channel_data = {
                "userid": plantfeed_user_id,
                "chart_name": f"Channel: {channel_name}",
                "embed_link": f"{plantlink_base}/mychannel/embed/channel/{channel_id}/",
                "chart_type": "Channel",
                "start_date": "2025-01-01",
                "end_date": "2025-01-14"
            }

            headers = {'Content-Type': 'application/json'}

            try:
                response = requests.post(plantfeed_link, json=channel_data, headers=headers)
                if response.status_code == 200:
                    return JsonResponse({"success": "Channel successfully sent to PlantFeed"}, status=200)
                else:
                    return JsonResponse({"error": f"Failed to share channel. PlantFeed Response: {response.text}"}, status=response.status_code)
            except requests.RequestException as e:
                return JsonResponse({"error": f"Failed to send request to PlantFeed: {str(e)}"}, status=500)
        else:
            return JsonResponse({"error": "Document not found"}, status=404)
    else:
        return JsonResponse({"error": "Database connection error"}, status=500)


@csrf_exempt
def share_chart(request, channel_id, chart_type, start_date, end_date, chart_name):
    try:
        _id = ObjectId(channel_id)
        db, collection = connect_to_mongodb('Channel', 'dashboard')
        if db is None or collection is None:
            return JsonResponse({"error": "Failed to connect to MongoDB."}, status=500)

        channel = collection.find_one({"_id": _id})
        if not channel:
            return JsonResponse({"error": "Channel not found."}, status=404)

        # Read plantfeed_user_id from Flutter request body (default "1" for backward compat)
        plantfeed_user_id = "1"
        if request.body:
            try:
                body = json.loads(request.body)
                plantfeed_user_id = str(body.get('plantfeed_user_id', '1'))
            except (json.JSONDecodeError, KeyError):
                pass

        plantfeed_link = settings.PLANTFEED_BASE_URL + "/group/PlantLink-Graph-API"
        plantlink_base = settings.PLANTLINK_BASE_URL
        embed_link = f"{plantlink_base}/mychannel/embed/channel/{channel_id}/{chart_type}Chart/{start_date}/{end_date}/"

        channel_data = {
            "userid": plantfeed_user_id,
            "chart_name": chart_name,
            "chart_type": chart_type,
            "start_date": start_date,
            "end_date": end_date,
            "embed_link": embed_link,
        }

        headers = {'Content-Type': 'application/json'}
        response = requests.post(plantfeed_link, json=channel_data, headers=headers)

        if response.status_code == 200:
            return JsonResponse({"success": f"{chart_type} chart successfully sent to PlantFeed."}, status=200)
        else:
            return JsonResponse({
                "error": f"Failed to share {chart_type} chart. PlantFeed Response: {response.text}",
                "status_code": response.status_code
            }, status=500)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def render_chart(request, channel_id, start_date, end_date, template_name):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is None or collection is None:
        return JsonResponse({"success": False, "error": "Error connecting to MongoDB."})
    channel = collection.find_one({"_id": _id})
    if not channel:
        return JsonResponse({"success": False, "error": "Document not found"})
    if channel.get('privacy', '') != "public":
        return JsonResponse({"success": False, "error": "Dashboard is not public"})
    context = {
        "channel_name": channel.get('channel_name', ''),
        "description": channel.get('description', ''),
        "channel_id": channel_id,
        "API": channel.get('API_KEY', ''),
        "graph_count": 1,
        "start_date": start_date,
        "end_date": end_date
    }
    return render(request, template_name, context)

def render_ph_chart(request, channel_id, start_date, end_date):
    return render_chart(request, channel_id, start_date, end_date, 'embed_ph_chart.html')

def render_rainfall_chart(request, channel_id, start_date, end_date):
    return render_chart(request, channel_id, start_date, end_date, 'embed_rainfall_chart.html')

def render_humidity_chart(request, channel_id, start_date, end_date):
    return render_chart(request, channel_id, start_date, end_date, 'embed_humid_chart.html')

def render_temperature_chart(request, channel_id, start_date, end_date):
    return render_chart(request, channel_id, start_date, end_date, 'embed_temperature_chart.html')

def render_nitrogen_chart(request, channel_id, start_date, end_date):
    return render_chart(request, channel_id, start_date, end_date, 'embed_nitrogen_chart.html')

def render_phosphorous_chart(request, channel_id, start_date, end_date):
    return render_chart(request, channel_id, start_date, end_date, 'embed_phosphorous_chart.html')

def render_potassium_chart(request, channel_id, start_date, end_date):
    return render_chart(request, channel_id, start_date, end_date, 'embed_potassium_chart.html')

def getHumidityTemperatureData(request, channel_id, start_date, end_date):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})
        if channel:
            humid_values = []
            temp_values = []
            timestamps_humid_temp = []
            API = channel.get('API_KEY', '')
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            db_humid_temp, collection_humid_temp = connect_to_mongodb('sensor', 'DHT11')
            if db_humid_temp is not None and collection_humid_temp is not None:
                humid_temp_data = collection_humid_temp.find_one({"API_KEY": API})
                if humid_temp_data:
                    for data_point in humid_temp_data.get('sensor_data', []):
                        timestamp_obj = data_point.get('timestamp', datetime.utcnow())
                        if start_date <= timestamp_obj <= end_date:
                            humid_values.append(data_point.get('humidity_value', ''))
                            temp_values.append(data_point.get('temperature_value', ''))
                            formatted_timestamp = timestamp_obj.astimezone(pytz.utc).strftime('%d-%m-%Y')
                            timestamps_humid_temp.append(formatted_timestamp)
            context = {
                "channel_id": channel_id,
                "humid_values": humid_values,
                "temp_values": temp_values,
                "timestamps_humid_temp": timestamps_humid_temp,
                "API": API,
            }
            return JsonResponse(context)
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")

def getNPKData(request, channel_id, start_date, end_date):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})
        if channel:
            nitrogen_values = []
            phosphorous_values = []
            potassium_values = []
            timestamps_NPK = []
            API = channel.get('API_KEY', '')
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            db_NPK, collection_NPK = connect_to_mongodb('sensor', 'NPK')
            if db_NPK is not None and collection_NPK is not None:
                NPK_data = collection_NPK.find_one({"API_KEY": API})
                if NPK_data:
                    for data_point in NPK_data.get('sensor_data', []):
                        timestamp_obj = data_point.get('timestamp', datetime.utcnow())
                        if start_date <= timestamp_obj <= end_date:
                            nitrogen_values.append(data_point.get('nitrogen_value', ''))
                            phosphorous_values.append(data_point.get('phosphorous_value', ''))
                            potassium_values.append(data_point.get('potassium_value', ''))
                            formatted_timestamp = timestamp_obj.astimezone(pytz.utc).strftime('%d-%m-%Y')
                            timestamps_NPK.append(formatted_timestamp)
            context = {
                "channel_id": channel_id,
                "nitrogen_values": nitrogen_values,
                "phosphorous_values": phosphorous_values,
                "potassium_values": potassium_values,
                "timestamps_NPK": timestamps_NPK,
                "API": API,
            }
            return JsonResponse(context)
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")

def getPHData(request, channel_id, start_date, end_date):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})
        if channel:
            ph_values = []
            timestamps = []
            API = channel.get('API_KEY', '')
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            db_ph, collection_ph = connect_to_mongodb('sensor', 'PHSensor')
            if db_ph is not None and collection_ph is not None:
                ph_data = collection_ph.find_one({"API_KEY": API})
                if ph_data:
                    for data_point in ph_data.get('sensor_data', []):
                        ph_values.append(data_point.get('ph_value', ''))
                        timestamp_obj = data_point.get('timestamp', datetime.utcnow())
                        formatted_timestamp = timestamp_obj.astimezone(pytz.utc).strftime('%d-%m-%Y')
                        timestamps.append(formatted_timestamp)
            context = {
                "channel_id": channel_id,
                "ph_values": ph_values,
                "timestamps": timestamps,
                "API": API,
            }
            return JsonResponse(context)
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")

def getRainfallData(request, channel_id, start_date, end_date):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})
        if channel:
            rainfall_values = []
            rainfall_timestamps = []
            API = channel.get('API_KEY', '')
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            db_rainfall, collection_rainfall = connect_to_mongodb('sensor', 'rainfall')
            if db_rainfall is not None and collection_rainfall is not None:
                rainfall_data = collection_rainfall.find_one({"API_KEY": API})
                if rainfall_data:
                    for data_point in rainfall_data.get('sensor_data', []):
                        rainfall_values.append(data_point.get('rainfall_value', ''))
                        timestamp_obj = data_point.get('timestamp', datetime.utcnow())
                        formatted_timestamp = timestamp_obj.astimezone(pytz.utc).strftime('%d-%m-%Y')
                        rainfall_timestamps.append(formatted_timestamp)
            context = {
                "channel_id": channel_id,
                "rainfall_values": rainfall_values,
                "timestamps": rainfall_timestamps,
                "API": API,
            }
            return JsonResponse(context)
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")

@csrf_exempt
def add_sensor(request, channel_id):
    if request.method == 'POST':
        API_KEY = request.POST.get('apiKey')
        db_channel, collection_channel = connect_to_mongodb('Channel', 'dashboard')
        _id = ObjectId(channel_id)
        filter_criteria = {'_id': _id}
        sensors = [
            {"name": "DHT11", "db_name": "DHT11"},
            {"name": "NPK", "db_name": "NPK"},
            {"name": "PHSensor", "db_name": "PHSensor"},
            {"name": "Rainfall", "db_name": "rainfall"}
        ]
        matching_sensors = []
        for sensor in sensors:
            sensor_db, sensor_collection = connect_to_mongodb('sensor', sensor['db_name'])
            if sensor_db is not None and sensor_collection is not None:
                sensor_data = sensor_collection.find({'API_KEY': API_KEY})
                for data in sensor_data:
                    matching_sensors.append({
                        'sensor_id': str(data.get('_id')),
                        'sensor_type': data.get('sensor_type', 'Unknown Type'),
                        'sensor_data_count': len(data.get('sensor_data', [])),
                    })
        if matching_sensors:
            collection_channel.update_one(
                filter_criteria,
                {'$set': {'API_KEY': API_KEY, 'allow_API': "permit", 'sensor': matching_sensors}}
            )
            return redirect('view_channel_sensor', channel_id=channel_id)
        else:
            return render(request, 'add_sensor.html', {
                'channel_id': channel_id,
                'error': 'No sensors found with the provided API_KEY.'
            })
    else:
        _id = ObjectId(channel_id)
        db, collection = connect_to_mongodb('Channel', 'dashboard')
        if db is not None and collection is not None:
            channel = collection.find_one({"_id": _id})
            if channel:
                sensor_api = channel.get('API_KEY', '')
                context = {"channel_id": channel_id, "API_KEY": sensor_api}
                return render(request, 'add_sensor.html', context)
            else:
                context = {"channel_id": channel_id}
                return render(request, 'add_sensor.html', context)

def manage_sensor(request, channel_id):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})
        if channel:
            sensor_api = channel.get('API_KEY', '')
            sensor_list = []
            if not sensor_api:
                return JsonResponse({"error": "No API key set for this channel"}, status=400)
            else:
                sensors = [
                    {"name": "DHT11", "db_name": "DHT11"},
                    {"name": "PHSensor", "db_name": "PHSensor"},
                    {"name": "NPK", "db_name": "NPK"},
                    {"name": "Rainfall", "db_name": "rainfall"}
                ]
                for sensor in sensors:
                    sensor_db, sensor_collection = connect_to_mongodb('sensor', sensor['db_name'])
                    if sensor_db is not None and sensor_collection is not None:
                        sensor_data = sensor_collection.find_one({"API_KEY": sensor_api})
                        if sensor_data:
                            sensor_list.append({
                                "sensor_id": str(sensor_data.get('_id')),
                                "sensor_name": sensor_data.get('sensor_name'),
                                "sensor_type": sensor_data.get('sensor_type'),
                                "sensor_data_count": len(sensor_data.get('sensor_data', []))
                            })
            return JsonResponse({
                "channel_id": channel_id,
                "sensors": sensor_list,
                "API_KEY_VALUE": sensor_api
            })
    return JsonResponse({"error": "Channel not found"}, status=404)

@csrf_exempt
def unset_sensor(request, channel_id):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({'_id': _id})
        if channel:
            collection.update_one({'_id': _id}, {'$set': {'API_KEY': '', 'sensor': []}})
            return JsonResponse({"success": True, "message": "API_KEY unset successfully."})
        else:
            return JsonResponse({"success": False, "error": "Channel document not found."}, status=404)
    else:
        return JsonResponse({"error": "Database connection error"}, status=500)

@csrf_exempt
def delete_sensor(request, channel_id, sensor_type):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({'_id': _id})
        if channel:
            api_key = channel.get('API_KEY', '')
            if api_key:
                sensor_collections = {
                    "DHT11": ('sensor', 'DHT11'),
                    "NPK": ('sensor', 'NPK'),
                    "ph_sensor": ('sensor', 'PHSensor'),
                    "rainfall": ('sensor', 'rainfall')
                }
                if sensor_type in sensor_collections:
                    sensor_db_name, sensor_collection_name = sensor_collections[sensor_type]
                    sensor_db, sensor_collection = connect_to_mongodb(sensor_db_name, sensor_collection_name)
                    delete_action = sensor_collection.find_one({"API_KEY": api_key})
                    if delete_action:
                        sensor_collection.delete_one({"API_KEY": api_key})
                        collection.update_one({'_id': _id}, {'$pull': {'sensor': {'sensor_type': sensor_type}}})
                        return redirect('view_channel_sensor', channel_id=channel_id)
                    else:
                        return JsonResponse({"success": False, "error": f"{sensor_type} sensor document not found."}, status=404)
                else:
                    return JsonResponse({"success": False, "error": "Invalid sensor type."}, status=400)
            else:
                return JsonResponse({"success": False, "error": "API_KEY not set for this channel."}, status=400)
        else:
            return JsonResponse({"success": False, "error": "Channel document not found."}, status=404)
    else:
        return JsonResponse({"error": "Database connection error"}, status=500)

@csrf_exempt
def edit_sensor(request, sensor_type, sensor_id, channel_id):
    if request.method == 'POST':
        sensor_name = request.POST.get('sensorName')
        sensor_type = request.POST.get('sensorType')
        API_KEY = request.POST.get('ApiKey')
        sensor_db_map = {
            "DHT11": ('sensor', 'DHT11'),
            "ph_sensor": ('sensor', 'PHSensor'),
            "NPK": ('sensor', 'NPK'),
            "rainfall": ('sensor', 'rainfall'),
        }
        if sensor_type in sensor_db_map:
            db_name, col_name = sensor_db_map[sensor_type]
            db, collection = connect_to_mongodb(db_name, col_name)
            if db is not None and collection is not None:
                _id = ObjectId(sensor_id)
                result = collection.update_one({"_id": _id}, {"$set": {"sensor_name": sensor_name}})
                if result.modified_count > 0:
                    return redirect('manage_sensor', channel_id=channel_id)
                else:
                    return redirect('view_channel_sensor', channel_id=channel_id)
    else:
        sensor_db_map = {
            "DHT11": ('sensor', 'DHT11'),
            "ph_sensor": ('sensor', 'PHSensor'),
            "NPK": ('sensor', 'NPK'),
            "rainfall": ('sensor', 'rainfall'),
        }
        if sensor_type in sensor_db_map:
            db_name, col_name = sensor_db_map[sensor_type]
            db, collection = connect_to_mongodb(db_name, col_name)
            _id = ObjectId(sensor_id)
            sensor = collection.find_one({"_id": _id})
            if sensor:
                context = {
                    "channel_id": channel_id,
                    "sensor_name": sensor.get("sensor_name", ""),
                    "sensor_type": sensor_type,
                    "API_KEY": sensor.get("API_KEY", ''),
                }
                return render(request, 'edit_sensor.html', context)
            else:
                return JsonResponse({"success": False, "error": "Channel not found"})
    return JsonResponse({"success": False, "error": "Invalid request method"})

@csrf_exempt
def forbid_API(request, channel_id):
    if request.method == 'POST':
        db, collection = connect_to_mongodb('Channel', 'dashboard')
        _id = ObjectId(channel_id)
        filter_criteria = {'_id': _id}
        update_result = collection.update_one(filter_criteria, {'$set': {'allow_API': 'not permitted'}})
        if update_result.modified_count > 0:
            return JsonResponse({'message': 'API access forbidden successfully'}, status=200)
        else:
            return JsonResponse({'error': 'Failed to update API access'}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def permit_API(request, channel_id):
    if request.method == 'POST':
        db, collection = connect_to_mongodb('Channel', 'dashboard')
        _id = ObjectId(channel_id)
        filter_criteria = {'_id': _id}
        update_result = collection.update_one(filter_criteria, {'$set': {'allow_API': 'permit'}})
        if update_result.modified_count > 0:
            return JsonResponse({'message': 'API access permitted successfully'}, status=200)
        else:
            return JsonResponse({'error': 'Failed to update API access'}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
