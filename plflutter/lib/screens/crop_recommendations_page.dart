import 'package:flutter/material.dart';

class CropRecommendationsPage extends StatelessWidget {
  final List<Map<String, dynamic>> recommendations;
  final String channelId;

  const CropRecommendationsPage({
    super.key,
    required this.recommendations,
    required this.channelId,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Crop Recommendations')),
      body: recommendations.isEmpty
          ? const Center(child: Text('No crop recommendations available.'))
          : Column(
              children: [
                Container(
                  color: Colors.grey[200],
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                  child: const Row(
                    children: [
                      Expanded(
                        flex: 2,
                        child: Text('Crop',
                            style: TextStyle(fontWeight: FontWeight.bold)),
                      ),
                      Expanded(
                        child: Text('Accuracy (%)',
                            style: TextStyle(fontWeight: FontWeight.bold)),
                      ),
                    ],
                  ),
                ),
                Expanded(
                  child: ListView.builder(
                    itemCount: recommendations.length,
                    itemBuilder: (context, index) {
                      final item = recommendations[index];
                      final isEven = index % 2 == 0;
                      return Container(
                        color: isEven ? Colors.white : Colors.grey[100],
                        padding: const EdgeInsets.symmetric(
                            horizontal: 16, vertical: 12),
                        child: Row(
                          children: [
                            Expanded(
                              flex: 2,
                              child: Text(
                                item['crop'] ?? '',
                                style: const TextStyle(fontSize: 15),
                              ),
                            ),
                            Expanded(
                              child: Text(
                                (item['accuracy'] as num).toStringAsFixed(2),
                                style: const TextStyle(fontSize: 15),
                              ),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
                ),
              ],
            ),
    );
  }
}
