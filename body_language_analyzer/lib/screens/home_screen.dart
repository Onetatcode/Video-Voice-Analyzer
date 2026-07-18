import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../services/api_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  String _healthStatus = 'Checking...';
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _checkBackendHealth();
  }

  Future<void> _checkBackendHealth() async {
    try {
      final api = context.read<ApiService>();
      final result = await api.healthCheck();
      setState(() {
        _healthStatus = 'Backend: ${result['status'] ?? 'OK'}';
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _healthStatus = 'Backend unreachable: $e';
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Body Language & Voice Analyzer'),
        centerTitle: true,
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(
                Icons.mic_external_on,
                size: 80,
                color: Colors.deepPurple,
              ),
              const SizedBox(height: 24),
              const Text(
                'Body Language & Voice Analyzer',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 12),
              const Text(
                'Upload a video to analyze your speaking confidence',
                style: TextStyle(fontSize: 16, color: Colors.grey),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 48),
              if (_isLoading)
                const CircularProgressIndicator()
              else
                Column(
                  children: [
                    Text(
                      _healthStatus,
                      style: TextStyle(
                        fontSize: 16,
                        color: _healthStatus.contains('unreachable')
                            ? Colors.red
                            : Colors.green,
                      ),
                    ),
                    const SizedBox(height: 24),
                    ElevatedButton.icon(
                      onPressed: _checkBackendHealth,
                      icon: const Icon(Icons.refresh),
                      label: const Text('Check Backend Again'),
                    ),
                  ],
                ),
            ],
          ),
        ),
      ),
    );
  }
}