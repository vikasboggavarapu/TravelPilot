"""
TravelPilot — Export Service
Generates PDF trip reports using ReportLab.
"""

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT


# ── Colour palette ────────────────────────────────────────────────────────────
NAVY = colors.HexColor("#0A0E1A")
TEAL = colors.HexColor("#00D4AA")
GOLD = colors.HexColor("#FFB547")
LIGHT_GREY = colors.HexColor("#F5F5F5")
MID_GREY = colors.HexColor("#888888")


def generate_trip_pdf(trip: dict, itinerary: list, budget_summary: dict, bookings: list) -> bytes:
    """
    Generate a PDF trip dashboard.
    Returns PDF as bytes.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    story = []

    # ── Title ─────────────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        "Title", parent=styles["Title"],
        fontSize=24, textColor=NAVY, alignment=TA_CENTER, spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        "Sub", parent=styles["Normal"],
        fontSize=11, textColor=MID_GREY, alignment=TA_CENTER, spaceAfter=20
    )

    story.append(Paragraph("✈ TravelPilot Trip Report", title_style))
    story.append(Paragraph(
        f"{trip.get('destination', '')} | "
        f"{trip.get('start_date', '')} → {trip.get('end_date', '')} | "
        f"{trip.get('num_travelers', 1)} traveller(s)",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=TEAL))
    story.append(Spacer(1, 0.5 * cm))

    # ── Budget Summary ────────────────────────────────────────────────────────
    story.append(_section_header("💰 Budget Overview", styles))
    currency = budget_summary.get("currency", "USD")
    budget_data = [
        ["Category", "Estimated Cost"],
        ["Accommodation", f"{currency} {budget_summary.get('spent_accommodation', 0):.0f}"],
        ["Transport", f"{currency} {budget_summary.get('spent_transport', 0):.0f}"],
        ["Food & Dining", f"{currency} {budget_summary.get('spent_food', 0):.0f}"],
        ["Activities", f"{currency} {budget_summary.get('spent_activities', 0):.0f}"],
        ["TOTAL ESTIMATED", f"{currency} {budget_summary.get('total_estimated', 0):.0f}"],
        ["Budget Remaining", f"{currency} {budget_summary.get('remaining', 0):.0f}"],
    ]
    story.append(_styled_table(budget_data, col_widths=[10 * cm, 5 * cm]))
    story.append(Spacer(1, 0.5 * cm))

    # ── Bookings ──────────────────────────────────────────────────────────────
    if bookings:
        story.append(_section_header("🎫 Bookings", styles))
        booking_data = [["Type", "Provider", "Reference", "Status", "Cost"]]
        for b in bookings:
            booking_data.append([
                b.get("booking_type", "").title(),
                b.get("provider", "-"),
                b.get("reference_number", "-"),
                b.get("status", "").title(),
                f"{b.get('currency', currency)} {b.get('cost', 0):.0f}",
            ])
        story.append(_styled_table(booking_data, col_widths=[3 * cm, 4 * cm, 3.5 * cm, 2.5 * cm, 2 * cm]))
        story.append(Spacer(1, 0.5 * cm))

    # ── Day-by-day Itinerary ──────────────────────────────────────────────────
    story.append(_section_header("📅 Day-by-Day Itinerary", styles))

    day_header_style = ParagraphStyle(
        "DayH", parent=styles["Heading2"],
        fontSize=13, textColor=TEAL, spaceBefore=12, spaceAfter=4
    )
    act_style = ParagraphStyle(
        "Act", parent=styles["Normal"],
        fontSize=9, spaceAfter=2, leftIndent=10
    )
    tip_style = ParagraphStyle(
        "Tip", parent=styles["Normal"],
        fontSize=8, textColor=MID_GREY, spaceAfter=4, leftIndent=20
    )

    for day in itinerary:
        weather = day.get("weather_summary", "")
        story.append(Paragraph(
            f"Day {day['day_number']} — {day['date']} | {day.get('theme', '')}  {weather}",
            day_header_style
        ))

        if day.get("notes"):
            story.append(Paragraph(f"📝 {day['notes']}", tip_style))

        for act in day.get("activities", []):
            time_str = f"{act.get('start_time', '?')}–{act.get('end_time', '?')}"
            cost_str = f"${act.get('estimated_cost', 0):.0f}"
            status = "✓" if act.get("status") == "confirmed" else "⚠"
            story.append(Paragraph(
                f"{status} <b>{time_str}</b>: {act['name']} "
                f"({act.get('category', '').title()}) | {cost_str} | {act.get('location', '')}",
                act_style
            ))
            if act.get("tips"):
                story.append(Paragraph(f"💡 {act['tips'][:120]}", tip_style))

        story.append(Paragraph(
            f"Day total: ~{currency} {day.get('estimated_cost', 0):.0f}",
            ParagraphStyle("DayTotal", parent=styles["Normal"], fontSize=9,
                           textColor=GOLD, spaceAfter=8, leftIndent=10)
        ))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL))
    story.append(Paragraph(
        "Generated by TravelPilot — Your AI Travel Companion 🌍",
        ParagraphStyle("Footer", parent=styles["Normal"],
                       fontSize=8, textColor=MID_GREY, alignment=TA_CENTER, spaceBefore=6)
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def _section_header(text: str, styles) -> Paragraph:
    style = ParagraphStyle(
        "SH", parent=styles["Heading1"],
        fontSize=14, textColor=NAVY, spaceBefore=16, spaceAfter=6
    )
    return Paragraph(text, style)


def _styled_table(data: list, col_widths: list = None) -> Table:
    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT_GREY, colors.white]),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, MID_GREY),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        # Highlight total row
        ("FONTNAME", (0, -2), (-1, -2), "Helvetica-Bold"),
        ("BACKGROUND", (0, -2), (-1, -2), colors.HexColor("#E8F8F5")),
    ]))
    return table
