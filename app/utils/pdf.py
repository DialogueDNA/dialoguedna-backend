from fpdf import FPDF

def generate_session_pdf(session: dict) -> str:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Session Title: {session['title']}", ln=True)
    pdf.cell(200, 10, txt=f"Summary: {session.get('summary', 'No summary available')}", ln=True)
    pdf.cell(200, 10, txt="Transcript:", ln=True)
    pdf.multi_cell(0, 10, txt=session.get("transcript", "No transcript available"))

    output_path = f"/tmp/session-{session['id']}.pdf"
    pdf.output(output_path)
    return output_path
