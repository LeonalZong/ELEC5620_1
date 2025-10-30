import React, { useEffect, useState } from 'react';
import { Card, Table, Button, Space, Tag, message, Modal, Typography, Tabs } from 'antd';
import { FileTextOutlined, EyeOutlined, DownloadOutlined, TableOutlined, FileSearchOutlined } from '@ant-design/icons';
import api from '@/services/api';
import type { Report } from '@/types';

const { Paragraph, Text } = Typography;
const { TabPane } = Tabs;

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

  // Split content into data overview and full analysis
  const splitReportContent = (content: string) => {
    const separator = '\n\n---\n\n';
    const parts = content.split(separator);
    
    if (parts.length >= 2) {
      return {
        dataOverview: parts[0],
        fullAnalysis: parts[1]
      };
    }
    
    // Fallback if separator not found
    return {
      dataOverview: '',
      fullAnalysis: content
    };
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
      width: 150,
      render: (symbol: string, record: Report) => (
        <Space direction="vertical" size={0}>
          <Tag color="blue">{symbol}</Tag>
          <span style={{ fontSize: '12px', color: '#666' }}>
            {record.stock?.name || 'Unknown Stock'}
          </span>
        </Space>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'report_type',
      key: 'type',
      width: 120,
      align: 'center',
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
      width: 200,
    },
    {
      title: 'Generated At',
      dataIndex: 'created_at',
      key: 'created',
      width: 150,
      render: (date: string) => new Date(date).toLocaleString(),
      sorter: (a: Report, b: Report) => 
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      defaultSortOrder: 'ascend',
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      align: 'center',
      render: (_: any, record: Report) => (
        <Space>
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => handleViewReport(record)}
            title="View Report"
          />
          <Button
            type="text"
            icon={<DownloadOutlined />}
            onClick={() => handleDownloadReport(record.id)}
            title="Download Report"
          />
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <FileTextOutlined style={{ marginRight: '8px' }} />
            Reports
          </div>
        }
        bordered={false}
        style={{ boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}
      >
        <Table
          dataSource={reports}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showTotal: (total) => `Total ${total} reports`,
            showSizeChanger: true,
            showQuickJumper: true,
          }}
          scroll={{ x: 800 }}
          size="middle"
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
        width={1200}
        style={{ top: 20 }}
        bodyStyle={{ maxHeight: 'calc(100vh - 200px)', overflowY: 'auto' }}
      >
        {selectedReport && (() => {
          const { dataOverview, fullAnalysis } = splitReportContent(selectedReport.content || '');
          
          return (
            <div>
              {/* Stock Information Header */}
              <Card size="small" style={{ marginBottom: 16, backgroundColor: '#f5f5f5' }}>
                <Space direction="vertical" style={{ width: '100%' }} size={4}>
                  <div>
                    <Text strong>Stock:</Text> <Tag color="blue">{selectedReport.stock?.symbol || 'Unknown'}</Tag>
                    <Text type="secondary">{selectedReport.stock?.name || 'Unknown Stock'}</Text>
                  </div>
                  <div>
                    <Text strong>Type:</Text> <Tag color={getReportTypeColor(selectedReport.report_type)}>
                      {selectedReport.report_type}
                    </Tag>
                    <Text strong style={{ marginLeft: 16 }}>Generated:</Text> <Text type="secondary">
                      {new Date(selectedReport.created_at).toLocaleString()}
                    </Text>
                  </div>
                </Space>
              </Card>

              {/* Tabs for different sections */}
              <Tabs defaultActiveKey="1" size="large">
                {/* Tab 1: Summary */}
                <TabPane
                  tab={
                    <span>
                      <FileTextOutlined />
                      Summary
                    </span>
                  }
                  key="1"
                >
                  <Card bordered={false} style={{ backgroundColor: '#fafafa' }}>
                    <Paragraph style={{ fontSize: '14px', lineHeight: '1.8' }}>
                      {selectedReport.summary}
                    </Paragraph>
                  </Card>
                  
                  {selectedReport.recommendations && (
                    <Card 
                      title={<Text strong>Investment Recommendations</Text>} 
                      size="small" 
                      style={{ marginTop: 16, borderLeft: '3px solid #1890ff' }}
                    >
                      <Paragraph style={{ fontSize: '14px', whiteSpace: 'pre-wrap' }}>
                        {selectedReport.recommendations}
                      </Paragraph>
                    </Card>
                  )}
                </TabPane>

                {/* Tab 2: Data Overview */}
                <TabPane
                  tab={
                    <span>
                      <TableOutlined />
                      Data Overview
                    </span>
                  }
                  key="2"
                >
                  <Card bordered={false}>
                    <pre style={{ 
                      fontFamily: 'Monaco, Courier, monospace', 
                      fontSize: '13px',
                      backgroundColor: '#f5f5f5',
                      padding: '16px',
                      borderRadius: '4px',
                      overflowX: 'auto',
                      lineHeight: '1.6'
                    }}>
                      {dataOverview || 'No data overview available.'}
                    </pre>
                  </Card>
                </TabPane>

                {/* Tab 3: Full Analysis */}
                <TabPane
                  tab={
                    <span>
                      <FileSearchOutlined />
                      Full Analysis
                    </span>
                  }
                  key="3"
                >
                  {(() => {
                    // Parse the full analysis into sections
                    const sections = fullAnalysis.split(/(?=# )/g).filter(s => s.trim());
                    
                    return (
                      <Space direction="vertical" style={{ width: '100%' }} size="large">
                        {sections.map((section, index) => {
                          // Extract title and content
                          const lines = section.split('\n');
                          const titleLine = lines[0].replace(/^#+\s*/, '').replace(/^\s*[\d📊⚠️💭📈📝]+\s*/, '');
                          const content = lines.slice(1).join('\n').trim();
                          
                          // Determine card color based on section type
                          let borderColor = '#1890ff';
                          let bgColor = '#ffffff';
                          
                          if (titleLine.includes('Risk')) {
                            borderColor = '#faad14';
                            bgColor = '#fffbe6';
                          } else if (titleLine.includes('Sentiment')) {
                            borderColor = '#722ed1';
                            bgColor = '#f9f0ff';
                          } else if (titleLine.includes('Fundamental')) {
                            borderColor = '#52c41a';
                            bgColor = '#f6ffed';
                          } else if (titleLine.includes('Conclusion')) {
                            borderColor = '#eb2f96';
                            bgColor = '#fff0f6';
                          }
                          
                          // Render content as flowing paragraphs
                          const paragraphs = content.split('\n\n').filter(p => p.trim());
                          
                          return (
                            <Card
                              key={index}
                              title={
                                <Text strong style={{ fontSize: '16px', color: borderColor }}>
                                  {titleLine}
                                </Text>
                              }
                              bordered={true}
                              style={{ 
                                borderLeft: `4px solid ${borderColor}`,
                                backgroundColor: bgColor,
                                boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
                              }}
                            >
                              <Space direction="vertical" style={{ width: '100%' }} size="middle">
                                {paragraphs.map((paragraph, pIndex) => {
                                  // Check if this is a subsection header (starts with ##)
                                  if (paragraph.trim().startsWith('##')) {
                                    const subLines = paragraph.split('\n');
                                    const subTitle = subLines[0].replace(/^#+\s*/, '').trim();
                                    const subContent = subLines.slice(1).join('\n').trim();
                                    
                                    return (
                                      <div key={pIndex} style={{ marginBottom: '16px' }}>
                                        <Text strong style={{ fontSize: '15px', display: 'block', marginBottom: '8px', color: '#262626' }}>
                                          {subTitle}
                                        </Text>
                                        <Paragraph 
                                          style={{ 
                                            fontSize: '14px',
                                            lineHeight: '1.9',
                                            color: '#434343',
                                            textAlign: 'justify',
                                            marginBottom: '12px',
                                            paddingLeft: '12px',
                                            borderLeft: '2px solid #e8e8e8'
                                          }}
                                        >
                                          {subContent}
                                        </Paragraph>
                                      </div>
                                    );
                                  } else {
                                    // Regular paragraph
                                    return (
                                      <Paragraph 
                                        key={pIndex}
                                        style={{ 
                                          fontSize: '14px',
                                          lineHeight: '1.9',
                                          color: '#434343',
                                          textAlign: 'justify',
                                          marginBottom: '12px'
                                        }}
                                      >
                                        {paragraph}
                                      </Paragraph>
                                    );
                                  }
                                })}
                              </Space>
                            </Card>
                          );
                        })}
                      </Space>
                    );
                  })()}
                </TabPane>
              </Tabs>
            </div>
          );
        })()}
      </Modal>
    </div>
  );
};

export default Reports;


