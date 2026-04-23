import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:intl/intl.dart';
import 'package:fl_chart/fl_chart.dart';
//import 'package:plflutter/screens/dashboard_functions.dart';
import 'package:plflutter/screens/connect_sensor_page.dart';
import 'package:plflutter/screens/configure_sensor_page.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter/services.dart';
import 'package:plflutter/screens/crop_recommendations_page.dart';

class DashboardScreen extends StatefulWidget {
  final String channelId;
  const DashboardScreen({super.key, required this.channelId});

  @override
  _DashboardScreenState createState() => _DashboardScreenState();
}

const String _baseUrl = 'https://rathe-Russell-proterandrous.ngrok-free.dev';

class _DashboardScreenState extends State<DashboardScreen> {
  late String channelId = widget.channelId;

  List<double> phData = [];
  List<double> rainfallData = [];
  List<double> humidityData = [];
  List<double> tempData = [];
  List<double> nitrogenData = [];
  List<double> phosphorousData = [];
  List<double> potassiumData = [];
  List<String> phTimestamps = [];
  List<String> rainfallTimestamps = [];
  List<String> humidTempTimestamps = [];
  List<String> npkTimestamps = [];

  String channelName = '';
  String description = '';
  String location = '';
  bool allowApi = false;
  List<Map<String, dynamic>> cropRecommendations = [];

  bool isLoading = true;

  Map<String, String> selectedChartTypes = {
    "pH Level Chart": "Spline Chart",
    "Rainfall Chart": "Spline Chart",
    "Humidity Chart": "Spline Chart",
    "Temperature Chart": "Spline Chart",
    "Nitrogen Chart": "Spline Chart",
    "Phosphorous Chart": "Spline Chart",
    "Potassium Chart": "Spline Chart",
  };

  String _plantfeedUserId = '1';

  @override
  void initState() {
    super.initState();
    _loadPlantfeedUserId();
    fetchSensorData();
  }

  Future<void> _loadPlantfeedUserId() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _plantfeedUserId = prefs.getString('userid') ?? '1';
    });
  }

  Future<void> fetchSensorData() async {
    try {
      final response = await http.get(
        Uri.parse('http://10.0.2.2:8000/mychannel/$channelId/get_dashboard_data/'),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);

        setState(() {
          phData = List<double>.from(
            (data['ph_values'] as List?)?.map((v) => double.tryParse(v.toString()) ?? 0.0) ?? [],
          );
          rainfallData = List<double>.from(
            (data['rainfall_values'] as List?)?.map((v) => double.tryParse(v.toString()) ?? 0.0) ?? [],
          );
          humidityData = List<double>.from(
            (data['humid_values'] as List?)?.map((v) => double.tryParse(v.toString()) ?? 0.0) ?? [],
          );
          tempData = List<double>.from(
            (data['temp_values'] as List?)?.map((v) => double.tryParse(v.toString()) ?? 0.0) ?? [],
          );
          nitrogenData = List<double>.from(
            (data['nitrogen_values'] as List?)?.map((v) => double.tryParse(v.toString()) ?? 0.0) ?? [],
          );
          phosphorousData = List<double>.from(
            (data['phosphorous_values'] as List?)?.map((v) => double.tryParse(v.toString()) ?? 0.0) ?? [],
          );
          potassiumData = List<double>.from(
            (data['potassium_values'] as List?)?.map((v) => double.tryParse(v.toString()) ?? 0.0) ?? [],
          );

          channelName = data['channel_name'] ?? '';
          description = data['description'] ?? '';
          location = data['location'] ?? '';
          allowApi = (data['allow_api'] ?? '') == 'permit';
          cropRecommendations = List<Map<String, dynamic>>.from(
            data['crop_recommendations'] ?? [],
          );
          phTimestamps = List<String>.from(data['timestamps'] ?? []);
          rainfallTimestamps = List<String>.from(data['rainfall_timestamps'] ?? []);
          humidTempTimestamps = List<String>.from(data['timestamps_humid_temp'] ?? []);
          npkTimestamps = List<String>.from(data['timestamps_NPK'] ?? []);

          isLoading = false;
        });
      } else {
        setState(() => isLoading = false);
        debugPrint('Failed to load sensor data. Status Code: ${response.statusCode}');
      }
    } catch (e) {
      setState(() => isLoading = false);
      debugPrint('Error fetching data: $e');
    }
  }

  List<FlSpot> _generateSpots(List<double> data) {
    return List.generate(data.length, (index) => FlSpot(index.toDouble(), data[index]));
  }

  String _formatDateForApi(String timestamp) {
    final s = timestamp.length >= 10 ? timestamp.substring(0, 10) : timestamp;
    if (RegExp(r'^\d{4}-\d{2}-\d{2}$').hasMatch(s)) return s;
    try {
      return DateFormat("yyyy-MM-dd").format(DateFormat("dd-MM-yyyy").parse(s));
    } catch (_) {}
    return s;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Dashboard"),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: fetchSensorData),
        ],
      ),
      body: isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // ── Header Card ──────────────────────────────────
                  Card(
                    elevation: 2,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    child: Padding(
                      padding: const EdgeInsets.all(14),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Dashboard: $channelName',
                            style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(height: 4),
                          Text('Description: $description', style: const TextStyle(fontSize: 13)),
                          const SizedBox(height: 2),
                          Text('Location: $location', style: const TextStyle(fontSize: 13)),
                          const SizedBox(height: 8),
                          Row(
                            children: [
                              Switch(
                                value: allowApi,
                                onChanged: _toggleApi,
                                activeColor: Colors.green,
                              ),
                              const Text('Allow receive sensor data'),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),

                  // ── Action Buttons ───────────────────────────────
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
                        icon: const Icon(Icons.share, color: Colors.white, size: 16),
                        label: const Text('Share Channel', style: TextStyle(color: Colors.white)),
                        onPressed: shareChannel,
                      ),
                      ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
                        icon: const Icon(Icons.settings, color: Colors.white, size: 16),
                        label: const Text('Configure Sensor', style: TextStyle(color: Colors.white)),
                        onPressed: () => Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => ConfigureSensorPage(channelId: channelId),
                          ),
                        ),
                      ),
                      ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
                        icon: const Icon(Icons.add, color: Colors.white, size: 16),
                        label: const Text('Connect Sensor', style: TextStyle(color: Colors.white)),
                        onPressed: () => Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => AddSensorScreen(channelId: channelId),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),

                  // ── Charts ───────────────────────────────────────
                  _buildChartSection("pH Level Chart", _generateSpots(phData), phTimestamps),
                  const SizedBox(height: 20),
                  _buildChartSection("Rainfall Chart", _generateSpots(rainfallData), rainfallTimestamps),
                  const SizedBox(height: 20),
                  _buildChartSection("Humidity Chart", _generateSpots(humidityData), humidTempTimestamps),
                  const SizedBox(height: 20),
                  _buildChartSection("Temperature Chart", _generateSpots(tempData), humidTempTimestamps),
                  const SizedBox(height: 20),
                  _buildChartSection("Nitrogen Chart", _generateSpots(nitrogenData), npkTimestamps),
                  const SizedBox(height: 20),
                  _buildChartSection("Phosphorous Chart", _generateSpots(phosphorousData), npkTimestamps),
                  const SizedBox(height: 20),
                  _buildChartSection("Potassium Chart", _generateSpots(potassiumData), npkTimestamps),
                  const SizedBox(height: 20),

                  // ── Crop Recommendations ─────────────────────────
                  Card(
                    elevation: 2,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    child: ListTile(
                      leading: const Icon(Icons.eco, color: Colors.green),
                      title: const Text('Crop Recommendations',
                          style: TextStyle(fontWeight: FontWeight.bold)),
                      subtitle: cropRecommendations.isNotEmpty
                          ? Text(
                              'Top: ${cropRecommendations.first['crop']} '
                              '(${cropRecommendations.first['accuracy'].toStringAsFixed(2)}%)',
                            )
                          : const Text('No data yet'),
                      trailing: const Icon(Icons.arrow_forward_ios, size: 16),
                      onTap: () => Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => CropRecommendationsPage(
                            recommendations: cropRecommendations,
                            channelId: channelId,
                          ),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                ],
              ),
            ),
    );
  }

  Widget _buildChartSection(String title, List<FlSpot> spots, List<String> timestamps) {
    String chartDataType = "";
    if (title == "pH Level Chart") chartDataType = "ph";
    else if (title == "Rainfall Chart") chartDataType = "rainfall";
    else if (title == "Humidity Chart") chartDataType = "humidity";
    else if (title == "Temperature Chart") chartDataType = "temperature";
    else if (title == "Nitrogen Chart") chartDataType = "nitrogen";
    else if (title == "Phosphorous Chart") chartDataType = "phosphorous";
    else if (title == "Potassium Chart") chartDataType = "potassium";

    if (spots.isEmpty) {
      return Column(
        children: [
          Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 10),
          const Text("No data available", style: TextStyle(color: Colors.grey)),
        ],
      );
    }

    double minXValue = spots.first.x;
    double maxXValue = spots.last.x;
    double minYValue = spots.map((s) => s.y).reduce((a, b) => a < b ? a : b);
    double maxYValue = spots.map((s) => s.y).reduce((a, b) => a > b ? a : b);

    return Column(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(title),
            DropdownButton<String>(
              value: selectedChartTypes[title],
              items: ["Spline Chart", "Line Chart", "Bar Chart"]
                  .map((type) => DropdownMenuItem(value: type, child: Text(type)))
                  .toList(),
              onChanged: (value) {
                setState(() => selectedChartTypes[title] = value!);
              },
            ),
          ],
        ),
        SizedBox(
          height: 300,
          child: selectedChartTypes[title] == "Bar Chart"
              ? BarChart(
                  BarChartData(
                    minY: minYValue,
                    maxY: maxYValue,
                    barGroups: _getBarChartData(spots),
                    titlesData: FlTitlesData(
                      bottomTitles: AxisTitles(
                        sideTitles: SideTitles(
                          showTitles: true,
                          getTitlesWidget: (value, meta) {
                            int index = value.toInt();
                            if (index >= 0 && index < timestamps.length) {
                              return Text(timestamps[index],
                                  style: const TextStyle(fontSize: 10));
                            }
                            return const Text('');
                          },
                        ),
                      ),
                    ),
                  ),
                )
              : LineChart(
                  LineChartData(
                    minX: minXValue,
                    maxX: maxXValue,
                    minY: minYValue,
                    maxY: maxYValue,
                    lineBarsData: [
                      _getChartData(spots, selectedChartTypes[title].toString()),
                    ],
                    titlesData: FlTitlesData(
                      bottomTitles: AxisTitles(
                        sideTitles: SideTitles(
                          showTitles: true,
                          getTitlesWidget: (value, meta) {
                            int index = value.toInt();
                            if (index >= 0 && index < timestamps.length) {
                              return Text(timestamps[index],
                                  style: const TextStyle(fontSize: 10));
                            }
                            return const Text('');
                          },
                        ),
                      ),
                    ),
                  ),
                ),
        ),
        const SizedBox(height: 10),
        TextButton.icon(
          onPressed: () => _showShareChartDialog(title, spots, chartDataType, timestamps),
          icon: const Icon(Icons.share),
          label: const Text("Share Chart"),
          style: TextButton.styleFrom(
            foregroundColor: Colors.white,
            backgroundColor: Colors.green,
          ),
        ),
      ],
    );
  }

  LineChartBarData _getChartData(List<FlSpot> spots, String chartType) {
    switch (chartType) {
      case "Line Chart":
        return LineChartBarData(
          spots: spots,
          isCurved: false,
          color: Colors.blue,
          belowBarData: BarAreaData(show: false),
        );
      case "Bar Chart":
        return LineChartBarData(
          spots: spots,
          isCurved: false,
          barWidth: 8,
          color: Colors.green,
          dotData: const FlDotData(show: false),
          belowBarData: BarAreaData(show: false),
        );
      default:
        return LineChartBarData(
          spots: spots,
          isCurved: true,
          color: const Color.fromARGB(255, 0, 244, 45),
          belowBarData: BarAreaData(show: false),
        );
    }
  }

  List<BarChartGroupData> _getBarChartData(List<FlSpot> spots) {
    return spots
        .map((spot) => BarChartGroupData(
              x: spot.x.toInt(),
              barRods: [BarChartRodData(toY: spot.y, color: Colors.green, width: 8)],
            ))
        .toList();
  }

  void _showShareChartDialog(
      String title, List<FlSpot> spots, String chartDataType, List<String> timestamps) {
    final chartNameController = TextEditingController(text: title);
    final startDateController = TextEditingController(
      text: timestamps.isNotEmpty ? _formatDateForApi(timestamps.first) : '',
    );
    final endDateController = TextEditingController(
      text: timestamps.isNotEmpty ? _formatDateForApi(timestamps.last) : '',
    );

    String? generatedEmbedCode;
    bool embedGenerated = false;

    showDialog(
      context: context,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              title: const Text("Share Chart"),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text("Chart Name"),
                    const SizedBox(height: 4),
                    TextField(
                      controller: chartNameController,
                      decoration: const InputDecoration(border: OutlineInputBorder()),
                    ),
                    const SizedBox(height: 12),
                    const Text("Start Date"),
                    const SizedBox(height: 4),
                    TextField(
                      controller: startDateController,
                      readOnly: true,
                      decoration: const InputDecoration(
                        border: OutlineInputBorder(),
                        hintText: 'YYYY-MM-DD',
                      ),
                      onTap: () async {
                        final picked = await showDatePicker(
                          context: context,
                          initialDate:
                              DateTime.tryParse(startDateController.text) ?? DateTime.now(),
                          firstDate: DateTime(2000),
                          lastDate: DateTime(2100),
                        );
                        if (picked != null) {
                          setDialogState(() {
                            startDateController.text =
                                DateFormat('yyyy-MM-dd').format(picked);
                          });
                        }
                      },
                    ),
                    const SizedBox(height: 12),
                    const Text("End Date"),
                    const SizedBox(height: 4),
                    TextField(
                      controller: endDateController,
                      readOnly: true,
                      decoration: const InputDecoration(
                        border: OutlineInputBorder(),
                        hintText: 'YYYY-MM-DD',
                      ),
                      onTap: () async {
                        final picked = await showDatePicker(
                          context: context,
                          initialDate:
                              DateTime.tryParse(endDateController.text) ?? DateTime.now(),
                          firstDate: DateTime(2000),
                          lastDate: DateTime(2100),
                        );
                        if (picked != null) {
                          setDialogState(() {
                            endDateController.text =
                                DateFormat('yyyy-MM-dd').format(picked);
                          });
                        }
                      },
                    ),
                    const SizedBox(height: 16),
                    ElevatedButton(
                      onPressed: () {
                        final start = startDateController.text;
                        final end = endDateController.text;
                        if (start.isEmpty || end.isEmpty) return;
                        setDialogState(() {
                          generatedEmbedCode =
                              '$_baseUrl/mychannel/embed/channel/$channelId/${chartDataType}Chart/$start/$end/';
                          embedGenerated = true;
                        });
                      },
                      child: const Text("Generate Embed Code"),
                    ),
                    if (embedGenerated) ...[
                      const SizedBox(height: 16),
                      ElevatedButton(
                        style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
                        onPressed: () async {
                          Navigator.of(context).pop();
                          await shareChart(
                            chartNameController.text,
                            spots,
                            chartDataType,
                            startDateController.text,
                            endDateController.text,
                            selectedChartTypes[title] ?? "Spline Chart",
                          );
                        },
                        child: const Text("Share to PlantFeed",
                            style: TextStyle(color: Colors.white)),
                      ),
                      const SizedBox(height: 12),
                      const Text("Embed Code"),
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          Expanded(
                            child: TextField(
                              readOnly: true,
                              controller:
                                  TextEditingController(text: generatedEmbedCode),
                              decoration:
                                  const InputDecoration(border: OutlineInputBorder()),
                            ),
                          ),
                          IconButton(
                            icon: const Icon(Icons.copy),
                            onPressed: () {
                              Clipboard.setData(
                                  ClipboardData(text: generatedEmbedCode ?? ''));
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(content: Text('Copied to clipboard')),
                              );
                            },
                          ),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: const Text("Cancel"),
                ),
              ],
            );
          },
        );
      },
    );
  }

  Future<void> _toggleApi(bool value) async {
    final action = value ? 'permit_API' : 'forbid_API';
    final url = 'http://10.0.2.2:8000/mychannel/$channelId/$action';
    try {
      final response = await http.post(
        Uri.parse(url),
        headers: {'Content-Type': 'application/json'},
      );
      if (response.statusCode == 200) {
        setState(() => allowApi = value);
      } else {
        _showErrorDialog('Failed to update API access.');
      }
    } catch (e) {
      _showErrorDialog('An error occurred: $e');
    }
  }

  Future<void> shareChannel() async {
    final url = 'http://10.0.2.2:8000/mychannel/$channelId/share';
    try {
      final response = await http.post(
        Uri.parse(url),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({"plantfeed_user_id": _plantfeedUserId}),
      );
      if (response.statusCode == 200) {
        final responseData = jsonDecode(response.body);
        if (responseData["success"] != null) {
          _showDialog("Channel Shared", responseData["success"]);
        } else {
          _showDialog("Error", "Failed to share the channel.");
        }
      } else {
        _showDialog("Error", "Error: ${response.statusCode}");
      }
    } catch (e) {
      _showDialog("Error", "An unexpected error occurred: $e");
    }
  }

  Future<void> shareChart(
    String chartTitle,
    List<FlSpot> spots,
    String chartDataType,
    String startDate,
    String endDate,
    String chartType,
  ) async {
    final String formattedStartDate = _formatDateForApi(startDate);
    final String formattedEndDate = _formatDateForApi(endDate);
    final encodedTitle = Uri.encodeComponent(chartTitle);
    final url =
        'http://10.0.2.2:8000/mychannel/$channelId/share_chart/${chartDataType}Chart/$formattedStartDate/$formattedEndDate/$encodedTitle/';

    final payload = {
      "plantfeed_user_id": _plantfeedUserId,
      "data_points": spots.map((spot) => {"x": spot.x, "y": spot.y}).toList(),
    };

    try {
      final response = await http.post(
        Uri.parse(url),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(payload),
      );

      if (response.statusCode == 200) {
        final responseData = jsonDecode(response.body);
        if (responseData["success"] != null) {
          _showDialog("Chart Shared", responseData["success"]);
        } else {
          _showErrorDialog("Failed to share the chart.");
        }
      } else {
        _showErrorDialog("Error: ${response.statusCode}");
      }
    } catch (e) {
      debugPrint('Error sharing chart: $e');
      _showErrorDialog("An unexpected error occurred.");
    }
  }

  void _showDialog(String title, String message) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text("OK"),
          ),
        ],
      ),
    );
  }

  void _showErrorDialog(String message) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Error"),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text("OK"),
          ),
        ],
      ),
    );
  }
}
