import re
from typing import Any, Dict, Optional, List

_TAG_RE = re.compile(r"<[^>]+>")

def strip_html(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    text = _TAG_RE.sub(" ", text)
    return " ".join(text.split()).strip()

def clean_vacature(raw: Dict[str, Any]) -> Dict[str, Any]:
    ref = raw.get("vacatureReferentie") or {}
    leverancier = raw.get("leverancier") or {}
    addr = raw.get("tewerkstellingsadres") or {}
    geo = addr.get("locatie") or {}

    functie = raw.get("functie") or {}
    beroep = (functie.get("beroepsprofiel") or {})
    ervaring = (beroep.get("ervaring") or {})
    arbeid = raw.get("arbeidsovereenkomst") or {}

    sollicitatie = raw.get("sollicitatieprocedure") or {}
    sollicitatie_via = sollicitatie.get("sollicitatieVia") or {}

    vereisten = ((raw.get("profiel") or {}).get("vereisten") or [])

    talen: List[Dict[str, Optional[str]]] = []
    rijbewijzen: List[Optional[str]] = []
    studies: List[Optional[str]] = []

    # extra’s voor matching (komen niet altijd voor, maar beter om nu al te ondersteunen)
    attesten: List[Dict[str, Optional[str]]] = []
    competenties: List[Dict[str, Optional[str]]] = []
    softskills: List[Dict[str, Optional[str]]] = []
    technische_competenties: List[Dict[str, Optional[str]]] = []
    vaardigheden: List[Dict[str, Optional[str]]] = []
    kennis: List[Dict[str, Optional[str]]] = []

    for v in vereisten:
        vtype = v.get("type")

        if vtype == "talen":
            score = v.get("score") or {}
            talen.append({
                "taal": v.get("label"),
                "niveau": score.get("label"),
            })

        elif vtype == "rijbewijs":
            rijbewijzen.append(v.get("code"))

        elif vtype == "studie":
            dn = v.get("diplomaNiveau") or {}
            studies.append(dn.get("label") or v.get("label"))

        elif vtype == "attest":
            attesten.append({"code": v.get("code"), "label": v.get("label")})

        elif vtype == "competentie":
            competenties.append({"code": v.get("code"), "label": v.get("label")})

        elif vtype == "softskill":
            softskills.append({"code": v.get("code"), "label": v.get("label")})

        elif vtype == "technischecompetentie":
            technische_competenties.append({"code": v.get("code"), "label": v.get("label")})

        elif vtype == "vaardigheid":
            vaardigheden.append({"code": v.get("code"), "label": v.get("label")})

        elif vtype == "kennis":
            kennis.append({"code": v.get("code"), "label": v.get("label")})

    return {
        "id": ref.get("interneReferentie"),
        "vdab_id": ref.get("vdabReferentie"),
        "status": raw.get("status"),
        "publicatieDatum": raw.get("publicatieDatum"),

        "meta": {
            "bron": raw.get("bron"),
            "internationaalOpengesteld": raw.get("internationaalOpengesteld"),
        },

        "job": {
            "titel": functie.get("functieTitel"),
            "jobdomeinen": [j.get("label") for j in (functie.get("jobdomeinen") or [])],
            "beroep": beroep.get("label"),
            "ervaring": ervaring.get("label"),
            "omschrijving": strip_html(functie.get("omschrijving")),
            "vrijeVereiste": strip_html(raw.get("vrijeVereiste")),
        },

        "contract": {
            "type": (arbeid.get("arbeidsContract") or {}).get("label"),
            "regime": (arbeid.get("arbeidsRegime") or {}).get("label"),
            "stelsel": [s.get("label") for s in (arbeid.get("arbeidsStelsel") or [])],

            "aantalUur": arbeid.get("aantalUur"),
            "vermoedelijkeStartdatum": arbeid.get("vermoedelijkeStartdatum"),
            "loon": {
                "minimumBrutoLoon": arbeid.get("minimumBrutoLoon"),
                "maximumBrutoLoon": arbeid.get("maximumBrutoLoon"),
            },
            "extra": strip_html(arbeid.get("extra")),
        },

        "locatie": {
            "postcode": addr.get("postcode"),
            "gemeente": addr.get("gemeente"),
            "provincie": (addr.get("provincie") or {}).get("label"),
            "geo": {
                "lat": geo.get("latitude"),
                "lon": geo.get("longitude"),
            },
        },

        "bedrijf": {
            "naam": leverancier.get("naam"),
            "kbo": leverancier.get("kboNummer"),
            "type": leverancier.get("type"),
        },

        "sollicitatie": {
            "cvGewenst": sollicitatie.get("cvGewenst"),
            "email": sollicitatie_via.get("email"),
            "webformulier": sollicitatie_via.get("webformulier"),
            "telefoon": sollicitatie_via.get("telefoon"),
        },

        "vereisten": {
            "talen": talen,
            "rijbewijzen": rijbewijzen,
            "studies": studies,

            "attesten": attesten,
            "competenties": competenties,
            "softSkills": softskills,
            "technischeCompetenties": technische_competenties,
            "vaardigheden": vaardigheden,
            "kennis": kennis,
        },
    }