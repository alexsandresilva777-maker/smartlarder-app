# -*- coding: utf-8 -*-
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import pytz
from utils.database import listar_produtos, get_config_alertas

_TZ = pytz.timezone("America/Sao_Paulo")


def _now_br():
    return datetime.now(_TZ).strftime("%d/%m/%Y às %H:%M")


def _linhas(produtos, cor_fundo, cor_borda):
    html = ""
    for p in produtos:
        dias_txt = "VENCIDO" if p["dias_para_vencer"] < 0 else f"{p['dias_para_vencer']}d"
        html += f"""<tr style='background:{cor_fundo};'>
          <td style='padding:8px 12px;border-bottom:1px solid {cor_borda};font-weight:500;'>{p['nome']}</td>
          <td style='padding:8px 12px;border-bottom:1px solid {cor_borda};color:#555;'>{p['categoria']}</td>
          <td style='padding:8px 12px;border-bottom:1px solid {cor_borda};'>{p['quantidade']} {p['unidade']}</td>
          <td style='padding:8px 12px;border-bottom:1px solid {cor_borda};font-weight:700;color:#c0392b;'>{p['validade']}</td>
          <td style='padding:8px 12px;border-bottom:1px solid {cor_borda};font-weight:700;'>{dias_txt}</td>
        </tr>"""
    return html


def gerar_html_alerta(vencidos, criticos, dias_aviso):
    def tabela(titulo, cor, prods, cf, cb):
        if not prods: return ""
        return f"""<h3 style='color:{cor};margin:24px 0 8px;'>{titulo} ({len(prods)})</h3>
        <table style='width:100%;border-collapse:collapse;'>
          <thead><tr style='background:{cor};color:white;'>
            <th style='padding:10px 12px;text-align:left;'>Produto</th>
            <th style='padding:10px 12px;text-align:left;'>Categoria</th>
            <th style='padding:10px 12px;text-align:left;'>Estoque</th>
            <th style='padding:10px 12px;text-align:left;'>Validade</th>
            <th style='padding:10px 12px;text-align:left;'>Situação</th>
          </tr></thead>
          <tbody>{_linhas(prods,cf,cb)}</tbody>
        </table>"""

    return f"""<!DOCTYPE html><html><head><meta charset='UTF-8'></head>
<body style='font-family:Inter,Arial,sans-serif;background:#f4f6f8;padding:20px;'>
  <div style='max-width:680px;margin:0 auto;background:white;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.1);'>
    <div style='background:linear-gradient(135deg,#0f2318,#2d6a4f);padding:32px;text-align:center;'>
      <div style='font-size:40px;'>📦</div>
      <h1 style='color:white;margin:8px 0 4px;font-size:24px;'>SmartLarder Pro</h1>
      <p style='color:#95d5b2;margin:0;font-size:14px;'>Relatório de Alertas — {_now_br()}</p>
    </div>
    <div style='padding:28px 32px;'>
      {tabela("🚨 Produtos Vencidos","#e74c3c",vencidos,"#fff8f8","#fde0e0")}
      {tabela(f"⚠️ Vencem em ≤{dias_aviso} dias","#e67e22",criticos,"#fffbf0","#fdecc8")}
      <p style='color:#aaa;font-size:12px;text-align:center;margin-top:28px;'>
        E-mail automático do <strong>SmartLarder Pro</strong>.
      </p>
    </div>
  </div>
</body></html>"""


def enviar_alerta_email(forcar=False) -> tuple[bool, str]:
    config = get_config_alertas(1)
    if not config.get("enviar_email") and not forcar:
        return False, "Envio de e-mail desativado nas configurações."
    if not config.get("email_destino"):
        return False, "E-mail de destino não configurado."
    if not config.get("smtp_usuario") or not config.get("smtp_senha"):
        return False, "Credenciais SMTP não configuradas."

    dias     = config.get("dias_aviso", 7)
    todos    = listar_produtos(1)
    vencidos = [p for p in todos if p["status"]=="vencido"]
    criticos = [p for p in todos if p["status"]=="critico"]
    if not vencidos and not criticos:
        return True, "Nenhum produto crítico. E-mail não enviado."

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"⚠️ SmartLarder: {len(vencidos)} vencidos, {len(criticos)} críticos"
        msg["From"]    = config["smtp_usuario"]
        msg["To"]      = config["email_destino"]
        msg.attach(MIMEText(gerar_html_alerta(vencidos,criticos,dias), "html", "utf-8"))
        with smtplib.SMTP(config.get("smtp_host","smtp.gmail.com"), int(config.get("smtp_porta",587))) as srv:
            srv.starttls()
            srv.login(config["smtp_usuario"], config["smtp_senha"])
            srv.sendmail(config["smtp_usuario"], config["email_destino"], msg.as_string())
        return True, f"E-mail enviado para {config['email_destino']}!"
    except smtplib.SMTPAuthenticationError:
        return False, "Falha de autenticação. Use uma Senha de App do Google."
    except Exception as e:
        return False, f"Erro ao enviar: {e}"
