import React, { useEffect, useState } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  message,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  Popconfirm,
} from 'antd';
import {
  UserOutlined,
  EditOutlined,
  DeleteOutlined,
  PlusOutlined,
  LockOutlined,
} from '@ant-design/icons';
import api from '@/services/api';
import type { User, UserRole } from '@/types';

const { Option } = Select;

const UserManagement: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [users, setUsers] = useState<User[]>([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [form] = Form.useForm();

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const response = await api.get('/admin/users');
      setUsers(response.data);
    } catch (error) {
      message.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (user: User) => {
    setEditingUser(user);
    form.setFieldsValue(user);
    setIsModalVisible(true);
  };

  const handleDelete = async (userId: number) => {
    try {
      await api.delete(`/admin/users/${userId}`);
      message.success('User deleted successfully');
      loadUsers();
    } catch (error) {
      message.error('Failed to delete user');
    }
  };

  const handleSubmit = async (values: any) => {
    try {
      if (editingUser) {
        await api.put(`/admin/users/${editingUser.id}`, values);
        message.success('User updated successfully');
      } else {
        await api.post('/admin/users', values);
        message.success('User created successfully');
      }
      setIsModalVisible(false);
      form.resetFields();
      setEditingUser(null);
      loadUsers();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Operation failed');
    }
  };

  const handleToggleStatus = async (userId: number, isActive: boolean) => {
    try {
      await api.put(`/admin/users/${userId}/status`, { is_active: isActive });
      message.success(`User ${isActive ? 'activated' : 'deactivated'} successfully`);
      loadUsers();
    } catch (error) {
      message.error('Failed to update user status');
    }
  };

  const getRoleColor = (role: UserRole) => {
    switch (role) {
      case 'ADMIN':
        return 'red';
      case 'ADVISOR':
        return 'blue';
      case 'INVESTOR':
        return 'green';
      default:
        return 'default';
    }
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
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
      title: 'Role',
      dataIndex: 'role',
      key: 'role',
      render: (role: UserRole) => (
        <Tag color={getRoleColor(role)}>{role}</Tag>
      ),
      filters: [
        { text: 'ADMIN', value: 'ADMIN' },
        { text: 'ADVISOR', value: 'ADVISOR' },
        { text: 'INVESTOR', value: 'INVESTOR' },
      ],
      onFilter: (value: any, record: User) => record.role === value,
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'status',
      render: (isActive: boolean, record: User) => (
        <Switch
          checked={isActive}
          onChange={(checked) => handleToggleStatus(record.id, checked)}
          checkedChildren="Active"
          unCheckedChildren="Inactive"
        />
      ),
    },
    {
      title: 'Created At',
      dataIndex: 'created_at',
      key: 'created',
      render: (date: string) => new Date(date).toLocaleString(),
      sorter: (a: User, b: User) =>
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: User) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            Edit
          </Button>
          <Popconfirm
            title="Are you sure to delete this user?"
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

  return (
    <div>
      <Card
        title={<h2 style={{ margin: 0 }}>User Management</h2>}
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setEditingUser(null);
              form.resetFields();
              setIsModalVisible(true);
            }}
          >
            Add User
          </Button>
        }
      >
        <Table
          dataSource={users}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showTotal: (total) => `Total ${total} users`,
          }}
        />
      </Card>

      {/* Add/Edit User Modal */}
      <Modal
        title={editingUser ? 'Edit User' : 'Add New User'}
        open={isModalVisible}
        onCancel={() => {
          setIsModalVisible(false);
          form.resetFields();
          setEditingUser(null);
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="username"
            label="Username"
            rules={[{ required: true, message: 'Please enter username' }]}
          >
            <Input prefix={<UserOutlined />} placeholder="Username" />
          </Form.Item>

          <Form.Item
            name="email"
            label="Email"
            rules={[
              { required: true, message: 'Please enter email' },
              { type: 'email', message: 'Invalid email format' },
            ]}
          >
            <Input type="email" placeholder="Email" />
          </Form.Item>

          {!editingUser && (
            <Form.Item
              name="password"
              label="Password"
              rules={[{ required: true, message: 'Please enter password' }]}
            >
              <Input.Password prefix={<LockOutlined />} placeholder="Password" />
            </Form.Item>
          )}

          <Form.Item
            name="role"
            label="Role"
            rules={[{ required: true, message: 'Please select role' }]}
          >
            <Select placeholder="Select role">
              <Option value="INVESTOR">INVESTOR</Option>
              <Option value="ADVISOR">ADVISOR</Option>
              <Option value="ADMIN">ADMIN</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="is_active"
            label="Status"
            valuePropName="checked"
            initialValue={true}
          >
            <Switch checkedChildren="Active" unCheckedChildren="Inactive" />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0 }}>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => setIsModalVisible(false)}>
                Cancel
              </Button>
              <Button type="primary" htmlType="submit">
                {editingUser ? 'Update' : 'Create'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default UserManagement;








