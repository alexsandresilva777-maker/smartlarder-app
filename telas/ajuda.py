# -*- coding: utf-8 -*-
import streamlit as st

def show_ajuda():
    st.markdown("## ❓ Manual de Operação & Documentação Técnica")
    st.markdown("---")
    
    st.markdown("""
    Bem-vindo à central de documentação oficial do **SmartLarder Pro**. Este ambiente consolida os 
    procedimentos padrão e arquitetura de níveis de acesso do sistema de inventário.
    """)
    
    with st.expander("👥 1. Governança de Usuários e Perfis de Acesso", expanded=True):
        st.markdown("""
        O controle de credenciais no banco relacional Supabase obedece a três categorias operacionais rígidas:
        
        * 🔑 **Administrador (admin):** Nível irrestrito. É o único perfil autorizado a gerenciar novos usuários, configurar parâmetros globais de infraestrutura, visualizar auditorias de perdas financeiras e extrair logs consolidados de movimentação.
        * 👔 **Gerente / Comercial:** Perfil voltado à gestão de compras e almoxarifado. Possui autonomia para catalogar fornecedores, lançar novos lotes, atualizar quantitativos e registrar justificativas de perdas físicas.
        * 👷 **Operador / Doméstico:** Perfil simplificado de rotina. Desenvolvido para consultas rápidas na despensa/estoque, geração automática de listas de compras e controle simples de entradas e saídas de mercadoria.
        """)
        
    with st.expander("📊 2. Arquitetura de Movimentações (Entradas e Saídas)"):
        st.markdown("""
        Para assegurar a integridade dos relatórios estatísticos e do giro de estoque, os lançamentos devem seguir o padrão:
        
        1. **Entrada Consolidada:** Realizada exclusivamente via aba *Recepção de Carga* para novos lotes de fornecedores cadastrados, exigindo a inclusão mandatória do preço de aquisição e data de validade.
        2. **Consumo e Baixa Direta:** Registros de saídas parciais direto na listagem de *Produtos* reduzem o inventário imediatamente.
        3. **Auditoria de Quebras/Vencimentos:** Itens impróprios para uso não devem ser apenas 'subtraídos' do estoque; devem ser formalizados no módulo *Perdas* para fins de dedução estatística.
        """)
        
    with st.expander("🔔 3. Ativação e Disparo do Alerta SMTP (E-mail)"):
        st.markdown("""
        O SmartLarder Pro envia relatórios automatizados sobre vencimentos críticos. Para parametrizar o envio via servidores seguros da Google (Gmail):
        
        1. Acesse o painel de segurança da sua conta Google corporativa ou pessoal em [myaccount.google.com](https://myaccount.google.com).
        2. Certifique-se de que a **Verificação em Duas Etapas** está ativa.
        3. Acesse o menu **Senhas de App** (*App Passwords*) e gere uma nova credencial nomeada como 'SmartLarder'.
        4. Insira a sequência gerada de 16 dígitos no campo correspondente da aba *Alertas* dentro do sistema e valide o salvamento.
        """)

    with st.expander("🛠️ 4. Guia de Resolução de Erros de Conectividade"):
        st.markdown("""
        * **Mensagem 'Access Denied / Privileges Required':** Indica que regras RLS (Row Level Security) na sua tabela do Supabase estão bloqueando o select do cliente anônimo. Execute o comando `GRANT SELECT ON public.tabela TO anon` no editor SQL do Supabase.
        * **Abas Administrativas Ocultas:** Clique no botão 🚪 *Sair* no rodapé do menu esquerdo para expirar o cookie de sessão local e refaça a autenticação para renovar os privilégios.
        """)
        
    st.info("✉️ **Suporte ao Usuário:** Para esclarecimento de dúvidas estruturais, contate o administrador do banco de dados da aplicação.")
