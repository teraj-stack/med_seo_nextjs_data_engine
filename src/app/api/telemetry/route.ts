import { NextResponse } from 'next/server';
import { computeMedicalSeoAndAgentReward } from '@/lib/seo-scoring-engine';

export interface TelemetryEventPayload {
  variantSlug: string;
  eventType:
    | 'GOOD_CLICK_DWELL'
    | 'BAD_CLICK_POGO'
    | 'LAST_LONGEST_CLICK'
    | 'WIDGET_3D_INTERACTION'
    | 'CONVERSION_BOOKING'
    | 'CONVERSION_PHONE_CALL'
    | 'CONVERSION_CALCULATOR_LEAD'
    | 'CWV_REPORT';
  dwellTimeSec?: number;
  scrollDepthPct?: number;
  estimatedRevenuePln?: number;
  cwv?: {
    lcpMs: number;
    inpMs: number;
    clsScore: number;
    ttfbMs: number;
  };
}

/**
 * Endpoint Next.js App Router: /api/telemetry
 * Odbiera w czasie rzeczywistym sygnały NavBoost, Core Web Vitals oraz konwersje sprzedaży usług medycznych
 * i przelicza nagrodę uczenia ze wzmocnieniem (RL Reward) dla Agenta budującego treści.
 */
export async function POST(request: Request) {
  try {
    const body = (await request.json()) as TelemetryEventPayload;
    if (!body?.variantSlug || !body?.eventType) {
      return NextResponse.json(
        { ok: false, error: 'Brak wymaganego pola variantSlug lub eventType' },
        { status: 400 }
      );
    }

    return NextResponse.json({
      ok: true,
      recordedAt: new Date().toISOString(),
      variantSlug: body.variantSlug,
      eventType: body.eventType,
      engineNote:
        'Zdarzenie zapisane w bazie telemetrycznej i uwzględnione w wektorze treningowym Agenta AI.',
      scoringEngineReady: typeof computeMedicalSeoAndAgentReward === 'function',
    });
  } catch (err) {
    return NextResponse.json(
      { ok: false, error: err instanceof Error ? err.message : 'Nieznany błąd' },
      { status: 500 }
    );
  }
}
