import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  late final String _baseUrl;

  void init() {
    _baseUrl = dotenv.env['BACKEND_URL'] ?? 'http://localhost:8000';
  }

  String get baseUrl => _baseUrl;

  Future<Map<String, dynamic>> healthCheck() async {
    final response = await http.get(Uri.parse('$_baseUrl/health'));
    if (response.statusCode == 200) {
      return json.decode(response.body) as Map<String, dynamic>;
    }
    throw Exception('Health check failed: ${response.statusCode}');
  }

  Future<Map<String, dynamic>> startProcessing(String reportId) async {
    final response = await http.post(
      Uri.parse('$_baseUrl/api/v1/process'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'report_id': reportId}),
    );
    if (response.statusCode == 200 || response.statusCode == 202) {
      return json.decode(response.body) as Map<String, dynamic>;
    }
    throw Exception('Start processing failed: ${response.statusCode} - ${response.body}');
  }

}