-- =============================================================================
-- MED-SEO & CONVERSION INTELLIGENCE DATABASE SCHEMA (Next.js + AI Content Agent)
-- Uwzględnia parametry:
--   1. NavBoost / Craps (goodClicks, badClicks, lastLongestClicks, dwellTime)
--   2. QualityBoost & PageRank_NS (siteAuthority, siteFocusScore, siteRadius, clickDepth)
--   3. E-E-A-T / YMYL (authorEntity, originalContentScore, effortScore, clinicalRefs)
--   4. Core Web Vitals (LCP <= 2500ms, INP <= 200ms, CLS <= 0.10)
--   5. AI Overviews / GEO (passageWordCount 130-170, Schema.org JSON-LD, entityDensity)
--   6. Sprzedaż usług medycznych (Conversion Rate, CTA Type, Revenue PLN, Agent Reward)
-- =============================================================================

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- 1. Tabela wariantów treści medycznych (jednostki eksperymentalne dla Agenta AI)
CREATE TABLE IF NOT EXISTS medical_content_variants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    service_category TEXT NOT NULL,          -- np. 'Proktologia Laserowa', 'Medycyna Estetyczna', 'Diagnostyka 3D'
    procedure_name TEXT NOT NULL,            -- np. 'Laserowe leczenie hemoroidów LHP', 'EMS RF Sculpt'
    content_format TEXT NOT NULL,            -- np. 'INTERACTIVE_3D_SIMULATOR', 'DOCTOR_QA_CASE_STUDY', 'PRICE_CALCULATOR_COMPARISON', 'PATIENT_TIMELINE_VIDEO'
    headline_hook_type TEXT NOT NULL,        -- np. 'EMPATHY_PAIN_FREE', 'CLINICAL_EFFICACY_DATA', 'DIRECT_QUESTION_AIO', 'FAST_RECOVERY_TIMELINE'
    
    -- Parametry E-E-A-T & YMYL
    author_name TEXT NOT NULL,               -- np. 'dr n. med. Jan Bujok'
    author_pwz_verified INTEGER DEFAULT 1,   -- Weryfikacja prawa wykonywania zawodu / encji autora w Knowledge Graph
    clinical_citations_count INTEGER DEFAULT 0,
    original_media_count INTEGER DEFAULT 0,  -- Liczba autorskich zdjęć / modeli 3D / wideo (nie-stockowych)
    effort_score REAL DEFAULT 0.0,           -- 0.0 - 100.0 (kalkulatory, modele 3D, tabele, unikalne dane)
    original_content_score REAL DEFAULT 0.0, -- 0.0 - 100.0
    
    -- Parametry AI Overviews (GEO) & Semantyka
    aio_passage_word_count INTEGER DEFAULT 150, -- Optymalnie 130-170 słów w bloku odpowiedzi pod H2
    schema_jsonld_types TEXT NOT NULL,       -- np. '["MedicalClinic","Physician","MedicalProcedure","FAQPage"]'
    entity_density_score REAL DEFAULT 0.0,   -- Nasycenie encjami medycznymi (ICD-10, nazwy anatomiczne, technologie)
    
    -- Parametry architektury domeny (QualityBoost / PageRank_NS)
    click_depth_from_home INTEGER DEFAULT 1, -- Odległość w kliknięciach od strony głównej (optymalnie 1-2)
    site_focus_alignment REAL DEFAULT 0.95,  -- Zgodność z głównym tematem domeny (siteFocusScore: 0.0 - 1.0)
    site_radius_deviation REAL DEFAULT 0.05, -- Odchylenie od rdzenia tematycznego (siteRadius: im mniej tym lepiej)
    
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- 2. Tabela sygnałów behawioralnych NavBoost & Konwersji Sprzedażowej (zbierana na bieżąco z Next.js)
CREATE TABLE IF NOT EXISTS navboost_conversion_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    variant_id INTEGER NOT NULL REFERENCES medical_content_variants(id) ON DELETE CASCADE,
    recorded_date TEXT DEFAULT (date('now')),
    
    -- Sygnały NavBoost / SERP & On-Page Behavior
    impressions_count INTEGER DEFAULT 0,
    total_clicks INTEGER DEFAULT 0,
    good_clicks INTEGER DEFAULT 0,           -- Użytkownik pozostał >45s lub wykonał interakcję bez szybkiego powrotu
    bad_clicks INTEGER DEFAULT 0,            -- Pogo-sticking: powrót do Google <12s
    last_longest_clicks INTEGER DEFAULT 0,   -- Sesje zakończone na tej podstronie (spełniona intencja)
    avg_dwell_time_sec REAL DEFAULT 0.0,     -- Średni czas zaangażowania na stronie
    avg_scroll_depth_pct REAL DEFAULT 0.0,   -- Głębokość przewinięcia strony (%)
    interactive_widget_uses INTEGER DEFAULT 0, -- Użycia modelu 3D / kalkulatora kosztów / suwaka przed-po
    
    -- Wyniki sprzedaży usług medycznych (Conversion Intelligence)
    bookings_completed INTEGER DEFAULT 0,    -- Umówione wizyty / zabiegi online
    phone_click_calls INTEGER DEFAULT 0,     -- Kliknięcia w numer telefonu (Recepcja)
    calculator_leads INTEGER DEFAULT 0,      -- Wypełnione wyceny zabiegu
    estimated_revenue_pln REAL DEFAULT 0.0,  -- Przychód wygenerowany przez dany wariant treści (PLN)
    
    -- Wyliczane wskaźniki efektywności
    conversion_rate_pct REAL DEFAULT 0.0,    -- (bookings + phone_calls) / total_clicks * 100
    navboost_satisfaction_ratio REAL DEFAULT 0.0 -- good_clicks / (good_clicks + bad_clicks)
);

-- 3. Tabela parametrów technicznych Core Web Vitals (CWV)
CREATE TABLE IF NOT EXISTS cwv_technical_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    variant_id INTEGER NOT NULL REFERENCES medical_content_variants(id) ON DELETE CASCADE,
    lcp_ms INTEGER NOT NULL,                 -- Largest Contentful Paint (cel <= 2500 ms)
    inp_ms INTEGER NOT NULL,                 -- Interaction to Next Paint (cel <= 200 ms)
    cls_score REAL NOT NULL,                 -- Cumulative Layout Shift (cel <= 0.10)
    ttfb_ms INTEGER NOT NULL,                -- Time to First Byte (cel <= 400 ms)
    cwv_passed INTEGER DEFAULT 1,            -- 1 jeśli spełnia wszystkie 3 progi Google
    measured_at TEXT DEFAULT (datetime('now'))
);

-- 4. Tabela treningowa dla Agenta AI budującego treści (Reinforcement Learning / Contextual Bandit)
CREATE TABLE IF NOT EXISTS agent_learning_dataset (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    variant_id INTEGER NOT NULL REFERENCES medical_content_variants(id) ON DELETE CASCADE,
    composite_seo_score REAL NOT NULL,       -- Złożony wynik Google Ranking (NavBoost + E-E-A-T + CWV + GEO) 0-100
    sales_effectiveness_score REAL NOT NULL, -- Wynik skuteczności sprzedaży usług medycznych 0-100
    agent_reward_signal REAL NOT NULL,       -- Łączna nagroda RL dla Agenta (0.0 - 1.0)
    winning_pattern_summary TEXT NOT NULL,   -- Wnioski wyekstrahowane dla promptu systemowego Agenta
    recommended_action TEXT NOT NULL,        -- np. 'SCALE_FORMAT', 'OPTIMIZE_AIO_PASSAGE', 'REWRITE_HOOK_REDUCE_BAD_CLICKS'
    evaluated_at TEXT DEFAULT (datetime('now'))
);

