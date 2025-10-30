import React, { useEffect, useState } from 'react';
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  message,
  Space,
  Tag,
  Popconfirm,
  InputNumber,
} from 'antd';
import {
  PlusOutlined,
  DeleteOutlined,
  EyeOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { stockService } from '@/services/stockService';
import type { TrackedStock } from '@/types';

const Portfolio: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [trackedStocks, setTrackedStocks] = useState<TrackedStock[]>([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    loadTrackedStocks();
  }, []);

  const loadTrackedStocks = async () => {
    try {
      setLoading(true);
      const stocks = await stockService.getTrackedStocks();
      setTrackedStocks(stocks);
    } catch (error) {
      message.error('Failed to load tracked stocks');
    } finally {
      setLoading(false);
    }
  };

  const handleTrackStock = async (values: { symbol: string; threshold?: number }) => {
    try {
      await stockService.trackStock(values.symbol.toUpperCase(), values.threshold);
      message.success(`Successfully tracked ${values.symbol.toUpperCase()}`);
      setIsModalVisible(false);
      form.resetFields();
      loadTrackedStocks();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Failed to track stock');
    }
  };

  const handleUntrackStock = async (symbol: string) => {
    try {
      await stockService.untrackStock(symbol);
      message.success(`Stopped tracking ${symbol}`);
      loadTrackedStocks();
    } catch (error) {
      message.error('Failed to untrack stock');
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
      ellipsis: true,
    },
    {
      title: 'Sector',
      dataIndex: ['stock', 'sector'],
      key: 'sector',
      render: (sector: string) => sector || '-',
    },
    {
      title: 'Current Price',
      dataIndex: ['stock', 'current_price'],
      key: 'price',
      render: (price: number) => (
        <span style={{ fontWeight: 'bold' }}>
          ${price?.toFixed(2) || '0.00'}
        </span>
      ),
    },
    {
      title: 'Alert Threshold',
      dataIndex: 'custom_alert_threshold',
      key: 'threshold',
      render: (threshold: number) => (
        threshold ? `${threshold}%` : 'Default'
      ),
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
          <Popconfirm
            title="Stop tracking this stock?"
            onConfirm={() => handleUntrackStock(record.stock.symbol)}
            okText="Yes"
            cancelText="No"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              Untrack
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card
        title={<h2 style={{ margin: 0 }}>My Portfolio</h2>}
        extra={
          <Space>
            <Button
              type="default"
              icon={<SearchOutlined />}
              onClick={() => navigate('/investor/stocks')}
            >
              Search Stocks
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setIsModalVisible(true)}
            >
              Track Stock
            </Button>
          </Space>
        }
      >
        <Table
          dataSource={trackedStocks}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showTotal: (total) => `Total ${total} stocks`,
          }}
        />
      </Card>

      {/* Add Stock Modal */}
      <Modal
        title="Track New Stock"
        open={isModalVisible}
        onCancel={() => {
          setIsModalVisible(false);
          form.resetFields();
        }}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleTrackStock}
        >
          <Form.Item
            name="symbol"
            label="Stock Symbol"
            rules={[
              { required: true, message: 'Please enter stock symbol' },
              { pattern: /^[A-Z]{1,5}$/, message: 'Invalid symbol format' },
            ]}
          >
            <Input
              placeholder="e.g., AAPL, MSFT, TSLA"
              style={{ textTransform: 'uppercase' }}
            />
          </Form.Item>

          <Form.Item
            name="threshold"
            label="Alert Threshold (%)"
            help="Get notified when price drops by this percentage"
          >
            <InputNumber
              style={{ width: '100%' }}
              placeholder="e.g., -5"
              min={-100}
              max={0}
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0 }}>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => setIsModalVisible(false)}>
                Cancel
              </Button>
              <Button type="primary" htmlType="submit">
                Track Stock
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Portfolio;

