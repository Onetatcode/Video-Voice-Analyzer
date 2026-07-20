enum ReportStatus {
  pending,
  processing,
  complete,
  failed;

  static ReportStatus fromString(String value) {
    return ReportStatus.values.firstWhere(
      (e) => e.name == value,
      orElse: () => ReportStatus.pending,
    );
  }
}

class Report {
  final String id;
  final String userId;
  final String videoUrl;
  final int? voiceScore;
  final int? bodyScore;
  final int? confidenceScore;
  final Map<String, dynamic>? reportJson;
  final DateTime createdAt;
  final ReportStatus status;
  final String? errorMessage;

  Report({
    required this.id,
    required this.userId,
    required this.videoUrl,
    this.voiceScore,
    this.bodyScore,
    this.confidenceScore,
    this.reportJson,
    required this.createdAt,
    required this.status,
    this.errorMessage,
  });

  factory Report.fromJson(Map<String, dynamic> json) {
    return Report(
      id: json['id'] as String,
      userId: json['user_id'] as String,
      videoUrl: json['video_url'] as String,
      voiceScore: json['voice_score'] as int?,
      bodyScore: json['body_score'] as int?,
      confidenceScore: json['confidence_score'] as int?,
      reportJson: json['report_json'] as Map<String, dynamic>?,
      createdAt: DateTime.parse(json['created_at'] as String),
      status: ReportStatus.fromString(json['status'] as String),
      errorMessage: json['error_message'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user_id': userId,
      'video_url': videoUrl,
      'voice_score': voiceScore,
      'body_score': bodyScore,
      'confidence_score': confidenceScore,
      'report_json': reportJson,
      'created_at': createdAt.toIso8601String(),
      'status': status.name,
      'error_message': errorMessage,
    };
  }

  Map<String, dynamic> toInsertJson() {
    return {
      'user_id': userId,
      'video_url': videoUrl,
      'status': ReportStatus.pending.name,
    };
  }

  Report copyWith({
    String? id,
    String? userId,
    String? videoUrl,
    int? voiceScore,
    int? bodyScore,
    int? confidenceScore,
    Map<String, dynamic>? reportJson,
    DateTime? createdAt,
    ReportStatus? status,
    String? errorMessage,
  }) {
    return Report(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      videoUrl: videoUrl ?? this.videoUrl,
      voiceScore: voiceScore ?? this.voiceScore,
      bodyScore: bodyScore ?? this.bodyScore,
      confidenceScore: confidenceScore ?? this.confidenceScore,
      reportJson: reportJson ?? this.reportJson,
      createdAt: createdAt ?? this.createdAt,
      status: status ?? this.status,
      errorMessage: errorMessage ?? this.errorMessage,
    );
  }

  String get statusDisplay {
    switch (status) {
      case ReportStatus.pending:
        return 'Pending';
      case ReportStatus.processing:
        return 'Processing...';
      case ReportStatus.complete:
        return 'Complete';
      case ReportStatus.failed:
        return 'Failed';
    }
  }

  bool get isComplete => status == ReportStatus.complete;
  bool get isProcessing => status == ReportStatus.processing;
  bool get isFailed => status == ReportStatus.failed;
  bool get isPending => status == ReportStatus.pending;
}