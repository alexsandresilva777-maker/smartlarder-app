import streamlit as st

def show_ajuda():
    st.title("📖 Guia do Usuário - SmartLarder Pro")
    st.markdown("---")
    
    st.info("💡 **Dica do Desenvolvedor:** Este guia foi criado para ajudar você a dominar sua despensa. Explore os tópicos abaixo para tirar o máximo proveito do sistema.")

    # Seção 1: Acesso
    with st.expander("🔐 1. Acesso e Segurança", expanded=True):
        st.write("""
        - **Login:** Utilize seu e-mail e senha cadastrados.
        - **Privacidade:** Suas informações de estoque são privadas e protegidas por criptografia.
        - **Sair:** Sempre clique no botão 'Sair' ao terminar, especialmente em dispositivos compartilhados.
        """)

    # Seção 2: Gestão de Estoque
    with st.expander("📦 2. Gestão de Produtos (Entradas e Saídas)"):
        st.write("""
        - **Cadastrar:** Use o menu 'Cadastro' para novos itens. Informe sempre a validade para receber alertas.
        - **Dar Baixa:** Quando consumir um item, vá em 'Produtos' e diminua a quantidade. Isso mantém sua **Lista de Compras** precisa.
        - **Estoque Mínimo:** Defina um limite (ex: 2 unidades). Quando o estoque chegar nesse número, o item aparecerá automaticamente na sua lista de compras.
        """)

    # Seção 3: Câmera e Scanner
    with st.expander("📷 3. Uso da Câmera e Scanner"):
        st.write("""
        - **Permissão:** Ao clicar em escanear, seu navegador pedirá permissão para usar a câmera. Clique em **'Permitir'**.
        - **Dica de Leitura:** Procure locais bem iluminados e mantenha a embalagem firme. Se o código estiver amassado, prefira o cadastro manual.
        - **Limpeza:** Às vezes, marcas de dedo na lente do celular dificultam o foco. Uma limpeza rápida resolve!
        """)

    # Seção 4: Alertas e E-mail
    with st.expander("📧 4. Configurando Alertas por E-mail"):
        st.warning("⚠️ **Segurança:** Nunca utilize sua senha pessoal de e-mail no sistema.")
        st.write("""
        Para receber avisos de vencimento, você precisa de uma **Senha de App** do Google:
        
        1. Acesse sua **Conta Google** e vá em **Segurança**.
        2. Ative a **Verificação em duas etapas**.
        3. Procure por **'Senhas de app'** na busca da conta.
        4. Gere uma senha para o app 'SmartLarder' e copie o código de 16 dígitos.
        5. Cole este código nas configurações de e-mail do sistema.
        """)

    # Seção 5: Lista de Compras
    with st.expander("🛒 5. Lista de Compras Inteligente"):
        st.write("""
        A lista é atualizada em tempo real com base em três critérios:
        1. Produtos com estoque **zerado**.
        2. Produtos abaixo do **estoque mínimo** definido por você.
        3. Produtos **vencidos** que precisam ser descartados e repostos.
        """)

    # Seção 6: FAQ
    with st.expander("❓ Perguntas Frequentes (FAQ)"):
        st.markdown("""
        **Posso acessar de dois celulares?**  
        Sim! Como os dados estão na nuvem, você e sua família podem acessar o mesmo estoque simultaneamente.
        
        **O sistema funciona sem internet?**  
        Não. Para garantir que seus dados estejam sempre sincronizados e seguros, é necessária uma conexão ativa.
        
        **Esqueci minha senha, e agora?**  
        Entre em contato com o administrador do sistema para solicitar a redefinição através do módulo de Usuários.
        """)

    st.markdown("---")
    st.success("✅ **SmartLarder Pro v3.1** — Organização gera economia!")