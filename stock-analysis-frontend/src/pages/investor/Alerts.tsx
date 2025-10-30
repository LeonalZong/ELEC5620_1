import React, { useEffect, useState } from 'react';
import { Card, Table, Tag, Button, Space, message, Popconfirm, Empty } from 'antd';
import { BellOutlined, CheckOutlined, DeleteOutlined, EyeOutlined, BarChartOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import api from '@/services/api';
import type { Alert, AlertStatus, AlertType } from '@/types';

const Alerts: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [alerts, setAlerts] = useState<Alert[]>([]);

  useEffect(() => {
    loadAlerts();
    
    // Auto-refresh alerts every 30 seconds
    const interval = setInterval(() => {
      loadAlerts();
    }, 30000); // 30 seconds
    
    // Cleanup interval on component unmount
    return () => clearInterval(interval);
  }, []);

  const loadAlerts = async () => {
    try {
      setLoading(true);
      const response = await api.get('/alerts');
      console.log('Alerts API response:', response.data);
      setAlerts(response.data);
    } catch (error) {
      console.error('Failed to load alerts:', error);
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

  const handleAnalyze = async (alertId: number, stockSymbol: string) => {
    try {
      message.loading('Generating analysis...', 0);
      
      // Call the analysis API
      const response = await api.post(`/alerts/${alertId}/analyze`);
      
      message.destroy();
      message.success('Analysis generated successfully');
      
      // Navigate to analysis page or show modal
      navigate(`/investor/stocks/${stockSymbol}?analysis=true`);
      
    } catch (error) {
      message.destroy();
      message.error('Failed to generate analysis');
    }
  };

  const getAlertTypeColor = (type: AlertType) => {
    switch (type) {
      case 'price_drop':
        return 'red';
      case 'price_rise':
        return 'green';
      case 'volume_spike':
        return 'orange';
      case 'news_alert':
        return 'blue';
      default:
        return 'default';
    }
  };

  const getStatusColor = (status: AlertStatus) => {
    switch (status) {
      case 'pending':
        return 'blue';
      case 'triggered':
        return 'red';
      case 'acknowledged':
        return 'green';
      default:
        return 'default';
    }
  };

  const columns = [
    {
      title: 'Stock',
      dataIndex: 'stock',
      key: 'symbol',
      render: (stock: any, record: Alert) => (
        <Space>
          <Tag color="blue">{stock?.symbol || record.stock?.symbol || 'N/A'}</Tag>
          <span>{stock?.name || record.stock?.name || 'N/A'}</span>
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
      render: (value: number) => value ? `$${value.toFixed(2)}` : '-',
    },
    {
      title: 'Trigger Count',
      key: 'trigger_count',
      render: (_: any, record: Alert) => {
        const count = record.trigger_count || 0;
        const required = record.required_triggers || 5;
        const percentage = (count / required) * 100;
        
        return (
          <Space>
            <Tag color={count >= required ? 'red' : count > 0 ? 'orange' : 'default'}>
              {count}/{required}
            </Tag>
            {count > 0 && (
              <span style={{ 
                fontSize: '12px', 
                color: percentage >= 80 ? '#ff4d4f' : percentage >= 50 ? '#fa8c16' : '#8c8c8c'
              }}>
                ({percentage.toFixed(0)}%)
              </span>
            )}
          </Space>
        );
      },
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
          {record.status === 'triggered' && (
            <>
              <Button
                type="link"
                icon={<CheckOutlined />}
                onClick={() => handleAcknowledge(record.id)}
                title="Acknowledge"
              />
              <Button
                type="link"
                icon={<BarChartOutlined />}
                onClick={() => handleAnalyze(record.id, record.stock?.symbol || '')}
                title="Analyze Drop"
              />
            </>
          )}
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/investor/stocks/${record.stock?.symbol}`)}
            title="View Stock"
          />
          <Popconfirm
            title="Delete this alert?"
            onConfirm={() => handleDelete(record.id)}
            okText="Yes"
            cancelText="No"
          >
            <Button type="link" danger icon={<DeleteOutlined />} title="Delete" />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const triggeredAlerts = alerts.filter(a => a.status === 'triggered');
  const pendingAlerts = alerts.filter(a => a.status === 'pending');
  const acknowledgedAlerts = alerts.filter(a => a.status === 'acknowledged');

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


