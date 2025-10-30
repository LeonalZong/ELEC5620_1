import React, { useState } from 'react';
import { Card, Input, Table, Button, Space, Tag, message } from 'antd';
import { SearchOutlined, EyeOutlined, StarOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { stockService } from '@/services/stockService';
import type { Stock } from '@/types';

const { Search } = Input;

const StockSearch: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [searchResults, setSearchResults] = useState<Stock[]>([]);
  const [searchTerm, setSearchTerm] = useState('');

  const handleSearch = async (value: string) => {
    if (!value.trim()) {
      message.warning('Please enter a search term');
      return;
    }

    try {
      setLoading(true);
      setSearchTerm(value);
      const results = await stockService.searchStocks(value);
      setSearchResults(results);
      
      if (results.length === 0) {
        message.info('No stocks found');
      }
    } catch (error) {
      message.error('Search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleTrackStock = async (symbol: string) => {
    try {
      await stockService.trackStock(symbol);
      message.success(`Now tracking ${symbol}`);
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Failed to track stock');
    }
  };

  const columns = [
    {
      title: 'Symbol',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (symbol: string) => <Tag color="blue">{symbol}</Tag>,
      width: 100,
    },
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
    },
    {
      title: 'Sector',
      dataIndex: 'sector',
      key: 'sector',
      render: (sector: string) => sector || '-',
    },
    {
      title: 'Industry',
      dataIndex: 'industry',
      key: 'industry',
      render: (industry: string) => industry || '-',
      ellipsis: true,
    },
    {
      title: 'Price',
      dataIndex: 'current_price',
      key: 'price',
      render: (price: number) => (
        <span style={{ fontWeight: 'bold' }}>
          ${price?.toFixed(2) || '0.00'}
        </span>
      ),
      width: 120,
    },
    {
      title: 'Market Cap',
      dataIndex: 'market_cap',
      key: 'market_cap',
      render: (cap: number) => {
        if (!cap) return '-';
        if (cap >= 1e12) return `$${(cap / 1e12).toFixed(2)}T`;
        if (cap >= 1e9) return `$${(cap / 1e9).toFixed(2)}B`;
        if (cap >= 1e6) return `$${(cap / 1e6).toFixed(2)}M`;
        return `$${cap.toFixed(2)}`;
      },
      width: 120,
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Stock) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/investor/stocks/${record.symbol}`)}
          >
            View
          </Button>
          <Button
            type="link"
            icon={<StarOutlined />}
            onClick={() => handleTrackStock(record.symbol)}
          >
            Track
          </Button>
        </Space>
      ),
      width: 180,
    },
  ];

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>
        <SearchOutlined /> Stock Search
      </h1>

      <Card>
        <Search
          placeholder="Search by symbol or company name (e.g., AAPL, Apple, BHP)"
          allowClear
          enterButton="Search"
          size="large"
          onSearch={handleSearch}
          loading={loading}
          style={{ marginBottom: 24 }}
        />

        {searchResults.length > 0 && (
          <>
            <div style={{ marginBottom: 16 }}>
              <strong>Found {searchResults.length} results for "{searchTerm}"</strong>
            </div>
            <Table
              dataSource={searchResults}
              columns={columns}
              rowKey="id"
              loading={loading}
              pagination={{
                pageSize: 20,
                showTotal: (total) => `Total ${total} stocks`,
              }}
            />
          </>
        )}

        {!loading && searchResults.length === 0 && searchTerm && (
          <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
            <SearchOutlined style={{ fontSize: 48, marginBottom: 16 }} />
            <p>No results found for "{searchTerm}"</p>
            <p>Try searching with a different term</p>
          </div>
        )}

        {!searchTerm && (
          <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
            <SearchOutlined style={{ fontSize: 48, marginBottom: 16 }} />
            <p>Enter a stock symbol or company name to search</p>
            <p>Examples: AAPL, Microsoft, BHP, Tesla</p>
          </div>
        )}
      </Card>
    </div>
  );
};

export default StockSearch;

