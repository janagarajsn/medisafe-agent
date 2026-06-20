from urllib.parse import quote

import requests

_OPENFDA_BASE = "https://api.fda.gov/drug"
_TIMEOUT = 10


def check_drug_interactions(drug1: str, drug2: str) -> dict:
    """Check for known interactions between two medications using OpenFDA data.

    Searches the FDA drug label database for interaction warnings that mention
    the second drug in the first drug's label, and vice versa.

    Args:
        drug1: First medication name, e.g. "Warfarin".
        drug2: Second medication name, e.g. "Aspirin".

    Returns:
        dict with ``interactions_found`` flag, detail list, and disclaimer.
    """
    try:
        found = []
        for primary, secondary in [(drug1, drug2), (drug2, drug1)]:
            url = (
                f"{_OPENFDA_BASE}/label.json"
                f"?search=drug_interactions:{quote(primary)}&limit=5"
            )
            resp = requests.get(url, timeout=_TIMEOUT)
            if resp.status_code != 200:
                continue
            for result in resp.json().get("results", []):
                for text in result.get("drug_interactions") or []:
                    if secondary.lower() in text.lower():
                        brand = (result.get("openfda") or {}).get("brand_name", [primary])
                        found.append({
                            "source_drug": brand[0] if brand else primary,
                            "interacts_with": secondary,
                            "excerpt": text[:500],
                        })

        if found:
            return {
                "interactions_found": True,
                "count": len(found),
                "details": found,
                "warning": (
                    f"Potential interaction(s) between {drug1} and {drug2} found in FDA data. "
                    "Consult your doctor or pharmacist before combining these medications."
                ),
                "disclaimer": "FDA label data only. Always follow your healthcare provider's guidance.",
            }

        return {
            "interactions_found": False,
            "message": (
                f"No documented interactions found between {drug1} and {drug2} in the FDA database."
            ),
            "disclaimer": (
                "Absence of a record does not guarantee safety. "
                "Always verify with your pharmacist or doctor."
            ),
        }

    except requests.Timeout:
        return {"checked": False, "message": "Request timed out. Please try again."}
    except Exception as exc:
        return {"checked": False, "message": f"Error checking interactions: {exc}"}


def get_drug_info(drug_name: str) -> dict:
    """Retrieve basic FDA information about a medication.

    Tries generic name first, then brand name as a fallback.

    Args:
        drug_name: Medication name, e.g. "metformin" or "Glucophage".

    Returns:
        dict with brand name, generic name, purpose, warnings, dosage.
    """
    try:
        for field in ("openfda.generic_name", "openfda.brand_name"):
            url = (
                f"{_OPENFDA_BASE}/label.json"
                f"?search={field}:{quote(drug_name)}&limit=1"
            )
            resp = requests.get(url, timeout=_TIMEOUT)
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                if results:
                    r = results[0]
                    openfda = r.get("openfda") or {}
                    return {
                        "found": True,
                        "brand_name": (openfda.get("brand_name") or ["Unknown"])[0],
                        "generic_name": (openfda.get("generic_name") or ["Unknown"])[0],
                        "manufacturer": (openfda.get("manufacturer_name") or ["Unknown"])[0],
                        "purpose": ((r.get("purpose") or ["Not specified"])[0])[:300],
                        "warnings": ((r.get("warnings") or ["Not available"])[0])[:500],
                        "dosage_and_administration": (
                            (r.get("dosage_and_administration") or ["Not available"])[0]
                        )[:400],
                        "disclaimer": (
                            "Information sourced from FDA drug labels. "
                            "Always follow your doctor's instructions."
                        ),
                    }

        return {"found": False, "message": f"No FDA records found for '{drug_name}'."}

    except requests.Timeout:
        return {"found": False, "message": "Request timed out. Please try again."}
    except Exception as exc:
        return {"found": False, "message": f"Error retrieving drug info: {exc}"}
