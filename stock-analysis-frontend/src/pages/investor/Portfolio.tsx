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
  BarChartOutlined,
  EditOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { stockService } from '@/services/stockService';
import { reportService } from '@/services/reportService';
import type { TrackedStock } from '@/types';

const Portfolio: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [trackedStocks, setTrackedStocks] = useState<TrackedStock[]>([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isEditModalVisible, setIsEditModalVisible] = useState(false);
  const [editingStock, setEditingStock] = useState<TrackedStock | null>(null);
  const [form] = Form.useForm();
  const [editForm] = Form.useForm();

  useEffect(() => {
    loadTrackedStocks();
    
    // Auto-refresh portfolio every 60 seconds
    const interval = setInterval(() => {
      loadTrackedStocks();
    }, 60000); // 60 seconds
    
    // Cleanup interval on component unmount
    return () => clearInterval(interval);
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

  const handleTrackStock = async (values: { 
    symbol: string; 
    threshold?: number;
    quantity?: number;
    purchasePrice?: number;
  }) => {
    try {
      await stockService.trackStock(
        values.symbol.toUpperCase(), 
        values.threshold,
        values.quantity,
        values.purchasePrice
      );
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

  const handleGenerateAnalysis = async (stockId: number, symbol: string) => {
    try {
      setLoading(true);
      await reportService.generateReport(stockId, 'COMPREHENSIVE');
      message.success(`Analysis report generated for ${symbol}`);
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Failed to generate analysis');
    } finally {
      setLoading(false);
    }
  };

  const handleEditThreshold = (stock: TrackedStock) => {
    setEditingStock(stock);
    editForm.setFieldsValue({
      threshold: stock.custom_alert_threshold,
    });
    setIsEditModalVisible(true);
  };

  const [isPortfolioModalVisible, setIsPortfolioModalVisible] = useState(false);
  const [portfolioForm] = Form.useForm();

  const handleUpdateThreshold = async (values: { threshold?: number }) => {
    if (!editingStock) return;
    
    try {
      // Directly update the threshold
      await stockService.updateTrackThreshold(editingStock.stock.symbol, values.threshold);
      message.success(`Updated alert threshold for ${editingStock.stock.symbol}`);
      setIsEditModalVisible(false);
      setEditingStock(null);
      editForm.resetFields();
      loadTrackedStocks();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Failed to update threshold');
    }
  };

  const handleEditPortfolio = (stock: TrackedStock) => {
    setEditingStock(stock);
    portfolioForm.setFieldsValue({
      quantity: stock.portfolio?.quantity || 0,
      purchasePrice: stock.portfolio?.purchase_price || stock.stock.current_price,
    });
    setIsPortfolioModalVisible(true);
  };

  const handleUpdatePortfolio = async (values: { quantity: number; purchasePrice: number }) => {
    if (!editingStock) return;
    
    try {
      await stockService.updatePortfolio(
        editingStock.stock.symbol, 
        values.quantity,
        values.purchasePrice
      );
      message.success(`Updated portfolio for ${editingStock.stock.symbol}`);
      setIsPortfolioModalVisible(false);
      setEditingStock(null);
      portfolioForm.resetFields();
      loadTrackedStocks();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Failed to update portfolio');
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
      align: 'right' as const,
      render: (price: number) => (
        <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
          ${price?.toFixed(2) || '0.00'}
        </span>
      ),
    },
    {
      title: 'Quantity',
      key: 'quantity',
      align: 'right' as const,
      render: (_: any, record: TrackedStock) => {
        if (record.portfolio) {
          return <span>{record.portfolio.quantity.toFixed(2)}</span>;
        }
        return <span style={{ color: '#999' }}>-</span>;
      },
    },
    {
      title: 'Avg Cost',
      key: 'avgCost',
      align: 'right' as const,
      render: (_: any, record: TrackedStock) => {
        if (record.portfolio) {
          return <span>${record.portfolio.purchase_price.toFixed(2)}</span>;
        }
        return <span style={{ color: '#999' }}>-</span>;
      },
    },
    {
      title: 'Market Value',
      key: 'marketValue',
      align: 'right' as const,
      render: (_: any, record: TrackedStock) => {
        if (record.portfolio) {
          return <span style={{ fontWeight: 'bold' }}>${record.portfolio.current_value.toFixed(2)}</span>;
        }
        return <span style={{ color: '#999' }}>-</span>;
      },
    },
    {
      title: 'Profit/Loss',
      key: 'profitLoss',
      align: 'right' as const,
      render: (_: any, record: TrackedStock) => {
        if (record.portfolio) {
          const { profit_loss, profit_loss_pct } = record.portfolio;
          const isProfit = profit_loss >= 0;
          return (
            <div>
              <div style={{ 
                color: isProfit ? '#52c41a' : '#ff4d4f',
                fontWeight: 'bold'
              }}>
                {isProfit ? '+' : ''}{profit_loss.toFixed(2)}
              </div>
              <div style={{ 
                color: isProfit ? '#52c41a' : '#ff4d4f',
                fontSize: '12px'
              }}>
                ({isProfit ? '+' : ''}{profit_loss_pct.toFixed(2)}%)
              </div>
            </div>
          );
        }
        return <span style={{ color: '#999' }}>-</span>;
      },
    },
    {
      title: 'Alert Threshold',
      dataIndex: 'custom_alert_threshold',
      key: 'threshold',
      align: 'center' as const,
      render: (threshold: number, record: TrackedStock) => (
        <Space>
          {threshold ? (
            <Tag color="orange">{threshold}%</Tag>
          ) : (
            <Tag color="default">Default</Tag>
          )}
          <Button
            type="text"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEditThreshold(record)}
            title="Edit Threshold"
          />
        </Space>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'status',
      align: 'center' as const,
      render: (isActive: string) => (
        <Tag color={isActive === 'Y' ? 'green' : 'red'}>
          {isActive === 'Y' ? 'Active' : 'Inactive'}
        </Tag>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 160,
      render: (_: any, record: TrackedStock) => (
        <Space>
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEditPortfolio(record)}
            title="Edit Holding"
          />
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/investor/stocks/${record.stock.symbol}`)}
            title="View Details"
          />
          <Button
            type="text"
            icon={<BarChartOutlined />}
            onClick={() => handleGenerateAnalysis(record.stock.id, record.stock.symbol)}
            title="Generate Analysis"
            loading={loading}
          />
          <Popconfirm
            title="Stop tracking this stock?"
            onConfirm={() => handleUntrackStock(record.stock.symbol)}
            okText="Yes"
            cancelText="No"
          >
            <Button 
              type="text" 
              danger 
              icon={<DeleteOutlined />}
              title="Untrack Stock"
            />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h2 style={{ margin: 0 }}>My Portfolio</h2>
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
          </div>
        }
        bordered={false}
        style={{ boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}
      >
        <Table
          dataSource={trackedStocks}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showTotal: (total) => `Total ${total} stocks`,
            showSizeChanger: true,
            showQuickJumper: true,
          }}
          scroll={{ x: 800 }}
          size="middle"
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

          <Form.Item
            name="quantity"
            label="Quantity (Optional)"
            help="Number of shares you own"
          >
            <InputNumber
              style={{ width: '100%' }}
              placeholder="e.g., 100"
              min={0}
              precision={2}
            />
          </Form.Item>

          <Form.Item
            name="purchasePrice"
            label="Purchase Price (Optional)"
            help="Average cost per share"
          >
            <InputNumber
              style={{ width: '100%' }}
              placeholder="e.g., 150.00"
              min={0}
              prefix="$"
              precision={2}
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

      {/* Edit Threshold Modal */}
      <Modal
        title={`Edit Alert Threshold - ${editingStock?.stock.symbol}`}
        open={isEditModalVisible}
        onCancel={() => {
          setIsEditModalVisible(false);
          setEditingStock(null);
          editForm.resetFields();
        }}
        footer={null}
      >
        <Form
          form={editForm}
          layout="vertical"
          onFinish={handleUpdateThreshold}
        >
          <Form.Item
            name="threshold"
            label="Alert Threshold (%)"
            help="Get notified when price drops by this percentage. Leave empty to use default system threshold."
          >
            <InputNumber
              style={{ width: '100%' }}
              placeholder="e.g., -5 (or leave empty for default)"
              min={-100}
              max={0}
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0 }}>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button 
                onClick={() => {
                  setIsEditModalVisible(false);
                  setEditingStock(null);
                  editForm.resetFields();
                }}
              >
                Cancel
              </Button>
              <Button type="primary" htmlType="submit">
                Update
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Edit Portfolio Modal */}
      <Modal
        title={`Edit Portfolio Holding - ${editingStock?.stock.symbol}`}
        open={isPortfolioModalVisible}
        onCancel={() => {
          setIsPortfolioModalVisible(false);
          setEditingStock(null);
          portfolioForm.resetFields();
        }}
        footer={null}
      >
        <Form
          form={portfolioForm}
          layout="vertical"
          onFinish={handleUpdatePortfolio}
        >
          <Form.Item
            name="quantity"
            label="Quantity"
            rules={[
              { required: true, message: 'Please enter quantity' },
              { type: 'number', min: 0, message: 'Quantity must be positive' },
            ]}
            help="Number of shares you own"
          >
            <InputNumber
              style={{ width: '100%' }}
              placeholder="e.g., 100"
              min={0}
              precision={2}
            />
          </Form.Item>

          <Form.Item
            name="purchasePrice"
            label="Purchase Price"
            rules={[
              { required: true, message: 'Please enter purchase price' },
              { type: 'number', min: 0, message: 'Price must be positive' },
            ]}
            help="Average cost per share"
          >
            <InputNumber
              style={{ width: '100%' }}
              placeholder="e.g., 150.00"
              min={0}
              prefix="$"
              precision={2}
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0 }}>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button 
                onClick={() => {
                  setIsPortfolioModalVisible(false);
                  setEditingStock(null);
                  portfolioForm.resetFields();
                }}
              >
                Cancel
              </Button>
              <Button type="primary" htmlType="submit">
                Update
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Portfolio;


