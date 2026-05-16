# -*- coding: utf-8 -*-
import streamlit as st
from datetime import datetime
import pytz
from utils.email_alert import enviar_alerta_email

_TZ = pytz.timezone("America/Sao_Paulo")

def _buscar_produtos_alertas_supabase(supabase, empresa_id):
    """Busca produtos no Supabase filtrados pela empresa e separa em categorias de vencimento dinâmicas"""
    try:
        res = supabase.table("produtos").select("*").eq("empresa_id", empresa_id).execute()
        if not res.data:
            return [], [], []
            
        produtos = res.data
        vencidos = []
        criticos = []
        atencao  = []
        hoje = datetime.now(_TZ).date()
        
        for p in produtos:
            val_raw = p.get("data_validade")
            try:
                if isinstance(val_raw, str):
                    val = datetime.strptime(val_raw[:10], "%Y-%m-%d").date()
                else:
                    val = val_raw
                dias = (val - hoje).days
            except Exception:
                dias = 999  # Fallback para produtos sem data válida cadastrada
                
            p["dias_para_vencer"] = dias
            
            if dias < 0:
                vencidos.append(p)
            elif dias <= 7:
                criticos.append(p)
            elif dias <= 30:
                atencao.append(p)
                
        return vencidos, criticos, atencao
    except Exception as e:
        st.error(f"Erro ao carregar dados de alerta: {e}")
        return [], [], []

def _get_config_alertas_supabase(supabase, empresa_id):
    """Busca as configurações de e-mail salvas no Supabase para a empresa ou retorna o dicionário padrão"""
    try:
        res = supabase.table("configuracoes").select("*").eq("empresa_id", empresa_id).limit(1).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
    except Exception:
        pass
    return {
        "email_destino": "", "smtp_usuario": "", "dias_aviso": 7,
        "smtp_senha": "", "smtp_host": "smtp.gmail.com", "smtp_porta": 587,
        "enviar_email": 0
    }

def _salvar_config_alertas_supabase(supabase, empresa_id, dados):
    """Salva ou atualiza os parâmetros de SMTP na tabela configuracoes isolando por empresa_id"""
    try:
        # Busca se já existe uma configuração salva para esta empresa
        res = supabase.table("configuracoes").select("id").eq("empresa_id", empresa_id).limit(1).execute()
        
        payload = {
            "empresa_id": empresa_id,
            "email_destino": dados.get("email_destino"),
            "smtp_usuario": dados.get("smtp_usuario"),
            "dias_aviso": dados.get("dias_aviso"),
            "smtp_senha": dados.get("smtp_senha"),
            "smtp_host": dados.get("smtp_host"),
            "smtp_porta": dados.get("smtp_porta"),
            "enviar_email": dados.get("enviar_email")
        }
        
        # Se existir, atualiza mantendo o mesmo ID primário. Se não, faz o insert.
        if res.data and len(res.data) > 0:
            payload["id"] = res.data[0]["id"]
            
        supabase.table("configuracoes").upsert(payload).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar configurações no banco: {e}")
        return False

def show_alertas():
    supabase = st.session_state.get("db")
    user_id = st.session_state.get("user_id", 1)
    empresa_id = st.session_state.get("empresa_id", 1)
    
    st.markdown("## 🔔 Central de Alertas")

    if supabase is None:
        st.error("Conexão com o banco de dados indisponível.")
        return

    vencidos, criticos, atencao = _buscar_produtos_alertas_supabase(supabase, empresa_id)

    # ── Cards de Indicadores (KPIs) ──────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    for col, qtd, label, bg, cor, borda in [
        (c1, len(vencidos), "🚨 Vencidos",    "#fde8e8", "#c62828", "#ffcdd2"),
        (c2, len(criticos), "⚠️ Vence ≤7d",  "#fff3cd", "#e65100", "#ffe082"),
        (c3, len(atencao),  "🕐 Atenção ≤30d", "#fff8e1", "#f57f17", "#fff9c4"),
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

    # ── Listas Auxiliares de Renderização ───────────────────────────────────────
    def _render_lista(titulo, cor, bg, items):
        if not items:
            return
        if titulo:
            st.markdown(f"### {titulo}")
        for p in items:
            dias_txt  = "VENCIDO" if p["dias_para_vencer"] < 0 else f"{p['dias_para_vencer']}d"
            preco_txt = f" · R$ {p['preco_custo']:.2f}".replace(".", ",") if p.get("preco_custo") else ""
            loc_txt   = f" · 📍 {p['localizacao']}" if p.get("localizacao") else ""
            st.markdown(
                f"""<div style='display:flex;align-items:center;
                    justify-content:space-between;padding:9px 16px;
                    background:{bg};border-left:4px solid {cor};
                    border-radius:0 10px 10px 0;margin-bottom:6px;'>
                  <div>
                    <span style='font-weight:600;font-size:0.9rem;'>{p.get('nome', 'Sem nome')}</span>
                    <span style='color:#888;font-size:0.79rem;margin-left:8px;'>
                      {p.get('categoria', 'Geral')} · {p.get('quantidade', 0)} {p.get('unidade', 'un')}{preco_txt}{loc_txt}
                    </span>
                  </div>
                  <span style='background:{cor};color:white;padding:3px 10px;
                               border-radius:20px;font-size:0.79rem;font-weight:700;'>
                    {dias_txt}
                  </span>
                </div>""",
                unsafe_allow_html=True,
            )

    _render_lista("🚨 Produtos Vencidos",       "#e74c3c", "#fde8e8", vencidos)
    _render_lista("⚠️ Vencem em até 7 dias",    "#e67e22", "#fff3cd", criticos)

    if atencao:
        with st.expander(f"🕐 Ver produtos em atenção ({len(atencao)})"):
            _render_lista("", "#f0a500", "#fffde7", atencao)

    if not vencidos and not criticos and not atencao:
        st.success("🎉 Tudo em ordem! Nenhum produto crítico ou vencido no momento.")

    st.markdown("---")

    # ── Configurações de E-mail (SMTP) ─────────────────────────────────────────
    st.markdown("### 📧 Configuração de Alertas por E-mail")
    config = _get_config_alertas_supabase(supabase, empresa_id)

    with st.expander("⚙️ Configurar SMTP / Gmail", expanded=False):
        st.info(
            "💡 **Gmail:** Ative a verificação em 2 etapas em "
            "[myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) "
            "gerando uma **Senha de App** dedicada para usar no campo abaixo."
        )
        with st.form("form_email_v31"):
            c1, c2 = st.columns(2)
            with c1:
                email_dest   = st.text_input("E-mail de Destino", value=config.get("email_destino") or "")
                smtp_usuario = st.text_input("E-mail Remetente (Gmail)", value=config.get("smtp_usuario") or "")
                dias_aviso   = st.number_input(
                    "Alertar com quantos dias de antecedência?",
                    min_value=1, max_value=90,
                    value=int(config.get("dias_aviso") or 7),
                )
            with c2:
                smtp_senha = st.text_input("Senha de App", type="password", value=config.get("smtp_senha") or "")
                smtp_host  = st.text_input("Servidor SMTP", value=config.get("smtp_host") or "smtp.gmail.com")
                smtp_porta = st.number_input("Porta", value=int(config.get("smtp_porta") or 587))

            enviar_auto = st.checkbox(
                "Ativar envio automático ao iniciar o sistema",
                value=bool(config.get("enviar_email")),
            )
            if st.form_submit_button("💾 Salvar Configurações", type="primary"):
                sucesso = _salvar_config_alertas_supabase(supabase, empresa_id, {
                    "email_destino": email_dest, "dias_aviso": dias_aviso,
                    "enviar_email": 1 if enviar_auto else 0,
                    "smtp_host": smtp_host, "smtp_porta": smtp_porta,
                    "smtp_usuario": smtp_usuario, "smtp_senha": smtp_senha,
                })
                if sucesso:
                    st.success("✅ Configurações de e-mail guardadas com segurança!")
                    st.rerun()

    # ── Envio Manual de Teste ──────────────────────────────────────────────────
    st.markdown("### 📤 Enviar Alerta Agora")
    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        if st.button("📧 Enviar E-mail de Alerta", type="primary", use_container_width=True):
            with st.spinner("Conectando ao servidor e enviando e-mail..."):
                # Passa a flag forçar para contornar travas de tempo no envio
                ok, msg = enviar_alerta_email(forcar=True)
            if ok:
                st.success(msg)
            else:
                st.error(msg)
    with col_info:
        st.info("Dispara um e-mail com o sumário completo em HTML contendo os produtos vencidos e os críticos mapeados no momento.")
