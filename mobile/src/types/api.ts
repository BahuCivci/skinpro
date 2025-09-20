export type DetectorRegion = {
  label: string;
  confidence: number;
  bbox: [number, number, number, number];
  bbox_abs: [number, number, number, number];
  area_pct: number;
  class_id: number;
};

export type LesionReport = {
  regions?: Array<{ x: number; y: number; width: number; height: number; area_pct: number }>;
  texture_score?: number;
  pore_proxy?: number;
  detector_regions?: DetectorRegion[];
  detector_overlay?: string; // base64 PNG
};

export type AnalysisResponse = {
  final_grade: string;
  confidence: number;
  inflamed_area_pct: number;
  used: {
    classifier_onnx: boolean;
    classifier_hf: boolean;
    heuristic: boolean;
  };
  meta?: Record<string, unknown>;
  lesions?: LesionReport;
};

export type CoachResponse = {
  plan: Record<string, string[]>;
  remedies: Array<{ id: string; title: string; summary: string; score: number }>;
  alerts: string[];
  community: string[];
};

export type ProfilePayload = {
  diet: string;
  stress: string;
  sleep_hours: number;
  hydration: string;
  hormonal: string;
  skincare: string[];
};
