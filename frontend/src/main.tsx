/**
 * main.tsx - Entry point de la aplicación
 * Tema: Negro con Rojo (TIVIT Dark Theme)
 */
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider, App as AntdApp, theme } from 'antd';
import esES from 'antd/locale/es_ES';

import { AuthProvider } from './context/AuthContext';
import App from './App';
import './index.css';

// Crear QueryClient con configuración
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutos
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// Tema personalizado TIVIT - Negro con Rojo
const tivitDarkTheme = {
  token: {
    // Colores principales
    colorPrimary: '#E31837',
    colorPrimaryHover: '#FF2D4D',
    colorPrimaryActive: '#C41230',
    colorPrimaryBg: 'rgba(227, 24, 55, 0.1)',
    colorPrimaryBgHover: 'rgba(227, 24, 55, 0.15)',
    
    // Colores de estado
    colorSuccess: '#52c41a',
    colorWarning: '#faad14',
    colorError: '#ff4d4f',
    colorInfo: '#1890ff',
    
    // Fondos oscuros
    colorBgContainer: '#141416',
    colorBgElevated: '#1E1E21',
    colorBgLayout: '#0A0A0B',
    colorBgSpotlight: '#1A1A1D',
    colorBgMask: 'rgba(0, 0, 0, 0.75)',
    
    // Bordes
    colorBorder: '#2A2A2E',
    colorBorderSecondary: '#3A3A3E',
    
    // Texto
    colorText: 'rgba(255, 255, 255, 0.95)',
    colorTextSecondary: 'rgba(255, 255, 255, 0.65)',
    colorTextTertiary: 'rgba(255, 255, 255, 0.45)',
    colorTextQuaternary: 'rgba(255, 255, 255, 0.25)',
    
    // Links
    colorLink: '#E31837',
    colorLinkHover: '#FF2D4D',
    colorLinkActive: '#C41230',
    
    // Otros
    borderRadius: 8,
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    fontSize: 14,
    
    // Sombras
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.4)',
    boxShadowSecondary: '0 8px 24px rgba(0, 0, 0, 0.5)',
  },
  algorithm: theme.darkAlgorithm,
  components: {
    Button: {
      primaryShadow: '0 0 0 rgba(227, 24, 55, 0)',
      defaultBg: '#1A1A1D',
      defaultBorderColor: '#2A2A2E',
    },
    Card: {
      colorBgContainer: '#141416',
    },
    Table: {
      headerBg: '#1A1A1D',
      rowHoverBg: '#1E1E21',
    },
    Menu: {
      darkItemBg: 'transparent',
      darkSubMenuItemBg: 'transparent',
      darkItemSelectedBg: '#E31837',
    },
    Input: {
      colorBgContainer: '#1A1A1D',
    },
    Select: {
      colorBgContainer: '#1A1A1D',
      optionSelectedBg: 'rgba(227, 24, 55, 0.2)',
    },
    Modal: {
      contentBg: '#141416',
      headerBg: '#141416',
    },
    Dropdown: {
      colorBgElevated: '#1E1E21',
    },
    Layout: {
      siderBg: '#0D0D0F',
      headerBg: '#111113',
      bodyBg: '#0A0A0B',
    },
  },
};

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <ConfigProvider theme={tivitDarkTheme} locale={esES}>
        <AntdApp>
          <AuthProvider>
            <App />
          </AuthProvider>
        </AntdApp>
      </ConfigProvider>
    </QueryClientProvider>
  </StrictMode>,
);
