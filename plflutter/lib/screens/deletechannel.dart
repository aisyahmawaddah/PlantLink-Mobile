// ignore_for_file: use_build_context_synchronously
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:plflutter/config.dart';

class DeleteChannelDialog extends StatefulWidget {
  final String channelId;
  final int sensorCount;
  final VoidCallback onDelete;

  const DeleteChannelDialog({
    required this.channelId,
    required this.sensorCount,
    required this.onDelete,
    super.key,
  });

  @override
  _DeleteChannelDialogState createState() => _DeleteChannelDialogState();
}

class _DeleteChannelDialogState extends State<DeleteChannelDialog> {
  bool _isLoading = false;

  Future<void> _deleteChannel() async {
    setState(() => _isLoading = true);

    final String apiUrl = '$baseUrl/mychannel/delete/';
    try {
      final response = await http.delete(
        Uri.parse('$apiUrl${widget.channelId}'),
      );

      if (response.statusCode == 200) {
        Navigator.of(context).pop();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Channel deleted successfully'),
            backgroundColor: Colors.green,
          ),
        );
        widget.onDelete();
      } else {
        Navigator.of(context).pop();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Failed to delete channel. Please try again.'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } catch (e) {
      Navigator.of(context).pop();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Connection error. Please try again.'),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Delete Channel'),
      content: _isLoading
          ? const SizedBox(
              height: 60,
              child: Center(child: CircularProgressIndicator()),
            )
          : Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Are you sure you want to delete this channel?'),
                if (widget.sensorCount > 0) ...[
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: Colors.orange.shade50,
                      border: Border.all(color: Colors.orange.shade300),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.warning_amber_rounded,
                            color: Colors.orange.shade700, size: 18),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            'This channel has ${widget.sensorCount} active sensor(s) linked. '
                            'Deleting will unlink them.',
                            style: TextStyle(
                                color: Colors.orange.shade800, fontSize: 13),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
      actions: [
        TextButton(
          onPressed: _isLoading ? null : () => Navigator.of(context).pop(),
          child: const Text('Cancel'),
        ),
        TextButton(
          style: TextButton.styleFrom(foregroundColor: Colors.red),
          onPressed: _isLoading ? null : _deleteChannel,
          child: const Text('Delete'),
        ),
      ],
    );
  }
}