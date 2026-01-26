/**
 * Página de detalle de RFP
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Layout, Typography, Card, Descriptions, Tag, Button, Space,
  Spin, Modal, Input, message, Row, Col, Alert, Divider, List, Tabs,
  Form, Select, DatePicker, InputNumber, Tooltip
} from 'antd';
import {
  ArrowLeftOutlined, CheckOutlined, CloseOutlined,
  ExclamationCircleOutlined, CalendarOutlined, DollarOutlined,
  GlobalOutlined, CodeOutlined, TeamOutlined, SearchOutlined, ReloadOutlined,
  EditOutlined, SaveOutlined, CloseCircleOutlined, NumberOutlined, AppstoreOutlined,
  ClockCircleOutlined, RobotOutlined, FileTextOutlined, InfoCircleOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { rfpApi } from '../lib/api';
import AppLayout from '../components/layout/AppLayout';
import { TeamEstimationView, CostEstimationView, SuggestedTeamView } from '../components/rfp';
import { CitationViewer } from '../components/common/CitationViewer';
import type { RFPStatus, Recommendation, RFPUpdate } from '../types';
import dayjs from 'dayjs';

const { Title, Text, Paragraph } = Typography;
const { Content } = Layout;
const { TextArea } = Input;

const statusColors: Record<RFPStatus, string> = {
  pending: 'default',
  analyzing: 'processing',
  analyzed: 'warning',
  go: 'success',
  no_go: 'error',
  error: 'error',
};

const statusLabels: Record<RFPStatus, string> = {
  pending: 'Pendiente',
  analyzing: 'Analizando',
  analyzed: 'Analizado',
  go: 'GO',
  no_go: 'NO GO',
  error: 'Error',
};

const recommendationColors: Record<Recommendation, string> = {
  strong_go: 'green',
  go: 'lime',
  conditional_go: 'gold',
  no_go: 'orange',
  strong_no_go: 'red',
};

const recommendationLabels: Record<Recommendation, string> = {
  strong_go: 'Muy Recomendable',
  go: 'Recomendable',
  conditional_go: 'Condicional',
  no_go: 'No Recomendable',
  strong_no_go: 'Definitivamente No',
};

const RFPDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [noGoReason, setNoGoReason] = useState('');
  const [noGoModalOpen, setNoGoModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('summary');
  const [isEditing, setIsEditing] = useState(false);
  const [pendingDecision, setPendingDecision] = useState<'go' | 'no_go' | null>(null);
  const [form] = Form.useForm();

  // RFP data
  const { data: rfp, isLoading } = useQuery({
    queryKey: ['rfp', id],
    queryFn: () => rfpApi.get(id!),
    enabled: !!id,
  });

  // Initialize form when RFP data loads
  useEffect(() => {
    if (rfp) {
      form.setFieldsValue({
        title: rfp.title,
        client_name: rfp.client_name,
        country: rfp.country,
        category: rfp.category,
        tvt: rfp.tvt,
        budget_min: rfp.budget_min,
        budget_max: rfp.budget_max,
        currency: rfp.currency,
        proposal_deadline: rfp.proposal_deadline ? dayjs(rfp.proposal_deadline) : null,
        project_duration: rfp.project_duration,
      });
    }
  }, [rfp, form]);

  // Team estimation data
  const {
    data: teamData,
    isLoading: teamDataLoading,
  } = useQuery({
    queryKey: ['rfp-team-estimation', id],
    queryFn: () => rfpApi.getTeamEstimation(id!),
    enabled: !!id && rfp?.status !== 'pending' && rfp?.status !== 'analyzing',
  });

  // Update RFP mutation
  const updateMutation = useMutation({
    mutationFn: (data: RFPUpdate) => rfpApi.update(id!, data),
    onSuccess: (data) => {
      queryClient.setQueryData(['rfp', id], data);
      message.success('Información actualizada correctamente');
      setIsEditing(false);
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Error al actualizar');
    },
  });

  // Decision mutation
  const decisionMutation = useMutation({
    mutationFn: ({ decision, reason }: { decision: 'go' | 'no_go'; reason?: string }) =>
      rfpApi.makeDecision(id!, { decision, reason }),
    onSuccess: (data) => {
      queryClient.setQueryData(['rfp', id], data);
      message.success(`Decisión registrada: ${data.decision?.toUpperCase()}`);
      setPendingDecision(null);
      if (data.decision === 'go') {
        navigate(`/rfp/${id}/questions`);
      }
    },
    onError: () => {
      message.error('Error al registrar la decisión');
      setPendingDecision(null);
    },
  });

  // Suggest team mutation
  const suggestTeamMutation = useMutation({
    mutationFn: (forceRefresh: boolean = false) => rfpApi.suggestTeam(id!, forceRefresh),
    onSuccess: (data) => {
      message.success(`Se encontraron ${data.suggested_team?.total_candidatos || 0} candidatos`);
      // Actualizar el cache directamente con los datos de la respuesta
      queryClient.setQueryData(['rfp-team-estimation', id], {
        team_estimation: data.team_estimation,
        cost_estimation: data.cost_estimation,
        suggested_team: data.suggested_team,
      });
      setActiveTab('candidates');
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Error al buscar candidatos');
    },
  });

  const handleGo = () => {
    setPendingDecision('go');
    decisionMutation.mutate({ decision: 'go' });
  };

  const handleNoGo = () => {
    setNoGoModalOpen(true);
  };

  const confirmNoGo = () => {
    setPendingDecision('no_go');
    decisionMutation.mutate({ decision: 'no_go', reason: noGoReason });
    setNoGoModalOpen(false);
    setNoGoReason('');
  };

  const handleSearchCandidates = (forceRefresh: boolean = false) => {
    suggestTeamMutation.mutate(forceRefresh);
  };

  const handleSaveEdit = async () => {
    try {
      const values = await form.validateFields();
      const updateData: RFPUpdate = {
        title: values.title,
        client_name: values.client_name,
        country: values.country,
        category: values.category,
        tvt: values.tvt,
        budget_min: values.budget_min,
        budget_max: values.budget_max,
        currency: values.currency,
        proposal_deadline: values.proposal_deadline ? values.proposal_deadline.format('YYYY-MM-DD') : null,
        project_duration: values.project_duration,
      };
      updateMutation.mutate(updateData);
    } catch (error) {
      // Validation error
    }
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    // Reset form to original values
    if (rfp) {
      form.setFieldsValue({
        title: rfp.title,
        client_name: rfp.client_name,
        country: rfp.country,
        category: rfp.category,
        tvt: rfp.tvt,
        budget_min: rfp.budget_min,
        budget_max: rfp.budget_max,
        currency: rfp.currency,
        proposal_deadline: rfp.proposal_deadline ? dayjs(rfp.proposal_deadline) : null,
        project_duration: rfp.project_duration,
      });
    }
  };

  // Validar que TVT solo tenga números
  const validateTVT = (_: unknown, value: string) => {
    if (value && !/^\d*$/.test(value)) {
      return Promise.reject('Solo se permiten números');
    }
    return Promise.resolve();
  };

  // Formatear categoría a título (Ej: desarrollo_software -> Desarrollo Software)
  const formatCategory = (category: string | null | undefined): string => {
    if (!category) return '-';
    return category
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (char) => char.toUpperCase());
  };



  if (isLoading) {
    return (
      <AppLayout>
        <Content style={{ padding: 24, textAlign: 'center' }}>
          <Spin size="large" />
        </Content>
      </AppLayout>
    );
  }

  if (!rfp) {
    return (
      <AppLayout>
        <Content style={{ padding: 24 }}>
          <Alert type="error" message="RFP no encontrado" />
        </Content>
      </AppLayout>
    );
  }

  const extracted = rfp.extracted_data;

  // Tab items configuration
  const tabItems = [
    {
      key: 'summary',
      label: (
        <span>
          <GlobalOutlined style={{ marginRight: 6 }} />
          Resumen
        </span>
      ),
      children: (
        <Row gutter={24}>
          {/* Main Info */}
          <Col span={16}>
            <Card
              title="Información del RFP"
              style={{ marginBottom: 24 }}
              extra={
                !isEditing ? (
                  <Button
                    icon={<EditOutlined />}
                    onClick={() => setIsEditing(true)}
                  >
                    Editar
                  </Button>
                ) : (
                  <Space>
                    <Button
                      icon={<CloseCircleOutlined />}
                      onClick={handleCancelEdit}
                    >
                      Cancelar
                    </Button>
                    <Button
                      type="primary"
                      icon={<SaveOutlined />}
                      onClick={handleSaveEdit}
                      loading={updateMutation.isPending}
                    >
                      Guardar
                    </Button>
                  </Space>
                )
              }
            >
              {!isEditing ? (
                <>
                  <Descriptions column={2}>
                    <Descriptions.Item label={<><FileTextOutlined style={{ marginRight: 4 }} /> Nombre del Proyecto</>} span={2}>
                      {rfp.title || '-'}
                    </Descriptions.Item>
                    <Descriptions.Item label={<><GlobalOutlined style={{ marginRight: 4 }} /> País</>}>
                      {rfp.country || '-'}
                    </Descriptions.Item>
                    <Descriptions.Item label={<><AppstoreOutlined style={{ marginRight: 4 }} /> Categoría</>}>
                      {formatCategory(rfp.category)}
                    </Descriptions.Item>
                    <Descriptions.Item label={<><NumberOutlined style={{ marginRight: 4 }} /> TVT</>}>
                      {rfp.tvt || '-'}
                    </Descriptions.Item>
                    <Descriptions.Item label={<><DollarOutlined style={{ marginRight: 4 }} /> Presupuesto</>}>
                      {rfp.budget_min || rfp.budget_max ? (
                        `${rfp.currency} ${rfp.budget_min?.toLocaleString() || '?'} - ${rfp.budget_max?.toLocaleString() || '?'}`
                      ) : '-'}
                    </Descriptions.Item>
                    <Descriptions.Item label={<><CalendarOutlined style={{ marginRight: 4 }} /> Deadline Propuesta</>}>
                      {rfp.proposal_deadline ? dayjs(rfp.proposal_deadline).format('DD/MM/YYYY') : '-'}
                    </Descriptions.Item>
                    <Descriptions.Item label={<><ClockCircleOutlined style={{ marginRight: 4 }} /> Duración Proyecto</>}>
                      <CitationViewer text={rfp.project_duration || '-'} files={rfp.files} />
                    </Descriptions.Item>
                    <Descriptions.Item label={<><RobotOutlined style={{ marginRight: 4 }} /> Confianza IA</>}>
                      {rfp.confidence_score ? `${rfp.confidence_score}%` : '-'}
                    </Descriptions.Item>
                  </Descriptions>
                </>
              ) : (
                <Form form={form} layout="vertical">
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item label="Nombre del Proyecto" name="title">
                        <Input placeholder="Nombre o título del proyecto" />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item label="Cliente" name="client_name">
                        <Input placeholder="Nombre del cliente" />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item label="País" name="country">
                        <Input placeholder="País" />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item label="Categoría" name="category">
                        <Select placeholder="Seleccione categoría">
                          <Select.Option value="desarrollo_software">Desarrollo Software</Select.Option>
                          <Select.Option value="mantencion_aplicaciones">Mantención App</Select.Option>
                          <Select.Option value="analitica">Analítica y Datos</Select.Option>
                          <Select.Option value="ia_chatbot">IA & Chatbots</Select.Option>
                          <Select.Option value="ia_documentos">IA Documental</Select.Option>
                          <Select.Option value="ia_video">IA Video</Select.Option>
                          <Select.Option value="otro">Otro</Select.Option>
                        </Select>
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item
                        label="TVT"
                        name="tvt"
                        rules={[{ validator: validateTVT }]}
                        tooltip="Solo números. Puede iniciar con 0."
                      >
                        <Input placeholder="Ej: 15.000 (sin puntos)" />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item label="Presupuesto Mín" name="budget_min">
                        <InputNumber
                          style={{ width: '100%' }}
                          placeholder="Mínimo"
                          formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')} parser={value => value!.replace(/\$\s?|(,*)/g, '')}
                        />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item label="Presupuesto Máx" name="budget_max">
                        <InputNumber
                          style={{ width: '100%' }}
                          placeholder="Máximo"
                          formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')} parser={value => value!.replace(/\$\s?|(,*)/g, '')}
                        />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item label="Moneda" name="currency">
                        <Select placeholder="Moneda">
                          <Select.Option value="USD">USD</Select.Option>
                          <Select.Option value="CLP">CLP</Select.Option>
                          <Select.Option value="UF">UF</Select.Option>
                          <Select.Option value="BRL">BRL</Select.Option>
                          <Select.Option value="MXN">MXN</Select.Option>
                        </Select>
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item label="Deadline Propuesta" name="proposal_deadline">
                        <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item label="Duración Proyecto" name="project_duration">
                        <Input placeholder="Ej: 12 meses" />
                      </Form.Item>
                    </Col>
                  </Row>
                </Form>
              )}

              {rfp.summary && (
                <>
                  <Divider />
                  <Title level={5}>Resumen</Title>
                  <Paragraph><CitationViewer text={rfp.summary} files={rfp.files} /></Paragraph>
                </>
              )}

              {extracted?.budget?.notes && (
                <>
                  <Divider />
                  <Title level={5}>Notas de Presupuesto</Title>
                  <Paragraph><CitationViewer text={extracted.budget.notes} files={rfp.files} /></Paragraph>
                </>
              )}
            </Card>

            {/* Tech Stack */}
            {extracted?.tech_stack && extracted.tech_stack.length > 0 && (
              <Card title={<><CodeOutlined /> Stack Tecnológico</>} style={{ marginBottom: 24 }}>
                <Space wrap>
                  {extracted.tech_stack.map((tech, i) => (
                    <Tag key={i} color="blue"><CitationViewer text={tech} files={rfp.files} /></Tag>
                  ))}
                </Space>
              </Card>
            )}

            {/* Risks */}
            {extracted?.risks && extracted.risks.length > 0 && (
              <Card
                title={<><ExclamationCircleOutlined style={{ marginRight: 6 }} /> Riesgos Identificados</>}
                style={{ marginBottom: 24 }}
              >
                <List
                  dataSource={extracted.risks}
                  renderItem={(risk) => {
                    const severityLabels: Record<string, string> = {
                      critical: 'CRÍTICO',
                      high: 'ALTO',
                      medium: 'MEDIO',
                      low: 'BAJO'
                    };
                    return (
                      <List.Item>
                        <List.Item.Meta
                          avatar={
                            <Tag color={
                              risk.severity === 'critical' ? 'red' :
                                risk.severity === 'high' ? 'orange' :
                                  risk.severity === 'medium' ? 'gold' : 'default'
                            } style={{ minWidth: 70, textAlign: 'center' }}>
                              {severityLabels[risk.severity] || risk.severity.toUpperCase()}
                            </Tag>
                          }
                          title={
                            <Space align="center" style={{ width: '100%', justifyContent: 'space-between' }}>
                              <Text strong>{risk.category.replace(/_/g, ' ').toUpperCase()}</Text>
                              {risk.reference_document && (
                                <Tooltip title="Referencia en el documento original">
                                  <Tag icon={<FileTextOutlined />} color="default">
                                    {risk.reference_document}
                                  </Tag>
                                </Tooltip>
                              )}
                            </Space>
                          }
                          description={risk.description}
                        />
                      </List.Item>
                    );
                  }}
                />
              </Card>
            )}
          </Col>

          {/* Sidebar */}
          <Col span={8}>


            {/* Recommendation Reasons */}
            {extracted?.recommendation_reasons && extracted.recommendation_reasons.length > 0 && (
              <Card title="Razones de la Recomendación" style={{ marginBottom: 24 }}>
                <List
                  size="small"
                  dataSource={extracted.recommendation_reasons}
                  renderItem={(reason) => (
                    <List.Item>
                      <CitationViewer text={reason} files={rfp.files} />
                    </List.Item>
                  )}
                />
              </Card>
            )}

            {/* SLAs */}
            {
              extracted?.sla && extracted.sla.length > 0 && (
                <Card title="SLAs" style={{ marginBottom: 24 }}>
                  <List
                    size="small"
                    dataSource={extracted.sla}
                    renderItem={(sla) => (
                      <List.Item>
                        <Space direction="vertical" size={4} style={{ width: '100%' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div style={{ flex: 1 }}>
                              <CitationViewer text={sla.description} files={rfp.files} />
                            </div>

                            {/* Premium Reference UI - Minimal "Bolita" */}
                            {sla.reference_document && (
                              <Tooltip
                                title={
                                  <Space direction="vertical" size={0}>
                                    <Text style={{ color: 'white', fontSize: 12 }}>Fuente detectada:</Text>
                                    <Text style={{ color: 'white', fontWeight: 600 }}>{sla.reference_document}</Text>
                                  </Space>
                                }
                                color="blue"
                              >
                                <div
                                  style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    width: 24,
                                    height: 24,
                                    borderRadius: '50%',
                                    // Use standard colors or transparency
                                    background: 'rgba(24, 144, 255, 0.15)',
                                    color: '#1890ff',
                                    cursor: 'pointer',
                                    marginLeft: 12,
                                    flexShrink: 0,
                                    transition: 'all 0.3s ease'
                                  }}
                                  onMouseOver={(e) => {
                                    e.currentTarget.style.background = '#1890ff';
                                    e.currentTarget.style.color = '#fff';
                                  }}
                                  onMouseOut={(e) => {
                                    e.currentTarget.style.background = 'rgba(24, 144, 255, 0.15)';
                                    e.currentTarget.style.color = '#1890ff';
                                  }}
                                >
                                  <InfoCircleOutlined style={{ fontSize: 14 }} />
                                </div>
                              </Tooltip>
                            )}
                          </div>

                          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                            {sla.source === 'detectado por ia' && (
                              <Tag color="purple" style={{ fontSize: 11, margin: 0 }}>
                                <RobotOutlined style={{ marginRight: 4 }} /> IA
                              </Tag>
                            )}
                            {sla.source === 'detectado en rfp' && (
                              <Tag color="cyan" style={{ fontSize: 11, margin: 0 }}>
                                <FileTextOutlined style={{ marginRight: 4 }} /> RFP
                              </Tag>
                            )}
                            {sla.is_aggressive && (
                              <Tag color="red" style={{ fontSize: 11, margin: 0 }}>Agresivo</Tag>
                            )}
                            {sla.metric && (
                              <Text type="secondary" style={{ fontSize: 12 }}>
                                | Métrica: {sla.metric}
                              </Text>
                            )}
                          </div>
                        </Space>
                      </List.Item>
                    )}
                  />
                </Card>
              )
            }

            {/* Penalties */}
            {
              extracted?.penalties && extracted.penalties.length > 0 && (
                <Card title="Penalidades" style={{ marginBottom: 24 }}>
                  <List
                    size="small"
                    dataSource={extracted.penalties}
                    renderItem={(penalty) => (
                      <List.Item>
                        <Space direction="vertical" size={0}>
                          <div><CitationViewer text={penalty.description} files={rfp.files} /></div>
                          {penalty.amount && <Text type="secondary">{penalty.amount}</Text>}
                          {penalty.is_high && <Tag color="red">Alta</Tag>}
                        </Space>
                      </List.Item>
                    )}
                  />
                </Card>
              )
            }

            {/* Decision Info */}
            {
              rfp.decision && (
                <Card title="Decisión Registrada">
                  <Tag color={rfp.decision === 'go' ? 'success' : 'error'} style={{ fontSize: 16, padding: '4px 12px' }}>
                    {rfp.decision.toUpperCase()}
                  </Tag>
                  {rfp.decision_reason && (
                    <Paragraph style={{ marginTop: 12 }}>
                      <Text strong>Razón:</Text> {rfp.decision_reason}
                    </Paragraph>
                  )}
                  {rfp.decided_at && (
                    <Text type="secondary">
                      {dayjs(rfp.decided_at).format('DD/MM/YYYY HH:mm')}
                    </Text>
                  )}
                </Card>
              )
            }
          </Col >
        </Row >
      ),
    },
    {
      key: 'team',
      label: (
        <span>
          <TeamOutlined style={{ marginRight: 6 }} />
          Equipo Estimado
        </span>
      ),
      children: (
        <TeamEstimationView
          teamEstimation={teamData?.team_estimation || null}
          loading={teamDataLoading}
          files={rfp.files}
        />
      ),
    },
    {
      key: 'costs',
      label: (
        <span>
          <DollarOutlined style={{ marginRight: 6 }} />
          Costos
        </span>
      ),
      children: (
        <CostEstimationView
          costEstimation={teamData?.cost_estimation || null}
          loading={teamDataLoading}
        />
      ),
    },
    {
      key: 'candidates',
      label: (
        <span>
          <SearchOutlined style={{ marginRight: 6 }} />
          Candidatos TIVIT
        </span>
      ),
      children: (
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {/* Search Candidates Button */}
          <Card size="small">
            <Space>
              <Button
                type="primary"
                icon={<SearchOutlined />}
                onClick={() => handleSearchCandidates(false)}
                loading={suggestTeamMutation.isPending}
                disabled={!teamData?.team_estimation}
              >
                Buscar Candidatos
              </Button>
              {teamData?.suggested_team && (
                <Button
                  icon={<ReloadOutlined />}
                  onClick={() => handleSearchCandidates(true)}
                  loading={suggestTeamMutation.isPending}
                >
                  Actualizar
                </Button>
              )}
              {!teamData?.team_estimation && (
                <Text type="secondary">
                  Se requiere una estimación de equipo para buscar candidatos
                </Text>
              )}
            </Space>
          </Card>

          <SuggestedTeamView
            suggestedTeam={teamData?.suggested_team || null}
            loading={suggestTeamMutation.isPending}
          />
        </Space>
      ),
    },
  ];

  return (
    <AppLayout>
      <Content style={{ padding: 24 }}>
        {/* Header */}
        <div style={{ marginBottom: 24 }}>
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/')}
            style={{ marginBottom: 16 }}
          >
            Volver
          </Button>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <Title level={2} style={{ margin: 0 }}>
                {rfp.client_name || rfp.file_name}
              </Title>
              <Space style={{ marginTop: 8 }}>
                <Tag color={statusColors[rfp.status]}>{statusLabels[rfp.status]}</Tag>
                {rfp.recommendation && (
                  <Tag color={recommendationColors[rfp.recommendation]}>
                    IA: {recommendationLabels[rfp.recommendation]}
                  </Tag>
                )}
              </Space>
            </div>

            {/* Decision Buttons */}
            {rfp.status === 'analyzed' && !rfp.decision && (
              <Space size="large">
                <Button
                  type="primary"
                  size="large"
                  icon={<CheckOutlined />}
                  onClick={handleGo}
                  loading={decisionMutation.isPending && pendingDecision === 'go'}
                  disabled={decisionMutation.isPending && pendingDecision === 'no_go'}
                  style={{ background: '#52c41a', borderColor: '#52c41a' }}
                >
                  GO
                </Button>
                <Button
                  danger
                  size="large"
                  icon={<CloseOutlined />}
                  onClick={handleNoGo}
                  loading={decisionMutation.isPending && pendingDecision === 'no_go'}
                  disabled={decisionMutation.isPending && pendingDecision === 'go'}
                >
                  NO GO
                </Button>
              </Space>
            )}

            {rfp.decision === 'go' && (
              <Button
                type="primary"
                onClick={() => navigate(`/rfp/${id}/questions`)}
              >
                Ver Preguntas
              </Button>
            )}
          </div>
        </div>

        {/* Tabs */}
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
          size="large"
        />

        {/* NO GO Modal */}
        <Modal
          title="Confirmar NO GO"
          open={noGoModalOpen}
          onOk={confirmNoGo}
          onCancel={() => setNoGoModalOpen(false)}
          okText="Confirmar NO GO"
          okButtonProps={{ danger: true }}
        >
          <p>¿Estás seguro de marcar este RFP como NO GO?</p>
          <TextArea
            placeholder="Razón del NO GO (opcional)"
            value={noGoReason}
            onChange={(e) => setNoGoReason(e.target.value)}
            rows={4}
          />
        </Modal>
      </Content>
    </AppLayout>
  );
};

export default RFPDetailPage;
