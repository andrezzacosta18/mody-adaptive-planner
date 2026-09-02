import streamlit as st


def show_privacy_policy():
    """
    Renderiza a Política de Privacidade do Mody.
    """

    st.title("Política de Privacidade — Mody")

    st.caption("Última atualização: 2 de setembro de 2026")

    st.markdown(
        """
O Mody é uma aplicação de produtividade criada para ajudar pessoas
a organizar tarefas, compromissos e rotinas de forma mais simples
e personalizada.

Esta Política de Privacidade explica quais informações podem ser
tratadas pelo Mody, por que são utilizadas e quais opções estão
disponíveis aos usuários.

## 1. Informações que o Mody pode armazenar

Ao utilizar o Mody, algumas informações podem ser armazenadas para
permitir o funcionamento da aplicação.

### Dados da conta

- endereço de e-mail;
- identificador interno da conta.

### Dados de perfil

- nome ou apelido informado pelo usuário;
- fuso horário.

### Preferências de personalização

O usuário pode selecionar voluntariamente necessidades práticas de
organização, como:

- organizar tarefas;
- começar tarefas com mais facilidade;
- manter o foco;
- evitar sobrecarga;
- planejar a rotina;
- lembrar compromissos;
- dividir tarefas maiores em passos menores.

Essas preferências são opcionais.

### Conteúdo criado pelo usuário

O Mody pode armazenar informações inseridas pelo próprio usuário,
como tarefas e compromissos.

### Check-ins

O usuário pode registrar voluntariamente um estado momentâneo por
meio das opções disponibilizadas pelo Mody, como estar bem,
sentir-se sobrecarregado ou querer desacelerar.

O Mody não solicita níveis de ansiedade, energia ou foco nos
check-ins reais.

## 2. Como essas informações são utilizadas

As informações armazenadas podem ser utilizadas para:

- criar e autenticar a conta;
- disponibilizar tarefas e compromissos;
- manter preferências escolhidas pelo usuário;
- adaptar determinadas funcionalidades à forma como o usuário
  deseja organizar seu dia;
- apresentar informações relacionadas à própria utilização do Mody;
- manter a segurança e o funcionamento da aplicação.

O Mody procura utilizar apenas as informações necessárias para
oferecer suas funcionalidades.

## 3. Produtividade e bem-estar

O Mody é uma ferramenta de produtividade e organização pessoal.

O aplicativo não realiza diagnósticos médicos ou psicológicos,
não calcula risco de saúde mental e não substitui avaliação,
diagnóstico, aconselhamento ou tratamento realizado por
profissionais qualificados.

Os check-ins e sugestões disponibilizados pelo aplicativo têm
finalidade exclusivamente organizacional e de apoio à utilização
das funcionalidades do Mody.

## 4. Dados utilizados para demonstrações e análises

O Mody pode utilizar dados sintéticos para desenvolvimento, testes,
demonstrações e funcionalidades analíticas.

Dados sintéticos são dados artificialmente gerados e não
correspondem aos dados pessoais ou check-ins reais dos usuários.

Por isso, métricas apresentadas em áreas demonstrativas podem
incluir variáveis que não são coletadas dos usuários reais.

## 5. Armazenamento e fornecedores

O Mody utiliza serviços tecnológicos de terceiros necessários ao
funcionamento da aplicação, incluindo serviços de autenticação,
banco de dados e envio de e-mails relacionados à conta.

Esses fornecedores podem processar as informações necessárias para
prestar seus respectivos serviços.

O acesso aos dados da aplicação é protegido por mecanismos de
autenticação e controles de acesso destinados a impedir que um
usuário tenha acesso aos dados pertencentes a outro usuário.

## 6. Recuperação de conta

O endereço de e-mail pode ser utilizado para funcionalidades
relacionadas à conta, incluindo confirmação de cadastro e
recuperação de senha.

O Mody não armazena a senha do usuário no banco de dados da
aplicação.

## 7. Exclusão da conta

O usuário pode excluir sua conta diretamente pelo Mody através da
opção **Excluir minha conta**.

A exclusão da conta é permanente e remove os dados associados à
conta armazenados nas tabelas da aplicação conforme o
funcionamento implementado pelo serviço.

Antes da exclusão, o Mody solicita confirmação do usuário.

## 8. Segurança

O Mody utiliza medidas técnicas destinadas a proteger os dados dos
usuários, incluindo autenticação e regras de acesso aos dados.

Apesar dessas medidas, nenhum sistema conectado à internet pode
garantir segurança absoluta.

## 9. Direitos do usuário

Dependendo da legislação aplicável, o usuário poderá ter direitos
relacionados aos seus dados pessoais, incluindo direitos de acesso,
correção e exclusão.

A funcionalidade de exclusão da conta está disponível diretamente
no aplicativo.

Para outras solicitações relacionadas à privacidade, o usuário
poderá utilizar o canal de contato indicado nesta política.

## 10. Alterações nesta Política

Esta Política de Privacidade poderá ser atualizada quando houver
alterações nas funcionalidades do Mody, nos serviços utilizados ou
na forma como as informações são tratadas.

A data da versão mais recente será indicada no início desta página.

## 11. Contato

Para dúvidas ou solicitações relacionadas à privacidade e ao
tratamento de dados pessoais:

**E-mail:** modyapp.contato@gmail.com
        """
    )