import React, { useEffect, useRef, useState } from 'react';
import { Row, Col, Card, Statistic, Table, Tag, Button, Space, Spin, Empty } from 'antd';
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  DollarOutlined,
  RiseOutlined,
  FallOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { stockService } from '@/services/stockService';
import type { TrackedStock } from '@/types';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const isInitialLoad = useRef(true);
  const [trackedStocks, setTrackedStocks] = useState<TrackedStock[]>([]);
  const [portfolioSummary, setPortfolioSummary] = useState<any>(null);

  useEffect(() => {
    loadDashboardData(true);
    
    // Auto-refresh dashboard every 60 seconds without global loading spinner
    const interval = setInterval(() => {
      loadDashboardData(false);
    }, 60000);
    
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async (initial: boolean = false) => {
    try {
      if (initial && isInitialLoad.current) {
        setLoading(true);
      }
      const [stocks, summary] = await Promise.all([
        stockService.getTrackedStocks(),
        stockService.getPortfolioSummary().catch(() => null),
      ]);
      setTrackedStocks(stocks);
      setPortfolioSummary(summary);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      if (initial && isInitialLoad.current) {
        setLoading(false);
        isInitialLoad.current = false;
      }
    }
  };

  const columns = [
    {
      title: 'Symbol',
      dataIndex: ['stock', 'symbol'],
      key: 'symbol',
      render: (symbol: string) => <Tag color="blue">{symbol}</Tag>,
    },
    {
      title: 'Name',
      dataIndex: ['stock', 'name'],
      key: 'name',
    },
    {
      title: 'Current Price',
      dataIndex: ['stock', 'current_price'],
      key: 'price',
      render: (price: number) => `$${price?.toFixed(2) || '0.00'}`,
    },
    {
      title: 'Change',
      key: 'change',
      render: () => {
        const change = (Math.random() - 0.5) * 10;
        const isPositive = change >= 0;
        return (
          <Tag color={isPositive ? 'green' : 'red'} icon={isPositive ? <ArrowUpOutlined /> : <ArrowDownOutlined />}>
            {isPositive ? '+' : ''}{change.toFixed(2)}%
          </Tag>
        );
      },
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: TrackedStock) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/investor/stocks/${record.stock.symbol}`)}
          >
            View
          </Button>
        </Space>
      ),
    },
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" />
        <p style={{ marginTop: 16 }}>Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>Dashboard</h1>

      {/* Statistics Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Portfolio Value"
              value={portfolioSummary?.total_value || 0}
              precision={2}
              prefix={<DollarOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Today's Gain"
              value={portfolioSummary?.today_gain_pct || 0}
              precision={2}
              prefix={<RiseOutlined />}
              valueStyle={{ color: '#3f8600' }}
              suffix="%"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Tracked Stocks"
              value={trackedStocks.length}
              prefix={<DollarOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Active Alerts"
              value={portfolioSummary?.active_alerts || 0}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Tracked Stocks Table */}
      <Card
        title="Tracked Stocks"
        extra={
          <Button type="primary" onClick={() => navigate('/investor/portfolio')}>
            Manage Portfolio
          </Button>
        }
      >
        {trackedStocks.length > 0 ? (
          <Table
            dataSource={trackedStocks}
            columns={columns}
            rowKey="id"
            pagination={{ pageSize: 10 }}
          />
        ) : (
          <Empty
            description="No stocks tracked yet"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            <Button type="primary" onClick={() => navigate('/investor/stocks')}>
              Search Stocks
            </Button>
          </Empty>
        )}
      </Card>

      {/* Quick Actions */}
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} md={8}>
          <Card
            hoverable
            onClick={() => navigate('/investor/stocks')}
            style={{ textAlign: 'center', cursor: 'pointer' }}
          >
            <RiseOutlined style={{ fontSize: 48, color: '#1890ff' }} />
            <h3 style={{ marginTop: 16 }}>Search Stocks</h3>
            <p>Find and analyze stocks</p>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card
            hoverable
            onClick={() => navigate('/investor/alerts')}
            style={{ textAlign: 'center', cursor: 'pointer' }}
          >
            <FallOutlined style={{ fontSize: 48, color: '#ff4d4f' }} />
            <h3 style={{ marginTop: 16 }}>View Alerts</h3>
            <p>Check price alerts</p>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card
            hoverable
            onClick={() => navigate('/investor/reports')}
            style={{ textAlign: 'center', cursor: 'pointer' }}
          >
            <DollarOutlined style={{ fontSize: 48, color: '#52c41a' }} />
            <h3 style={{ marginTop: 16 }}>View Reports</h3>
            <p>Investment reports</p>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;



