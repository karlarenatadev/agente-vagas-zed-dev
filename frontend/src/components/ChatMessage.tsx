import { motion } from 'framer-motion'
import { AlertCircle, Bot, GraduationCap, Search, User, UserRoundCheck } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { AgentName, ChatMessage as ChatMessageType } from '../types'
import { ScoutReport, type ScoutData } from './ScoutReport'
import { CuratorReport, type CuratorData, type CuratorSkill } from './CuratorReport'

interface Props {
  message: ChatMessageType
}

const JOB_FIELDS = new Set([
  'titulo', 'source', 'fallback_reason', 'fallback_message',
  'empresa', 'localizacao', 'salario', 'beneficios', 'link',
  'score_aderencia', 'prioridade_candidatura', 'habilidades_correspondentes',
  'soft_skills_correspondentes', 'habilidades_faltantes',
  'contagem_correspondencia', 'dica_curriculo',
])

/**
 * Detecta a saída estruturada do Scout (vagas_compativeis) e a converte em
 * dados renderizáveis como cards. Retorna null quando não há vagas no texto.
 */
function parseScoutData(content: string): ScoutData | null {
  if (!/vagas_compativeis:/i.test(content)) return null

  const resumoMatch = content.match(/###\s*resumo\s*\n([\s\S]*?)(?:\n###|\nvagas_compativeis:|$)/i)
  const resumo = resumoMatch
    ? resumoMatch[1].replace(/\*\*/g, '').replace(/\s+/g, ' ').trim()
    : ''
  const field = (name: string) => {
    const match = content.match(new RegExp(`^\\s*${name}:\\s*(.*)$`, 'im'))
    return match ? match[1].trim() : ''
  }

  const requisitos: ScoutData['requisitos'] = []
  const reqBlock = content.match(/requisitos_mais_recorrentes:\s*\n([\s\S]*?)(?:\nvagas_compativeis:|$)/i)
  if (reqBlock) {
    const reqRegex = /requisito:\s*(.+)\n\s*ocorrencias:\s*(.+)/gi
    let m: RegExpExecArray | null
    while ((m = reqRegex.exec(reqBlock[1])) !== null) {
      const requisito = m[1].trim()
      if (requisito && !/^n[ãa]o informado$/i.test(requisito)) {
        requisitos.push({ requisito, ocorrencias: m[2].trim() })
      }
    }
  }

  const vagasRaw = content.slice(content.search(/vagas_compativeis:/i) + 'vagas_compativeis:'.length)
  const blocks = vagasRaw.split(/\n(?=\s*\d+\.\s*titulo:)/i)
  const vagas: ScoutData['vagas'] = []

  for (const block of blocks) {
    const job: Record<string, string> = {}
    const lineRegex = /^\s*(?:\d+\.\s*)?([a-z_]+):\s*(.*)$/gim
    let line: RegExpExecArray | null
    while ((line = lineRegex.exec(block)) !== null) {
      const key = line[1].toLowerCase()
      if (JOB_FIELDS.has(key)) job[key] = line[2].trim()
    }
    if (job.titulo) vagas.push(job)
  }

  if (vagas.length === 0) return null
  return {
    resumo,
    status_busca: field('status_busca'),
    fallback_simulado: field('fallback_simulado'),
    fallback_llm: field('fallback_llm'),
    fallback_reason: field('fallback_reason'),
    fallback_message: field('fallback_message'),
    busca_degradada: field('busca_degradada'),
    aviso_degradacao: field('aviso_degradacao'),
    requisitos,
    vagas,
  }
}

type CuratorSkillTextField = Exclude<keyof CuratorSkill, 'habilidade' | 'resources'>

const SKILL_FIELDS = [
  'habilidade', 'prioridade', 'nivel_recomendado', 'por_que_importa',
  'alinhamento_com_perfil', 'projeto_pratico', 'tempo_estimado_estudo',
  'relacao_com_vagas', 'impacto_esperado_aderencia',
] as const

function assignSkillField(
  skill: CuratorSkill,
  key: CuratorSkillTextField,
  value: string,
) {
  switch (key) {
    case 'prioridade':
      skill.prioridade = value
      break
    case 'nivel_recomendado':
      skill.nivel_recomendado = value
      break
    case 'por_que_importa':
      skill.por_que_importa = value
      break
    case 'alinhamento_com_perfil':
      skill.alinhamento_com_perfil = value
      break
    case 'projeto_pratico':
      skill.projeto_pratico = value
      break
    case 'tempo_estimado_estudo':
      skill.tempo_estimado_estudo = value
      break
    case 'relacao_com_vagas':
      skill.relacao_com_vagas = value
      break
    case 'impacto_esperado_aderencia':
      skill.impacto_esperado_aderencia = value
      break
  }
}

const RESOURCE_MAP = [
  { kind: 'free', label: 'Curso gratuito', name: 'curso_gratuito_recomendado', platform: 'plataforma_gratuita', link: 'link_gratuito' },
  { kind: 'paid', label: 'Curso pago', name: 'curso_pago_acessivel_recomendado', platform: 'plataforma_paga', link: 'link_pago' },
  { kind: 'reference', label: 'Documentação', name: 'documentacao_ou_referencia', platform: 'plataforma_referencia', link: 'link_referencia' },
  { kind: 'quick', label: 'Conteúdo rápido', name: 'conteudo_complementar_rapido', platform: 'plataforma_conteudo_rapido', link: 'link_conteudo_rapido' },
] as const

const BUCKET_LABELS: Record<string, string> = {
  'estudar agora': 'Estudar agora',
  'estudar depois': 'Estudar depois',
  'opcional': 'Opcional',
}

function isUsable(value?: string): boolean {
  if (!value) return false
  const trimmed = value.trim()
  return trimmed !== '' && trimmed !== '-' && !/^n[ãa]o\s/i.test(trimmed)
}

/**
 * Detecta a saída estruturada do Curator (trilha de evolução) e a converte em
 * habilidades agrupadas por bucket. Retorna null quando não há trilha no texto.
 */
function parseCuratorData(content: string): CuratorData | null {
  if (!/curso_gratuito_recomendado|projeto_pratico|nivel_recomendado/i.test(content)) return null

  const resumoMatch = content.match(/###\s*resumo\s*\n([\s\S]*?)(?:\n###|$)/i)
  const resumo = resumoMatch
    ? resumoMatch[1].replace(/\*\*/g, '').replace(/Contexto usado:[\s\S]*/i, '').replace(/\s+/g, ' ').trim()
    : ''

  // Limita à seção de dados (entre "### dados" e a próxima seção "### ...").
  let dados = content
  const dadosIdx = content.search(/###\s*dados/i)
  if (dadosIdx >= 0) {
    const rest = content.slice(dadosIdx + content.slice(dadosIdx).indexOf('\n') + 1)
    const nextSection = rest.search(/\n###\s/)
    dados = nextSection >= 0 ? rest.slice(0, nextSection) : rest
  }

  // Localiza cada cabeçalho de bucket; guarda início do cabeçalho e do conteúdo.
  const headerRegex = /^[ \t]*(estudar agora|estudar depois|opcional):[ \t]*$/gim
  const headers: { name: string; headerStart: number; contentStart: number }[] = []
  let h: RegExpExecArray | null
  while ((h = headerRegex.exec(dados)) !== null) {
    headers.push({ name: h[1].toLowerCase(), headerStart: h.index, contentStart: h.index + h[0].length })
  }

  const buckets: CuratorData['buckets'] = []

  for (let i = 0; i < headers.length; i++) {
    const start = headers[i].contentStart
    const end = i + 1 < headers.length ? headers[i + 1].headerStart : dados.length
    const slice = dados.slice(start, end)

    const skillBlocks = slice.split(/\n(?=\s*\d+\.\s*habilidade:)/i)
    const skills: CuratorData['buckets'][number]['skills'] = []

    for (const block of skillBlocks) {
      const raw: Record<string, string> = {}
      const lineRegex = /^\s*(?:\d+\.\s*)?([a-z_]+):\s*(.*)$/gim
      let line: RegExpExecArray | null
      while ((line = lineRegex.exec(block)) !== null) {
        raw[line[1].toLowerCase()] = line[2].trim()
      }
      if (!raw.habilidade) continue

      const skill: CuratorSkill = { habilidade: raw.habilidade, resources: [] }
      for (const key of SKILL_FIELDS) {
        if (key !== 'habilidade' && raw[key]) assignSkillField(skill, key, raw[key])
      }
      for (const res of RESOURCE_MAP) {
        if (isUsable(raw[res.name])) {
          skill.resources.push({
            kind: res.kind,
            label: res.label,
            name: raw[res.name],
            platform: raw[res.platform],
            link: raw[res.link],
          })
        }
      }
      skills.push(skill)
    }

    if (skills.length > 0) {
      buckets.push({ label: BUCKET_LABELS[headers[i].name] ?? headers[i].name, skills })
    }
  }

  if (buckets.length === 0) return null
  return { resumo, buckets }
}

const AGENT_META = {
  Maestro: {
    label: 'Maestro',
    helper: 'orquestrador',
    className: 'message-agent-maestro',
    icon: Bot,
  },
  Scout: {
    label: 'Scout',
    helper: 'vagas',
    className: 'message-agent-scout',
    icon: Search,
  },
  Curator: {
    label: 'Curator',
    helper: 'aprendizado',
    className: 'message-agent-curator',
    icon: GraduationCap,
  },
  Coach: {
    label: 'Coach',
    helper: 'entrevista',
    className: 'message-agent-coach',
    icon: UserRoundCheck,
  },
} satisfies Record<AgentName, {
  label: string
  helper: string
  className: string
  icon: typeof Bot
}>

const CAREER_MENU_PATTERN = /(?:O que voc[eê] gostaria de fazer\??[\s\S]*?Digite\s+A,\s*B,\s*C\s+ou\s+D:?)|(?:A\s*[—-].*(?:Buscar|Encontrar).*[\s\S]*?B\s*[—-].*(?:curso|material|lacuna).*[\s\S]*?C\s*[—-].*(?:entrevista|Praticar).*[\s\S]*?D\s*[—-].*(?:quiz|diagn[oó]stico))/i

function getRenderableContent(content: string) {
  let visibleContent = content
  let previousContent = ''

  while (visibleContent !== previousContent) {
    previousContent = visibleContent
    visibleContent = visibleContent.replace(CAREER_MENU_PATTERN, '')
  }

  const hasCareerMenu = visibleContent !== content
  const cleanedContent = visibleContent
    .replace(/\n{3,}/g, '\n\n')
    .trim()

  return {
    hasCareerMenu,
    visibleContent: cleanedContent,
  }
}

export function ChatMessage({ message }: Props) {
  const isUser = message.role === 'user'
  const isSystem = message.role === 'system'
  const agent = message.agent ?? 'Maestro'
  const meta = AGENT_META[agent]
  const AgentIcon = meta.icon
  const { hasCareerMenu, visibleContent } = getRenderableContent(message.content)
  const hasStructuredCareerData = /score_aderencia|prioridade|habilidades_faltantes|curso_gratuito|projeto_pratico|pontuacao_final|nota_parcial/i
    .test(message.content)
  const scoutData = !isUser && !isSystem ? parseScoutData(message.content) : null
  const curatorData = !isUser && !isSystem && !scoutData ? parseCuratorData(message.content) : null

  if (isSystem) {
    return (
      <motion.div
        className="message-row system"
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="system-message" role="status">
          <AlertCircle size={14} aria-hidden="true" />
          <span>{message.content}</span>
        </div>
      </motion.div>
    )
  }

  if (isUser) {
    return (
      <motion.div
        className="message-row user"
        initial={{ opacity: 0, x: 12 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.18 }}
      >
        <div className="message-bubble user-bubble">
          <div className="message-author user-author">
            <span>Você</span>
            <User size={13} aria-hidden="true" />
          </div>
          <p>{message.content}</p>
        </div>
      </motion.div>
    )
  }

  return (
    <motion.div
      className={`message-row agent ${meta.className}`}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
    >
      <div className="message-avatar" aria-hidden="true">
        <AgentIcon size={17} />
      </div>

      <article className={`message-bubble agent-bubble ${hasStructuredCareerData ? 'structured-agent-bubble' : ''}`}>
        <div className="message-author">
          <div>
            <strong>{meta.label}</strong>
            <span>{meta.helper}</span>
          </div>
          <time dateTime={message.timestamp.toISOString()}>
            {message.timestamp.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
          </time>
        </div>

        <div className="prose-chat">
          {scoutData ? (
            <ScoutReport data={scoutData} />
          ) : curatorData ? (
            <CuratorReport data={curatorData} />
          ) : (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                table: ({ children }) => <div className="table-scroll"><table>{children}</table></div>,
                a: ({ children, href }) => (
                  <a href={href} target="_blank" rel="noopener noreferrer">
                    {children}
                  </a>
                ),
              }}
            >
              {visibleContent || 'A esteira de carreira está pronta para a próxima ação.'}
            </ReactMarkdown>
          )}

          {hasCareerMenu && (
            <div className="compact-career-menu" role="note" aria-label="Menu de carreira compactado">
              <strong>Menu A/B/C/D compactado</strong>
              <span>Use a esteira visual de ações para escolher a próxima etapa.</span>
            </div>
          )}

          {message.isStreaming && (
            <span className="typing-indicator" aria-label="Resposta em andamento">
              <span />
              <span />
              <span />
            </span>
          )}
        </div>
      </article>
    </motion.div>
  )
}
