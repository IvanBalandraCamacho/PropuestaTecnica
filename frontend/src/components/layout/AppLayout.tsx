/**
 * Layout principal de la aplicación
 */
import React from 'react';
import { Layout, Menu, Avatar, Dropdown, Typography, Space } from 'antd';
import { 
  DashboardOutlined, LogoutOutlined, UserOutlined 
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

interface AppLayoutProps {
  children: React.ReactNode;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: user?.full_name || user?.email,
      disabled: true,
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Cerrar Sesión',
      onClick: handleLogout,
    },
  ];

  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
      onClick: () => navigate('/'),
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        theme="dark"
        width={220}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <div style={{ 
          height: 64, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          borderBottom: '1px solid rgba(255,255,255,0.1)',
        }}>
          <Text strong style={{ color: '#fff', fontSize: 18 }}>
            RFP Analyzer
          </Text>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          style={{ marginTop: 16 }}
        />
      </Sider>
      
      <Layout style={{ marginLeft: 220 }}>
        <Header style={{ 
          background: '#fff', 
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'flex-end',
          boxShadow: '0 1px 4px rgba(0,0,0,0.1)',
        }}>
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <Space style={{ cursor: 'pointer' }}>
              <Avatar icon={<UserOutlined />} />
              <Text>{user?.full_name}</Text>
            </Space>
          </Dropdown>
        </Header>
        
        <Content style={{ background: '#f5f5f5' }}>
          {children}
        </Content>
      </Layout>
    </Layout>
  );
};

export default AppLayout;
