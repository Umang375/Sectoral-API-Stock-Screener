"""Predefined sector taxonomy and normalization logic for stock classification."""

import difflib

FALLBACK_SECTOR = "Diversified / Others"

PREDEFINED_SECTORS: list[str] = [
    "Agro Chemicals",
    "Alcoholic Beverages",
    "Alkali Chemicals",
    "Asset Management",
    "Auto Ancillary",
    "Auto OEM",
    "Aviation",
    "Banks",
    "Batteries",
    "Bearings",
    "Cement",
    "Chemicals",
    "City Gas",
    "Communication Equipment",
    "Dairy Products",
    "Defence",
    "Diagnostic Chains",
    "Dyes & Pigments",
    "Electrical Appliances",
    "EMS",
    "Fertilizer",
    "FMCG",
    "General Insurance",
    "Glass Products",
    "Holding Companies",
    "Home Finance",
    "Hospitality",
    "Hospitals",
    "Infrastructure",
    "Innerwear Manufacturers",
    "Insurance",
    "IT - Product/Platform",
    "IT Large Cap",
    "IT Mid Cap",
    "IT Small Cap",
    "IT/ITeS",
    "Jewellery",
    "Life Insurance",
    "Logistics",
    "Media & Entertainment",
    "Metal Pipes",
    "Metals",
    "Microfinance",
    "NBFC - Deposit -Taking",
    "NBFC - Non Deposit Taking",
    "Oil Refiners",
    "Packaged Meat",
    "Packaging and Containers",
    "Packaging Films",
    "Paint Manufacturers",
    "Paper & Board",
    "Pharma",
    "Pharma - API & CRAMS",
    "Pharma - Small Cap",
    "Pipe Manufacturers",
    "Plastic Pipes",
    "Plywood",
    "Polymers",
    "Power",
    "Private Bank",
    "PSU",
    "Public Bank",
    "QSR",
    "Railways",
    "Rating Agencies",
    "Real Estate",
    "Recycling",
    "Refractories",
    "Retail Chains",
    "Solar Panel Mfg",
    "Speciality Chemicals",
    "Sugar",
    "Telecom",
    "Textiles",
    "Tiles",
    "Transformers",
    "Tyre",
    "Upstream",
    "Wires & Cables",
    "Yarn",
    FALLBACK_SECTOR,
]

# Quick case-insensitive lookup
SECTOR_LOWERCASE_MAP: dict[str, str] = {
    s.lower().strip(): s for s in PREDEFINED_SECTORS
}


def normalize_sector(raw_sector: str | None) -> str:
    """Normalize and match a raw sector string to the predefined taxonomy.

    1. Checks for exact case-insensitive match.
    2. Performs fuzzy matching using difflib for slight typos/variations.
    3. Falls back to FALLBACK_SECTOR ("Diversified / Others") if unmatched.
    """
    if not raw_sector or not isinstance(raw_sector, str):
        return FALLBACK_SECTOR

    cleaned = raw_sector.strip()
    if not cleaned:
        return FALLBACK_SECTOR

    lower = cleaned.lower()

    # Exact match (case-insensitive)
    if lower in SECTOR_LOWERCASE_MAP:
        return SECTOR_LOWERCASE_MAP[lower]

    # Fuzzy match with confidence cutoff
    candidates = list(SECTOR_LOWERCASE_MAP.keys())
    matches = difflib.get_close_matches(lower, candidates, n=1, cutoff=0.7)
    if matches:
        return SECTOR_LOWERCASE_MAP[matches[0]]

    return FALLBACK_SECTOR


def format_sectors_for_prompt() -> str:
    """Format predefined sectors as a bulleted string for the Gemini prompt."""
    return "\n".join(f'- "{sector}"' for sector in PREDEFINED_SECTORS if sector != FALLBACK_SECTOR)
