import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { ApplicationPipeline } from '../ApplicationPipeline'
import { ApplicationTracker } from '../ApplicationTracker'
import { ChatMessage } from '../ChatMessage'
import { ChatTerminal } from '../ChatTerminal'
import { JobDescriptionAnalyzer } from '../JobDescriptionAnalyzer'
import { PdiPlan } from '../PdiPlan'
import { ProfilePanel } from '../ProfilePanel'
import { ResumeMatchReport } from '../ResumeMatchReport'
import { ResumeTailoringSuggestions } from '../ResumeTailoringSuggestions'
import { ResumeUpload } from '../ResumeUpload'
import { apiRequest } from '../../lib/api'
import { useWebSocket } from '../../hooks/useWebSocket'
import {
  applicationFixture,
  jobAnalysisFixture,
  matchReportFixture,
  pdiFixture,
  reconciliationFixture,
  resumeAnalysisFixture,
  tailoringFixture,
} from '../../test/fixtures'

type MockResponse = {
  ok: boolean
  status: number
  json: () => Promise<unknown>
  text: () => Promise<string>
}

function response(body: unknown, options: { ok?: boolean; status?: number; text?: string } = {}): MockResponse {
  return {
    ok: options.ok ?? true,
    status: options.status ?? 200,
    json: async () => body,
    text: async () => options.text ?? (body === undefined ? '' : JSON.stringify(body)),
  }
}

function mockFetch(...responses: MockResponse[]) {
  const fetchMock = vi.fn()
  for (const item of responses) {
    fetchMock.mockResolvedValueOnce(item)
  }
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

function plain(value: string | null | undefined): string {
  return (value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
}

function textIncludes(expected: string) {
  return (_content: string, element: Element | null) =>
    plain(element?.textContent).includes(expected)
}

function expectTextNow(expected: string) {
  expect(screen.getAllByText(textIncludes(expected)).length).toBeGreaterThan(0)
}

async function expectTextEventually(expected: string) {
  expect((await screen.findAllByText(textIncludes(expected))).length).toBeGreaterThan(0)
}

function deferred<T>() {
  let resolve!: (value: T) => void
  const promise = new Promise<T>(done => {
    resolve = done
  })
  return { promise, resolve }
}

class MockWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3

  readyState = MockWebSocket.CONNECTING
  sent: string[] = []
  onopen: ((event: Event) => void) | null = null
  onclose: ((event: Event) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null

  url: string

  constructor(url: string) {
    this.url = url
  }

  send(data: string) {
    this.sent.push(data)
  }

  close() {
    this.readyState = MockWebSocket.CLOSED
    this.onclose?.(new Event('close'))
  }

  open() {
    this.readyState = MockWebSocket.OPEN
    this.onopen?.(new Event('open'))
  }
}

function installMockWebSocket() {
  const sockets: MockWebSocket[] = []
  const WebSocketMock = class extends MockWebSocket {
    constructor(url: string) {
      super(url)
      sockets.push(this)
    }
  }

  vi.stubGlobal('WebSocket', WebSocketMock)
  return sockets
}

function WebSocketHarness() {
  const { messages, sendMessage } = useWebSocket()

  return (
    <div>
      <button type="button" onClick={() => sendMessage('Oi Maestro')}>Enviar WS</button>
      <div>
        {messages.map(message => (
          <p key={message.id}>{message.role}: {message.content}</p>
        ))}
      </div>
    </div>
  )
}

describe('fluxo principal do frontend', () => {
  it('envia mensagem pelo WebSocket quando a conexao esta aberta', async () => {
    const sockets = installMockWebSocket()

    render(<WebSocketHarness />)

    await waitFor(() => expect(sockets.length).toBe(1))
    sockets[0].open()

    fireEvent.click(screen.getByRole('button', { name: /Enviar WS/i }))

    expect(sockets[0].sent).toEqual([
      JSON.stringify({ type: 'message', content: 'Oi Maestro' }),
    ])
    expectTextNow('user: oi maestro')
  })

  it('mostra feedback quando o envio WebSocket falha por conexao interrompida', async () => {
    const sockets = installMockWebSocket()

    render(<WebSocketHarness />)

    await waitFor(() => expect(sockets.length).toBe(1))
    sockets[0].open()
    sockets[0].readyState = MockWebSocket.CLOSED

    fireEvent.click(screen.getByRole('button', { name: /Enviar WS/i }))

    expect(sockets[0].sent).toEqual([])
    await expectTextEventually('nao foi possivel enviar agora')
    expectTextNow('aguarde reconectar')
  })

  it('normaliza erros de API com detail em lista, texto inesperado e corpo vazio', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(response(
      { detail: [{ type: 'missing', loc: ['body', 'description'], msg: 'Field required' }] },
      { ok: false, status: 422 },
    )))
    await expect(apiRequest('/api/job-description/analyze')).rejects.toThrow('Alguns dados enviados')

    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(response(
      undefined,
      { ok: false, status: 500, text: '<html>erro interno</html>' },
    )))
    await expect(apiRequest('/api/resume-match/analyze')).rejects.toThrow('O backend encontrou uma falha')

    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(response(
      undefined,
      { ok: true, status: 200, text: '' },
    )))
    await expect(apiRequest('/api/resume/upload')).rejects.toThrow('resposta vazia')
  })

  it('encerra chamadas de API lentas com mensagem amigavel de timeout', async () => {
    vi.useFakeTimers()
    try {
      vi.stubGlobal('fetch', vi.fn((_url: RequestInfo | URL, init?: RequestInit) =>
        new Promise((_resolve, reject) => {
          init?.signal?.addEventListener('abort', () => {
            reject(new DOMException('Aborted', 'AbortError'))
          })
        })
      ))

      const request = apiRequest('/api/resume/upload', { timeoutMs: 10 })
      const assertion = expect(request).rejects.toThrow('demorou mais que o esperado')

      await vi.advanceTimersByTimeAsync(11)
      await assertion
    } finally {
      vi.useRealTimers()
    }
  })

  it('renderiza a pipeline com etapas principais e bloqueia acoes sem prerequisito', async () => {
    mockFetch(
      response({ exists: false, content: '' }),
      response({ exists: false, content: '' }),
      response({ exists: false, content: '' }),
      response({ exists: false, content: '' }),
      response({ exists: false, content: '' }),
      response({ exists: false, content: '' }),
    )

    render(
      <ApplicationPipeline
        mode="menu"
        onOpenResume={vi.fn()}
        onOpenJob={vi.fn()}
        onOpenPdi={vi.fn()}
        onStartInterview={vi.fn()}
      />,
    )

    for (const label of ['curriculo', 'vaga', 'match', 'reconciliacao', 'sugest', 'pdi', 'entrevista']) {
      expectTextNow(label)
    }

    await waitFor(() => {
      expect((screen.getByRole('button', { name: /Abrir vaga/i }) as HTMLButtonElement).disabled).toBe(true)
      expect((screen.getByRole('button', { name: /Abrir relat/i }) as HTMLButtonElement).disabled).toBe(true)
      expect((screen.getByRole('button', { name: /Gerar PDI/i }) as HTMLButtonElement).disabled).toBe(true)
      expect((screen.getByRole('button', { name: /Treinar entrevista/i }) as HTMLButtonElement).disabled).toBe(true)
    })
    expectTextNow('proximo passo recomendado')
    expectTextNow('gere o pdi antes de iniciar o treino')
  })

  it('explica o progresso quando a pipeline esta recolhida', async () => {
    window.localStorage.setItem('import-vagas:pipeline-collapsed', 'true')
    mockFetch(
      response({ exists: true, content: 'Curriculo analisado com Python.' }),
      response({ exists: true, content: 'Vaga analisada com requisitos.' }),
      response({ exists: true, content: 'Match calculado.' }),
      response({ exists: false, content: '' }),
      response({ exists: false, content: '' }),
      response({ exists: false, content: '' }),
    )

    render(
      <ApplicationPipeline
        mode="menu"
        onOpenResume={vi.fn()}
        onOpenJob={vi.fn()}
        onOpenPdi={vi.fn()}
        onStartInterview={vi.fn()}
      />,
    )

    await waitFor(() => {
      expect(screen.getByRole('list', { name: /3 de 7 etapas/i })).toBeTruthy()
    })
    expect(screen.getAllByLabelText(/Reconcilia/i).some(element =>
      element.getAttribute('aria-label')?.includes('disponivel agora')
    )).toBe(true)
  })

  it.each([
    ['erro 500 com corpo texto', response(undefined, { ok: false, status: 500, text: '<html>erro interno</html>' })],
    ['resposta vazia', response(undefined, { ok: true, status: 200, text: '' })],
    [
      'validacao FastAPI em lista',
      response(
        { detail: [{ type: 'missing', loc: ['query', 'path'], msg: 'Field required' }] },
        { ok: false, status: 422 },
      ),
    ],
  ])('mostra mensagem amigavel quando a pipeline nao consegue sincronizar: %s', async (_caseName, failedResponse) => {
    mockFetch(failedResponse)

    render(
      <ApplicationPipeline
        mode="menu"
        onOpenResume={vi.fn()}
        onOpenJob={vi.fn()}
        onOpenPdi={vi.fn()}
        onStartInterview={vi.fn()}
      />,
    )

    await expectTextEventually('nao conseguiu sincronizar')
    expectTextNow('as acoes continuam disponiveis')
  })

  it('cobre upload de curriculo com loading, sucesso e erro local de arquivo', async () => {
    const upload = deferred<MockResponse>()
    vi.stubGlobal('fetch', vi.fn().mockReturnValue(upload.promise))

    render(<ResumeUpload onContinueQuiz={vi.fn()} />)

    const input = screen.getByLabelText(/Selecionar curr/i) as HTMLInputElement
    const file = new File(
      ['Pessoa Teste com Python, SQL, Power BI e comunicacao em projetos de dados.'],
      'curriculo.txt',
      { type: 'text/plain' },
    )
    fireEvent.change(input, { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: /Enviar curr/i }))

    expect(screen.getByText(/Enviando e analisando/i)).toBeTruthy()

    upload.resolve(response({
      success: true,
      message: 'Curriculo analisado com sucesso.',
      analysis: resumeAnalysisFixture,
    }))

    await expectTextEventually('analise do curriculo concluida')
    expect(screen.getByRole('button', { name: /Continuar para o quiz/i })).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: /Escolher outro arquivo/i }))
    const invalidFile = new File(['conteudo'], 'curriculo.exe', { type: 'text/plain' })
    fireEvent.change(input, { target: { files: [invalidFile] } })
    expect(screen.getByRole('alert').textContent).toContain('PDF, DOCX ou TXT')
  })

  it('cobre analise de vaga com erro curto, loading, sucesso e falha de match', async () => {
    const jobRequest = deferred<MockResponse>()
    vi.stubGlobal(
      'fetch',
      vi.fn()
        .mockReturnValueOnce(jobRequest.promise)
        .mockResolvedValueOnce(response(
          { detail: 'Envie e analise um curriculo primeiro.' },
          { ok: false, status: 400 },
        )),
    )

    render(<JobDescriptionAnalyzer />)

    fireEvent.change(screen.getByLabelText(/Descri/i), { target: { value: 'vaga curta' } })
    fireEvent.click(screen.getByRole('button', { name: /Analisar descr/i }))
    expect(screen.getByText(/Texto muito curto/i)).toBeTruthy()

    fireEvent.change(screen.getByLabelText(/Descri/i), {
      target: {
        value: 'Analista de dados com Python, SQL, Power BI, dashboards e comunicacao com stakeholders.',
      },
    })
    fireEvent.click(screen.getByRole('button', { name: /Analisar descr/i }))
    expectTextNow('lendo o mapa da vaga')

    jobRequest.resolve(response(jobAnalysisFixture))
    await expectTextEventually('analise da vaga concluida')

    fireEvent.click(screen.getByRole('button', { name: /Comparar com meu curr/i }))
    await expectTextEventually('envie e analise um curriculo primeiro')
  })

  it('cobre match com vazio, loading, erro, sucesso e reconciliacao', async () => {
    const onCompare = vi.fn()

    const { rerender } = render(
      <ResumeMatchReport
        report={null}
        loading={false}
        error=""
        onCompare={onCompare}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: /Comparar com meu curr/i }))
    expect(onCompare).toHaveBeenCalledTimes(1)
    expectTextNow('match aguardando curriculo e vaga')

    rerender(<ResumeMatchReport report={null} loading error="" onCompare={onCompare} />)
    expect(screen.getByText(/Cruzando as rotas/i)).toBeTruthy()

    rerender(
      <ResumeMatchReport
        report={null}
        loading={false}
        error="Analise uma descricao de vaga primeiro."
        onCompare={onCompare}
      />,
    )
    expectTextNow('analise uma descricao de vaga primeiro')
    expectTextNow('curriculo e vaga analisados')

    mockFetch(
      response({ detail: 'Nenhuma reconciliacao foi gerada ainda.' }, { ok: false, status: 404 }),
      response(reconciliationFixture),
    )

    rerender(
      <ResumeMatchReport
        report={matchReportFixture}
        loading={false}
        error=""
        onCompare={onCompare}
      />,
    )
    expect(await screen.findByLabelText(/Score geral 72 de 100/i)).toBeTruthy()
    expectTextNow('relatorio de aderencia gerado')
    expectTextNow('escolher o foco da candidatura')
    fireEvent.click(screen.getByRole('button', { name: /Reconciliar candidatura/i }))
    await expectTextEventually('reconciliacao concluida')
    expectTextNow('sugestoes aguardando relatorio de match')
  })

  it('cobre sugestoes seguras com loading, erro e sucesso', async () => {
    const tailoringRequest = deferred<MockResponse>()
    vi.stubGlobal('fetch', vi.fn().mockReturnValueOnce(tailoringRequest.promise))

    render(<ResumeTailoringSuggestions />)
    expectTextNow('sugestoes aguardando relatorio de match')

    fireEvent.click(screen.getByRole('button', { name: /Sugerir ajustes/i }))
    expectTextNow('organizando evidencias')
    tailoringRequest.resolve(response(tailoringFixture))

    await expectTextEventually('sugestoes seguras prontas')
    expect(screen.getByText(/PDI personalizado/i)).toBeTruthy()

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(response(
        { detail: 'Compare a vaga com o curriculo primeiro.' },
        { ok: false, status: 400 },
      )),
    )
    fireEvent.click(screen.getByRole('button', { name: /Gerar novamente/i }))
    await expectTextEventually('compare a vaga com o curriculo primeiro')
  })

  it('mostra erro amigavel para sugestoes com validacao FastAPI em lista', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response(
      { detail: [{ type: 'missing', loc: ['body', 'use_latest_match_report'], msg: 'Field required' }] },
      { ok: false, status: 422 },
    )))

    render(<ResumeTailoringSuggestions />)
    fireEvent.click(screen.getByRole('button', { name: /Sugerir ajustes/i }))

    await expectTextEventually('alguns dados enviados')
  })

  it('cobre PDI com carregamento inicial, erro de prerequisito e sucesso', async () => {
    mockFetch(
      response({ detail: 'Nenhum PDI foi gerado ainda.' }, { ok: false, status: 404 }),
      response({ detail: 'Gere sugestoes seguras de curriculo primeiro.' }, { ok: false, status: 400 }),
    )

    render(<PdiPlan />)

    expect(await screen.findByRole('button', { name: /Gerar PDI para essa vaga/i })).toBeTruthy()
    expectTextNow('pdi aguardando pre-requisitos')
    fireEvent.click(screen.getByRole('button', { name: /Gerar PDI para essa vaga/i }))
    await expectTextEventually('gere sugestoes seguras')

    cleanup()
    const generateRequest = deferred<MockResponse>()
    vi.stubGlobal(
      'fetch',
      vi.fn()
        .mockResolvedValueOnce(response({ detail: 'Nenhum PDI foi gerado ainda.' }, { ok: false, status: 404 }))
        .mockReturnValueOnce(generateRequest.promise),
    )
    render(<PdiPlan />)
    fireEvent.click(await screen.findByRole('button', { name: /Gerar PDI para essa vaga/i }))
    expect((screen.getByRole('button', { name: /Gerando PDI/i }) as HTMLButtonElement).disabled).toBe(true)
    generateRequest.resolve(response(pdiFixture))

    await expectTextEventually('plano de desenvolvimento gerado')
    expect(screen.getByText(/PDI salvo/i)).toBeTruthy()
  })

  it('mostra erro amigavel para PDI quando backend retorna texto nao JSON', async () => {
    mockFetch(
      response({ detail: 'Nenhum PDI foi gerado ainda.' }, { ok: false, status: 404 }),
      response(undefined, { ok: false, status: 500, text: '<html>erro interno</html>' }),
    )

    render(<PdiPlan />)
    fireEvent.click(await screen.findByRole('button', { name: /Gerar PDI para essa vaga/i }))

    await expectTextEventually('backend encontrou uma falha')
  })

  it('diferencia PDI salvo carregado de PDI gerado agora', async () => {
    mockFetch(response(pdiFixture))

    render(<PdiPlan />)

    await expectTextEventually('pdi salvo carregado')
    expectTextNow('gerar novamente')
  })

  it('cobre candidaturas com loading, vazio e lista simples', async () => {
    mockFetch(response([]))

    const { unmount } = render(<ApplicationTracker isOpen onClose={vi.fn()} />)

    expect(screen.getByText(/Carregando candidaturas/i)).toBeTruthy()
    expect(await screen.findByText(/Nenhuma candidatura salva ainda/i)).toBeTruthy()

    unmount()
    mockFetch(response([applicationFixture]))
    render(<ApplicationTracker isOpen onClose={vi.fn()} />)
    expect(await screen.findByText(/Analista de Dados Junior/i)).toBeTruthy()
    expect(screen.getByText(/Acme/)).toBeTruthy()
  })

  it.each([
    ['erro 500 com corpo texto', response(undefined, { ok: false, status: 500, text: '<html>erro interno</html>' }), 'backend encontrou uma falha'],
    ['resposta vazia', response(undefined, { ok: true, status: 200, text: '' }), 'resposta vazia'],
    [
      'validacao FastAPI em lista',
      response(
        { detail: [{ type: 'missing', loc: ['body', 'status'], msg: 'Field required' }] },
        { ok: false, status: 422 },
      ),
      'alguns dados enviados',
    ],
  ])('mostra erro amigavel no painel de candidaturas: %s', async (_caseName, failedResponse, expected) => {
    mockFetch(failedResponse)

    render(<ApplicationTracker isOpen onClose={vi.fn()} />)

    await expectTextEventually(expected)
    expectTextNow('tentar sincronizar novamente')
  })

  it.each([
    ['erro 500 com corpo texto', response(undefined, { ok: false, status: 500, text: '<html>erro interno</html>' }), 'backend encontrou uma falha'],
    ['resposta vazia', response(undefined, { ok: true, status: 200, text: '' }), 'resposta vazia'],
  ])('mostra erro amigavel no painel de perfil: %s', async (_caseName, failedResponse, expected) => {
    mockFetch(failedResponse)

    render(<ProfilePanel activeAgent="Maestro" onNavigate={vi.fn()} />)

    await expectTextEventually(expected)
    expectTextNow('tente novamente')
  })

  it('diferencia vagas reais de oportunidades simuladas no Scout', () => {
    const baseMessage = {
      id: 'scout-1',
      role: 'agent' as const,
      agent: 'Scout' as const,
      timestamp: new Date('2026-06-18T12:00:00'),
    }

    render(
      <ChatMessage
        message={{
          ...baseMessage,
          content: `## RESPOSTA: SCOUT
### estado
sucesso

### resumo
Analisei 1 vaga encontrada.

### dados

requisitos_mais_recorrentes:
1. requisito: Python
   ocorrencias: 1

vagas_compativeis:
1. titulo: Analista de Dados
   source: real
   fallback_reason:
   fallback_message:
   empresa: Acme
   localizacao: Remoto
   salario: Nao informado
   beneficios: Nao informado
   link: https://jobs.example.com/vaga-123
   score_aderencia: 90/100
   prioridade_candidatura: Alta
   habilidades_correspondentes: Python
   soft_skills_correspondentes: Comunicacao
   habilidades_faltantes: SQL
   contagem_correspondencia: 1 de 2 habilidades correspondem
   dica_curriculo: Destaque projetos com dados.
`,
        }}
      />,
    )

    expect(screen.getByRole('link', { name: /Ver vaga/i }).getAttribute('href'))
      .toBe('https://jobs.example.com/vaga-123')

    cleanup()

    render(
      <ChatMessage
        message={{
          ...baseMessage,
          id: 'scout-2',
          content: `## RESPOSTA: SCOUT
### estado
sucesso

### resumo
Analisei 1 oportunidade simulada.

### dados

requisitos_mais_recorrentes:
1. requisito: Python
   ocorrencias: 1

vagas_compativeis:
1. titulo: Analista de Dados
   source: simulated
   fallback_reason: firecrawl_error
   fallback_message: Firecrawl falhou; oportunidade simulada para orientar a estrategia.
   empresa: Acme
   localizacao: Remoto
   salario: Nao informado
   beneficios: Nao informado
   link: https://jobs.example.com/vaga-123
   score_aderencia: 90/100
   prioridade_candidatura: Alta
   habilidades_correspondentes: Python
   soft_skills_correspondentes: Comunicacao
   habilidades_faltantes: SQL
   contagem_correspondencia: 1 de 2 habilidades correspondem
   dica_curriculo: Destaque projetos com dados.
`,
        }}
      />,
    )

    expectTextNow('simulada')
    expectTextNow('firecrawl falhou')
    expect(screen.queryByRole('link', { name: /Ver vaga/i })).toBeNull()
  })

  it('mostra feedback claro enquanto o Scout busca vagas reais', () => {
    render(
      <ChatTerminal
        disabled={false}
        scoutLoading
        messages={[]}
        isStreaming={false}
        mode="menu"
        onQuickAction={vi.fn()}
      />,
    )

    expectTextNow('buscando vagas reais')
    expectTextNow('isso pode levar alguns segundos')
  })
})
