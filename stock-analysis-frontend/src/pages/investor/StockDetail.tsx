import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Row,
  Col,
  Statistic,
  Button,
  Tabs,
  Table,
  Tag,
  List,
  Space,
  Spin,
  message,
  Descriptions,
} from 'antd';
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  StarOutlined,
  StarFilled,
  LeftOutlined,
} from '@ant-design/icons';
import { stockService } from '@/services/stockService';
import type { Stock, StockAnalysis } from '@/types';

const { TabPane } = Tabs;

const StockDetail: React.FC = () => {
  const { symbol } = useParams<{ symbol: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [stock, setStock] = useState<Stock | null>(null);
  const [analysis, setAnalysis] = useState<StockAnalysis | null>(null);
  const [isTracked, setIsTracked] = useState(false);

  useEffect(() => {
    if (symbol) {
      loadStockDetail();
    }
  }, [symbol]);

  const loadStockDetail = async () => {
    try {
      setLoading(true);
      const stockData = await stockService.getStockBySymbol(symbol!);
      setStock(stockData);
      
      // Try to load analysis, but don't fail if it's not available
      try {
        const analysisData = await stockService.getStockAnalysis(symbol!);
        setAnalysis(analysisData);
      } catch (error) {
        console.log('Analysis not available for this stock');
        setAnalysis(null);
      }
      
      // Check if tracked
      const trackedStocks = await stockService.getTrackedStocks();
      setIsTracked(trackedStocks.some(ts => ts.stock.symbol === symbol));
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Failed to load stock details');
      console.error('Error loading stock details:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTrackToggle = async () => {
    try {
      if (isTracked) {
        await stockService.untrackStock(symbol!);
        message.success(`Stopped tracking ${symbol}`);
        setIsTracked(false);
      } else {
        await stockService.trackStock(symbol!);
        message.success(`Now tracking ${symbol}`);
        setIsTracked(true);
      }
    } catch (error) {
      message.error('Failed to update tracking status');
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!stock) {
    return <div>Stock not found</div>;
  }

  const priceChange = (Math.random() - 0.5) * 10;
  const isPositive = priceChange >= 0;

  return (
    <div>
      {/* Header */}
      <Space style={{ marginBottom: 24 }}>
        <Button icon={<LeftOutlined />} onClick={() => navigate(-1)}>
          Back
        </Button>
      </Space>

      {/* Stock Info Card */}
      <Card>
        <Row gutter={[16, 16]} align="middle">
          <Col flex="auto">
            <Space direction="vertical" size="small">
              <Space>
                <h1 style={{ margin: 0 }}>{stock.name}</h1>
                <Tag color="blue" style={{ fontSize: 16 }}>{stock.symbol}</Tag>
              </Space>
              <Space>
                {stock.sector && <Tag>{stock.sector}</Tag>}
                {stock.industry && <Tag>{stock.industry}</Tag>}
                {stock.exchange && <Tag>{stock.exchange}</Tag>}
              </Space>
            </Space>
          </Col>
          <Col>
            <Space size="large">
              <Statistic
                title="Current Price"
                value={stock.current_price}
                precision={2}
                prefix="$"
                valueStyle={{ fontSize: 32 }}
              />
              <Statistic
                title="Change"
                value={priceChange}
                precision={2}
                suffix="%"
                valueStyle={{ color: isPositive ? '#3f8600' : '#cf1322' }}
                prefix={isPositive ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
              />
              <Button
                type={isTracked ? 'default' : 'primary'}
                icon={isTracked ? <StarFilled /> : <StarOutlined />}
                onClick={handleTrackToggle}
                size="large"
              >
                {isTracked ? 'Tracked' : 'Track'}
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Tabs */}
      <Card style={{ marginTop: 16 }}>
        <Tabs defaultActiveKey="overview">
          <TabPane tab="Overview" key="overview">
            <Descriptions bordered column={2}>
              <Descriptions.Item label="Symbol">{stock.symbol}</Descriptions.Item>
              <Descriptions.Item label="Name">{stock.name}</Descriptions.Item>
              <Descriptions.Item label="Sector">{stock.sector || '-'}</Descriptions.Item>
              <Descriptions.Item label="Industry">{stock.industry || '-'}</Descriptions.Item>
              <Descriptions.Item label="Market Cap">
                ${stock.market_cap ? (stock.market_cap / 1e9).toFixed(2) + 'B' : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Currency">{stock.currency}</Descriptions.Item>
              <Descriptions.Item label="Exchange">{stock.exchange || '-'}</Descriptions.Item>
              <Descriptions.Item label="Status">
                <Tag color={stock.is_active ? 'green' : 'red'}>
                  {stock.is_active ? 'Active' : 'Inactive'}
                </Tag>
              </Descriptions.Item>
            </Descriptions>
          </TabPane>

          <TabPane tab="Technical Analysis" key="analysis">
            {analysis?.technical_analysis ? (
              <Row gutter={[16, 16]}>
                <Col span={24}>
                  <Card title="Trend Analysis">
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <div>
                        <strong>Trend:</strong>{' '}
                        <Tag color="blue">{analysis.technical_analysis.trend}</Tag>
                      </div>
                      <div>
                        <strong>Strength:</strong>{' '}
                        <Tag color="green">{analysis.technical_analysis.strength}</Tag>
                      </div>
                      <div>
                        <strong>Recommendation:</strong>{' '}
                        <Tag color="orange">{analysis.technical_analysis.recommendation}</Tag>
                      </div>
                    </Space>
                  </Card>
                </Col>
                <Col span={8}>
                  <Card>
                    <Statistic
                      title="Daily Change"
                      value={analysis.technical_analysis.daily_change}
                      precision={2}
                      suffix="%"
                      valueStyle={{ color: analysis.technical_analysis.daily_change >= 0 ? '#3f8600' : '#cf1322' }}
                    />
                  </Card>
                </Col>
                <Col span={8}>
                  <Card>
                    <Statistic
                      title="Weekly Change"
                      value={analysis.technical_analysis.weekly_change}
                      precision={2}
                      suffix="%"
                      valueStyle={{ color: analysis.technical_analysis.weekly_change >= 0 ? '#3f8600' : '#cf1322' }}
                    />
                  </Card>
                </Col>
                <Col span={8}>
                  <Card>
                    <Statistic
                      title="Monthly Change"
                      value={analysis.technical_analysis.monthly_change}
                      precision={2}
                      suffix="%"
                      valueStyle={{ color: analysis.technical_analysis.monthly_change >= 0 ? '#3f8600' : '#cf1322' }}
                    />
                  </Card>
                </Col>
              </Row>
            ) : (
              <div style={{ textAlign: 'center', padding: 40 }}>
                <p>Technical analysis not available</p>
              </div>
            )}
          </TabPane>

          <TabPane tab="Risk Analysis" key="risk">
            {analysis?.risk_analysis ? (
              <Row gutter={[16, 16]}>
                <Col span={24}>
                  <Card title="Risk Assessment">
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <div>
                        <strong>Risk Level:</strong>{' '}
                        <Tag color={
                          analysis.risk_analysis.risk_level === 'high' ? 'red' :
                          analysis.risk_analysis.risk_level === 'medium' ? 'orange' : 'green'
                        }>
                          {analysis.risk_analysis.risk_level.toUpperCase()}
                        </Tag>
                      </div>
                      <div>
                        <strong>Risk Score:</strong> {analysis.risk_analysis.risk_score}
                      </div>
                      <div>
                        <strong>Risk Factors:</strong>{' '}
                        {analysis.risk_analysis.risk_factors.map(factor => (
                          <Tag key={factor} color="red">{factor}</Tag>
                        ))}
                      </div>
                      <div>
                        <strong>Recommendation:</strong> {analysis.risk_analysis.recommendation}
                      </div>
                    </Space>
                  </Card>
                </Col>
                <Col span={12}>
                  <Card>
                    <Statistic
                      title="Volatility"
                      value={analysis.risk_analysis.volatility}
                      precision={2}
                    />
                  </Card>
                </Col>
                <Col span={12}>
                  <Card>
                    <Statistic
                      title="Beta"
                      value={analysis.risk_analysis.beta}
                      precision={2}
                    />
                  </Card>
                </Col>
              </Row>
            ) : (
              <div style={{ textAlign: 'center', padding: 40 }}>
                <p>Risk analysis not available</p>
              </div>
            )}
          </TabPane>

          <TabPane tab="Sentiment" key="sentiment">
            {analysis?.sentiment_analysis ? (
              <Card title="Market Sentiment">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <strong>Overall Sentiment:</strong>{' '}
                    <Tag color={
                      analysis.sentiment_analysis.overall_sentiment === 'positive' ? 'green' :
                      analysis.sentiment_analysis.overall_sentiment === 'negative' ? 'red' : 'blue'
                    }>
                      {analysis.sentiment_analysis.overall_sentiment.toUpperCase()}
                    </Tag>
                  </div>
                  <div>
                    <strong>Sentiment Score:</strong> {analysis.sentiment_analysis.sentiment_score.toFixed(2)}
                  </div>
                  <div>
                    <strong>Confidence:</strong> {(analysis.sentiment_analysis.confidence * 100).toFixed(0)}%
                  </div>
                  <div>
                    <strong>Key Factors:</strong>{' '}
                    {analysis.sentiment_analysis.key_factors.map(factor => (
                      <Tag key={factor}>{factor}</Tag>
                    ))}
                  </div>
                </Space>
              </Card>
            ) : (
              <div style={{ textAlign: 'center', padding: 40 }}>
                <p>Sentiment analysis not available</p>
              </div>
            )}
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default StockDetail;


