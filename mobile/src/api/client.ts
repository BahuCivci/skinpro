import { z } from 'zod';

import type { AnalysisResponse, CoachResponse, ProfilePayload } from '@/types/api';

const analysisSchema = z.object({
  final_grade: z.string(),
  confidence: z.number(),
  inflamed_area_pct: z.number(),
  used: z.object({
    classifier_onnx: z.boolean(),
    classifier_hf: z.boolean(),
    heuristic: z.boolean(),
  }),
  lesions: z
    .object({
      regions: z
        .array(
          z.object({
            x: z.number(),
            y: z.number(),
            width: z.number(),
            height: z.number(),
            area_pct: z.number(),
          })
        )
        .optional(),
      texture_score: z.number().optional(),
      pore_proxy: z.number().optional(),
      detector_regions: z
        .array(
          z.object({
            label: z.string(),
            confidence: z.number(),
            bbox: z.tuple([z.number(), z.number(), z.number(), z.number()]),
            bbox_abs: z.tuple([z.number(), z.number(), z.number(), z.number()]),
            area_pct: z.number(),
            class_id: z.number(),
          })
        )
        .optional(),
      detector_overlay: z.string().optional(),
    })
    .optional(),
  meta: z.record(z.any()).optional(),
});

const coachSchema = z.object({
  plan: z.record(z.array(z.string())),
  remedies: z.array(
    z.object({
      id: z.string(),
      title: z.string(),
      summary: z.string(),
      score: z.number(),
    })
  ),
  alerts: z.array(z.string()),
  community: z.array(z.string()),
});

const API_BASE = process.env.EXPO_PUBLIC_API_BASE ?? 'http://127.0.0.1:8000';

export async function analyzePhoto(uri: string): Promise<AnalysisResponse> {
  const fileExt = uri.split('.').pop() ?? 'jpg';
  const form = new FormData();
  form.append('file', {
    uri,
    name: `photo.${fileExt}`,
    type: `image/${fileExt}`,
  } as any);

  const response = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    body: form,
    headers: {
      Accept: 'application/json',
    },
  });
  if (!response.ok) {
    throw new Error(`Analyze failed: ${response.status}`);
  }
  const json = await response.json();
  return analysisSchema.parse(json);
}

export async function requestCoach(profile: ProfilePayload, analysis: AnalysisResponse): Promise<CoachResponse> {
  const payload = {
    profile,
    analysis: {
      final_grade: analysis.final_grade,
      inflamed_area_pct: analysis.inflamed_area_pct,
      lesions: analysis.lesions ?? {},
    },
  };
  const response = await fetch(`${API_BASE}/coach`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`Coach failed: ${response.status}`);
  }
  const json = await response.json();
  return coachSchema.parse(json);
}
