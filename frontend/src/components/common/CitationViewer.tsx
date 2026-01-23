import { Tag, Tooltip, Typography } from 'antd';
import { FileTextOutlined } from '@ant-design/icons';
import type { RFPFile } from '../../types';

const { Text } = Typography;

interface CitationViewerProps {
    text: string;
    files: RFPFile[] | undefined;
}

/**
 * Parsea el texto buscando citas del formato [Fuente: doc_X, Página Y] o [Source: doc_X, Page Y]
 * y las convierte en elementos interactivos.
 */
export const CitationViewer: React.FC<CitationViewerProps> = ({ text, files }) => {
    if (!text) return null;

    // Regex para capturar [Fuente: ... ] o [Source: ... ]
    // Captura grupos: 1=Etiqueta(Fuente/Source), 2=Contenido(doc_X, Pagina Y)
    const citationRegex = /\[(Fuente|Source):\s*([^\]]+)\]/g;

    const parts = text.split(citationRegex);

    if (parts.length === 1) {
        return <Text>{text}</Text>;
    }

    const elements: React.ReactNode[] = [];
    let lastIndex = 0;

    // Reset regex
    citationRegex.lastIndex = 0;

    let match;
    while ((match = citationRegex.exec(text)) !== null) {
        const fullMatch = match[0];
        const startIndex = match.index;
        const content = match[2]; // Ej: "doc_4, Página 24" or "Anexos.pdf, Pg 10"

        // Agregar texto previo
        if (startIndex > lastIndex) {
            elements.push(<span key={`text-${lastIndex}`}>{text.substring(lastIndex, startIndex)}</span>);
        }

        // Procesar la cita
        // Intentar extraer el ID del doc (ej: doc_4)
        const docIdMatch = content.match(/doc_(\d+)/i);
        let fileInfo: RFPFile | undefined;
        let fileIndex = -1;

        if (docIdMatch && files) {
            fileIndex = parseInt(docIdMatch[1], 10) - 1; // doc_1 -> index 0
            if (fileIndex >= 0 && fileIndex < files.length) {
                fileInfo = files[fileIndex];
            }
        }

        if (fileInfo) {
            elements.push(
                <Tooltip
                    key={`cit-${startIndex}`}
                    title={
                        <div>
                            <div><strong>Archivo:</strong> {fileInfo.filename}</div>
                            <div>{content}</div>
                            <div style={{ fontSize: '10px', marginTop: 4 }}>Haz clic para descargar</div>
                        </div>
                    }
                >
                    <Tag
                        color="blue"
                        style={{ cursor: 'pointer', marginLeft: 4, marginRight: 4 }}
                        onClick={(e) => {
                            e.stopPropagation();
                            // TODO: Implementar visualizador o descarga directa
                            // Por ahora, usamos una descarga simulada si tuviéramos la URL, 
                            // pero como tenemos el file_gcs_path, necesitamos el endpoint de descarga.
                            // Disparamos un evento o usamos una función de descarga si se pasa como prop.
                            console.log('Open file:', fileInfo);
                        }}
                    >
                        <FileTextOutlined style={{ marginRight: 4 }} />
                        {content.trim()}
                    </Tag>
                </Tooltip>
            );
        } else {
            // Fallback si no encontramos el archivo o el formato no es doc_X
            elements.push(
                <Tag key={`cit-${startIndex}`} style={{ marginLeft: 4, marginRight: 4 }}>
                    {fullMatch}
                </Tag>
            );
        }

        lastIndex = startIndex + fullMatch.length;
    }

    // Agregar texto restante
    if (lastIndex < text.length) {
        elements.push(<span key={`text-${lastIndex}`}>{text.substring(lastIndex)}</span>);
    }

    return <span>{elements}</span>;
};
