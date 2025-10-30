import React, { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Button, Space, message } from 'antd';
import { UserOutlined, TeamOutlined, StockOutlined, AlertOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { advisorService } from '@/services/advisorService';

const AdvisorDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({
    total_clients: 0,
    active_portfolios: 0,
    total_alerts: 0,
    pending_reviews: 0,
  });

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const data = await advisorService.getDashboard();
      setStats(data);
    } catch (error) {
      message.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>Advisor Dashboard</h1>

      {/* Statistics Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Clients"
              value={stats.total_clients}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Active Portfolios"
              value={stats.active_portfolios}
              prefix={<StockOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Alerts"
              value={stats.total_alerts}
              prefix={<AlertOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Pending Reviews"
              value={stats.pending_reviews}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#f5222d' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Quick Actions */}
      <Row gutter={[16, 16]}>
        <Col xs={24} md={8}>
          <Card
            hoverable
            onClick={() => navigate('/advisor/clients')}
            style={{ textAlign: 'center', cursor: 'pointer' }}
          >
            <TeamOutlined style={{ fontSize: 48, color: '#1890ff' }} />
            <h3 style={{ marginTop: 16 }}>Manage Clients</h3>
            <p>View and manage client portfolios</p>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card
            hoverable
            onClick={() => navigate('/advisor/portfolios')}
            style={{ textAlign: 'center', cursor: 'pointer' }}
          >
            <StockOutlined style={{ fontSize: 48, color: '#52c41a' }} />
            <h3 style={{ marginTop: 16 }}>Client Portfolios</h3>
            <p>Monitor and adjust portfolios</p>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card
            hoverable
            onClick={() => navigate('/advisor/reports')}
            style={{ textAlign: 'center', cursor: 'pointer' }}
          >
            <AlertOutlined style={{ fontSize: 48, color: '#faad14' }} />
            <h3 style={{ marginTop: 16 }}>Generate Reports</h3>
            <p>Create client reports</p>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default AdvisorDashboard;








