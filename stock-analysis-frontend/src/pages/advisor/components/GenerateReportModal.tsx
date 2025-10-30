import React, { useState } from 'react';
import { Modal, Input, DatePicker, message } from 'antd';
import { advisorService } from '@/services/advisorService';

interface Props {
  open: boolean;
  onClose: () => void;
  clientId: number;
  onSuccess?: () => void;
}

const GenerateReportModal: React.FC<Props> = ({ open, onClose, clientId, onSuccess }) => {
  const [title, setTitle] = useState('');
  const [range, setRange] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const handleOk = async () => {
    try {
      setLoading(true);
      const payload: any = { title };
      if (range && range[0] && range[1]) {
        payload.start = range[0].toISOString();
        payload.end = range[1].toISOString();
      }
      await advisorService.generateReport(clientId, payload);
      message.success('Report generated');
      onClose();
      onSuccess?.();
    } catch (e: any) {
      message.error(e?.message || 'Failed to generate report');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      open={open}
      title="Generate Report"
      onOk={handleOk}
      confirmLoading={loading}
      onCancel={onClose}
      okText="Generate"
    >
      <Input placeholder="Title (optional)" value={title} onChange={(e) => setTitle(e.target.value)} style={{ marginBottom: 12 }} />
      <DatePicker.RangePicker onChange={(vals) => setRange(vals as any)} style={{ width: '100%' }} />
    </Modal>
  );
};

export default GenerateReportModal;


