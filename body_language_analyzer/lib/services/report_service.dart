import 'package:supabase_flutter/supabase_flutter.dart';
import '../models/report.dart';

class ReportService {
  final SupabaseClient _client = Supabase.instance.client;

  Future<Report?> getReport(String reportId) async {
    final userId = _client.auth.currentUser?.id;
    if (userId == null) throw Exception('User not authenticated');

    final response = await _client
        .from('reports')
        .select()
        .eq('id', reportId)
        .eq('user_id', userId)
        .maybeSingle();

    if (response == null) return null;
    return Report.fromJson(response as Map<String, dynamic>);
  }

  Future<List<Report>> getUserReports() async {
    final userId = _client.auth.currentUser?.id;
    if (userId == null) throw Exception('User not authenticated');

    final response = await _client
        .from('reports')
        .select()
        .eq('user_id', userId)
        .order('created_at', ascending: false);

    return (response as List)
        .map((json) => Report.fromJson(json as Map<String, dynamic>))
        .toList();
  }

  Future<void> updateReportStatus({
    required String reportId,
    required ReportStatus status,
    int? voiceScore,
    int? bodyScore,
    int? confidenceScore,
    Map<String, dynamic>? reportJson,
    String? errorMessage,
  }) async {
    final userId = _client.auth.currentUser?.id;
    if (userId == null) throw Exception('User not authenticated');

    final updates = <String, dynamic>{
      'status': status.name,
    };

    if (voiceScore != null) updates['voice_score'] = voiceScore;
    if (bodyScore != null) updates['body_score'] = bodyScore;
    if (confidenceScore != null) updates['confidence_score'] = confidenceScore;
    if (reportJson != null) updates['report_json'] = reportJson;
    if (errorMessage != null) updates['error_message'] = errorMessage;

    await _client
        .from('reports')
        .update(updates)
        .eq('id', reportId)
        .eq('user_id', userId);
  }

  Future<void> deleteReport(String reportId) async {
    final userId = _client.auth.currentUser?.id;
    if (userId == null) throw Exception('User not authenticated');

    await _client
        .from('reports')
        .delete()
        .eq('id', reportId)
        .eq('user_id', userId);
  }
}