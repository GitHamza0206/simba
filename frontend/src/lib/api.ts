import { config } from '@/config'
import { Message } from '@/types/chat'

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
  onChunk: (chunk: string) => void,
  onComplete: () => void
): Promise<void> {
  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  try {
    while (reader) {
      const { value, done } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value);
      console.log(chunk);
      onChunk(chunk);
    }
  } finally {
    reader?.releaseLock();
    onComplete();
  }
}

