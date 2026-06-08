# Autenticacao pelo backend

Este backend centraliza o cadastro e o login no Keycloak. O frontend nao precisa usar `keycloak-js` para estas duas acoes iniciais.

## Subindo o Keycloak de desenvolvimento

O repositorio ja traz um `docker-compose.yml` com um realm importado para teste local.

```bash
docker compose up -d keycloak
```

Depois de subir, o painel fica em:

- URL: `http://localhost:8080`
- Usuario admin: `admin`
- Senha admin: `admin`
- Realm: `conecta-ufc`

O import cria estes clients:

- `conecta-ufc-backend`: client confidencial usado pela API FastAPI.
- `conecta-ufc-frontend`: client publico para uso futuro do frontend, se necessario.

No backend, use os mesmos valores do arquivo `conecta-ufc-backend/.env.example`.

```bash
cp conecta-ufc-backend/.env.example conecta-ufc-backend/.env
```

```env
KEYCLOAK_SERVER_URL=http://localhost:8080/
KEYCLOAK_REALM=conecta-ufc
KEYCLOAK_CLIENT_ID=conecta-ufc-backend
KEYCLOAK_CLIENT_SECRET=conecta-ufc-dev-secret
FRONTEND_ORIGIN=http://localhost:5173
```

## Configuracao manual equivalente no Keycloak

No client `conecta-ufc-backend`:

- `Client authentication`: `On`
- `Direct access grants`: `On`
- `Service accounts roles`: `On`

Em `Service account roles`, atribua ao client:

- `realm-management` -> `manage-users`

No `.env` do backend, o segredo precisa ser o mesmo configurado no client:

```env
KEYCLOAK_SERVER_URL=http://localhost:8080/
KEYCLOAK_REALM=conecta-ufc
KEYCLOAK_CLIENT_ID=conecta-ufc-backend
KEYCLOAK_CLIENT_SECRET=conecta-ufc-dev-secret
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
