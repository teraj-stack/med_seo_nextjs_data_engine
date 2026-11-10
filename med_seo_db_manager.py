#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MED-SEO & CONVERSION INTELLIGENCE ENGINE (SQLite + Next.js Data Layer + AI Agent Trainer)
Tworzy bazę danych SQLite, oblicza parametry Google Search (NavBoost, E-E-A-T, CWV, GEO/AIO,
siteAuthority/siteFocusScore) oraz trenuje ranking skuteczności typów treści w sprzedaży usług medycznych.
"""

import os
import json
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "db")
DB_PATH = os.path.join(DB_DIR, "med_seo_intelligence.sqlite")
SCHEMA_PATH = os.path.join(DB_DIR, "schema.sql")
PUBLIC_DIR = os.path.join(BASE_DIR, "public")


def compute_scores(variant, nav, cwv):
    """
    Wylicza:
    1. Wynik SEO Google Search (0-100) na podstawie:
       - NavBoost (goodClicks vs badClicks, lastLongestClicks, dwell time) [35% wagi]
       - E-E-A-T / YMYL (autor PWZ, cytowania kliniczne, original_media, effort_score) [25% wagi]
       - AI Overviews / GEO (długość pasażu 130-170 słów, Schema.org JSON-LD, entity_density) [20% wagi]
       - Core Web Vitals (LCP <= 2500ms, INP <= 200ms, CLS <= 0.10) [10% wagi]
       - Architektura domeny (click_depth <= 2, site_focus_alignment, site_radius) [10% wagi]
    2. Wynik skuteczności sprzedaży usług medycznych (0-100)
    3. Sygnał nagrody RL dla Agenta AI (0.000 - 1.000)
    """
    # 1. NavBoost Score (0-100)
    good = nav["good_clicks"]
    bad = nav["bad_clicks"]
    total_c = max(nav["total_clicks"], 1)
    sat_ratio = good / max(good + bad, 1)
    llc_ratio = nav["last_longest_clicks"] / total_c
    dwell_norm = min(nav["avg_dwell_time_sec"] / 180.0, 1.0)
    navboost_score = (sat_ratio * 50.0) + (llc_ratio * 30.0) + (dwell_norm * 20.0)

    # 2. E-E-A-T / YMYL Score (0-100)
    pwz_bonus = 25.0 if variant["author_pwz_verified"] else 0.0
    citations_norm = min(variant["clinical_citations_count"] / 6.0, 1.0) * 20.0
    media_norm = min(variant["original_media_count"] / 8.0, 1.0) * 20.0
    effort_norm = (variant["effort_score"] / 100.0) * 35.0
    eeat_score = pwz_bonus + citations_norm + media_norm + effort_norm

    # 3. AI Overviews / GEO Score (0-100)
    wc = variant["aio_passage_word_count"]
    if 130 <= wc <= 170:
        passage_score = 40.0
    elif 110 <= wc <= 195:
        passage_score = 25.0
    else:
        passage_score = 10.0
    schemas = json.loads(variant["schema_jsonld_types"])
    schema_score = min(len(schemas) / 4.0, 1.0) * 30.0
    entity_score = (variant["entity_density_score"] / 100.0) * 30.0
    geo_score = passage_score + schema_score + entity_score

    # 4. Core Web Vitals Score (0-100)
    lcp_ok = 40.0 if cwv["lcp_ms"] <= 2500 else (20.0 if cwv["lcp_ms"] <= 4000 else 0.0)
    inp_ok = 35.0 if cwv["inp_ms"] <= 200 else (15.0 if cwv["inp_ms"] <= 500 else 0.0)
    cls_ok = 25.0 if cwv["cls_score"] <= 0.10 else (10.0 if cwv["cls_score"] <= 0.25 else 0.0)
    cwv_score = lcp_ok + inp_ok + cls_ok

    # 5. Domain Architecture / QualityBoost (0-100)
    depth_score = 40.0 if variant["click_depth_from_home"] == 1 else (25.0 if variant["click_depth_from_home"] == 2 else 5.0)
    focus_score = variant["site_focus_alignment"] * 40.0
    radius_score = max(0.0, (1.0 - variant["site_radius_deviation"]) * 20.0)
    domain_score = depth_score + focus_score + radius_score

    composite_seo = (
        navboost_score * 0.35
        + eeat_score * 0.25
        + geo_score * 0.20
        + cwv_score * 0.10
        + domain_score * 0.10
    )

    # Wynik skuteczności sprzedaży usług medycznych (Conversion Rate + Widget Engagement + Przychód)
    leads = nav["bookings_completed"] + nav["phone_click_calls"] + nav["calculator_leads"]
    conv_rate = (leads / total_c) * 100.0
    widget_rate = (nav["interactive_widget_uses"] / total_c) * 100.0
    sales_score = min(100.0, (conv_rate * 6.2) + (widget_rate * 0.75))

    # Sygnał nagrody RL dla Agenta AI (60% skuteczność sprzedaży + 40% utrzymanie pozycji Google SEO)
    reward = round(((sales_score * 0.60) + (composite_seo * 0.40)) / 100.0, 4)

    return {
        "composite_seo_score": round(composite_seo, 2),
        "sales_effectiveness_score": round(sales_score, 2),
        "agent_reward_signal": reward,
        "conversion_rate_pct": round(conv_rate, 2),
        "navboost_satisfaction_ratio": round(sat_ratio * 100.0, 2),
    }


def init_and_seed_db():
    os.makedirs(DB_DIR, exist_ok=True)
    os.makedirs(PUBLIC_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        cur.executescript(f.read())

    # Never replace existing rows during a demo seed run.
    if cur.execute("SELECT COUNT(*) FROM medical_content_variants").fetchone()[0]:
        conn.close()
        print("[OK] Existing data preserved; demo seed skipped.")
        return

    seed_variants = [
        {
            "slug": "laserowe-leczenie-hemoroidow-model-3d-przebieg",
            "service_category": "Proktologia Laserowa",
            "procedure_name": "Laserowa plastyka hemoroidów LHP (1470 nm)",
            "content_format": "INTERACTIVE_3D_PROCEDURE_MODEL",
            "headline_hook_type": "EMPATHY_DISCREET_PAIN_FREE",
            "author_name": "dr n. med. Jan Bujok (Chirurg / Proktolog)",
            "author_pwz_verified": 1,
            "clinical_citations_count": 7,
            "original_media_count": 11,
            "effort_score": 96.0,
            "original_content_score": 98.0,
            "aio_passage_word_count": 154,
            "schema_jsonld_types": json.dumps(["MedicalClinic", "Physician", "MedicalProcedure", "FAQPage", "VideoObject"]),
            "entity_density_score": 94.0,
            "click_depth_from_home": 1,
            "site_focus_alignment": 0.98,
            "site_radius_deviation": 0.03,
            "nav": {
                "impressions_count": 14800,
                "total_clicks": 1920,
                "good_clicks": 1765,
                "bad_clicks": 82,
                "last_longest_clicks": 1340,
                "avg_dwell_time_sec": 248.0,
                "avg_scroll_depth_pct": 86.5,
                "interactive_widget_uses": 1190,
                "bookings_completed": 148,
                "phone_click_calls": 94,
                "calculator_leads": 76,
                "estimated_revenue_pln": 412000.0,
            },
            "cwv": {"lcp_ms": 1420, "inp_ms": 68, "cls_score": 0.02, "ttfb_ms": 180},
            "winning_pattern": "Interaktywny model 3D przebiegu zabiegu + dyskretny ton empatyczny + bezpośredni blok odpowiedzi 154 słów pod H2 z autoryzacją lekarza PWZ eliminuje lęk pacjenta i generuje najwyższy lastLongestClicks (69.8%).",
            "action": "SCALE_FORMAT_PRIMARY",
        },
        {
            "slug": "kalkulator-kosztow-i-porownanie-metod-proktologia",
            "service_category": "Proktologia Laserowa",
            "procedure_name": "Kwalifikacja i zabieg laserowy vs metoda klasyczna",
            "content_format": "TRANSPARENT_PRICING_CALCULATOR",
            "headline_hook_type": "FAST_RECOVERY_TIMELINE_ROI",
            "author_name": "dr n. med. Jan Bujok (Chirurg / Proktolog)",
            "author_pwz_verified": 1,
            "clinical_citations_count": 5,
            "original_media_count": 8,
            "effort_score": 92.0,
            "original_content_score": 94.0,
            "aio_passage_word_count": 146,
            "schema_jsonld_types": json.dumps(["MedicalClinic", "MedicalProcedure", "FAQPage", "OfferCatalog"]),
            "entity_density_score": 89.0,
            "click_depth_from_home": 1,
            "site_focus_alignment": 0.96,
            "site_radius_deviation": 0.05,
            "nav": {
                "impressions_count": 11200,
                "total_clicks": 1540,
                "good_clicks": 1390,
                "bad_clicks": 95,
                "last_longest_clicks": 1020,
                "avg_dwell_time_sec": 215.0,
                "avg_scroll_depth_pct": 82.0,
                "interactive_widget_uses": 1080,
                "bookings_completed": 119,
                "phone_click_calls": 81,
                "calculator_leads": 112,
                "estimated_revenue_pln": 338000.0,
            },
            "cwv": {"lcp_ms": 1310, "inp_ms": 54, "cls_score": 0.01, "ttfb_ms": 165},
            "winning_pattern": "Interaktywna tabela porównawcza czasu rekonwalescencji (1 dzień vs 4 tygodnie) + przejrzysty kalkulator rat i ceny zabiegu daje najwyższą konwersję formularza wyceny.",
            "action": "SCALE_FORMAT_SECONDARY",
        },
        {
            "slug": "ems-rf-sculpt-badania-kliniczne-efekty-przed-po",
            "service_category": "Medycyna Estetyczna & Hi-Tech",
            "procedure_name": "Modelowanie sylwetki EMS EMT RF Sculpt",
            "content_format": "DOCTOR_QA_CASE_STUDY_BEFORE_AFTER",
            "headline_hook_type": "CLINICAL_EFFICACY_DATA",
            "author_name": "Zespół Medyczny BM Clinics (Weryfikacja Kliniczna)",
            "author_pwz_verified": 1,
            "clinical_citations_count": 6,
            "original_media_count": 14,
            "effort_score": 88.0,
            "original_content_score": 91.0,
            "aio_passage_word_count": 162,
            "schema_jsonld_types": json.dumps(["MedicalClinic", "MedicalProcedure", "FAQPage", "ImageGallery"]),
            "entity_density_score": 87.0,
            "click_depth_from_home": 1,
            "site_focus_alignment": 0.92,
            "site_radius_deviation": 0.08,
            "nav": {
                "impressions_count": 9600,
                "total_clicks": 1210,
                "good_clicks": 1045,
                "bad_clicks": 110,
                "last_longest_clicks": 740,
                "avg_dwell_time_sec": 184.0,
                "avg_scroll_depth_pct": 78.0,
                "interactive_widget_uses": 690,
                "bookings_completed": 78,
                "phone_click_calls": 49,
                "calculator_leads": 44,
                "estimated_revenue_pln": 196000.0,
            },
            "cwv": {"lcp_ms": 1780, "inp_ms": 92, "cls_score": 0.04, "ttfb_ms": 210},
            "winning_pattern": "Suwak autorskich zdjęć Przed/Po z parametrami energii RF + sekcja Q&A obalająca mity przyciąga ruch z AI Overviews.",
            "action": "KEEP_AND_EXPAND_FAQ",
        },
        {
            "slug": "wirtualny-spacer-3d-przygotowanie-do-wizyty-w-klinice",
            "service_category": "Nawigacja Przestrzenna & Komfort Pacjenta",
            "procedure_name": "Pierwsza wizyta proktologiczna — dyskrecja i nawigacja 3D",
            "content_format": "SPATIAL_3D_CLINIC_TOUR_AND_CHECKLIST",
            "headline_hook_type": "EMPATHY_ZERO_STRESS_ONBOARDING",
            "author_name": "dr n. med. Jan Bujok (Chirurg / Proktolog)",
            "author_pwz_verified": 1,
            "clinical_citations_count": 3,
            "original_media_count": 9,
            "effort_score": 94.0,
            "original_content_score": 95.0,
            "aio_passage_word_count": 148,
            "schema_jsonld_types": json.dumps(["MedicalClinic", "Physician", "FAQPage", "Place"]),
            "entity_density_score": 84.0,
            "click_depth_from_home": 2,
            "site_focus_alignment": 0.95,
            "site_radius_deviation": 0.05,
            "nav": {
                "impressions_count": 6400,
                "total_clicks": 890,
                "good_clicks": 812,
                "bad_clicks": 41,
                "last_longest_clicks": 615,
                "avg_dwell_time_sec": 262.0,
                "avg_scroll_depth_pct": 91.0,
                "interactive_widget_uses": 580,
                "bookings_completed": 71,
                "phone_click_calls": 52,
                "calculator_leads": 19,
                "estimated_revenue_pln": 178000.0,
            },
            "cwv": {"lcp_ms": 1890, "inp_ms": 115, "cls_score": 0.03, "ttfb_ms": 195},
            "winning_pattern": "Wirtualny podgląd gabinetu i prywatnego wejścia obniża barierę wstydu pacjenta o 64% i generuje najdłuższy czas sesji (262s).",
            "action": "EMBED_IN_ALL_PROCEDURE_PAGES",
        },
        {
            "slug": "ogolny-artykul-blogowy-co-to-sa-hemoroidy",
            "service_category": "Blog Ogólny (Test Kontrolny)",
            "procedure_name": "Ogólny artykuł informacyjny bez interakcji i bez ceny",
            "content_format": "GENERIC_TEXT_BLOG_POST",
            "headline_hook_type": "GENERIC_DEFINITION_TITLE",
            "author_name": "Redakcja (Brak encji lekarza)",
            "author_pwz_verified": 0,
            "clinical_citations_count": 0,
            "original_media_count": 0,
            "effort_score": 22.0,
            "original_content_score": 31.0,
            "aio_passage_word_count": 310,
            "schema_jsonld_types": json.dumps(["Article"]),
            "entity_density_score": 38.0,
            "click_depth_from_home": 3,
            "site_focus_alignment": 0.65,
            "site_radius_deviation": 0.35,
            "nav": {
                "impressions_count": 8200,
                "total_clicks": 410,
                "good_clicks": 115,
                "bad_clicks": 265,
                "last_longest_clicks": 42,
                "avg_dwell_time_sec": 29.0,
                "avg_scroll_depth_pct": 31.0,
                "interactive_widget_uses": 0,
                "bookings_completed": 3,
                "phone_click_calls": 4,
                "calculator_leads": 0,
                "estimated_revenue_pln": 4200.0,
            },
            "cwv": {"lcp_ms": 3450, "inp_ms": 280, "cls_score": 0.19, "ttfb_ms": 520},
            "winning_pattern": "NEGATYWNY WZORZEC (Kontrolny): Brak weryfikacji lekarza PWZ, brak interaktywnego kalkulatora/3D i zbyt długi pasaż (310 słów) powodują 69% badClicks (pogo-sticking) i śladową sprzedaż (1.7%).",
            "action": "DEPRECATE_AND_REWRITE_BY_AGENT",
        },
    ]

    exported_rows = []

    for item in seed_variants:
        cur.execute(
            """
            INSERT INTO medical_content_variants (
                slug, service_category, procedure_name, content_format, headline_hook_type,
                author_name, author_pwz_verified, clinical_citations_count, original_media_count,
                effort_score, original_content_score, aio_passage_word_count, schema_jsonld_types,
                entity_density_score, click_depth_from_home, site_focus_alignment, site_radius_deviation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item["slug"], item["service_category"], item["procedure_name"],
                item["content_format"], item["headline_hook_type"], item["author_name"],
                item["author_pwz_verified"], item["clinical_citations_count"],
                item["original_media_count"], item["effort_score"], item["original_content_score"],
                item["aio_passage_word_count"], item["schema_jsonld_types"],
                item["entity_density_score"], item["click_depth_from_home"],
                item["site_focus_alignment"], item["site_radius_deviation"]
            ),
        )
        vid = cur.lastrowid
        nav = item["nav"]
        cwv = item["cwv"]
        scores = compute_scores(item, nav, cwv)

        cur.execute(
            """
            INSERT INTO navboost_conversion_metrics (
                variant_id, impressions_count, total_clicks, good_clicks, bad_clicks,
                last_longest_clicks, avg_dwell_time_sec, avg_scroll_depth_pct,
                interactive_widget_uses, bookings_completed, phone_click_calls,
                calculator_leads, estimated_revenue_pln, conversion_rate_pct,
                navboost_satisfaction_ratio
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                vid, nav["impressions_count"], nav["total_clicks"], nav["good_clicks"],
                nav["bad_clicks"], nav["last_longest_clicks"], nav["avg_dwell_time_sec"],
                nav["avg_scroll_depth_pct"], nav["interactive_widget_uses"],
                nav["bookings_completed"], nav["phone_click_calls"], nav["calculator_leads"],
                nav["estimated_revenue_pln"], scores["conversion_rate_pct"],
                scores["navboost_satisfaction_ratio"]
            ),
        )

        cwv_passed = 1 if (cwv["lcp_ms"] <= 2500 and cwv["inp_ms"] <= 200 and cwv["cls_score"] <= 0.10) else 0
        cur.execute(
            """
            INSERT INTO cwv_technical_metrics (
                variant_id, lcp_ms, inp_ms, cls_score, ttfb_ms, cwv_passed
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (vid, cwv["lcp_ms"], cwv["inp_ms"], cwv["cls_score"], cwv["ttfb_ms"], cwv_passed),
        )

        cur.execute(
            """
            INSERT INTO agent_learning_dataset (
                variant_id, composite_seo_score, sales_effectiveness_score,
                agent_reward_signal, winning_pattern_summary, recommended_action
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                vid, scores["composite_seo_score"], scores["sales_effectiveness_score"],
                scores["agent_reward_signal"], item["winning_pattern"], item["action"]
            ),
        )

        exported_rows.append({
            "id": vid,
            "slug": item["slug"],
            "service_category": item["service_category"],
            "procedure_name": item["procedure_name"],
            "content_format": item["content_format"],
            "headline_hook_type": item["headline_hook_type"],
            "author_name": item["author_name"],
            "author_pwz_verified": bool(item["author_pwz_verified"]),
            "clinical_citations_count": item["clinical_citations_count"],
            "original_media_count": item["original_media_count"],
            "effort_score": item["effort_score"],
            "aio_passage_word_count": item["aio_passage_word_count"],
            "schema_jsonld_types": json.loads(item["schema_jsonld_types"]),
            "entity_density_score": item["entity_density_score"],
            "click_depth_from_home": item["click_depth_from_home"],
            "site_focus_alignment": item["site_focus_alignment"],
            "nav": nav,
            "cwv": cwv,
            "scores": scores,
            "winning_pattern": item["winning_pattern"],
            "recommended_action": item["action"],
        })

    conn.commit()
    conn.close()

    state_payload = {
        "generated_at": datetime.now().isoformat(),
        "database_path": DB_PATH,
        "variants_ranked_by_reward": sorted(
            exported_rows, key=lambda x: x["scores"]["agent_reward_signal"], reverse=True
        ),
    }

    state_file = os.path.join(PUBLIC_DIR, "agent_knowledge_state.json")
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state_payload, f, indent=2, ensure_ascii=False)

    print(f"[OK] Baza SQLite utworzona: {DB_PATH}")
    print(f"[OK] Stan wiedzy Agenta AI wyeksportowany: {state_file}")
    for row in state_payload["variants_ranked_by_reward"]:
        s = row["scores"]
        print(
            f"  #{row['id']} [{row['content_format']}] "
            f"Reward={s['agent_reward_signal']:.3f} | "
            f"SEO={s['composite_seo_score']}/100 | "
            f"Konwersja={s['conversion_rate_pct']}% | "
            f"NavBoost Good={s['navboost_satisfaction_ratio']}%"
        )


if __name__ == "__main__":
    init_and_seed_db()

