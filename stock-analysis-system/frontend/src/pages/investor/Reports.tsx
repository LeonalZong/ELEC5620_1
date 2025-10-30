import React, { useEffect, useState } from 'react';
import { Card, Table, Button, Space, Tag, message, Modal, Typography } from 'antd';
import { FileTextOutlined, EyeOutlined, DownloadOutlined } from '@ant-design/icons';
import api from '@/services/api';
import type { Report } from '@/types';

const { Paragraph } = Typography;

const Reports: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [reports, setReports] = useState<Report[]>([]);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [isModalVisible, setIsModalVisible] = useState(false);

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      setLoading(true);
      const response = await api.get('/reports');
      setReports(response.data);
    } catch (error) {
      message.error('Failed to load reports');
    } finally {
      setLoading(false);
    }
  };

  const handleViewReport = (report: Report) => {
    setSelectedReport(report);
    setIsModalVisible(true);
  };

  const handleDownloadReport = async (reportId: number) => {
    try {
      const response = await api.get(`/reports/${reportId}/download`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `report_${reportId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      message.success('Report downloaded');
    } catch (error) {
      message.error('Failed to download report');
    }
  };

  const getReportTypeColor = (type: string) => {
    switch (type) {
      case 'DAILY':
        return 'blue';
      case 'WEEKLY':
        return 'green';
      case 'MONTHLY':
        return 'orange';
      case 'CUSTOM':
        return 'purple';
      default:
        return 'default';
    }
  };

  const columns = [
    {
      title: 'Stock',
      dataIndex: ['stock', 'symbol'],
      key: 'symbol',
      render: (symbol: string, record: Report) => (
        <Space>
          <Tag color="blue">{symbol}</Tag>
          <span>{record.stock?.name}</span>
        </Space>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'report_type',
      key: 'type',
      render: (type: string) => (
        <Tag color={getReportTypeColor(type)}>
          {type}
        </Tag>
      ),
    },
    {
      title: 'Title',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
    },
    {
      title: 'Generated At',
      dataIndex: 'created_at',
      key: 'created',
      render: (date: string) => new Date(date).toLocaleString(),
      sorter: (a: Report, b: Report) => 
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      defaultSortOrder: 'ascend',
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Report) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleViewReport(record)}
          >
            View
          </Button>
          <Button
            type="link"
            icon={<DownloadOutlined />}
            onClick={() => handleDownloadReport(record.id)}
          >
            Download
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>
        <FileTextOutlined /> Reports
      </h1>

      <Card>
        <Table
          dataSource={reports}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showTotal: (total) => `Total ${total} reports`,
          }}
        />
      </Card>

      {/* Report Detail Modal */}
      <Modal
        title={selectedReport?.title}
        open={isModalVisible}
        onCancel={() => {
          setIsModalVisible(false);
          setSelectedReport(null);
        }}
        footer={[
          <Button key="close" onClick={() => setIsModalVisible(false)}>
            Close
          </Button>,
          <Button
            key="download"
            type="primary"
            icon={<DownloadOutlined />}
            onClick={() => selectedReport && handleDownloadReport(selectedReport.id)}
          >
            Download
          </Button>,
        ]}
        width={800}
      >
        {selectedReport && (
          <div>
            <Space direction="vertical" style={{ width: '100%', marginBottom: 16 }}>
              <div>
                <strong>Stock:</strong> {selectedReport.stock?.symbol} - {selectedReport.stock?.name}
              </div>
              <div>
                <strong>Type:</strong> <Tag color={getReportTypeColor(selectedReport.report_type)}>
                  {selectedReport.report_type}
                </Tag>
              </div>
              <div>
                <strong>Generated:</strong> {new Date(selectedReport.created_at).toLocaleString()}
              </div>
            </Space>

            <Card title="Summary" size="small" style={{ marginBottom: 16 }}>
              <Paragraph>{selectedReport.summary}</Paragraph>
            </Card>

            <Card title="Full Report" size="small">
              <Paragraph style={{ whiteSpace: 'pre-wrap' }}>
                {selectedReport.content}
              </Paragraph>
            </Card>

            {selectedReport.recommendations && (
              <Card title="Recommendations" size="small" style={{ marginTop: 16 }}>
                <Paragraph>{selectedReport.recommendations}</Paragraph>
              </Card>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default Reports;

