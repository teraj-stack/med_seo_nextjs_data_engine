'use client';

import React, { useState, useTransition } from 'react';
import {
  computeMedicalSeoAndAgentReward,
  type MedicalContentVariantInput,
  type NavBoostConversionMetrics,
  type CoreWebVitalsMetrics,
} from '@/lib/seo-scoring-engine';

interface VariantRecord {
  id: number;
  variant: MedicalContentVariantInput;
  nav: NavBoostConversionMetrics;
  cwv: CoreWebVitalsMetrics;
  winningPattern: string;
}

const INITIAL_VARIANTS: VariantRecord[] = [
  {
    id: 1,
    variant: {
      slug: 'laserowe-leczenie-hemoroidow-model-3d-przebieg',
      serviceCategory: 'Proktologia Laserowa',
      procedureName: 'Laserowa plastyka hemoroidów LHP (1470 nm)',
      contentFormat: 'INTERACTIVE_3D_PROCEDURE_MODEL',
      headlineHookType: 'EMPATHY_DISCREET_PAIN_FREE',
      authorName: 'dr n. med. Jan Bujok (Chirurg / Proktolog)',
      authorPwzVerified: true,
      clinicalCitationsCount: 7,
      originalMediaCount: 11,
      effortScore: 96,
      aioPassageWordCount: 154,
      schemaJsonLdTypes: ['MedicalClinic', 'Physician', 'MedicalProcedure', 'FAQPage', 'VideoObject'],
      entityDensityScore: 94,
      clickDepthFromHome: 1,
      siteFocusAlignment: 0.98,
      siteRadiusDeviation: 0.03,
    },
    nav: {
      impressionsCount: 14800,
      totalClicks: 1920,
      goodClicks: 1765,
      badClicks: 82,
      lastLongestClicks: 1340,
      avgDwellTimeSec: 248,
      avgScrollDepthPct: 86.5,
      interactiveWidgetUses: 1190,
      bookingsCompleted: 148,
      phoneClickCalls: 94,
      calculatorLeads: 76,
      estimatedRevenuePln: 412000,
    },
    cwv: { lcpMs: 1420, inpMs: 68, clsScore: 0.02, ttfbMs: 180 },
    winningPattern:
      'Interaktywny model 3D przebiegu zabiegu + dyskretny ton empatyczny + pasaż 154 słów pod H2 z autoryzacją lekarza PWZ eliminuje lęk pacjenta i generuje najwyższy lastLongestClicks (69.8%).',
  },
  {
    id: 2,
    variant: {
      slug: 'kalkulator-kosztow-i-porownanie-metod-proktologia',
      serviceCategory: 'Proktologia Laserowa',
      procedureName: 'Kwalifikacja i zabieg laserowy vs metoda klasyczna',
      contentFormat: 'TRANSPARENT_PRICING_CALCULATOR',
      headlineHookType: 'FAST_RECOVERY_TIMELINE_ROI',
      authorName: 'dr n. med. Jan Bujok (Chirurg / Proktolog)',
      authorPwzVerified: true,
      clinicalCitationsCount: 5,
      originalMediaCount: 8,
      effortScore: 92,
      aioPassageWordCount: 146,
      schemaJsonLdTypes: ['MedicalClinic', 'MedicalProcedure', 'FAQPage', 'OfferCatalog'],
      entityDensityScore: 89,
      clickDepthFromHome: 1,
      siteFocusAlignment: 0.96,
      siteRadiusDeviation: 0.05,
    },
    nav: {
      impressionsCount: 11200,
      totalClicks: 1540,
      goodClicks: 1390,
      badClicks: 95,
      lastLongestClicks: 1020,
      avgDwellTimeSec: 215,
      avgScrollDepthPct: 82.0,
      interactiveWidgetUses: 1080,
      bookingsCompleted: 119,
      phoneClickCalls: 81,
      calculatorLeads: 112,
      estimatedRevenuePln: 338000,
    },
    cwv: { lcpMs: 1310, inpMs: 54, clsScore: 0.01, ttfbMs: 165 },
    winningPattern:
      'Tabela porównawcza czasu rekonwalescencji (1 dzień vs 4 tygodnie) + przejrzysty kalkulator kosztów daje najwyższą konwersję formularza wyceny (20.26%).',
  },
];

export default function MedSeoAgentDatabasePage() {
  const [records, setRecords] = useState<VariantRecord[]>(INITIAL_VARIANTS);
  const [isPending, startTransition] = useTransition();

  const handleSimulateConversion = (id: number, type: 'BOOKING' | 'BAD_CLICK') => {
    startTransition(() => {
      setRecords((prev) =>
        prev.map((item) => {
          if (item.id !== id) return item;
          if (type === 'BOOKING') {
            return {
              ...item,
              nav: {
                ...item.nav,
                totalClicks: item.nav.totalClicks + 1,
                goodClicks: item.nav.goodClicks + 1,
                lastLongestClicks: item.nav.lastLongestClicks + 1,
                interactiveWidgetUses: item.nav.interactiveWidgetUses + 1,
                bookingsCompleted: item.nav.bookingsCompleted + 1,
                estimatedRevenuePln: item.nav.estimatedRevenuePln + 2800,
              },
            };
          }
          return {
            ...item,
            nav: {
              ...item.nav,
              totalClicks: item.nav.totalClicks + 1,
              badClicks: item.nav.badClicks + 1,
            },
          };
        })
      );
    });
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-8">
      <header className="max-w-7xl mx-auto mb-8 border-b border-cyan-500/20 pb-6">
        <span className="inline-block px-3 py-1 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-300 border border-cyan-400/30 mb-3">
          NEXT.JS 15 • GOOGLE CONTENT WAREHOUSE + NAVBOOST + E-E-A-T + GEO ENGINE
        </span>
        <p role="note">ARCHIWALNA DEMONSTRACJA — dane syntetyczne, brak pomiaru Google i brak treningu AI. Korzystaj z głównej aplikacji BM Clinic.</p>
        <h1 className="text-3xl font-bold tracking-tight">
          Baza Danych Efektywności Treści Medycznych &amp; Trener Agenta AI
        </h1>
        <p className="text-slate-400 mt-2">
          Zbieranie na bieżąco parametrów NavBoost, Core Web Vitals, E-E-A-T oraz konwersji sprzedaży usług medycznych.
        </p>
      </header>

      <section className="max-w-7xl mx-auto grid gap-6">
        {records.map((rec) => {
          const reward = computeMedicalSeoAndAgentReward(rec.variant, rec.nav, rec.cwv);
          return (
            <article
              key={rec.id}
              className="rounded-2xl border border-white/15 bg-white/5 backdrop-blur-xl p-6 shadow-2xl"
            >
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <span className="text-xs font-mono uppercase text-cyan-400">
                    {rec.variant.contentFormat} • {rec.variant.serviceCategory}
                  </span>
                  <h2 className="text-xl font-semibold mt-1">{rec.variant.procedureName}</h2>
                  <p className="text-xs text-slate-400 mt-1">
                    Autor (E-E-A-T): {rec.variant.authorName} | Pasaż AIO: {rec.variant.aioPassageWordCount} słów
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <div className="text-xs text-slate-400">Nagroda Agenta AI (RL Reward)</div>
                    <div className="text-2xl font-bold text-lime-400">{reward.agentRewardSignal}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-slate-400">Konwersja Sprzedaży</div>
                    <div className="text-2xl font-bold text-cyan-300">{reward.conversionRatePct}%</div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-slate-400">Wynik Google SEO</div>
                    <div className="text-2xl font-bold text-white">{reward.compositeSeoScore}/100</div>
                  </div>
                </div>
              </div>

              <p className="mt-4 text-sm text-slate-300 bg-slate-900/60 p-3 rounded-xl border border-white/10">
                <strong>Wniosek dla Agenta AI:</strong> {rec.winningPattern}
              </p>

              <div className="mt-4 flex flex-wrap gap-3">
                <button
                  type="button"
                  disabled={isPending}
                  onClick={() => handleSimulateConversion(rec.id, 'BOOKING')}
                  className="px-4 py-2 rounded-xl bg-cyan-500/20 border border-cyan-400/40 text-cyan-200 text-xs font-semibold hover:bg-cyan-500/30"
                >
                  + Zarejestruj wizytę pacjenta (goodClick + lastLongestClick +2800 PLN)
                </button>
                <button
                  type="button"
                  disabled={isPending}
                  onClick={() => handleSimulateConversion(rec.id, 'BAD_CLICK')}
                  className="px-4 py-2 rounded-xl bg-rose-500/20 border border-rose-400/40 text-rose-200 text-xs font-semibold hover:bg-rose-500/30"
                >
                  + Symuluj szybkie cofnięcie (badClick / pogo-sticking)
                </button>
              </div>
            </article>
          );
        })}
      </section>
    </main>
  );
}

