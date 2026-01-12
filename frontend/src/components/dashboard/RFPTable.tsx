/**
 * Tabla de RFPs
 */
import React from 'react';
import { Table, Tag, Button, Space, Tooltip } from 'antd';
import { EyeOutlined, CalendarOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table';
import type { RFPSummary, RFPStatus, Recommendation } from '../../types';
import dayjs from 'dayjs';

interface RFPTableProps {
  data: RFPSummary[];
  pagination: TablePaginationConfig;
}

const statusConfig: Record<RFPStatus, { color: string; label: string }> = {
  pending: { color: 'default', label: 'Pendiente' },
  analyzing: { color: 'processing', label: 'Analizando' },
  analyzed: { color: 'warning', label: 'Analizado' },
  go: { color: 'success', label: 'GO' },
  no_go: { color: 'error', label: 'NO GO' },
  error: { color: 'error', label: 'Error' },
};

const recommendationConfig: Record<Recommendation, { color: string; label: string }> = {
  strong_go: { color: 'green', label: 'Muy Recomendable' },
  go: { color: 'lime', label: 'Recomendable' },
  conditional_go: { color: 'gold', label: 'Condicional' },
  no_go: { color: 'orange', label: 'No Recomendable' },
  strong_no_go: { color: 'red', label: 'No Participar' },
};

const RFPTable: React.FC<RFPTableProps> = ({ data, pagination }) => {
  const navigate = useNavigate();

  const columns: ColumnsType<RFPSummary> = [
    {
      title: 'Cliente',
      dataIndex: 'client_name',
      key: 'client_name',
      render: (text, record) => (
        <Button type="link" onClick={() => navigate(`/rfp/${record.id}`)}>
          {text || record.file_name}
        </Button>
      ),
    },
    {
      title: 'País',
      dataIndex: 'country',
      key: 'country',
      width: 100,
      render: (text) => text || '-',
    },
    {
      title: 'Categoría',
      dataIndex: 'category',
      key: 'category',
      width: 160,
      render: (text) => text ? (
        <Tag>{text.replace(/_/g, ' ')}</Tag>
      ) : '-',
    },
    {
      title: 'Presupuesto',
      key: 'budget',
      width: 150,
      render: (_, record) => {
        if (!record.budget_min && !record.budget_max) return '-';
        return `${record.currency} ${(record.budget_min || record.budget_max)?.toLocaleString()}`;
      },
    },
    {
      title: 'Deadline',
      dataIndex: 'proposal_deadline',
      key: 'proposal_deadline',
      width: 120,
      render: (date) => date ? (
        <Tooltip title={dayjs(date).format('DD/MM/YYYY')}>
          <Space>
            <CalendarOutlined />
            {dayjs(date).format('DD/MM')}
          </Space>
        </Tooltip>
      ) : '-',
    },
    {
      title: 'Recomendación',
      dataIndex: 'recommendation',
      key: 'recommendation',
      width: 140,
      render: (rec: Recommendation | null) => rec ? (
        <Tag color={recommendationConfig[rec].color}>
          {recommendationConfig[rec].label}
        </Tag>
      ) : '-',
    },
    {
      title: 'Estado',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: RFPStatus) => (
        <Tag color={statusConfig[status].color}>
          {statusConfig[status].label}
        </Tag>
      ),
    },
    {
      title: 'Fecha',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 100,
      render: (date) => dayjs(date).format('DD/MM/YY'),
    },
    {
      title: 'Acciones',
      key: 'actions',
      width: 80,
      fixed: 'right',
      render: (_, record) => (
        <Button
          type="text"
          icon={<EyeOutlined />}
          onClick={() => navigate(`/rfp/${record.id}`)}
        />
      ),
    },
  ];

  return (
    <Table
      columns={columns}
      dataSource={data}
      rowKey="id"
      pagination={pagination}
      scroll={{ x: 1200 }}
      size="middle"
    />
  );
};

export default RFPTable;
