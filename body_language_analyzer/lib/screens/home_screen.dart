import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../services/api_service.dart';
import '../services/auth_service.dart';

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

  Future<void> _signOut() async {
    final auth = context.read<AuthService>();
    await auth.signOut();
    // AuthGate will handle navigation
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Body Language & Voice Analyzer'),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: _signOut,
            tooltip: 'Logout',
          ),
        ],
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
                    const SizedBox(height: 16),
                    ElevatedButton.icon(
                      onPressed: () {
                        // TODO: Navigate to Upload screen (Phase 3)
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Upload screen coming in Phase 3')),
                        );
                      },
                      icon: const Icon(Icons.upload_file),
                      label: const Text('Upload Video'),
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                      ),
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