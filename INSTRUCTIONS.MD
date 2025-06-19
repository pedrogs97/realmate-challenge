# 🧪 Instruções de Execução — Realmate Challenge

Este projeto implementa uma API assíncrona de mensagens via webhooks utilizando Django, Django Rest Framework, Celery, Redis e PostgreSQL, conforme os requisitos do desafio técnico da Realmate.

---

## ✅ Pré-requisitos

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Poetry](https://python-poetry.org/) (opcional, usado em desenvolvimento local)

---

## 📦 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/pedrogs97/realmate-challenge.git
cd realmate-challenge
```

### 2. Configure o `.env`

Crie um arquivo `.env` na raiz do projeto com base no `.env.example`:

```bash
cp .env.example .env
```

---

## 🚀 Subindo o ambiente com Docker

### 1. Suba todos os serviços

```bash
docker-compose up --build
```

### 2. Acesse o container `web` e aplique as migrações:

```bash
docker-compose exec web bash
python manage.py migrate
```

## 🌐 Endpoints Disponíveis

### POST `/webhook/`

Recebe eventos do tipo:

- `NEW_CONVERSATION`
- `NEW_MESSAGE`
- `CLOSE_CONVERSATION`

Exemplo de criação de conversa:

```bash
curl -X POST http://localhost:8000/webhook/   -H "Content-Type: application/json"   -d '{
    "type": "NEW_CONVERSATION",
    "timestamp": "2025-06-04T14:20:00Z",
    "data": {
      "id": "6a41b347-8d80-4ce9-84ba-7af66f369f6a"
    }
  }'
```

---

### GET `/conversations/{id}/`

Retorna o status da conversa e as mensagens relacionadas:

```bash
curl http://localhost:8000/conversations/6a41b347-8d80-4ce9-84ba-7af66f369f6a/
```

---

## ⚙️ O que está rodando

| Serviço        | Porta  | Descrição                        |
|----------------|--------|----------------------------------|
| Django API     | 8000   | Backend principal da aplicação   |
| PostgreSQL     | 5432   | Banco de dados relacional        |
| Redis          | 6379   | Broker do Celery + Buffer Cache  |
| Celery Worker  | —      | Processa tarefas assíncronas     |

---

## 🧹 Resetando o ambiente

```bash
docker-compose down -v
docker-compose up --build
docker-compose exec web python manage.py migrate
```
---