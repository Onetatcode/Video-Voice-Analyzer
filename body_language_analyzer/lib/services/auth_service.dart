import 'package:supabase_flutter/supabase_flutter.dart';

class AuthException implements Exception {
  final String message;
  AuthException(this.message);
  @override
  String toString() => message;
}

class AuthService {
  final GoTrueClient _auth = Supabase.instance.client.auth;

  User? get currentUser => _auth.currentUser;

  Stream<AuthState> get authStateChanges => _auth.onAuthStateChange;

  Future<void> signUp({required String email, required String password}) async {
    try {
      final response = await _auth.signUp(email: email, password: password);
      if (response.user == null) {
        throw AuthException('Sign up failed: No user returned');
      }
    } on AuthException catch (e) {
      throw AuthException(e.message);
    } catch (e) {
      throw AuthException('Sign up failed: $e');
    }
  }

  Future<void> signIn({required String email, required String password}) async {
    try {
      final response = await _auth.signInWithPassword(email: email, password: password);
      if (response.user == null) {
        throw AuthException('Login failed: No user returned');
      }
    } on AuthException catch (e) {
      throw AuthException(e.message);
    } catch (e) {
      throw AuthException('Login failed: $e');
    }
  }

  Future<void> signOut() async {
    try {
      await _auth.signOut();
    } catch (e) {
      throw AuthException('Sign out failed: $e');
    }
  }
}