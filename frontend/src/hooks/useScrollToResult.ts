import { useCallback, useEffect, useRef } from 'react'

const HIGHLIGHT_DURATION_MS = 3200

export function useScrollToResult<T extends HTMLElement>() {
  const nodeRef = useRef<T | null>(null)
  const pendingRevealRef = useRef(false)
  const timeoutRef = useRef<number | null>(null)
  const revealTimerRef = useRef<number | null>(null)
  const alignmentTimerRef = useRef<number | null>(null)

  const revealTarget = useCallback((target: T) => {
    if (revealTimerRef.current) window.clearTimeout(revealTimerRef.current)
    revealTimerRef.current = window.setTimeout(() => {
      const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
      const scrollContainer = target.closest<HTMLElement>('.resume-modal-panel')

      target.focus({ preventScroll: true })
      target.scrollIntoView({
        behavior: reducedMotion ? 'auto' : 'smooth',
        block: 'start',
      })

      const alignWithinScrollContainer = () => {
        if (!scrollContainer) return

        const currentOffset =
          target.getBoundingClientRect().top
          - scrollContainer.getBoundingClientRect().top
        const alignedTop = Math.max(
          0,
          scrollContainer.scrollTop + currentOffset - 16
        )

        scrollContainer.scrollTo({ top: alignedTop, behavior: 'auto' })
        scrollContainer.scrollTop = alignedTop
      }

      if (scrollContainer) {
        alignWithinScrollContainer()

        if (alignmentTimerRef.current) {
          window.clearTimeout(alignmentTimerRef.current)
        }
        alignmentTimerRef.current = window.setTimeout(() => {
          alignWithinScrollContainer()
          alignmentTimerRef.current = null
        }, 120)
      }

      target.classList.add('result-highlight--active')

      if (timeoutRef.current) window.clearTimeout(timeoutRef.current)
      timeoutRef.current = window.setTimeout(() => {
        target.classList.remove('result-highlight--active')
        timeoutRef.current = null
      }, reducedMotion ? 900 : HIGHLIGHT_DURATION_MS)
      revealTimerRef.current = null
    }, 0)
  }, [])

  const targetRef = useCallback((node: T | null) => {
    nodeRef.current = node
    if (node && pendingRevealRef.current) {
      pendingRevealRef.current = false
      revealTarget(node)
    }
  }, [revealTarget])

  const reveal = useCallback(() => {
    const target = nodeRef.current
    if (target) {
      revealTarget(target)
    } else {
      pendingRevealRef.current = true
    }
  }, [revealTarget])

  useEffect(() => () => {
    if (revealTimerRef.current) window.clearTimeout(revealTimerRef.current)
    if (timeoutRef.current) window.clearTimeout(timeoutRef.current)
    if (alignmentTimerRef.current) window.clearTimeout(alignmentTimerRef.current)
  }, [])

  return {
    reveal,
    targetRef,
  }
}
