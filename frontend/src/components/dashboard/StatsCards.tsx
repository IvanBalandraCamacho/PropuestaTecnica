/**
 * Tarjetas de estadísticas del dashboard
 */
import React from 'react';
import { Row, Col, Card, Statistic, Progress } from 'antd';
import { 
  FileTextOutlined, CheckCircleOutlined, 
  CloseCircleOutlined, ClockCircleOutlined 
} from '@ant-design/icons';
import type { DashboardStats } from '../../types';

interface StatsCardsProps {
  stats: DashboardStats;
}

const StatsCards: React.FC<StatsCardsProps> = ({ stats }) => {
  return (
    <Row gutter={16}>
      <Col span={6}>
        <Card>
          <Statistic
            title="Total RFPs"
            value={stats.total_rfps}
            prefix={<FileTextOutlined />}
            valueStyle={{ color: '#1890ff' }}
          />
        </Card>
      </Col>
      <Col span={6}>
        <Card>
          <Statistic
            title="GO"
            value={stats.go_count}
            prefix={<CheckCircleOutlined />}
            valueStyle={{ color: '#52c41a' }}
          />
        </Card>
      </Col>
      <Col span={6}>
        <Card>
          <Statistic
            title="NO GO"
            value={stats.no_go_count}
            prefix={<CloseCircleOutlined />}
            valueStyle={{ color: '#ff4d4f' }}
          />
        </Card>
      </Col>
      <Col span={6}>
        <Card>
          <Statistic
            title="Pendientes"
            value={stats.pending_count + stats.analyzing_count}
            prefix={<ClockCircleOutlined />}
            valueStyle={{ color: '#faad14' }}
          />
        </Card>
      </Col>
      
      {/* GO Rate */}
      <Col span={24} style={{ marginTop: 16 }}>
        <Card size="small">
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <span>Tasa de GO:</span>
            <Progress 
              percent={stats.go_rate} 
              style={{ flex: 1, marginBottom: 0 }}
              strokeColor={{
                '0%': '#52c41a',
                '100%': '#87d068',
              }}
            />
          </div>
        </Card>
      </Col>
    </Row>
  );
};

export default StatsCards;
