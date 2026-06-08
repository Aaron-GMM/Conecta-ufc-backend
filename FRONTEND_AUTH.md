# Autenticacao pelo backend

Este backend centraliza o cadastro e o login no Keycloak. O frontend nao precisa usar `keycloak-js` para estas duas acoes iniciais.

## Configuracao necessaria no Keycloak

No client `conecta-ufc-backend`:

- `Client authentication`: `On`
- `Direct access grants`: `On`
- `Service accounts roles`: `On`

Em `Service account roles`, atribua ao client:

- `realm-management` -> `manage-users`

No `.env` do backend:

```env
KEYCLOAK_SERVER_URL=http://localhost:8080/
KEYCLOAK_REALM=conecta-ufc
KEYCLOAK_CLIENT_ID=conecta-ufc-backend
KEYCLOAK_CLIENT_SECRET=cole_o_secret_do_client_backend
FRONTEND_ORIGIN=http://localhost:5173
```

## Cadastro de usuario

Endpoint:

```http
POST /usuarios
```

Body:

```json
{
  "nome": "Joao Silva",
  "email": "joao@email.com",
  "senha": "123456",
  "curso": "Ciencia da Computacao",
  "oportunidades": ["bolsa", "estagio", "monitoria"]
}
```

## Login

Endpoint:

```http
POST /usuarios/login
```

Body:

```json
{
  "email": "joao@email.com",
  "senha": "123456"
}
```
