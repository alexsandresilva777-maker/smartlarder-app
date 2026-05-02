import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import imports  # noqa
import streamlit as st
from utils.database import listar_produtos, get_config_alertas, salvar_config_alertas
from utils.email_alert import enviar_alerta_email

def show_alertas():
    st.markdown("## 🔔 Central de Alertas")

    produtos = listar_produtos()
    vencidos = [p for p in produtos if p["status"]=="vencido"]
    criticos = [p for p in produtos if p["status"]=="critico"]
    atencao  = [p for p in produtos if p["status"]=="atencao"]

    # ── KPI cards ──────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    for col, qtd, label, bg, cor, borda in [
        (c1, len(vencidos), "🚨 Vencidos",    "#fde8e8","#c62828","#ffcdd2"),
        (c2, len(criticos), "⚠️ Vence ≤7d",  "#fff3cd","#e65100","#ffe082"),
        (c3, len(atencao),  "🕐 Atenção ≤30d","#fff8e1","#f57f17","#fff9c4"),
    ]:
        with col:
            st.markdown(
                f"""<div style='background:{bg};border:1.5px solid {borda};
                    border-radius:14px;padding:18px;text-align:center;
                    box-shadow:0 2px 10px rgba(0,0,0,.06);'>
                  <div style='font-size:2.4rem;font-weight:800;color:{cor};'>{qtd}</div>
                  <div style='font-size:0.8rem;color:#555;font-weight:600;
                              margin-top:4px;'>{label}</div>
                </div>""",
                unsafe_allow_html=True,
            )

    st.markdown("")

    # ── Listas ──────────────────────────────────────────────
    def _render_lista(titulo, cor, bg, items):
        if not items:
            return
        st.markdown(f"### {titulo}")
        for p in items:
            dias_txt  = "VENCIDO" if p["dias_para_vencer"] < 0 else f"{p['dias_para_vencer']}d"
            preco_txt = (f" · R$ {p['preco_custo']:.2f}".replace(".",",")
                         if p.get("preco_custo") else "")
            loc_txt   = f" · 📍 {p['localizacao']}" if p.get("localizacao") else ""
            st.markdown(
                f"""<div style='display:flex;align-items:center;
                    justify-content:space-between;padding:9px 16px;
                    background:{bg};border-left:4px solid {cor};
                    border-radius:0 10px 10px 0;margin-bottom:6px;'>
                  <div>
                    <span style='font-weight:600;font-size:0.9rem;'>{p['nome']}</span>
                    <span style='color:#888;font-size:0.79rem;margin-left:8px;'>
                      {p['categoria']} · {p['quantidade']} {p['unidade']}{preco_txt}{loc_txt}
                    </span>
                  </div>
                  <span style='background:{cor};color:white;padding:3px 10px;
                               border-radius:20px;font-size:0.79rem;font-weight:700;'>
                    {dias_txt}
                  </span>
                </div>""",
                unsafe_allow_html=True,
            )

    _render_lista("🚨 Produtos Vencidos",       "#e74c3c","#fde8e8", vencidos)
    _render_lista("⚠️ Vencem em até 7 dias",    "#e67e22","#fff3cd", criticos)

    if atencao:
        with st.expander(f"🕐 Ver produtos em atenção ({len(atencao)})"):
            _render_lista("","#f0a500","#fffde7", atencao)

    if not vencidos and not criticos and not atencao:
        st.success("🎉 Tudo em ordem! Nenhum produto crítico no momento.")

    st.markdown("---")

    # ── Config e-mail ───────────────────────────────────────
    st.markdown("### 📧 Configuração de Alertas por E-mail")
    config = get_config_alertas()

    with st.expander("⚙️ Configurar SMTP / Gmail", expanded=False):
        st.info(
            "💡 **Gmail:** Ative verificação em 2 etapas → "
            "[myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) "
            "→ crie uma **Senha de App** e use no campo abaixo."
        )
        with st.form("form_email_v31"):
            c1, c2 = st.columns(2)
            with c1:
                email_dest   = st.text_input("E-mail de Destino",
                                             value=config.get("email_destino") or "")
                smtp_usuario = st.text_input("E-mail Remetente (Gmail)",
                                             value=config.get("smtp_usuario") or "")
                dias_aviso   = st.number_input(
                    "Alertar com quantos dias de antecedência?",
                    min_value=1, max_value=90,
                    value=int(config.get("dias_aviso") or 7),
                )
            with c2:
                smtp_senha = st.text_input("Senha de App", type="password",
                                           value=config.get("smtp_senha") or "")
                smtp_host  = st.text_input("Servidor SMTP",
                                           value=config.get("smtp_host") or "smtp.gmail.com")
                smtp_porta = st.number_input("Porta",
                                             value=int(config.get("smtp_porta") or 587))

            enviar_auto = st.checkbox(
                "Ativar envio automático ao iniciar o sistema",
                value=bool(config.get("enviar_email")),
            )
            if st.form_submit_button("💾 Salvar Configurações", type="primary"):
                salvar_config_alertas(dict(
                    email_destino=email_dest, dias_aviso=dias_aviso,
                    enviar_email=1 if enviar_auto else 0,
                    smtp_host=smtp_host, smtp_porta=smtp_porta,
                    smtp_usuario=smtp_usuario, smtp_senha=smtp_senha,
                ))
                st.success("✅ Configurações salvas!")

    # ── Envio manual ────────────────────────────────────────
    st.markdown("### 📤 Enviar Alerta Agora")
    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        if st.button("📧 Enviar E-mail de Alerta", type="primary", use_container_width=True):
            with st.spinner("Enviando..."):
                ok, msg = enviar_alerta_email(forcar=True)
            if ok:
                st.success(msg)
            else:
                st.error(msg)
    with col_info:
        st.info("Envia relatório HTML com produtos vencidos e críticos para o e-mail configurado.")
