import React, { useEffect, useState } from 'react';
import { Card, Table, Tag, Button, Space, message, Popconfirm, Empty } from 'antd';
import { BellOutlined, CheckOutlined, DeleteOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import api from '@/services/api';
import type { Alert, AlertStatus, AlertType } from '@/types';

const Alerts: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [alerts, setAlerts] = useState<Alert[]>([]);

  useEffect(() => {
    loadAlerts();
  }, []);

  const loadAlerts = async () => {
    try {
      setLoading(true);
      const response = await api.get('/alerts');
      setAlerts(response.data);
    } catch (error) {
      message.error('Failed to load alerts');
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledge = async (alertId: number) => {
    try {
      await api.put(`/alerts/${alertId}/acknowledge`);
      message.success('Alert acknowledged');
      loadAlerts();
    } catch (error) {
      message.error('Failed to acknowledge alert');
    }
  };

  const handleDelete = async (alertId: number) => {
    try {
      await api.delete(`/alerts/${alertId}`);
      message.success('Alert deleted');
      loadAlerts();
    } catch (error) {
      message.error('Failed to delete alert');
    }
  };

  const getAlertTypeColor = (type: AlertType) => {
    switch (type) {
      case 'PRICE_DROP':
        return 'red';
      case 'PRICE_RISE':
        return 'green';
      case 'VOLUME_SPIKE':
        return 'orange';
      case 'NEWS_ALERT':
        return 'blue';
      default:
        return 'default';
    }
  };

  const getStatusColor = (status: AlertStatus) => {
    switch (status) {
      case 'PENDING':
        return 'blue';
      case 'TRIGGERED':
        return 'red';
      case 'ACKNOWLEDGED':
        return 'green';
      default:
        return 'default';
    }
  };

  const columns = [
    {
      title: 'Stock',
      dataIndex: ['stock', 'symbol'],
      key: 'symbol',
      render: (symbol: string, record: Alert) => (
        <Space>
          <Tag color="blue">{symbol}</Tag>
          <span>{record.stock?.name}</span>
        </Space>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'alert_type',
      key: 'type',
      render: (type: AlertType) => (
        <Tag color={getAlertTypeColor(type)}>
          {type.replace('_', ' ')}
        </Tag>
      ),
    },
    {
      title: 'Message',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true,
    },
    {
      title: 'Threshold',
      dataIndex: 'threshold_value',
      key: 'threshold',
      render: (value: number) => value ? `${value}%` : '-',
    },
    {
      title: 'Current Value',
      dataIndex: 'current_value',
      key: 'current',
      render: (value: number) => value ? `${value}%` : '-',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: AlertStatus) => (
        <Tag color={getStatusColor(status)}>
          {status}
        </Tag>
      ),
    },
    {
      title: 'Triggered At',
      dataIndex: 'triggered_at',
      key: 'triggered',
      render: (date: string) => date ? new Date(date).toLocaleString() : '-',
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Alert) => (
        <Space>
          {record.status === 'TRIGGERED' && (
            <Button
              type="link"
              icon={<CheckOutlined />}
              onClick={() => handleAcknowledge(record.id)}
            >
              Acknowledge
            </Button>
          )}
          <Button
            type="link"
            onClick={() => navigate(`/investor/stocks/${record.stock?.symbol}`)}
          >
            View Stock
          </Button>
          <Popconfirm
            title="Delete this alert?"
            onConfirm={() => handleDelete(record.id)}
            okText="Yes"
            cancelText="No"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              Delete
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const triggeredAlerts = alerts.filter(a => a.status === 'TRIGGERED');
  const pendingAlerts = alerts.filter(a => a.status === 'PENDING');
  const acknowledgedAlerts = alerts.filter(a => a.status === 'ACKNOWLEDGED');

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>
        <BellOutlined /> Alerts
      </h1>

      {/* Triggered Alerts */}
      {triggeredAlerts.length > 0 && (
        <Card
          title={<span style={{ color: '#cf1322' }}>⚠️ Triggered Alerts ({triggeredAlerts.length})</span>}
          style={{ marginBottom: 16 }}
        >
          <Table
            dataSource={triggeredAlerts}
            columns={columns}
            rowKey="id"
            loading={loading}
            pagination={false}
          />
        </Card>
      )}

      {/* Pending Alerts */}
      <Card
        title={`Pending Alerts (${pendingAlerts.length})`}
        style={{ marginBottom: 16 }}
      >
        {pendingAlerts.length > 0 ? (
          <Table
            dataSource={pendingAlerts}
            columns={columns}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 10 }}
          />
        ) : (
          <Empty description="No pending alerts" />
        )}
      </Card>

      {/* Acknowledged Alerts */}
      <Card title={`Acknowledged Alerts (${acknowledgedAlerts.length})`}>
        {acknowledgedAlerts.length > 0 ? (
          <Table
            dataSource={acknowledgedAlerts}
            columns={columns}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 10 }}
          />
        ) : (
          <Empty description="No acknowledged alerts" />
        )}
      </Card>
    </div>
  );
};

export default Alerts;

