import React, { useEffect } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import { Layout, Menu, Avatar, Dropdown, Space, Typography } from 'antd';
import {
  DashboardOutlined,
  TeamOutlined,
  WalletOutlined,
  FileTextOutlined,
  BarChartOutlined,
  LogoutOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '@/stores/authStore';
import type { MenuProps } from 'antd';

// Import actual components
import AdvisorDashboard from './AdvisorDashboard';
import ClientManagement from './ClientManagement';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

const AdvisorLayout: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  useEffect(() => {
    if (!user) {
      navigate('/login');
    }
  }, [user, navigate]);

  const menuItems: MenuProps['items'] = [
    {
      key: 'dashboard',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
      onClick: () => navigate('/advisor'),
    },
    {
      key: 'clients',
      icon: <TeamOutlined />,
      label: 'Clients',
      onClick: () => navigate('/advisor/clients'),
    },
    {
      key: 'portfolios',
      icon: <WalletOutlined />,
      label: 'Portfolios',
      onClick: () => navigate('/advisor/portfolios'),
    },
    {
      key: 'reports',
      icon: <FileTextOutlined />,
      label: 'Reports',
      onClick: () => navigate('/advisor/reports'),
    },
    {
      key: 'analytics',
      icon: <BarChartOutlined />,
      label: 'Analytics',
      onClick: () => navigate('/advisor/analytics'),
    },
  ];

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: 'Profile',
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Logout',
      onClick: logout,
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        breakpoint="lg"
        collapsedWidth="0"
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontSize: 18,
            fontWeight: 'bold',
          }}
        >
          Stock Analysis
        </div>
        <Menu
          theme="dark"
          mode="inline"
          defaultSelectedKeys={['dashboard']}
          items={menuItems}
        />
      </Sider>
      <Layout style={{ marginLeft: 200 }}>
        <Header
          style={{
            padding: '0 24px',
            background: '#fff',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            boxShadow: '0 1px 4px rgba(0,21,41,.08)',
          }}
        >
          <Text strong style={{ fontSize: 16 }}>
            Advisor Dashboard
          </Text>
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <Space style={{ cursor: 'pointer' }}>
              <Avatar icon={<UserOutlined />} />
              <Text>{user?.username}</Text>
            </Space>
          </Dropdown>
        </Header>
        <Content style={{ margin: '24px 16px 0', overflow: 'initial' }}>
          <div style={{ padding: 24, background: '#fff', minHeight: 360 }}>
            <Routes>
              <Route path="/" element={<AdvisorDashboard />} />
              <Route path="/clients" element={<ClientManagement />} />
              <Route path="/portfolios" element={<PortfoliosPlaceholder />} />
              <Route path="/reports" element={<ReportsPlaceholder />} />
              <Route path="/analytics" element={<AnalyticsPlaceholder />} />
            </Routes>
          </div>
        </Content>
      </Layout>
    </Layout>
  );
};

// Placeholder components

const PortfoliosPlaceholder: React.FC = () => (
  <div>
    <h1>Client Portfolios</h1>
    <p>View and edit client portfolios.</p>
  </div>
);

const ReportsPlaceholder: React.FC = () => (
  <div>
    <h1>Reports</h1>
    <p>Generate and manage client reports.</p>
  </div>
);

const AnalyticsPlaceholder: React.FC = () => (
  <div>
    <h1>Analytics</h1>
    <p>View analytics and insights for your clients.</p>
  </div>
);

export default AdvisorLayout;

