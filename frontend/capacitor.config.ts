import type { CapacitorConfig } from '@capacitor/cli';

/**
 * PlantMind Android/iOS native shell configuration.
 *
 * The native app bundles the compiled web assets (frontend/dist) and talks to
 * the PlantMind backend over HTTP. The backend address is configured at
 * runtime in the app ("Connect to server" screen / Settings), because the
 * APK ships without a bundled Python backend.
 */
const config: CapacitorConfig = {
  appId: 'com.plantmind.app',
  appName: 'PlantMind',
  webDir: 'dist',
  android: {
    // The PlantMind backend runs on plain http://<PC-IP>:8000 on the LAN.
    allowMixedContent: true,
  },
  server: {
    androidScheme: 'https',
    cleartext: true,
  },
};

export default config;
