import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:plflutter/screens/dashboard_page.dart';
import 'package:plflutter/screens/sensor_service.dart';

class AddSensorScreen extends StatefulWidget {
  final String channelId;

  const AddSensorScreen({super.key, required this.channelId});

  @override
  State<AddSensorScreen> createState() => _AddSensorScreenState();
}

class _AddSensorScreenState extends State<AddSensorScreen> {
  final TextEditingController _apiKeyController = TextEditingController();
  String _existingApiKey = '';
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadExistingApiKey();
  }

  Future<void> _loadExistingApiKey() async {
    try {
      final data = await SensorService().fetchSensors(widget.channelId);
      setState(() {
        _existingApiKey = data['API_KEY_VALUE'] ?? '';
        _apiKeyController.text = _existingApiKey;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }

  void _onConnectPressed() async {
    final newKey = _apiKeyController.text.trim();
    if (newKey.isEmpty) {
      _showSnackbar("API Key cannot be empty");
      return;
    }

    // If channel already has a different API key, confirm first
    if (_existingApiKey.isNotEmpty && newKey != _existingApiKey) {
      final confirmed = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Replace API Key?'),
          content: Text(
            'This channel already has API key "$_existingApiKey".\n\nReplace it with "$newKey"?'
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () => Navigator.pop(context, true),
              style: ElevatedButton.styleFrom(backgroundColor: Colors.orange),
              child: const Text('Replace'),
            ),
          ],
        ),
      );
      if (confirmed != true) return;
    }

    await _connectSensor(newKey);
  }

  Future<void> _connectSensor(String apiKey) async {
    try {
      final url = Uri.parse('http://10.0.2.2:8000/mychannel/${widget.channelId}/add_sensor');
      final response = await http.post(url, body: {'apiKey': apiKey});

            if (response.statusCode == 200 || response.statusCode == 302) {
              _showSnackbar("API key saved! Data will appear once your sensor connects.");
              if (!mounted) return;
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => DashboardScreen(channelId: widget.channelId),
                ),
              );
            } else if (response.statusCode == 409) {
              if (!mounted) return;
              showDialog(
                context: context,
                builder: (context) => AlertDialog(
                  title: const Text('API Key Already In Use'),
                  content: Text(
                    '"$apiKey" is already assigned to another one of your channels. Please use a different API key.',
                  ),
                  actions: [
                    ElevatedButton(
                      onPressed: () => Navigator.pop(context),
                      child: const Text('OK'),
                    ),
                  ],
                ),
              );
            } else {
              _showSnackbar("Server error (${response.statusCode}). Please try again.");
            }
    } catch (e) {
      _showSnackbar("Connection failed. Check your network.");
    }
  }

  void _showSnackbar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Add Sensor')),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : Center(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const Text(
                      'Add new sensor to this channel',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 20),
                    if (_existingApiKey.isNotEmpty)
                      Container(
                        padding: const EdgeInsets.all(12),
                        margin: const EdgeInsets.only(bottom: 12),
                        decoration: BoxDecoration(
                          color: Colors.orange.shade50,
                          border: Border.all(color: Colors.orange),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          'Current API key: "$_existingApiKey". Changing it will replace the existing sensor connection.',
                          style: const TextStyle(color: Colors.deepOrange),
                        ),
                      ),
                    TextFormField(
                      controller: _apiKeyController,
                      decoration: const InputDecoration(
                        labelText: 'API Key',
                        border: OutlineInputBorder(),
                      ),
                    ),
                    const SizedBox(height: 20),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        ElevatedButton(
                          onPressed: () => Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) => DashboardScreen(channelId: widget.channelId),
                            ),
                          ),
                          style: ElevatedButton.styleFrom(backgroundColor: Colors.grey),
                          child: const Text('Close'),
                        ),
                        ElevatedButton(
                          onPressed: _onConnectPressed,
                          style: ElevatedButton.styleFrom(backgroundColor: Colors.blue),
                          child: const Text('Connect sensor'),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
    );
  }

  @override
  void dispose() {
    _apiKeyController.dispose();
    super.dispose();
  }
}