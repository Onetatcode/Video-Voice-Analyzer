import 'dart:async';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:provider/provider.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../services/storage_service.dart';
import '../services/supabase_service.dart';
import '../services/api_service.dart';
import '../models/report.dart';

class UploadScreen extends StatefulWidget {
  const UploadScreen({super.key});

  @override
  State<UploadScreen> createState() => _UploadScreenState();
}

class _UploadScreenState extends State<UploadScreen> {
  PlatformFile? _selectedVideo;
  double _uploadProgress = 0.0;
  bool _isUploading = false;
  String? _errorMessage;
  String? _successMessage;
  Timer? _progressTimer;

  Future<void> _pickVideo() async {
    try {
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.video,
        allowMultiple: false,
        withData: true, // Important for web
      );

      if (result != null && result.files.single.bytes != null) {
        final file = result.files.first;
        final sizeInMB = file.size / (1024 * 1024);
        
        if (sizeInMB > 50) {
          setState(() => _errorMessage = 'Video must be less than 50MB');
          return;
        }

        setState(() {
          _selectedVideo = file;
          _errorMessage = null;
          _successMessage = null;
        });
      }
    } catch (e) {
      setState(() => _errorMessage = 'Failed to pick video: $e');
    }
  }

  Future<void> _uploadVideo() async {
    if (_selectedVideo == null) return;

    setState(() {
      _isUploading = true;
      _uploadProgress = 0.0;
      _errorMessage = null;
      _successMessage = null;
    });

    try {
      final supabaseService = context.read<SupabaseService>();
      final user = supabaseService.client.auth.currentUser;
      if (user == null) throw Exception('User not logged in');

      final api = context.read<ApiService>();
      final storage = StorageService();
      
      _startProgressTimer();

      // Upload to Supabase Storage
      final videoUrl = await storage.uploadVideo(
        _selectedVideo!.bytes!,
        _selectedVideo!.name,
      );

      // Create report row in database
      final reportResponse = await supabaseService.client.from('reports').insert({
        'user_id': user.id,
        'video_url': videoUrl,
        'status': 'pending',
      }).select().single();

      final reportId = reportResponse['id'] as String;

      // Trigger backend processing (fire-and-forget; auto-poller catches misses)
      try {
        await api.startProcessing(reportId);
      } catch (e) {
        print('Backend unreachable — auto-poller will pick up report $reportId');
      }

      _stopProgressTimer();
      
      setState(() {
        _isUploading = false;
        _uploadProgress = 1.0;
        _successMessage = 'Video uploaded! Processing started — check History tab for updates.';
        _selectedVideo = null;
      });

      Future.delayed(const Duration(seconds: 2), () {
        if (mounted) {
          Navigator.of(context).pop();
        }
      });
    } catch (e) {
      _stopProgressTimer();
      setState(() {
        _isUploading = false;
        _uploadProgress = 0.0;
        _errorMessage = 'Upload failed: $e';
      });
    }
  }

  @override
  void dispose() {
    _progressTimer?.cancel();
    super.dispose();
  }

  void _startProgressTimer() {
    _progressTimer = Timer.periodic(const Duration(milliseconds: 100), (_) {
      if (!mounted || !_isUploading) return;
      setState(() {
        _uploadProgress = (_uploadProgress + 0.02).clamp(0.0, 0.9);
      });
    });
  }

  void _stopProgressTimer() {
    _progressTimer?.cancel();
    _progressTimer = null;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Upload Video'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: _isUploading ? null : () => Navigator.pop(context),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Icon(Icons.videocam, size: 80, color: Colors.deepPurple),
              const SizedBox(height: 24),
              const Text(
                'Upload Video for Analysis',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              const Text(
                'Select a front-facing video (max 50MB)',
                style: TextStyle(fontSize: 16, color: Colors.grey),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 32),

              GestureDetector(
                onTap: _isUploading ? null : _pickVideo,
                child: Container(
                  height: 200,
                  decoration: BoxDecoration(
                    color: Colors.grey.shade100,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: _selectedVideo != null ? Colors.deepPurple : Colors.grey.shade300,
                      width: 2,
                    ),
                  ),
                  child: _selectedVideo == null
                      ? Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.cloud_upload_outlined,
                              size: 48,
                              color: Colors.grey.shade400,
                            ),
                            const SizedBox(height: 12),
                            Text(
                              'Tap to select video',
                              style: TextStyle(fontSize: 16, color: Colors.grey.shade600),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'MP4, MOV, AVI supported',
                              style: TextStyle(fontSize: 12, color: Colors.grey.shade500),
                            ),
                          ],
                        )
                      : Stack(
                          fit: StackFit.expand,
                          children: [
                            ClipRRect(
                              borderRadius: BorderRadius.circular(10),
                              child: Container(
                                color: Colors.black12,
                                child: const Center(
                                  child: Icon(Icons.videocam, size: 64, color: Colors.deepPurple),
                                ),
                              ),
                            ),
                            Positioned(
                              top: 8,
                              right: 8,
                              child: CircleAvatar(
                                backgroundColor: Colors.black54,
                                child: IconButton(
                                  icon: const Icon(Icons.close, color: Colors.white, size: 20),
                                  onPressed: () => setState(() => _selectedVideo = null),
                                ),
                              ),
                            ),
                            Positioned(
                              bottom: 8,
                              left: 8,
                              right: 8,
                              child: Container(
                                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                decoration: BoxDecoration(
                                  color: Colors.black54,
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Text(
                                  _selectedVideo!.name,
                                  style: const TextStyle(color: Colors.white, fontSize: 12),
                                  textAlign: TextAlign.center,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                            ),
                          ],
                        ),
                ),
              ),

              const SizedBox(height: 24),

              if (_isUploading || _uploadProgress > 0) ...[
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Uploading... ${(_uploadProgress * 100).toInt()}%',
                      style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
                    ),
                    const SizedBox(height: 8),
                    LinearProgressIndicator(
                      value: _uploadProgress,
                      minHeight: 8,
                      borderRadius: BorderRadius.circular(4),
                    ),
                  ],
                ),
                const SizedBox(height: 24),
              ],

              if (_errorMessage != null)
                Container(
                  padding: const EdgeInsets.all(12),
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    color: Colors.red.shade50,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.red.shade200),
                  ),
                  child: Text(
                    _errorMessage!,
                    style: TextStyle(color: Colors.red.shade800),
                  ),
                ),

              if (_successMessage != null)
                Container(
                  padding: const EdgeInsets.all(12),
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    color: Colors.green.shade50,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.green.shade200),
                  ),
                  child: Text(
                    _successMessage!,
                    style: TextStyle(color: Colors.green.shade800),
                  ),
                ),

              ElevatedButton.icon(
                onPressed: (_selectedVideo != null && !_isUploading) ? _uploadVideo : null,
                icon: _isUploading
                    ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : const Icon(Icons.upload),
                label: Text(_isUploading ? 'Uploading...' : 'Upload & Analyze'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                  textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                ),
              ),

              const SizedBox(height: 16),
              TextButton(
                onPressed: _isUploading ? null : () => Navigator.pop(context),
                child: const Text('Cancel'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}