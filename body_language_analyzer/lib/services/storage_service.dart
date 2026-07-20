import 'dart:typed_data';
import 'package:supabase_flutter/supabase_flutter.dart';

class StorageService {
  static final StorageService _instance = StorageService._internal();
  factory StorageService() => _instance;
  StorageService._internal();

  final SupabaseClient _client = Supabase.instance.client;

  /// Upload video file to Supabase Storage
  /// Returns the public URL of the uploaded video
  Future<String> uploadVideo(Uint8List videoBytes, String fileName) async {
    final user = _client.auth.currentUser;
    if (user == null) {
      throw Exception('User not authenticated');
    }

    // Generate unique filename
    final uniqueFileName = '${user.id}/${DateTime.now().millisecondsSinceEpoch}_$fileName';
    
    try {
      // Upload bytes to Supabase Storage
      await _client.storage
          .from('videos')
          .uploadBinary(uniqueFileName, videoBytes, fileOptions: const FileOptions(upsert: false));
      
      // Get public URL
      final publicUrl = _client.storage.from('videos').getPublicUrl(uniqueFileName);
      return publicUrl;
    } on StorageException catch (e) {
      throw Exception('Failed to upload video: ${e.message}');
    } catch (e) {
      throw Exception('Failed to upload video: $e');
    }
  }

  /// Delete video from storage
  Future<void> deleteVideo(String videoUrl) async {
    try {
      // Extract file path from URL
      final uri = Uri.parse(videoUrl);
      final pathSegments = uri.pathSegments;
      final bucketIndex = pathSegments.indexOf('videos');
      if (bucketIndex != -1 && bucketIndex + 1 < pathSegments.length) {
        final filePath = pathSegments.sublist(bucketIndex + 1).join('/');
        await _client.storage.from('videos').remove([filePath]);
      }
    } catch (e) {
      // Ignore delete errors
    }
  }
}