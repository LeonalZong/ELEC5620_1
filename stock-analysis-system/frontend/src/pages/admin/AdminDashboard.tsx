import React, { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, message } from 'antd';
import {
  UserOutlined,
  TeamOutlined,
  StockOutlined,
  AlertOutlined,
  LineChartOutlined,
  DatabaseOutlined,
} from '@ant-design/icons';
import api from '@/services/api';

const AdminDashboard: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({
    total_users: 0,
    total_investors: 0,
    total_advisors: 0,
    total_stocks: 0,
    total_alerts: 0,
    system_health: 'healthy',
  });

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const response = await api.get('/admin/dashboard');
      setStats(response.data);
    } catch (error) {
      message.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>System Dashboard</h1>

      {/* Statistics Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Users"
              value={stats.total_users}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Investors"
              value={stats.total_investors}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Advisors"
              value={stats.total_advisors}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Stocks"
              value={stats.total_stocks}
              prefix={<StockOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* System Status */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="System Health" extra={<Tag color="green">Healthy</Tag>}>
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Statistic
                  title="Database"
                  value="Online"
                  prefix={<DatabaseOutlined />}
                  valueStyle={{ color: '#52c41a', fontSize: 16 }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="API Status"
                  value="Running"
                  prefix={<LineChartOutlined />}
                  valueStyle={{ color: '#52c41a', fontSize: 16 }}
                />
              </Col>
            </Row>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Recent Activity">
            <Statistic
              title="Total Alerts Today"
              value={stats.total_alerts}
              prefix={<AlertOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default AdminDashboard;

