import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:plflutter/config.dart';

class SensorService {
  Future<Map<String, dynamic>> fetchSensors(String channelId) async {
    final url = Uri.parse('$baseUrl/mychannel/$channelId/manage_sensor');
    try {
      final response = await http.get(url);
      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to load sensors. Status code: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error fetching sensors: $e');
    }
  }

  Future<void> editSensor({
    required String channelId,
    required String sensorType,
    required String sensorId,
    required String newSensorName,
    required String apiKey,
  }) async {
    final url = Uri.parse('$baseUrl/mychannel/$channelId/edit_sensor/$sensorType/$sensorId/');
    final response = await http.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'sensorName': newSensorName,
        'sensorType': sensorType,
        'ApiKey': apiKey,
      }),
    );
    if (response.statusCode != 200 && response.statusCode != 302) {
      throw Exception('Failed to edit sensor');
    }
  }

  Future<void> deleteSensor({
    required String channelId,
    required String sensorType,
  }) async {
    final url = Uri.parse('$baseUrl/mychannel/$channelId/delete_sensor/$sensorType/');
    final response = await http.delete(url);
    if (response.statusCode != 200 && response.statusCode != 302) {
      throw Exception('Failed to delete sensor');
    }
  }

  Future<void> unsetSensor(String channelId) async {
    final url = Uri.parse('$baseUrl/mychannel/$channelId/unset_sensor');
    try {
      final response = await http.post(url);
      if (response.statusCode != 200) {
        throw Exception('Failed to unset sensor. Status code: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error unsetting sensor: $e');
    }
  }
}