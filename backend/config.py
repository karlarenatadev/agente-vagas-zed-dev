"""
Configurações centralizadas do backend.
Lê variáveis de ambiente via python-dotenv.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega o .env ao lado deste arquivo (backend/.env), independente do
# diretório de onde o servidor foi iniciado. Sem isso, iniciar o backend a
# partir da raiz do projeto deixava FIRECRAWL_API_KEY vazia e o Scout caía
# no modo simulado.
load_dotenv(Path(__file__).resolve().parent / ".env")

# Raiz do projeto (dois níveis acima de backend/)
PROJECT_ROOT = Path(__file__).parent.parent

# Diretórios
DATA_DIR = Path(os.getenv("DATA_DIR", str(PROJECT_ROOT / "data")))
PERSONAS_DIR = Path(os.getenv("PERSONAS_DIR", str(PROJECT_ROOT / "personas")))
SKILLS_DIR = Path(os.getenv("SKILLS_DIR", str(PROJECT_ROOT / "skills")))

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")

# Modelo LLM
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
# URL base do provedor LLM compativel com a API da OpenAI (ex.: OpenRouter).
# Vazio => usa o padrao do SDK (https://api.openai.com/v1). Permite apontar para
# OpenRouter e outros provedores compativeis sem trocar de SDK.
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")

# Arquivos de dados
QUIZ_FILE = DATA_DIR / "personality-quiz.md"
PROFILE_FILE = DATA_DIR / "user-profile.md"
JOB_RESULTS_FILE = DATA_DIR / "job-search-results.md"
COURSE_RECS_FILE = DATA_DIR / "course-recommendations.md"
INTERVIEW_FILE = DATA_DIR / "interview-session.md"
RESUME_ANALYSIS_FILE = DATA_DIR / "resume-analysis.md"
JOB_DESCRIPTION_ANALYSIS_FILE = DATA_DIR / "job-description-analysis.md"
# Saídas reservadas para as próximas etapas de vaga x currículo e PDI.
RESUME_MATCH_REPORT_FILE = DATA_DIR / "resume-match-report.md"
RESUME_TAILORING_SUGGESTIONS_FILE = DATA_DIR / "resume-tailoring-suggestions.md"
PDI_PLAN_FILE = DATA_DIR / "pdi-plan.md"
RECONCILIATION_FILE = DATA_DIR / "reconciliation.md"

# Upload de currículo
MAX_RESUME_UPLOAD_SIZE = 5 * 1024 * 1024

# Logging estruturado
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_TO_FILE = os.getenv("LOG_TO_FILE", "false").lower() in {"1", "true", "yes", "on"}
LOG_DIR = Path(os.getenv("LOG_DIR", str(PROJECT_ROOT / "logs")))
LOG_FILE = Path(os.getenv("LOG_FILE", str(LOG_DIR / "backend.log")))
LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", str(5 * 1024 * 1024)))
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "3"))

# Personas
MAESTRO_PERSONA = PERSONAS_DIR / "maestro.md"
SCOUT_PERSONA = PERSONAS_DIR / "scout.md"
CURATOR_PERSONA = PERSONAS_DIR / "curator.md"
COACH_PERSONA = PERSONAS_DIR / "coach.md"

# Skills
DISPATCH_SKILL = SKILLS_DIR / "dispatch.md"
FIRECRAWL_SKILL = SKILLS_DIR / "firecrawl.md"
JOB_SEARCH_SKILL = SKILLS_DIR / "job-search.md"
COURSE_ANALYSIS_SKILL = SKILLS_DIR / "course-analysis.md"
INTERVIEW_SIM_SKILL = SKILLS_DIR / "interview-sim.md"
