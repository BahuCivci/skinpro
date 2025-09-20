import React, { createContext, useContext, useMemo, useState } from 'react';

import type { AnalysisResponse } from '@/types/api';

type AnalysisContextValue = {
  analysis: AnalysisResponse | null;
  setAnalysis: (value: AnalysisResponse | null) => void;
};

const AnalysisContext = createContext<AnalysisContextValue | undefined>(undefined);

export const AnalysisProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const value = useMemo(() => ({ analysis, setAnalysis }), [analysis]);
  return <AnalysisContext.Provider value={value}>{children}</AnalysisContext.Provider>;
};

export const useAnalysis = (): AnalysisContextValue => {
  const ctx = useContext(AnalysisContext);
  if (!ctx) {
    throw new Error('useAnalysis must be used within AnalysisProvider');
  }
  return ctx;
};
