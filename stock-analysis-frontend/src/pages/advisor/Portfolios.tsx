import React, { useEffect, useState } from 'react';
import { Card, Select, Button, Space, message } from 'antd';
import { useNavigate } from 'react-router-dom';
import { advisorService, AdvisorClient } from '@/services/advisorService';

const AdvisorPortfolios: React.FC = () => {
  const navigate = useNavigate();
  const [clients, setClients] = useState<AdvisorClient[]>([]);
  const [loading, setLoading] = useState(false);
  const [clientId, setClientId] = useState<number | undefined>(undefined);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const list = await advisorService.getClients();
        setClients(list);
      } catch (e) {
        message.error('Failed to load clients');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  return (
    <div>
      <h1 style={{ marginBottom: 16 }}>Client Portfolios</h1>
      <Card>
        <Space>
          <Select
            showSearch
            placeholder="Select client"
            loading={loading}
            style={{ width: 260 }}
            options={clients.map(c => ({ value: c.id, label: `${c.username} (#${c.id})` }))}
            filterOption={(input, option) => (option?.label as string).toLowerCase().includes(input.toLowerCase())}
            value={clientId}
            onChange={(v) => setClientId(Number(v))}
            allowClear
          />
          <Button type="primary" disabled={!clientId} onClick={() => navigate(`/advisor/clients/${clientId}`)}>View</Button>
        </Space>
      </Card>
    </div>
  );
};

export default AdvisorPortfolios;


