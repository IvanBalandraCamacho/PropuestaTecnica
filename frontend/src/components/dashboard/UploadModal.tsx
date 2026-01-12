/**
 * Modal para subir RFPs
 */
import React, { useState } from 'react';
import { Modal, Upload, message, Typography, Spin, Steps } from 'antd';
import { InboxOutlined, LoadingOutlined, CheckCircleOutlined, FileSearchOutlined, CloudUploadOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';
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
  const [fileName, setFileName] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string>('');

  const resetState = () => {
    setStep('idle');
    setFileName('');
    setErrorMessage('');
  };

  const handleCancel = () => {
    if (step === 'uploading' || step === 'analyzing') {
      // No permitir cerrar durante el proceso
      message.warning('Por favor espera a que termine el análisis');
      return;
    }
    resetState();
    onCancel();
  };

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,
    accept: '.pdf,.docx',
    showUploadList: false,
    disabled: step !== 'idle',
    beforeUpload: async (file) => {
      // Validar tamaño (max 50MB)
      const isLt50M = file.size / 1024 / 1024 < 50;
      if (!isLt50M) {
        message.error('El archivo debe ser menor a 50MB');
        return false;
      }

      setFileName(file.name);
      setStep('uploading');
      setErrorMessage('');

      try {
        // Cambiar a analyzing después de un momento
        setTimeout(() => setStep('analyzing'), 1000);

        // El endpoint ahora es síncrono - espera al análisis
        await rfpApi.upload(file);
        
        setStep('complete');
        message.success('RFP analizado exitosamente');
        
        // Esperar un momento para mostrar el estado de éxito
        setTimeout(() => {
          resetState();
          onSuccess();
        }, 1500);
        
      } catch (error: any) {
        setStep('error');
        const errorMsg = error?.response?.data?.detail || error?.message || 'Error al procesar el archivo';
        setErrorMessage(errorMsg);
        message.error(errorMsg);
      }

      return false; // Prevenir upload automático
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
        <Dragger {...uploadProps}>
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">
            Haz clic o arrastra un archivo aquí
          </p>
          <p className="ant-upload-hint">
            Soporta archivos PDF y DOCX (máx. 50MB)
          </p>
        </Dragger>
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
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <Text strong style={{ fontSize: 16 }}>{fileName}</Text>
        </div>
        
        <Steps
          current={getCurrentStep()}
          items={[
            {
              title: 'Subiendo',
              icon: step === 'uploading' ? <LoadingOutlined /> : <CloudUploadOutlined />,
            },
            {
              title: 'Analizando con IA',
              icon: step === 'analyzing' ? <LoadingOutlined /> : <FileSearchOutlined />,
            },
            {
              title: 'Completado',
              icon: <CheckCircleOutlined />,
            },
          ]}
        />
        
        <div style={{ textAlign: 'center', marginTop: 32 }}>
          {step === 'uploading' && (
            <>
              <Spin size="large" />
              <div style={{ marginTop: 16 }}>
                <Text type="secondary">Subiendo archivo...</Text>
              </div>
            </>
          )}
          
          {step === 'analyzing' && (
            <>
              <Spin 
                size="large" 
                indicator={<LoadingOutlined style={{ fontSize: 48 }} spin />} 
              />
              <div style={{ marginTop: 16 }}>
                <Text type="secondary">
                  Analizando documento con Gemini...
                </Text>
                <br />
                <Text type="secondary" style={{ fontSize: 12 }}>
                  Esto puede tomar entre 30 segundos y 2 minutos
                </Text>
              </div>
            </>
          )}
          
          {step === 'complete' && (
            <>
              <CheckCircleOutlined style={{ fontSize: 48, color: '#52c41a' }} />
              <div style={{ marginTop: 16 }}>
                <Text type="success" strong>¡Análisis completado!</Text>
              </div>
            </>
          )}
        </div>
      </div>
    );
  };

  return (
    <Modal
      title="Subir RFP"
      open={open}
      onCancel={handleCancel}
      footer={null}
      width={500}
      closable={step === 'idle' || step === 'error' || step === 'complete'}
      maskClosable={step === 'idle' || step === 'error'}
    >
      {renderContent()}
    </Modal>
  );
};

export default UploadModal;
