import 'package:flutter/material.dart';
import 'package:plflutter/screens/deletechannel.dart';
import 'package:plflutter/screens/editchannel_page.dart';
import 'package:plflutter/screens/dashboard_page.dart';
import 'package:plflutter/screens/fetch_channel.dart';

class ViewChannel extends StatefulWidget {
  const ViewChannel({super.key});

  @override
  State<ViewChannel> createState() => _ViewChannelState();
}

class _ViewChannelState extends State<ViewChannel> {
  final GlobalKey<_BasePageState> _statsKey = GlobalKey<_BasePageState>();
  final GlobalKey<_ChannelsListState> _listKey = GlobalKey<_ChannelsListState>();

  Future<void> _refreshAll() async {
    await Future.wait([
      _statsKey.currentState?.fetchChannelStatistics() ?? Future.value(),
      _listKey.currentState?._loadChannels() ?? Future.value(),
    ]);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'My Channel',
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
        ),
        backgroundColor: const Color(0xFF4CAF50),
        centerTitle: true,
        automaticallyImplyLeading: false,
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 10),
            child: IconButton(
              icon: const Icon(Icons.refresh, color: Colors.white),
              tooltip: 'Refresh',
              onPressed: _refreshAll,
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          BasePage(key: _statsKey),
          const SizedBox(height: 8),
          Expanded(child: ChannelsList(key: _listKey)),
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
    return Container(
      color: const Color(0xFF4CAF50),
      padding: const EdgeInsets.all(10),
      child: isLoading
          ? const Center(child: CircularProgressIndicator(color: Colors.white))
          : ChannelStats(
              totalChannels: totalChannels,
              totalSensors: totalSensors,
              publicChannels: publicChannels,
            ),
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
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: [
            _StatCard(
              icon: Icons.sensors,
              label: 'Total Channels',
              value: totalChannels.toString(),
            ),
            _StatCard(
              icon: Icons.device_hub,
              label: 'Registered Sensors',
              value: totalSensors.toString(),
            ),
            _StatCard(
              icon: Icons.public,
              label: 'Public Channels',
              value: publicChannels.toString(),
            ),
          ],
        ),
      ],
    );
  }
}

class _StatCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _StatCard({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Icon(icon, color: Colors.white, size: 22),
        const SizedBox(height: 4),
        Text(
          value,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 20,
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          label,
          style: const TextStyle(color: Colors.white70, fontSize: 11),
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
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => DashboardScreen(channelId: channel['_id']),
        ),
      );
    }
  }

  void _showDeleteDialog(Map<String, dynamic> channel) {
    final int sensorCount = (channel['sensor_count'] ?? 0) as int;
  
    showDialog(
      context: context,
      builder: (context) {
        return DeleteChannelDialog(
          channelId: channel['_id'].toString(),
          sensorCount: sensorCount,
          onDelete: _loadChannels,
        );
      },
    );
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
                  padding: const EdgeInsets.symmetric(
                      horizontal: 8.0, vertical: 4.0),
                  child: TextField(
                    decoration: InputDecoration(
                      labelText: "Search Channels",
                      prefixIcon:
                          const Icon(Icons.search, color: Color(0xFF4CAF50)),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                        borderSide: const BorderSide(
                            color: Color(0xFF4CAF50), width: 2),
                      ),
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
                            header: Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                const Text(
                                  "Channels",
                                  style: TextStyle(
                                      fontWeight: FontWeight.bold,
                                      color: Color(0xFF4CAF50)),
                                ),
                                ElevatedButton.icon(
                                  onPressed: () {
                                    Navigator.pushNamed(context, '/channels/create');
                                  },
                                  icon: const Icon(Icons.add, size: 18),
                                  label: const Text(
                                    'Create',
                                    style: TextStyle(fontWeight: FontWeight.w600),
                                  ),
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: const Color(0xFF4CAF50),
                                    foregroundColor: Colors.white,
                                    elevation: 2,
                                    shape: RoundedRectangleBorder(
                                      borderRadius: BorderRadius.circular(20),
                                    ),
                                    padding: const EdgeInsets.symmetric(
                                        horizontal: 14, vertical: 8),
                                  ),
                                ),
                              ],
                            ),
                            rowsPerPage: 6,
                            columns: const [
                              DataColumn(label: Text('Channel Name')),
                              DataColumn(label: Text('Description')),
                              DataColumn(label: Text('Date Created')),
                              DataColumn(label: Text('Date Modified')),
                              DataColumn(label: Text('Sensors')),
                              DataColumn(label: Text('Action')),
                            ],
                            source: ChannelDataSource(
                              _filteredChannels,
                              context,
                              _navigateToPage,
                              _showDeleteDialog,
                            ),
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
  final Future<void> Function(BuildContext, String, Map<String, dynamic>)
      navigateToPage;
  final void Function(Map<String, dynamic>) showDeleteDialog;

  ChannelDataSource(
      this._channels, this.context, this.navigateToPage, this.showDeleteDialog);

  @override
  DataRow getRow(int index) {
    final channel = _channels[index];
    final int sensorCount = (channel['sensor_count'] ?? 0) as int;

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

  const PlaceholderPage(
      {super.key, required this.action, required this.channelName});

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