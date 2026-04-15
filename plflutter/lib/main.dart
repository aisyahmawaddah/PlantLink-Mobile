import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:plflutter/home_page.dart';
import 'package:plflutter/viewchannel_page.dart';
import 'package:plflutter/createchannel_page.dart';
import 'package:plflutter/login_page.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'PlantLink',
      theme: ThemeData(primarySwatch: Colors.blue),
      debugShowCheckedModeBanner: false,
      home: const AuthCheck(),
      routes: {
        '/login': (context) => const LoginPage(),
        '/home': (context) => const Home(),
        '/channels': (context) => const ViewChannel(),
        '/channels/create': (context) => const CreateChannel(),
      },
    );
  }
}

class AuthCheck extends StatefulWidget {
  const AuthCheck({super.key});

  @override
  State<AuthCheck> createState() => _AuthCheckState();
}

class _AuthCheckState extends State<AuthCheck> {
  @override
  void initState() {
    super.initState();
    _checkLogin();
  }

  Future<void> _checkLogin() async {
    final prefs = await SharedPreferences.getInstance();
    final username = prefs.getString('username') ?? '';
    if (mounted) {
      Navigator.pushReplacementNamed(
        context,
        username.isNotEmpty ? '/home' : '/login',
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(child: CircularProgressIndicator()),
    );
  }
}
