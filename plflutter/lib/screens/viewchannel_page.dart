import 'package:flutter/material.dart';
import 'package:plflutter/screens/deletechannel.dart';
import 'package:plflutter/screens/editchannel_page.dart';
import 'package:plflutter/screens/dashboard_page.dart';
import 'fetch_channel.dart';
// import 'dart:convert';
// import 'package:http/http.dart' as http;

class ViewChannel extends StatelessWidget {
  const ViewChannel({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('View Channel'),
        backgroundColor: Colors.green[300],
        centerTitle: true,
      ),
      body: Column(
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blue[200],
                  ),
                  onPressed: () {
                    Navigator.pushNamed(context, '/channels/create');
                  },
                  child: const Text('Create +'),
                ),
              ),

              Container(
                padding: const EdgeInsets.all(10),
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blue[200],
                  ),
                  onPressed: null,
                  child: const Text('Manage Sensors'),
                ),
              ),
            ],
          ),
          const BasePage(),
          const SizedBox(height: 20),
          const Expanded(child: ChannelsList()),
        ],
      ),
    );
  }
}

class BasePage extends StatefulWidget {
  const BasePage({super.key});

  @override
  State<BasePage> createState() => _BasePageState();
}

class _BasePageState extends State<BasePage> {
  int totalChannels = 0;
  int totalSensors = 0;
  int publicChannels = 0;
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    fetchChannelStatistics();
  }

  Future<void> fetchChannelStatistics() async {
    try {
      final stats = await ChannelService().fetchChannelStatistics();
      setState(() {
        totalChannels = stats['totalChannels'] ?? 0;
        totalSensors = stats['totalSensors'] ?? 0;
        publicChannels = stats['publicChannels'] ?? 0;
        isLoading = false;
      });
    } catch (e) {
      setState(() {
        isLoading = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error fetching stats: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          color: Colors.green[300],
          padding: const EdgeInsets.all(10),
          child: isLoading
              ? const Center(child: CircularProgressIndicator())
              : ChannelStats(
                  totalChannels: totalChannels,
                  totalSensors: totalSensors,
                  publicChannels: publicChannels,
                ),
        ),
      ],
    );
  }
}

class ChannelStats extends StatelessWidget {
  final int totalChannels;
  final int totalSensors;
  final int publicChannels;

  const ChannelStats({
    super.key,
    required this.totalChannels,
    required this.totalSensors,
    required this.publicChannels,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(10),
          child: Row(
            children: [
              Image.asset('assets/plant1.png', width: 25),
              const Text(' '),
              const Text('Total Channels: '),
              Text(totalChannels.toString()),

              const Expanded(child: SizedBox()),

              Image.asset('assets/plant1.png', width: 25),
              const Text(' '),
              const Text('Registered Sensors: '),
              Text(totalSensors.toString()),
            ],
          ),
        ),
        Container(
          padding: const EdgeInsets.all(10),
          child: Row(
            children: [
              Image.asset('assets/plant1.png', width: 25),
              const Text(' '),
              const Text('Public Channels: '),
              Text(publicChannels.toString()),

              const Expanded(child: SizedBox()),
            ],
          ),
        ),
      ],
    );
  }
}

class ChannelsList extends StatefulWidget {
  const ChannelsList({super.key});

  @override
  State<ChannelsList> createState() => _ChannelsListState();
}

class _ChannelsListState extends State<ChannelsList> {
  List<Map<String, dynamic>> _allChannels = [];
  List<Map<String, dynamic>> _filteredChannels = [];
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadChannels();
  }

  Future<void> _loadChannels() async {
    setState(() {
      isLoading = true;
    });
    try {
      final channels = await ChannelService().fetchChannels();
      setState(() {
        _allChannels = channels;
        _filteredChannels = channels;
        isLoading = false;
      });
    } catch (e) {
      setState(() {
        isLoading = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error loading channels: $e')),
      );
    }
  }

  void _filterChannels(String query) {
    setState(() {
      if (query.isEmpty) {
        _filteredChannels = _allChannels;
      } else {
        _filteredChannels = _allChannels
            .where((channel) =>
                channel['channel_name'] != null &&
                channel['channel_name']
                    .toLowerCase()
                    .contains(query.toLowerCase()))
            .toList();
      }
    });
  }

  Future<void> _navigateToPage(
      BuildContext context, String action, Map<String, dynamic> channel) async {
    if (action == "Edit") {
      final result = await Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => EditChannelPage(channel: channel),
        ),
      );
      if (result == true) {
        _loadChannels();
        
      }
    } else {
      // Navigate to the DashboardScreen for "View" action
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => DashboardScreen(channelId: channel['_id']),
        // builder: (context) => PlaceholderPage(action: action, channelName: channel['channel_name']),
      ),
    );
    }
  }

  void _showDeleteDialog(Map<String, dynamic> channel) {
  if (channel['sensor'] != null && channel['sensor'].isNotEmpty) {
    // Show warning dialog if sensors are present
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Cannot Delete Channel'),
          content: const Text('This channel has sensors connected. Please delete the sensors first before deleting the channel.'),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(context).pop(); // Close the dialog
              },
              child: const Text('OK'),
            ),
          ],
        );
      },
    );
  } else {
    // Show delete confirmation dialog if no sensors are present
    showDialog(
      context: context,
      builder: (context) {
        return DeleteChannelDialog(
          channelId: channel['_id'].toString(),
          onDelete: _loadChannels,
        );
      },
    );
  }
}


  @override
  Widget build(BuildContext context) {
    return isLoading
        ? const Center(child: CircularProgressIndicator())
        : Padding(
            padding: const EdgeInsets.all(8.0),
            child: Column(
              children: [
                Padding(
                  padding: const EdgeInsets.all(8.0),
                  child: TextField(
                    decoration: const InputDecoration(
                      labelText: "Search Channels",
                      prefixIcon: Icon(Icons.search),
                      border: OutlineInputBorder(),
                    ),
                    onChanged: _filterChannels,
                  ),
                ),
                Expanded(
                  child: _filteredChannels.isEmpty
                      ? const Center(child: Text("No channels found"))
                      : SingleChildScrollView(
                        scrollDirection: Axis.vertical,
                        child: PaginatedDataTable(
                            header: const Text("Channels"),
                            rowsPerPage: 6, // Set your rows per page
                            columns: const [
                              DataColumn(label: Text('Channel Name')),
                              DataColumn(label: Text('Description')),
                              DataColumn(label: Text('Date Created')),
                              DataColumn(label: Text('Date Modified')),
                              DataColumn(label: Text('Sensors')),
                              DataColumn(label: Text('Action')),
                            ],
                            source: ChannelDataSource(_filteredChannels,context,_navigateToPage,_showDeleteDialog),
                          ),
                      ),
                ),
              ],
            ),
          );
  }
}

class ChannelDataSource extends DataTableSource {
  final List<Map<String, dynamic>> _channels;
  final BuildContext context;
  final Future<void> Function(BuildContext, String, Map<String, dynamic>) navigateToPage;
  final void Function(Map<String, dynamic>) showDeleteDialog;

  ChannelDataSource(this._channels, this.context, this.navigateToPage, this.showDeleteDialog);

  @override
  DataRow getRow(int index) {
    final channel = _channels[index];
    int sensorCount = channel['sensor_count'] ?? 0;
    return DataRow(cells: [
      DataCell(Text(channel['channel_name'] ?? '')),
      DataCell(Text(channel['description'] ?? '')),
      DataCell(Text(channel['date_created'] ?? '')),
      DataCell(Text(channel['date_modified'] ?? '')),
      DataCell(Text(sensorCount.toString())),
      DataCell(Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          IconButton(
            icon: const Icon(Icons.remove_red_eye, color: Colors.blue),
            tooltip: "View Channel",
            onPressed: () => navigateToPage(context, "View", channel),
          ),
          IconButton(
            icon: const Icon(Icons.edit, color: Colors.orange),
            tooltip: "Edit Channel",
            onPressed: () => navigateToPage(context, "Edit", channel),
          ),
          IconButton(
            icon: const Icon(Icons.delete, color: Colors.red),
            tooltip: "Delete Channel",
            onPressed: () => showDeleteDialog(channel),
          ),
        ],
      )),
    ]);
  }

  @override
  int get rowCount => _channels.length;

  @override
  bool get isRowCountApproximate => false;

  @override
  int get selectedRowCount => 0;
}


class PlaceholderPage extends StatelessWidget {
  final String action;
  final String channelName;

  const PlaceholderPage({super.key, required this.action, required this.channelName});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("$action Channel")),
      body: Center(
        child: Text(
          "This is the placeholder page for $action on channel: $channelName",
          style: const TextStyle(fontSize: 18),
          textAlign: TextAlign.center,
        ),
      ),
    );
  }
}