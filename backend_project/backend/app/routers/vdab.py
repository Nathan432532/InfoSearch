import json
import os
import re
import unicodedata
from typing import Any
from urllib.parse import urlparse

import httpx
import mysql.connector
from fastapi import APIRouter, Cookie, HTTPException
from pydantic import BaseModel

from app.routers.auth import UserResponse, get_current_user_from_token
from app.services.json_cleaner import clean_vacature
from app.services.vdab_service import get_vacature_detail, get_vacatures

router = APIRouter(tags=["vacancies"])

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "").rstrip("/")


class SearchRequest(BaseModel):
    query: str | None = None
    filters: dict[str, Any] | None = None
    details: dict[str, Any] | None = None


class SaveSearchRequest(BaseModel):
    query: str
    type: str = "company"
    title: str | None = None
    filters: dict[str, Any] | None = None
    results: list[dict[str, Any]] | None = None


class SaveResultItemRequest(BaseModel):
    query: str
    type: str = "company"
    title: str | None = None
    filters: dict[str, Any] | None = None
    result: dict[str, Any]
    rank: int | None = None


class CompanyProfile(BaseModel):
    bedrijf_id: int
    sector: str | None = None
    ai_beschrijving: str | None = None
    tech_stack: list[str] | None = None
    machine_park: list[str] | None = None
    business_trigger: str | None = None
    keywords: list[str] | None = None
    locatie: str | None = None
    contactgegevens: str | None = None


RESULT_TYPE_MAP = {
    "company": "bedrijf",
    "job": "vacature",
}

SEARCH_SESSION_TYPE_MAP = {
    "company": "company",
    "job": "job",
}


def _require_user(session_token: str | None) -> UserResponse:
    return get_current_user_from_token(session_token)


def _db_config() -> dict[str, Any]:
    return {
        "host": os.getenv("MYSQL_HOST", "mysql"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "database": os.getenv("MYSQL_DATABASE", "InfoSearch"),
        "user": os.getenv("MYSQL_USER", "user"),
        "password": os.getenv("MYSQL_PASSWORD", "pass"),
    }


def _normalize_type(value: str | None) -> str:
    normalized = (value or "company").strip().lower()
    if normalized not in RESULT_TYPE_MAP:
        raise HTTPException(status_code=400, detail="Invalid type")
    return normalized


def _score_value(raw_score: Any) -> float | None:
    if raw_score is None:
        return None
    try:
        score = float(raw_score)
        if 1.0 <= score <= 10.0:
            return score
    except (ValueError, TypeError):
        pass
    return None


_COMPANY_SUFFIXES = {
    "bv", "bvba", "nv", "gmbh", "ltd", "srl", "sa", "sprl", "vof", "commv", "cv", "llc", "inc"
}


def _strip_accents(value: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(char)
    )


def _normalize_business_name(value: Any) -> str:
    text = _strip_accents(str(value or "").lower())
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    parts = [part for part in text.split() if part not in _COMPANY_SUFFIXES]
    return " ".join(parts)


def _normalize_phone(value: Any) -> str:
    raw = str(value or "")
    digits = re.sub(r"\D+", "", raw)
    if digits.startswith("00"):
        digits = digits[2:]
    if digits.startswith("32") and len(digits) > 9:
        digits = "0" + digits[2:]
    return digits


def _normalize_email(value: Any) -> str:
    return str(value or "").strip().lower()


def _normalize_domain(value: Any) -> str:
    raw = str(value or "").strip().lower()
    if not raw:
        return ""
    if "://" not in raw:
        raw = "https://" + raw
    parsed = urlparse(raw)
    host = parsed.netloc or parsed.path.split("/", 1)[0]
    return host.removeprefix("www.").rstrip("/")


def _normalize_address(value: Any) -> str:
    text = _strip_accents(str(value or "").lower())
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return " ".join(text.split())


def _business_dedupe_keys(payload: dict[str, Any]) -> dict[str, str]:
    contact = str(payload.get("contactgegevens") or "")
    email_match = re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", contact, re.I)
    phone_value = payload.get("telefoon") or payload.get("phone") or contact
    website_value = payload.get("website") or payload.get("url") or payload.get("source_url") or contact
    address = payload.get("adres") or payload.get("address") or payload.get("locatie") or ""
    vat = payload.get("kbo_nummer") or payload.get("kbo") or payload.get("vat") or payload.get("btw_nummer") or ""
    return {
        "name": _normalize_business_name(payload.get("bedrijfsnaam") or payload.get("naam") or payload.get("title")),
        "domain": _normalize_domain(website_value),
        "phone": _normalize_phone(phone_value),
        "email": _normalize_email(email_match.group(0) if email_match else payload.get("email")),
        "address": _normalize_address(address),
        "vat": re.sub(r"\W+", "", str(vat or "").lower()),
    }


def _is_duplicate_business(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_keys = _business_dedupe_keys(left)
    right_keys = _business_dedupe_keys(right)
    for key in ["vat", "domain", "email", "phone"]:
        if left_keys[key] and left_keys[key] == right_keys[key]:
            return True
    if left_keys["name"] and left_keys["name"] == right_keys["name"]:
        if left_keys["address"] and right_keys["address"] and left_keys["address"] == right_keys["address"]:
            return True
        if not left_keys["address"] or not right_keys["address"]:
            return True
    return False


def _merge_result_payload(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = dict(existing)
    for key, value in incoming.items():
        if value in (None, "", [], {}):
            continue
        current = merged.get(key)
        if current in (None, "", [], {}):
            merged[key] = value
        elif isinstance(current, list):
            values = value if isinstance(value, list) else [value]
            for item in values:
                if item not in current:
                    current.append(item)
        elif isinstance(value, str) and isinstance(current, str) and len(value) > len(current):
            merged[key] = value
    sources = []
    for source in [existing.get("source_url"), incoming.get("source_url"), existing.get("sources"), incoming.get("sources")]:
        if isinstance(source, list):
            sources.extend(str(item) for item in source if item)
        elif source:
            sources.append(str(source))
    if sources:
        merged["sources"] = sorted(set(sources))
    merged["save_status"] = "merged"
    return merged


def _build_result_payload(result: dict[str, Any], item_type: str) -> dict[str, Any]:
    payload = dict(result)
    payload.pop("saved_result_id", None)
    payload.pop("saved_search_id", None)

    if item_type == "company":
        raw_company_id = payload.get("bedrijf_id") or payload.get("id")
        try:
            payload["bedrijf_id"] = int(raw_company_id) if raw_company_id is not None else None
        except (TypeError, ValueError):
            payload["bedrijf_id"] = None
    else:
        vacature_ref = (
            payload.get("vacatureReferentie")
            or payload.get("interne_referentie")
            or payload.get("vacature_id")
            or payload.get("id")
        )
        if vacature_ref is not None:
            payload["vacatureReferentie"] = str(vacature_ref)

    return payload


def _insert_saved_results(cursor: Any, search_id: int, item_type: str, results: list[dict[str, Any]], user_id: int | None = None) -> dict[str, int]:
    result_type = RESULT_TYPE_MAP[item_type]
    stats = {"new": 0, "merged": 0, "rejected_low_quality": 0}

    for index, result in enumerate(results, start=1):
        payload = _build_result_payload(result, item_type)
        rank = payload.get("rank") or index
        score = _score_value(payload.get("score"))
        vacature_id = None
        bedrijf_id = None

        if item_type == "job":
            vacature_id = (
                payload.get("vacatureReferentie")
                or payload.get("interne_referentie")
                or payload.get("vacature_id")
            )
        else:
            raw_bedrijf_id = payload.get("bedrijf_id") or payload.get("id")
            try:
                bedrijf_id = int(raw_bedrijf_id) if raw_bedrijf_id is not None else None
            except (ValueError, TypeError):
                bedrijf_id = None

        if item_type == "company" and score is not None and score < 4:
            stats["rejected_low_quality"] += 1
            continue
        if item_type == "job" and not vacature_id:
            raise HTTPException(status_code=400, detail="Saved job result is missing vacature reference")
        if item_type == "company" and bedrijf_id is None:
            raise HTTPException(status_code=400, detail="Saved company result is missing bedrijf_id")

        if item_type == "company" and user_id is not None:
            cursor.execute(
                """
                SELECT r.id, r.explanation_json, r.match_score
                FROM tblSearchResults r
                JOIN tblSearchSessions s ON s.id = r.search_id
                WHERE s.user_id = %s AND r.result_type = 'bedrijf'
                """,
                (user_id,),
            )
            for existing_id, existing_json, existing_score in cursor.fetchall():
                existing_payload = json.loads(existing_json) if existing_json else {}
                existing_bedrijf_id = existing_payload.get("bedrijf_id") or existing_payload.get("id")
                is_same_id = bedrijf_id is not None and str(existing_bedrijf_id) == str(bedrijf_id)
                if is_same_id or _is_duplicate_business(existing_payload, payload):
                    merged_payload = _merge_result_payload(existing_payload, payload)
                    merged_score = max(
                        float(existing_score or 0),
                        float(score or 0),
                    ) or None
                    cursor.execute(
                        """
                        UPDATE tblSearchResults
                        SET match_score = %s, explanation_json = %s
                        WHERE id = %s
                        """,
                        (merged_score, json.dumps(merged_payload, ensure_ascii=False, default=str), existing_id),
                    )
                    stats["merged"] += 1
                    break
            else:
                cursor.execute(
                    """
                    INSERT INTO tblSearchResults
                        (search_id, result_type, vacature_id, bedrijf_id, `rank`, match_score, explanation_json)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        search_id,
                        result_type,
                        vacature_id,
                        bedrijf_id,
                        rank,
                        score,
                        json.dumps(payload, ensure_ascii=False, default=str),
                    ),
                )
                stats["new"] += 1
            continue

        cursor.execute(
            """
            INSERT INTO tblSearchResults
                (search_id, result_type, vacature_id, bedrijf_id, `rank`, match_score, explanation_json)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                search_id,
                result_type,
                vacature_id,
                bedrijf_id,
                rank,
                score,
                json.dumps(payload, ensure_ascii=False, default=str),
            ),
        )
        stats["new"] += 1

    return stats


def _row_to_saved_result(row: dict[str, Any]) -> dict[str, Any]:
    payload = json.loads(row["explanation_json"]) if row.get("explanation_json") else {}
    payload["saved_result_id"] = row["id"]
    payload["saved_search_id"] = row["search_id"]
    return {
        "id": row["id"],
        "search_id": row["search_id"],
        "type": "company" if row["result_type"] == "bedrijf" else "job",
        "title": row.get("search_title") or row.get("session_title") or row.get("query") or "Opgeslagen resultaat",
        "query": row.get("query") or "",
        "datum": row["created_at"].isoformat() if row.get("created_at") else None,
        "rank": row.get("rank"),
        "score": float(row["match_score"]) if row.get("match_score") is not None else None,
        "result": payload,
    }


def _fetch_vacancies(where_sql: str = "", params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    query = f"""
        SELECT
            interne_referentie,
            vdab_referentie,
            status,
            publicatie_datum,
            bron,
            internationaal_opengesteld,
            titel,
            beroep,
            ervaring,
            omschrijving,
            vrije_vereiste,
            contract_type,
            contract_regime,
            aantal_uur,
            vermoedelijke_startdatum,
            loon_min,
            loon_max,
            contract_extra,
            postcode,
            gemeente,
            provincie,
            lat,
            lon,
            cv_gewenst,
            sollicitatie_email,
            sollicitatie_webformulier,
            sollicitatie_telefoon,
            bedrijf_id,
            created_at,
            updated_at
        FROM tblVacatures
        {where_sql}
        ORDER BY created_at DESC
    """

    conn = mysql.connector.connect(**_db_config())
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    finally:
        conn.close()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/vacancies")
def list_vacancies() -> dict[str, Any]:
    try:
        vacancies = _fetch_vacancies()
        return {"vacancies": vacancies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vacancies/{id}")
def get_vacancy(id: str) -> dict[str, Any]:
    try:
        vacancies = _fetch_vacancies("WHERE interne_referentie = %s", (id,))
        if not vacancies:
            raise HTTPException(status_code=404, detail="Vacancy not found")
        return {"vacancy": vacancies[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
def search_vacancies(payload: SearchRequest) -> dict[str, Any]:
    try:
        clauses: list[str] = []
        values: list[Any] = []

        query_text = (payload.query or "").strip()
        if query_text:
            like_value = f"%{query_text}%"
            clauses.append(
                "("
                "titel LIKE %s OR "
                "omschrijving LIKE %s OR "
                "vrije_vereiste LIKE %s OR "
                "beroep LIKE %s OR "
                "gemeente LIKE %s"
                ")"
            )
            values.extend([like_value, like_value, like_value, like_value, like_value])

        allowed_filters = {
            "status": "status",
            "gemeente": "gemeente",
            "postcode": "postcode",
            "contract_type": "contract_type",
            "ervaring": "ervaring",
        }

        for key, column in allowed_filters.items():
            filter_value = (payload.filters or {}).get(key)
            if filter_value is None:
                continue
            if isinstance(filter_value, str):
                filter_value = filter_value.strip()
                if not filter_value:
                    continue
            clauses.append(f"{column} = %s")
            values.append(filter_value)

        sector_filter = (payload.filters or {}).get("sector")
        if isinstance(sector_filter, str) and sector_filter.strip():
            clauses.append("beroep LIKE %s")
            values.append(f"%{sector_filter.strip()}%")

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        vacancies = _fetch_vacancies(where_sql, tuple(values))

        return {
            "query": payload.query,
            "filters": payload.filters or {},
            "results": vacancies,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/companies/search")
def search_companies(payload: SearchRequest) -> dict[str, Any]:
    try:
        clauses: list[str] = []
        values: list[Any] = []

        query_text = (payload.query or "").strip()
        if query_text:
            like_value = f"%{query_text}%"
            clauses.append(
                "("
                "v.titel LIKE %s OR "
                "v.omschrijving LIKE %s OR "
                "v.vrije_vereiste LIKE %s OR "
                "v.beroep LIKE %s OR "
                "v.gemeente LIKE %s OR "
                "b.naam LIKE %s"
                ")"
            )
            values.extend([like_value] * 6)

        gemeente_filter = (payload.filters or {}).get("gemeente") or (payload.filters or {}).get("locatie")
        if gemeente_filter and isinstance(gemeente_filter, str) and gemeente_filter.strip():
            clauses.append("(v.gemeente LIKE %s OR b.adres_gemeente LIKE %s)")
            like_gem = f"%{gemeente_filter.strip()}%"
            values.extend([like_gem, like_gem])

        where_sql = f"WHERE b.id IS NOT NULL AND {' AND '.join(clauses)}" if clauses else "WHERE b.id IS NOT NULL"

        query = f"""
            SELECT
                b.id            AS bedrijf_id,
                b.naam          AS bedrijfsnaam,
                b.kbo_nummer,
                b.adres_gemeente,
                b.adres_provincie,
                b.email         AS bedrijf_email,
                b.telefoon      AS bedrijf_telefoon,
                b.website,
                v.interne_referentie,
                v.titel,
                v.beroep,
                v.omschrijving,
                v.vrije_vereiste,
                v.gemeente,
                v.provincie,
                v.contract_type,
                v.ervaring,
                v.sollicitatie_email,
                v.sollicitatie_telefoon,
                v.publicatie_datum
            FROM tblVacatures v
            JOIN tblBedrijven b ON v.bedrijf_id = b.id
            {where_sql}
            ORDER BY b.naam, v.publicatie_datum DESC
        """

        conn = mysql.connector.connect(**_db_config())
        try:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(query, tuple(values))
                rows = cursor.fetchall()
        finally:
            conn.close()

        companies: dict[int, dict[str, Any]] = {}
        for row in rows:
            bid = row["bedrijf_id"]
            if bid not in companies:
                companies[bid] = {
                    "id": bid,
                    "bedrijfsnaam": row["bedrijfsnaam"],
                    "kbo_nummer": row.get("kbo_nummer"),
                    "locatie": ", ".join(
                        p for p in [row.get("adres_gemeente") or row.get("gemeente"), row.get("adres_provincie") or row.get("provincie")] if p
                    ),
                    "contactgegevens": " - ".join(
                        p for p in [row.get("bedrijf_email") or row.get("sollicitatie_email"), row.get("bedrijf_telefoon") or row.get("sollicitatie_telefoon"), row.get("website")] if p
                    ),
                    "vacatures": [],
                }
            companies[bid]["vacatures"].append(
                {
                    "referentie": row["interne_referentie"],
                    "titel": row["titel"],
                    "beroep": row.get("beroep"),
                    "gemeente": row.get("gemeente"),
                    "contract_type": row.get("contract_type"),
                    "ervaring": row.get("ervaring"),
                    "omschrijving": (row.get("omschrijving") or "")[:300],
                    "vrije_vereiste": (row.get("vrije_vereiste") or "")[:300],
                    "publicatie_datum": str(row["publicatie_datum"]) if row.get("publicatie_datum") else None,
                }
            )

        return {
            "query": payload.query,
            "filters": payload.filters or {},
            "results": list(companies.values()),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _parse_json_list(raw: Any) -> list[str]:
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except Exception:
            return [raw.strip()] if raw.strip() else []
    return []


TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9\-\+\.]{1,}")

STOPWORDS = {
    "de", "het", "een", "en", "of", "voor", "van", "met", "op", "in", "aan", "te", "tot",
    "software", "platform", "systeem", "system", "toolkit", "services", "package",
    "ai", "automated", "automatic", "based", "sites",
}

SYNONIEMEN = {
    "agv": ["autonomous guided vehicle", "guided vehicles", "fleet orchestration", "warehouse robotics"],
    "warehouse": ["logistiek", "magazijn", "intralogistics"],
    "robot": ["robotica", "robotics", "autonome"],
    "robots": ["robotica", "robotics", "autonome"],
    "scada": ["wonderware", "intouch", "hmi", "supervisory"],
    "plc": ["s7", "s7-1500", "codesys", "safety plc"],
    "siemens": ["s7", "s7-1500", "sinamics"],
    "schneider": ["ecostruxure", "modicon"],
    "drives": ["drive", "sinamics", "frequentieregelaars", "high power"],
    "battery": ["batterij", "battery-management", "bms"],
    "vision": ["camera", "computer vision", "inspectie", "inspection", "defect detection"],
    "maintenance": ["onderhoud", "storingen", "predictive maintenance", "preventive maintenance"],
    "field": ["buitendienst", "field service"],
    "service": ["buitendienst", "service engineer", "field service"],
    "recruitment": ["recruitment", "staffing", "hiring", "vacature", "engineers"],
    "staffing": ["recruitment", "hiring", "vacature", "engineers"],
    "food": ["brewery", "brouwerij", "voeding", "beverage", "packaging", "food processing", "horeca"],
    "voeding": ["food", "food processing", "horeca", "keukenmachines"],
    "horeca": ["professionele keuken", "keukenmachines", "catering", "commercial kitchen"],
    "aardappel": ["aardappelschiller", "aardappelschilmachine", "aardappelverwerking", "potato", "potato peeler", "potato peeling machine"],
    "aardappelen": ["aardappelschiller", "aardappelschilmachine", "aardappelverwerking", "potato", "potato peeler", "potato peeling machine"],
    "schiller": ["peeler", "peeling", "schilmachine", "aardappelschiller", "potato peeler"],
    "schillers": ["peelers", "peeling machines", "schilmachines", "aardappelschillers", "potato peelers"],
    "schilmachine": ["peeling machine", "peeler", "aardappelschilmachine", "potato peeling machine"],
    "peeler": ["schiller", "schilmachine", "potato peeler", "potato peeling machine"],
    "peelers": ["schillers", "schilmachines", "potato peelers"],
    "potato": ["aardappel", "aardappelschiller", "aardappelschilmachine", "potato peeler", "potato peeling machine"],
    "keukenmachine": ["horeca", "professionele keuken", "commercial kitchen", "food processing"],
    "keukenmachines": ["horeca", "professionele keuken", "commercial kitchen", "food processing"],
    "cnc": ["bewerkingscentra", "metal forming", "walsinstallaties"],
}


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        value = " ".join(str(item) for item in value)
    return str(value).lower()


def _tokenize(value: Any) -> list[str]:
    text = _normalize_text(value)
    return [token for token in TOKEN_RE.findall(text) if token not in STOPWORDS and len(token) > 1]


def _build_company_text(company: dict[str, Any]) -> str:
    parts = [
        company.get("naam", ""),
        company.get("sector", ""),
        company.get("locatie", ""),
        company.get("ai_beschrijving", ""),
        company.get("business_trigger", ""),
        " ".join(company.get("vacatures", [])),
        " ".join(company.get("beroepen", [])),
        " ".join(company.get("tech_stack", [])),
        " ".join(company.get("machine_park", [])),
        " ".join(company.get("keywords", [])),
        " ".join(company.get("vacature_samenvattingen", [])),
    ]
    return _normalize_text(" ".join(part for part in parts if part))


def _expanded_product_terms(product_tokens: set[str]) -> set[str]:
    terms = set(product_tokens)
    for token in list(product_tokens):
        terms.update(_tokenize(SYNONIEMEN.get(token, [])))
    return terms


def _score_company_match(product: str, company: dict[str, Any]) -> tuple[float, list[str]]:
    product_text = _normalize_text(product)
    company_text = _build_company_text(company)
    product_tokens = set(_tokenize(product_text))
    expanded_terms = _expanded_product_terms(product_tokens)

    score = 0.0
    product_evidence = 0
    reasons: list[str] = []

    exact_phrases = [
        "siemens s7-1500", "profinet", "sinamics", "scada", "schneider", "ecostruxure",
        "field service", "service engineer", "battery-management", "autonomous", "robot",
        "robotics", "warehouse", "agv", "machine vision", "computer vision", "cnc",
        "metal forming", "food", "beverage", "predictive maintenance", "preventive maintenance",
        "automatische aardappelschiller", "aardappelschilmachine", "aardappelschillers",
        "industriële aardappelschiller", "industriele aardappelschiller", "professionele aardappelschiller",
        "potato peeling machine", "automatic potato peeler", "commercial potato peeler",
        "food processing machinery", "horeca keukenmachines", "aardappelverwerkingsmachines",
    ]
    for phrase in exact_phrases:
        if phrase in product_text and phrase in company_text:
            score += 4.0
            product_evidence += 2
            reasons.append(phrase)

    overlap_count = 0
    for token in product_tokens:
        if token in company_text:
            score += 1.4
            overlap_count += 1
            product_evidence += 1
            reasons.append(token)
        for synonym in SYNONIEMEN.get(token, []):
            if synonym in company_text:
                score += 1.0
                overlap_count += 1
                product_evidence += 1
                reasons.append(synonym)

    score += min(3.0, overlap_count * 0.35)

    if any(term in company_text for term in ["plc", "scada", "robot", "robotica", "cnc", "maintenance", "onderhoud", "field service"]):
        score += 0.5

    if company.get("business_trigger"):
        score += 0.3

    if company.get("tech_stack"):
        score += 0.3

    potato_query = bool({"aardappel", "aardappelen", "schiller", "schillers", "schilmachine", "potato", "peeler", "peelers"} & expanded_terms)
    if potato_query:
        potato_evidence_terms = [
            "aardappel", "aardappelschiller", "aardappelschilmachine", "schilmachine",
            "potato", "peeler", "peeling", "horeca", "keukenmachine", "food processing",
            "voedingsmachine", "catering", "commercial kitchen",
        ]
        if any(term in company_text for term in potato_evidence_terms):
            score += 2.0
            product_evidence += 2
            reasons.append("potato/food-processing equipment evidence")
        else:
            score -= 6.0

    if any(t in product_tokens for t in {"siemens", "plc", "profinet", "s7-1500"}):
        if "siemens" not in company_text and "s7" not in company_text and "plc" not in company_text:
            score -= 3.0
    if any(t in product_tokens for t in {"schneider", "scada"}):
        if "schneider" not in company_text and "ecostruxure" not in company_text and "scada" not in company_text and "wonderware" not in company_text:
            score -= 3.0
    if any(t in product_tokens for t in {"robot", "robotics", "agv", "warehouse", "autonomous"}):
        if "robot" not in company_text and "robotica" not in company_text and "autonome" not in company_text and "agv" not in company_text:
            score -= 2.5
    if any(t in product_tokens for t in {"food", "beverage", "packaging", "voeding", "horeca"}):
        if not any(term in company_text for term in ["food", "beverage", "voeding", "brouwerij", "afvullijnen", "packaging", "horeca", "keuken"]):
            score -= 2.5

    # Product-first relevance: do not allow a company to rank on generic or
    # location-only overlap. A candidate needs concrete product evidence before
    # it can be saved as a useful prospect.
    if product_tokens and product_evidence == 0:
        score = min(score, 2.0)
        reasons.append("rejected: no concrete product/service evidence")

    unique_reasons: list[str] = []
    seen: set[str] = set()
    for reason in reasons:
        if reason not in seen:
            seen.add(reason)
            unique_reasons.append(reason)

    return score, unique_reasons[:5]


def _deterministic_prospect_results(product: str, companies: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    ranked: list[tuple[float, dict[str, Any], list[str]]] = []
    for company in companies:
        score, reasons = _score_company_match(product, company)
        ranked.append((score, company, reasons))

    ranked.sort(key=lambda item: (-item[0], item[1].get("naam", "")))

    results: list[dict[str, Any]] = []
    quality_ranked = [(raw_score, company, reasons) for raw_score, company, reasons in ranked if raw_score >= 4]
    for raw_score, company, reasons in quality_ranked[:limit]:
        normalized_score = max(1, min(10, int(round(raw_score))))
        reason_text = ", ".join(reasons) if reasons else "concrete product/service overlap in vacancy data"
        results.append(
            {
                "id": company["id"],
                "bedrijf_id": company["id"],
                "bedrijfsnaam": company["naam"],
                "sector": company.get("sector", "Onbekend"),
                "locatie": company.get("locatie", ""),
                "beschrijving": (company.get("ai_beschrijving") or company.get("business_trigger") or f"{company['naam']} heeft relevante vacaturesignalen.")[:280],
                "waarom": f"Match op product/service-evidence: {reason_text}.",
                "score": normalized_score,
                "contactgegevens": company.get("contactgegevens", "Niet beschikbaar"),
                "techstack": company.get("tech_stack", [])[:8],
                "sources": company.get("source_urls", []),
            }
        )

    return results


def _fetch_all_companies_with_vacatures() -> list[dict[str, Any]]:
    query = """
        SELECT
            b.id AS bedrijf_id,
            b.naam AS bedrijfsnaam,
            b.kbo_nummer,
            b.adres_gemeente,
            b.adres_provincie,
            b.email AS bedrijf_email,
            b.telefoon AS bedrijf_telefoon,
            b.website,
            b.sector AS bedrijf_sector,
            b.ai_beschrijving,
            b.tech_stack_json,
            b.machine_park_json,
            b.business_trigger,
            b.keywords_json,
            v.interne_referentie,
            v.titel,
            v.beroep,
            v.omschrijving,
            v.vrije_vereiste,
            v.gemeente,
            v.provincie,
            v.contract_type,
            v.ervaring,
            v.sollicitatie_email,
            v.sollicitatie_telefoon
        FROM tblVacatures v
        JOIN tblBedrijven b ON v.bedrijf_id = b.id
        ORDER BY b.naam, v.interne_referentie
    """
    conn = mysql.connector.connect(**_db_config())
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
    finally:
        conn.close()

    companies: dict[int, dict[str, Any]] = {}
    for row in rows:
        bid = row["bedrijf_id"]
        if bid not in companies:
            companies[bid] = {
                "id": bid,
                "naam": row["bedrijfsnaam"],
                "sector": row.get("bedrijf_sector") or row.get("beroep") or "Onbekend",
                "locatie": ", ".join(
                    p for p in [row.get("adres_gemeente") or row.get("gemeente"), row.get("adres_provincie") or row.get("provincie")] if p
                ),
                "contactgegevens": " - ".join(
                    p for p in [row.get("bedrijf_email") or row.get("sollicitatie_email"), row.get("bedrijf_telefoon") or row.get("sollicitatie_telefoon"), row.get("website")] if p
                ),
                "source_urls": [url for url in [row.get("website")] if url],
                "ai_beschrijving": row.get("ai_beschrijving") or "",
                "business_trigger": row.get("business_trigger") or "",
                "tech_stack": _parse_json_list(row.get("tech_stack_json")),
                "machine_park": _parse_json_list(row.get("machine_park_json")),
                "keywords": _parse_json_list(row.get("keywords_json")),
                "vacatures": [],
                "beroepen": [],
                "vacature_samenvattingen": [],
            }
        titel = (row.get("titel") or "").strip()
        if titel:
            companies[bid]["vacatures"].append(titel)

        beroep = (row.get("beroep") or "").strip()
        if beroep and beroep not in companies[bid]["beroepen"]:
            companies[bid]["beroepen"].append(beroep)
        if beroep and beroep not in companies[bid]["tech_stack"]:
            companies[bid]["tech_stack"].append(beroep)

        summary_parts = [
            titel,
            beroep,
            (row.get("omschrijving") or "")[:220].strip(),
            (row.get("vrije_vereiste") or "")[:160].strip(),
        ]
        summary = " | ".join(part for part in summary_parts if part)
        if summary and len(companies[bid]["vacature_samenvattingen"]) < 3:
            companies[bid]["vacature_samenvattingen"].append(summary)
    return list(companies.values())


@router.post("/companies/prospect")
def company_prospect(payload: SearchRequest) -> dict[str, Any]:
    product = (payload.query or "").strip()
    if not product:
        raise HTTPException(status_code=400, detail="Product description required")

    try:
        bedrijven = _fetch_all_companies_with_vacatures()
        if not bedrijven:
            raise HTTPException(status_code=404, detail="No companies in database")

        filters = payload.filters or {}
        locatie_filter = (filters.get("locatie") or "").strip().lower()
        sector_filter = (filters.get("sector") or "").strip().lower()
        bedrijfsgrootte_filter = (filters.get("bedrijfsgrootte") or "").strip().lower()
        regio_filter = (filters.get("regio") or "").strip().lower()

        regio_map = {
            "vlaanderen": ["oost-vlaanderen", "west-vlaanderen", "antwerpen", "limburg", "vlaams-brabant"],
            "wallonie": ["henegouwen", "luik", "luxemburg", "namen", "waals-brabant"],
            "brussel": ["brussel"],
        }

        def matches_filters(company: dict[str, Any]) -> bool:
            loc = (company.get("locatie") or "").lower()
            if locatie_filter and locatie_filter not in loc:
                return False
            if sector_filter:
                sec = (company.get("sector") or "").lower()
                vacs = " ".join(company.get("vacatures", [])).lower()
                if sector_filter not in sec and sector_filter not in vacs:
                    return False
            if regio_filter and regio_filter in regio_map:
                if not any(prov in loc for prov in regio_map[regio_filter]):
                    return False
            if bedrijfsgrootte_filter:
                # We do not have employee-count data yet, so use the number of
                # linked vacancies as a pragmatic size signal until real company
                # size enrichment is added.
                vacature_count = len(company.get("vacatures", []))
                if bedrijfsgrootte_filter == "klein" and vacature_count >= 5:
                    return False
                if bedrijfsgrootte_filter == "middel" and not (5 <= vacature_count <= 20):
                    return False
                if bedrijfsgrootte_filter == "groot" and vacature_count <= 20:
                    return False
            return True

        has_active_filters = any(
            value.strip() for value in [locatie_filter, sector_filter, bedrijfsgrootte_filter, regio_filter]
        )
        filtered_bedrijven = [company for company in bedrijven if matches_filters(company)]
        if not filtered_bedrijven and not has_active_filters:
            filtered_bedrijven = bedrijven

        heuristic_results = _deterministic_prospect_results(product, filtered_bedrijven, limit=10)
        low_quality_rejected = max(len(filtered_bedrijven) - len(heuristic_results), 0)
        query_expansion_used = any(token in SYNONIEMEN for token in _tokenize(product))

        ai_results = None
        used_ai = False
        # The AI wrapper currently fetches its own broad candidate list and does
        # not accept filters, so use the backend-filtered deterministic ranking
        # when filters are active. This prevents filtered searches from showing
        # unfiltered AI results.
        if AI_SERVICE_URL and not has_active_filters:
            try:
                with httpx.Client(timeout=120.0) as client:
                    res = client.post(
                        f"{AI_SERVICE_URL}/generate-prospect",
                        params={"product": product},
                    )
                    if res.status_code == 200:
                        data = res.json()
                        rapport = data.get("rapport")
                        if isinstance(rapport, list) and all(isinstance(r, dict) and r.get("bedrijfsnaam") for r in rapport):
                            ai_results = rapport
                            used_ai = True
                    else:
                        print(f"AI prospect service returned {res.status_code}, using deterministic fallback...")
            except Exception as e:
                print(f"AI service unreachable ({e}), using deterministic fallback...")

        if ai_results is None:
            ai_results = heuristic_results
        elif isinstance(ai_results, list):
            # Keep product-first quality rules even when the AI path is used.
            ai_results = [item for item in ai_results if float(item.get("score") or 0) >= 4]

        results = ai_results if isinstance(ai_results, list) else [ai_results]
        return {
            "query": product,
            "ai_powered": used_ai,
            "results": results,
            "run_report": {
                "new_businesses_returned": len(results),
                "duplicates_merged_or_skipped": 0,
                "low_quality_results_rejected": low_quality_rejected,
                "best_search_terms": _tokenize(product)[:8],
                "query_expansion_used": query_expansion_used,
                "product_first_relevance": True,
                "location_filter_used_as_constraint_only": bool(locatie_filter or regio_filter),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _find_existing_company_id(cursor: Any, cleaned: dict[str, Any]) -> int | None:
    company_payload = {
        "bedrijfsnaam": cleaned["bedrijf"].get("naam"),
        "kbo_nummer": cleaned["bedrijf"].get("kbo"),
        "email": cleaned["sollicitatie"].get("email"),
        "telefoon": cleaned["sollicitatie"].get("telefoon"),
        "website": cleaned["sollicitatie"].get("webformulier"),
        "adres": " ".join(
            str(part) for part in [
                cleaned["locatie"].get("postcode"),
                cleaned["locatie"].get("gemeente"),
                cleaned["locatie"].get("provincie"),
            ] if part
        ),
    }
    if company_payload["kbo_nummer"]:
        cursor.execute("SELECT id FROM tblBedrijven WHERE kbo_nummer = %s", (company_payload["kbo_nummer"],))
        row = cursor.fetchone()
        if row:
            return row[0]

    cursor.execute(
        """
        SELECT id, kbo_nummer, naam, website, email, telefoon, adres_postcode, adres_gemeente, adres_provincie
        FROM tblBedrijven
        WHERE adres_gemeente = %s OR naam LIKE %s OR email = %s OR telefoon = %s
        LIMIT 200
        """,
        (
            cleaned["locatie"].get("gemeente"),
            f"%{(cleaned['bedrijf'].get('naam') or '').split()[0] if cleaned['bedrijf'].get('naam') else ''}%",
            cleaned["sollicitatie"].get("email"),
            cleaned["sollicitatie"].get("telefoon"),
        ),
    )
    for row in cursor.fetchall():
        candidate = {
            "bedrijf_id": row[0],
            "kbo_nummer": row[1],
            "bedrijfsnaam": row[2],
            "website": row[3],
            "email": row[4],
            "telefoon": row[5],
            "adres": " ".join(str(part) for part in [row[6], row[7], row[8]] if part),
        }
        if _is_duplicate_business(candidate, company_payload):
            return row[0]
    return None


@router.post("/vacancies/update")
def update_vacancies(aantal: int = 500) -> dict[str, Any]:
    try:
        data = get_vacatures(aantal=aantal)
        raw_list = data.get("resultaten", [])
        is_fallback = data.get("fallback", False)

        conn = mysql.connector.connect(**_db_config())
        upserted = 0
        new_businesses_saved = 0
        duplicates_merged_or_skipped = 0
        low_quality_rejected = 0
        try:
            with conn.cursor() as cursor:
                total = len(raw_list)
                for idx, item in enumerate(raw_list, 1):
                    ref = item.get("vacatureReferentie") or {}
                    interne_id = ref.get("interneReferentie")
                    if not interne_id:
                        continue

                    if idx % 50 == 0 or idx == total:
                        print(f"[vacancies] Processing {idx}/{total} ...")

                    raw = get_vacature_detail(interne_id)
                    if not raw:
                        continue

                    cleaned = clean_vacature(raw)
                    if not cleaned["id"] or not cleaned["job"].get("titel"):
                        continue

                    bedrijf_id = _find_existing_company_id(cursor, cleaned)
                    kbo = cleaned["bedrijf"].get("kbo")
                    if bedrijf_id:
                        cursor.execute(
                            """
                            UPDATE tblBedrijven
                            SET kbo_nummer=COALESCE(kbo_nummer, %s),
                                naam=COALESCE(NULLIF(naam, ''), %s),
                                type=COALESCE(type, %s),
                                email=COALESCE(email, %s),
                                telefoon=COALESCE(telefoon, %s),
                                website=COALESCE(website, %s),
                                adres_postcode=COALESCE(adres_postcode, %s),
                                adres_gemeente=COALESCE(adres_gemeente, %s),
                                adres_provincie=COALESCE(adres_provincie, %s),
                                updated_at=CURRENT_TIMESTAMP
                            WHERE id=%s
                            """,
                            (
                                kbo,
                                cleaned["bedrijf"].get("naam"),
                                cleaned["bedrijf"].get("type"),
                                cleaned["sollicitatie"].get("email"),
                                cleaned["sollicitatie"].get("telefoon"),
                                cleaned["sollicitatie"].get("webformulier"),
                                cleaned["locatie"]["postcode"],
                                cleaned["locatie"]["gemeente"],
                                cleaned["locatie"]["provincie"],
                                bedrijf_id,
                            ),
                        )
                        duplicates_merged_or_skipped += 1
                    elif cleaned["bedrijf"].get("naam"):
                        cursor.execute(
                            "INSERT INTO tblBedrijven (kbo_nummer, naam, type, website, email, telefoon, adres_postcode, adres_gemeente, adres_provincie, source_code) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'vdab')",
                            (
                                kbo,
                                cleaned["bedrijf"].get("naam"),
                                cleaned["bedrijf"].get("type"),
                                cleaned["sollicitatie"].get("webformulier"),
                                cleaned["sollicitatie"].get("email"),
                                cleaned["sollicitatie"].get("telefoon"),
                                cleaned["locatie"]["postcode"],
                                cleaned["locatie"]["gemeente"],
                                cleaned["locatie"]["provincie"],
                            ),
                        )
                        bedrijf_id = cursor.lastrowid
                        new_businesses_saved += 1
                    else:
                        low_quality_rejected += 1

                    cursor.execute(
                        "INSERT INTO tblVacatures ("
                        " interne_referentie, vdab_referentie, status, publicatie_datum,"
                        " bron, internationaal_opengesteld,"
                        " titel, beroep, ervaring, omschrijving, vrije_vereiste,"
                        " contract_type, contract_regime, aantal_uur, vermoedelijke_startdatum,"
                        " loon_min, loon_max, contract_extra,"
                        " postcode, gemeente, provincie, lat, lon,"
                        " cv_gewenst, sollicitatie_email, sollicitatie_webformulier, sollicitatie_telefoon,"
                        " bedrijf_id, raw_json"
                        ") VALUES ("
                        " %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s"
                        ") ON DUPLICATE KEY UPDATE "
                        " vdab_referentie=VALUES(vdab_referentie), status=VALUES(status),"
                        " publicatie_datum=VALUES(publicatie_datum), bron=VALUES(bron),"
                        " internationaal_opengesteld=VALUES(internationaal_opengesteld),"
                        " titel=VALUES(titel), beroep=VALUES(beroep), ervaring=VALUES(ervaring),"
                        " omschrijving=VALUES(omschrijving), vrije_vereiste=VALUES(vrije_vereiste),"
                        " contract_type=VALUES(contract_type), contract_regime=VALUES(contract_regime),"
                        " aantal_uur=VALUES(aantal_uur), vermoedelijke_startdatum=VALUES(vermoedelijke_startdatum),"
                        " loon_min=VALUES(loon_min), loon_max=VALUES(loon_max),"
                        " contract_extra=VALUES(contract_extra),"
                        " postcode=VALUES(postcode), gemeente=VALUES(gemeente),"
                        " provincie=VALUES(provincie), lat=VALUES(lat), lon=VALUES(lon),"
                        " cv_gewenst=VALUES(cv_gewenst),"
                        " sollicitatie_email=VALUES(sollicitatie_email),"
                        " sollicitatie_webformulier=VALUES(sollicitatie_webformulier),"
                        " sollicitatie_telefoon=VALUES(sollicitatie_telefoon),"
                        " bedrijf_id=VALUES(bedrijf_id), raw_json=VALUES(raw_json),"
                        " updated_at=CURRENT_TIMESTAMP",
                        (
                            cleaned["id"],
                            cleaned["vdab_id"],
                            cleaned["status"],
                            cleaned["publicatieDatum"],
                            cleaned["meta"]["bron"],
                            cleaned["meta"]["internationaalOpengesteld"],
                            cleaned["job"]["titel"],
                            cleaned["job"]["beroep"],
                            cleaned["job"]["ervaring"],
                            cleaned["job"]["omschrijving"],
                            cleaned["job"]["vrijeVereiste"],
                            cleaned["contract"]["type"],
                            cleaned["contract"]["regime"],
                            cleaned["contract"]["aantalUur"],
                            cleaned["contract"]["vermoedelijkeStartdatum"],
                            cleaned["contract"]["loon"]["minimumBrutoLoon"],
                            cleaned["contract"]["loon"]["maximumBrutoLoon"],
                            cleaned["contract"]["extra"],
                            cleaned["locatie"]["postcode"],
                            cleaned["locatie"]["gemeente"],
                            cleaned["locatie"]["provincie"],
                            cleaned["locatie"]["geo"]["lat"],
                            cleaned["locatie"]["geo"]["lon"],
                            cleaned["sollicitatie"]["cvGewenst"],
                            cleaned["sollicitatie"]["email"],
                            cleaned["sollicitatie"]["webformulier"],
                            cleaned["sollicitatie"]["telefoon"],
                            bedrijf_id,
                            json.dumps(raw, ensure_ascii=False),
                        ),
                    )
                    upserted += 1

                conn.commit()
            return {
                "upserted": upserted,
                "fetched": len(raw_list),
                "fallback": is_fallback,
                "run_report": {
                    "new_businesses_saved": new_businesses_saved,
                    "duplicates_merged_or_skipped": duplicates_merged_or_skipped,
                    "low_quality_results_rejected": low_quality_rejected,
                    "best_search_terms": ["VDAB scheduled vacancy import"],
                    "query_expansion_used": False,
                    "maximized_with_pagination": len(raw_list) >= min(aantal, 50),
                },
            }
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/companies/unenriched")
def get_unenriched_companies(limit: int = 50) -> dict[str, Any]:
    query = """
        SELECT
            b.id            AS bedrijf_id,
            b.naam          AS bedrijfsnaam,
            b.kbo_nummer,
            b.adres_gemeente,
            b.adres_provincie,
            (
                SELECT CONCAT_WS(' | ',
                    COALESCE(v2.titel, ''),
                    COALESCE(v2.beroep, ''),
                    COALESCE(LEFT(v2.omschrijving, 2000), ''),
                    COALESCE(LEFT(v2.vrije_vereiste, 1000), '')
                )
                FROM tblVacatures v2
                WHERE v2.bedrijf_id = b.id
                ORDER BY v2.publicatie_datum DESC
                LIMIT 1
            ) AS vacature_tekst
        FROM tblBedrijven b
        WHERE b.ai_enriched_at IS NULL
        ORDER BY b.created_at DESC
        LIMIT %s
    """
    conn = mysql.connector.connect(**_db_config())
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
    finally:
        conn.close()

    results = [row for row in rows if row.get("vacature_tekst")]
    return {"companies": results, "count": len(results)}


@router.post("/companies/upsert-profile")
def upsert_company_profile(payload: CompanyProfile) -> dict[str, Any]:
    conn = mysql.connector.connect(**_db_config())
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE tblBedrijven
                SET sector          = COALESCE(%s, sector),
                    ai_beschrijving = COALESCE(%s, ai_beschrijving),
                    tech_stack_json = %s,
                    machine_park_json = %s,
                    business_trigger = COALESCE(%s, business_trigger),
                    keywords_json   = %s,
                    ai_enriched_at  = CURRENT_TIMESTAMP,
                    updated_at      = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    payload.sector,
                    payload.ai_beschrijving,
                    json.dumps(payload.tech_stack) if payload.tech_stack else None,
                    json.dumps(payload.machine_park) if payload.machine_park else None,
                    payload.business_trigger,
                    json.dumps(payload.keywords) if payload.keywords else None,
                    payload.bedrijf_id,
                ),
            )
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Company not found")
        return {"status": "ok", "bedrijf_id": payload.bedrijf_id}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/sync")
def full_sync(aantal: int = 500) -> dict[str, Any]:
    import_result = update_vacancies(aantal=aantal)

    enrich_result: dict[str, Any] = {"status": "skipped"}
    if AI_SERVICE_URL:
        try:
            with httpx.Client(timeout=300.0) as client:
                res = client.post(f"{AI_SERVICE_URL}/enrich-new")
                enrich_result = res.json() if res.status_code == 200 else {"error": res.text}
        except Exception as e:
            enrich_result = {"error": str(e)}

    return {
        "import": import_result,
        "enrichment": enrich_result,
    }


def _raise_save_error(error: Exception) -> None:
    if isinstance(error, HTTPException):
        raise error

    message = str(error)
    lowered = message.lower()
    if (
        "tblsearchsessions" in lowered
        or "tblsearchresults" in lowered
        or "tblusers" in lowered
        or "foreign key" in lowered
        or "constraint" in lowered
        or "unknown column" in lowered
        or "doesn't exist" in lowered
    ):
        raise HTTPException(
            status_code=500,
            detail=(
                "Save schema/database mismatch. Check that the search session migrations ran, "
                "including init.sql, 007_fix_results_nullable.sql and 008_default_user.sql. "
                f"Original error: {message}"
            ),
        )

    raise HTTPException(status_code=500, detail=message)


@router.post("/searches/save")
def save_search(payload: SaveSearchRequest, infosearch_session: str | None = Cookie(default=None)) -> dict[str, Any]:
    user = _require_user(infosearch_session)
    item_type = _normalize_type(payload.type)
    session_type = SEARCH_SESSION_TYPE_MAP[item_type]
    conn = mysql.connector.connect(**_db_config())
    try:
        with conn.cursor() as cursor:
            title = payload.title or f"{item_type}: {payload.query[:80]}"
            cursor.execute(
                """
                INSERT INTO tblSearchSessions (user_id, type, title, input_text, filters_json, save_mode)
                VALUES (%s, %s, %s, %s, %s, 'whole')
                """,
                (
                    user.id,
                    session_type,
                    title,
                    payload.query,
                    json.dumps(payload.filters) if payload.filters else None,
                ),
            )
            search_id = cursor.lastrowid
            save_stats = _insert_saved_results(cursor, search_id, item_type, payload.results or [], user.id)
            conn.commit()
        return {"status": "ok", "search_id": search_id, "save_stats": save_stats}
    except Exception as e:
        conn.rollback()
        _raise_save_error(e)
    finally:
        conn.close()


@router.post("/searches/save-item")
def save_search_item(payload: SaveResultItemRequest, infosearch_session: str | None = Cookie(default=None)) -> dict[str, Any]:
    user = _require_user(infosearch_session)
    item_type = _normalize_type(payload.type)
    session_type = SEARCH_SESSION_TYPE_MAP[item_type]
    conn = mysql.connector.connect(**_db_config())
    try:
        with conn.cursor() as cursor:
            title = payload.title or f"{item_type}: {payload.query[:80]}"
            cursor.execute(
                """
                INSERT INTO tblSearchSessions (user_id, type, title, input_text, filters_json, save_mode)
                VALUES (%s, %s, %s, %s, %s, 'single')
                """,
                (
                    user.id,
                    session_type,
                    title,
                    payload.query,
                    json.dumps(payload.filters) if payload.filters else None,
                ),
            )
            search_id = cursor.lastrowid
            save_stats = _insert_saved_results(cursor, search_id, item_type, [payload.result], user.id)
            conn.commit()
        return {"status": "ok", "search_id": search_id, "save_stats": save_stats}
    except Exception as e:
        conn.rollback()
        _raise_save_error(e)
    finally:
        conn.close()


@router.get("/searches/saved")
def get_saved_searches(infosearch_session: str | None = Cookie(default=None)) -> dict[str, Any]:
    user = _require_user(infosearch_session)
    conn = mysql.connector.connect(**_db_config())
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(
                """
                SELECT s.id, s.type, s.title, s.input_text AS query, s.filters_json, s.created_at, s.save_mode
                FROM tblSearchSessions s
                WHERE s.user_id = %s
                  AND s.type IN ('company', 'job', 'bedrijf', 'vacature')
                  AND COALESCE(s.save_mode, 'whole') = 'whole'
                ORDER BY s.created_at DESC
                """,
                (user.id,),
            )
            sessions = cursor.fetchall()

            grouped_searches = {
                "company": [],
                "job": [],
            }
            for session in sessions:
                raw_type = session["type"]
                session_type = "company" if raw_type in {"bedrijf", "company"} else "job"
                session["type"] = session_type
                session["datum"] = session.pop("created_at").isoformat() if session.get("created_at") else None
                session["filters"] = json.loads(session.pop("filters_json")) if session.get("filters_json") else None
                session["resultUrl"] = f"/results/{session_type}?query={session['query']}"

                cursor.execute(
                    "SELECT id, search_id, explanation_json, `rank`, match_score, result_type, created_at FROM tblSearchResults WHERE search_id = %s ORDER BY `rank`",
                    (session["id"],),
                )
                result_rows = cursor.fetchall()
                session["results"] = [
                    {
                        **json.loads(row["explanation_json"]),
                        "saved_result_id": row["id"],
                        "saved_search_id": row["search_id"],
                    }
                    for row in result_rows
                ]
                grouped_searches[session_type].append(session)

            cursor.execute(
                """
                SELECT r.id, r.search_id, r.`rank`, r.match_score, r.result_type, r.explanation_json, r.created_at,
                       s.title AS search_title, s.input_text AS query
                FROM tblSearchResults r
                JOIN tblSearchSessions s ON s.id = r.search_id
                WHERE s.user_id = %s
                  AND s.type IN ('company', 'job', 'bedrijf', 'vacature')
                  AND COALESCE(s.save_mode, 'whole') = 'single'
                ORDER BY r.created_at DESC, r.`rank` ASC
                """,
                (user.id,),
            )
            saved_result_rows = cursor.fetchall()

            grouped_results = {
                "company": [],
                "job": [],
            }
            for row in saved_result_rows:
                mapped = _row_to_saved_result(row)
                grouped_results[mapped["type"]].append(mapped)

        return {
            "searches": grouped_searches,
            "results": grouped_results,
        }
    finally:
        conn.close()


@router.delete("/searches/saved/{search_id}")
def delete_saved_search(search_id: int, infosearch_session: str | None = Cookie(default=None)) -> dict[str, str]:
    user = _require_user(infosearch_session)
    conn = mysql.connector.connect(**_db_config())
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM tblSearchSessions WHERE id = %s AND user_id = %s", (search_id, user.id))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Search not found")
            cursor.execute("DELETE FROM tblSearchResults WHERE search_id = %s", (search_id,))
            cursor.execute("DELETE FROM tblSearchSessions WHERE id = %s AND user_id = %s", (search_id, user.id))
            conn.commit()
        return {"status": "deleted"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.delete("/searches/saved-item/{saved_result_id}")
def delete_saved_result(saved_result_id: int, infosearch_session: str | None = Cookie(default=None)) -> dict[str, str]:
    user = _require_user(infosearch_session)
    conn = mysql.connector.connect(**_db_config())
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT r.search_id
                FROM tblSearchResults r
                JOIN tblSearchSessions s ON s.id = r.search_id
                WHERE r.id = %s AND s.user_id = %s
                """,
                (saved_result_id, user.id),
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Saved result not found")
            search_id = row[0]

            cursor.execute("DELETE FROM tblSearchResults WHERE id = %s", (saved_result_id,))
            cursor.execute("SELECT COUNT(*) FROM tblSearchResults WHERE search_id = %s", (search_id,))
            remaining = cursor.fetchone()[0]
            if remaining == 0:
                cursor.execute("DELETE FROM tblSearchSessions WHERE id = %s AND user_id = %s", (search_id, user.id))
            conn.commit()
        return {"status": "deleted"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
