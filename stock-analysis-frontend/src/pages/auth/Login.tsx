import React, { useState } from 'react';
import { Form, Input, Button, Card, Typography, message, Space } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { LoginRequest } from '@/types';
import './Auth.css';

const { Title, Text } = Typography;

const Login: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login, user } = useAuthStore();

  const onFinish = async (values: LoginRequest) => {
    setLoading(true);
    try {
      // Trim whitespace from username and email
      const trimmedValues = {
        ...values,
        username: values.username.trim(),
      };
      
      await login(trimmedValues);
      message.success('Login successful!');
      
      // Redirect based on user role
      const role = user?.role.toLowerCase();
      navigate(`/${role}`);
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <Card className="auth-card" bordered={false}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div className="auth-header">
            <Title level={2}>Stock Analysis System</Title>
            <Text type="secondary">Sign in to your account</Text>
          </div>

          <Form
            name="login"
            onFinish={onFinish}
            autoComplete="off"
            size="large"
          >
            <Form.Item
              name="username"
              rules={[{ required: true, message: 'Please input your username!' }]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="Username"
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[{ required: true, message: 'Please input your password!' }]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="Password"
              />
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                block
              >
                Sign In
              </Button>
            </Form.Item>
          </Form>

          <div className="auth-footer">
            <Text>Don't have an account? </Text>
            <Link to="/register">Sign up now</Link>
          </div>

          <div className="demo-accounts">
            <Text type="secondary" style={{ fontSize: '12px' }}>
              Demo Accounts:
            </Text>
            <div style={{ marginTop: '8px', fontSize: '12px' }}>
              <div>Investor: investor_test / testpass123</div>
              <div>Advisor: advisor_test / testpass123</div>
              <div>Admin: admin_test / testpass123</div>
            </div>
          </div>
        </Space>
      </Card>
    </div>
  );
};

export default Login;


