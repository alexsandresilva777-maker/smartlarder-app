# -*- coding: utf-8 -*-
import streamlit as st

def show_ajuda():
    st.markdown("## 💡 Central de Ajuda e Boas Práticas")
    st.markdown("---")
    st.markdown("Seja bem-vindo ao **SmartLarder Pro**! Escolha o seu perfil abaixo para ver as dicas rápidas de utilização e garantir a máxima eficiência no controle do estoque.")

    # Criação das abas para organizar o conteúdo por público-alvo
    tab1, tab2, tab3, tab4 = st.tabs([
        "👷 Promotores & Repositores", 
        "🏠 Uso Doméstico", 
        "🏪 Estabelecimentos Comerciais",
        "❓ Dúvidas Frequentes"
    ])

    # 1. ABA: PROMOTORES DE VENDAS E REPOSITORES
    with tab1:
        st.markdown("### 🚚 Guia Rápido para Promotores e Repositores")
        st.markdown("""
        Seu papel é fundamental para manter o estoque físico perfeitamente sincronizado com o sistema. Siga esta rotina:

        * **Atenção Máxima na Recepção de Carga:** Ao receber novos paletes ou caixas, confira o código de barras (EAN) antes de guardar o produto na prateleira. Se o código não estiver cadastrado, use a aba **Cadastrar**.
        * **Regra de Ouro (PVPS):** O primeiro que vence é o primeiro que sai. Ao abastecer as gôndolas ou o estoque, coloque sempre os produtos com **validade mais próxima na frente** e os mais novos atrás.
        * **Registre as Perdas na Hora:** Encontrou uma embalagem rasgada, amassada ou um produto vencido no fundo da prateleira? Vá direto na aba **Perdas** e faça o registro para evitar furos no estoque.
        * **Volume Inicial:** Quando cadastrar um item novo, lembre-se de lançar a quantidade que está entrando fisicamente no momento.
        """)
        st.info("💡 **Dica de Campo:** Se o scanner de câmera não focar de primeira, certifique-se de que o código de barras está bem iluminado e sem reflexos da embalagem plástica.")

    # 2. ABA: DONAS DE CASA (USO DOMÉSTICO)
    with tab2:
        st.markdown("### 🍏 Guia Rápido para Organização Doméstica")
        st.markdown("""
        O SmartLarder Pro também é perfeito para evitar o desperdício de alimentos em casa e economizar na hora das compras!

        * **Evite o Desperdício:** Monitore semanalmente a aba **Alertas**. O sistema avisa quais itens da sua despensa vão vencer nos próximos 7 dias. Planeje o cardápio da semana com base neles!
        * **Lista de Compras Inteligente:** Antes de ir ao supermercado, consulte a aba **Lista de Compras**. O sistema gera automaticamente a lista dos itens que estão zerados ou abaixo do limite mínimo necessário para a sua casa.
        * **Entrada e Saída Simples:** Criou o hábito de usar o sistema? Sempre que consumir o último item de uma caixa (como uma caixa de leite ou um pacote de arroz), atualize a quantidade para manter sua despensa real.
        """)
        st.success("🏠 **Dica de Organização:** Separe sua despensa doméstica por categorias básicas no cadastro (ex: Alimentos, Limpeza, Higiene) para facilitar a visualização nos Relatórios.")

    # 3. ABA: ESTABELECIMENTOS COMERCIAIS
    with tab3:
        st.markdown("### 🏪 Guia Rápido para Comércio (Mercearias, Padarias, Minimercados)")
        st.markdown("""
        Para comércios, o controle rígido evita prejuízos financeiros e multas de fiscalização.

        * **Auditoria de Validades:** Utilize a central de **Alertas** diariamente. Produtos vencidos expostos geram penalidades graves. Use o relatório para fazer promoções de queima de estoque (bota-fora) dos itens próximos ao vencimento.
        * **Gestão por Perfis (Níveis de Acesso):** * Mantenha os seus repositores e caixas no perfil de **Operador** (eles apenas consultam e dão entrada/saída).
            * Deixe o perfil de **Admin** apenas com a gerência para evitar alterações acidentais de senhas ou exclusão de dados.
        * **Histórico de Movimentações:** Use o painel de **Relatórios** para entender o giro das suas mercadorias — descubra quais marcas vendem mais rápido e quais estão paradas ocupando espaço.
        """)
        st.warning("🔒 **Nota de Segurança:** Nunca compartilhe a senha do seu usuário Administrador. Cadastre um usuário individual para cada colaborador na aba **Usuários**.")

    # 4. ABA: DÚVIDAS FREQUENTES
    with tab4:
        st.markdown("### ❓ Perguntas Frequentes (FAQ)")
        
        with st.expander("O sistema funciona sem internet?"):
            st.write("Não. Como os dados de estoque e usuários ficam guardados com segurança na nuvem do Supabase, o aplicativo precisa de conexão com a internet (Wi-Fi ou dados móveis) para atualizar as informações em tempo real.")
            
        with st.expander("O que fazer se um código de barras não for reconhecido?"):
            st.write("Verifique se o número digitado está correto. Se o produto for novo, vá até a aba **Cadastrar**, insira o código manualmente e preencha os dados do item pela primeira vez. Nas próximas consultas, ele será achado instantaneamente.")
            
        with st.expander("Os dados inseridos podem sumir ou resetar sozinhos?"):
            st.write("Não! Toda vez que você salva um produto, uma carga ou um usuário, a informação é gravada permanentemente no seu banco de dados em nuvem. O aplicativo está blindado contra perdas de dados.")

    st.markdown("---")
    st.caption("SmartLarder Pro — Sistema de Gestão e Monitoramento de Validades.")
