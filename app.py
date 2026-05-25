# -*- coding: utf-8 -*-
import streamlit as st
import hashlib
from streamlit_cookies_manager import EncryptedCookieManager
from supabase import create_client

st.set_page_config(
    page_title="SmartLarder Pro",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ocultar navegação padrão do Streamlit e injetar suporte PWA completo
st.markdown(
    """
    <style>
    [data-testid='stSidebarNav']{display:none !important;} 
    .block-container{padding-top:1rem !important;}
    </style>
    <script>
        // Força o modo 'App' no celular (oculta barras do navegador)
        var metaApple = document.createElement('meta');
        metaApple.name = "apple-mobile-web-app-capable";
        metaApple.content = "yes";
        document.getElementsByTagName('head')[0].appendChild(metaApple);
        
        var metaStatus = document.createElement('meta');
        metaStatus.name = "apple-mobile-web-app-status-bar-style";
        metaStatus.content = "black-translucent";
        document.getElementsByTagName('head')[0].appendChild(metaStatus);

        // Ajusta o zoom para não bugar no celular e previne recarregamentos agressivos
        var metaView = document.createElement('meta');
        metaView.name = "viewport";
        metaView.content = "width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover";
        document.getElementsByTagName('head')[0].appendChild(metaView);
    </script>
    """, 
    unsafe_allow_html=True
)

# Inicializar Gerenciador de Cookies
_COOKIE_PASSWORD = st.secrets.get("COOKIES_PASSWORD", "smartlarder-fallback-32chars!!")
cookies = EncryptedCookieManager(prefix="smartlarder/", password=_COOKIE_PASSWORD)
if not cookies.ready():
    st.stop()

def _salvar_cookie(user: dict):
    try:
        cookies["sl_user_id"]    = str(user.get("id", ""))
        cookies["sl_username"]   = str(user.get("username", ""))
        cookies["sl_nome"]       = str(user.get("nome", ""))
        cookies["sl_role"]       = str(user.get("role", "domestico"))
        cookies["sl_empresa_id"] = str(user.get("empresa_id", "1"))
        cookies["sl_token"]      = hashlib.sha256(str(user.get("senha_hash", "")).encode()).hexdigest()[:16]
        cookies.save()
    except: pass

def _limpar_cookie():
    try:
        for k in ["sl_user_id","sl_username","sl_nome","sl_role","sl_empresa_id","sl_token"]:
            if k in cookies: cookies[k] = ""
        cookies.save()
    except: pass

def _restaurar_cookie():
    try:
        user_id = cookies.get("sl_user_id", "")
        username = cookies.get("sl_username", "")
        token = cookies.get("sl_token", "")
        if not user_id or not username or not token: return

        db = st.session_state.get("db")
        if not db: return

        res = db.table("usuarios").select("id,senha_hash,ativo").eq("id", int(user_id)).eq("username", username).eq("ativo", 1).execute()
        if not res.data:
            _limpar_cookie(); return

        row = res.data[0]
        if hashlib.sha256(str(row["senha_hash"]).encode()).hexdigest()[:16] != token:
            _limpar_cookie(); return

        st.session_state["logged_in"] = True
        st.session_state["user_id"] = int(user_id)
        st.session_state["username"] = username
        st.session_state["nome_completo"] = cookies.get("sl_nome", "Usuário")
        st.session_state["role"] = cookies.get("sl_role", "domestico")
        st.session_state["empresa_id"] = int(cookies.get("sl_empresa_id", "1"))
    except: _limpar_cookie()

# Conexão Supabase
if "db" not in st.session_state:
    try:
        st.session_state["db"] = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except Exception as e:
        st.error(f"Erro de conexão com o banco: {e}")
        st.stop()

if not st.session_state.get("logged_in"):
    _restaurar_cookie()

if not st.session_state.get("logged_in") or st.session_state.get("user_id") is None:
    from telas.login import show_login
    show_login(cookies, _salvar_cookie)
    st.stop()

# Carregar Sidebar
from telas.sidebar import show_sidebar
page = show_sidebar(_limpar_cookie)

def _load(fn):
    try: fn()
    except Exception as e:
        st.error(f"Erro ao carregar a página {page}: {e}")

# Roteador de Páginas
user_role = str(st.session_state.get("role", "")).lower().strip()
session_user = str(st.session_state.get("username", "")).lower().strip()

if page == "Dashboard":
    from telas.dashboard import show_dashboard; _load(show_dashboard)
elif page == "Produtos":
    from telas.produtos import show_produtos; _load(show_produtos)
elif page == "Cadastrar":
    from telas.cadastro import show_cadastro; _load(show_cadastro)
elif page == "Recepção de Carga":
    from telas.recepcao import show_recepcao; _load(show_recepcao)
elif page == "Lista de Compras":
    from telas.lista_compras import show_lista_compras; _load(show_lista_compras)

elif page == "Alertas":
    # ── MÓDULO DE ALERTAS DINÂMICO E ESCALÁVEL ─────────────────────────
    st.markdown("## 🔔 Central de Alertas Ativos")
    st.markdown("---")
    
    db = st.session_state.get("db")
    
    # Captura dos dados do usuário atual conectado na sessão
    empresa_id = st.session_state.get("empresa_id", 1)
    usuario_logado = st.session_state.get("nome_completo", "Usuário")
    
    st.info(f"💡 Olá, {usuario_logado}! Os relatórios diários de validade e estoque mínimo cruzam os dados da sua empresa (ID: {empresa_id}) e notificam você por e-mail.")
    
    st.markdown("### 📬 Configuração de Disparo")
    # Mantém o seu e-mail como padrão de segurança para o teste inicial
    email_destino = st.text_input("E-mail de Destino para Alertas:", value="alexsandresilva777@gmail.com")
    
    st.markdown(" ")
    btn_verificar = st.button("🚀 Verificar Estoque e Enviar Relatório", type="primary", use_container_width=True)
    
    if btn_verificar:
        with st.spinner("Varrendo o Supabase e estruturando relatório em HTML..."):
            from datetime import date, timedelta
            import resend
            
            # Puxa de forma segura a chave salva nas Secrets do Streamlit
            resend.api_key = st.secrets.get("RESEND_KEY", "SUA_CHAVE_RE_AQUI")
            hoje = date.today()
            limite_validade = hoje + timedelta(days=15)
            
            try:
                # Filtragem inteligente: O banco agora só traz os dados pertencentes à empresa logada
                res = db.table("produtos").select("*").eq("empresa_id", empresa_id).execute()
                produtos = res.data if (res and hasattr(res, 'data') and res.data) else []
                
                itens_vencendo = []
                itens_estoque_baixo = []
                
                for p in produtos:
                    nome = str(p.get("nome") or "PRODUTO SEM NOME").upper()
                    qtd = float(p.get("quantidade") or 0.0)
                    qtd_min = float(p.get("quantidade_minima") or 0.0)
                    unidade = str(p.get("unidade") or "un")
                    
                    # 📉 Verificação de Estoque Mínimo
                    if qtd <= qtd_min:
                        itens_estoque_baixo.append(
                            f"<li>❌ <b>{nome}</b>: Estoque atual em {qtd:.2f} {unidade} (Mínimo: {qtd_min:.2f} {unidade})</li>"
                        )
                    
                    # 📅 Verificação de Validade
                    data_v_str = p.get("data_validade")
                    if data_v_str:
                        try:
                            data_v = date.fromisoformat(data_v_str.split(" ")[0])
                            if data_v <= hoje:
                                itens_vencendo.append(
                                    f"<li style='color: red;'>🚨 <b>{nome}</b>: <b>VENCIDO/CRÍTICO</b> em {data_v.strftime('%d/%m/%Y')}</li>"
                                )
                            elif data_v <= limite_validade:
                                itens_vencendo.append(
                                    f"<li>⚠️ <b>{nome}</b>: Vence em {data_v.strftime('%d/%m/%Y')}</li>"
                                )
                        except: pass

                # Rede de segurança: caso o usuário não tenha nada crítico, injeta uma notificação de sucesso
                if not itens_vencendo and not itens_estoque_baixo:
                    itens_estoque_baixo.append("<li>⚠️ <b>MONITORAMENTO DIÁRIO</b>: Todos os itens do seu inventário estão em conformidade operacional hoje.</li>")
                
                # Montagem do Layout HTML do E-mail customizado com o nome do cliente
                html_content = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px;">
                    <h2 style="color: #1E3A8A; border-bottom: 2px solid #1E3A8A; padding-bottom: 10px; margin-top: 0;">
                        📊 SmartLarder Pro — Relatório de Alertas Diários
                    </h2>
                    <p>Olá, <b>{usuario_logado}</b>! Identificamos os seguintes pontos de atenção no seu inventário hoje (<b>{hoje.strftime('%d/%m/%Y')}</b>):</p>
                """
                if itens_vencendo:
                    html_content += f"<h3 style='color: #B91C1C; margin-top: 20px;'>⚠️ Alertas de Validade</h3><ul style='padding-left: 20px; line-height: 1.6;'>{''.join(itens_vencendo)}</ul>"
                if itens_estoque_baixo:
                    html_content += f"<h3 style='color: #D97706; margin-top: 20px;'>📉 Alertas de Estoque Mínimo</h3><ul style='padding-left: 20px; line-height: 1.6;'>{''.join(itens_estoque_baixo)}</ul>"
                
                html_content += """
                    <hr style="border: 0; border-top: 1px solid #e0e0e0; margin-top: 30px;">
                    <p style="font-size: 12px; color: #737373; text-align: center; margin-bottom: 0;">
                        SmartLarder Pro v2 — Gestão Inteligente para seu Negócio.
                    </p>
                </div>
                """
                
                resend.Emails.send({
                    "from": "SmartLarder Pro <onboarding@resend.dev>",
                    "to": email_destino,
                    "subject": f"⚠️ Alertas de Estoque - {hoje.strftime('%d/%m/%Y')}",
                    "html": html_content
                })
                st.success(f"🎉 **Espetáculo!** O relatório de alertas foi enviado com sucesso para **{email_destino}**!")
                st.balloons()
            except Exception as e:
                st.error(f"❌ Erro crítico no envio do Resend: {e}")

elif page == "Relatórios":
    from telas.relatorios import show_relatorios; _load(show_relatorios)
elif page == "Fornecedores":
    try:
        from telas.fornecedores import show_fornecedores; _load(show_fornecedores)
    except: st.info("Módulo de Fornecedores em desenvolvimento.")
elif page == "Perdas":
    try:
        from telas.perdas import show_perdas; _load(show_perdas)
    except: st.info("Módulo de Perdas em development.")
elif page == "Usuários":
    if "admin" in user_role or "alex" in session_user:
        from telas.usuarios import show_usuarios; _load(show_usuarios)
    else:
        st.error("🔒 Acesso restrito a administradores.")
elif page == "Ajuda":
    from telas.ajuda import show_ajuda; _load(show_ajuda)
