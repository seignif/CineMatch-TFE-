# CineMatch 🎬

> Plateforme web de matchmaking pour cinéphiles belges — TFE EPHEC 2025-2026

## Stack technique

| Couche | Technologies |
|--------|-------------|
| Backend | Python 3.13, Django 5.1, DRF, Django Channels, Celery |
| Frontend | React 18, TypeScript 5, Vite, TailwindCSS |
| Base de données | PostgreSQL 15 |
| Cache / Broker | Redis 7.2 |
| APIs externes | TMDb, allocine-seances |

## Démarrage rapide

### 1. Prérequis
- Docker Desktop (pour PostgreSQL + Redis)
- Python 3.11+
- Node.js 18+

### 2. Infrastructure (Docker)

```bash
docker compose up -d
```

### 3. Backend

```bash
cd backend
venv/Scripts/activate          # Windows
# ou: source venv/bin/activate  # Linux/Mac

# Configuration
cp .env.example .env           # Édite TMDB_API_KEY

# Base de données
python manage.py migrate
python manage.py createsuperuser

# Serveur
python manage.py runserver
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

### 5. Celery (optionnel pour le dev)

```bash
cd backend
# Worker
celery -A config worker -l info

# Beat (tâches périodiques)
celery -A config beat -l info
```

## URLs de développement

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000/api/ |
| Admin Django | http://localhost:8000/admin/ |
| WebSocket | ws://localhost:8000/ws/chat/:id/ |

## Structure du projet

```
CineMatch/
├── backend/           # Django + DRF
│   ├── config/        # Settings, URLs, ASGI, Celery
│   ├── apps/
│   │   ├── users/     # Authentification, profils
│   │   ├── films/     # Films, cinémas, séances + services TMDb/AlloCiné
│   │   ├── matching/  # Swipe, matchs, algorithme
│   │   └── chat/      # WebSocket, messages
│   └── api/           # Routage API global
├── frontend/          # React + TypeScript
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── services/  # API calls, WebSocket
│       ├── types/     # Types TypeScript
│       └── hooks/
└── docker-compose.yml # PostgreSQL + Redis
```

## Développement

**Étudiant :** Noah Rogier
**École :** EPHEC — Technologies de l'Informatique (3TI)
**Superviseur :** Louis Van Dormael
**Client pilote :** Kinepolis Braine-l'Alleud
