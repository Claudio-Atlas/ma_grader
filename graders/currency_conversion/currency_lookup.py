# currency_lookup.py

import re
import difflib

country_currency_dict = {
    "Afghanistan": "AFN",
    "Albania": "ALL",
    "Algeria": "DZD",
    "Angola": "AOA",
    "Argentina": "ARS",
    "Armenia": "AMD",
    "Aruba": "AWG",
    "Netherlands":"AWG",
    "Australia": "AUD",
    "Azerbaijan": "AZN",
    "Bahamas": "BSD",
    "Bahrain": "BHD",
    "Bangladesh": "BDT",
    "Barbados": "BBD",
    "Belarus": "BYN",
    "Belize": "BZD",
    "Bermuda": "BMD",
    "Bhutan": "BTN",
    "Bolivia": "BOB",
    "Bosnia and Herzegovina": "BAM",
    "Botswana": "BWP",
    "Brazil": "BRL",
    "Brunei": "BND",
    "Bulgaria": "BGN",
    "Burundi": "BIF",
    "Cabo Verde": "CVE",
    "Cambodia": "KHR",
    "Canada": "CAD",
    "Cayman Islands": "KYD",
    "Chile": "CLP",
    "China": "CNY",
    "Colombia": "COP",
    "Comoros": "KMF",
    "Congo": "CDF",
    "Costa Rica": "CRC",
    "Croatia": "EUR",
    "Cuba": "CUP",
    "Czechia": "CZK",
    "Denmark": "DKK",
    "Djibouti": "DJF",
    "Dominica": "XCD",
    "Dominican Republic": "DOP",
    "Egypt": "EGP",
    "El Salvador": "SVC",
    "Equatorial Guinea": "XAF",
    "Eritrea": "ERN",
    "Ethiopia": "ETB",
    "Falkland Islands": "FKP",
    "Fiji": "FJD",
    "France": "EUR",
    "Gambia": "GMD",
    "Georgia": "GEL",
    "Germany": "EUR",
    "Ghana": "GHS",
    "Gibraltar": "GIP",
    "Guatemala": "GTQ",
    "Guernsey": "GBP",
    "Guinea": "GNF",
    "Guyana": "GYD",
    "Haiti": "HTG",
    "Honduras": "HNL",
    "Hong Kong (China)": "HKD",
    "Hungary": "HUF",
    "Iceland": "ISK",
    "India": "INR",
    "Indonesia": "IDR",
    "International Monetary Fund": "XDR",
    "Iran": "IRR",
    "Iraq": "IQD",
    "Ireland": "EUR",
    "Israel": "ILS",
    "Italy": "EUR",
    "Ivory Coast": "XOF",
    "Jamaica": "JMD",
    "Japan": "JPY",
    "Jersey": "GBP",
    "Jordan": "JOD",
    "Kazakhstan": "KZT",
    "Kenya": "KES",
    "Kuwait": "KWD",
    "Kyrgyzstan": "KGS",
    "Laos": "LAK",
    "Lebanon": "LBP",
    "Liberia": "LRD",
    "Libya": "LYD",
    "Macau (China)": "MOP",
    "Madagascar": "MGA",
    "Malawi": "MWK",
    "Malaysia": "MYR",
    "Maldives": "MVR",
    "Mali": "XOF",
    "Malta": "EUR",
    "Mauritania": "MRU",
    "Mauritius": "MUR",
    "Mexico": "MXN",
    "Moldova": "MDL",
    "Mongolia": "MNT",
    "Morocco": "MAD",
    "Mozambique": "MZN",
    "Myanmar": "MMK",
    "Namibia": "NAD",
    "Nepal": "NPR",
    "Netherlands": "EUR",
    "New Zealand": "NZD",
    "Nicaragua": "NIO",
    "Nigeria": "NGN",
    "North Korea": "KPW",
    "North Macedonia": "MKD",
    "Norway": "NOK",
    "Oman": "OMR",
    "Pakistan": "PKR",
    "Palestine": "ILS",
    "Panama": "PAB",
    "Papua New Guinea": "PGK",
    "Paraguay": "PYG",
    "Peru": "PEN",
    "Philippines": "PHP",
    "Poland": "PLN",
    "Qatar": "QAR",
    "Romania": "RON",
    "Russia": "RUB",
    "Rwanda": "RWF",
    "Saint Helena": "SHP",
    "Samoa": "WST",
    "Sao Tome and Principe": "STN",
    "Saudi Arabia": "SAR",
    "Serbia": "RSD",
    "Seychelles": "SCR",
    "Sierra Leone": "SLL",
    "Singapore": "SGD",
    "Slovakia": "EUR",
    "Slovenia": "EUR",
    "Somalia": "SOS",
    "South Africa": "ZAR",
    "South Korea": "KRW",
    "Spain": "EUR",
    "Sri Lanka": "LKR",
    "Sudan": "SDG",
    "Suriname": "SRD",
    "Sweden": "SEK",
    "Switzerland": "CHF",
    "Syria": "SYP",
    "Taiwan": "TWD",
    "Tajikistan": "TJS",
    "Tanzania": "TZS",
    "Thailand": "THB",
    "Togo": "XOF",
    "Tonga": "TOP",
    "Trinidad and Tobago": "TTD",
    "Tunisia": "TND",
    "Turkey": "TRY",
    "Turkmenistan": "TMT",
    "Uganda": "UGX",
    "Ukraine": "UAH",
    "United Arab Emirates": "AED",
    "United Kingdom": "GBP",
    "Uruguay": "UYU",
    "Uzbekistan": "UZS",
    "Vanuatu": "VUV",
    "Venezuela": "VES",
    "Vietnam": "VND",
    "Wallis and Futuna": "XPF",
    "Yemen": "YER",
    "Zambia": "ZMW"
}
def _norm_country(s: str) -> str:
    """Lowercase, drop apostrophes/commas, collapse whitespace."""
    s = str(s).strip().lower().replace("'", "").replace(",", "")
    return re.sub(r"\s+", " ", s).strip()


def _strip_parenthetical(s: str) -> str:
    """Remove a trailing/inline qualifier in parentheses, e.g.
    'Hong Kong (China)' -> 'Hong Kong'."""
    return re.sub(r"\([^)]*\)", "", s).strip()


def get_country_entry_by_name(country_name: str):
    if not country_name:
        return None

    # Compare both the full name and a parenthetical-stripped version, so a
    # student typing "Hong Kong" matches the list entry "Hong Kong (China)".
    target = _norm_country(country_name)
    target_np = _norm_country(_strip_parenthetical(country_name))

    for name, code in country_currency_dict.items():
        full = _norm_country(name)
        no_paren = _norm_country(_strip_parenthetical(name))
        if target in (full, no_paren) or target_np in (full, no_paren):
            return {"country": name, "currency_code": code}

    return None


def resolve_country(name: str):
    """
    Resolve a typed country name to an approved entry, tolerating typos.

    Returns (entry_or_None, how) where `how` is "exact", "fuzzy", or None.
    The fuzzy match uses a tight cutoff so only obvious misspellings recover
    (e.g. "Venzuela" -> "Venezuela"), never a wild guess.
    """
    if not name or not str(name).strip():
        return None, None

    exact = get_country_entry_by_name(name)
    if exact:
        return exact, "exact"

    target = _norm_country(_strip_parenthetical(name))
    if not target:
        return None, None

    candidates = {_norm_country(_strip_parenthetical(c)): c for c in country_currency_dict}
    matches = difflib.get_close_matches(target, list(candidates.keys()), n=1, cutoff=0.84)
    if matches:
        canonical = candidates[matches[0]]
        return {"country": canonical, "currency_code": country_currency_dict[canonical]}, "fuzzy"

    return None, None

