"""
PDF Report Generation for Flight Summary.

Creates a PDF summary of flights grouped by month.
"""

import re
from datetime import datetime
from pathlib import Path

from .deps import ensure_reportlab

# Auto-install reportlab if needed
HAS_REPORTLAB = ensure_reportlab()

if HAS_REPORTLAB:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def parse_month_year(date_str):
    """Extract month and year from date string like 'April 28, 2025' or ISO date."""
    if not date_str:
        return ("Unknown", 9999, 0)

    # Try ISO format first (YYYY-MM-DD)
    iso_match = re.match(r'(\d{4})-(\d{2})-(\d{2})', date_str)
    if iso_match:
        year = int(iso_match.group(1))
        month_num = int(iso_match.group(2))
        month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December']
        month_name = month_names[month_num - 1] if 1 <= month_num <= 12 else 'Unknown'
        return (month_name, year, month_num)

    # Try "Month DD, YYYY" or "Month YYYY" formats
    match = re.match(r'(\w+)\s+\d{1,2}?,?\s*(\d{4})', date_str)
    if match:
        month_name = match.group(1)
        year = int(match.group(2))
        month_order = {
            'January': 1, 'February': 2, 'March': 3, 'April': 4,
            'May': 5, 'June': 6, 'July': 7, 'August': 8,
            'September': 9, 'October': 10, 'November': 11, 'December': 12
        }
        return (month_name, year, month_order.get(month_name, 0))

    match = re.match(r'(\w+)\s+(\d{4})', date_str)
    if match:
        month_name = match.group(1)
        year = int(match.group(2))
        month_order = {
            'January': 1, 'February': 2, 'March': 3, 'April': 4,
            'May': 5, 'June': 6, 'July': 7, 'August': 8,
            'September': 9, 'October': 10, 'November': 11, 'December': 12
        }
        return (month_name, year, month_order.get(month_name, 0))

    return ("Unknown", 9999, 0)


def group_flights_by_month(flights):
    """Group flights by month-year.

    Args:
        flights: List of flight dicts with flight_info containing dates

    Returns:
        Dict of (year, month_num, month_name) -> list of flights, sorted
    """
    from collections import defaultdict

    flights_by_month = defaultdict(list)

    for flight in flights:
        flight_info = flight.get("flight_info") or {}

        # Try ISO date first, then display dates
        iso_date = flight_info.get("iso_date")
        dates = flight_info.get("dates") or []
        date_str = iso_date or (dates[0] if dates else "")

        month_name, year, month_num = parse_month_year(date_str)
        key = (year, month_num, month_name)
        flights_by_month[key].append(flight)

    return dict(sorted(flights_by_month.items()))


def generate_pdf_report(flights, output_path, title="Flight Summary"):
    """Generate a PDF report of flights grouped by month.

    Args:
        flights: List of flight dicts
        output_path: Path to save the PDF
        title: Title for the report

    Returns:
        Path to the generated PDF or None on failure
    """
    from .airports import get_airport_display, VALID_AIRPORT_CODES

    if not flights:
        print("      No flights to include in PDF")
        return None

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not HAS_REPORTLAB:
        # Fall back to text report
        print("      (reportlab not available, generating text file instead)")
        return generate_text_report(flights, output_path.with_suffix('.txt'), title)

    # Group flights by month
    flights_by_month = group_flights_by_month(flights)

    if not flights_by_month:
        print("      No flights grouped by month")
        return None

    # Create PDF
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=20,
        alignment=1  # Center
    )

    month_style = ParagraphStyle(
        'MonthHeader',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=15,
        spaceAfter=10,
        textColor=colors.darkblue
    )

    story = []

    # Title
    story.append(Paragraph(title, title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
    story.append(Spacer(1, 20))

    # Summary stats
    total_flights = len(flights)
    total_months = len(flights_by_month)
    story.append(Paragraph(f"Total Flights: {total_flights} across {total_months} months", styles['Normal']))
    story.append(Spacer(1, 20))

    # Flights by month
    for (year, month_num, month_name), month_flights in flights_by_month.items():
        # Month header
        story.append(Paragraph(f"{month_name} {year} ({len(month_flights)} flights)", month_style))

        # Build table data
        table_data = [['Confirmation', 'Flight', 'Route', 'Date']]

        for flight in month_flights:
            flight_info = flight.get("flight_info") or {}
            conf = flight.get("confirmation") or "------"

            # Get flight number
            flight_nums = flight_info.get("flight_numbers") or []
            flight_num = flight_nums[0] if flight_nums else ""

            # Get route
            route_tuple = flight_info.get("route")
            airports = flight_info.get("airports") or []

            if route_tuple:
                valid_airports = list(route_tuple)
            else:
                valid_airports = [code for code in airports if code in VALID_AIRPORT_CODES]

            if len(valid_airports) >= 2:
                origin = valid_airports[0]
                dest = valid_airports[1]
                route = f"{origin} -> {dest}"
            elif valid_airports:
                route = valid_airports[0]
            else:
                route = ""

            # Get date
            dates = flight_info.get("dates") or []
            date_str = dates[0] if dates else ""

            table_data.append([conf, flight_num, route, date_str])

        # Create table
        table = Table(table_data, colWidths=[1.2*inch, 0.8*inch, 2.5*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))

        story.append(table)
        story.append(Spacer(1, 15))

    # Build PDF
    try:
        doc.build(story)
        return output_path
    except Exception as e:
        print(f"      Error generating PDF: {e}")
        # Fall back to text report
        return generate_text_report(flights, output_path.with_suffix('.txt'), title)


def generate_text_report(flights, output_path, title="Flight Summary"):
    """Generate a plain text report of flights grouped by month.

    Args:
        flights: List of flight dicts
        output_path: Path to save the text file
        title: Title for the report

    Returns:
        Path to the generated file or None on failure
    """
    from .airports import get_airport_display, VALID_AIRPORT_CODES

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    flights_by_month = group_flights_by_month(flights)

    lines = []
    lines.append("=" * 70)
    lines.append(f"  {title}")
    lines.append("=" * 70)
    lines.append(f"  Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    lines.append(f"  Total Flights: {len(flights)}")
    lines.append("")

    for (year, month_num, month_name), month_flights in flights_by_month.items():
        lines.append("")
        lines.append("=" * 70)
        lines.append(f"  {month_name.upper()} {year}  ({len(month_flights)} flights)")
        lines.append("=" * 70)
        lines.append("")

        for flight in month_flights:
            flight_info = flight.get("flight_info") or {}
            conf = flight.get("confirmation") or "------"

            flight_nums = flight_info.get("flight_numbers") or []
            flight_num = flight_nums[0] if flight_nums else ""

            route_tuple = flight_info.get("route")
            airports = flight_info.get("airports") or []

            if route_tuple:
                valid_airports = list(route_tuple)
            else:
                valid_airports = [code for code in airports if code in VALID_AIRPORT_CODES]

            if len(valid_airports) >= 2:
                origin = get_airport_display(valid_airports[0])
                dest = get_airport_display(valid_airports[1])
                route = f"{origin} -> {dest}"
            elif valid_airports:
                route = get_airport_display(valid_airports[0])
            else:
                route = ""

            dates = flight_info.get("dates") or []
            date_str = dates[0] if dates else ""

            lines.append(f"  {conf:<10} {flight_num:<8} {route}")
            if date_str:
                lines.append(f"             Date: {date_str}")
            lines.append("")

    lines.append("")
    lines.append("=" * 70)

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        return output_path
    except Exception as e:
        print(f"      Error generating report: {e}")
        return None
