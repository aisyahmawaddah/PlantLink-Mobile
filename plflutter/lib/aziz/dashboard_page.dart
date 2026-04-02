import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:intl/intl.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:plflutter/aziz/dashboard_functions.dart';
import 'package:plflutter/aziz/connect_sensor_page.dart';
import 'package:plflutter/aziz/configure_sensor_page.dart';
import 'package:plflutter/viewchannel_page.dart';
import 'package:shared_preferences/shared_preferences.dart';

class DashboardScreen extends StatefulWidget {
  final String channelId;
  const DashboardScreen({super.key, required this.channelId});

  @override
  _DashboardScreenState createState() => _DashboardScreenState();
}

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
      _plantfeedUserId = prefs.getString('plantfeed_user_id') ?? '1';
    });
  }

  Future<void> fetchSensorData() async {
    try {
      final response = await http.get(
        Uri.parse('http://10.0.2.2:8000/mychannel/$channelId/get_dashboard_data/')
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);

        setState(() {
          phData = List<double>.from(
            (data['ph_values'] as List?)?.map((v) => double.tryParse(v.toString()) ?? 0.0) ?? []
          );
          rainfallData = List<double>.from(
            (data['rainfall_values'] as List?)?.map((v) => double.tryParse(v.toString()) ?? 0.0) ?? []
          );
          humidityData = List<double>.from(
            (data['humid_values'] as List?)?.map((v) => double.tryParse(v.toString()) ?? 0.0) ?? []
          );
          tempData = List<double>.from(
            (data['temp_values'] as List?)?.map((v) => double.tryParse(v.toString()) ?? 0.0) ?? []
          );
          nitrogenData = List<double>.from(
            (data['nitrogen_values'] as List?)?.map((v) => double.tryParse(v.toString()) ?? 0.0) ?? []
          );
          phosphorousData = List<double>.from(
            (data['phosphorous_values'] as List?)?.map((v) => double.tryParse(v.toString()) ?? 0.0) ?? []
          );
          potassiumData = List<double>.from(
            (data['potassium_values'] as List?)?.map((v) => double.tryParse(v.toString()) ?? 0.0) ?? []
          );

          phTimestamps = List<String>.from(data['timestamps'] ?? []);
          rainfallTimestamps = List<String>.from(data['rainfall_timestamps'] ?? []);
          humidTempTimestamps = List<String>.from(data['timestamps_humid_temp'] ?? []);
          npkTimestamps = List<String>.from(data['timestamps_NPK'] ?? []);

          isLoading = false;
        });
      } else {
        setState(() { isLoading = false; });
        debugPrint('Failed to load sensor data. Status Code: ${response.statusCode}');
      }
    } catch (e) {
      setState(() { isLoading = false; });
      debugPrint('Error fetching data: $e');
    }
  }

  List<FlSpot> _generateSpots(List<double> data) {
    return List.generate(data.length, (index) {
      return FlSpot(index.toDouble(), data[index]);
    });
  }

  Future<bool> _onWillPop() async {
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (context) => const ViewChannel()),
    );
    return Future.value(false);
  }

  // Parses a timestamp string to yyyy-MM-dd regardless of input format
  String _formatDateForApi(String timestamp) {
    final s = timestamp.length >= 10 ? timestamp.substring(0, 10) : timestamp;
    // Already yyyy-MM-dd
    if (RegExp(r'^\d{4}-\d{2}-\d{2}$').hasMatch(s)) return s;
    // Try dd-MM-yyyy
    try {
      return DateFormat("yyyy-MM-dd").format(DateFormat("dd-MM-yyyy").parse(s));
    } catch (_) {}
    // Return raw as fallback
    return s;
  }

  @override
  Widget build(BuildContext context) {
    return WillPopScope(
      onWillPop: _onWillPop,
      child: Scaffold(
        appBar: AppBar(
          title: const Text("Dashboard"),
          actions: [
            IconButton(
              icon: const Icon(Icons.refresh),
              onPressed: fetchSensorData,
            ),
          ],
        ),
        body: isLoading
            ? const Center(child: CircularProgressIndicator())
            : SingleChildScrollView(
                child: Column(
                  children: [
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
                    const SizedBox(height: 15),
                    Padding(
                      padding: const EdgeInsets.all(8.0),
                      child: Column(
                        children: [
                          const SizedBox(width: 10),
                          GreenButtonWithIcon(
                            label: 'Share Channel',
                            onPressed: shareChannel,
                          ),
                          const SizedBox(width: 10),
                          GreenButtonWithIcon(
                            label: 'Configure Sensor',
                            onPressed: () {
                              Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (context) => ConfigureSensorPage(channelId: channelId)
                                ),
                              );
                            },
                          ),
                          const SizedBox(width: 10),
                          GreenButtonWithIcon(
                            label: 'Connect Sensor',
                            onPressed: () {
                              Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (context) => AddSensorScreen(channelId: channelId)
                                ),
                              );
                            },
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
      ),
    );
  }

  Widget _buildChartSection(String title, List<FlSpot> spots, List<String> timestamps) {
    String chartDataType = "";
    if (title == "pH Level Chart") { chartDataType = "ph"; }
    else if (title == "Rainfall Chart") { chartDataType = "rainfall"; }
    else if (title == "Humidity Chart") { chartDataType = "humidity"; }
    else if (title == "Temperature Chart") { chartDataType = "temperature"; }
    else if (title == "Nitrogen Chart") { chartDataType = "nitrogen"; }
    else if (title == "Phosphorous Chart") { chartDataType = "phosphorous"; }
    else if (title == "Potassium Chart") { chartDataType = "potassium"; }

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
    double minYValue = spots.map((spot) => spot.y).reduce((a, b) => a < b ? a : b);
    double maxYValue = spots.map((spot) => spot.y).reduce((a, b) => a > b ? a : b);

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
                setState(() {
                  selectedChartTypes[title] = value!;
                });
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
                              return Text(timestamps[index], style: const TextStyle(fontSize: 10));
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
                              return Text(timestamps[index], style: const TextStyle(fontSize: 10));
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
          onPressed: () async {
            if (timestamps.isEmpty) {
              _showErrorDialog("Timestamps are required to share the chart.");
              return;
            }
            String startDate = timestamps.first;
            String endDate = timestamps.last;
            String chartType = selectedChartTypes[title] ?? "Spline Chart";
            await shareChart(title, spots, chartDataType, startDate, endDate, chartType);
          },
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
    return spots.map((spot) {
      return BarChartGroupData(
        x: spot.x.toInt(),
        barRods: [
          BarChartRodData(toY: spot.y, color: Colors.green, width: 8),
        ],
      );
    }).toList();
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

  Future<void> shareChart(String chartTitle, List<FlSpot> spots, String chartDataType,
      String startDate, String endDate, String chartType) async {

    final String formattedStartDate = _formatDateForApi(startDate);
    final String formattedEndDate = _formatDateForApi(endDate);
    final encodedTitle = Uri.encodeComponent(chartTitle);
    final url = 'http://10.0.2.2:8000/mychannel/$channelId/share_chart/${chartDataType}Chart/$formattedStartDate/$formattedEndDate/$encodedTitle/';

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
          showDialog(
            context: context,
            builder: (context) {
              return AlertDialog(
                title: const Text("Chart Shared"),
                content: Text(responseData["success"]),
                actions: [
                  TextButton(
                    onPressed: () => Navigator.of(context).pop(),
                    child: const Text("OK"),
                  ),
                ],
              );
            },
          );
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
      builder: (context) {
        return AlertDialog(
          title: Text(title),
          content: Text(message),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text("OK"),
            ),
          ],
        );
      },
    );
  }

  void _showErrorDialog(String message) {
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text("Error"),
          content: Text(message),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text("OK"),
            ),
          ],
        );
      },
    );
  }
}
