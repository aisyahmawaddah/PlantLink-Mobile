// ignore_for_file: use_build_context_synchronously
import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:plflutter/screens/location_dropdown.dart';

class EditChannelPage extends StatefulWidget {
  final Map<String, dynamic> channel;

  const EditChannelPage({super.key, required this.channel});

  @override
  State<EditChannelPage> createState() => _EditChannelPageState();
}

class _EditChannelPageState extends State<EditChannelPage> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _nameController;
  late TextEditingController _descriptionController;
  String? _selectedState;
  String? _selectedDistrict;
  String? _privacy;
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    _nameController = TextEditingController(text: widget.channel['channel_name']);
    _descriptionController = TextEditingController(text: widget.channel['description']);

    // Parse location safely — stored as "State, District"
    final rawLocation = widget.channel['location'] as String? ?? '';
    final parts = rawLocation.split(', ');
    _selectedState = (parts.isNotEmpty && parts[0].trim().isNotEmpty) ? parts[0].trim() : null;
    _selectedDistrict = (parts.length >= 2 && parts[1].trim().isNotEmpty) ? parts[1].trim() : null;

    _privacy = widget.channel['privacy'] ?? 'public';
  }

  Future<void> _saveChanges() async {
    if (!_formKey.currentState!.validate() || _isSubmitting) return;

    setState(() => _isSubmitting = true);

    try {
      final response = await http.put(
        Uri.parse("http://10.0.2.2:8000/mychannel/${widget.channel['_id']}/edit"),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'channel_name': _nameController.text.trim(),
          'description': _descriptionController.text.trim(),
          'location': '${_selectedState ?? ''}, ${_selectedDistrict ?? ''}',
          'privacy': _privacy,
        }),
      );

      final responseData = json.decode(response.body);

      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Channel updated successfully!'),
            backgroundColor: Colors.green,
          ),
        );
        Navigator.pop(context, true);
      } else {
        final errorMsg = responseData['error'] ?? 'Failed to update channel.';
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(errorMsg),
            backgroundColor: Colors.red,
          ),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Connection error. Please try again.'),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Edit Channel'),
        backgroundColor: Colors.green,
        foregroundColor: Colors.white,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextFormField(
                controller: _nameController,
                decoration: const InputDecoration(
                  labelText: 'Channel Name',
                  border: UnderlineInputBorder(),
                ),
                maxLength: 20,
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'Channel name is required';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 8),
              TextFormField(
                controller: _descriptionController,
                decoration: const InputDecoration(
                  labelText: 'Description',
                  border: UnderlineInputBorder(),
                ),
                maxLength: 50,
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'Description is required';
                  }
                  if (value.trim().length < 5) {
                    return 'Description must be at least 5 characters';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),
              const Text(
                'Location',
                style: TextStyle(fontSize: 14, fontWeight: FontWeight.w400, color: Colors.grey),
              ),
              const SizedBox(height: 8),
              LocationDropdown(
                onLocationSelected: (state, district) {
                  setState(() {
                    _selectedState = state;
                    _selectedDistrict = district;
                  });
                },
                initialState: _selectedState,
                initialDistrict: _selectedDistrict,
              ),
              const SizedBox(height: 20),
              DropdownButtonFormField<String>(
                value: _privacy,
                decoration: const InputDecoration(
                  labelText: 'Privacy',
                  border: UnderlineInputBorder(),
                ),
                items: const [
                  DropdownMenuItem(value: 'public', child: Text('public')),
                  DropdownMenuItem(value: 'private', child: Text('private')),
                ],
                onChanged: (value) => setState(() => _privacy = value),
                validator: (value) {
                  if (value == null) return 'Please select a privacy option';
                  return null;
                },
              ),
              const SizedBox(height: 30),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.green,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  onPressed: _isSubmitting ? null : _saveChanges,
                  child: _isSubmitting
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                        )
                      : const Text('Save Changes', style: TextStyle(fontSize: 16)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}