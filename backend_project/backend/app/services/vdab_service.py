import os
import time
import requests
from requests.auth import HTTPBasicAuth
from app.services.json_cleaner import clean_vacature

def _get_vdab_config() -> tuple[str, str, str, str]:
    client_id = os.getenv("VDAB_CLIENT_ID", "").strip()
    client_secret = os.getenv("VDAB_CLIENT_SECRET", "").strip()
    api_key = os.getenv("VDAB_API_KEY", "").strip()
    vdab_host = os.getenv("VDAB_HOST", "op-derden.vdab.be").strip() or "op-derden.vdab.be"

    if not client_id or not client_secret:
        raise RuntimeError("Missing VDAB_CLIENT_ID / VDAB_CLIENT_SECRET env vars")
    if not api_key:
        raise RuntimeError("Missing VDAB_API_KEY env var")

    return client_id, client_secret, api_key, vdab_host


def _allow_fallback() -> bool:
    return os.getenv("VDAB_ALLOW_FALLBACK", "true").strip().lower() in {"1", "true", "yes", "on"}


def _is_rate_limited(response: requests.Response) -> bool:
    return response.status_code == 429


def _request_with_retry(url: str, headers: dict, params: dict | None = None, timeout: int = 20) -> requests.Response:
    retries = 3
    backoffs = [1, 2, 4]
    last_response = None

    for attempt in range(retries):
        response = requests.get(url, headers=headers, params=params, timeout=timeout)
        last_response = response
        if response.status_code != 429:
            return response
        if attempt < retries - 1:
            time.sleep(backoffs[attempt])

    return last_response


def _fallback_raw_vacature() -> dict:
    return {
        "vacatureReferentie": {
            "interneReferentie": "fallback-9f7886a8-236b-4068-bf02-f03a773f3b4d",
            "vdabReferentie": 51489354,
        },
        "status": "GEPUBLICEERD",
        "publicatieDatum": "2012-03-28",
        "bron": "VDAB_VACATURE_OPENING",
        "internationaalOpengesteld": True,
        "functie": {
            "functieTitel": "Technisch verkoopsadviseur",
            "jobdomeinen": [{"label": "Verkoop"}],
            "beroepsprofiel": {
                "label": "Vertegenwoordiger",
                "ervaring": {"label": "Beperkte ervaring ( < 2 jaar )"},
            },
            "omschrijving": "Als technisch verkoopsadviseur bent u verantwoordelijk voor het actief prospecteren.",
        },
        "vrijeVereiste": "Commerciele instelling, flexibiliteit en basis Office-kennis.",
        "arbeidsovereenkomst": {
            "arbeidsContract": {"label": "Werfreserve"},
            "arbeidsRegime": {"label": "voltijds"},
            "arbeidsStelsel": [{"label": "Dagwerk"}],
            "aantalUur": None,
            "vermoedelijkeStartdatum": None,
            "minimumBrutoLoon": None,
            "maximumBrutoLoon": None,
            "extra": "Uitdagende job met bedrijfswagen, laptop en GSM.",
        },
        "tewerkstellingsadres": {
            "postcode": "7700",
            "gemeente": "MOESKROEN",
            "provincie": {"label": "Provincie Henegouwen"},
            "locatie": {"latitude": 50.7441471, "longitude": 3.2548545},
        },
        "leverancier": {
            "naam": "Van Tuning Center bvba",
            "kboNummer": "0862409974",
            "type": "GEWONE_BEDRIJVEN",
        },
        "sollicitatieprocedure": {
            "cvGewenst": True,
            "sollicitatieVia": {
                "email": "jl.matton@vtc.be",
                "webformulier": None,
                "telefoon": None,
            },
        },
        "profiel": {
            "vereisten": [
                {"type": "talen", "label": "Nederlands", "score": {"label": "goed"}},
                {"type": "talen", "label": "Frans", "score": {"label": "zeer goed"}},
                {"type": "rijbewijs", "code": "B"},
                {"type": "studie", "diplomaNiveau": {"label": "Geen"}},
            ]
        },
    }

def _get_access_token() -> str:
    client_id, client_secret, _, vdab_host = _get_vdab_config()
    token_url = f"https://{vdab_host}/isam/sps/oauth/oauth20/token"

    r = requests.post(
        token_url,
        data={"grant_type": "client_credentials"},
        auth=HTTPBasicAuth(client_id, client_secret),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=20,
    )

    # Belangrijk: toon echte fout van VDAB/ISAM
    if r.status_code != 200:
        raise RuntimeError(f"Token error {r.status_code}: {r.text}")

    return r.json()["access_token"]

def get_vacatures(aantal: int = 100) -> dict:    
    _, _, api_key, _ = _get_vdab_config()
    token = _get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "X-IBM-Client-Id": api_key,
    }
    url = "https://api.vdab.be/services/openservices/vacatures/v4/vacatures"

    all_results = []
    offset = 0
    page_size = min(aantal, 50)  # VDAB typically caps at 50 per request

    while len(all_results) < aantal:
        params = {"aantal": page_size, "offset": offset}
        r = _request_with_retry(url, headers=headers, params=params, timeout=30)
        if r.status_code == 200:
            page = r.json().get("resultaten", [])
            if not page:
                break
            all_results.extend(page)
            offset += len(page)
            if len(page) < page_size:
                break
        elif _is_rate_limited(r) and _allow_fallback():
            if not all_results:
                return {
                    "fallback": True,
                    "reason": "VDAB rate limit (429)",
                    "resultaten": [_fallback_raw_vacature()],
                }
            break  # keep what we have
        else:
            if not all_results:
                raise RuntimeError(f"Vacatures error {r.status_code}: {r.text}")
            break

    return {"resultaten": all_results}

def get_one_vacature_detail() -> dict:
    _, _, api_key, _ = _get_vdab_config()
    token = _get_access_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "X-IBM-Client-Id": api_key,
    }

    base_url = "https://api.vdab.be/services/openservices/vacatures/v4/vacatures"

    # Stap 1: haal 1 vacature op
    r = _request_with_retry(base_url, headers=headers, params={"aantal": 1}, timeout=20)
    if r.status_code == 429 and _allow_fallback():
        return clean_vacature(_fallback_raw_vacature())
    if r.status_code != 200:
        raise RuntimeError(f"List error {r.status_code}: {r.text}")

    data = r.json()
    interne_id = data["resultaten"][0]["vacatureReferentie"]["interneReferentie"]

    # Stap 2: haal volledige detail op
    detail_url = f"{base_url}/{interne_id}"
    detail = _request_with_retry(detail_url, headers=headers, timeout=20)
    if detail.status_code == 429 and _allow_fallback():
        return clean_vacature(_fallback_raw_vacature())
    if detail.status_code != 200:
        raise RuntimeError(f"Detail error {detail.status_code}: {detail.text}")


    raw = detail.json()
    return clean_vacature(raw)


def get_vacature_detail(interne_id: str) -> dict | None:
    _, _, api_key, _ = _get_vdab_config()
    token = _get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "X-IBM-Client-Id": api_key,
    }
    url = f"https://api.vdab.be/services/openservices/vacatures/v4/vacatures/{interne_id}"
    r = _request_with_retry(url, headers=headers, timeout=20)
    if r.status_code == 200:
        return r.json()
    if _is_rate_limited(r) and _allow_fallback():
        return _fallback_raw_vacature()
    return None