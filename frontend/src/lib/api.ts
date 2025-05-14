import apiClient from './http/client';
import { supabase } from './supabase';

// Define ChatState interface for better type safety
interface ChatState {
  messages: Array<Record<string, unknown>>;
  documents: Array<Record<string, unknown>>;
  error?: string;
}

export async function sendMessage(message: string, sessionId?: string): Promise<Response> {
  try {
    const body: Record<string, unknown> = { message };
    if (sessionId) {
      body.session_id = sessionId;
    }

    const { data: { session }, error: sessionError } = await supabase.auth.getSession();

    if (sessionError) {
      console.error('Error getting session for chat:', sessionError);
      throw new Error('Authentication error: Could not get session.');
    }
    if (!session) {
      console.error('No active session found for chat API call.');
      throw new Error('Authentication required for chat. Please log in.');
    }
    const accessToken = session.access_token;
    if (!accessToken) {
      console.error('Access token not found in session for chat.');
      throw new Error('Authentication error: Access token missing for chat.');
    }

    const url = apiClient.defaults.baseURL ? apiClient.defaults.baseURL + '/chat' : '/chat';

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + accessToken,
      },
      body: JSON.stringify(body),
    });

    if (response.status !== 200) {
      let errorDetail = 'HTTP error! status: ' + response.status;
      try {
        const errorData = await response.json();
        if (errorData && errorData.detail) {
          errorDetail = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
          if (Array.isArray(errorData.detail)) {
            errorDetail = errorData.detail.map((err: { loc?: string[]; msg: string }) => `${err.loc?.join('->') || ''}: ${err.msg}`).join('; ');
          }
        }
      } catch (e) {
        // Ignore if response is not JSON or already consumed
      }
      throw new Error(errorDetail);
    }
    return response;
  } catch (error: unknown) {
    console.error('API Error in sendMessage:', error);
    if (error instanceof Error) {
      if (error.message.includes('API key')) {
        throw new Error('Missing or invalid API key. Please check your configuration.');
      }
      throw error;
    }
    throw new Error(String(error));
  }
}

export async function handleChatStream(
  response: Response,
  onChunk: (content: string, state: ChatState | null, newSessionId?: string) => void,
  onComplete: () => void
): Promise<void> {
  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  console.log('🔄 Starting stream handling...');

  try {
    if (!reader) {
      throw new Error('Connection error: Failed to establish stream');
    }

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      buffer += chunk;

      let newlineIndex;
      while ((newlineIndex = buffer.indexOf('\n')) >= 0) {
        const line = buffer.substring(0, newlineIndex).trim();
        buffer = buffer.substring(newlineIndex + 1);

        if (!line) continue;

        try {
          const jsonStr = line.replace(/^data: /, '');
          console.log('📦 Raw chunk line:', jsonStr);

          const data = JSON.parse(jsonStr);
          console.log('🔍 Parsed data:', data);

          if (data.error) {
            console.error('❌ Stream error event:', data.error);
            onChunk('Error: ' + data.error, { error: data.error, messages: [], documents: [] });
            throw new Error(data.error);
          }

          const content = data.content !== undefined ? data.content : '';
          const state = data.state || null;
          const newSessionId = data.new_session_id || undefined;

          console.log('📝 Update:', { content, state, newSessionId });
          onChunk(content, state as ChatState | null, newSessionId);

        } catch (e) {
          console.error('❌ Error parsing stream line:', line, e);
        }
      }
    }
  } catch (error) {
    console.error('Stream processing error:', error);
    if (error instanceof Error) {
      throw error;
    }
    throw new Error(String(error));
  } finally {
    console.log('✅ Stream handling complete');
    if (reader) {
      try {
        await reader.cancel();
        reader.releaseLock();
      } catch (e) {
        console.warn('Error cancelling or releasing reader lock:', e);
      }
    }
    onComplete();
  }
}
