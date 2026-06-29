import json
import os

def load_cpi_data():
    """
    Loads monthly CPI reference data from the local JSON file
    inside graders/income_projection/cpi_monthly.json.
    Returns nested dict: data[year][month] = value
    """
    file_path = os.path.join(os.path.dirname(__file__), "cpi_monthly.json")
    with open(file_path, "r") as f:
        return json.load(f)


def get_cpi_value(year: int, month: str) -> float:
    """
    Retrieves CPI value for a specific year and month (e.g., get_cpi_value(2020, 'Jun')).
    Raises ValueError if year/month not found.
    """
    data = load_cpi_data()
    year_str = str(year)
    month_key = month.capitalize()[:3]

    if year_str not in data:
        raise ValueError(f"No CPI data found for year {year}")
    if month_key not in data[year_str]:
        raise ValueError(f"No CPI data found for month {month_key} in {year}")
    value = data[year_str][month_key]
    if value is None:
        raise ValueError(f"CPI data for {month_key} {year} is not yet available.")
    return value


def get_inflation_factor(year_start: int, month_start: str, year_end: int, month_end: str) -> float:
    """
    Calculates inflation factor = CPI_end / CPI_start.
    Example: get_inflation_factor(2020, 'Jun', 2025, 'Jun')
    """
    start = get_cpi_value(year_start, month_start)
    end = get_cpi_value(year_end, month_end)
    return round(end / start, 6)
