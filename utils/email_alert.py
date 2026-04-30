import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from utils.database import listar_produtos, get_config_alertas

def _linhas_html(produtos, cor_fundo, cor_borda):
    html = ""
    for p in produtos:
        dias_txt = "VENCIDO" if p["dias_para_vencer"] < 0 else f"{p['dias_para_vencer']}d"
        html += f"""
        <tr style='background:{cor_fundo};'>
          <td style='padding:8px 12px;border-bottom:1px solid {cor_borda};font-weight:500;'>{p['nome']}</td>
          <td style='padding:8px 12px;border-bottom:1px solid {cor_borda};color:#555;'>{p['categoria']}</td>
          <td style='padding:8px 12px;border-bottom:1px solid {cor_borda};'>{p['quantidade']} {p['unidade']}</td>
          <td style='padding:8px 12px;border-bottom:1px solid {cor_borda};font-weight:700;color:#c0392b;'>{p['validade']}</td>
          <td style='padding:8px 12px;border-bottom:1px solid {cor_borda};font-weight:700;'>{dias_txt}</td>
        </tr>"""
    return html

def _tabela_html(titulo, cor_header, produtos, cor_fundo, cor_borda):
    if not produtos:
        return ""
    return f"""
    <h3 style='color:{cor_header};margin:24px 0 8px;'>{titulo} ({len(produtos)})</h3>
    <table style='width:100%;border-collapse:collapse;border-radius:8px;overflow:hidden;'>
      <thead>
        <tr style='background:{cor_header};color:white;'>
          <th style='padding:10px 12px;text-align:left;'>Produto</th>
          <th style='padding:10px 12px;text-align:left;'>Categoria</th>
          <th style='padding:10px 12px;text-align:left;'>Estoque</th>
          <th style='padding:10px 12px;text-align:left;'>Validade</th>
          <th style='padding:10px 12px;text-align:left;'>Situação</th>
        </tr>
      </thead>
      <tbody>{_linhas_html(produtos, cor_fundo, cor_borda)}</tbody>
    </table>"""

def gerar_html_alerta(vencidos, criticos, dias_aviso):
    return f"""<!DOCTYPE html>
<html><head><meta charset='UTF-8'></head>
<body style='margin:0;padding:0;background:#f4f6f8;font-family:Inter,Arial,sans-serif;'>
  <div style='max-width:680px;margin:30px auto;background:white;border-radius:16px;
              overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.10);'>
    <div style='background:linear-gradient(135deg,#0f2318,#2d6a4f);padding:32px;text-align:center;'>
      <div style='font-size:40px;'>📦</div>
      <h1 style='color:white;margin:8px 0 4px;font-size:24px;'>SmartLarder Pro</h1>
      <p style='color:#95d5b2;margin:0;font-size:14px;'>Relatório de Alertas — {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
    </div>
    <div style='padding:28px 32px;'>
      <div style='display:flex;gap:16px;margin-bottom:24px;'>
        <div style='flex:1;background:#fde8e8;border-radius:10px;padding:16px;text-align:center;'>
          <div style='font-size:28px;font-weight:800;color:#e74c3c;'>{len(vencidos)}</div>
          <div style='font-size:13px;color:#7a0000;'>🚨 Vencidos</div>
        </div>
        <div style='flex:1;background:#fff3cd;border-radius:10px;padding:16px;text-align:center;'>
          <div style='font-size:28px;font-weight:800;color:#e67e22;'>{len(criticos)}</div>
          <div style='font-size:13px;color:#7a4500;'>⚠️ Vencem em ≤{dias_aviso}d</div>
        </div>
      </div>
      {_tabela_html("🚨 Produtos Vencidos","#e74c3c",vencidos,"#fff8f8","#fde0e0")}
      {_tabela_html("⚠️ Vencem em Breve","#e67e22",criticos,"#fffbf0","#fdecc8")}
      <p style='color:#aaa;font-size:12px;text-align:center;margin-top:28px;border-top:1px solid #eee;padding-top:16px;'>
        E-mail automático do <strong>SmartLarder Pro</strong>. Acesse o sistema para mais detalhes.
      </p>
    </div>
  </div>
</body></html>"""

def enviar_alerta_email(forcar=False) -> tuple[bool, str]:
    config = get_config_alertas()
    if not config.get("enviar_email") and not forcar:
        return False, "Envio de e-mail desativado nas configurações."
    if not config.get("email_destino"):
        return False, "E-mail de destino não configurado."
    if not config.get("smtp_usuario") or not config.get("smtp_senha"):
        return False, "Credenciais SMTP não configuradas."

    dias = config.get("dias_aviso", 7)
    todos    = listar_produtos()
    vencidos = [p for p in todos if p["status"] == "vencido"]
    criticos = [p for p in todos if p["status"] == "critico"]

    if not vencidos and not criticos:
        return True, "Nenhum produto crítico. E-mail não enviado."

    html = gerar_html_alerta(vencidos, criticos, dias)
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"⚠️ SmartLarder: {len(vencidos)} vencidos, {len(criticos)} críticos"
        msg["From"]    = config["smtp_usuario"]
        msg["To"]      = config["email_destino"]
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(config.get("smtp_host","smtp.gmail.com"),
                          int(config.get("smtp_porta", 587))) as srv:
            srv.starttls()
            srv.login(config["smtp_usuario"], config["smtp_senha"])
            srv.sendmail(config["smtp_usuario"], config["email_destino"], msg.as_string())
        return True, f"E-mail enviado para {config['email_destino']}!"
    except smtplib.SMTPAuthenticationError:
        return False, "Falha de autenticação. Use uma Senha de App do Google."
    except Exception as e:
        return False, f"Erro ao enviar: {e}"
