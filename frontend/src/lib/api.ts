import { config } from '@/config'

export async function sendMessage(message: string): Promise<Response> {
  try {
    const response = await fetch(`${config.apiUrl}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}

export async function handleChatStream(
  response: Response,
  onChunk: (content: string, state: any) => void,
  onComplete: () => void
): Promise<void> {
  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  console.log('🔄 Starting stream handling...');

  try {
    while (reader) {
      const { value, done } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value);
      buffer += chunk;

      // Split buffer by double newlines and process complete messages
      const messages = buffer.split('\n\n');
      buffer = messages.pop() || ''; // Keep the last incomplete chunk in buffer

      for (const message of messages) {
        if (!message.trim()) continue;

        try {
          // Remove 'data: ' prefix if it exists
          const jsonStr = message.replace(/^data: /, '');
          console.log('📦 Raw chunk:', jsonStr);
          
          const data = JSON.parse(jsonStr);
          console.log('🔍 Parsed data:', data);

          if (data.error) {
            console.error('❌ Stream error:', data.error);
            continue;
          }

          // Pass both content and state to the callback
          if (data.content !== undefined) {
            console.log('📝 Content update:', { content: data.content, state: data.state });
            onChunk(data.content, data.state);
          } else if (data.state) {
            console.log('🔄 State-only update:', data.state);
            onChunk('', data.state);
          }
        } catch (e) {
          console.error('❌ Error parsing stream chunk:', e);
        }
      }
    }
  } finally {
    console.log('✅ Stream handling complete');
    reader?.releaseLock();
    onComplete();
  }
}

