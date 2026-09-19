export interface Plant {
  id: number;
  name: string;
  species: string;
  growth_stage: string;
  age_days: number;
  watering_frequency: string;
  light_condition: string;
  notes: string;
  is_demo: boolean;
  created_at: string;
  updated_at: string;
  health_status: string;
  risk_level: string | null;
  last_analysis: string | null;
  latest_condition: string | null;
  analysis_count: number;
  image_path: string | null;
}

export interface PlantInput {
  name: string;
  species: string;
  growth_stage: string;
  age_days: number;
  watering_frequency: string;
  light_condition: string;
  notes: string;
}

export interface Triple {
  source: string;
  source_name: string;
  source_type: string;
  relationship: string;
  target: string;
  target_name: string;
  target_type: string;
}

export interface Recommendation {
  title: string;
  why: string;
  source: string;
  priority?: string;
}

export interface PreventiveItem {
  title: string;
  source: string;
}

export interface Analysis {
  id: number;
  plant_id: number;
  plant_name: string | null;
  image_path: string | null;
  detected_symptoms: string[];
  predicted_condition: string;
  confidence: number;
  plant_state: Record<string, unknown> & { risk_level?: string };
  explanation: string[];
  recommendation: Recommendation[];
  preventive_care: PreventiveItem[];
  evidence: {
    identified_entities?: { entity_id: string; name: string; entity_type: string; match_reason: string }[];
    triples?: Triple[];
    documents?: { title: string; excerpt: string }[];
    runners_up?: { condition: string; score: number }[];
  };
  limitations: string[];
  model_status: string;
  reasoning_mode: string;
  llm_summary: string | null;
  is_demo: boolean;
  created_at: string;
}

export interface CareEvent {
  id: number;
  plant_id: number;
  event_type: string;
  description: string;
  date: string;
}

export interface DashboardStats {
  total_plants: number;
  total_analyses: number;
  needs_attention: number;
  healthy: number;
  monitor: number;
  new_plants: number;
  status_breakdown: Record<string, number>;
  recent_conditions: {
    analysis_id: number;
    plant_id: number;
    plant_name: string | null;
    condition: string;
    confidence: number;
    risk_level: string | null;
    created_at: string;
  }[];
}

export interface Entity {
  id: string;
  entity_type: string;
  name: string;
  description: string;
}

export interface RelationshipSet {
  entity: Entity | null;
  outgoing: Triple[];
  incoming: Triple[];
}

export interface HealthCheck {
  status: string;
  version: string;
  database: string;
  graph_backend: string;
  vision_model: string;
  llm_configured: boolean;
  reasoning_mode: string;
}
