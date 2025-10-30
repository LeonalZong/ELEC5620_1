import React, { useEffect, useState } from 'react';
import { Card, Input, Table, Progress, Row, Col, Statistic, message, Select } from 'antd';
import { advisorService } from '@/services/advisorService';

const { Search } = Input;

const AdvisorAnalytics: React.FC = () => {
  const [clientId, setClientId] = useState<number | undefined>(undefined);
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [returns, setReturns] = useState<{date:string; value:number; change_pct:number}[]>([]);
  const [days, setDays] = useState<number>(30);

  const load = async (cid?: number) => {
    if (!cid) return;
    try {
      setLoading(true);
      const res = await advisorService.getAnalytics(cid);
      setData(res);
    } catch (e) {
      message.error('Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { if (clientId) load(clientId); }, [clientId]);
  useEffect(() => { if (clientId) loadReturns(clientId, days); }, [clientId, days]);

  const loadReturns = async (cid: number, d: number) => {
    try {
      const res = await advisorService.getReturns(cid, d);
      setReturns(res.equity || []);
    } catch (e) {
      // ignore
    }
  };

  const sectors = Object.entries(data?.sector_distribution_pct || {}).map(([k, v]: any) => ({ sector: k, pct: v as number }));

  return (
    <div>
      <h1 style={{ marginBottom: 16 }}>Analytics</h1>
      <Card style={{ marginBottom: 16 }}>
        <Search placeholder="Enter client user id" enterButton="Analyze" onSearch={(v) => setClientId(Number(v) || undefined)} />
      </Card>
      <Row gutter={[16,16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={12} md={6}>
          <Card loading={loading}>
            <Statistic title="Total Value" value={data?.total_value ?? 0} precision={2} prefix="$" />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card loading={loading}>
            <Statistic title="Holdings" value={data?.holdings ?? 0} />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card loading={loading}>
            <Statistic title="Total Alerts" value={data?.alerts?.total ?? 0} />
          </Card>
        </Col>
      </Row>
      <Card title="Sector Distribution" loading={loading}>
        <Table
          dataSource={sectors}
          columns={[{ title: 'Sector', dataIndex: 'sector', key: 'sector' }, { title: 'Percent', dataIndex: 'pct', key: 'pct', render: (v: number) => (
            <div style={{ minWidth: 200 }}>
              <Progress percent={v} size="small" />
            </div>
          ) }]}
          rowKey={(r) => r.sector}
          pagination={false}
        />
      </Card>
      <Card title="Equity Curve" style={{ marginTop: 16 }}>
        <Row style={{ marginBottom: 12 }}>
          <Col>
            <Select
              value={days}
              onChange={(v) => setDays(v)}
              options={[{value:7,label:'7d'},{value:30,label:'30d'},{value:60,label:'60d'},{value:90,label:'90d'}]}
              style={{ width: 100 }}
            />
          </Col>
        </Row>
        <Table
          dataSource={returns}
          columns={[{ title: 'Date', dataIndex: 'date', key: 'date' }, { title: 'Value', dataIndex: 'value', key: 'value' }, { title: 'Change %', dataIndex: 'change_pct', key: 'change_pct' }]}
          rowKey={(r)=>r.date}
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  );
};

export default AdvisorAnalytics;


