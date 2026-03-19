"""
Invoice PDF Generator for SEO Automation SaaS
"""
import os
import io
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

# Try to import reportlab for PDF generation
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm, cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logging.warning("reportlab not installed, PDF generation disabled")


class InvoiceGenerator:
    """Generate PDF invoices for subscriptions"""
    
    def __init__(self):
        self.company_name = "SEO Automation SaaS"
        self.company_address = "București, România"
        self.company_email = "billing@seoautomation.ro"
        self.company_cui = "RO12345678"  # Placeholder
    
    def generate_invoice(self, invoice_data: Dict[str, Any]) -> Optional[bytes]:
        """
        Generate a PDF invoice
        
        invoice_data should contain:
        - invoice_number: str
        - date: str (ISO format)
        - customer_name: str
        - customer_email: str
        - plan_name: str
        - billing_period: str (e.g., "monthly" or "annual")
        - amount: float
        - currency: str (default "EUR")
        - items: list of {description, quantity, unit_price, total}
        """
        if not REPORTLAB_AVAILABLE:
            logging.error("[INVOICE] reportlab not available, cannot generate PDF")
            return None
        
        buffer = io.BytesIO()
        
        # Create the PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Styles
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='InvoiceTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#00E676'),
            spaceAfter=20
        ))
        styles.add(ParagraphStyle(
            name='CompanyName',
            parent=styles['Normal'],
            fontSize=16,
            textColor=colors.HexColor('#333333'),
            fontName='Helvetica-Bold'
        ))
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#666666'),
            fontName='Helvetica-Bold',
            spaceBefore=15,
            spaceAfter=5
        ))
        styles.add(ParagraphStyle(
            name='RightAlign',
            parent=styles['Normal'],
            alignment=TA_RIGHT
        ))
        
        # Build content
        content = []
        
        # Header with company info
        content.append(Paragraph(self.company_name, styles['CompanyName']))
        content.append(Paragraph(self.company_address, styles['Normal']))
        content.append(Paragraph(f"Email: {self.company_email}", styles['Normal']))
        content.append(Paragraph(f"CUI: {self.company_cui}", styles['Normal']))
        content.append(Spacer(1, 20))
        
        # Invoice title and number
        content.append(Paragraph("FACTURĂ", styles['InvoiceTitle']))
        
        # Invoice details table
        invoice_date = invoice_data.get('date', datetime.now(timezone.utc).isoformat())
        if isinstance(invoice_date, str):
            try:
                invoice_date = datetime.fromisoformat(invoice_date.replace('Z', '+00:00'))
            except:
                invoice_date = datetime.now(timezone.utc)
        
        invoice_info = [
            ['Număr factură:', invoice_data.get('invoice_number', f'INV-{uuid.uuid4().hex[:8].upper()}')],
            ['Data emiterii:', invoice_date.strftime('%d.%m.%Y')],
            ['Perioadă facturare:', 'Anual' if invoice_data.get('billing_period') == 'annual' else 'Lunar'],
        ]
        
        info_table = Table(invoice_info, colWidths=[4*cm, 6*cm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#666666')),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        content.append(info_table)
        content.append(Spacer(1, 20))
        
        # Customer info
        content.append(Paragraph("FACTURAT CĂTRE:", styles['SectionHeader']))
        content.append(Paragraph(invoice_data.get('customer_name', 'Client'), styles['Normal']))
        content.append(Paragraph(invoice_data.get('customer_email', ''), styles['Normal']))
        content.append(Spacer(1, 20))
        
        # Items table
        content.append(Paragraph("DETALII SERVICII:", styles['SectionHeader']))
        
        items = invoice_data.get('items', [])
        if not items:
            # Default item based on plan
            billing_text = "anual" if invoice_data.get('billing_period') == 'annual' else "lunar"
            items = [{
                'description': f"Abonament {invoice_data.get('plan_name', 'Pro')} ({billing_text})",
                'quantity': 1,
                'unit_price': invoice_data.get('amount', 0),
                'total': invoice_data.get('amount', 0)
            }]
        
        # Create items table
        table_data = [['Descriere', 'Cant.', 'Preț unitar', 'Total']]
        for item in items:
            table_data.append([
                item['description'],
                str(item['quantity']),
                f"€{item['unit_price']:.2f}",
                f"€{item['total']:.2f}"
            ])
        
        items_table = Table(table_data, colWidths=[9*cm, 2*cm, 3*cm, 3*cm])
        items_table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00E676')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            # Body
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        content.append(items_table)
        content.append(Spacer(1, 20))
        
        # Total
        currency = invoice_data.get('currency', 'EUR').upper()
        total_amount = invoice_data.get('amount', 0)
        
        total_table_data = [
            ['Subtotal:', f"€{total_amount:.2f}"],
            ['TVA (0%):', '€0.00'],
            ['TOTAL:', f"€{total_amount:.2f}"],
        ]
        
        total_table = Table(total_table_data, colWidths=[13*cm, 4*cm])
        total_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('TEXTCOLOR', (1, -1), (1, -1), colors.HexColor('#00E676')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#00E676')),
        ]))
        content.append(total_table)
        content.append(Spacer(1, 30))
        
        # Footer notes
        content.append(Paragraph("NOTE:", styles['SectionHeader']))
        content.append(Paragraph(
            "Această factură a fost generată automat și este valabilă fără semnătură și ștampilă.",
            styles['Normal']
        ))
        content.append(Paragraph(
            f"Plata a fost procesată prin Stripe. Pentru întrebări: {self.company_email}",
            styles['Normal']
        ))
        
        # Build PDF
        doc.build(content)
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        logging.info(f"[INVOICE] Generated PDF invoice {invoice_data.get('invoice_number')}")
        return pdf_bytes
    
    async def save_invoice(self, db, user_id: str, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save invoice record to database"""
        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
        invoice_record = {
            "id": str(uuid.uuid4()),
            "invoice_number": invoice_number,
            "user_id": user_id,
            "plan_name": invoice_data.get('plan_name'),
            "billing_period": invoice_data.get('billing_period', 'monthly'),
            "amount": invoice_data.get('amount'),
            "currency": invoice_data.get('currency', 'EUR'),
            "status": "paid",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "pdf_generated": REPORTLAB_AVAILABLE
        }
        
        await db.invoices.insert_one(invoice_record)
        logging.info(f"[INVOICE] Saved invoice {invoice_number} for user {user_id}")
        
        return invoice_record


# Global invoice generator instance
invoice_generator = InvoiceGenerator()
