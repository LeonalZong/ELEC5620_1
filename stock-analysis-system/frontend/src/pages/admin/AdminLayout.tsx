import React, { useEffect } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import { Layout, Menu, Avatar, Dropdown, Space, Typography, Badge } from 'antd';
import {
  DashboardOutlined,
  UserOutlined,
  SettingOutlined,
  MonitorOutlined,
  FileTextOutlined,
  ToolOutlined,
  LogoutOutlined,
  TeamOutlined,
  SafetyOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '@/stores/authStore';
import type { MenuProps } from 'antd';

// Import actual components
import AdminDashboard from './AdminDashboard';
import UserManagement from './UserManagement';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

const AdminLayout: React.FC = () => {
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
      onClick: () => navigate('/admin'),
    },
    {
      key: 'system',
      icon: <SettingOutlined />,
      label: 'System Management',
      children: [
        {
          key: 'users',
          icon: <TeamOutlined />,
          label: 'User Management',
          onClick: () => navigate('/admin/users'),
        },
        {
          key: 'roles',
          icon: <SafetyOutlined />,
          label: 'Role Management',
          onClick: () => navigate('/admin/roles'),
        },
      ],
    },
    {
      key: 'monitoring',
      icon: <MonitorOutlined />,
      label: 'System Monitoring',
      children: [
        {
          key: 'performance',
          label: 'Performance',
          onClick: () => navigate('/admin/performance'),
        },
        {
          key: 'tasks',
          label: 'Background Tasks',
          onClick: () => navigate('/admin/tasks'),
        },
        {
          key: 'logs',
          label: 'System Logs',
          onClick: () => navigate('/admin/logs'),
        },
      ],
    },
    {
      key: 'settings',
      icon: <ToolOutlined />,
      label: 'Settings',
      onClick: () => navigate('/admin/settings'),
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
          Admin Panel
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
          <Space>
            <Text strong style={{ fontSize: 16 }}>
              System Administration
            </Text>
            <Badge count={5} style={{ marginLeft: 16 }}>
              <FileTextOutlined style={{ fontSize: 20 }} />
            </Badge>
          </Space>
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <Space style={{ cursor: 'pointer' }}>
              <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#f56a00' }} />
              <Text>{user?.username}</Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                (Admin)
              </Text>
            </Space>
          </Dropdown>
        </Header>
        <Content style={{ margin: '24px 16px 0', overflow: 'initial' }}>
          <div style={{ padding: 24, background: '#fff', minHeight: 360 }}>
            <Routes>
              <Route path="/" element={<AdminDashboard />} />
              <Route path="/users" element={<UserManagement />} />
              <Route path="/roles" element={<RoleManagementPlaceholder />} />
              <Route path="/performance" element={<PerformancePlaceholder />} />
              <Route path="/tasks" element={<TasksPlaceholder />} />
              <Route path="/logs" element={<LogsPlaceholder />} />
              <Route path="/settings" element={<SettingsPlaceholder />} />
            </Routes>
          </div>
        </Content>
      </Layout>
    </Layout>
  );
};

// Placeholder components (Admin panel style)

const RoleManagementPlaceholder: React.FC = () => (
  <div>
    <h1>Role Management</h1>
    <p>Manage user roles and permissions.</p>
  </div>
);

const PerformancePlaceholder: React.FC = () => (
  <div>
    <h1>System Performance</h1>
    <p>Monitor system performance metrics.</p>
    <ul>
      <li>CPU Usage</li>
      <li>Memory Usage</li>
      <li>Disk Usage</li>
      <li>Network Traffic</li>
      <li>Database Connections</li>
    </ul>
  </div>
);

const TasksPlaceholder: React.FC = () => (
  <div>
    <h1>Background Tasks</h1>
    <p>Monitor and manage Celery background tasks.</p>
    <ul>
      <li>Stock Price Monitoring</li>
      <li>News Data Collection</li>
      <li>Report Generation</li>
      <li>Alert Checking</li>
    </ul>
  </div>
);

const LogsPlaceholder: React.FC = () => (
  <div>
    <h1>System Logs</h1>
    <p>View system logs and activities.</p>
  </div>
);

const SettingsPlaceholder: React.FC = () => (
  <div>
    <h1>System Settings</h1>
    <p>Configure system settings.</p>
  </div>
);

export default AdminLayout;

