import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'org.healthaware.app',
  appName: 'HealthAware',
  webDir: 'dist/health-awareness-frontend',
  server: {
    androidScheme: 'https',
    cleartext: false,
  },
  plugins: {
    StatusBar: {
      style: 'DARK',
      backgroundColor: '#00645c',
    },
  },
};

export default config;
