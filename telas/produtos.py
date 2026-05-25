# -*- coding: utf-8 -*-
import streamlit as st
from datetime import datetime
import pytz

_TZ = pytz.timezone("America/Sao_Paulo")

CATEGORIAS = ["Alimentos","Bebidas","Limpeza","Higiene","Medicamentos","Outros"]
UNIDADES   = ["un","kg","g","L","ml","cx","fardo","pct","dz"]


def _semaforo(produto: dict) -> tuple[str, str, str, str]:
    """
    Semáforo de validade adaptado para a coluna 'data_validade' do banco:
    🔴 Vencido ou ≤ 7 dias
    🟡 8 a 15 dias
    🟢 > 15 dias
    """
    hoje = datetime.now(_TZ).date()
    val_raw = produto.get("data_validade")
    
    if not val_raw:
        return ("🟢", "#2d6a4f", "#e8f5e9", "Sem data")
        
    try:
        if isinstance(val_raw, str):
            val = datetime.strptime(val_raw[:10], "%Y-%m-%d").date()
        else:
            val = val_raw
        dias = (val - hoje).days
    except Exception:
        dias = 999

    if dias < 0:    return ("🔴","#e74c3c","#fde8e8","Vencido")
    if dias <= 7:    return ("🔴","#e74c3c","#fff3cd",f"{dias}d")
    if dias <= 15:   return ("🟡","#f0a500","#fffde7",f"{dias}d")
    return ("🟢","#2d6a4f","#e8f5e9","OK")


def _fmt_brl(v):
    return f"R$ {v:.2f}".replace(".",",")


def _buscar_produtos_supabase(supabase, empresa_id, busca="", categoria="Todas", status_filtro="Todos"):
    """Realiza a listagem e filtros baseando-se estritamente nas colunas oficiais do banco."""
    try:
        # Filtra os produtos vinculados unicamente à empresa ativa do usuário
        query = supabase.table("produtos").select("*").eq("empresa_id", empresa_id)
        res = query.execute()
        
        if not res.data:
            return []
            
        produtos = res.data
        produtos_filtrados = []
        hoje = datetime.now(_TZ).date()
        
        for p in produtos:
            # 1. Filtro por nome ou código de barras (coluna 'barcode')
            if busca:
                nome_p = p.get("nome", "").lower()
                cod_p = p.get("barcode", "") or ""
                if busca.lower() not in nome_p and busca not in cod_p:
                    continue
            
            # 2. Filtro por Categoria
            if categoria != "Todas" and p.get("categoria") != categoria:
                continue
                
            # Calcular dias para vencer dinamicamente
            val_raw = p.get("data_validade")
            if val_raw:
                try:
                    if isinstance(val_raw, str):
                        val = datetime.strptime(val_raw[:10], "%Y-%m-%d").date()
                    else:
                        val = val_raw
                    dias = (val - hoje).days
                except Exception:
                    dias = 999
            else:
                dias = 999
                
            status_real = "ok"
            if dias < 0:
                status_real = "vencido"
            elif dias <= 7:
                status_real = "critico"
            elif dias <= 30:
                status_real = "atencao"
                
            # 3. Filtro por Status do Semáforo
            if status_filtro == "Vencido" and status_real != "vencido":
                continue
            elif status_filtro == "Crítico (≤7d)" and status_real != "critico":
                continue
            elif status_filtro == "Atenção (≤30d)" and status_real != "atencao":
                continue
            elif status_filtro == "OK" and status_real != "ok":
                continue
                
            p["status"] = status_real
            p["dias_para_vencer"] = dias
            produtos_filtrados.append(p)
            
        return produtos_filtrados
    except Exception as e:
        st.error(f"Erro ao buscar produtos: {e}")
        return []


def show_produtos():
    supabase = st.session_state.get("db")
    user_id = st.session_state.get("user_id", 1)
    empresa_id = st.session_state.get("empresa_id", 1)
    
    st.markdown("## 📋 Produtos em Estoque")

    if supabase is None:
        st.error("Conexão com o banco de dados indisponível.")
        return

    # ── Filtros ────────────────────────────────────────────────────────────────
    with st.expander("🔍 Filtros", expanded=True):
        f1, f2, f3 = st.columns(3)
        with f1:
            fn = st.text_input("Buscar por nome ou código", placeholder="Ex: Arroz / 7891...")
        with f2:
            fc = st.selectbox("Categoria", ["Todas"]+CATEGORIAS)
        with f3:
            fs = st.selectbox("Status", ["Todos","Vencido","Crítico (≤7d)","Atenção (≤30d)","OK"])

    produtos = _buscar_produtos_supabase(supabase, empresa_id, fn, fc, fs)

    if not produtos:
        st.info("Nenhum produto encontrado com os filtros aplicados.")
        return

    valor_total = sum((p.get("preco_custo") or 0) * float(p.get("quantidade", 0) or 0) for p in produtos)
    st.markdown(
        f"**{len(produtos)} product(s)** · "
        f"Valor filtrado: **{_fmt_brl(valor_total)}**"
    )

    # ── Lista de produtos com semáforo ─────────────────────────────────────────
    for p in produtos:
        emoji, cor, bg, label = _semaforo(p)
        preco_txt  = _fmt_brl(p["preco_custo"]) if p.get("preco_custo") else "—"
        
        qtd_atual = float(p.get("quantidade", 0) or 0)
        qtd_minima = float(p.get("quantidade_minima", 0) or 0)
        abaixo_min = qtd_minima > 0 and qtd_atual < qtd_minima

        with st.container():
            c1, c2, c3, c4, c5 = st.columns([3, 1.2, 1.4, 1.6, 2.2])

            with c1:
                min_warn = " 🔴" if abaixo_min else ""
                st.markdown(
                    f"<div style='padding:2px 0;'>"
                    f"<span style='font-weight:600;font-size:0.92rem;'>{p['nome']}{min_warn}</span><br>"
                    f"<span style='color:#888;font-size:0.78rem;'>"
                    f"{p.get('barcode') or '—'} · {p.get('categoria', 'Outros')}"
                    f"{' · 📍 '+p['localizacao'] if p.get('localizacao') else ''}"
                    f"</span></div>",
                    unsafe_allow_html=True,
                )
            with c2:
                min_txt = f"/{qtd_minima:.0f}" if qtd_minima > 0 else ""
                st.markdown(f"**{qtd_atual:.1f}**{min_txt} {p.get('unidade', 'un')}")
            with c3:
                val_txt = p.get("data_validade") if p.get("data_validade") else "—"
                st.markdown(f"📅 `{val_txt}`")
            with c4:
                st.markdown(
                    f"<span style='background:{cor};color:white;padding:3px 11px;"
                    f"border-radius:20px;font-size:0.77rem;font-weight:700;'>\n"
                    f"{emoji} {label}</span>"
                    f"&nbsp;<span style='font-size:0.77rem;color:#666;'>{preco_txt}</span>",
                    unsafe_allow_html=True,
                )
            with c5:
                b1, b2, b3 = st.columns(3)
                with b1:
                    if st.button("✏️", key=f"e_{p['id']}", help="Editar"):
                        st.session_state[f"edit_{p['id']}"] = True
                with b2:
                    if st.button("📦", key=f"m_{p['id']}", help="Movimentar"):
                        st.session_state[f"mov_{p['id']}"]  = True
                with b3:
                    if st.button("🗑️", key=f"d_{p['id']}", help="Excluir"):
                        st.session_state[f"del_{p['id']}"] = True

            # Confirmação exclusão direto no Supabase
            if st.session_state.get(f"del_{p['id']}"):
                st.warning(f"Confirma exclusão de **{p['nome']}**?")
                y, n = st.columns(2)
                with y:
                    if st.button("✅ Confirmar", key=f"dy_{p['id']}"):
                        try:
                            supabase.table("produtos").delete().eq("id", p["id"]).execute()
                            st.success("Produto removido!")
                        except Exception as e:
                            st.error(f"Erro ao deletar: {e}")
                        st.session_state.pop(f"del_{p['id']}", None)
                        st.rerun()
                with n:
                    if st.button("❌ Cancelar", key=f"dn_{p['id']}"):
                        st.session_state.pop(f"del_{p['id']}", None)
                        st.rerun()

            if st.session_state.get(f"edit_{p['id']}"):
                with st.expander(f"✏️ Editando: {p['nome']}", expanded=True):
                    _form_edicao(supabase, p, empresa_id)

            if st.session_state.get(f"mov_{p['id']}"):
                with st.expander(f"📦 Movimentar: {p['nome']}", expanded=True):
                    _form_mov(supabase, p, empresa_id)

        st.markdown("<hr style='margin:5px 0;border-color:#eef2ee;'>", unsafe_allow_html=True)


def _form_edicao(supabase, p, empresa_id):
    with st.form(f"fe_{p['id']}"):
        c1, c2 = st.columns(2)
        with c1:
            nome       = st.text_input("Nome", value=p["nome"])
            codigo     = st.text_input("Código de Barras", value=p.get("barcode") or "")
            categoria  = st.selectbox("Categoria", CATEGORIAS,
                                      index=CATEGORIAS.index(p["categoria"]) if p.get("categoria") in CATEGORIAS else 0)
        with c2:
            quantidade = st.number_input("Quantidade", value=float(p.get("quantidade", 0.0) or 0.0), min_value=0.0, step=0.1)
            unidade    = st.selectbox("Unidade", UNIDADES,
                                      index=UNIDADES.index(p["unidade"]) if p.get("unidade") in UNIDADES else 0)
            
            val_raw = p.get("data_validade")
            if val_raw:
                try:
                    val_date = datetime.strptime(val_raw[:10], "%Y-%m-%d").date()
                except Exception:
                    val_date = datetime.now(_TZ).date()
            else:
                val_date = datetime.now(_TZ).date()
                
            validade   = st.date_input("Validade", value=val_date)
            preco      = st.number_input("Preço Custo (R$)", value=float(p.get("preco_custo", 0) or 0),
                                         min_value=0.0, step=0.01, format="%.2f")
        c3, c4 = st.columns(2)
        with c3:
            estoque_min = st.number_input("Estoque Mínimo", value=float(p.get("quantidade_minima", 0) or 0),
                                          min_value=0.0, step=1.0)
        with c4:
            localizacao = st.text_input("Localização", value=p.get("localizacao") or "")

        s1, s2 = st.columns(2)
        with s1: salvar   = st.form_submit_button("💾 Salvar", type="primary")
        with s2: cancelar = st.form_submit_button("❌ Cancelar")

    if salvar:
        try:
            db_quantidade = float(quantidade) if quantidade is not None else 0.0
            
            supabase.table("produtos").update({
                "barcode": codigo, 
                "nome": nome, 
                "categoria": categoria,
                "quantidade": db_quantidade, 
                "unidade": unidade, 
                "data_validade": str(validade),
                "localizacao": localizacao, 
                "preco_custo": preco, 
                "quantidade_minima": estoque_min
            }).eq("id", p["id"]).execute()
            
            st.success("✅ Produto updated com sucesso!")
            st.session_state.pop(f"edit_{p['id']}", None)
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar alterações no Supabase: {e}")
        
    if cancelar:
        st.session_state.pop(f"edit_{p['id']}", None)
        st.rerun()


def _form_mov(supabase, p, empresa_id):
    with st.form(f"fm_{p['id']}"):
        qtd_atual = float(p.get("quantidade", 0) or 0)
        qtd_minima = float(p.get("quantidade_minima", 0) or 0)
        st.info(f"Estoque atual: **{qtd_atual} {p.get('unidade','un')}** | Mínimo: **{qtd_minima} {p.get('unidade','un')}**")
        
        tipo = st.radio("Tipo", ["entrada","saida"], horizontal=True,
                        format_func=lambda x: "📥 Entrada" if x=="entrada" else "📤 Saída")
        qtd  = st.number_input("Quantidade", min_value=0.01, step=0.1, value=1.0)
        obs  = st.text_input("Observação", placeholder="Ex: Recebimento NF 1234 / Venda")
        s1, s2 = st.columns(2)
        with s1: salvar   = st.form_submit_button("💾 Registrar", type="primary")
        with s2: cancelar = st.form_submit_button("❌ Cancelar")

    if salvar:
        if tipo == "saida" and qtd > qtd_atual:
            st.error("Quantidade de saída maior que o estoque disponível!")
        else:
            try:
                nova_qtd = qtd_atual + qtd if tipo == "entrada" else qtd_atual - qtd
                
                # 1. Atualiza quantidade na tabela de produtos
                supabase.table("produtos").update({"quantidade": nova_qtd}).eq("id", p["id"]).execute()
                
                # 2. Registra o histórico na tabela de movimentações conforme as colunas do SQL
                supabase.table("movimentacoes").insert({
                    "empresa_id": empresa_id,
                    "produto_id": p["id"],
                    "tipo": tipo,
                    "quantidade": qtd,
                    "motivo": obs
                }).execute()
                
                st.success(f"✅ {'Entrada' if tipo=='entrada' else 'Saída'} registrada!")
            except Exception as e:
                st.error(f"Erro ao registrar movimentação: {e}")
                
            st.session_state.pop(f"mov_{p['id']}", None)
            st.rerun()
            
    if cancelar:
        st.session_state.pop(f"mov_{p['id']}", None)
        st.rerun()
