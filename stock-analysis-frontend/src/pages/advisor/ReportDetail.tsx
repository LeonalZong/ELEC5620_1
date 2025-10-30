import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Card, Typography, Spin, message } from 'antd';
import { advisorService } from '@/services/advisorService';

const { Title, Paragraph, Text } = Typography;

const ReportDetail: React.FC = () => {
  const { id } = useParams();
  const reportId = Number(id);
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const data = await advisorService.getReport(reportId);
        setReport(data);
      } catch (e) {
        message.error('Failed to load report');
      } finally {
        setLoading(false);
      }
    };
    if (!isNaN(reportId)) load();
  }, [reportId]);

  if (loading) return <Spin />;
  if (!report) return null;

  return (
    <div>
      <Title level={2}>{report.title}</Title>
      <Text type="secondary">Created at: {report.created_at}</Text>
      <Card title="Executive Summary" style={{ marginTop: 16 }}>
        <Paragraph>{report.summary}</Paragraph>
      </Card>
      {report.content && (
        <Card title="Content" style={{ marginTop: 16 }}>
          <Paragraph style={{ whiteSpace: 'pre-wrap' }}>{report.content}</Paragraph>
        </Card>
      )}
      {report.details_json && (
        <Card title="Details" style={{ marginTop: 16 }}>
          <pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(report.details_json, null, 2)}</pre>
        </Card>
      )}
    </div>
  );
};

export default ReportDetail;


