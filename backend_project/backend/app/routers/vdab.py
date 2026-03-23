import json
import os
from typing import Any

import mysql.connector
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.vdab_service import get_vacatures, get_vacature_detail
from app.services.json_cleaner import clean_vacature

router = APIRouter(tags=["vacancies"])

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "")


class SearchRequest(BaseModel):
    query: str | None = None
    filters: dict[str, Any] | None = None
    details: dict[str, Any] | None = None


def _db_config() -> dict[str, Any]:
    return {
        "host": os.getenv("MYSQL_HOST", "mysql"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "database": os.getenv("MYSQL_DATABASE", "InfoSearch"),
        "user": os.getenv("MYSQL_USER", "user"),
        "password": os.getenv("MYSQL_PASSWORD", "pass"),
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
    """Search companies via their linked vacancies. Groups results by company."""
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

        # Filter on gemeente from the filters dict
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

        # Group by company
        companies: dict[int, dict[str, Any]] = {}
        for row in rows:
            bid = row["bedrijf_id"]
            if bid not in companies:
                companies[bid] = {
                    "id": bid,
                    "bedrijfsnaam": row["bedrijfsnaam"],
                    "kbo_nummer": row.get("kbo_nummer"),
                    "locatie": ", ".join(
                        p for p in [row.get("adres_gemeente") or row.get("gemeente"),
                                    row.get("adres_provincie") or row.get("provincie")]
                        if p
                    ),
                    "contactgegevens": " — ".join(
                        p for p in [row.get("bedrijf_email") or row.get("sollicitatie_email"),
                                    row.get("bedrijf_telefoon") or row.get("sollicitatie_telefoon"),
                                    row.get("website")]
                        if p
                    ),
                    "vacatures": [],
                }
            companies[bid]["vacatures"].append({
                "referentie": row["interne_referentie"],
                "titel": row["titel"],
                "beroep": row.get("beroep"),
                "gemeente": row.get("gemeente"),
                "contract_type": row.get("contract_type"),
                "ervaring": row.get("ervaring"),
                "omschrijving": (row.get("omschrijving") or "")[:300],
                "vrije_vereiste": (row.get("vrije_vereiste") or "")[:300],
                "publicatie_datum": str(row["publicatie_datum"]) if row.get("publicatie_datum") else None,
            })

        results = list(companies.values())
        return {
            "query": payload.query,
            "filters": payload.filters or {},
            "results": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _fetch_all_companies_with_vacatures() -> list[dict[str, Any]]:
    """Fetch all companies with their vacancies for AI analysis."""
    query = """
        SELECT
            b.id AS bedrijf_id, b.naam AS bedrijfsnaam, b.kbo_nummer,
            b.adres_gemeente, b.adres_provincie,
            b.email AS bedrijf_email, b.telefoon AS bedrijf_telefoon, b.website,
            v.interne_referentie, v.titel, v.beroep, v.omschrijving,
            v.vrije_vereiste, v.gemeente, v.provincie, v.contract_type,
            v.ervaring, v.sollicitatie_email, v.sollicitatie_telefoon
        FROM tblVacatures v
        JOIN tblBedrijven b ON v.bedrijf_id = b.id
        ORDER BY b.naam
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
                "sector": row.get("beroep") or "Onbekend",
                "locatie": ", ".join(
                    p for p in [row.get("adres_gemeente") or row.get("gemeente"),
                                row.get("adres_provincie") or row.get("provincie")] if p
                ),
                "contactgegevens": " — ".join(
                    p for p in [row.get("bedrijf_email") or row.get("sollicitatie_email"),
                                row.get("bedrijf_telefoon") or row.get("sollicitatie_telefoon"),
                                row.get("website")] if p
                ),
                "tech_stack": [],
                "vacatures": [],
            }
        companies[bid]["vacatures"].append(row.get("titel", ""))
        beroep = row.get("beroep")
        if beroep and beroep not in companies[bid]["tech_stack"]:
            companies[bid]["tech_stack"].append(beroep)
    return list(companies.values())


@router.post("/companies/prospect")
def company_prospect(payload: SearchRequest) -> dict[str, Any]:
    """AI-powered company prospecting. Delegates scoring to the AI service."""
    product = (payload.query or "").strip()
    if not product:
        raise HTTPException(status_code=400, detail="Product description required")

    try:
        bedrijven = _fetch_all_companies_with_vacatures()
        if not bedrijven:
            raise HTTPException(status_code=404, detail="No companies in database")

        ai_results = None

        # Call AI service
        if AI_SERVICE_URL:
            try:
                with httpx.Client(timeout=120.0) as client:
                    res = client.post(
                        f"{AI_SERVICE_URL}/generate-prospect",
                        params={"product": product},
                    )
                    if res.status_code == 200:
                        data = res.json()
                        ai_results = data.get("rapport")
            except Exception as e:
                print(f"AI service unreachable ({e}), using fallback...")

        # Fallback: heuristic scoring if AI service is unavailable
        if ai_results is None:
            ai_results = [
                {
                    "id": c["id"],
                    "bedrijfsnaam": c["naam"],
                    "sector": c.get("sector", "Onbekend"),
                    "locatie": c.get("locatie", ""),
                    "beschrijving": f"{c['naam']} heeft {len(c.get('vacatures', []))} actieve vacature(s).",
                    "waarom": "Score gebaseerd op beschikbare vacaturedata (AI niet beschikbaar).",
                    "score": min(10, len(c.get("vacatures", [])) * 2 + 3),
                    "contactgegevens": c.get("contactgegevens", "Niet beschikbaar"),
                    "techstack": c.get("tech_stack", []),
                }
                for c in bedrijven[:5]
            ]

        return {
            "query": product,
            "ai_powered": bool(AI_SERVICE_URL) and ai_results is not None,
            "results": ai_results if isinstance(ai_results, list) else [ai_results],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vacancies/update")
def update_vacancies(aantal: int = 100) -> dict[str, Any]:
    try:
        data = get_vacatures(aantal=aantal)
        raw_list = data.get("resultaten", [])
        is_fallback = data.get("fallback", False)

        conn = mysql.connector.connect(**_db_config())
        upserted = 0
        try:
            with conn.cursor() as cursor:
                for item in raw_list:
                    ref = (item.get("vacatureReferentie") or {})
                    interne_id = ref.get("interneReferentie")
                    if not interne_id:
                        continue

                    raw = get_vacature_detail(interne_id)
                    if not raw:
                        continue

                    cleaned = clean_vacature(raw)
                    if not cleaned["id"] or not cleaned["job"].get("titel"):
                        continue

                    bedrijf_id = None
                    kbo = cleaned["bedrijf"].get("kbo")
                    if kbo:
                        cursor.execute(
                            "INSERT INTO tblBedrijven (kbo_nummer, naam, type, "
                            "adres_postcode, adres_gemeente, adres_provincie, source_code) "
                            "VALUES (%s, %s, %s, %s, %s, %s, 'vdab') "
                            "ON DUPLICATE KEY UPDATE "
                            "naam=VALUES(naam), type=VALUES(type), "
                            "adres_postcode=COALESCE(VALUES(adres_postcode), adres_postcode), "
                            "adres_gemeente=COALESCE(VALUES(adres_gemeente), adres_gemeente), "
                            "adres_provincie=COALESCE(VALUES(adres_provincie), adres_provincie), "
                            "updated_at=CURRENT_TIMESTAMP",
                            (
                                kbo,
                                cleaned["bedrijf"].get("naam"),
                                cleaned["bedrijf"].get("type"),
                                cleaned["locatie"]["postcode"],
                                cleaned["locatie"]["gemeente"],
                                cleaned["locatie"]["provincie"],
                            ),
                        )
                        cursor.execute(
                            "SELECT id FROM tblBedrijven WHERE kbo_nummer = %s", (kbo,)
                        )
                        row = cursor.fetchone()
                        if row:
                            bedrijf_id = row[0]

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
            return {"upserted": upserted, "fetched": len(raw_list), "fallback": is_fallback}
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))