import streamlit as st
from scanner_logic import run_full_scan
from fpdf import FPDF
import pandas as pd
import datetime
import time

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="CyberAudit", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

# --- CHARGEMENT CSS ---
def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"⚠️ Fichier {file_name} introuvable ! Vérifie qu'il est bien dans le même dossier.")

local_css("style.css")

# --- 2. INITIALISATION MEMOIRE ---
if 'history' not in st.session_state: st.session_state['history'] = []
if 'saved_author' not in st.session_state: st.session_state['saved_author'] = "CyberAudit"
if 'scan_count' not in st.session_state: st.session_state['scan_count'] = 0

# --- 3. SECURITÉ (LOGIN OK) ---
def check_password():
    def password_entered():
        entered_pwd = st.session_state["password"]
        if entered_pwd in st.secrets["passwords"]:
            st.session_state["password_correct"] = True
            st.session_state["username"] = st.secrets["passwords"][entered_pwd]
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("""
            <style>section[data-testid="stSidebar"] {display: none;}</style>
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 60vh; text-align: center;">
                <h1 style="font-size: 70px; font-weight: 800; margin-bottom: 0px; line-height: 1;">
                    <span style="color: #ffffff;">Cyber</span><span style="color:#3b82f6">Audit</span>
                </h1>
                <p style="color: #94a3b8; font-size: 22px; margin-top: 10px; font-weight: 500;">Espace Sécurisé Bêta</p>
                <div style="margin-top: 40px; width: 100%; max-width: 400px;">
        """, unsafe_allow_html=True)
            
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.text_input("Code d'accès", type="password", on_change=password_entered, key="password", label_visibility="collapsed", placeholder="Entrez votre code d'accès...")
            st.info("🔐 Accès restreint aux bêta-testeurs.")
        
        st.markdown("</div></div>", unsafe_allow_html=True)
        return False
    
    elif not st.session_state["password_correct"]:
        st.markdown("""<div style="text-align: center; margin-top: 150px;"><h1 style="font-size: 40px;">CyberAudit</h1></div>""", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.text_input("Code d'accès", type="password", on_change=password_entered, key="password", label_visibility="collapsed")
            st.error("😕 Code incorrect.")
        return False
    
    else:
        return True

if not check_password():
    st.stop()

# --- 4. UI HTML GENERATORS ---
def get_card_html(title, value, badge_text, badge_color, icon_name):
    border_color = "#3b82f6"
    bg_color = "#1e293b"
    return f"""
    <div style="background-color:{bg_color}; border:1px solid {border_color}40; border-radius:16px; padding:20px; height:170px; display:flex; flex-direction:column; justify-content:space-between; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); overflow: hidden;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px;">
            <div style="background:#334155; width:42px; height:42px; border-radius:10px; display:flex; align-items:center; justify-content:center; color:#fff;">
                <span class="material-icons-round" style="font-size:20px;">{icon_name}</span>
            </div>
            <span style="background:{badge_color}20; color:{badge_color}; padding:4px 10px; border-radius:20px; font-size:10px; font-weight:700; white-space: nowrap;">{badge_text}</span>
        </div>
        <div>
            <p style="color:#94a3b8; font-size:12px; font-weight:600; text-transform:uppercase; margin-bottom:5px; letter-spacing:0.5px;">{title}</p>
            <h2 style="color:#f8fafc; font-size:28px; font-weight:700; margin:0;">{value}</h2>
        </div>
    </div>
    """

def get_row_html(label, status, detail):
    color = "#10b981" if status else "#ef4444"
    icon = "check_circle" if status else "cancel"
    return f"""
    <div style="display:flex; align-items:center; justify-content:space-between; padding:16px 20px; background:#1e293b; border-radius:12px; margin-bottom:12px; border:1px solid #334155;">
        <div style="display:flex; align-items:center; gap:15px;">
            <span class="material-icons-round" style="color:{color}; font-size:20px;">{icon}</span>
            <span style="color:#f1f5f9; font-weight:600; font-size:15px;">{label}</span>
        </div>
        <span style="color:#94a3b8; font-size:13px; font-family:monospace;">{detail}</span>
    </div>
    """

# --- 5. FONCTION AUXILIAIRE D'AFFICHAGE VIP ---
def render_vip_stats(placeholder):
    count = st.session_state['scan_count']
    placeholder.markdown(f"""
        <div style="background: #1e293b; padding: 15px; border-radius: 12px; border: 1px solid #334155; margin-top: 20px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                <p style="color: #f1f5f9; font-weight: 600; font-size: 14px; margin:0;">Licence Bêta</p>
                <p style="color: #10b981; font-weight: 700; font-size: 12px; margin:0;">VIP</p>
            </div>
            <p style="font-size: 12px; margin:0 0 10px 0; color: #94a3b8;">
                Audits réalisés cette session : <strong style="color:white">{count}</strong>
            </p>
            <div style="height: 4px; background: #334155; border-radius: 2px; overflow:hidden;">
                <div style="height: 4px; background: linear-gradient(90deg, #3b82f6, #8b5cf6); width: 100%; border-radius: 2px;"></div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 6. PDF GENERATOR ---
class PDFReport(FPDF):
    def __init__(self, author_name="CyberAudit"):
        super().__init__()
        self.author_name = author_name

    def header(self):
        self.set_fill_color(15, 23, 42)
        self.rect(0, 0, 210, 50, 'F')
        self.set_y(20)
        self.set_font('Arial', 'B', 24)
        self.set_x(10)
        if self.author_name == "CyberAudit" or not self.author_name:
            self.set_text_color(255, 255, 255)
            w_cyber = self.get_string_width("Cyber")
            self.cell(w_cyber, 10, "Cyber", 0, 0)
            self.set_text_color(59, 130, 246)
            self.cell(0, 10, "Audit", 0, 0)
        else:
            self.set_text_color(255, 255, 255)
            self.cell(0, 10, self.author_name, 0, 0)
        self.set_font('Arial', '', 10)
        self.set_text_color(148, 163, 184)
        self.set_x(-70)
        self.cell(60, 10, f'Réf: AUDIT-{datetime.date.today().strftime("%Y%m%d")}', 0, 0, 'R')
        self.ln(40)

    def footer(self):
        self.set_y(-30)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(100, 116, 139)
        self.multi_cell(0, 4, f"Rapport généré par {self.author_name}. Ne remplace pas un pentest complet.", align='C')
        self.ln(2)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_pdf_bytes(data, author_name):
    pdf = PDFReport(author_name=author_name)
    pdf.add_page()
    
    # TITRE
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(15, 23, 42)
    pdf.write(10, "Rapport d'Audit")
    pdf.set_text_color(15, 23, 42)
    pdf.write(10, f" : {data['domain']}")
    pdf.ln(15)
    
    # DATE
    pdf.set_font("Arial", '', 11)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 10, f"Généré le {datetime.datetime.now().strftime('%d/%m/%Y à %H:%M')}", 0, 1)
    pdf.ln(10)
    
    # SCORE
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
    
    # SECTION TECH
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 10, "Analyse Technique", 0, 1)
    pdf.set_draw_color(226, 232, 240)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # --- METHODE SANS FONCTION (ANTI "NONE") ---
    
    # 1. SSL
    pdf.set_font("Arial", 'B', 11)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(120, 8, "SSL/TLS", 0, 0)
    ok = data['ssl']['status']
    pdf.set_text_color(21, 128, 61) if ok else pdf.set_text_color(185, 28, 28)
    pdf.cell(0, 8, "CONFORME" if ok else "ATTENTION", 0, 1, 'R')
    pdf.set_font("Arial", '', 10)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(0, 6, f"Résultat : Valide ({data['ssl'].get('days_left',0)} jours)", 0, 1)
    pdf.ln(2)
    pdf.set_draw_color(241, 245, 249)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    # 2. INFRA
    pdf.set_font("Arial", 'B', 11)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(120, 8, "Infrastructure", 0, 0)
    ok = len(data['open_ports'])==0
    pdf.set_text_color(21, 128, 61) if ok else pdf.set_text_color(185, 28, 28)
    pdf.cell(0, 8, "CONFORME" if ok else "ATTENTION", 0, 1, 'R')
    pdf.set_font("Arial", '', 10)
    pdf.set_text_color(71, 85, 105)
    res_txt = f"Ports: {data['open_ports']}" if data['open_ports'] else "Aucun port critique"
    pdf.cell(0, 6, f"Résultat : {res_txt}", 0, 1)
    pdf.ln(2)
    pdf.set_draw_color(241, 245, 249)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    # 3. EMAIL
    pdf.set_font("Arial", 'B', 11)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(120, 8, "Email DMARC", 0, 0)
    ok = data['email']['dmarc']
    pdf.set_text_color(21, 128, 61) if ok else pdf.set_text_color(185, 28, 28)
    pdf.cell(0, 8, "CONFORME" if ok else "ATTENTION", 0, 1, 'R')
    pdf.set_font("Arial", '', 10)
    pdf.set_text_color(71, 85, 105)
    res_txt = "Actif" if data['email']['dmarc'] else "Manquant"
    pdf.cell(0, 6, f"Résultat : {res_txt}", 0, 1)
    pdf.ln(2)
    pdf.set_draw_color(241, 245, 249)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    # 4. HEADERS
    pdf.set_font("Arial", 'B', 11)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(120, 8, "Sécurité Web (Headers)", 0, 0)
    ok = data['headers']['status']
    pdf.set_text_color(21, 128, 61) if ok else pdf.set_text_color(185, 28, 28)
    pdf.cell(0, 8, "CONFORME" if ok else "ATTENTION", 0, 1, 'R')
    pdf.set_font("Arial", '', 10)
    pdf.set_text_color(71, 85, 105)
    headers_txt = "Headers Sécurisés" if data['headers']['status'] else "Headers Manquants (HSTS/X-Frame)"
    pdf.cell(0, 6, f"Résultat : {headers_txt}", 0, 1)
    
    return pdf.output(dest='S').encode('latin-1')

# --- 6. SIDEBAR ---
with st.sidebar:
    st.markdown("""<div style="padding: 10px 0px;"><h2 style="margin:0; font-size: 22px; font-weight: 700;"><span style="color: #f1f5f9;">Cyber</span><span style="color:#3b82f6">Audit</span></h2></div>""", unsafe_allow_html=True)
    st.markdown("---")
    menu = st.radio("Navigation", ["Dashboard", "Mes Rapports", "Configuration"], label_visibility="collapsed")
    st.markdown("---")
    
    # FEEDBACK (VERSION SELECTBOX GARDÉE)
    st.markdown("### 🐛 Bêta Testeur ?")
    
    with st.expander("Un bug ? Une idée ?"):
        feedback_type = st.selectbox(
            "Type", 
            ["Bug 🐛", "Idée 💡", "Autre"], 
            label_visibility="collapsed"
        )
        
        feedback_msg = st.text_area("Message", placeholder="Décris le problème...", label_visibility="collapsed")
        
        if st.button("Envoyer le rapport 🚀", use_container_width=True):
            if feedback_msg:
                print(f"--- FEEDBACK ({feedback_type}) : {feedback_msg} ---")
                st.success("Merci ! Message reçu 5/5.")
                time.sleep(2)
                st.rerun()
            else:
                st.warning("Message vide.")

    st.markdown("---")
    
    # --- CORRECTION DISPARITION VIP ---
    # On crée le placeholder ET on l'affiche TOUT DE SUITE
    vip_placeholder = st.empty()
    render_vip_stats(vip_placeholder) # <--- C'est ça qui empêche la disparition pendant le chargement

# --- 7. PAGES LOGIC ---
if menu == "Dashboard":
    user_name = st.session_state.get("username", "Expert")
    st.markdown(f"""<div><h1 style="margin:0;">Bonjour, {user_name} 👋</h1><p style="margin-top: 5px; color: #94a3b8;">Voici l'état de vos analyses de sécurité aujourd'hui.</p></div><br>""", unsafe_allow_html=True)
    
    with st.form("scan_form", clear_on_submit=False):
        c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
        with c1:
            domain = st.text_input("Rechercher un domaine...", placeholder="ex: mon-client.com", label_visibility="collapsed")
        with c2:
            submitted = st.form_submit_button("Lancer l'audit ✨", type="primary", use_container_width=True)

    if submitted and domain:
        with st.spinner("Analyse intelligente en cours..."):
            time.sleep(0.5)
            data = run_full_scan(domain)
            st.session_state['scan_count'] += 1
            st.session_state['history'].insert(0, data)
            
            # MISE A JOUR DU COMPTEUR VIP APRES LE SCAN
            render_vip_stats(vip_placeholder)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"<h3>Résultats pour <span style='color:#3b82f6'>{domain}</span></h3>", unsafe_allow_html=True)
        
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
            details_headers = "Headers OK" if data['headers']['status'] else f"Manquant: {', '.join(data['headers']['missing'])}"
            st.markdown(get_row_html("Headers HTTP (HSTS/X-Frame)", data['headers']['status'], details_headers), unsafe_allow_html=True)

        with col_R:
            st.markdown("### Export")
            st.info("Le rapport client est prêt à être envoyé.")
            # Appel de la fonction "hardcodée" (sans sous-fonction)
            pdf_bytes = create_pdf_bytes(data, st.session_state['saved_author'])
            st.download_button("📥 Télécharger PDF", data=pdf_bytes, file_name=f"Audit_{domain}.pdf", mime="application/pdf", use_container_width=True)

elif menu == "Mes Rapports":
    st.title("Historique")
    if st.session_state['history']:
        df = pd.DataFrame(st.session_state['history'])
        st.dataframe(df[['domain', 'score']], use_container_width=True)
    else:
        st.info("Aucun audit récent.")

elif menu == "Configuration":
    st.title("⚙️ Paramètres")
    st.markdown("Personnalisez l'expérience CyberAudit.")
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container():
        st.markdown("### 🎨 Marque Blanche")
        st.info("Le nom que vous entrez ici remplacera 'CyberAudit' sur tous les rapports PDF générés.")
        current_name = st.session_state['saved_author']
        new_name = st.text_input("Nom de l'auteur / Agence", value=current_name)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Sauvegarder les modifications"):
            st.session_state['saved_author'] = new_name
            st.success(f"C'est noté ! Le nom **{new_name}** sera utilisé sur les prochains PDF.")
            time.sleep(1)
            st.rerun()
        st.info(f"Nom actuel utilisé sur le PDF : **{st.session_state['saved_author']}**")

# --- 8. EXECUTION FINALE ---
# IMPORTANT : On appelle la mise à jour une dernière fois pour être sûr
render_vip_stats(vip_placeholder)