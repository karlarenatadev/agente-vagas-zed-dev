import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// StrictMode removido intencionalmente: o double-mount em dev
// causa "WebSocket closed before connection established" no hook de WS.
createRoot(document.getElementById('root')!).render(<App />)
