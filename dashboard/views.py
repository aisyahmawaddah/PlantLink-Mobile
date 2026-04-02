from datetime import datetime, time
import os
from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
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
# Helper function to convert ObjectId to string recursively
def convert_objectid_to_str(data):
    if isinstance(data, list):  # If the data is a list, apply to each item
        return [convert_objectid_to_str(item) for item in data]
    elif isinstance(data, dict):  # If the data is a dictionary, apply to each value
        return {key: convert_objectid_to_str(value) for key, value in data.items()}
    elif isinstance(data, ObjectId):  # If it's an ObjectId, convert it to string
        return str(data)
    return data  # Return the data if it's neither a list, dict, nor ObjectId

def get_channel_statistics(request):
    if request.method == 'GET':
        try:
            # Connect to MongoDB
            db, collection = connect_to_mongodb('Channel', 'dashboard')
            
            # Get total channels
            total_channels = collection.count_documents({})
            
            # Get total sensors
            total_sensors = sum([
                len(channel.get('sensor', []))
                for channel in collection.find({}, {'sensor': 1})
            ])
            
            # Get total public channels
            public_channels = collection.count_documents({'privacy': 'public'})
            
            # Return the statistics
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
        # Connect to MongoDB
        db, collection = connect_to_mongodb('Channel', 'dashboard')
        
        if collection is not None:
            channels = list(collection.find())  # Fetch all channels from MongoDB

            # Convert ObjectId to string in the fetched data
            channels = convert_objectid_to_str(channels)

            # Serialize the data using the ChannelSerializer
            serializer = ChannelSerializer(channels, many=True)

            # Return the serialized data as a response
            return Response(serializer.data)
        else:
            return Response({"error": "Failed to connect to MongoDB"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        # Validate incoming data using the ChannelSerializer
        serializer = ChannelSerializer(data=request.data)
        if serializer.is_valid():
            # If valid, insert the data directly into MongoDB
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
            # Parse the incoming JSON data
            data = json.loads(request.body)

            # Extract channel details
            channel_name = data.get('channel_name')
            description = data.get('description')
            location = data.get('location')
            privacy = data.get('privacy')

            # Validation (optional, can be improved further)
            if not channel_name or not description or not location or not privacy:
                return JsonResponse({'error': 'Missing required fields'}, status=400)

            # Connect to MongoDB
            db, collection = connect_to_mongodb('Channel', 'dashboard')

            # Check if a channel with the same name already exists
            if collection.find_one({"channel_name": channel_name}):
                return JsonResponse(
                    {'error': 'A channel with this name already exists.'},
                    status=400
                )

            # Insert into MongoDB with formatted date
            now = datetime.now()
            formatted_date = now.strftime("%d/%m/%Y")  # Format to DD/MM/YYYY
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
                "sensor": []  # Initialize with an empty sensor list
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
            # Parse the incoming data
            data = json.loads(request.body)
            channel_name = data.get('channel_name')

            if not channel_name:
                return JsonResponse({'error': 'Channel name is required.'}, status=400)

            # Connect to MongoDB
            db, collection = connect_to_mongodb('Channel', 'dashboard')

            existing_channel = collection.find_one({
                "channel_name": channel_name,
                "_id": {"$ne": ObjectId(channel_id)}  # Exclude the current channel from the check
            })
            
            # Check if a channel with the same name already exists
            if existing_channel:
                return JsonResponse(
                    {'error': 'A channel with this name already exists.'},
                    status=400
                )

            # Find the channel and update it
            now = datetime.now()
            formatted_date = now.strftime("%d/%m/%Y")
            result = collection.update_one(
                {"_id": ObjectId(channel_id)},  # Match the channel by its ID
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
            # Connect to MongoDB
            db, collection = connect_to_mongodb('Channel', 'dashboard')

            # Find the channel by ID and delete it
            result = collection.delete_one({"_id": ObjectId(channel_id)})

            if result.deleted_count == 0:
                return JsonResponse({'error': 'Channel not found'}, status=404)

            return JsonResponse({'message': 'Channel deleted successfully'}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

#test

# To train model - DONE
def load_trained_model():
    model_path = os.path.join('static', 'dashboard', 'best_random_forest_model.pkl')
    # model_path = '/home/shiroooo/PlantLink/static/dashboard/best_random_forest_model.pkl'
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

# To render dashboard data dynamically - DONE (New)
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
            
            # Fetch data from sensor:DHT11
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
                        humidity_value = data_point.get('humidity_value', '')
                        temperature_value = data_point.get('temperature_value', '')
                        
                        humid_values.append(humidity_value)
                        temp_values.append(temperature_value)

                        timestamp_obj = data_point.get('timestamp', datetime.utcnow())
                        formatted_timestamp = timestamp_obj.astimezone(pytz.utc).strftime('%d-%m-%Y')
                        timestamps_humid_temp.append(formatted_timestamp)
            # Fetch data from sensor:NPK
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
                        nitrogen_value = data_point.get('nitrogen_value', '')
                        phosphorous_value = data_point.get('phosphorous_value', '')
                        potassium_value = data_point.get('potassium_value', '')
                        
                        nitrogen_values.append(nitrogen_value)
                        phosphorous_values.append(phosphorous_value)
                        potassium_values.append(potassium_value)
                        timestamp_obj = data_point.get('timestamp', datetime.utcnow())
                        formatted_timestamp = timestamp_obj.astimezone(pytz.utc).strftime('%d-%m-%Y')
                        timestamps_NPK.append(formatted_timestamp)
            
            # Fetch data from sensor:PHSensor
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
            # Fetch data from sensor:rainfallSensor
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
            
            # Update the sensor array in the channel document
            collection.update_one(
                {"_id": _id},
                {"$set": {"sensor": updated_sensor_array}}
            )

            context = {
                "channel_id": channel_id,
                "ph_values": ph_values,
                "timestamps": timestamps,  # Ensure alignment
                "rainfall_values": rainfall_values,
                "rainfall_timestamps": rainfall_timestamps,  # Ensure alignment
                "humid_values": humid_values,
                "temp_values": temp_values,
                "timestamps_humid_temp": timestamps_humid_temp,  # Ensure alignment
                "nitrogen_values": nitrogen_values,
                "phosphorous_values": phosphorous_values,
                "potassium_values": potassium_values,
                "timestamps_NPK": timestamps_NPK,  # Ensure alignment
                "API": API_KEY,
            }
            if humid_values or ph_values or rainfall_values or nitrogen_values or potassium_values or phosphorous_value or temp_values:
                # Load the trained Random Forest model
                model = load_trained_model()
                if model:
                    # Prepare input data for model prediction
                    input_data = {
                        'N': float(nitrogen_values[-1]) if nitrogen_values else 0.0,  
                        'P': float(potassium_values[-1]) if potassium_values else 0.0,
                        'K': float(phosphorous_values[-1]) if phosphorous_values else 0.0,
                        'temperature': float(temp_values[-1]) if temp_values else 0.0,  
                        'humidity': float(humid_values[-1]) if humid_values else 0.0,  
                        'ph': float(ph_values[-1]) if ph_values else 0.0,  
                        'rainfall':float(rainfall_values[-1]) if rainfall_values else 0.0,   
                    }

                    input_df = pd.DataFrame([input_data])

                    # Make predictions using the model
                    prediction = model.predict(input_df)
                    
                    probabilities = model.predict_proba(input_df)
                    
                    labels = model.classes_

                    # Combine the labels with their probabilities and sort them by probability in descending order
                    crop_recommendations = [
                        {"crop": label, "accuracy": prob * 100}  # Convert to percentage
                        for label, prob in zip(labels, probabilities[0])
                    ]
                    crop_recommendations.sort(key=lambda x: x["accuracy"], reverse=True)
                    # Add the crop recommendation to the context
                    context["crop_recommendations"] = crop_recommendations

                return JsonResponse(context)
                
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")
        return JsonResponse({"success": False, "error": "Database connection error"})    
# To view embedded code dashboard
def render_embed_code(request, channel_id):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})
        if channel:
            channel_privacy = channel.get('privacy', '')
            if channel_privacy == "public":
                print("Found channel")
                channel_name = channel.get('channel_name', '')
                description = channel.get('description', '')
                API_KEY = channel.get('API_KEY', '')
                soil_location=channel.get("location", '')
                graph_count = 0

                if API_KEY:
                    # Check sensors in DHT11
                    dht_db, dht_collection = connect_to_mongodb('sensor', 'DHT11')
                    if dht_db is not None and dht_collection is not None:
                        dht_sensor = dht_collection.find_one({"API_KEY": API_KEY})
                        if dht_sensor:
                            graph_count += 2

                    # Check sensors in NPK
                    NPK_db, NPK_collection = connect_to_mongodb('sensor', 'NPK')
                    if NPK_db is not None and NPK_collection is not None:
                        NPK_sensor = NPK_collection.find_one({"API_KEY": API_KEY})
                        if NPK_sensor:
                            graph_count += 3

                    # Check sensors in PHSensor
                    ph_db, ph_collection = connect_to_mongodb('sensor', 'PHSensor')
                    if ph_db is not None and ph_collection is not None:
                        ph_sensor = ph_collection.find_one({"API_KEY": API_KEY})
                        if ph_sensor:
                            graph_count += 1

                    # Check sensors in rainfallSensor
                    rainfall_db, rainfall_collection = connect_to_mongodb('sensor', 'rainfall')
                    if rainfall_db is not None and ph_collection is not None:
                        rainfall_sensor = rainfall_collection.find_one({"API_KEY": API_KEY})
                        if rainfall_sensor:
                            graph_count += 1
                context = {
                    "channel_name": channel_name,
                    "description": description,
                    "channel_id": channel_id,
                    "API": API_KEY,
                    "graph_count": graph_count,
                    "soil_location":soil_location
                }

                return render(request, 'embed_dashboard.html', context)
            else:
                return JsonResponse({"success": False, "error": "Dashboard is not public"})
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")
    
# DECLARE PLANTFEED URL HERE
PLANTFEED_SHARING_URL="https://d30c-2a09-bac5-55fe-18d2-00-279-9c.ngrok-free.app"
PLANTFEED_SHARING_API_PATH=PLANTFEED_SHARING_URL+"group/PlantLink-Graph-API"

@csrf_exempt
def share_channel(request, channel_id):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})
        if channel:
            plantfeed_link = PLANTFEED_SHARING_API_PATH
            channel_name = channel.get('channel_name', 'Unknown Channel')
            
            # Read plantfeed_user_id sent by Flutter
            plantfeed_user_id = "1"
            if request.body:
                try:
                    body = json.loads(request.body)
                    plantfeed_user_id = str(body.get('plantfeed_user_id', '1'))
                except:
                    pass
                
            channel_data = {
                "userid": plantfeed_user_id,  # now uses real user ID
                "chart_name": f"Channel: {channel_name}",
                "embed_link": f"http://52.64.72.29:8000/mychannel/embed/channel/{channel_id}/",
                "chart_type": "Channel",
                "start_date": "2025-01-01",
                "end_date": "2025-01-14"
            }

            headers = {
                'Content-Type': 'application/json',
            }

            try:
                response = requests.post(
                    plantfeed_link, 
                    json=channel_data,  # Use json parameter instead of data
                    headers=headers
                )
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

        plantfeed_link = PLANTFEED_SHARING_API_PATH
        embed_link = f"http://52.64.72.29:8000/mychannel/embed/channel/{channel_id}/{chart_type}Chart/{start_date}/{end_date}/"
        
        # Format the data according to PlantFeed's expected structure
        channel_data = {
            "userid": "1",  # Make sure this matches a valid user ID in PlantFeed
            "chart_name": chart_name,
            "chart_type": chart_type,
            "start_date": start_date,
            "end_date": end_date,
            "embed_link": embed_link,
        }

        # Add headers to ensure proper JSON content type
        headers = {
            'Content-Type': 'application/json',
        }

        response = requests.post(
            plantfeed_link, 
            json=channel_data,  # Use json parameter instead of data
            headers=headers
        )

        print("Sending data:", channel_data)
        print("Response:", response.text)


        if response.status_code == 200:
            return JsonResponse({"success": f"{chart_type} chart successfully sent to PlantFeed."}, status=200)
        else:
            return JsonResponse({
                "error": f"Failed to share {chart_type} chart. PlantFeed Response: {response.text}",
                "status_code": response.status_code
            }, status=500)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

#render chart
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
        "API": channel.get('api_KEY', ''),
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

# For retrieve Humidity and Temperature data - DONE
def getHumidityTemperatureData(request, channel_id, start_date, end_date):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})

        if channel:
            sensor = channel.get('sensor', '')
            humid_values = []
            temp_values = []
            timestamps_humid_temp = []
            API = channel.get('API_KEY', '')
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Fetch data from sensor:DHT11
            db_humid_temp, collection_humid_temp = connect_to_mongodb('sensor', 'DHT11')
            if db_humid_temp is not None and collection_humid_temp is not None:
                humid_temp_data = collection_humid_temp.find_one({"API_KEY": API})
                if humid_temp_data:
                    for data_point in humid_temp_data.get('sensor_data', []):
                        timestamp_obj = data_point.get('timestamp', datetime.utcnow())
                        if start_date <= timestamp_obj <= end_date:
                            humidity_value = data_point.get('humidity_value', '')
                            temperature_value = data_point.get('temperature_value', '')
                            humid_values.append(humidity_value)
                            temp_values.append(temperature_value)
                            formatted_timestamp = timestamp_obj.astimezone(pytz.utc).strftime('%d-%m-%Y')
                            timestamps_humid_temp.append(formatted_timestamp)
            context = {
                "channel_id": channel_id,
                "humid_values": humid_values,
                "temp_values": temp_values,
                "timestamps_humid_temp": timestamps_humid_temp,
                "API": API,
            }
            print("check here",context)
            return JsonResponse(context)
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")

# For retrieve NPK data - DONE
def getNPKData(request, channel_id, start_date, end_date):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})

        if channel:
            sensor = channel.get('sensor', '')
            nitrogen_values = []
            phosphorous_values = []
            potassium_values = []
            timestamps_NPK = []
            API = channel.get('API_KEY', '')
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Fetch data from sensor:DHT11
            db_NPK, collection_NPK = connect_to_mongodb('sensor', 'NPK')
            if db_NPK is not None and collection_NPK is not None:
                NPK_data = collection_NPK.find_one({"API_KEY": API})
                if NPK_data:
                    for data_point in NPK_data.get('sensor_data', []):
                        timestamp_obj = data_point.get('timestamp', datetime.utcnow())
                        if start_date <= timestamp_obj <= end_date:
                            nitrogen_value = data_point.get('nitrogen_value', '')
                            phosphorous_value = data_point.get('phosphorous_value', '')
                            potassium_value = data_point.get('potassium_value', '')
                            nitrogen_values.append(nitrogen_value)
                            phosphorous_values.append(phosphorous_value)
                            potassium_values.append(potassium_value)
                            formatted_timestamp = timestamp_obj.astimezone(pytz.utc).strftime('%d-%m-%Y')
                            timestamps_NPK.append(formatted_timestamp)
                        else:
                            print("invalid timestamp")
                else:
                    print("npk_data empty")
            context = {
                "channel_id": channel_id,
                "nitrogen_values" :nitrogen_values,
                "phosphorous_values" :phosphorous_values, 
                "potassium_values" :potassium_values, 
                "timestamps_NPK" :timestamps_NPK, 
                "API": API,
            }
            return JsonResponse(context)
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")

# For retrieve PH data - DONE
def getPHData(request, channel_id, start_date, end_date):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})

        if channel:
            sensor = channel.get('sensor', '')
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

# For retrieve rainfall data - DONE
def getRainfallData(request, channel_id, start_date, end_date):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})

        if channel:
            sensor = channel.get('sensor', '')
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

# ADD SENSOR TO CHANNEL - (New)
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

        # Fetch data from each sensor collection
        for sensor in sensors:
            sensor_db, sensor_collection = connect_to_mongodb('sensor', sensor['db_name'])
            if sensor_db is not None and sensor_collection is not None:
                # Fetch sensors matching the provided API_KEY
                sensor_data = sensor_collection.find({'API_KEY': API_KEY})
                for data in sensor_data:
                    matching_sensors.append({
                        'sensor_id': str(data.get('_id')),
                        'sensor_type': data.get('sensor_type', 'Unknown Type'),
                        'sensor_data_count': len(data.get('sensor_data', [])),
                    })

        # Update the channel document with the matching sensors
        if matching_sensors:
            # Use $set to overwrite the 'sensor' array with the new matching sensors
            collection_channel.update_one(
                filter_criteria,
                {
                    '$set': {
                        'API_KEY': API_KEY,
                        'allow_API': "permit",
                        'sensor': matching_sensors  # Overwrite the sensor array
                    }
                }
            )
            print(f"Successfully updated sensors for channel {channel_id}.")
            return redirect('view_channel_sensor', channel_id=channel_id)
        else:
            print(f"No sensors found with API_KEY: {API_KEY}")
            return render(request, 'add_sensor.html', {
                'channel_id': channel_id,
                'error': 'No sensors found with the provided API_KEY.'
            })
    else:
        # Handle GET request to render the form
        _id = ObjectId(channel_id)
        db, collection = connect_to_mongodb('Channel', 'dashboard')

        if db is not None and collection is not None:
            channel = collection.find_one({"_id": _id})
            if channel:
                print("Found channel")
                sensor_api = channel.get('API_KEY', '')
                context = {"channel_id": channel_id, "API_KEY": sensor_api}
                return render(request, 'add_sensor.html', context)
            else:
                context = {"channel_id": channel_id}
                return render(request, 'add_sensor.html', context)

# MANAGE SENSOR BASED ON API KEY - DONE (New)
def manage_sensor(request, channel_id):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')

    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})
        if channel:
            print("Found channel")
            sensor_api = channel.get('API_KEY', '')
            sensor_list = []

            if not sensor_api:
                return JsonResponse({"error": "No API key set for this channel"}, status=400)
            else:
                # Fetch data from different sensor collections
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

# UNSET SENSOR - Clears the API key from the channel directly (New)
@csrf_exempt
def unset_sensor(request, channel_id):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    
    if db is not None and collection is not None:
        channel = collection.find_one({'_id': _id})
        if channel:
            # Directly unset the API_KEY without any checks
            collection.update_one(
                {'_id': _id},
                {'$set': 
                    {'API_KEY': '', 'sensor': []}
                }
            )
            return JsonResponse({"success": True, "message": "API_KEY unset successfully."})
        else:
            return JsonResponse({"success": False, "error": "Channel document not found."}, status=404)
    else:
        return JsonResponse({"error": "Database connection error"}, status=500)

#   DELETE SENSOR - DONE (New)
@csrf_exempt
def delete_sensor(request, channel_id, sensor_type):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    print(sensor_type)

    if db is not None and collection is not None:
        channel = collection.find_one({'_id': _id})
        if channel:
            api_key = channel.get('API_KEY', '')
            if api_key:
                # Determine the sensor collection to delete from
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
                        # Delete the specific sensor data
                        sensor_collection.delete_one({"API_KEY": api_key})
                        
                        # Update the channel's sensor array to remove the deleted sensor
                        collection.update_one(
                            {'_id': _id},
                            {'$pull': {'sensor': {'sensor_type': sensor_type}}}
                        )
                        
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

# EDIT SENSOR - DONE (changed)
@csrf_exempt
def edit_sensor(request, sensor_type, sensor_id, channel_id):
    if request.method == 'POST':
        print(sensor_type)
        # Fetch form data
        sensor_name = request.POST.get('sensorName')
        sensor_type = request.POST.get('sensorType')
        API_KEY = request.POST.get('ApiKey')

        if sensor_type == "DHT11":
            db, collection = connect_to_mongodb('sensor', 'DHT11')
            if db is not None and collection is not None:
                # Convert channel_id to ObjectId
                _id = ObjectId(sensor_id)
                result = collection.update_one(
                    {"_id": _id},
                    {"$set": {
                        "sensor_name": sensor_name,
                    }}
                )
                if result.modified_count > 0:
                    # Channel updated successfully
                    return redirect('manage_sensor', channel_id=channel_id)
                else:
                    return redirect('view_channel_sensor', channel_id=channel_id)

        elif sensor_type == "ph_sensor":
            db, collection = connect_to_mongodb('sensor', 'PHSensor')
            if db is not None and collection is not None:
                # Convert channel_id to ObjectId
                _id = ObjectId(sensor_id)
                result = collection.update_one(
                    {"_id": _id},
                    {"$set": {
                        "sensor_name": sensor_name,
                    }}
                )
                if result.modified_count > 0:
                    # Channel updated successfully
                    return redirect('manage_sensor', channel_id=channel_id)
                else:
                    return redirect('view_channel_sensor', channel_id=channel_id)
        elif sensor_type == "NPK":
            db, collection = connect_to_mongodb('sensor', 'NPK')
            if db is not None and collection is not None:
                # Convert channel_id to ObjectId
                _id = ObjectId(sensor_id)
                result = collection.update_one(
                    {"_id": _id},
                    {"$set": {
                        "sensor_name": sensor_name,
                    }}
                )
                if result.modified_count > 0:
                    # Channel updated successfully
                    return redirect('manage_sensor', channel_id=channel_id)
                else:
                    return redirect('view_channel_sensor', channel_id=channel_id)
        elif sensor_type == "rainfall":
            db, collection = connect_to_mongodb('sensor', 'rainfall')
            if db is not None and collection is not None:
                # Convert channel_id to ObjectId
                _id = ObjectId(sensor_id)
                result = collection.update_one(
                    {"_id": _id},
                    {"$set": {
                        "sensor_name": sensor_name,
                    }}
                )
                if result.modified_count > 0:
                    # Channel updated successfully
                    return redirect('manage_sensor', channel_id=channel_id)
                else:
                    return redirect('view_channel_sensor', channel_id=channel_id)

    else:
        # Fetch channel details from MongoDB to pre-fill the form
        if sensor_type == "DHT11":
            db, collection = connect_to_mongodb('sensor', 'DHT11')
            _id = ObjectId(sensor_id)
            sensor = collection.find_one({"_id": _id})
            if sensor:
                sensor_name = sensor.get("sensor_name", "")
                API_KEY = sensor.get("API_KEY", '')
                context = {
                    "channel_id": channel_id,
                    "sensor_name": sensor_name,
                    "sensor_type": sensor_type,
                    "API_KEY": API_KEY,
                }
                # Render the edit form with channel data
                return render(request, 'edit_sensor.html', context)
            else:
                # Handle if channel not found in MongoDB
                return JsonResponse({"success": False, "error": "Channel not found"})
        elif sensor_type == "ph_sensor":
            db, collection = connect_to_mongodb('sensor', 'PHSensor')
            _id = ObjectId(sensor_id)
            sensor = collection.find_one({"_id": _id})
            if sensor:
                sensor_name = sensor.get("sensor_name", "")
                API_KEY = sensor.get("API_KEY", '')
                context = {
                    "channel_id": channel_id,
                    "sensor_name": sensor_name,
                    "sensor_type": sensor_type,
                    "API_KEY": API_KEY,
                }
                # Render the edit form with channel data
                return render(request, 'edit_sensor.html', context)
            else:
                # Handle if channel not found in MongoDB
                return JsonResponse({"success": False, "error": "Channel not found"})

    # Default response if request method is not 'POST'
    return JsonResponse({"success": False, "error": "Invalid request method"})

# TO CHANGE CHANNEL PERMISSION TO FORBID API - DONE
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

# TO CHANGE CHANNEL PERMISSION TO ALLOW API - DONE
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
