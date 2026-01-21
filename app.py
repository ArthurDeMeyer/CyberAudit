import streamlit as st
from scanner_logic import run_full_scan
from fpdf import FPDF
import pandas as pd
import datetime

# --- CONFIG ---
st.set_page_config(page_title="CyberAudit", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

# --- CSS LOAD ---
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
local_css("style.css")

# --- UI HTML GENERATORS ---
def get_card_html(title, value, badge_text, badge_color, icon_name):
    border_color = "#3758f9"
    bg_color = "#1a1d1f"
    return f"""
    <div style="background-color:{bg_color}; border:1px solid {border_color}; border-radius:16px; padding:24px; height:100%; display:flex; flex-direction:column; justify-content:space-between;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:15px;">
            <div style="background:#272b30; width:48px; height:48px; border-radius:12px; display:flex; align-items:center; justify-content:center; color:#fff;">
                <span class="material-icons-round" style="font-size:24px;">{icon_name}</span>
            </div>
            <span style="background:{badge_color}20; color:{badge_color}; padding:6px 12px; border-radius:20px; font-size:11px; font-weight:700;">{badge_text}</span>
        </div>
        <div>
            <p style="color:#94a3b8; font-size:13px; font-weight:600; text-transform:uppercase; margin-bottom:8px; letter-spacing:0.5px;">{title}</p>
            <h2 style="color:#fff; font-size:32px; font-weight:700; margin:0;">{value}</h2>
        </div>
    </div>
    """

def get_row_html(label, status, detail):
    color = "#10b981" if status else "#ef4444"
    icon = "check_circle" if status else "cancel"
    return f"""
    <div style="display:flex; align-items:center; justify-content:space-between; padding:16px 20px; background:#1a1d1f; border-radius:12px; margin-bottom:12px; border:1px solid #2f3336;">
        <div style="display:flex; align-items:center; gap:15px;">
            <span class="material-icons-round" style="color:{color}; font-size:20px;">{icon}</span>
            <span style="color:#e2e8f0; font-weight:600; font-size:15px;">{label}</span>
        </div>
        <span style="color:#94a3b8; font-size:13px; font-family:monospace;">{detail}</span>
    </div>
    """

# --- PDF GENERATOR ---
class PDFReport(FPDF):
    def header(self):
        self.set_fill_color(17, 24, 39)
        self.rect(0, 0, 210, 50, 'F')
        self.set_y(20)
        self.set_font('Arial', 'B', 24)
        self.set_x(10)
        
        self.set_text_color(255, 255, 255)
        w_cyber = self.get_string_width("Cyber")
        self.cell(w_cyber, 10, "Cyber", 0, 0)
        
        self.set_text_color(55, 88, 249)
        self.cell(0, 10, "Audit.io", 0, 0)
        
        self.set_font('Arial', '', 10)
        self.set_text_color(156, 163, 175)
        self.set_x(-70)
        self.cell(60, 10, f'Réf: AUDIT-{datetime.date.today().strftime("%Y%m%d")}', 0, 0, 'R')
        self.ln(40)

    def footer(self):
        self.set_y(-30)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(107, 114, 128)
        self.multi_cell(0, 4, "AVERTISSEMENT : Ce rapport est généré automatiquement. Il ne remplace pas un audit d'intrusion complet (Pentest).", align='C')
        self.ln(2)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_pdf_bytes(data):
    pdf = PDFReport()
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(17, 24, 39)
    pdf.write(10, "Rapport d'")
    pdf.set_text_color(17, 24, 39)
    pdf.write(10, "Audit")
    pdf.set_text_color(17, 24, 39)
    pdf.write(10, f" : {data['domain']}")
    pdf.ln(15)
    
    pdf.set_font("Arial", '', 11)
    pdf.set_text_color(107, 114, 128)
    pdf.cell(0, 10, f"Généré le {datetime.datetime.now().strftime('%d/%m/%Y à %H:%M')}", 0, 1)
    pdf.ln(10)
    
    if data['score'] >= 80: bg=(220,252,231); txt=(21,128,61); label="EXCELLENT"
    elif data['score'] >= 50: bg=(254,249,195); txt=(161,98,7); label="MOYEN"
    else: bg=(254,226,226); txt=(185,28,28); label="CRITIQUE"
    
    pdf.set_fill_color(*bg)
    pdf.rect(10, pdf.get_y(), 190, 35, 'F')
    pdf.set_y(pdf.get_y() + 5)
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(100,100,100)
    pdf.cell(0, 8, "SCORE DE SÉCURITÉ", 0, 1, 'C')
    pdf.set_font("Arial", 'B', 26)
    pdf.set_text_color(*txt)
    pdf.cell(0, 12, f"{data['score']} / 100", 0, 1, 'C')
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, label, 0, 1, 'C')
    pdf.ln(15)
    
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(17, 24, 39)
    pdf.cell(0, 10, "Analyse Technique", 0, 1)
    pdf.set_draw_color(229, 231, 235)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    def add_line(t, ok, r):
        pdf.set_font("Arial", 'B', 11)
        pdf.set_text_color(17, 24, 39)
        pdf.cell(120, 8, t, 0, 0)
        pdf.set_text_color(21, 128, 61) if ok else pdf.set_text_color(185, 28, 28)
        pdf.cell(0, 8, "CONFORME" if ok else "ATTENTION", 0, 1, 'R')
        pdf.set_font("Arial", '', 10)
        pdf.set_text_color(55, 65, 81)
        pdf.cell(0, 6, f"Résultat : {r}", 0, 1)
        pdf.ln(2)
        pdf.set_draw_color(243, 244, 246)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)

    add_line("SSL/TLS", data['ssl']['status'], f"Valide ({data['ssl'].get('days_left',0)} jours)")
    add_line("Infrastructure", len(data['open_ports'])==0, f"Ports: {data['open_ports']}" if data['open_ports'] else "Aucun port critique")
    add_line("Email DMARC", data['email']['dmarc'], "Actif" if data['email']['dmarc'] else "Manquant")
    # NOUVELLE LIGNE PDF POUR LES HEADERS
    headers_txt = "Headers Sécurisés" if data['headers']['status'] else "Headers Manquants (HSTS/X-Frame)"
    add_line("Sécurité Web (Headers)", data['headers']['status'], headers_txt)
    
    return pdf.output(dest='S').encode('latin-1')

# --- SESSION ---
if 'history' not in st.session_state: st.session_state['history'] = []

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("""
        <div style="padding: 10px 10px 30px 10px;">
            <h2 style="margin:0; font-size: 22px; font-weight: 700;">
                <span style="color: #ffffff;">Cyber</span><span style="color:#3758f9">Audit.io</span>
            </h2>
        </div>
    """, unsafe_allow_html=True)
    
    menu = st.radio("", ["Dashboard", "Mes Rapports", "Configuration"], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("""
        <div style="background: #1a1d1f; padding: 15px; border-radius: 12px; border: 1px solid #2f3336;">
            <p style="color: #fff; font-weight: 600; font-size: 14px; margin:0;">Plan Pro</p>
            <p style="font-size: 12px; margin:0 0 10px 0; color: #94a3b8;">Licence Active</p>
            <div style="height: 4px; background: #2f3336; border-radius: 2px;">
                <div style="height: 4px; background: #3758f9; width: 70%; border-radius: 2px;"></div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- DASHBOARD ---
if menu == "Dashboard":
    st.markdown("""
    <div>
        <h1 style="margin:0;">Bonjour, Expert 👋</h1>
        <p style="margin-top: 5px; color: #94a3b8;">Voici l'état de vos analyses de sécurité aujourd'hui.</p>
    </div>
    <br>
    """, unsafe_allow_html=True)
    
    with st.form("scan_form", clear_on_submit=False):
        c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
        with c1:
            domain = st.text_input("Rechercher un domaine...", placeholder="ex: mon-client.com", label_visibility="collapsed")
        with c2:
            submitted = st.form_submit_button("Lancer l'audit ✨", type="primary", use_container_width=True)

    if submitted and domain:
        with st.spinner("Analyse intelligente en cours..."):
            import time
            time.sleep(0.5)
            data = run_full_scan(domain)
            st.session_state['history'].insert(0, data)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"<h3>Résultats pour <span style='color:#3758f9'>{domain}</span></h3>", unsafe_allow_html=True)
        
        # 5 COLONNES MAINTENANT
        k1, k2, k3, k4, k5 = st.columns(5)
        
        with k1:
            color = "#10b981" if data['score'] >= 80 else "#ef4444"
            st.markdown(get_card_html("Score Global", f"{data['score']}%", "Excellent" if data['score']>=80 else "Critique", color, "verified_user"), unsafe_allow_html=True)
        with k2:
            color = "#10b981" if data['ssl']['status'] else "#ef4444"
            st.markdown(get_card_html("Certificat SSL", "Valide" if data['ssl']['status'] else "Expiré", f"{data['ssl'].get('days_left',0)} jours", color, "lock"), unsafe_allow_html=True)
        with k3:
            nb = len(data['open_ports'])
            color = "#10b981" if nb == 0 else "#ef4444"
            st.markdown(get_card_html("Ports Ouverts", str(nb), "Sécurisé", color, "router"), unsafe_allow_html=True)
        with k4:
            color = "#10b981" if data['email']['dmarc'] else "#f59e0b"
            st.markdown(get_card_html("Email DMARC", "Actif" if data['email']['dmarc'] else "Manquant", "Anti-Spoofing", color, "mark_email_read"), unsafe_allow_html=True)
        # NOUVELLE CARTE HEADERS
        with k5:
            color = "#10b981" if data['headers']['status'] else "#ef4444"
            status_txt = "Sécurisé" if data['headers']['status'] else "Risque"
            st.markdown(get_card_html("Sécurité Web", status_txt, "Headers", color, "shield"), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_L, col_R = st.columns([2, 1])
        
        with col_L:
            st.markdown("### Détails Techniques")
            st.markdown(get_row_html("Chiffrement SSL/TLS", data['ssl']['status'], f"Issuer: {data['ssl'].get('issuer', 'Unknown')}"), unsafe_allow_html=True)
            st.markdown(get_row_html("Pare-feu (Ports)", len(data['open_ports'])==0, "Aucun port critique détecté" if not data['open_ports'] else f"Ports: {data['open_ports']}"), unsafe_allow_html=True)
            st.markdown(get_row_html("Protection Email", data['email']['dmarc'], "Enregistrement DMARC présent" if data['email']['dmarc'] else "Risque d'usurpation"), unsafe_allow_html=True)
            # NOUVELLE LIGNE DETAILS
            details_headers = "Headers OK" if data['headers']['status'] else f"Manquant: {', '.join(data['headers']['missing'])}"
            st.markdown(get_row_html("Headers HTTP (HSTS/X-Frame)", data['headers']['status'], details_headers), unsafe_allow_html=True)

        with col_R:
            st.markdown("### Export")
            st.info("Le rapport client est prêt à être envoyé.")
            pdf_bytes = create_pdf_bytes(data)
            st.download_button("📥 Télécharger PDF", data=pdf_bytes, file_name=f"Audit_{domain}.pdf", mime="application/pdf", use_container_width=True)

elif menu == "Mes Rapports":
    st.title("Historique")
    if st.session_state['history']:
        df = pd.DataFrame(st.session_state['history'])
        st.dataframe(df[['domain', 'score']], use_container_width=True)
    else:
        st.info("Aucun audit récent.")