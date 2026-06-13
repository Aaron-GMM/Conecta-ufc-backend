# Guia da integracao Keycloak no Conecta UFC

Este documento explica o que foi feito no backend, por que cada parte existe e como o frontend deve consumir cadastro e login pela API.

## Objetivo

A ideia foi deixar o frontend sem precisar conversar diretamente com o Keycloak para cadastro e login.

O fluxo ficou assim:

```txt
Cadastro:
Frontend -> Backend FastAPI -> Keycloak

Login:
Frontend -> Backend FastAPI -> Keycloak

Depois do login:
Frontend guarda o access_token retornado pelo backend
```

## Tecnologias usadas

- FastAPI: framework Python usado para criar as rotas HTTP.
- Keycloak: servidor de identidade, responsavel por usuarios, senha, login e tokens.
- python-keycloak: biblioteca Python usada pelo backend para conversar com o Keycloak.
- python-dotenv: biblioteca usada para carregar variaveis do arquivo `.env`.
- CORS do FastAPI: configuracao que permite o frontend em `localhost:5173` chamar o backend em outra porta.

## Arquivos criados ou alterados

### `conecta-ufc-backend/app/core/config.py`

Centraliza as configuracoes do Keycloak e do frontend.

Ele carrega o arquivo:

```txt
conecta-ufc-backend/.env
```

Variaveis usadas:

```env
KEYCLOAK_SERVER_URL=http://localhost:8080/
KEYCLOAK_REALM=conecta-ufc
KEYCLOAK_CLIENT_ID=conecta-ufc-backend
KEYCLOAK_CLIENT_SECRET=secret_do_client_backend
FRONTEND_ORIGIN=http://localhost:5173
```

O `KEYCLOAK_CLIENT_SECRET` e sensivel. Ele deve ficar somente no backend.

### `conecta-ufc-backend/app/main.py`

Cria a aplicacao FastAPI e registra as rotas.

Tambem configura CORS para permitir chamadas vindas do frontend:

```txt
http://localhost:5173
```

Sem CORS, o navegador bloquearia chamadas do frontend para o backend, mesmo que a API estivesse funcionando.

### `conecta-ufc-backend/app/schemas/usuario.py`

Define os formatos de entrada e saida das rotas.

Cadastro recebe:

```json
{
  "nome": "Joao Silva",
  "email": "joao@email.com",
  "senha": "123456",
  "curso": "Ciencia da Computacao",
  "oportunidades": ["bolsa", "estagio", "monitoria"]
}
```

Login recebe:

```json
{
  "email": "joao@email.com",
  "senha": "123456"
}
```

### `conecta-ufc-backend/app/services/keycloak_service.py`

Contem a comunicacao real com o Keycloak.

Foram criadas duas funcoes principais:

```python
criar_usuario_keycloak(usuario)
```

Cria um usuario no Keycloak usando a Admin API.

```python
login_keycloak(login)
```

Envia email e senha ao Keycloak e recebe tokens.

### `conecta-ufc-backend/app/api/routes/usuarios.py`

Expoe as rotas HTTP que o frontend vai chamar.

Rotas atuais:

```http
POST /usuarios
POST /usuarios/login
```

## Como o cadastro funciona

O frontend chama:

```http
POST http://localhost:8000/usuarios
```

Com body:

```json
{
  "nome": "Joao Silva",
  "email": "joao@email.com",
  "senha": "123456",
  "curso": "Ciencia da Computacao",
  "oportunidades": ["bolsa", "estagio"]
}
```

O backend transforma isso em um payload do Keycloak:

```json
{
  "username": "joao@email.com",
  "email": "joao@email.com",
  "firstName": "Joao Silva",
  "enabled": true,
  "emailVerified": true,
  "attributes": {
    "curso": ["Ciencia da Computacao"],
    "oportunidades": ["bolsa", "estagio"]
  },
  "credentials": [
    {
      "type": "password",
      "value": "123456",
      "temporary": false
    }
  ]
}
```

O `curso` e as `oportunidades` ficam salvos como atributos do usuario no Keycloak.

## Como o login funciona

O frontend chama:

```http
POST http://localhost:8000/usuarios/login
```

Com body:

```json
{
  "email": "joao@email.com",
  "senha": "123456"
}
```

O backend chama o Keycloak usando Direct Access Grants.

Se o email e a senha estiverem corretos, o backend retorna:

```json
{
  "access_token": "token-de-acesso",
  "refresh_token": "token-de-renovacao",
  "expires_in": 300,
  "refresh_expires_in": 1800,
  "token_type": "Bearer"
}
```

O frontend deve guardar o `access_token` e usar depois em rotas protegidas.

## O que e Direct Access Grants

Direct Access Grants e o fluxo em que uma aplicacao envia usuario e senha diretamente para o Keycloak em troca de tokens.

Neste projeto, quem envia usuario e senha ao Keycloak e o backend.

Isso permite que o frontend simplesmente chame:

```txt
POST /usuarios/login
```

Ponto importante: esse fluxo e mais simples, mas em muitos sistemas modernos o fluxo recomendado e o login por redirecionamento usando Authorization Code + PKCE. Aqui foi escolhido o caminho mais simples porque o objetivo atual e centralizar cadastro e login no backend.

## O que e access_token

O `access_token` e a prova de que o usuario fez login.

Depois que o frontend recebe esse token, ele pode chamar futuras rotas protegidas assim:

```js
const token = localStorage.getItem("access_token");

await fetch("http://localhost:8000/alguma-rota-protegida", {
  headers: {
    Authorization: `Bearer ${token}`,
  },
});
```

Ainda nao implementamos validacao de token nas rotas protegidas. Isso sera necessario quando houver rotas que dependam de usuario logado.

## Configuracao necessaria no Keycloak

No realm:

```txt
conecta-ufc
```

No client:

```txt
conecta-ufc-backend
```

Configurar:

```txt
Client authentication: On
Direct access grants: On
Service accounts roles: On
```

Depois, em `Service account roles`, adicionar:

```txt
realm-management -> manage-users
```

Essa permissao permite que o backend crie usuarios no Keycloak.

## Como rodar o backend

Na pasta principal do repositorio:

```bash
cd /home/jacdev/Programing/ES/Conecta-ufc-backend/conecta-ufc-backend
source ../.venv/bin/activate
uvicorn app.main:app --reload
```

A API deve ficar disponivel em:

```txt
http://localhost:8000
```

Documentacao automatica do FastAPI:

```txt
http://localhost:8000/docs
```

## Como testar com curl

Cadastro:

```bash
curl -X POST http://localhost:8000/usuarios \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Usuario Teste",
    "email": "usuario.teste@email.com",
    "senha": "123456",
    "curso": "Ciencia da Computacao",
    "oportunidades": ["bolsa", "estagio"]
  }'
```

Login:

```bash
curl -X POST http://localhost:8000/usuarios/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario.teste@email.com",
    "senha": "123456"
  }'
```

## O que ainda falta no futuro

Ainda nao foi feita a validacao do `access_token` nas rotas protegidas.

Quando o sistema tiver rotas que so usuarios logados podem acessar, sera necessario:

1. Ler o header `Authorization: Bearer <token>`.
2. Validar o token emitido pelo Keycloak.
3. Descobrir quem e o usuario.
4. Permitir ou negar acesso.

Tambem sera util criar:

- refresh de token;
- logout;
- recuperacao de senha;
- tratamento melhor para email ja cadastrado;
- separacao entre mensagens de erro internas e mensagens para o frontend.

## Fontes e documentacoes

### Keycloak

- Documentacao geral: https://www.keycloak.org/documentation
- Securing Applications and Services: https://www.keycloak.org/docs/latest/securing_apps/
- Server Administration Guide: https://www.keycloak.org/docs/latest/server_admin/
- Admin REST API: https://www.keycloak.org/docs-api/latest/rest-api/
- Endpoint OpenID do realm: `http://localhost:8080/realms/conecta-ufc/.well-known/openid-configuration`

### python-keycloak

- Documentacao principal: https://python-keycloak.readthedocs.io/
- Admin client: https://python-keycloak.readthedocs.io/en/v5.7.0/modules/admin.html
- PyPI: https://pypi.org/project/python-keycloak/

### FastAPI

- Documentacao principal: https://fastapi.tiangolo.com/
- CORS no FastAPI: https://fastapi.tiangolo.com/tutorial/cors/
- Security no FastAPI: https://fastapi.tiangolo.com/tutorial/security/

### python-dotenv

- PyPI: https://pypi.org/project/python-dotenv/

## Videos para estudar

Use estes termos ou links como ponto de partida:

- Keycloak para iniciantes: https://www.youtube.com/results?search_query=keycloak+tutorial+for+beginners
- Keycloak Direct Access Grants: https://www.youtube.com/results?search_query=keycloak+direct+access+grants
- Keycloak com FastAPI: https://www.youtube.com/results?search_query=keycloak+fastapi+python
- FastAPI para iniciantes: https://www.youtube.com/results?search_query=fastapi+tutorial+for+beginners
- FastAPI CORS: https://www.youtube.com/results?search_query=fastapi+cors+tutorial

## Prompt para estudar no ChatGPT

Copie e cole este prompt em outro ChatGPT:

```txt
Quero que voce aja como um tutor paciente e tecnico. Eu tenho um backend FastAPI integrado com Keycloak para cadastro e login de usuarios.

Contexto do projeto:
- Backend em Python com FastAPI.
- Frontend em JavaScript/Vite rodando em http://localhost:5173.
- Keycloak rodando em http://localhost:8080.
- Realm: conecta-ufc.
- Client confidencial do backend: conecta-ufc-backend.
- O backend expoe POST /usuarios para cadastrar usuario.
- O backend expoe POST /usuarios/login para fazer login.
- O cadastro recebe nome, email, senha, curso e oportunidades.
- O backend salva curso e oportunidades como attributes do usuario no Keycloak.
- O login usa Direct Access Grants no Keycloak e retorna access_token, refresh_token, expires_in, refresh_expires_in e token_type.
- O backend usa python-keycloak, python-dotenv e CORS do FastAPI.

Quero que voce me ensine, passo a passo:
1. O que e Keycloak.
2. O que e realm.
3. O que e client confidencial.
4. O que e client secret.
5. O que e service account.
6. Por que o backend precisa da role realm-management/manage-users.
7. O que e Direct Access Grants.
8. Como o backend cria usuarios no Keycloak.
9. Como o backend faz login no Keycloak.
10. O que sao access_token e refresh_token.
11. O que e Bearer token.
12. Por que o CORS foi necessario.
13. Como o frontend deve chamar POST /usuarios.
14. Como o frontend deve chamar POST /usuarios/login.
15. O que ainda falta para proteger rotas usando o access_token.

Explique de forma simples, com analogias, exemplos de requisicao HTTP e pequenos trechos de codigo. Nao pule conceitos. Ao final, me faca perguntas para verificar se eu entendi.
```
