import socket
import ssl
import datetime
import dns.resolver
import requests

def check_ssl(domain):
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=3) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                not_after = datetime.datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                days_left = (not_after - datetime.datetime.utcnow()).days
                issuer = dict(x[0] for x in cert['issuer'])
                common_name = issuer.get('commonName', 'Unknown')
                return {"status": True, "days_left": days_left, "issuer": common_name}
    except:
        return {"status": False, "days_left": 0, "issuer": "Error"}

def check_ports(domain):
    # Ports critiques uniquement
    target_ports = [21, 22, 23, 3389, 8080] 
    open_ports = []
    try:
        ip = socket.gethostbyname(domain)
        for port in target_ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex((ip, port))
            if result == 0:
                open_ports.append(port)
            sock.close()
    except:
        pass
    return open_ports

def check_email_security(domain):
    try:
        answers = dns.resolver.resolve(f'_dmarc.{domain}', 'TXT')
        dmarc_record = str(answers[0])
        has_dmarc = "v=DMARC1" in dmarc_record
        return {"dmarc": has_dmarc}
    except:
        return {"dmarc": False}

def check_security_headers(domain):
    # Vérification des headers HTTP de sécurité
    try:
        # On tente de se connecter en HTTPS
        url = f"https://{domain}"
        response = requests.get(url, timeout=3)
        headers = response.headers
        
        # Points clés
        hsts = 'Strict-Transport-Security' in headers
        x_frame = 'X-Frame-Options' in headers
        csp = 'Content-Security-Policy' in headers
        
        # Si au moins HSTS ou X-Frame est là, on considère que c'est sécurisé pour le MVP
        is_secure = hsts or x_frame
        
        missing = []
        if not hsts: missing.append("HSTS")
        if not x_frame: missing.append("X-Frame")
        
        return {"status": is_secure, "hsts": hsts, "missing": missing}
    except:
        return {"status": False, "hsts": False, "missing": ["Unreachable"]}

def calculate_score(ssl_data, open_ports, email_data, headers_data):
    score = 0
    
    # 1. SSL (25 Pts)
    if ssl_data['status'] and ssl_data['days_left'] > 15:
        score += 25
    elif ssl_data['status']:
        score += 15

    # 2. Infrastructure (25 Pts)
    if len(open_ports) == 0:
        score += 25
    else:
        score += max(0, 25 - (len(open_ports) * 10))

    # 3. Email (25 Pts)
    if email_data['dmarc']:
        score += 25
        
    # 4. Headers (25 Pts)
    if headers_data['status']:
        score += 25
    # Bonus si HSTS est là
    if headers_data['status'] and not headers_data['hsts']: 
        score -= 5 # Petite pénalité si X-Frame est là mais pas HSTS
        
    return score

def run_full_scan(domain):
    domain = domain.replace("https://", "").replace("http://", "").replace("www.", "").split('/')[0]
    
    ssl_res = check_ssl(domain)
    ports_res = check_ports(domain)
    email_res = check_email_security(domain)
    headers_res = check_security_headers(domain)
    
    final_score = calculate_score(ssl_res, ports_res, email_res, headers_res)
    
    return {
        "domain": domain,
        "score": final_score,
        "ssl": ssl_res,
        "open_ports": ports_res,
        "email": email_res,
        "headers": headers_res
    }