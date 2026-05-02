import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import imports  # noqa
import streamlit as st

def show_ajuda():
    st.markdown("## ❓ Ajuda — Como usar o SmartLarder Pro")

    st.markdown("""
    <div style='background:linear-gradient(135deg,#e8f5e9,#f0faf2);
                border:1.5px solid #a8d5b5;border-radius:14px;
                padding:18px 22px;margin-bottom:24px;'>
      <div style='font-size:1rem;font-weight:700;color:#0f2318;margin-bottom:4px;'>
        📦 Bem-vindo ao SmartLarder Pro
      </div>
      <div style='font-size:0.88rem;color:#2d6a4f;'>
        Sistema de controle inteligente de validade e estoque para empresas e mercados.
        Use o menu lateral para navegar entre as seções.
      </div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🚀 Primeiros Passos",
        "📷 Código de Barras",
        "🛒 Lista de Compras",
        "📧 Alertas E-mail",
        "👥 Usuários",
    ])

    with tab1:
        st.markdown("### 🚀 Primeiros Passos")
        st.markdown("""
        **1. Acesse o sistema**
        - Login padrão: usuário `admin` / senha `admin123`
        - ⚠️ Troque a senha em **Usuários → Alterar senha** após o primeiro acesso

        **2. Cadastre seus produtos**
        - Vá em **➕ Cadastrar**
        - Digite ou escaneie o código de barras EAN
        - O sistema busca o nome automaticamente na internet
        - Informe apenas a **data de validade** e **quantidade**

        **3. Configure o Estoque Mínimo**
        - Em **📋 Produtos**, clique em ✏️ para editar cada produto
        - Defina o campo **Estoque Mínimo**
        - O sistema usará isso para sugerir compras automaticamente

        **4. Registre movimentações**
        - Em **📋 Produtos**, clique em 📦 ao lado do produto
        - Registre **entradas** (recebimento) e **saídas** (vendas/consumo)
        - Isso alimenta o cálculo de consumo médio da Lista de Compras

        **5. Monitore pelo Dashboard**
        - Acesse **🏠 Dashboard** para ver o resumo completo
        - KPIs de estoque, valor investido e gasto mensal
        - Gráficos de status e alertas em tempo real
        """)

    with tab2:
        st.markdown("### 📷 Leitura de Código de Barras")
        st.markdown("""
        **Leitor USB ou Bluetooth (pistola)**
        1. Vá em **➕ Cadastrar**
        2. Clique no campo **"Código EAN"**
        3. Aponte o leitor para o produto → código inserido automaticamente
        4. Clique **🔍 Buscar** → nome, marca e categoria preenchidos
        5. Digite apenas **validade** e **quantidade** → Salvar

        **Câmera do celular ou webcam**
        1. Clique no botão **📷 Câmera**
        2. Aponte para o código de barras
        3. Copie o número detectado e cole no campo EAN
        4. Clique **🔍 Buscar**

        **Códigos manuais (sem código de barras)**
        - Use códigos curtos como `001`, `002`, `A1`
        - O sistema entra em modo manual — preencha todos os campos
        - Ideal para produtos de feira, hortifrúti e itens artesanais

        **Bases de dados consultadas automaticamente:**
        | Base | Cobertura |
        |---|---|
        | Open Food Facts | Alimentos do mundo todo |
        | Open Beauty Facts | Cosméticos e higiene |
        | Open Products Facts | Produtos gerais |
        | UPC Item DB | Produtos internacionais |
        """)

    with tab3:
        st.markdown("### 🛒 Lista de Compras Inteligente")
        st.markdown("""
        A lista de compras é gerada automaticamente pelo sistema com base em dois critérios:

        **Critério 1 — Estoque Mínimo**
        - Configure o mínimo em cada produto (Produtos → ✏️ Editar)
        - Quando o estoque cair abaixo do mínimo, o produto entra na lista
        - Exemplo: mínimo 10 unidades, estoque atual 3 → sugere comprar 7+

        **Critério 2 — Consumo Médio**
        - Calculado com base nas saídas dos últimos 30 dias
        - Se o estoque atual vai acabar em menos de 7 dias, o produto entra na lista
        - Exemplo: consumo de 5/dia, estoque 20 → acaba em 4 dias → lista!

        **Urgências:**
        - 🚨 **Alta** — produto vencido ou estoque zerado
        - ⚠️ **Média** — vai acabar em breve ou abaixo do mínimo

        **Exportar a lista:**
        - Clique em **📥 Exportar Lista de Compras (CSV)**
        - Abra no Excel para imprimir ou compartilhar com o fornecedor
        """)

    with tab4:
        st.markdown("### 📧 Configuração de Alertas por E-mail")
        st.markdown("""
        O sistema envia um relatório HTML por e-mail com produtos vencidos e críticos.

        **Configuração com Gmail (recomendado):**
        1. Ative a **verificação em 2 etapas** na sua conta Google
        2. Acesse: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
        3. Crie uma **Senha de App** (selecione "Outro" → "SmartLarder")
        4. No sistema, vá em **🔔 Alertas → Configurar SMTP**
        5. Preencha:
           - E-mail de destino (quem recebe)
           - E-mail remetente (seu Gmail)
           - Senha de App (não é a senha normal!)
        6. Clique **📧 Enviar E-mail de Alerta** para testar

        **⚠️ Atenção:** Use sempre a **Senha de App**, nunca a senha normal da conta Google.
        """)

    with tab5:
        st.markdown("### 👥 Gestão de Usuários")
        st.markdown("""
        Disponível apenas para **Administradores**.

        **Perfis de acesso:**
        | Perfil | Permissões |
        |---|---|
        | 👷 Operador | Cadastrar produtos, ver dashboard |
        | 👔 Gerente | + Relatórios, alertas, lista de compras |
        | 🔑 Admin | Acesso total + gerenciar usuários |

        **Criar novo usuário:**
        1. Vá em **👥 Usuários → Novo Usuário**
        2. Preencha nome, username, e-mail e senha
        3. Escolha o perfil de acesso
        4. Clique **Criar Usuário**

        **Boas práticas de segurança:**
        - Troque a senha padrão `admin123` imediatamente
        - Crie usuários individuais para cada funcionário
        - Use o perfil **Operador** para quem só precisa cadastrar produtos
        - Desative usuários de ex-funcionários (não delete — preserva o histórico)
        """)

    st.markdown("---")
    st.markdown("""
    <div style='text-align:center;color:#888;font-size:0.82rem;'>
      SmartLarder Pro · Dúvidas? Acesse o repositório no GitHub para reportar problemas.
    </div>
    """, unsafe_allow_html=True)
