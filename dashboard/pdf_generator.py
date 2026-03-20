from fpdf import FPDF
import datetime

class AnomalyReportPDF(FPDF):
    def header(self):
        # Background color for header
        self.set_fill_color(24, 24, 27)
        self.rect(0, 0, 210, 40, 'F')
        
        # Title
        self.set_font("helvetica", "B", 24)
        self.set_text_color(6, 182, 212) # Neon Cyan
        self.cell(0, 20, "STOCK ANOMALY REPORT", ln=True, align="C")
        
        # Subtitle
        self.set_font("helvetica", "I", 10)
        self.set_text_color(161, 161, 170) # Zinc-400
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cell(0, 5, f"Generated on: {now} | System Status: ACTIVE", ln=True, align="C")
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(161, 161, 170)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}} | Confidential ML Monitoring Data", align="C")

def generate_anomaly_pdf(df, output_path):
    pdf = AnomalyReportPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Table Header
    pdf.set_fill_color(39, 39, 42) # Zinc-800
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    
    cols = ["Timestamp", "Ticker", "Z-Score", "IsoForest", "LSTM", "Ensemble", "Status"]
    col_widths = [45, 25, 23, 23, 23, 23, 28]
    
    for i in range(len(cols)):
        pdf.cell(col_widths[i], 10, cols[i], border=1, align="C", fill=True)
    pdf.ln()
    
    # Table Data
    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(39, 39, 42)
    
    for _, row in df.iterrows():
        # Alternating row colors? Maybe too complex for now, keep it clean.
        pdf.set_text_color(39, 39, 42)
        
        # If flagged, red text
        is_flagged = row['is_flagged'] == 1
        if is_flagged:
            pdf.set_text_color(244, 63, 94) # Rose-500
            
        pdf.cell(col_widths[0], 8, str(row['timestamp']), border=1, align="C")
        pdf.cell(col_widths[1], 8, str(row['ticker']), border=1, align="C")
        pdf.cell(col_widths[2], 8, f"{row['zscore_score']:.3f}", border=1, align="C")
        pdf.cell(col_widths[3], 8, f"{row['if_score']:.3f}", border=1, align="C")
        pdf.cell(col_widths[4], 8, f"{row['lstm_score']:.3f}", border=1, align="C")
        pdf.cell(col_widths[5], 8, f"{row['ensemble_score']:.3f}", border=1, align="C")
        
        status = "ALERT" if is_flagged else "NORMAL"
        pdf.cell(col_widths[6], 8, status, border=1, align="C")
        pdf.ln()

    pdf.output(output_path)
    return output_path
