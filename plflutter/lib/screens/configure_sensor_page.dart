import 'package:flutter/material.dart';
import 'package:plflutter/screens/sensor_service.dart';

class ConfigureSensorPage extends StatefulWidget {
  final String channelId;

  const ConfigureSensorPage({super.key, required this.channelId});

  @override
  State<ConfigureSensorPage> createState() => _ConfigureSensorPageState();
}

class _ConfigureSensorPageState extends State<ConfigureSensorPage> {
  late Future<Map<String, dynamic>> _sensorData;

  @override
  void initState() {
    super.initState();
    _sensorData = SensorService().fetchSensors(widget.channelId);
  }

  void _editSensorName(String sensorId, String currentName, String sensorType, String apiKey, List<dynamic> allSensors) {
    final controller = TextEditingController(text: currentName);
    String? errorText;

    showDialog(
      context: context,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setStateDialog) {
            return AlertDialog(
              title: const Text('Edit Sensor Name'),
              content: TextField(
                controller: controller,
                decoration: InputDecoration(
                  labelText: 'Sensor Name',
                  errorText: errorText,
                ),
                onChanged: (_) {
                  if (errorText != null) setStateDialog(() => errorText = null);
                },
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('Cancel'),
                ),
                TextButton(
                  onPressed: () async {
                    final newName = controller.text.trim();
                    if (newName.isEmpty) {
                      setStateDialog(() => errorText = 'Sensor name cannot be empty.');
                      return;
                    }
                    final isDuplicate = allSensors.any((s) =>
                        s['sensor_id'] != sensorId &&
                        (s['sensor_name'] ?? '').toString().toLowerCase() == newName.toLowerCase());
                    if (isDuplicate) {
                      setStateDialog(() => errorText = 'Sensor name already exists.');
                      return;
                    }
                    try {
                      await SensorService().editSensor(
                        channelId: widget.channelId,
                        sensorType: sensorType,
                        sensorId: sensorId,
                        newSensorName: newName,
                        apiKey: apiKey,
                      );
                      if (!mounted) return;
                      final messenger = ScaffoldMessenger.of(context);
                      Navigator.pop(context);
                      setState(() {
                        _sensorData = SensorService().fetchSensors(widget.channelId);
                      });
                      messenger.showSnackBar(const SnackBar(
                        content: Text('Sensor name updated successfully'),
                        backgroundColor: Colors.green,
                      ));
                    } catch (e) {
                      setStateDialog(() => errorText = 'Failed to update sensor name.');
                    }
                  },
                  child: const Text('Save'),
                ),
              ],
            );
          },
        );
      },
    );
  }

  void _deleteSensor(String sensorId, String sensorType, String sensorName) {
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Delete Sensor'),
          content: Text('Are you sure you want to delete "$sensorName"?\n\nThis will permanently remove all its data.'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            TextButton(
              style: TextButton.styleFrom(foregroundColor: Colors.red),
              onPressed: () async {
                final messenger = ScaffoldMessenger.of(context);
                Navigator.pop(context);
                try {
                  await SensorService().deleteSensor(
                    channelId: widget.channelId,
                    sensorType: sensorType,
                  );
                  if (!mounted) return;
                  setState(() {
                    _sensorData = SensorService().fetchSensors(widget.channelId);
                  });
                  messenger.showSnackBar(const SnackBar(
                    content: Text('Sensor deleted successfully'),
                    backgroundColor: Colors.green,
                  ));
                } catch (e) {
                  if (!mounted) return;
                  messenger.showSnackBar(SnackBar(
                    content: Text('Failed to delete sensor: $e'),
                    backgroundColor: Colors.red,
                  ));
                }
              },
              child: const Text('Delete'),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Configure Sensors'),
        backgroundColor: Colors.green,
        foregroundColor: Colors.white,
      ),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _sensorData,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          } else if (snapshot.hasError) {
            return Center(child: Text('Error: ${snapshot.error}'));
          } else if (!snapshot.hasData) {
            return const Center(child: Text('No sensor data available.'));
          } else if (snapshot.data!['sensors'].isEmpty) {
            final apiKey = snapshot.data!['API_KEY_VALUE'];
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24.0),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.sensors_off, size: 48, color: Colors.orange),
                    const SizedBox(height: 16),
                    Text(
                      apiKey != null && apiKey.toString().isNotEmpty
                          ? 'API key "$apiKey" is saved.\nNo sensor data yet — program your device with this key and it will appear here automatically.'
                          : 'No sensors connected yet.',
                      textAlign: TextAlign.center,
                      style: const TextStyle(fontSize: 16),
                    ),
                  ],
                ),
              ),
            );
          } else {
            final apiKey = snapshot.data!['API_KEY_VALUE'];
            final sensors = snapshot.data!['sensors'] as List<dynamic>;

            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Text(
                    'API Key: $apiKey',
                    style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                ),
                const Divider(),
                Expanded(
                  child: ListView.builder(
                    itemCount: sensors.length,
                    itemBuilder: (context, index) {
                      final sensor = sensors[index];
                      final sensorName = sensor['sensor_name'] ?? '';
                      return Card(
                        margin: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
                        child: ListTile(
                          title: Text(
                              sensorName.trim().isNotEmpty ? sensorName : '[No Sensor Name]',
                              style: TextStyle(
                                  color: sensorName.trim().isNotEmpty ? null : Colors.grey,
                                  fontStyle: sensorName.trim().isNotEmpty ? FontStyle.normal : FontStyle.italic,
                              ),
                          ),
                          subtitle: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('Type: ${sensor['sensor_type']}'),
                              Text('Data Count: ${sensor['sensor_data']}'),
                            ],
                          ),
                          trailing: SizedBox(
                            width: 80,
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                SizedBox(
                                  width: 36,
                                  child: IconButton(
                                    padding: EdgeInsets.zero,
                                    icon: const Icon(Icons.edit, color: Colors.blue, size: 20),
                                    onPressed: () => _editSensorName(
                                      sensor['sensor_id'],
                                      sensorName,
                                      sensor['sensor_type'],
                                      apiKey,
                                      sensors,
                                    ),
                                  ),
                                ),
                                SizedBox(
                                  width: 36,
                                  child: IconButton(
                                    padding: EdgeInsets.zero,
                                    icon: const Icon(Icons.delete, color: Colors.red, size: 20),
                                    onPressed: () => _deleteSensor(
                                      sensor['sensor_id'],
                                      sensor['sensor_type'],
                                      sensorName,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      );
                    },
                  ),
                ),
              ],
            );
          }
        },
      ),
    );
  }
}