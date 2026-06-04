import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:plflutter/config.dart'; 

class ChannelService {
  static final String _baseChannelUrl = '$baseUrl/mychannel/api/channels/';
  static final String _baseStatsUrl = '$baseUrl/mychannel/stats/';

  Future<String> _getUserId() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('userid') ?? '';
  }

  Future<List<Map<String, dynamic>>> fetchChannels() async {
    try {
      final userid = await _getUserId();
      final uri = Uri.parse(_baseChannelUrl).replace(
        queryParameters: {'userid': userid},
      );
      final response = await http.get(uri);

      if (response.statusCode == 200) {
        List<dynamic> data = json.decode(response.body);
        return List<Map<String, dynamic>>.from(data);
      } else {
        throw Exception('Failed to load channels');
      }
    } catch (e) {
      print("Error fetching channels: $e");
      return [];
    }
  }

  Future<Map<String, dynamic>> fetchChannelStatistics() async {
    try {
      final userid = await _getUserId();
      final uri = Uri.parse(_baseStatsUrl).replace(
        queryParameters: {'userid': userid},
      );
      final response = await http.get(uri);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception("Failed to fetch statistics.");
      }
    } catch (e) {
      print("Error fetching stats: $e");
      return {"totalChannels": 0, "totalSensors": 0, "publicChannels": 0};
    }
  }
}
