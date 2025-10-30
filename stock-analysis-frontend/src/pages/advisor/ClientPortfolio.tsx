import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Card, Table, Tag, Statistic, Row, Col, message, Button, Space } from 'antd';
import GenerateReportModal from './components/GenerateReportModal';
import { advisorService } from '@/services/advisorService';

const ClientPortfolio: React.FC = () => {
  const { id } = useParams();
  const clientId = Number(id);
  const [summary, setSummary] = useState<any>(null);
  const [holdings, setHoldings] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [reportOpen, setReportOpen] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const [s, h] = await Promise.all([
          advisorService.getClientSummary(clientId).catch(() => null),
          advisorService.getClientPortfolio(clientId).catch(() => []),
        ]);
        setSummary(s);
        setHoldings(h);
      } catch (e) {
        message.error('Failed to load client portfolio');
      } finally {
        setLoading(false);
      }
    };
    if (!isNaN(clientId)) load();
  }, [clientId]);

  const columns = [
    { title: 'Symbol', dataIndex: ['stock', 'symbol'], key: 'symbol' },
    { title: 'Name', dataIndex: ['stock', 'name'], key: 'name' },
    { title: 'Quantity', dataIndex: 'quantity', key: 'quantity', align: 'right' as const },
    { title: 'Purchase', dataIndex: 'purchase_price', key: 'purchase_price', align: 'right' as const,
      render: (v: number) => `$${(v ?? 0).toFixed(2)}` },
    { title: 'Current', dataIndex: 'current_price', key: 'current_price', align: 'right' as const,
      render: (v: number) => `$${(v ?? 0).toFixed(2)}` },
    { title: 'Value', dataIndex: 'current_value', key: 'current_value', align: 'right' as const,
      render: (v: number) => `$${(v ?? 0).toFixed(2)}` },
    { title: 'P/L %', dataIndex: 'profit_loss_pct', key: 'profit_loss_pct', align: 'right' as const,
      render: (v: number) => <Tag color={v >= 0 ? 'green' : 'red'}>{(v ?? 0).toFixed(2)}%</Tag> },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 style={{ margin: 0 }}>Client Portfolio</h1>
        <Space>
          <Button type="primary" disabled={isNaN(clientId)} onClick={() => setReportOpen(true)}>
            Generate Report
          </Button>
        </Space>
      </div>
      <Row gutter={[16,16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={12} md={6}>
          <Card loading={loading}>
            <Statistic title="Total Value" value={summary?.total_value ?? 0} precision={2} prefix="$" />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card loading={loading}>
            <Statistic title="Total P/L" value={summary?.total_profit_loss ?? 0} precision={2} prefix="$" />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card loading={loading}>
            <Statistic title="Return %" value={summary?.total_profit_loss_pct ?? 0} precision={2} suffix="%" />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card loading={loading}>
            <Statistic title="Holdings" value={summary?.total_holdings ?? holdings.length} />
          </Card>
        </Col>
      </Row>

      <Card>
        <Table
          dataSource={holdings}
          columns={columns}
          rowKey={(r) => `${r.stock?.symbol}-${r.purchase_date}`}
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {!isNaN(clientId) && (
        <GenerateReportModal
          open={reportOpen}
          onClose={() => setReportOpen(false)}
          clientId={clientId}
          onSuccess={() => { /* could navigate to reports or refresh */ }}
        />
      )}
    </div>
  );
};

export default ClientPortfolio;


