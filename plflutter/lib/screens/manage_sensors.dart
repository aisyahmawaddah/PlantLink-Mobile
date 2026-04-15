import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:plflutter/screens/viewchannel_page.dart'; // import ViewChannel() page 

class ManageSensorsPage extends StatefulWidget {
  const ManageSensorsPage({Key? key}) : super(key: key);

  @override
  _ManageSensorsPageState createState() => _ManageSensorsPageState();
}

class _ManageSensorsPageState extends State<ManageSensorsPage> {
  late Future<Map<String, dynamic>> _sensorData;

  @override
  void initState() {
    super.initState();
    _sensorData = _fetchSensors();
  }

  Future<Map<String, dynamic>> _fetchSensors() async {
    const url = 'http://10.0.2.2:8000/sensor/';
    try {
      final response = await http.get(Uri.parse(url));
      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to load sensors. Status code: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error fetching sensors: $e');
    }
  }

  // Override the back button behavior
  Future<bool> _onWillPop() async {
    // Navigate to  any other page when the back button is pressed
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (context) => const ViewChannel()),//ChannelPage()), //ViewChannel() here
    );
    return Future.value(false); // Prevent the default pop action
  }

  @override
  Widget build(BuildContext context) {
    return WillPopScope(
      onWillPop: _onWillPop, // Attach the custom back button behavior
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Manage Sensors'),
        ),
        body: FutureBuilder<Map<String, dynamic>>(
          future: _sensorData,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            } else if (snapshot.hasError) {
              return Center(child: Text('Error: ${snapshot.error}'));
            } else if (snapshot.hasData) {
              final data = snapshot.data!;
              final sensors = data['sensors'] as List<dynamic>;
              final sensorCounts = data['sensor_counts'] as Map<String, dynamic>;
              final totalSensors = data['total_sensors'] as int;

              return Column(
                children: [
                  Padding(
                    padding: const EdgeInsets.all(8.0),
                    child: Text(
                      'Total Sensors: $totalSensors',
                      style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                  ),
                  const Padding(
                    padding: EdgeInsets.all(8.0),
                    child: Text(
                      'Sensor Counts by Type:',
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                  ),
                  Expanded(
                    child: ListView(
                      children: [
                        for (var sensorType in sensorCounts.keys)
                          Padding(
                            padding: const EdgeInsets.symmetric(vertical: 4.0),
                            child: Text(
                              '$sensorType: ${sensorCounts[sensorType]}',
                              style: const TextStyle(fontSize: 16),
                            ),
                          ),
                        const Divider(),
                        ...sensors.map((sensor) {
                          final sensorName = sensor['sensor_name'] ?? 'Unnamed Sensor';
                          final sensorType = sensor['sensor_type'] ?? 'Unknown Type';
                          final apiKey = sensor['API_KEY'];
                          final sensorDataCount = sensor['sensor_data_count'];
                          final matchingChannels = (sensor['matching_channels'] as List)
                              .map((channel) => channel['channel_name'])
                              .toList();
                          final isUsed = matchingChannels.isNotEmpty;

                          return Card(
                            margin: const EdgeInsets.all(8.0),
                            child: ListTile(
                              leading: Icon(
                                Icons.sensors,
                                color: isUsed ? Colors.green : Colors.red,
                              ),
                              title: Text(sensorName),
                              subtitle: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text('Type: $sensorType'),
                                  Text('API_KEY: $apiKey'),
                                  Text('Data Count: $sensorDataCount'),
                                  Text('Matching Channels: ${matchingChannels.join(', ')}'),
                                ],
                              ),
                              trailing: isUsed
                                  ? const Text(
                                      'USED',
                                      style: TextStyle(color: Colors.green),
                                    )
                                  : const Text(
                                      'NOT USED',
                                      style: TextStyle(color: Colors.red),
                                    ),
                            ),
                          );
                        }),
                      ],
                    ),
                  ),
                ],
              );
            } else {
              return const Center(child: Text('No sensor data found.'));
            }
          },
        ),
      ),
    );
  }
}