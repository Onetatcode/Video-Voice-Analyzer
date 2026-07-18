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
}