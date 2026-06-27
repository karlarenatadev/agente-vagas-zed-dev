import { type ChangeEvent, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { AlertCircle, CheckCircle2, FileText, Loader2, UploadCloud } from 'lucide-react'
import { useScrollToResult } from '../hooks/useScrollToResult'
import { apiRequest } from '../lib/api'
import { getFriendlyErrorMessage } from '../lib/errorMessages'
import type { ProfileSuggestion, ResumeAnalysis, ResumeUploadResponse } from '../types'
import { GeneratedResultNotice } from './ui/GeneratedResultNotice'
import { ProfileSuggestionConfirm } from './ProfileSuggestionConfirm'

interface Props {
  onContinueQuiz: () => void
}

type UploadStatus = 'idle' | 'selected' | 'uploading' | 'success' | 'error'

const ACCEPTED_EXTENSIONS = ['.txt', '.pdf', '.docx']
const MAX_FILE_SIZE = 5 * 1024 * 1024
const RESUME_ANALYSIS_STORAGE_KEY = 'import-vagas:resume-analysis-complete'

function isValidExtension(fileName: string): boolean {
  return ACCEPTED_EXTENSIONS.some(extension => fileName.toLowerCase().endsWith(extension))
}

function SummaryList({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null

  return (
    <div className="resume-summary-block">
      <span>{title}</span>
      <div className="resume-chip-list">
        {items.map(item => (
          <strong key={`${title}-${item}`}>{item}</strong>
        ))}
      </div>
    </div>
  )
}

function ResumeAnalysisSummary({ analysis }: { analysis: ResumeAnalysis }) {
  return (
    <div className="resume-analysis-summary">
      <p>{analysis.professional_summary}</p>

      <div className="resume-summary-grid">
        <SummaryList title="Áreas prováveis" items={analysis.probable_areas} />
        <SummaryList title="Habilidades detectadas" items={analysis.technical_skills.slice(0, 8)} />
        <SummaryList title="Funções alvo sugeridas" items={analysis.suggested_target_roles} />
        <SummaryList title="Confirmar no quiz" items={analysis.fields_to_confirm} />
      </div>

      <div className="resume-level">
        <span>Nível estimado</span>
        <strong>{analysis.estimated_level || 'Precisa confirmar no quiz'}</strong>
      </div>
    </div>
  )
}

export function ResumeUpload({ onContinueQuiz }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [status, setStatus] = useState<UploadStatus>('idle')
  const [message, setMessage] = useState('')
  const [analysis, setAnalysis] = useState<ResumeAnalysis | null>(null)
  const [suggestions, setSuggestions] = useState<ProfileSuggestion[]>([])
  const {
    reveal,
    targetRef,
  } = useScrollToResult<HTMLDivElement>()
  const {
    reveal: revealError,
    targetRef: errorRef,
  } = useScrollToResult<HTMLDivElement>()

  const validateFile = (file: File): string | null => {
    if (!isValidExtension(file.name)) {
      return 'Envie um arquivo PDF, DOCX ou TXT.'
    }
    if (file.size > MAX_FILE_SIZE) {
      return 'O arquivo precisa ter no máximo 5 MB.'
    }
    if (file.size === 0) {
      return 'O arquivo está vazio. Envie um currículo com texto legível.'
    }
    return null
  }

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    setAnalysis(null)
    setSuggestions([])

    if (!file) {
      setSelectedFile(null)
      setStatus('idle')
      return
    }

    const validationError = validateFile(file)
    if (validationError) {
      setSelectedFile(null)
      setStatus('error')
      setMessage(validationError)
      revealError()
      return
    }

    setSelectedFile(file)
    setStatus('selected')
    setMessage('Arquivo pronto para análise.')
  }

  const uploadResume = async () => {
    if (!selectedFile) {
      inputRef.current?.click()
      return
    }

    const formData = new FormData()
    formData.append('file', selectedFile)

    setStatus('uploading')
    setMessage('Enviando e analisando currículo...')

    try {
      const data = await apiRequest<ResumeUploadResponse>('/api/resume/upload', {
        method: 'POST',
        body: formData,
      })

      if (!data.success || !data.analysis) {
        throw new Error(data.message || 'Não foi possível analisar o currículo.')
      }

      setAnalysis(data.analysis)
      setSuggestions(data.profile_suggestions ?? [])
      setMessage(data.message)
      setStatus('success')
      reveal()
      window.localStorage.setItem(RESUME_ANALYSIS_STORAGE_KEY, 'true')
      window.dispatchEvent(new Event('profile-updated'))
      window.dispatchEvent(new Event('pipeline-updated'))
    } catch (error) {
      console.error('Falha no upload do currículo:', error)
      setStatus('error')
      setMessage(getFriendlyErrorMessage(
        error,
        'Não foi possível analisar o currículo. Envie um PDF, DOCX ou TXT com texto legível.'
      ))
      revealError()
    }
  }

  const resetSelection = () => {
    setSelectedFile(null)
    setAnalysis(null)
    setSuggestions([])
    setStatus('idle')
    setMessage('')
    if (inputRef.current) inputRef.current.value = ''
  }

  const isUploading = status === 'uploading'

  return (
    <motion.section
      className={`resume-upload-card ${status}`}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      aria-label="Upload de currículo"
    >
      <input
        ref={inputRef}
        type="file"
        accept=".txt,.pdf,.docx"
        className="resume-file-input"
        onChange={handleFileChange}
        aria-label="Selecionar currículo"
      />

      <div className="resume-upload-header">
        <div className="resume-upload-icon" aria-hidden="true">
          {status === 'success' ? <CheckCircle2 size={22} /> : <FileText size={22} />}
        </div>

        <div>
          <span className="eyebrow">Antes do quiz</span>
          <h2>Tenho um currículo pronto</h2>
          <p>
            Envie seu currículo para o Maestro identificar habilidades, experiências e possíveis
            funções alvo antes do quiz.
          </p>
        </div>
      </div>

      {selectedFile && status !== 'success' && (
        <div className="resume-selected-file">
          <FileText size={15} aria-hidden="true" />
          <span>{selectedFile.name}</span>
          <button type="button" onClick={resetSelection} aria-label="Trocar arquivo selecionado">trocar</button>
        </div>
      )}

      {message && (
        <div
          ref={status === 'error' ? errorRef : undefined}
          className={`resume-upload-message ${status === 'error' ? 'error' : ''}`}
          role={status === 'error' ? 'alert' : 'status'}
          tabIndex={status === 'error' ? -1 : undefined}
        >
          {status === 'uploading'
            ? <Loader2 size={15} className="spin" aria-hidden="true" />
            : status === 'error'
              ? <AlertCircle size={15} aria-hidden="true" />
              : <CheckCircle2 size={15} aria-hidden="true" />}
          <span>{message}</span>
        </div>
      )}

      {analysis && (
        <div
          ref={targetRef}
          className="generated-result"
          tabIndex={-1}
        >
          <GeneratedResultNotice
            title="Análise do currículo concluída"
            nextStep="Próximo passo: confirme seu perfil e depois analise a vaga desejada."
          />
          <ResumeAnalysisSummary analysis={analysis} />
          <p className="resume-success-note">
            Encontrei possíveis áreas, habilidades e funções alvo. Agora confirme essas informações
            no quiz para melhorar as recomendações.
          </p>
          <ProfileSuggestionConfirm suggestions={suggestions} />
        </div>
      )}

      <div className="resume-upload-actions">
        <button
          type="button"
          className="secondary-action-button"
          onClick={() => inputRef.current?.click()}
          disabled={isUploading}
        >
          <UploadCloud size={16} aria-hidden="true" />
          {selectedFile ? 'Escolher outro arquivo' : 'Selecionar currículo'}
        </button>

        {status !== 'success' ? (
          <button
            type="button"
            className="primary-action-button"
            onClick={uploadResume}
            disabled={isUploading}
          >
            {isUploading ? <Loader2 size={16} className="spin" aria-hidden="true" /> : <UploadCloud size={16} aria-hidden="true" />}
            {selectedFile ? 'Enviar currículo' : 'Enviar currículo'}
          </button>
        ) : (
          <button type="button" className="primary-action-button" onClick={onContinueQuiz}>
            Continuar para o quiz
          </button>
        )}
      </div>
    </motion.section>
  )
}

export default ResumeUpload
