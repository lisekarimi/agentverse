# date_server.py
from mcp.server.fastmcp import FastMCP
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import holidays
from dateutil import parser

mcp = FastMCP("date_server")

@mcp.tool()
async def parse_date_string(date_string: str) -> str:
    """Convert a natural language date to YYYY-MM-DD format.

    Args:
        date_string: Date in natural language (e.g., "Thursday 6 December", "Dec 25 2025")
    """
    try:
        parsed_date = parser.parse(date_string, dayfirst=False)
        return parsed_date.strftime("%Y-%m-%d")
    except Exception as e:
        return f"Could not parse date: {e}"

@mcp.tool()
async def get_current_date(format: str = "%Y-%m-%d") -> str:
    """Get the current date in a specific format.

    Args:
        format: The date format string (default: YYYY-MM-DD)

    Common formats:
        %Y-%m-%d → 2025-12-01
        %d/%m/%Y → 01/12/2025
        %B %d, %Y → December 01, 2025
        %A, %B %d, %Y → Monday, December 01, 2025
    """
    now = datetime.now()
    return now.strftime(format)


@mcp.tool()
async def get_date_by_offset(days: int = 0, weeks: int = 0, months: int = 0, years: int = 0, from_date: str = None) -> str:
    """Get a date by adding/subtracting time from a specific date or today.

    Args:
        days: Number of days to add/subtract
        weeks: Number of weeks to add/subtract
        months: Number of months to add/subtract
        years: Number of years to add/subtract
        from_date: Starting date in YYYY-MM-DD format (if None, uses today)

    Examples:
        days=1 → tomorrow
        days=1, from_date="2025-11-27" → the day after Nov 27
        weeks=2 → 2 weeks from now
        months=1, from_date="2025-12-25" → 1 month after Dec 25
    """
    if from_date:
        try:
            base = datetime.strptime(from_date, "%Y-%m-%d")
        except:
            return f"Invalid from_date format. Use YYYY-MM-DD"
    else:
        base = datetime.now()

    target_date = base + relativedelta(days=days, weeks=weeks, months=months, years=years)
    return target_date.strftime("%A, %Y-%m-%d")

@mcp.tool()
async def get_specific_weekday(weekday: str, occurrence: str = "next") -> str:
    """Get the date of a specific weekday (past or future).

    Args:
        weekday: Day of week (monday, tuesday, wednesday, thursday, friday, saturday, sunday)
        occurrence: "next" or "previous" (default: "next")
    """
    weekdays = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6
    }

    target_weekday = weekdays.get(weekday.lower())
    if target_weekday is None:
        return f"Invalid weekday: {weekday}"

    today = datetime.now()
    days_diff = target_weekday - today.weekday()

    if occurrence.lower() == "next":
        if days_diff <= 0:
            days_diff += 7
    elif occurrence.lower() == "previous":
        if days_diff >= 0:
            days_diff -= 7

    target_date = today + timedelta(days=days_diff)
    return target_date.strftime("%A, %Y-%m-%d")

@mcp.tool()
async def is_business_day(date_str: str, country_code: str = "US") -> str:
    """Check if a date is available for appointments (checks BOTH weekend AND holiday status).
    Use this tool when checking appointment availability.

    Args:
        date_str: Date in YYYY-MM-DD format
        country_code: Country code (US, FR, GB, MA, etc.)
    """
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        day_name = target_date.strftime("%A")

        # Check if weekend
        is_weekend = target_date.weekday() >= 5

        # Check if holiday
        country_holidays = holidays.country_holidays(country_code)
        is_holiday = target_date in country_holidays
        holiday_name = country_holidays.get(target_date, "")

        if is_weekend:
            return f"{date_str} ({day_name}) is a weekend - NOT available for appointments"
        elif is_holiday:
            return f"{date_str} ({day_name}) is a holiday ({holiday_name}) - NOT available for appointments"
        else:
            return f"{date_str} ({day_name}) is available for appointments"

    except ValueError as e:
        return f"Invalid date format: {e}"
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
async def get_holiday_date(holiday_name: str, year: int, country_code: str = "US") -> str:
    """Find the exact date of a specific holiday.

    Args:
        holiday_name: Name of the holiday (e.g., "Thanksgiving", "Christmas")
        year: Year to check
        country_code: Country code (default: US)
    """
    country_holidays = holidays.country_holidays(country_code, years=year)

    for date, name in country_holidays.items():
        if holiday_name.lower() in name.lower():
            return date.strftime("%A, %B %d, %Y")

    return f"{holiday_name} not found in {year}"

if __name__ == "__main__":
    mcp.run(transport='stdio')
