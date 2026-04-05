"""
Generate patient-friendly PDF reports from encounter results.
Uses reportlab for PDF generation.
"""

from typing import Dict, Any, Optional
import tempfile
import os


class ReportService:
    """Generates patient-friendly PDF reports from encounter results."""

    def generate_report(
        self, results: Dict[str, Any], encounter: Any, encounter_id: str
    ) -> Dict[str, Any]:
        """Returns a dict representation of the report (for API)."""
        return {
            "encounter_id": encounter_id,
            "results_count": len(results),
            "motors_executed": list(results.keys()),
        }

    def generate_pdf(
        self,
        patient_name: str,
        encounter_date: str,
        results: Dict[str, Any],
        clinical_notes: Optional[str] = None,
        plan_of_action: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """Generate PDF report and return bytes."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.units import inch
            from reportlab.lib.colors import HexColor
            from reportlab.platypus import (
                SimpleDocTemplate,
                Paragraph,
                Spacer,
                Table,
                TableStyle,
                HRFlowable,
            )
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_CENTER
        except ImportError:
            raise RuntimeError("reportlab is required for PDF generation")

        buffer = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

        doc = SimpleDocTemplate(
            buffer.name,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )

        styles = getSampleStyleSheet()
        styles.add(
            ParagraphStyle(
                name="TitleCustom",
                parent=styles["Title"],
                fontSize=22,
                textColor=HexColor("#7c3aed"),
                spaceAfter=6,
            )
        )
        styles.add(
            ParagraphStyle(
                name="Subtitle",
                parent=styles["Normal"],
                fontSize=11,
                textColor=HexColor("#6b7280"),
                spaceAfter=20,
            )
        )
        styles.add(
            ParagraphStyle(
                name="SectionHeader",
                parent=styles["Heading2"],
                fontSize=14,
                textColor=HexColor("#1f2937"),
                spaceBefore=16,
                spaceAfter=8,
            )
        )
        styles.add(
            ParagraphStyle(
                name="ResultLabel",
                parent=styles["Normal"],
                fontSize=10,
                textColor=HexColor("#4b5563"),
            )
        )

        story = []

        # Header
        story.append(Paragraph("Integrum", styles["TitleCustom"]))
        story.append(Paragraph("Reporte de Evaluación Clínica", styles["Subtitle"]))
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#e5e7eb")))
        story.append(Spacer(1, 12))

        # Patient info
        story.append(
            Paragraph(f"<b>Paciente:</b> {patient_name}", styles["ResultLabel"])
        )
        story.append(
            Paragraph(f"<b>Fecha:</b> {encounter_date}", styles["ResultLabel"])
        )
        story.append(Spacer(1, 16))

        # Key results table
        story.append(Paragraph("Resultados Principales", styles["SectionHeader"]))

        key_findings = [["Evaluación", "Resultado"]]
        for motor_name, result in results.items():
            val = (
                result.get("calculated_value")
                or result.get("clinical_profile")
                or result.get("status", "")
            )
            if val and val not in ("N/A", "Bloqueado por V&V"):
                display_name = motor_name.replace("Motor", "")
                key_findings.append([display_name, str(val)])

        if len(key_findings) > 1:
            table = Table(key_findings, colWidths=[2.5 * inch, 3.5 * inch])
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#7c3aed")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#ffffff")),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 10),
                        ("FONTSIZE", (0, 1), (-1, -1), 9),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                        ("TOPPADDING", (0, 0), (-1, 0), 8),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [HexColor("#ffffff"), HexColor("#f9fafb")],
                        ),
                        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#e5e7eb")),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ]
                )
            )
            story.append(table)

        # Clinical notes
        if clinical_notes:
            story.append(Paragraph("Notas Clínicas", styles["SectionHeader"]))
            story.append(Paragraph(clinical_notes, styles["ResultLabel"]))

        # Plan
        if plan_of_action:
            story.append(Paragraph("Plan de Acción", styles["SectionHeader"]))
            summary = plan_of_action.get("summary", "")
            if summary:
                story.append(Paragraph(summary, styles["ResultLabel"]))

        # Footer
        story.append(Spacer(1, 40))
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#e5e7eb")))
        footer_style = ParagraphStyle(
            "Footer",
            parent=styles["Normal"],
            fontSize=8,
            textColor=HexColor("#9ca3af"),
            alignment=TA_CENTER,
        )
        story.append(
            Paragraph(
                "<i>Integrum — Medicina de Precisión en Obesidad</i>", footer_style
            )
        )
        story.append(
            Paragraph(
                "<i>Resultados interpretados por profesional de salud calificado</i>",
                footer_style,
            )
        )

        doc.build(story)

        with open(buffer.name, "rb") as f:
            pdf_bytes = f.read()

        os.unlink(buffer.name)
        return pdf_bytes


report_service = ReportService()
