import React, { useEffect, useRef, useState } from 'react';
import { Card, Input, Button, Space, Typography, Avatar, Spin, message, Tag, Select } from 'antd';
import { SendOutlined, RobotOutlined, UserOutlined, PlusOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import { streamChatMessage, createNewSession } from '@/services/chatService';
import { advisorService, AdvisorClient } from '@/services/advisorService';

const { TextArea } = Input;
const { Title, Text } = Typography;

interface MessageItem {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const AdvisorAIAssistant: React.FC = () => {
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const [streamingContent, setStreamingContent] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [subjectUserId, setSubjectUserId] = useState<number | undefined>(undefined);
  const [manualClientId, setManualClientId] = useState<string>('');
  const [clients, setClients] = useState<AdvisorClient[]>([]);
  const [clientsLoading, setClientsLoading] = useState<boolean>(false);

  useEffect(() => {
    const init = async () => {
      try {
        const id = await createNewSession();
        setSessionId(id);
        setMessages([{
          role: 'assistant',
          content: `👋 Hi Advisor! Select a client and ask me to analyze their portfolio, market trends, alerts, or performance.`,
          timestamp: new Date()
        }]);
        // fetch clients (best-effort)
        setClientsLoading(true);
        const list = await advisorService.getClients();
        setClients(list);
      } catch (e) {
        message.error('Failed to initialize session');
      } finally {
        setClientsLoading(false);
      }
    };
    init();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;

    if (!subjectUserId) {
      message.warning('Please set a client user id before sending.');
      return;
    }

    const userMsg: MessageItem = { role: 'user', content: text, timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    const aiMsg: MessageItem = { role: 'assistant', content: '', timestamp: new Date() };
    setMessages(prev => [...prev, aiMsg]);

    try {
      let full = '';
      await streamChatMessage(
        text,
        sessionId,
        chunk => { full += chunk; setStreamingContent(full); },
        () => {
          setMessages(prev => {
            const list = [...prev];
            list[list.length - 1] = { ...list[list.length - 1], content: full };
            return list;
          });
          setStreamingContent('');
          setLoading(false);
        },
        err => {
          message.error(`Failed to send: ${err}`);
          setMessages(prev => prev.slice(0, -1));
          setStreamingContent('');
          setLoading(false);
        },
        { subject_user_id: subjectUserId }
      );
    } catch (e: any) {
      message.error(`Failed to send: ${e.message}`);
      setMessages(prev => prev.slice(0, -1));
      setLoading(false);
    }
  };

  const handleNewChat = async () => {
    try {
      const id = await createNewSession();
      setSessionId(id);
      setMessages([{
        role: 'assistant',
        content: `👋 Started a new conversation! Select a client and tell me what to analyze.`,
        timestamp: new Date()
      }]);
      message.success('Started new conversation');
    } catch (e) {
      message.error('Failed to start new conversation');
    }
  };

  const tryExtractDraft = (text: string): { token?: string; diff?: string } => {
    try {
      const codeBlockMatch = text.match(/```[\s\S]*?\{[\s\S]*\}[\s\S]*?```/);
      const jsonMatch = codeBlockMatch ? codeBlockMatch[0].replace(/```/g, '') : text;
      const obj = JSON.parse(jsonMatch.match(/\{[\s\S]*\}/)?.[0] || '{}');
      if (obj.status === 'draft' && obj.token) {
        return { token: String(obj.token), diff: String(obj.diff_summary || '') };
      }
    } catch {}
    return {};
  };

  const renderMessage = (msg: MessageItem, i: number) => {
    const isUser = msg.role === 'user';
    const isLastAI = msg.role === 'assistant' && i === messages.length - 1;
    const display = isLastAI && streamingContent ? streamingContent : msg.content;
    const draft = !isUser ? tryExtractDraft(display) : {};
    return (
      <div key={i} style={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start', marginBottom: 16 }}>
        <Space align="start" direction="horizontal" style={{ maxWidth: '75%', display: 'flex', flexDirection: isUser ? 'row' : 'row-reverse' }}>
          <Avatar icon={isUser ? <UserOutlined /> : <RobotOutlined />} style={{ backgroundColor: isUser ? '#1890ff' : '#52c41a' }} />
          <Card style={{ backgroundColor: isUser ? '#e6f7ff' : '#f6ffed', border: 'none', borderRadius: 12 }} bodyStyle={{ padding: '12px 16px' }}>
            {isUser ? (
              <Text>{display}</Text>
            ) : (
              <div className="markdown-content">
                {/* 如果检测到 draft.token，则不渲染原始 JSON，改为摘要+按钮 */}
                {draft.token ? null : <ReactMarkdown>{display}</ReactMarkdown>}
                {isLastAI && loading && (<Spin size="small" style={{ marginLeft: 8 }} />)}
              </div>
            )}
            {!isUser && draft.token && (
              <div style={{ marginTop: 8 }}>
                <Space>
                  <Button type="primary" size="small" onClick={() => setInput(`confirm ${draft.token}`)}>Confirm</Button>
                  <Button size="small" onClick={() => setInput(`cancel ${draft.token}`)}>Cancel</Button>
                </Space>
                {draft.diff && <div style={{ marginTop: 6, fontSize: 12, color: '#666' }}>{draft.diff}</div>}
              </div>
            )}
            <div style={{ marginTop: 8, fontSize: 12, color: '#999' }}>{msg.timestamp.toLocaleTimeString()}</div>
          </Card>
        </Space>
      </div>
    );
  };

  return (
    <div style={{ height: 'calc(100vh - 64px)', display: 'flex', flexDirection: 'column', padding: 24, background: '#f0f2f5' }}>
      <Card style={{ marginBottom: 16 }} bodyStyle={{ padding: '16px 24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Space>
            <RobotOutlined style={{ fontSize: 24, color: '#52c41a' }} />
            <Title level={4} style={{ margin: 0 }}>Advisor AI Assistant</Title>
            <Tag color="blue">Client mode</Tag>
          </Space>
          <Space>
            <Select
              showSearch
              placeholder="Select client"
              loading={clientsLoading}
              style={{ width: 220 }}
              filterOption={(input, option) =>
                (option?.label as string).toLowerCase().includes(input.toLowerCase())
              }
              options={clients.map(c => ({ value: c.id, label: `${c.username} (#${c.id})` }))}
              onChange={(val) => setSubjectUserId(Number(val))}
              value={subjectUserId}
              allowClear
            />
            <Input
              placeholder="or type client id"
              style={{ width: 160 }}
              value={manualClientId}
              onChange={(e) => setManualClientId(e.target.value)}
              onPressEnter={() => setSubjectUserId(Number(manualClientId) || undefined)}
            />
            <Button onClick={() => setSubjectUserId(Number(manualClientId) || undefined)}>Set</Button>
            <Button icon={<PlusOutlined />} onClick={handleNewChat}>New Chat</Button>
          </Space>
        </div>
      </Card>

      <Card style={{ flex: 1, marginBottom: 16, overflow: 'hidden', display: 'flex', flexDirection: 'column' }} bodyStyle={{ padding: 24, flex: 1, overflowY: 'auto' }}>
        <div style={{ marginBottom: 8 }}>
          <Text type="secondary">Current client user id: {subjectUserId ?? '-'}</Text>
        </div>
        <div style={{ flex: 1 }}>
          {messages.map((m, i) => renderMessage(m, i))}
          <div ref={messagesEndRef} />
        </div>
      </Card>

      <Card bodyStyle={{ padding: 16 }}>
        <Space.Compact style={{ width: '100%' }}>
          <TextArea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onPressEnter={(e) => { if (!e.shiftKey) { e.preventDefault(); handleSend(); } }}
            placeholder="Enter your question... (Shift+Enter newline)"
            autoSize={{ minRows: 1, maxRows: 4 }}
            disabled={loading}
            style={{ flex: 1 }}
          />
          <Button type="primary" icon={<SendOutlined />} onClick={handleSend} loading={loading} disabled={!input.trim() || !subjectUserId}>
            Send
          </Button>
        </Space.Compact>
        <Text type="secondary" style={{ fontSize: 12, marginTop: 8, display: 'block' }}>
          Tip: Select a client user id before sending. This assistant analyzes data for that client only.
        </Text>
      </Card>
    </div>
  );
};

export default AdvisorAIAssistant;


