# smart_vehicle_app

An app for smart vehicle control, live monitoring, fall event management, medication reminder, and vital signal monitoring.

## Getting Started

This project is a starting point for a Flutter application.

A few resources to get you started if this is your first Flutter project:

- [Learn Flutter](https://docs.flutter.dev/get-started/learn-flutter)
- [Write your first Flutter app](https://docs.flutter.dev/get-started/codelab)
- [Flutter learning resources](https://docs.flutter.dev/reference/learning-resources)

For help getting started with Flutter development, view the
[online documentation](https://docs.flutter.dev/), which offers tutorials,
samples, guidance on mobile development, and a full API reference.

# To change between Direct Connection mode and LAN mode

Files containing required links:
smart_vehicle_backend/app_runtime.py
smart_vehicle_backend/blueprints/live.py
smart_vehicle_backend/services/robot_controller.py

Links:
PI_BASE_URL = "http://192.168.2.80:8000" # LAN
PI_BASE_URL = "http://192.168.149.1:8000" # Direct Connection

# Patient Example Account

Email: patient1@try.com
Password: password1