// Mirror of backend Pydantic schemas — kept manually since we don't generate
// from OpenAPI in this MVP. Keep in sync when backend changes.

export type UserRole = "farmer" | "admin";

export type FarmType = "kfh" | "lph" | "ip" | "ooo" | "coop" | "other";
export type FarmDirection =
  | "crop"
  | "livestock"
  | "dairy"
  | "meat"
  | "poultry"
  | "beekeeping"
  | "aquaculture"
  | "mixed"
  | "other";
export type FarmerStatus = "beginning" | "operating" | "expanding";

export type DocumentType =
  | "federal_law"
  | "government_decree"
  | "ministry_order"
  | "regional_act"
  | "tax_code"
  | "methodology"
  | "other";

export type DocumentStatus =
  | "pending"
  | "parsing"
  | "chunking"
  | "embedding"
  | "indexed"
  | "failed"
  | "archived";

export type MessageRole = "user" | "assistant" | "system";
export type FeedbackKind = "positive" | "negative" | "hallucination" | "outdated";

export interface FarmerProfile {
  id: string;
  user_id: string;
  region_code: string | null;
  region_name: string | null;
  farm_type: FarmType | null;
  direction: FarmDirection | null;
  status: FarmerStatus | null;
  okved: string | null;
  years_in_business: number | null;
  inn: string | null;
  created_at: string;
  updated_at: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  profile: FarmerProfile | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface SourceInfo {
  document_id: string;
  chunk_id: string;
  title: string;
  short_title: string | null;
  doc_number: string | null;
  section_path: string | null;
  snippet: string;
  score: number;
  source_url: string | null;
}

export interface AnswerResponse {
  session_id: string;
  message_id: string;
  answer: string;
  sources: SourceInfo[];
  token_usage: Record<string, number>;
  retrieval_meta: Record<string, unknown>;
}

export interface ChatSession {
  id: string;
  user_id: string;
  title: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: MessageRole;
  content: string;
  sources: SourceInfo[];
  token_usage: Record<string, number>;
  retrieval_meta: Record<string, unknown>;
  created_at: string;
}

export interface SessionWithMessages extends ChatSession {
  messages: ChatMessage[];
}

export interface SessionList {
  items: ChatSession[];
  total: number;
}

export interface LegalDocument {
  id: string;
  title: string;
  short_title: string | null;
  doc_type: DocumentType;
  doc_number: string | null;
  doc_date: string | null;
  effective_from: string | null;
  effective_until: string | null;
  issuing_body: string | null;
  source_url: string | null;
  tags: string[];
  target_regions: string[];
  target_farm_types: string[];
  target_directions: string[];
  status: DocumentStatus;
  is_active: boolean;
  chunk_count: number;
  error_message: string | null;
  summary: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentList {
  items: LegalDocument[];
  total: number;
  limit: number;
  offset: number;
}

export const FARM_TYPE_LABELS: Record<FarmType, string> = {
  kfh: "Крестьянское (фермерское) хозяйство",
  lph: "Личное подсобное хозяйство",
  ip: "ИП — глава КФХ или сельхоз-ИП",
  ooo: "ООО / иное юридическое лицо",
  coop: "Сельскохозяйственный кооператив",
  other: "Иное",
};

export const DIRECTION_LABELS: Record<FarmDirection, string> = {
  crop: "Растениеводство",
  livestock: "Животноводство",
  dairy: "Молочное скотоводство",
  meat: "Мясное скотоводство",
  poultry: "Птицеводство",
  beekeeping: "Пчеловодство",
  aquaculture: "Аквакультура",
  mixed: "Смешанное",
  other: "Иное",
};

export const STATUS_LABELS: Record<FarmerStatus, string> = {
  beginning: "Начинающий фермер",
  operating: "Действующий",
  expanding: "Расширяющий деятельность",
};

export const DOCUMENT_TYPE_LABELS: Record<DocumentType, string> = {
  federal_law: "Федеральный закон",
  government_decree: "Постановление Правительства РФ",
  ministry_order: "Приказ Минсельхоза России",
  regional_act: "Региональный нормативный акт",
  tax_code: "Налоговый кодекс / налоговое",
  methodology: "Методические рекомендации",
  other: "Иное",
};
