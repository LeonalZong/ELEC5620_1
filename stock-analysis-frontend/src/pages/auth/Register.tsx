import React, { useState } from 'react';
import { Form, Input, Button, Card, Typography, message, Space, Select } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { RegisterRequest, UserRole } from '@/types';
import './Auth.css';

const { Title, Text } = Typography;
const { Option } = Select;

const Register: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { register } = useAuthStore();

  const onFinish = async (values: RegisterRequest) => {
    setLoading(true);
    try {
      // Trim whitespace from all fields
      const trimmedValues = {
        ...values,
        username: values.username.trim(),
        email: values.email.trim(),
      };
      
      await register(trimmedValues);
      message.success('Registration successful! Please login.');
      navigate('/login');
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <Card className="auth-card" bordered={false}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div className="auth-header">
            <Title level={2}>Create Account</Title>
            <Text type="secondary">Sign up for Stock Analysis System</Text>
          </div>

          <Form
            name="register"
            onFinish={onFinish}
            autoComplete="off"
            size="large"
            initialValues={{ role: UserRole.INVESTOR }}
          >
            <Form.Item
              name="username"
              rules={[
                { required: true, message: 'Please input your username!' },
                { min: 3, message: 'Username must be at least 3 characters!' },
              ]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="Username"
              />
            </Form.Item>

            <Form.Item
              name="email"
              rules={[
                { required: true, message: 'Please input your email!' },
                { type: 'email', message: 'Please enter a valid email!' },
              ]}
            >
              <Input
                prefix={<MailOutlined />}
                placeholder="Email"
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[
                { required: true, message: 'Please input your password!' },
                { min: 6, message: 'Password must be at least 6 characters!' },
              ]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="Password"
              />
            </Form.Item>

            <Form.Item
              name="confirmPassword"
              dependencies={['password']}
              rules={[
                { required: true, message: 'Please confirm your password!' },
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    if (!value || getFieldValue('password') === value) {
                      return Promise.resolve();
                    }
                    return Promise.reject(new Error('Passwords do not match!'));
                  },
                }),
              ]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="Confirm Password"
              />
            </Form.Item>

            <Form.Item
              name="role"
              rules={[{ required: true, message: 'Please select your role!' }]}
            >
              <Select placeholder="Select Role">
                <Option value={UserRole.INVESTOR}>Investor</Option>
                <Option value={UserRole.ADVISOR}>Advisor</Option>
              </Select>
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                block
              >
                Sign Up
              </Button>
            </Form.Item>
          </Form>

          <div className="auth-footer">
            <Text>Already have an account? </Text>
            <Link to="/login">Sign in</Link>
          </div>
        </Space>
      </Card>
    </div>
  );
};

export default Register;


