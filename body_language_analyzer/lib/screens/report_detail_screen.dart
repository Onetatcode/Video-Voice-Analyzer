import 'package:flutter/material.dart';
import 'dart:ui';
import 'package:provider/provider.dart';

import '../models/report.dart';
import '../services/report_service.dart';
import '../widgets/glass_widgets.dart';

class ReportDetailScreen extends StatefulWidget {
  final String reportId;

  const ReportDetailScreen({super.key, required this.reportId});

  @override
  State<ReportDetailScreen> createState() => _ReportDetailScreenState();
}

class _ReportDetailScreenState extends State<ReportDetailScreen> {
  late Future<Report?> _reportFuture;

  @override
  void initState() {
    super.initState();
    _loadReport();
  }

  void _loadReport() {
    _reportFuture = context.read<ReportService>().getReport(widget.reportId);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: FutureBuilder<Report?>(
        future: _reportFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }

          if (snapshot.hasError) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.error_outline, size: 64, color: Colors.red.shade300),
                  const SizedBox(height: 16),
                  Text('Failed to load report', style: Theme.of(context).textTheme.headlineSmall),
                  const SizedBox(height: 8),
                  Text(snapshot.error.toString(), style: Theme.of(context).textTheme.bodyMedium),
                  const SizedBox(height: 16),
                  ElevatedButton.icon(
                    onPressed: () => setState(_loadReport),
                    icon: const Icon(Icons.refresh),
                    label: const Text('Retry'),
                  ),
                ],
              ),
            );
          }

          final report = snapshot.data;
          if (report == null) {
            return const Center(child: Text('Report not found'));
          }

          return CustomScrollView(
            slivers: [
              _buildAppBar(report),
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _buildStatusCard(report),
                      const SizedBox(height: 24),
                      if (report.isComplete) ...[
                        _buildScoreSection(report),
                        const SizedBox(height: 24),
                        _buildDetailsSection(report),
                        const SizedBox(height: 24),
                        _buildActionButtons(report),
                      ] else if (report.isFailed) ...[
                        _buildErrorSection(report),
                        const SizedBox(height: 24),
                        _buildActionButtons(report),
                      ] else ...[
                        _buildProcessingSection(report),
                      ],
                      const SizedBox(height: 32),
                    ],
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildAppBar(Report report) {
    return SliverAppBar(
      expandedHeight: 120,
      pinned: true,
      stretch: true,
      backgroundColor: Colors.transparent,
      flexibleSpace: FlexibleSpaceBar(
        title: Text(report.statusDisplay, style: const TextStyle(fontWeight: FontWeight.w600)),
        centerTitle: true,
        background: ClipRect(
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
            child: Container(
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surface.withOpacity(0.8),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildStatusCard(Report report) {
    Color statusColor;
    IconData statusIcon;
    String statusText;

    switch (report.status) {
      case ReportStatus.complete:
        statusColor = Colors.green;
        statusIcon = Icons.check_circle;
        statusText = 'Analysis Complete';
        break;
      case ReportStatus.processing:
        statusColor = Colors.blue;
        statusIcon = Icons.hourglass_top;
        statusText = 'Processing...';
        break;
      case ReportStatus.pending:
        statusColor = Colors.orange;
        statusIcon = Icons.schedule;
        statusText = 'Pending Analysis';
        break;
      case ReportStatus.failed:
        statusColor = Colors.red;
        statusIcon = Icons.error;
        statusText = 'Analysis Failed';
        break;
    }

    return GlassCard(
      padding: const EdgeInsets.all(20),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: statusColor.withOpacity(0.15),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(statusIcon, color: statusColor, size: 28),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(statusText, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                const SizedBox(height: 4),
                Text(
                  'Uploaded ${_formatDate(report.createdAt)}',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6)),
                ),
              ],
            ),
          ),
          if (report.isComplete)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [Theme.of(context).colorScheme.primary, Theme.of(context).colorScheme.secondary],
                ),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Text(
                '${report.confidenceScore ?? 0}%',
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 18),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildScoreSection(Report report) {
    return GlassCard(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Confidence Scores', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
          const SizedBox(height: 20),
          Row(
            children: [
              Expanded(child: _buildScoreCard('Overall', report.confidenceScore ?? 0, Theme.of(context).colorScheme.primary)),
              const SizedBox(width: 12),
              Expanded(child: _buildScoreCard('Voice', report.voiceScore ?? 0, Colors.blue)),
              const SizedBox(width: 12),
              Expanded(child: _buildScoreCard('Body', report.bodyScore ?? 0, Colors.green)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildScoreCard(String label, int score, Color color) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Column(
        children: [
          Text(label, style: TextStyle(fontSize: 12, color: color, fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          Text('$score', style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: color)),
          const SizedBox(height: 8),
          SizedBox(
            width: double.infinity,
            height: 6,
            child: ClipRRect(
              borderRadius: BorderRadius.circular(3),
              child: LinearProgressIndicator(
                value: score / 100,
                backgroundColor: color.withOpacity(0.2),
                valueColor: AlwaysStoppedAnimation<Color>(color),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDetailsSection(Report report) {
    final json = report.reportJson;
    if (json == null) return const SizedBox();

    return GlassCard(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Analysis Details', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
          const SizedBox(height: 16),
          if (json['strengths'] != null) _buildListSection('Strengths', json['strengths'], Icons.thumb_up, Colors.green),
          if (json['weaknesses'] != null) _buildListSection('Areas to Improve', json['weaknesses'], Icons.thumb_down, Colors.red),
          if (json['tips'] != null) _buildListSection('Actionable Tips', json['tips'], Icons.lightbulb, Colors.amber),
        ],
      ),
    );
  }

  Widget _buildListSection(String title, dynamic items, IconData icon, Color color) {
    final list = items is List ? items.cast<String>() : <String>[];
    if (list.isEmpty) return const SizedBox();

    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: color, size: 20),
              const SizedBox(width: 8),
              Text(title, style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold, color: color)),
            ],
          ),
          const SizedBox(height: 8),
          ...list.map((item) => Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  margin: const EdgeInsets.only(top: 6),
                  width: 6,
                  height: 6,
                  decoration: BoxDecoration(color: color, shape: BoxShape.circle),
                ),
                const SizedBox(width: 12),
                Expanded(child: Text(item, style: Theme.of(context).textTheme.bodyMedium)),
              ],
            ),
          )),
        ],
      ),
    );
  }

  Widget _buildErrorSection(Report report) {
    return GlassCard(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.error_outline, color: Colors.red, size: 24),
              const SizedBox(width: 12),
              Text('Analysis Failed', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold, color: Colors.red)),
            ],
          ),
          const SizedBox(height: 12),
          Text(report.errorMessage ?? 'An unknown error occurred during analysis.', style: Theme.of(context).textTheme.bodyMedium),
        ],
      ),
    );
  }

  Widget _buildProcessingSection(Report report) {
    return GlassCard(
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          SizedBox(
            width: 80,
            height: 80,
            child: CircularProgressIndicator(
              strokeWidth: 4,
              valueColor: AlwaysStoppedAnimation<Color>(Theme.of(context).colorScheme.primary),
            ),
          ),
          const SizedBox(height: 24),
          Text('Analyzing Your Video', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          Text('This usually takes 1-3 minutes depending on video length.', style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Colors.grey.shade600)),
          const SizedBox(height: 24),
          Text('Report ID: ${report.id.substring(0, 8)}...', style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.grey.shade500)),
        ],
      ),
    );
  }

  Widget _buildActionButtons(Report report) {
    return Row(
      children: [
        Expanded(
          child: OutlinedButton.icon(
            onPressed: () async {
              final confirmed = await showDialog<bool>(
                context: context,
                builder: (context) => AlertDialog(
                  title: const Text('Delete Report'),
                  content: const Text('Are you sure you want to delete this report? This action cannot be undone.'),
                  actions: [
                    TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
                    TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('Delete', style: TextStyle(color: Colors.red))),
                  ],
                ),
              );
              if (confirmed == true && context.mounted) {
                await context.read<ReportService>().deleteReport(report.id);
                if (context.mounted) {
                  Navigator.pop(context);
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Report deleted')));
                }
              }
            },
            icon: const Icon(Icons.delete_outline),
            label: const Text('Delete'),
            style: OutlinedButton.styleFrom(
              foregroundColor: Colors.red,
              side: const BorderSide(color: Colors.red),
              padding: const EdgeInsets.symmetric(vertical: 14),
            ),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: ElevatedButton.icon(
            onPressed: () => Navigator.pushNamed(context, '/upload'),
            icon: const Icon(Icons.upload_file),
            label: const Text('New Analysis'),
            style: ElevatedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 14)),
          ),
        ),
      ],
    );
  }

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final diff = now.difference(date);

    if (diff.inDays == 0) {
      if (diff.inHours == 0) return '${diff.inMinutes}m ago';
      return '${diff.inHours}h ago';
    } else if (diff.inDays == 1) return 'Yesterday';
    else if (diff.inDays < 7) return '${diff.inDays}d ago';
    else return '${date.day}/${date.month}/${date.year}';
  }
}