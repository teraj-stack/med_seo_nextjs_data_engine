export interface MedicalContentVariantInput {
  slug: string;
  serviceCategory: string;
  procedureName: string;
  contentFormat:
    | 'INTERACTIVE_3D_PROCEDURE_MODEL'
    | 'TRANSPARENT_PRICING_CALCULATOR'
    | 'DOCTOR_QA_CASE_STUDY_BEFORE_AFTER'
    | 'SPATIAL_3D_CLINIC_TOUR_AND_CHECKLIST'
    | 'GENERIC_TEXT_BLOG_POST';
  headlineHookType: string;
  authorName: string;
  authorPwzVerified: boolean;
  clinicalCitationsCount: number;
  originalMediaCount: number;
  effortScore: number;
  aioPassageWordCount: number;
  schemaJsonLdTypes: string[];
  entityDensityScore: number;
  clickDepthFromHome: number;
  siteFocusAlignment: number;
  siteRadiusDeviation: number;
}

export interface NavBoostConversionMetrics {
  impressionsCount: number;
  totalClicks: number;
  goodClicks: number;
  badClicks: number;
  lastLongestClicks: number;
  avgDwellTimeSec: number;
  avgScrollDepthPct: number;
  interactiveWidgetUses: number;
  bookingsCompleted: number;
  phoneClickCalls: number;
  calculatorLeads: number;
  estimatedRevenuePln: number;
}

export interface CoreWebVitalsMetrics {
  lcpMs: number;
  inpMs: number;
  clsScore: number;
  ttfbMs: number;
}

export interface ComputedAgentReward {
  compositeSeoScore: number;
  salesEffectivenessScore: number;
  agentRewardSignal: number;
  conversionRatePct: number;
  navboostSatisfactionRatio: number;
}

/**
 * Oblicza złożony wynik pozycjonowania Google Search (NavBoost + E-E-A-T + GEO/AIO + CWV + QualityBoost)
 * oraz sygnał nagrody Reinforcement Learning (Contextual Bandit) dla Agenta AI budującego treści medyczne.
 */
export function computeMedicalSeoAndAgentReward(
  variant: MedicalContentVariantInput,
  nav: NavBoostConversionMetrics,
  cwv: CoreWebVitalsMetrics
): ComputedAgentReward {
  const totalClicks = Math.max(nav.totalClicks, 1);
  const satRatio = nav.goodClicks / Math.max(nav.goodClicks + nav.badClicks, 1);
  const llcRatio = nav.lastLongestClicks / totalClicks;
  const dwellNorm = Math.min(nav.avgDwellTimeSec / 180.0, 1.0);
  const navboostScore = satRatio * 50.0 + llcRatio * 30.0 + dwellNorm * 20.0;

  // 2. E-E-A-T & YMYL Score
  const pwzBonus = variant.authorPwzVerified ? 25.0 : 0.0;
  const citationsNorm = Math.min(variant.clinicalCitationsCount / 6.0, 1.0) * 20.0;
  const mediaNorm = Math.min(variant.originalMediaCount / 8.0, 1.0) * 20.0;
  const effortNorm = (variant.effortScore / 100.0) * 35.0;
  const eeatScore = pwzBonus + citationsNorm + mediaNorm + effortNorm;

  // 3. AI Overviews / GEO Score (130-170 słów w bloku semantycznym pod H2)
  const wc = variant.aioPassageWordCount;
  const passageScore = wc >= 130 && wc <= 170 ? 40.0 : wc >= 110 && wc <= 195 ? 25.0 : 10.0;
  const schemaScore = Math.min(variant.schemaJsonLdTypes.length / 4.0, 1.0) * 30.0;
  const entityScore = (variant.entityDensityScore / 100.0) * 30.0;
  const geoScore = passageScore + schemaScore + entityScore;

  // 4. Core Web Vitals (CWV)
  const lcpOk = cwv.lcpMs <= 2500 ? 40.0 : cwv.lcpMs <= 4000 ? 20.0 : 0.0;
  const inpOk = cwv.inpMs <= 200 ? 35.0 : cwv.inpMs <= 500 ? 15.0 : 0.0;
  const clsOk = cwv.clsScore <= 0.1 ? 25.0 : cwv.clsScore <= 0.25 ? 10.0 : 0.0;
  const cwvScore = lcpOk + inpOk + clsOk;

  // 5. Architektura domeny (PageRank_NS & siteFocusScore)
  const depthScore =
    variant.clickDepthFromHome === 1 ? 40.0 : variant.clickDepthFromHome === 2 ? 25.0 : 5.0;
  const focusScore = variant.siteFocusAlignment * 40.0;
  const radiusScore = Math.max(0.0, (1.0 - variant.siteRadiusDeviation) * 20.0);
  const domainScore = depthScore + focusScore + radiusScore;

  const compositeSeoScore =
    navboostScore * 0.35 +
    eeatScore * 0.25 +
    geoScore * 0.2 +
    cwvScore * 0.1 +
    domainScore * 0.1;

  // Skuteczność sprzedaży usług medycznych
  const totalLeads = nav.bookingsCompleted + nav.phoneClickCalls + nav.calculatorLeads;
  const conversionRatePct = (totalLeads / totalClicks) * 100.0;
  const widgetRatePct = (nav.interactiveWidgetUses / totalClicks) * 100.0;
  const salesEffectivenessScore = Math.min(100.0, conversionRatePct * 6.2 + widgetRatePct * 0.75);

  // Nagroda RL dla Agenta AI (60% sprzedaż usług medycznych + 40% parametry Google Search)
  const agentRewardSignal = Number(
    ((salesEffectivenessScore * 0.6 + compositeSeoScore * 0.4) / 100.0).toFixed(4)
  );

  return {
    compositeSeoScore: Number(compositeSeoScore.toFixed(2)),
    salesEffectivenessScore: Number(salesEffectivenessScore.toFixed(2)),
    agentRewardSignal,
    conversionRatePct: Number(conversionRatePct.toFixed(2)),
    navboostSatisfactionRatio: Number((satRatio * 100.0).toFixed(2)),
  };
}
