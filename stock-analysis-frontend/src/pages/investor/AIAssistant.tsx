/**
 * AI Assistant Page
 * AI analysis assistant page - ChatGPT-like chat interface
 */
import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  Input,
  Button,
  Space,
  Typography,
  Avatar,
  Spin,
  message,
  Tag,
  Tooltip,
  Empty
} from 'antd';
import {
  SendOutlined,
  RobotOutlined,
  UserOutlined,
  DeleteOutlined,
  PlusOutlined,
  ThunderboltOutlined
} from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import { streamChatMessage, createNewSession } from '../../services/chatService';

const { TextArea } = Input;
const { Title, Text } = Typography;

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const AIAssistant: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [streamingContent, setStreamingContent] = useState('');

  // Suggested quick questions
  const suggestedQuestions = [
    'How risky is my portfolio?',
    "What's the current market sentiment?",
    'Analyze my holdings performance',
    'Which alerts are close to triggering?',
    'Give me some investment insights'
  ];

  // Initialize session
  useEffect(() => {
    const initSession = async () => {
      try {
        const newSessionId = await createNewSession();
        setSessionId(newSessionId);
        
        // Add welcome message
        setMessages([{
          role: 'assistant',
          content: `👋 Hi! I'm your **AI Analysis Assistant**, here to help analyze your portfolio and market trends.

I can help you:
- 📊 Analyze portfolio risk
- 📈 Assess market sentiment and trends
- 💰 Calculate returns and performance
- ⚠️ Monitor alert status
- 💡 Provide investment insights

What would you like me to analyze?`,
          timestamp: new Date()
        }]);
      } catch (error) {
        message.error('Failed to initialize session');
      }
    };

    initSession();
  }, []);

  // Auto scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  // Send message
  const handleSend = async (text?: string) => {
    const messageText = text || input.trim();
    if (!messageText || loading) return;

    // Add user message
    const userMessage: Message = {
      role: 'user',
      content: messageText,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    // Add an empty AI message for streaming updates
    const aiMessage: Message = {
      role: 'assistant',
      content: '',
      timestamp: new Date()
    };
    setMessages(prev => [...prev, aiMessage]);

    try {
      let fullContent = '';

      await streamChatMessage(
        messageText,
        sessionId,
        // onChunk
        (chunk) => {
          fullContent += chunk;
          setStreamingContent(fullContent);
        },
        // onComplete
        () => {
          setMessages(prev => {
            const newMessages = [...prev];
            newMessages[newMessages.length - 1] = {
              ...newMessages[newMessages.length - 1],
              content: fullContent
            };
            return newMessages;
          });
          setStreamingContent('');
          setLoading(false);
        },
        // onError
        (error) => {
          message.error(`Failed to send message: ${error}`);
          setMessages(prev => prev.slice(0, -1)); // Remove the empty AI message
          setStreamingContent('');
          setLoading(false);
        }
      );
    } catch (error: any) {
      message.error(`Failed to send message: ${error.message}`);
      setMessages(prev => prev.slice(0, -1));
      setLoading(false);
    }
  };

  // Start new chat
  const handleNewChat = async () => {
    try {
      const newSessionId = await createNewSession();
      setSessionId(newSessionId);
      setMessages([{
        role: 'assistant',
        content: "👋 Started a new conversation! What can I analyze for you?",
        timestamp: new Date()
      }]);
      message.success('Started new conversation');
    } catch (error) {
      message.error('Failed to start new conversation');
    }
  };

  // Render message
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

  const renderMessage = (msg: Message, index: number) => {
    const isUser = msg.role === 'user';
    const isLastAIMessage = msg.role === 'assistant' && index === messages.length - 1;
    const displayContent = isLastAIMessage && streamingContent ? streamingContent : msg.content;
    const draft = !isUser ? tryExtractDraft(displayContent) : {};

    return (
      <div
        key={index}
        style={{
          display: 'flex',
          justifyContent: isUser ? 'flex-end' : 'flex-start',
          marginBottom: '16px',
          animation: 'fadeIn 0.3s ease-in'
        }}
      >
        <Space align="start" direction="horizontal" style={{ maxWidth: '75%', display: 'flex', flexDirection: isUser ? 'row' : 'row-reverse' }}>
          {/* Avatar */}
          <Avatar
            icon={isUser ? <UserOutlined /> : <RobotOutlined />}
            style={{
              backgroundColor: isUser ? '#1890ff' : '#52c41a',
              order: isUser ? 1 : 0
            }}
          />
          
          {/* Message Content */}
          <Card
            style={{
              backgroundColor: isUser ? '#e6f7ff' : '#f6ffed',
              borderRadius: '12px',
              border: 'none',
              boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
            }}
            bodyStyle={{ padding: '12px 16px' }}
          >
            {isUser ? (
              <Text>{displayContent}</Text>
            ) : (
              <div className="markdown-content">
                <ReactMarkdown>{displayContent}</ReactMarkdown>
                {isLastAIMessage && loading && (
                  <Spin size="small" style={{ marginLeft: '8px' }} />
                )}
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
            <div style={{ marginTop: '8px', fontSize: '12px', color: '#999' }}>
              {msg.timestamp.toLocaleTimeString()}
            </div>
          </Card>
        </Space>
      </div>
    );
  };

  return (
    <div style={{ height: 'calc(100vh - 64px)', display: 'flex', flexDirection: 'column', padding: '24px', background: '#f0f2f5' }}>
      {/* Header */}
      <Card style={{ marginBottom: '16px' }} bodyStyle={{ padding: '16px 24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Space>
            <RobotOutlined style={{ fontSize: '24px', color: '#52c41a' }} />
            <Title level={4} style={{ margin: 0 }}>AI Analysis Assistant</Title>
            <Tag color="green">Online</Tag>
          </Space>
          <Button
            icon={<PlusOutlined />}
            onClick={handleNewChat}
            disabled={loading}
          >
            New Chat
          </Button>
        </div>
      </Card>

      {/* Messages Area */}
      <Card
        style={{
          flex: 1,
          marginBottom: '16px',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column'
        }}
        bodyStyle={{
          padding: '24px',
          flex: 1,
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        {messages.length === 0 ? (
          <Empty description="No messages yet" />
        ) : (
          <div style={{ flex: 1 }}>
            {messages.map((msg, index) => renderMessage(msg, index))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </Card>

      {/* Quick Actions */}
      {messages.length <= 1 && (
        <Card style={{ marginBottom: '16px' }} bodyStyle={{ padding: '16px' }}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <Space>
              <ThunderboltOutlined style={{ color: '#faad14' }} />
              <Text strong>Quick questions:</Text>
            </Space>
            <Space wrap>
              {suggestedQuestions.map((q, index) => (
                <Tag
                  key={index}
                  style={{ cursor: 'pointer', padding: '4px 12px' }}
                  onClick={() => handleSend(q)}
                  color="blue"
                >
                  {q}
                </Tag>
              ))}
            </Space>
          </Space>
        </Card>
      )}

      {/* Input Area */}
      <Card bodyStyle={{ padding: '16px' }}>
        <Space.Compact style={{ width: '100%' }}>
          <TextArea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onPressEnter={(e) => {
              if (!e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Enter your question... (Shift+Enter for newline)"
            autoSize={{ minRows: 1, maxRows: 4 }}
            disabled={loading}
            style={{ flex: 1 }}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={() => handleSend()}
            loading={loading}
            disabled={!input.trim()}
            style={{ height: 'auto' }}
          >
            Send
          </Button>
        </Space.Compact>
        <Text type="secondary" style={{ fontSize: '12px', marginTop: '8px', display: 'block' }}>
          💡 Tip: This interface provides analysis only; it cannot execute trades or modify settings
        </Text>
      </Card>

      {/* Custom Styles */}
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .markdown-content {
          line-height: 1.6;
        }

        .markdown-content h1, .markdown-content h2, .markdown-content h3 {
          margin-top: 16px;
          margin-bottom: 8px;
        }

        .markdown-content ul, .markdown-content ol {
          margin-left: 20px;
        }

        .markdown-content code {
          background: #f5f5f5;
          padding: 2px 6px;
          border-radius: 3px;
          font-family: 'Courier New', monospace;
        }

        .markdown-content strong {
          color: #262626;
          font-weight: 600;
        }
      `}</style>
    </div>
  );
};

export default AIAssistant;


