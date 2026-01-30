# 🚀 BID-KILLER ENGINE - Backend API

Backend FastAPI complet pour l'analyse automatique de DCE BTP avec IA.

---

## 📋 TABLE DES MATIÈRES

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Démarrage](#démarrage)
4. [Architecture](#architecture)
5. [API Endpoints](#api-endpoints)
6. [Stripe Setup](#stripe-setup)
7. [Déploiement](#déploiement)

---

## 🔧 INSTALLATION

### Prérequis

- Python 3.10+
- PostgreSQL 14+
- Compte Anthropic (API Claude)
- Compte Stripe (paiements)

### Étape 1 : Cloner & Setup

```bash
cd bid-killer-backend

# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt
```

### Étape 2 : Base de Données PostgreSQL

```bash
# Installation PostgreSQL (Ubuntu/Debian)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Créer la base de données
sudo -u postgres psql
CREATE DATABASE bidkiller_db;
CREATE USER bidkiller WITH PASSWORD 'votre_mot_de_passe';
GRANT ALL PRIVILEGES ON DATABASE bidkiller_db TO bidkiller;
\q
```

---

## ⚙️ CONFIGURATION

### Étape 1 : Variables d'environnement

```bash
# Copier le template
cp .env.example .env

# Éditer le fichier .env
nano .env
```

### Étape 2 : Remplir les variables CRITIQUES

```bash
# 1. Database
DATABASE_URL=postgresql://bidkiller:votre_mot_de_passe@localhost:5432/bidkiller_db

# 2. Secret Key (IMPORTANT !)
# Générer une clé unique :
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Copier le résultat dans SECRET_KEY

# 3. Anthropic API
# Obtenir sur : https://console.anthropic.com/settings/keys
ANTHROPIC_API_KEY=sk-ant-api03-VOTRE_CLE_ICI

# 4. Stripe (voir section Stripe Setup ci-dessous)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

---

## 🚀 DÉMARRAGE

### Mode Développement

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Lancer le serveur (avec hot reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

L'API sera accessible sur : **http://localhost:8000**

Documentation interactive : **http://localhost:8000/docs**

### Vérification

```bash
# Test de santé
curl http://localhost:8000/health

# Réponse attendue :
{
  "status": "healthy",
  "database": "connected",
  "api": "operational"
}
```

---

## 🏗️ ARCHITECTURE

### Structure du Projet

```
bid-killer-backend/
├── app/
│   ├── main.py              # Point d'entrée FastAPI
│   ├── config.py            # Configuration & Settings
│   ├── database.py          # SQLAlchemy models & DB
│   ├── routes/
│   │   ├── auth.py          # Authentification (JWT)
│   │   ├── users.py         # Gestion utilisateurs
│   │   ├── subscriptions.py # Stripe subscriptions
│   │   ├── analysis.py      # Analyse DCE (upload)
│   │   └── export_routes.py # Export DOCX/PDF
│   └── services/
│       └── claude_service.py # Intégration Claude AI
├── requirements.txt
├── .env.example
└── README.md
```

### Stack Technique

- **Framework** : FastAPI 0.109
- **Database** : PostgreSQL + SQLAlchemy (async)
- **Auth** : JWT (python-jose)
- **Passwords** : bcrypt (passlib)
- **AI** : Anthropic Claude Sonnet 4
- **Payments** : Stripe
- **Documents** : python-docx, PyPDF2

---

## 📡 API ENDPOINTS

### Authentication

```bash
# Inscription
POST /api/auth/register
Body: {
  "email": "user@company.com",
  "password": "SecurePass123!",
  "full_name": "Jean Dupont",
  "company_name": "BTP Solutions"
}

# Connexion
POST /api/auth/login
Body: username=user@company.com&password=SecurePass123!

# Profil utilisateur
GET /api/auth/me
Headers: Authorization: Bearer <token>
```

### Users

```bash
# Récupérer profil
GET /api/users/profile

# Modifier profil
PUT /api/users/profile
Body: {"full_name": "Nouveau Nom"}

# Changer mot de passe
POST /api/users/change-password
Body: {
  "current_password": "ancien",
  "new_password": "nouveau"
}

# Vérifier quota
GET /api/users/quota
```

### Analysis (DCE)

```bash
# Uploader et analyser un DCE
POST /api/analysis/upload
Content-Type: multipart/form-data
Body: file=@/path/to/dce.pdf

# Historique des analyses
GET /api/analysis/history?limit=20&offset=0

# Détails d'une analyse
GET /api/analysis/{analysis_id}

# Supprimer une analyse
DELETE /api/analysis/{analysis_id}
```

### Subscriptions (Stripe)

```bash
# Créer session checkout
POST /api/subscriptions/create-checkout-session
Body: {
  "price_id": "price_STARTER_ID",
  "success_url": "https://app.bid-killer.fr/success",
  "cancel_url": "https://app.bid-killer.fr/cancel"
}

# Abonnement actuel
GET /api/subscriptions/current

# Annuler abonnement
POST /api/subscriptions/cancel

# Portail client Stripe
POST /api/subscriptions/portal
Body: {"return_url": "https://app.bid-killer.fr/account"}
```

### Export

```bash
# Télécharger mémoire technique DOCX
GET /api/export/{analysis_id}/docx

# Exporter en JSON
GET /api/export/{analysis_id}/json
```

---

## 💳 STRIPE SETUP

### Étape 1 : Créer un compte Stripe

1. Allez sur https://dashboard.stripe.com/register
2. Créez un compte
3. Activez le mode TEST

### Étape 2 : Créer les produits

Dans **Stripe Dashboard > Produits** :

#### Produit 1 : Starter
- **Nom** : Bid-Killer Starter
- **Prix** : 49€/mois
- **Copier le Price ID** (commence par `price_...`)
- Coller dans `.env` → `STRIPE_STARTER_PRICE_ID`

#### Produit 2 : Professional
- **Nom** : Bid-Killer Professional
- **Prix** : 149€/mois
- **Copier le Price ID**
- Coller dans `.env` → `STRIPE_PRO_PRICE_ID`

#### Produit 3 : Enterprise
- **Nom** : Bid-Killer Enterprise
- **Prix** : 499€/mois
- **Copier le Price ID**
- Coller dans `.env` → `STRIPE_ENTERPRISE_PRICE_ID`

### Étape 3 : Configurer les Webhooks

1. **Stripe Dashboard > Développeurs > Webhooks**
2. **Ajouter un endpoint** : `https://votre-domaine.com/api/subscriptions/webhook`
3. **Événements à écouter** :
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
4. **Copier le Webhook Secret** (commence par `whsec_...`)
5. Coller dans `.env` → `STRIPE_WEBHOOK_SECRET`

### Étape 4 : Récupérer les clés API

1. **Stripe Dashboard > Développeurs > Clés API**
2. **Mode Test** (pour développement)
3. Copier **Secret key** (commence par `sk_test_...`)
4. Coller dans `.env` → `STRIPE_SECRET_KEY`

---

## 🌐 DÉPLOIEMENT

### Option 1 : Railway.app (Recommandé)

```bash
# 1. Installer Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Créer un projet
railway init

# 4. Ajouter PostgreSQL
railway add postgresql

# 5. Déployer
railway up

# 6. Configurer les variables d'environnement
# Via Railway Dashboard ou :
railway variables set ANTHROPIC_API_KEY=sk-ant-...
railway variables set STRIPE_SECRET_KEY=sk_test_...
# etc.
```

### Option 2 : Render.com

1. Créer un compte sur https://render.com
2. **New > Web Service**
3. Connecter votre repo GitHub
4. **Build Command** : `pip install -r requirements.txt`
5. **Start Command** : `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Ajouter une **PostgreSQL Database**
7. Configurer les **Environment Variables** depuis `.env`

### Option 3 : VPS (DigitalOcean, OVH, etc.)

```bash
# 1. Installer Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 2. Créer Dockerfile
# (à créer - voir documentation Docker)

# 3. Build & Run
docker build -t bid-killer-backend .
docker run -p 8000:8000 bid-killer-backend
```

---

## 🧪 TESTS

### Tester l'API en local

```bash
# 1. Créer un utilisateur
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!",
    "full_name": "Test User"
  }'

# 2. Se connecter
curl -X POST http://localhost:8000/api/auth/login \
  -d "username=test@example.com&password=TestPass123!"

# 3. Copier le token reçu

# 4. Tester un endpoint protégé
curl http://localhost:8000/api/users/profile \
  -H "Authorization: Bearer VOTRE_TOKEN"
```

---

## 🔐 SÉCURITÉ

### Best Practices Implémentées

✅ **Mots de passe** : Hash bcrypt (12 rounds)
✅ **JWT** : Tokens avec expiration (30 min)
✅ **CORS** : Origines autorisées configurables
✅ **SQL Injection** : Protection SQLAlchemy ORM
✅ **Rate Limiting** : À implémenter (TODO)
✅ **HTTPS** : Obligatoire en production

### À FAIRE avant Production

- [ ] Activer HTTPS (Let's Encrypt)
- [ ] Implémenter rate limiting (slowapi)
- [ ] Configurer les logs (Sentry)
- [ ] Backup automatique de la DB
- [ ] Monitoring (Prometheus + Grafana)

---

## 📊 MONITORING

### Logs

```bash
# Voir les logs en temps réel
tail -f logs/bid-killer.log

# Logs d'erreur uniquement
grep ERROR logs/bid-killer.log
```

### Métriques Clés

- **Temps de réponse moyen** : < 2s
- **Taux d'erreur** : < 0.1%
- **Uptime** : > 99.9%
- **Analyses/jour** : Tracking dans `audit_logs`

---

## 🆘 TROUBLESHOOTING

### Erreur : "Database connection failed"

```bash
# Vérifier que PostgreSQL est démarré
sudo systemctl status postgresql

# Tester la connexion manuellement
psql -U bidkiller -d bidkiller_db -h localhost
```

### Erreur : "Anthropic API key invalid"

```bash
# Vérifier que la clé est bien dans .env
cat .env | grep ANTHROPIC_API_KEY

# Tester la clé directement
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"claude-sonnet-4-20250514","max_tokens":10,"messages":[{"role":"user","content":"test"}]}'
```

### Erreur : "Stripe webhook signature invalid"

```bash
# Utiliser ngrok pour tester les webhooks en local
ngrok http 8000

# Copier l'URL ngrok dans Stripe Dashboard
# https://xxxx.ngrok.io/api/subscriptions/webhook
```

---

## 📞 SUPPORT

- **Email** : support@bid-killer.fr
- **Documentation** : https://docs.bid-killer.fr
- **Issues** : https://github.com/votre-repo/issues

---

## 📄 LICENCE

Propriétaire - Tous droits réservés © 2024 Bid-Killer Engine
