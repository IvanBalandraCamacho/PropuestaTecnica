import React from 'react';
import { Modal, Button } from 'antd';
import DocViewer, { DocViewerRenderers } from "@cyntler/react-doc-viewer";
import DocxRenderer from './renderers/DocxRenderer';

interface FilePreviewModalProps {
    visible: boolean;
    onClose: () => void;
    fileUrl: string | null;
    fileName: string;
    fileType?: string;
}

const FilePreviewModal: React.FC<FilePreviewModalProps> = ({ visible, onClose, fileUrl, fileName, fileType }) => {

    if (!fileUrl) return null;

    const docs = [
        { uri: fileUrl, fileName: fileName, fileType: fileType }
    ];

    return (
        <Modal
            title={`Vista Previa: ${fileName}`}
            open={visible}
            onCancel={onClose}
            footer={[
                <a key="download" href={fileUrl || '#'} download={fileName} style={{ textDecoration: 'none' }}>
                    <Button type="primary" onClick={(e) => { if (!fileUrl) e.preventDefault(); }}>
                        Descargar
                    </Button>
                </a>,
                <Button key="close" onClick={onClose}>
                    Cerrar
                </Button>
            ]}
            width="80%"
            style={{ top: 20 }}
            bodyStyle={{ height: '80vh', padding: 0 }}
            destroyOnClose
        >
            <DocViewer
                documents={docs}
                pluginRenderers={[DocxRenderer, ...DocViewerRenderers]}
                style={{ height: '100%' }}
                config={{
                    header: {
                        disableHeader: true,
                        disableFileName: true,
                        retainURLParams: true
                    },
                    pdfVerticalScrollByDefault: true
                }}
            />
        </Modal>
    );
};

export default FilePreviewModal;
