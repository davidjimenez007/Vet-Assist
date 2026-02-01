# VetAssist AI

AI Receptionist and Smart Scheduling System for Veterinary Clinics.

## Features

- **Voice Calls**: Automated phone answering with natural Spanish conversation
- **WhatsApp Integration**: Chat-based appointment scheduling
- **Smart Scheduling**: Intelligent slot management with conflict prevention
- **Emergency Detection**: Automatic triage and escalation for urgent cases
- **Dashboard**: Real-time monitoring of appointments and conversations

## Tech Stack

- **Backend**: Python + FastAPI + PostgreSQL
- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS
- **AI**: OpenAI GPT-4o
- **Telephony**: Twilio (Voice & WhatsApp)

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for local development)
- Python 3.11+ (for local development)
- Twilio Account (for voice/WhatsApp)
- OpenAI API Key

### Quick Start with Docker

1. Clone the repository:
```bash
git clone <repository-url>
cd vetassist
```

2. Copy the environment file:
```bash
cp .env.example .env
```

3. Update the `.env` file with your credentials:
- Add your Twilio credentials
- Add your OpenAI API key
- Set a secure SECRET_KEY

4. Start the services:
```bash
docker-compose up -d
```

5. Run database migrations:
```bash
docker-compose exec backend alembic upgrade head
```

6. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Local Development

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

## Project Structure

```
vetassist/
├── backend/
│   ├── app/
│   │   ├── api/          # REST API endpoints
│   │   ├── agents/       # AI conversation agents
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   └── prompts/      # AI prompts
│   ├── migrations/       # Alembic migrations
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── app/          # Next.js pages
│   │   ├── components/   # React components
│   │   └── lib/          # Utilities
│   └── public/
└── docker-compose.yml
```

## Twilio Configuration

### Voice Webhooks

Configure your Twilio phone number with these webhooks:

- **Voice URL**: `https://your-domain.com/webhooks/voice/incoming`
- **Voice Status Callback**: `https://your-domain.com/webhooks/voice/status`

### WhatsApp Webhooks

Configure your Twilio WhatsApp number:

- **Webhook URL**: `https://your-domain.com/webhooks/whatsapp/incoming`
- **Status Callback URL**: `https://your-domain.com/webhooks/whatsapp/status`

## Initial Setup

After starting the application for the first time:

1. Use the setup endpoint to create the initial clinic and admin user:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/setup" \
  -H "Content-Type: application/json" \
  -d '{
    "clinic_name": "Your Clinic Name",
    "admin_name": "Admin Name",
    "admin_email": "admin@clinic.com",
    "admin_phone": "+1234567890"
  }'
```

2. Use the returned access token to log in to the dashboard.

## API Documentation

Once the backend is running, access the interactive API documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

MIT
