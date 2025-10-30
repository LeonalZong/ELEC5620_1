import React, { useEffect } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import { Layout, Menu, Avatar, Dropdown, Space, Typography } from 'antd';
import {
  DashboardOutlined,
  WalletOutlined,
  SearchOutlined,
  BellOutlined,
  FileTextOutlined,
  LogoutOutlined,
  UserOutlined,
  RobotOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '@/stores/authStore';
import type { MenuProps } from 'antd';

// Import actual components
import Dashboard from './Dashboard';
import Portfolio from './Portfolio';
import StockSearch from './StockSearch';
import StockDetail from './StockDetail';
import Alerts from './Alerts';
import Reports from './Reports';
import AIAssistant from './AIAssistant';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

const InvestorLayout: React.FC = () => {
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
      onClick: () => navigate('/investor'),
    },
    {
      key: 'portfolio',
      icon: <WalletOutlined />,
      label: 'My Portfolio',
      onClick: () => navigate('/investor/portfolio'),
    },
    {
      key: 'stocks',
      icon: <SearchOutlined />,
      label: 'Stock Search',
      onClick: () => navigate('/investor/stocks'),
    },
    {
      key: 'alerts',
      icon: <BellOutlined />,
      label: 'Alerts',
      onClick: () => navigate('/investor/alerts'),
    },
    {
      key: 'ai-assistant',
      icon: <RobotOutlined />,
      label: 'AI Assistant',
      onClick: () => navigate('/investor/ai-assistant'),
    },
    {
      key: 'reports',
      icon: <FileTextOutlined />,
      label: 'Reports',
      onClick: () => navigate('/investor/reports'),
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
            Investor Dashboard
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
              <Route path="/" element={<Dashboard />} />
              <Route path="/portfolio" element={<Portfolio />} />
              <Route path="/stocks" element={<StockSearch />} />
              <Route path="/stocks/:symbol" element={<StockDetail />} />
              <Route path="/alerts" element={<Alerts />} />
              <Route path="/ai-assistant" element={<AIAssistant />} />
              <Route path="/reports" element={<Reports />} />
            </Routes>
          </div>
        </Content>
      </Layout>
    </Layout>
  );
};

export default InvestorLayout;

