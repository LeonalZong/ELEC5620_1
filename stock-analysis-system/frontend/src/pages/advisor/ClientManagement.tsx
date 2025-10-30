import React, { useEffect, useState } from 'react';
import { Card, Table, Button, Space, Tag, message, Input } from 'antd';
import { UserOutlined, EyeOutlined, SearchOutlined, TeamOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import api from '@/services/api';
import type { User } from '@/types';

const { Search } = Input;

const ClientManagement: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [clients, setClients] = useState<User[]>([]);

  useEffect(() => {
    loadClients();
  }, []);

  const loadClients = async () => {
    try {
      setLoading(true);
      const response = await api.get('/advisor/clients');
      setClients(response.data);
    } catch (error) {
      message.error('Failed to load clients');
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    {
      title: 'Username',
      dataIndex: 'username',
      key: 'username',
      render: (username: string) => (
        <Space>
          <UserOutlined />
          {username}
        </Space>
      ),
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'status',
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'green' : 'red'}>
          {isActive ? 'Active' : 'Inactive'}
        </Tag>
      ),
    },
    {
      title: 'Last Login',
      dataIndex: 'last_login',
      key: 'last_login',
      render: (date: string) => date ? new Date(date).toLocaleString() : 'Never',
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: User) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/advisor/clients/${record.id}`)}
          >
            View Portfolio
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>
        <TeamOutlined /> Client Management
      </h1>

      <Card>
        <Search
          placeholder="Search clients by username or email"
          allowClear
          enterButton={<SearchOutlined />}
          size="large"
          style={{ marginBottom: 16 }}
          onSearch={(value) => {
            // Implement search functionality
            message.info('Search functionality coming soon');
          }}
        />

        <Table
          dataSource={clients}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showTotal: (total) => `Total ${total} clients`,
          }}
        />
      </Card>
    </div>
  );
};

export default ClientManagement;

