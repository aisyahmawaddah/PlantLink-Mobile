from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId

from pymongo import MongoClient
import urllib.parse

def connect_to_mongodb(database_name, collection_name=None, username='vicolee1363', password='KHw5zZkg8JirjK0E', cluster='cluster0', retry_writes=True):
    try:
        # Construct MongoDB URI
        uri = f'mongodb+srv://vicolee1363:KHw5zZkg8JirjK0E@cluster0.c0yyh6f.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
        
        # Connect to MongoDB server
        client = MongoClient(uri)
        
        # Select the specified database
        db = client[database_name]
        
        # If collection_name is provided, select the collection
        if collection_name:
            collection = db[collection_name]
        else:
            collection = None
        
        # Return the database and collection
        return db, collection
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None, None

#from main.mongo_setup import connect_to_mongodb         #TO CONNECT TO MONGODB AND GET DB AND COLLECTION

# VIEW ALL SENSOR - in development
def sensors(request):
    # Define the list of sensor types to fetch data for
    sensors = [
        {"name": "DHT11", "db_name": "DHT11"},
        {"name": "NPK", "db_name": "NPK"},
        {"name": "PHSensor", "db_name": "PHSensor"},
        {"name": "Rainfall", "db_name": "rainfall"}
    ]

    sensor_list = []
    sensor_counts = {sensor["name"]: 0 for sensor in sensors}  # Initialize counts for each sensor type
    total_sensors = 0  # Initialize total sensor count

    # Fetch all channels and store them in memory for quick lookup
    channel_db, channel_collection = connect_to_mongodb('Channel', 'dashboard')
    channels = list(channel_collection.find()) if channel_db is not None and channel_collection is not None else []

    # Fetch data from each sensor collection
    for sensor in sensors:
        sensor_db, sensor_collection = connect_to_mongodb('sensor', sensor['db_name'])
        if sensor_db is not None and sensor_collection is not None:
            # Fetch all sensor data (ignoring API key and channel data)
            sensor_data = sensor_collection.find()
            for data in sensor_data:
                # Increment the count for the current sensor type
                sensor_counts[sensor["name"]] += 1
                total_sensors += 1

                # Initialize a list to store matching channels
                matching_channels = []

                # Get the sensor's API key
                sensor_api_key = data.get('API_KEY')

                # Find all channels with matching API keys
                for channel in channels:
                    if channel.get('API_KEY') == sensor_api_key:
                        matching_channels.append({
                            "channel_id": str(channel.get('_id')),
                            "channel_name": channel.get('channel_name', 'Unknown')
                        })

                # Append the sensor data with matching channel information
                sensor_list.append({
                    "sensor_id": str(data.get('_id')),
                    "API_KEY": sensor_api_key,
                    "sensor_name": data.get('sensor_name'),
                    "sensor_type": data.get('sensor_type'),
                    "sensor_data_count": len(data.get('sensor_data', [])),
                    "matching_channels": matching_channels,  # List of channels matching the API key
                })

    # Return the collected sensor data along with counts
    return JsonResponse({
        "sensors": sensor_list,
        "sensor_counts": sensor_counts,  # Count of each sensor type
        "total_sensors": total_sensors  # Total count of sensors
    })


# Create your views here.
@csrf_exempt
def arduino_data(request):
    if request.method == 'POST' and settings.RECEIVE_DATA_ENABLED:
        # Process incoming data
        # For example:
        # arduino_data = request.POST.get('data')
        # SensorData.objects.create(**arduino_data)
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'data reception disabled'})

def toggle_data_reception(request):
    if request.method == 'POST':
        settings.RECEIVE_DATA_ENABLED = not settings.RECEIVE_DATA_ENABLED
        return JsonResponse({'status': 'success', 'receive_data_enabled': settings.RECEIVE_DATA_ENABLED})
    else:
        return JsonResponse({'status': 'invalid request method'})


import socket
def get_ip_address(request):
    ip_address = socket.gethostbyname(socket.gethostname())
    return HttpResponse(f"Server IP Address: {ip_address}")


def check_ip(ip_address):
    mongo_uri = 'mongodb+srv://vicolee1363:KHw5zZkg8JirjK0E@cluster0.c0yyh6f.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'

    try:
        # Create a new client and connect to the server
        client = MongoClient(mongo_uri)
        db = client.sensor
        collection = db['permitted_ips']
        result = collection.find_one({'ip': ip_address})

        client.close()

        # Debug print to check if data is retrieved
        return result
    except Exception as e:
        # If an error occurs during MongoDB connection or data retrieval
        print(f"Error: {str(e)}")
        return False

@csrf_exempt
def post_ph_sensor_data(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ph_value = data.get('pH')
            ip_address = data.get('IP')
            print(f"Received pH value: {ph_value}")
            print(f"Received IP address: {ip_address}")
            
            # to  check the ip is whitelisted
            is_permitted=check_ip(ip_address)
            if is_permitted:
                ph_value_formatted = f'{ph_value:.4f}'
                timestamp = datetime.now()
                doc = {
                        'ph_value': ph_value_formatted,
                        'timestamp': timestamp
                    }
                
                db, collection = connect_to_mongodb('sensor','PH_data')
                if db is not None and collection is not None:
                    print("Connected to MongoDB successfully.")
                    # Use db and collection objects for further operations
                    # For example, insert data into collection
                    insertion_result = collection.insert_one(doc)
                    print(f"Inserted document ID: {insertion_result.inserted_id}")
                else:
                    print("Error connecting to MongoDB.")
            return JsonResponse({'message': 'pH data received successfully'}, status=200)
        except json.JSONDecodeError as e:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

@csrf_exempt
def post_humid_temp_sensor_data(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            humidity_value = data.get('humidity')
            temperature_value = data.get('temperature')
            ip_address = data.get('IP')
            print(f"Received humidity value: {humidity_value}")
            print(f"Received temperature value: {temperature_value}")
            print(f"Received IP address: {ip_address}")
            
            # to  check the ip is whitelisted
            is_permitted=check_ip(ip_address)
            if is_permitted:
                humidity_value_formatted = f'{humidity_value:.2f}'
                temperature_value_formatted = f'{temperature_value:.2f}'
                timestamp = datetime.now()
                doc = {
                        'humidity_value': humidity_value_formatted,
                        'temperature_value': temperature_value_formatted,
                        'timestamp': timestamp
                    }
                db, collection = connect_to_mongodb('sensor','humid_temperature_data')
                if db is not None and collection is not None:
                    print("Connected to MongoDB successfully.")
                    # Use db and collection objects for further operations
                    # For example, insert data into collection
                    insertion_result = collection.insert_one(doc)
                    print(f"Inserted document ID: {insertion_result.inserted_id}")
                else:
                    print("Error connecting to MongoDB.")
            return JsonResponse({'message': 'humidity and temperature data received successfully'}, status=200)
        except json.JSONDecodeError as e:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

@csrf_exempt
def post_dht_sensor_data(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            humidity_value = data.get('humidity')
            temperature_value = data.get('temperature')
            API_KEY = data.get('API_KEY')
            print(f"Received humidity value: {humidity_value}")
            print(f"Received temperature value: {temperature_value}")
            print(f"Received API KEY: {API_KEY}")
            
            db, collection = connect_to_mongodb('sensor','DHT11')
            if db is not None and collection is not None:
                filter_criteria = {'API_KEY': API_KEY}
                humidity_value_formatted = f'{humidity_value:.2f}'
                temperature_value_formatted = f'{temperature_value:.2f}'
                timestamp = datetime.now()
                doc = {
                        'humidity_value': humidity_value_formatted,
                        'temperature_value': temperature_value_formatted,
                        'timestamp': timestamp
                    }
                update_result = collection.update_one(filter_criteria, {'$push': {'sensor_data': doc}})
                if update_result.modified_count > 0:
                    print("Sensor data added successfully.")
                else:
                    print("No document matching the filter criteria found.")

            return JsonResponse({'message': 'humidity and temperature data received successfully'}, status=200)
        except json.JSONDecodeError as e:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

@csrf_exempt
def post_ph_data(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ph_value = data.get('phValue')  # Ensure 'pH' key is correctly spelled
            API_KEY = data.get('API_KEY')
            
            if ph_value is None or API_KEY is None:
                return JsonResponse({'error': 'Invalid data format'}, status=400)

            print(f"Received pH value: {ph_value}")
            print(f"Received API_KEY: {API_KEY}")

            db, collection = connect_to_mongodb('sensor', 'PHSensor')
            if db is not None and collection is not None:
                filter_criteria = {'API_KEY': API_KEY}
                ph_value_formatted = f'{ph_value:.4f}'
                timestamp = datetime.now()
                doc = {
                    'ph_value': ph_value_formatted,
                    'timestamp': timestamp
                }
                update_result = collection.update_one(filter_criteria, {'$push': {'sensor_data': doc}})
                if update_result.modified_count > 0:
                    print("Sensor data added successfully.")
                else:
                    print("No document matching the filter criteria found.")
        except json.JSONDecodeError as e:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

from django.http import JsonResponse, HttpResponseNotAllowed, HttpResponseBadRequest
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import asyncio
import websockets
@csrf_exempt
def combined_post(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            sensor_type = data.get("sensor_type")
            API_KEY = data.get('API_KEY')

            if API_KEY is None:
                return JsonResponse({'error': 'API_KEY is required'}, status=400)
            
            # Check if the API_KEY is allowed in the channel:dashboard
            db_channel, collection_channel = connect_to_mongodb('Channel', 'dashboard')
            if db_channel is not None and collection_channel is not None:
                channel = collection_channel.find_one({"API_KEY": API_KEY})
                if channel:
                    allow_API = channel.get('allow_API', '')
                    if allow_API != 'permit':
                        return JsonResponse({'error': 'API access is not permitted for this API_KEY'}, status=403)
                else:
                    return JsonResponse({'error': 'API_KEY not found in the channel:dashboard'}, status=404)
            else:
                return JsonResponse({'error': 'Database connection error'}, status=500)

            if sensor_type == "DHT11":
                humidity_value = data.get('humidity')
                temperature_value = data.get('temperature')
                API_KEY = data.get('API_KEY')
                print(f"Received humidity value: {humidity_value}")
                print(f"Received temperature value: {temperature_value}")
                print(f"Received API KEY: {API_KEY}")

                if humidity_value is None or temperature_value is None or API_KEY is None:
                    return JsonResponse({'error': 'Missing data or API_KEY'}, status=400)

                db, collection = connect_to_mongodb('sensor', 'DHT11')
                if db is not None and collection is not None:
                    filter_criteria = {'API_KEY': API_KEY}
                    existing_document = collection.find_one(filter_criteria)
                    humidity_value_formatted = f'{humidity_value:.2f}'
                    temperature_value_formatted = f'{temperature_value:.2f}'
                    timestamp = datetime.now()
                    doc = {
                        'humidity_value': humidity_value_formatted,
                        'temperature_value': temperature_value_formatted,
                        'timestamp': timestamp
                    }

                    if existing_document:
                        update_result = collection.update_one(filter_criteria, {'$push': {'sensor_data': doc}})
                        if update_result.modified_count > 0:
                            print("Sensor data added successfully.")
                            aws_websocket_url = "wss://jzngfcdfgl.execute-api.ap-southeast-2.amazonaws.com/production/"
                            message = {
                                'action': 'sendMessage',
                                'to': API_KEY,
                                'message': {
                                    'sensor_type': 'DHT11',
                                    'humidity_value': humidity_value_formatted,
                                    'temperature_value': temperature_value_formatted,
                                    'timestamp': timestamp.strftime('%d-%m-%Y')
                                }
                            }
                            asyncio.run(send_websocket_message(aws_websocket_url, message))

                            return JsonResponse({'message': 'humidity and temperature data received successfully'}, status=200)
                        else:
                            print("Failed to update sensor data.")
                            return JsonResponse({'error': 'Failed to update sensor data'}, status=500)
                    else:
                        # Insert a new document if no existing document is found
                        new_document = {
                            'API_KEY': API_KEY,
                            'sensor_name': '',
                            'sensor_type': 'DHT11',
                            'sensor_data': [doc]
                        }
                        collection.insert_one(new_document)
                        return JsonResponse({'message': 'New DHT11 sensor document created'}, status=201)
                else:
                    return JsonResponse({'error': 'Database connection error'}, status=500)

            elif sensor_type == "NPK":
                nitrogen_value = data.get('nitrogen')
                phosphorous_value = data.get('phosphorous')
                potassium_value = data.get('potassium')
                API_KEY = data.get('API_KEY')
                print(f"Received nitrogen value: {nitrogen_value}")
                print(f"Received phosphorous value: {phosphorous_value}")
                print(f"Received potassium value: {potassium_value}")
                print(f"Received API KEY: {API_KEY}")

                if nitrogen_value is None or phosphorous_value is None or potassium_value is None or API_KEY is None:
                    return JsonResponse({'error': 'Missing data or API_KEY'}, status=400)

                db, collection = connect_to_mongodb('sensor', 'NPK')
                if db is not None and collection is not None:
                    filter_criteria = {'API_KEY': API_KEY}
                    existing_document = collection.find_one(filter_criteria)
                    nitrogen_value_formatted = f'{nitrogen_value:.2f}'
                    phosphorous_value_formatted = f'{phosphorous_value:.2f}'
                    potassium_value_formatted = f'{potassium_value:.2f}'
                    timestamp = datetime.now()
                    doc = {
                        'nitrogen_value': nitrogen_value_formatted,
                        'phosphorous_value': phosphorous_value_formatted,
                        'potassium_value':potassium_value_formatted,
                        'timestamp': timestamp
                    }

                    if existing_document:
                        update_result = collection.update_one(filter_criteria, {'$push': {'sensor_data': doc}})
                        if update_result.modified_count > 0:
                            print("Sensor data added successfully.")
                            aws_websocket_url = "wss://jzngfcdfgl.execute-api.ap-southeast-2.amazonaws.com/production/"
                            message = {
                                'action': 'sendMessage',
                                'to': API_KEY,
                                'message': {
                                    'sensor_type': 'NPK',
                                    'nitrogen_value': nitrogen_value_formatted,
                                    'phosphorous_value': phosphorous_value_formatted,
                                    'potassium_value':potassium_value_formatted,
                                    'timestamp': timestamp.strftime('%d-%m-%Y')
                                }
                            }
                            asyncio.run(send_websocket_message(aws_websocket_url, message))

                            return JsonResponse({'message': 'Nitrogen, Phosphorous, and Potassium  data received successfully'}, status=200)
                        else:
                            print("Failed to update sensor data.")
                            return JsonResponse({'error': 'Failed to update sensor data'}, status=500)
                    else:
                        # Insert a new document if no existing document is found
                        new_document = {
                            'API_KEY': API_KEY,
                            'sensor_name': '',
                            'sensor_type': 'NPK',
                            'sensor_data': [doc]
                        }
                        collection.insert_one(new_document)
                        return JsonResponse({'message': 'New DHT11 sensor document created'}, status=201)
                else:
                    return JsonResponse({'error': 'Database connection error'}, status=500)
                
            elif sensor_type == "ph_sensor":
                ph_value = data.get('phValue')
                API_KEY = data.get('API_KEY')

                if ph_value is None or API_KEY is None:
                    return JsonResponse({'error': 'Missing pH value or API_KEY'}, status=400)

                print(f"Received pH value: {ph_value}")
                print(f"Received API KEY: {API_KEY}")

                db, collection = connect_to_mongodb('sensor', 'PHSensor')
                if db is not None and collection is not None:
                    filter_criteria = {'API_KEY': API_KEY}
                    existing_document = collection.find_one(filter_criteria)
                    ph_value_formatted = f'{ph_value:.4f}'
                    timestamp = datetime.now()
                    doc = {
                        'ph_value': ph_value_formatted,
                        'timestamp': timestamp
                    }

                    if existing_document:
                        update_result = collection.update_one(filter_criteria, {'$push': {'sensor_data': doc}})
                        if update_result.modified_count > 0:
                            aws_websocket_url = "wss://jzngfcdfgl.execute-api.ap-southeast-2.amazonaws.com/production/"
                            message = {
                                'action': 'sendMessage',
                                'to': API_KEY,
                                'message': {
                                    'sensor_type': 'ph_sensor',
                                    'ph_value': ph_value_formatted,
                                    'timestamp': timestamp.strftime('%d-%m-%Y')
                                }
                            }
                            asyncio.run(send_websocket_message(aws_websocket_url, message))
                            print("Sensor data added successfully.")
                            return JsonResponse({'message': 'pH data received successfully'}, status=200)
                        else:
                            print("Failed to update sensor data.")
                            return JsonResponse({'error': 'Failed to update sensor data'}, status=500)
                    else:
                        # Insert a new document if no existing document is found
                        new_document = {
                            'API_KEY': API_KEY,
                            'sensor_name': '',
                            'sensor_type': 'ph_sensor',
                            'sensor_data': [doc]
                        }
                        collection.insert_one(new_document)
                        
                        return JsonResponse({'message': 'New pH sensor document created'}, status=201)
                else:
                    return JsonResponse({'error': 'Database connection error'}, status=500)

            elif sensor_type == "rainfall":
                rainfall_value = data.get('rainfallValue')
                API_KEY = data.get('API_KEY')

                if rainfall_value is None or API_KEY is None:
                    return JsonResponse({'error': 'Missing rainfall value or API_KEY'}, status=400)

                print(f"Received rainfall value: {rainfall_value}")
                print(f"Received API KEY: {API_KEY}")

                db, collection = connect_to_mongodb('sensor', 'rainfall')
                if db is not None and collection is not None:
                    filter_criteria = {'API_KEY': API_KEY}
                    existing_document = collection.find_one(filter_criteria)
                    rainfall_value_formatted = f'{rainfall_value:.4f}'
                    timestamp = datetime.now()
                    doc = {
                        'rainfall_value': rainfall_value_formatted,
                        'timestamp': timestamp
                    }

                    if existing_document:
                        update_result = collection.update_one(filter_criteria, {'$push': {'sensor_data': doc}})
                        if update_result.modified_count > 0:
                            aws_websocket_url = "wss://jzngfcdfgl.execute-api.ap-southeast-2.amazonaws.com/production/"
                            message = {
                                'action': 'sendMessage',
                                'to': API_KEY,
                                'message': {
                                    'sensor_type': 'rainfall_sensor',
                                    'rainfall_value': rainfall_value_formatted,
                                    'timestamp': timestamp.strftime('%d-%m-%Y')
                                }
                            }
                            asyncio.run(send_websocket_message(aws_websocket_url, message))
                            print("Sensor data added successfully.")
                            return JsonResponse({'message': 'rainfall data received successfully'}, status=200)
                        else:
                            print("Failed to update sensor data.")
                            return JsonResponse({'error': 'Failed to update sensor data'}, status=500)
                    else:
                        # Insert a new document if no existing document is found
                        new_document = {
                            'API_KEY': API_KEY,
                            'sensor_name': '',
                            'sensor_type': 'rainfall',
                            'sensor_data': [doc]
                        }
                        collection.insert_one(new_document)
                        
                        return JsonResponse({'message': 'New rainfall sensor document created'}, status=201)
                else:
                    return JsonResponse({'error': 'Database connection error'}, status=500)
                
        except json.JSONDecodeError as e:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return HttpResponseNotAllowed(['POST'])


async def send_websocket_message(url, message):
    async with websockets.connect(url) as websocket:
        await websocket.send(json.dumps(message))


from pymongo import MongoClient
def check_ip(ip_address):
    mongo_uri = 'mongodb+srv://vicolee1363:KHw5zZkg8JirjK0E@cluster0.c0yyh6f.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'

    try:
        # Create a new client and connect to the server
        client = MongoClient(mongo_uri)
        db = client.sensor
        collection = db['permitted_ips']
        result = collection.find_one({'ip': ip_address})

        client.close()

        # Debug print to check if data is retrieved
        return result
    except Exception as e:
        # If an error occurs during MongoDB connection or data retrieval
        print(f"Error: {str(e)}")
        return False
    

def another_view(request):
    ip_to_check = '192.168.100.49'  # Example IP address to check

    # Call the is_ip_permitted function to check if the IP is permitted
    is_permitted = check_ip(ip_to_check)
    
    if is_permitted:
        return HttpResponse("IP is permitted.")
    else:
        return HttpResponse("IP is not permitted.")

    