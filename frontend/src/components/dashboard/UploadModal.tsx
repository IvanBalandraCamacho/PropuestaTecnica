/**
 * Modal para subir RFPs
 */
import React, { useState } from 'react';
import { Modal, Upload, message, Typography, Spin, Steps } from 'antd';
import { InboxOutlined, LoadingOutlined, CheckCircleOutlined, FileSearchOutlined, CloudUploadOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';
import type { RcFile } from 'antd/es/upload';
import { rfpApi } from '../../lib/api';

const { Dragger } = Upload;
const { Text, Title } = Typography;

interface UploadModalProps {
  open: boolean;
  onCancel: () => void;
  onSuccess: () => void;
}

type UploadStep = 'idle' | 'uploading' | 'analyzing' | 'complete' | 'error';

const UploadModal: React.FC<UploadModalProps> = ({ open, onCancel, onSuccess }) => {
  const [step, setStep] = useState<UploadStep>('idle');
  const [fileList, setFileList] = useState<RcFile[]>([]);
  const [errorMessage, setErrorMessage] = useState<string>('');

  const resetState = () => {
    setStep('idle');
    setFileList([]);
    setErrorMessage('');
  };

  const handleCancel = () => {
    if (step === 'uploading' || step === 'analyzing') {
      message.warning('Por favor espera a que termine el análisis');
      return;
    }
    resetState();
    onCancel();
  };

  const handleUpload = async () => {
    if (fileList.length === 0) return;

    setStep('uploading');
    setErrorMessage('');

    try {
      setTimeout(() => setStep('analyzing'), 2000);

      // Enviar todos los archivos
      await rfpApi.upload(fileList);

      setStep('complete');
      message.success('Proyecto analizado exitosamente');

      setTimeout(() => {
        resetState();
        onSuccess();
      }, 1500);

    } catch (error: any) {
      setStep('error');
      const errorMsg = error?.response?.data?.detail || error?.message || 'Error al procesar los archivos';
      setErrorMessage(errorMsg);
      message.error(errorMsg);
    }
  };

  const uploadProps: UploadProps = {
    name: 'files',
    multiple: true,
    fileList: fileList,
    accept: '.pdf,.docx,.xlsx,.xls',
    showUploadList: true,
    disabled: step !== 'idle',
    beforeUpload: (file) => {
      const isLt50M = file.size / 1024 / 1024 < 50;
      if (!isLt50M) {
        message.error(`${file.name} debe ser menor a 50MB`);
        return Upload.LIST_IGNORE;
      }
      setFileList(prev => [...prev, file as RcFile]);
      return false; // Prevent auto upload
    },
    onRemove: (file) => {
      setFileList(prev => prev.filter(f => f.uid !== file.uid));
    },
  };

  const getCurrentStep = () => {
    switch (step) {
      case 'uploading': return 0;
      case 'analyzing': return 1;
      case 'complete': return 2;
      default: return -1;
    }
  };

  const renderContent = () => {
    if (step === 'idle') {
      return (
        <div style={{ marginTop: 20 }}>
          <Dragger {...uploadProps} height={150}>
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">
              Haz clic o arrastra archivos aquí
            </p>
            <p className="ant-upload-hint">
              PDF, DOCX, Excel (Máx. 50MB c/u)
            </p>
          </Dragger>

          {fileList.length > 0 && (
            <div style={{ marginTop: 24, textAlign: 'center' }}>
              <div style={{ marginBottom: 16 }}>
                <Text type="secondary">
                  {fileList.length} archivo(s) seleccionado(s)
                </Text>
              </div>
              <button
                onClick={handleUpload}
                style={{
                  backgroundColor: '#1890ff',
                  color: 'white',
                  border: 'none',
                  padding: '10px 30px',
                  borderRadius: '6px',
                  fontSize: '16px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  boxShadow: '0 4px 12px rgba(24, 144, 255, 0.2)',
                  transition: 'all 0.3s ease'
                }}
                onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
                onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
              >
                Analizar Proyecto
              </button>
            </div>
          )}
        </div>
      );
    }

    if (step === 'error') {
      return (
        <div style={{ textAlign: 'center', padding: '40px 20px' }}>
          <div style={{ color: '#ff4d4f', fontSize: 48, marginBottom: 16 }}>
            ⚠️
          </div>
          <Title level={4} style={{ color: '#ff4d4f' }}>Error al procesar</Title>
          <Text type="secondary">{errorMessage}</Text>
          <div style={{ marginTop: 24 }}>
            <Text
              style={{ color: '#1890ff', cursor: 'pointer' }}
              onClick={resetState}
            >
              Intentar de nuevo
            </Text>
          </div>
        </div>
      );
    }

    // Estados de progreso
    return (
      <div style={{ padding: '20px 0' }}>
        <Steps
          current={getCurrentStep()}
          items={[
            {
              title: 'Subiendo',
              description: 'Cargando archivos...',
              icon: step === 'uploading' ? <LoadingOutlined /> : <CloudUploadOutlined />,
            },
            {
              title: 'Analizando',
              description: 'IA procesando contexto...',
              icon: step === 'analyzing' ? <LoadingOutlined /> : <FileSearchOutlined />,
            },
            {
              title: 'Listo',
              icon: <CheckCircleOutlined />,
            },
          ]}
        />

        <div style={{ textAlign: 'center', marginTop: 40, minHeight: 100 }}>
          {step === 'uploading' && (
            <div className="fade-in">
              <Text strong style={{ fontSize: 16 }}>Subiendo {fileList.length} archivos...</Text>
            </div>
          )}

          {step === 'analyzing' && (
            <div className="fade-in">
              <Text strong style={{ fontSize: 16, display: 'block', marginBottom: 8 }}>
                Analizando Proyecto
              </Text>
              <Text type="secondary">
                La IA está leyendo los PDFs y cruzando datos con los Excels...
              </Text>
            </div>
          )}

          {step === 'complete' && (
            <div className="fade-in">
              <Text type="success" strong style={{ fontSize: 18 }}>¡Proyecto procesado!</Text>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <Modal
      title="Nuevo Proyecto"
      open={open}
      onCancel={handleCancel}
      footer={null}
      width={600}
      closable={step === 'idle' || step === 'error' || step === 'complete'}
      maskClosable={step === 'idle' || step === 'error'}
    >
      {renderContent()}
    </Modal>
  );
};

export default UploadModal;
