import calendar
import io
from datetime import date
from django.utils import timezone
from MyNewApp.models import Child, Attendance

# ── ReportLab Imports ──────────────────────────────────────────
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
)

# ── OpenPyXL Imports ───────────────────────────────────────────
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


def get_monthly_attendance_data(year: int, month: int):
    """
    Computes a full attendance grid and statistics for the given year and month.
    """
    num_days = calendar.monthrange(year, month)[1]
    month_name = calendar.month_name[month]

    children = Child.objects.all().order_by('last_name', 'first_name')
    attendances = Attendance.objects.filter(
        date__year=year,
        date__month=month
    ).select_related('child')

    # Mapping: (child_id, day_int) -> status ('Present' / 'Absent')
    att_dict = {(att.child_id, att.date.day): att.status for att in attendances}

    children_data = []
    class_daily_present = {d: 0 for d in range(1, num_days + 1)}
    class_daily_absent = {d: 0 for d in range(1, num_days + 1)}
    recorded_days_set = set()

    for idx, child in enumerate(children, start=1):
        day_records = []
        present_cnt = 0
        absent_cnt = 0

        for d in range(1, num_days + 1):
            st = att_dict.get((child.id, d))
            if st == 'Present':
                present_cnt += 1
                class_daily_present[d] += 1
                recorded_days_set.add(d)
                day_records.append({'day': d, 'code': 'P', 'status': 'Present'})
            elif st == 'Absent':
                absent_cnt += 1
                class_daily_absent[d] += 1
                recorded_days_set.add(d)
                day_records.append({'day': d, 'code': 'A', 'status': 'Absent'})
            else:
                day_records.append({'day': d, 'code': '—', 'status': 'None'})

        total_recorded = present_cnt + absent_cnt
        rate = round((present_cnt / total_recorded * 100), 1) if total_recorded > 0 else 0.0

        children_data.append({
            'num': idx,
            'child': child,
            'days': day_records,
            'present': present_cnt,
            'absent': absent_cnt,
            'total': total_recorded,
            'rate': rate,
        })

    # Overall statistics
    total_enrolled = len(children)
    male_count = sum(1 for c in children if c.gender.lower() == 'male')
    female_count = sum(1 for c in children if c.gender.lower() == 'female')
    total_present_all = sum(c['present'] for c in children_data)
    total_absent_all = sum(c['absent'] for c in children_data)
    total_recorded_all = total_present_all + total_absent_all
    overall_rate = round((total_present_all / total_recorded_all * 100), 1) if total_recorded_all > 0 else 0.0

    return {
        'year': year,
        'month': month,
        'month_name': month_name,
        'num_days': num_days,
        'days_range': list(range(1, num_days + 1)),
        'children_data': children_data,
        'total_enrolled': total_enrolled,
        'male_count': male_count,
        'female_count': female_count,
        'class_daily_present': class_daily_present,
        'class_daily_absent': class_daily_absent,
        'total_sessions_recorded': len(recorded_days_set),
        'total_present_all': total_present_all,
        'total_absent_all': total_absent_all,
        'overall_rate': overall_rate,
    }


def generate_attendance_excel(data, center_name="Child Development Center", user_name=""):
    """
    Generates an Excel workbook (.xlsx) formatted for Barangay CDC ECCD reporting.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Attendance {data['month_name'][:3]} {data['year']}"
    ws.views.sheetView[0].showGridLines = True

    # Styling Palettes
    primary_fill = PatternFill(start_color="1C4F40", end_color="1C4F40", fill_type="solid")
    sub_fill = PatternFill(start_color="E7F0EA", end_color="E7F0EA", fill_type="solid")
    header_fill = PatternFill(start_color="2A5245", end_color="2A5245", fill_type="solid")
    present_fill = PatternFill(start_color="EAF5EE", end_color="EAF5EE", fill_type="solid")
    absent_fill = PatternFill(start_color="FCE8E6", end_color="FCE8E6", fill_type="solid")
    gray_fill = PatternFill(start_color="F4F3EE", end_color="F4F3EE", fill_type="solid")

    font_title = Font(name="Calibri", size=15, bold=True, color="1C4F40")
    font_sub = Font(name="Calibri", size=10, bold=False, color="555555")
    font_meta = Font(name="Calibri", size=10, bold=True, color="1E2A26")
    font_tbl_hdr = Font(name="Calibri", size=9, bold=True, color="FFFFFF")
    font_bold = Font(name="Calibri", size=9, bold=True)
    font_data = Font(name="Calibri", size=9)
    font_present = Font(name="Calibri", size=9, bold=True, color="1C4F40")
    font_absent = Font(name="Calibri", size=9, bold=True, color="B7402C")

    thin_border_side = Side(border_style="thin", color="D8D3C4")
    tbl_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    thick_bottom = Border(bottom=Side(border_style="medium", color="1C4F40"))

    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")

    num_days = data['num_days']
    last_col_idx = 4 + num_days + 4  # No., ID, Name, Gender + days + Pres, Abs, Tot, Rate
    last_col_letter = get_column_letter(last_col_idx)

    # 1. Header Titles
    ws.merge_cells(f"A1:{last_col_letter}1")
    ws["A1"] = "BARANGAY EARLY CHILDHOOD CARE AND DEVELOPMENT (ECCD)"
    ws["A1"].font = font_sub
    ws["A1"].alignment = align_center

    ws.merge_cells(f"A2:{last_col_letter}2")
    ws["A2"] = center_name.upper()
    ws["A2"].font = font_title
    ws["A2"].alignment = align_center

    ws.merge_cells(f"A3:{last_col_letter}3")
    ws["A3"] = f"MONTHLY ATTENDANCE REPORT — {data['month_name'].upper()} {data['year']}"
    ws["A3"].font = font_meta
    ws["A3"].alignment = align_center

    # 2. Metadata Information Block
    row = 5
    ws[f"A{row}"] = "Center Name:"
    ws[f"B{row}"] = center_name
    ws[f"E{row}"] = "Reporting Period:"
    ws[f"G{row}"] = f"{data['month_name']} {data['year']}"
    for col in ["A", "E"]:
        ws[f"{col}{row}"].font = font_bold
    for col in ["B", "G"]:
        ws[f"{col}{row}"].font = font_data

    row += 1
    ws[f"A{row}"] = "Total Enrolled:"
    ws[f"B{row}"] = f"{data['total_enrolled']} (Male: {data['male_count']}, Female: {data['female_count']})"
    ws[f"E{row}"] = "Overall Attendance:"
    ws[f"G{row}"] = f"{data['overall_rate']}%"
    for col in ["A", "E"]:
        ws[f"{col}{row}"].font = font_bold
    for col in ["B", "G"]:
        ws[f"{col}{row}"].font = font_data

    row += 2  # Start table header at row 8
    tbl_start_row = row

    # Table Header Row 1
    headers = ["#", "Child ID", "Child's Full Name", "Sex"]
    for c_idx, h_text in enumerate(headers, start=1):
        cell = ws.cell(row=tbl_start_row, column=c_idx, value=h_text)
        cell.font = font_tbl_hdr
        cell.fill = primary_fill
        cell.alignment = align_center
        cell.border = tbl_border

    # Day columns (1..num_days)
    for d in range(1, num_days + 1):
        c_idx = 4 + d
        cell = ws.cell(row=tbl_start_row, column=c_idx, value=d)
        cell.font = font_tbl_hdr
        cell.fill = header_fill
        cell.alignment = align_center
        cell.border = tbl_border

    # Summary columns
    sum_headers = ["Present", "Absent", "Total", "Rate (%)"]
    for idx, h_text in enumerate(sum_headers, start=1):
        c_idx = 4 + num_days + idx
        cell = ws.cell(row=tbl_start_row, column=c_idx, value=h_text)
        cell.font = font_tbl_hdr
        cell.fill = primary_fill
        cell.alignment = align_center
        cell.border = tbl_border

    # Data Rows
    row = tbl_start_row + 1
    for item in data['children_data']:
        child = item['child']
        ws.cell(row=row, column=1, value=item['num']).alignment = align_center
        ws.cell(row=row, column=2, value=f"CDC-{child.id:04d}").alignment = align_center
        ws.cell(row=row, column=3, value=f"{child.last_name}, {child.first_name}").alignment = align_left
        ws.cell(row=row, column=4, value=child.gender[0].upper()).alignment = align_center

        for c_idx in range(1, 5):
            c = ws.cell(row=row, column=c_idx)
            c.font = font_data
            c.border = tbl_border

        # Days
        for d_info in item['days']:
            d_col = 4 + d_info['day']
            cell = ws.cell(row=row, column=d_col, value=d_info['code'])
            cell.alignment = align_center
            cell.border = tbl_border
            if d_info['code'] == 'P':
                cell.font = font_present
                cell.fill = present_fill
            elif d_info['code'] == 'A':
                cell.font = font_absent
                cell.fill = absent_fill
            else:
                cell.font = font_data

        # Stats
        c_pres = ws.cell(row=row, column=4 + num_days + 1, value=item['present'])
        c_abs = ws.cell(row=row, column=4 + num_days + 2, value=item['absent'])
        c_tot = ws.cell(row=row, column=4 + num_days + 3, value=item['total'])
        c_rate = ws.cell(row=row, column=4 + num_days + 4, value=f"{item['rate']}%")

        for c, f in [(c_pres, font_present), (c_abs, font_absent), (c_tot, font_bold), (c_rate, font_bold)]:
            c.alignment = align_center
            c.font = f
            c.border = tbl_border

        row += 1

    # Daily Present Totals row
    row_pres = row
    ws.cell(row=row_pres, column=1, value="")
    ws.cell(row=row_pres, column=2, value="")
    ws.cell(row=row_pres, column=3, value="Total Present per Day").alignment = align_right
    ws.cell(row=row_pres, column=3).font = font_bold
    ws.cell(row=row_pres, column=4, value="")

    for c_idx in range(1, 5):
        ws.cell(row=row_pres, column=c_idx).border = tbl_border
        ws.cell(row=row_pres, column=c_idx).fill = sub_fill

    for d in range(1, num_days + 1):
        d_col = 4 + d
        cell = ws.cell(row=row_pres, column=d_col, value=data['class_daily_present'][d])
        cell.alignment = align_center
        cell.font = font_present
        cell.border = tbl_border
        cell.fill = sub_fill

    # Total Present sum cell
    cell_tot_p = ws.cell(row=row_pres, column=4 + num_days + 1, value=data['total_present_all'])
    cell_tot_p.alignment = align_center
    cell_tot_p.font = font_present
    cell_tot_p.fill = sub_fill
    cell_tot_p.border = tbl_border

    for extra_col in range(4 + num_days + 2, last_col_idx + 1):
        c = ws.cell(row=row_pres, column=extra_col, value="")
        c.border = tbl_border
        c.fill = sub_fill

    row += 1

    # Daily Absent Totals row
    row_abs = row
    ws.cell(row=row_abs, column=3, value="Total Absent per Day").alignment = align_right
    ws.cell(row=row_abs, column=3).font = font_bold
    for c_idx in range(1, 5):
        ws.cell(row=row_abs, column=c_idx).border = tbl_border
        ws.cell(row=row_abs, column=c_idx).fill = sub_fill

    for d in range(1, num_days + 1):
        d_col = 4 + d
        cell = ws.cell(row=row_abs, column=d_col, value=data['class_daily_absent'][d])
        cell.alignment = align_center
        cell.font = font_absent
        cell.border = tbl_border
        cell.fill = sub_fill

    cell_tot_a = ws.cell(row=row_abs, column=4 + num_days + 2, value=data['total_absent_all'])
    cell_tot_a.alignment = align_center
    cell_tot_a.font = font_absent
    cell_tot_a.fill = sub_fill
    cell_tot_a.border = tbl_border

    for extra_col in [4 + num_days + 1, 4 + num_days + 3, 4 + num_days + 4]:
        c = ws.cell(row=row_abs, column=extra_col, value="")
        c.border = tbl_border
        c.fill = sub_fill

    row += 2

    # Legend Block
    ws.cell(row=row, column=1, value="LEGEND:").font = font_bold
    ws.cell(row=row, column=2, value="P = Present   |   A = Absent   |   — = No Session / Weekend / Holiday").font = font_sub
    row += 2

    # Signatures Block
    ws.cell(row=row, column=2, value="Prepared by:").font = font_bold
    ws.cell(row=row, column=18, value="Noted by:").font = font_bold
    row += 2
    ws.cell(row=row, column=2, value=user_name or "Child Development Worker").font = font_bold
    ws.cell(row=row, column=18, value="Barangay Chairman / ECCD Focal Person").font = font_bold
    row += 1
    ws.cell(row=row, column=2, value="Day Care Teacher").font = font_sub
    ws.cell(row=row, column=18, value="Barangay Council / ECCD Office").font = font_sub

    # Column Widths
    ws.column_dimensions["A"].width = 5
    ws.column_dimensions["B"].width = 13
    ws.column_dimensions["C"].width = 24
    ws.column_dimensions["D"].width = 6
    for d in range(1, num_days + 1):
        col_letter = get_column_letter(4 + d)
        ws.column_dimensions[col_letter].width = 4.2
    for idx in range(1, 5):
        col_letter = get_column_letter(4 + num_days + idx)
        ws.column_dimensions[col_letter].width = 9.5

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def generate_attendance_pdf(data, center_name="Child Development Center", user_name=""):
    """
    Generates a print-ready landscape PDF report for Barangay CDC reporting.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=0.4 * inch,
        rightMargin=0.4 * inch,
        topMargin=0.4 * inch,
        bottomMargin=0.4 * inch
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1C4F40'),
        alignment=1
    )
    sub_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#5B655F'),
        alignment=1
    )
    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#1E2A26'),
        alignment=1
    )

    elements = []

    # Title & Subheaders
    elements.append(Paragraph("REPUBLIC OF THE PHILIPPINES &bull; CITY GOVERNMENT OF ZAMBOANGA", sub_style))
    elements.append(Paragraph(center_name.upper(), title_style))
    elements.append(Paragraph(f"MONTHLY ATTENDANCE REGISTER &bull; {data['month_name'].upper()} {data['year']}", meta_style))
    elements.append(Spacer(1, 6))

    # Meta summary table
    meta_data = [
        [
            f"<b>Reporting Period:</b> {data['month_name']} {data['year']}",
            f"<b>Total Enrolled:</b> {data['total_enrolled']} (M: {data['male_count']}, F: {data['female_count']})",
            f"<b>Sessions Logged:</b> {data['total_sessions_recorded']} day(s)",
            f"<b>Overall Attendance Rate:</b> {data['overall_rate']}%"
        ]
    ]
    meta_table = Table(
        [[Paragraph(cell, styles['Normal']) for cell in meta_data[0]]],
        colWidths=[2.0 * inch, 2.5 * inch, 2.0 * inch, 2.5 * inch]
    )
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FAF8F3')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#D8D3C4')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 8))

    # Table of Attendance Grid
    num_days = data['num_days']
    header_row = ["#", "Child Name", "Sex"] + [str(d) for d in range(1, num_days + 1)] + ["P", "A", "Rate"]
    table_rows = [header_row]

    for item in data['children_data']:
        child = item['child']
        row = [
            str(item['num']),
            f"{child.last_name}, {child.first_name}",
            child.gender[0].upper()
        ]
        for d_info in item['days']:
            row.append(d_info['code'])
        row.append(str(item['present']))
        row.append(str(item['absent']))
        row.append(f"{item['rate']}%")
        table_rows.append(row)

    # Daily Present Totals
    p_row = ["", "Total Present", ""]
    for d in range(1, num_days + 1):
        p_row.append(str(data['class_daily_present'][d]))
    p_row += [str(data['total_present_all']), "", ""]
    table_rows.append(p_row)

    # Daily Absent Totals
    a_row = ["", "Total Absent", ""]
    for d in range(1, num_days + 1):
        a_row.append(str(data['class_daily_absent'][d]))
    a_row += ["", str(data['total_absent_all']), ""]
    table_rows.append(a_row)

    # Column Width calculations
    col_w_num = 0.25 * inch
    col_w_name = 1.65 * inch
    col_w_sex = 0.28 * inch
    col_w_day = 0.23 * inch
    col_w_p = 0.32 * inch
    col_w_a = 0.32 * inch
    col_w_rate = 0.52 * inch
    col_widths = [col_w_num, col_w_name, col_w_sex] + [col_w_day] * num_days + [col_w_p, col_w_a, col_w_rate]

    grid_table = Table(table_rows, colWidths=col_widths, repeatRows=1)
    grid_style = [
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 6.5),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1C4F40')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#D8D3C4')),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        # Totals rows
        ('BACKGROUND', (0, -2), (-1, -1), colors.HexColor('#E7F0EA')),
        ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
    ]

    # Colorize 'P' and 'A'
    for r_idx in range(1, len(data['children_data']) + 1):
        for c_idx in range(3, 3 + num_days):
            val = table_rows[r_idx][c_idx]
            if val == 'P':
                grid_style.append(('TEXTCOLOR', (c_idx, r_idx), (c_idx, r_idx), colors.HexColor('#1C4F40')))
                grid_style.append(('BACKGROUND', (c_idx, r_idx), (c_idx, r_idx), colors.HexColor('#EAF5EE')))
                grid_style.append(('FONTNAME', (c_idx, r_idx), (c_idx, r_idx), 'Helvetica-Bold'))
            elif val == 'A':
                grid_style.append(('TEXTCOLOR', (c_idx, r_idx), (c_idx, r_idx), colors.HexColor('#B7402C')))
                grid_style.append(('BACKGROUND', (c_idx, r_idx), (c_idx, r_idx), colors.HexColor('#FCE8E6')))
                grid_style.append(('FONTNAME', (c_idx, r_idx), (c_idx, r_idx), 'Helvetica-Bold'))

    grid_table.setStyle(TableStyle(grid_style))
    elements.append(grid_table)
    elements.append(Spacer(1, 8))

    # Legend & Signatures
    legend_text = "<b>LEGEND:</b> &nbsp;&nbsp; <b>P</b> = Present &nbsp;&bull;&nbsp; <b>A</b> = Absent &nbsp;&bull;&nbsp; <b>—</b> = No Session Recorded / Weekend / Holiday"
    elements.append(Paragraph(legend_text, sub_style))
    elements.append(Spacer(1, 14))

    sig_data = [
        [
            Paragraph("<b>Prepared by:</b><br/><br/><br/><b>" + (user_name or "Child Development Worker") + "</b><br/>Day Care Teacher / Worker", sub_style),
            Paragraph("<b>Noted by:</b><br/><br/><br/><b>HON. BARANGAY CHAIRMAN</b><br/>Barangay Council / ECCD Office", sub_style),
        ]
    ]
    sig_table = Table(sig_data, colWidths=[5.0 * inch, 5.0 * inch])
    elements.append(KeepTogether(sig_table))

    doc.build(elements)
    buf.seek(0)
    return buf
