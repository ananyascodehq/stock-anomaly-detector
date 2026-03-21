from fpdf import FPDF
import datetime

class AnomalyReportPDF(FPDF):
    def header(self):
        # Blue vertical bar
        self.set_fill_color(37, 99, 235)  # Blue-600
        self.rect(10, 10, 1.5, 12, 'F')
        
        # Title
        self.set_font("helvetica", "B", 22)
        self.set_text_color(15, 23, 42)  # Slate-900 
        self.set_xy(16, 10)
        self.cell(0, 10, "STOCK ANOMALY ANALYSIS REPORT", ln=True, align="L")
        
        # Subtitle
        self.set_font("helvetica", "B", 8)
        self.set_text_color(100, 116, 139)  # Slate-500
        self.set_xy(16, 21)
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cell(50, 5, f"GENERATED ON: {now}", align="L")
        
        self.set_text_color(59, 130, 246)  # Blue-500
        self.set_xy(70, 21)  # Fix overlap by hardcoding X position further right
        self.cell(40, 5, "SYSTEM STATUS: ACTIVE", ln=True, align="L")
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(148, 163, 184) # Slate-400
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}} | Confidential ML Monitoring Data", align="C")

def generate_anomaly_pdf(df, output_path):
    pdf = AnomalyReportPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # 2. Intro Text
    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(51, 65, 85) # Slate-700
    intro_txt_1 = "This report summarizes critical statistical deviations detected by the ensemble model across global equity markets. Utilizing a combination of "
    intro_txt_2 = "Isolation Forest"
    intro_txt_3 = " algorithms and rolling "
    intro_txt_4 = "Z-Score"
    intro_txt_5 = " analysis, the system identifies assets exhibiting non-linear volatility patterns and volume spikes that deviate from historical normative baselines."
    
    pdf.set_x(10)
    pdf.write(7, intro_txt_1)
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(37, 99, 235) # Blue-600
    pdf.write(7, intro_txt_2)
    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(51, 65, 85)
    pdf.write(7, intro_txt_3)
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(37, 99, 235)
    pdf.write(7, intro_txt_4)
    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(51, 65, 85)
    pdf.write(7, intro_txt_5)
    pdf.ln(14)
    
    # Outline box for the Table Area (to get rounded corners feel, just top bar for now)
    pdf.set_draw_color(226, 232, 240)
    pdf.set_fill_color(248, 250, 252) # Slate-50 header background
    table_y_start = pdf.get_y()
    
    pdf.rect(10, table_y_start, 190, 12, 'FD')
    pdf.rect(10, table_y_start, 190, 70, 'D') # Master outer container frame 

    # 4. Table Header (Global)
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(15, 23, 42)
    y_th = pdf.get_y() + 3
    pdf.set_xy(14, y_th)
    pdf.cell(50, 6, "DETECTED ANOMALIES RAW FEED")
    
    pdf.ln(11)
    
    # 5. Table Columns Row
    cols = ["TIMESTAMP", "TICKER", "Z-SCORE", "ISOFOREST SCORE", "ENSEMBLE", "STATUS"]
    col_widths = [45, 25, 25, 35, 30, 30]
    
    pdf.set_font("helvetica", "B", 7)
    pdf.set_text_color(100, 116, 139) # Slate-500
    
    y_start = pdf.get_y()
    x = 10
    for i, col in enumerate(cols):
        pdf.set_xy(x, y_start)
        # Offset center alignment manually for visuals
        pdf.cell(col_widths[i], 8, col, align="C" if i > 1 else "L")
        x += col_widths[i]
    pdf.ln(9)
    pdf.set_draw_color(226, 232, 240)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    
    # 6. Data Rows
    for _, row in df.iterrows():
        x = 10
        y_curr = pdf.get_y() + 4
        
        # TIMESTAMP
        pdf.set_xy(x+4, y_curr)
        pdf.set_font("helvetica", "B", 8)
        pdf.set_text_color(71, 85, 105) # Lighter slate
        pdf.cell(col_widths[0]-4, 6, str(row['timestamp']), align="L")
        x += col_widths[0]
        
        # TICKER
        pdf.set_xy(x-4, y_curr)
        pdf.set_text_color(15, 23, 42) # Slate-900 strong
        pdf.set_font("helvetica", "B", 9)
        pdf.cell(col_widths[1], 6, str(row['ticker']), align="L")
        x += col_widths[1]
        
        # Z-SCORE
        pdf.set_xy(x, y_curr)
        z_val = float(row['zscore_score'])
        if z_val >= 3.5:
            pdf.set_text_color(239, 68, 68) # Red-500
            pdf.set_fill_color(254, 226, 226) # Red-100
            pdf.set_xy(x + (col_widths[2]-15)/2, y_curr)
            pdf.cell(15, 6, f"{z_val:.2f}", align="C", fill=True)
        elif z_val >= 3.0:
            pdf.set_text_color(59, 130, 246) # Blue-500
            pdf.set_fill_color(219, 234, 254) # Blue-100
            pdf.set_xy(x + (col_widths[2]-15)/2, y_curr)
            pdf.cell(15, 6, f"{z_val:.2f}", align="C", fill=True)
        else:
            pdf.set_text_color(15, 23, 42)
            pdf.cell(col_widths[2], 6, f"{z_val:.2f}", align="C")
        x += col_widths[2]
        
        # ISOFOREST
        pdf.set_xy(x, y_curr)
        i_val = float(row['if_score'])
        if i_val >= 0.8:
            pdf.set_text_color(239, 68, 68) 
            pdf.set_fill_color(254, 226, 226) 
            pdf.set_xy(x + (col_widths[3]-15)/2, y_curr)
            pdf.cell(15, 6, f"{i_val:.2f}", align="C", fill=True)
        elif i_val >= 0.6:
            pdf.set_text_color(59, 130, 246) 
            pdf.set_fill_color(219, 234, 254) 
            pdf.set_xy(x + (col_widths[3]-15)/2, y_curr)
            pdf.cell(15, 6, f"{i_val:.2f}", align="C", fill=True)
        else:
            pdf.set_text_color(15, 23, 42)
            pdf.cell(col_widths[3], 6, f"{i_val:.2f}", align="C")
        x += col_widths[3]
        
        # ENSEMBLE
        pdf.set_xy(x, y_curr)
        e_val = float(row['ensemble_score'])
        pdf.set_text_color(15, 23, 42)
        pdf.set_font("helvetica", "B", 8)
        pdf.cell(col_widths[4], 6, f"{e_val:.2f}", align="C")
        x += col_widths[4]
        
        # STATUS
        pdf.set_xy(x, y_curr)
        is_flagged = row['is_flagged'] == 1
        
        if is_flagged:
            status = "ALERT"
            pdf.set_fill_color(239, 68, 68) # solid red
            pdf.set_text_color(255, 255, 255)
        else:
            status = "NORMAL"
            pdf.set_fill_color(241, 245, 249) # solid slate-100
            pdf.set_text_color(71, 85, 105) # Slate-600
            
        pdf.set_font("helvetica", "B", 7)
        pdf.set_xy(x + (col_widths[5]-18)/2, y_curr)
        pdf.cell(18, 6, status, align="C", fill=True)
        
        pdf.ln(11)
        pdf.set_draw_color(241, 245, 249) # Very light subtle divider
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        
        # Enforce page break with framing correctly if needed
        if pdf.get_y() > 270:
            pdf.add_page()
            
    # Redraw outer table border matching the height correctly
    pdf.set_draw_color(226, 232, 240)
    pdf.line(10, table_y_start, 10, pdf.get_y())
    pdf.line(200, table_y_start, 200, pdf.get_y())

    pdf.output(output_path)
    return output_path
