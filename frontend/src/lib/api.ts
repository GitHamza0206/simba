import { config } from '@/config'
import apiClient from './http/client'
import { getAuthHeaders } from './supabase'

export async function sendMessage(message: string, sessionId?: string): Promise<Response> {
  try {
    const body: Record<string, any> = { message }
    if (sessionId) {
      body.session_id = sessionId
    }

    const response = await apiClient.post('/chat', body, {
      responseType: 'stream'
    })
    
    if (response.status !== 200) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    return response as any
  } catch (error: any) {
    console.error('API Error in sendMessage:', error)
    if (error.response && error.response.data) {
      const errorData = error.response.data as any
      let detailMessage = errorData.detail
      if (Array.isArray(detailMessage)) {
        detailMessage = detailMessage.map((err: any) => `${err.loc?.join('->') || ''}: ${err.msg}`).join('; ')
      }
      if (typeof detailMessage === 'string' && detailMessage.includes('API key')) {
        throw new Error('Missing or invalid API key. Please check your configuration.')
      }
      throw new Error(detailMessage || `HTTP error! status: ${error.response.status}`)
    }
    throw error
  }
}

export async function handleChatStream(
  response: Response,
  onChunk: (content: string, state: any, newSessionId?: string) => void,
  onComplete: () => void
): Promise<void> {
  const reader = response.body?.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  console.log('🔄 Starting stream handling...')

  try {
    if (!reader) {
      throw new Error('Connection error: Failed to establish stream')
    }

    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      
      const chunk = decoder.decode(value, { stream: true })
      buffer += chunk

      let newlineIndex
      while ((newlineIndex = buffer.indexOf('\n')) >= 0) {
        const line = buffer.substring(0, newlineIndex).trim()
        buffer = buffer.substring(newlineIndex + 1)

        if (!line) continue

        try {
          const jsonStr = line.replace(/^data: /, '')
          console.log('📦 Raw chunk line:', jsonStr)
          
          const data = JSON.parse(jsonStr)
          console.log('🔍 Parsed data:', data)

          if (data.error) {
            console.error('❌ Stream error event:', data.error)
            onChunk(`Error: ${data.error}`, { error: data.error })
            throw new Error(data.error)
          }

          const content = data.content !== undefined ? data.content : ''
          const state = data.state || null
          const newSessionId = data.new_session_id || undefined

          console.log('📝 Update:', { content, state, newSessionId })
          onChunk(content, state, newSessionId)

        } catch (e) {
          console.error('❌ Error parsing stream line:', line, e)
        }
      }
    }
  } catch (error) {
    console.error('Stream processing error:', error)
    throw error
  } finally {
    console.log('✅ Stream handling complete')
    if (reader) {
      try {
        await reader.cancel()
        reader.releaseLock()
      } catch (e) {
        console.warn('Error cancelling or releasing reader lock:', e)
      }
    }
    onComplete()
  }
}

