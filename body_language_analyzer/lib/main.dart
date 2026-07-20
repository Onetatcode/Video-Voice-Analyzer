import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:provider/provider.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import 'services/api_service.dart';
import 'services/auth_service.dart';
import 'services/report_service.dart';
import 'services/storage_service.dart';
import 'services/supabase_service.dart';
import 'screens/auth_gate.dart';
import 'screens/auth/login_screen.dart';
import 'screens/auth/sign_up_screen.dart';
import 'screens/home_screen.dart';
import 'screens/history_screen.dart';
import 'screens/report_detail_screen.dart';
import 'screens/upload_screen.dart';
import 'theme/app_theme.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  await dotenv.load(fileName: '.env');

  final supabaseService = SupabaseService();
  await supabaseService.init();
  ApiService().init();

  runApp(
    MultiProvider(
      providers: [
        Provider<SupabaseService>.value(value: supabaseService),
        Provider<ApiService>.value(value: ApiService()),
        Provider<AuthService>.value(value: AuthService()),
        Provider<StorageService>.value(value: StorageService()),
        Provider<ReportService>.value(value: ReportService()),
      ],
      child: const MyApp(),
    ),
  );
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Body Language & Voice Analyzer',
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.system,
      home: const AuthGate(),
      routes: {
        '/login': (_) => const LoginScreen(),
        '/signup': (_) => const SignUpScreen(),
        '/upload': (_) => const UploadScreen(),
      },
      onGenerateRoute: (settings) {
        if (settings.name == '/report' && settings.arguments is String) {
          return MaterialPageRoute(
            builder: (_) => ReportDetailScreen(reportId: settings.arguments as String),
          );
        }
        return null;
      },
    );
  }
}
