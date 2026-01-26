import React from 'react';
import { Tag, Tooltip } from 'antd';
import { FileTextOutlined, RobotOutlined } from '@ant-design/icons';

export interface SourceBadgeProps {
    /** Origen del dato: "detectado en rfp" o "detectado por ia" */
    source?: string;
    /** Referencia del documento: "NombreArchivo, Pagina X" */
    referenceDocument?: string;
}

/**
 * Badge visual que indica el origen de la información:
 * - Azul con icono de documento: extraído del RFP
 * - Morado con icono de robot: inferido por IA
 */
export const SourceBadge: React.FC<SourceBadgeProps> = ({ source, referenceDocument }) => {
    if (!source && !referenceDocument) return null;

    const isFromDocument = source?.toLowerCase().includes('rfp') ||
        source?.toLowerCase().includes('documento');
    const isFromAI = source?.toLowerCase().includes('ia') ||
        source?.toLowerCase().includes('ai');

    // Determinar estilo según origen
    const badgeConfig = isFromDocument ? {
        color: '#1890ff',
        backgroundColor: 'rgba(24, 144, 255, 0.1)',
        icon: <FileTextOutlined />,
        label: 'RFP'
    } : isFromAI ? {
        color: '#722ed1',
        backgroundColor: 'rgba(114, 46, 209, 0.1)',
        icon: <RobotOutlined />,
        label: 'IA'
    } : {
        color: '#8c8c8c',
        backgroundColor: 'rgba(140, 140, 140, 0.1)',
        icon: <FileTextOutlined />,
        label: 'Ref'
    };

    const tooltipContent = (
        <div>
            {source && <div><strong>Origen:</strong> {source}</div>}
            {referenceDocument && <div><strong>Referencia:</strong> {referenceDocument}</div>}
        </div>
    );

    return (
        <Tooltip title={tooltipContent}>
            <Tag
                style={{
                    cursor: 'help',
                    marginLeft: 4,
                    fontSize: 10,
                    padding: '0 6px',
                    borderRadius: 10,
                    border: `1px solid ${badgeConfig.color}`,
                    color: badgeConfig.color,
                    backgroundColor: badgeConfig.backgroundColor,
                }}
            >
                {badgeConfig.icon}
                <span style={{ marginLeft: 4 }}>{badgeConfig.label}</span>
            </Tag>
        </Tooltip>
    );
};

export default SourceBadge;
