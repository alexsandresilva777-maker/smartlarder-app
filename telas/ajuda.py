# -*- coding: utf-8 -*-
import streamlit as st

def show_ajuda():
    # 1. SEÇÃO PRINCIPAL (O SEU TEXTO ORIGINAL INTEGRAIS)
    st.markdown("# 📖 Manual de Operação & Documentação Técnica")
    st.markdown("##### Bem-vindo à central de documentação oficial do **SmartLarder Pro**.")
    st.markdown("Este ambiente consolida os procedimentos padrão e arquitetura de níveis de acesso do sistema de inventário.")
    st.markdown("---")

    st.markdown("### 👥 1. Governança de Usuários e Perfis de Acesso")
    st.markdown("""
    O controle de credenciais no banco relacional Supabase obedece a três categorias operacionais rígidas:
    
    * **🔑 Administrador (admin):** Nível irrestrito. É o único perfil autorizado a gerenciar novos usuários, configurar parâmetros globais de infraestrutura, visualizar auditorias de perdas financeiras e extrair logs consolidados de movimentação.
    * **👔 Gerente / Comercial:** Perfil voltado à gestão de compras e almoxarifado. Possui autonomia para catalogar fornecedores, lançar novos lotes, atualizar quantitativos e registrar justificativas de perdas físicas.
    * **👷 Operador / Doméstico:** Perfil simplificado de rotina. Desenvolvido para consultas rápidas na despensa/estoque, geração automática de listas de compras e controle simples de entradas e saídas de mercadoria.
    """)

    st.markdown("### 📊 2. Arquitetura de Movimentações (Entradas e Saídas)")
    st.markdown("""
    Para assegurar a integridade dos relatórios estatísticos e do giro de estoque, os lançamentos devem seguir o padrão:
    
    * **🚚 Entrada Consolidada:** Realizada exclusivamente via aba *Recepção de Carga* para novos lotes de fornecedores cadastrados, exigindo a inclusão mandatória do preço de aquisição e data de validade.
    * **📉 Consumo e Baixa Direta:** Registros de saídas parciais direto na listagem de *Produtos* reduzem o inventário imediatamente.
    * **⚠️ Auditoria de Quebras/Vencimentos:** Itens impróprios para uso não devem ser apenas 'subtraídos' do estoque; devem ser formalizados no módulo *Perdas* para fins de dedução estatística.
    """)

    st.markdown("### 🔔 3. Ativação e Disparo do Alerta SMTP (E-mail)")
    st.markdown("""
    O SmartLarder Pro envia relatórios automatizados sobre vencimentos críticos. Para parametrizar o envio via servidores seguros da Google (Gmail):
    
    1. Acesse o painel de segurança da sua conta Google corporativa ou pessoal em [myaccount.google.com](https://myaccount.google.com).
    2. Certifique-se de que a **Verificação em Duas Etapas** está activa.
    3. Acesse o menu **Senhas de App** (App Passwords) e gere uma nova credencial nomeada como *'SmartLarder'*.
    4. Insira a sequência gerada de **16 dígitos** no campo correspondente da aba *Alertas* dentro do sistema e valide o salvamento.
    """)

    st.markdown("### 🛠️ 4. Guia de Resolução de Erros de Conectividade")
    st.markdown("""
    * **Mensagem 'Access Denied / Privileges Required':** Indica que regras RLS (*Row Level Security*) na sua tabela do Supabase estão bloqueando o select do cliente anônimo. Execute o comando `GRANT SELECT ON public.tabela TO anon;` no editor SQL do Supabase.
    * **🔒 Abas Administrativas Ocultas:** Clique no botão **🚪 Sair** no rodapé do menu esquerdo para expirar o cookie de sessão local e refaça a autenticação para renovar os privilégios.
    """)

    # 2. NOVA SEÇÃO ADICIONADA: DICAS DE MELHOR USO COMPLEMENTARES
    st.markdown("---")
    st.markdown("## 💡 Dicas de Melhor Uso por Público Alvo")
    st.markdown("Para extrair o máximo de eficiência do aplicativo no dia a dia, siga as recomendações práticas abaixo:")

    # Organização das dicas por abas visuais para manter a tela limpa
    tab_com, tab_rep, tab_dom = st.tabs([
        "🏪 Estabelecimentos Comerciais", 
        "👷 Promotores & Repositores", 
        "🏠 Donas de Casa / Doméstico"
    ])

    with tab_com:
        st.markdown("""
        * **Campanhas de Queima de Estoque:** Monitore a aba **Alertas** todas as manhãs. Identificar produtos que vencem em até 7 dias permite criar promoções relâmpago, transformando o que seria perda em faturamento.
        * **Segurança Operacional:** Nunca deixe o tablet ou computador da loja logado no perfil de *Admin*. Crie contas de *Operador* para a equipe de balcão e reposição para evitar alterações acidentais de estoque.
        """)

    with tab_rep:
        st.markdown("""
        * **Regra Prática do PVPS:** Ao organizar as prateleiras ou gôndolas, aplique estritamente o conceito de *Primeiro que Vence, Primeiro que Sai*. Coloque os lotes novos sempre no fundo e puxe os antigos para a frente.
        * **Sincronismo de Avarias:** Se uma embalagem quebrar ou amassar no manuseio, registre o descarte na aba **Perdas** no exato momento do ocorrido para manter o inventário confiável.
        """)

    with tab_dom:
        st.markdown("""
        * **Planejamento de Cardápio:** Consulte os **Alertas** semanais para direcionar as refeições da casa com base nos ingredientes que estão mais próximos do vencimento, reduzindo o desperdício doméstico.
        * **Lista de Compras Automatizada:** Antes de sair de casa para o supermercado, abra o aplicativo para verificar quais itens essenciais estão zerados, evitando compras redundantes ou esquecimentos.
        """)

    # Rodapé de Suporte original mantido
    st.markdown("---")
    c1, c2 = st.columns([6, 2])
    c1.caption("SmartLarder Pro — Sistema de Gestão de Inventário e Validades.")
    c2.markdown("✉️ Suporte ao Usuário: Contate o administrador do banco de dados da aplicação.")
