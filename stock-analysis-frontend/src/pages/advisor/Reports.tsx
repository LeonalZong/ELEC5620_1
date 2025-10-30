import React, { useEffect, useState } from 'react';
import { Card, Table, Input, message, DatePicker, Space, Button } from 'antd';
import { useNavigate } from 'react-router-dom';
import GenerateReportModal from './components/GenerateReportModal';
import dayjs from 'dayjs';
import { advisorService } from '@/services/advisorService';

const { Search } = Input;

const AdvisorReports: React.FC = () => {
  const [clientId, setClientId] = useState<number | undefined>(undefined);
  const navigate = useNavigate();
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [range, setRange] = useState<[any, any] | null>(null);
  const [open, setOpen] = useState(false);

  const load = async (cid?: number) => {
    if (!cid) return;
    try {
      setLoading(true);
      const params: any = {};
      if (range && range[0] && range[1]) {
        params.start = dayjs(range[0]).toISOString();
        params.end = dayjs(range[1]).toISOString();
      }
      const list = await advisorService.getReports(cid, params);
      setReports(list);
    } catch (e) {
      message.error('Failed to load reports');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { if (clientId) load(clientId); }, [clientId]);

  const columns = [
    { title: 'Title', dataIndex: 'title', key: 'title', render: (text: string, record: any) => (
      <a onClick={() => navigate(`/advisor/reports/${record.id}`)}>{text}</a>
    ) },
    { title: 'Summary', dataIndex: 'summary', key: 'summary' },
    { title: 'Created', dataIndex: 'created_at', key: 'created_at' },
  ];

  return (
    <div>
      <h1 style={{ marginBottom: 16 }}>Reports</h1>
      <Card style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Search
            placeholder="Enter client user id"
            enterButton="Load"
            onSearch={(v) => setClientId(Number(v) || undefined)}
          />
          <DatePicker.RangePicker onChange={(vals) => setRange(vals as any)} />
          <div>
            <Button type="primary" disabled={!clientId} onClick={() => setOpen(true)}>Generate Report</Button>
          </div>
        </Space>
      </Card>
      <Card>
        <Table dataSource={reports} columns={columns} rowKey="id" loading={loading} />
      </Card>
      {clientId && (
        <GenerateReportModal open={open} onClose={() => setOpen(false)} clientId={clientId} onSuccess={() => load(clientId)} />
      )}
    </div>
  );
};

export default AdvisorReports;


