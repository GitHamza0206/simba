# simba-chat

Embeddable chat widget for Simba RAG applications.

## Installation

```bash
npm install simba-chat
# or
bun add simba-chat
# or
pnpm add simba-chat
```

## Usage

### Inline Chat

```tsx
import { SimbaChat } from 'simba-chat';
import 'simba-chat/styles.css';

function App() {
  return (
    <SimbaChat
      apiUrl="https://your-simba-api.com"
      apiKey="your-api-key"
      collection="my-docs"
      placeholder="Ask me anything..."
      onError={(error) => console.error(error)}
      onMessage={(message) => console.log('New message:', message)}
    />
  );
}
```

### Floating Bubble

```tsx
import { SimbaChatBubble } from 'simba-chat';
import 'simba-chat/styles.css';

function App() {
  return (
    <SimbaChatBubble
      apiUrl="https://your-simba-api.com"
      apiKey="your-api-key"
      position="bottom-right"
      defaultOpen={false}
    />
  );
}
```

### Custom UI with Hook

```tsx
import { useSimbaChat } from 'simba-chat';

function CustomChat() {
  const { messages, status, sendMessage, stop, clear } = useSimbaChat({
    apiUrl: 'https://your-simba-api.com',
    apiKey: 'your-api-key',
    collection: 'my-docs',
  });

  return (
    <div>
      {messages.map((msg) => (
        <div key={msg.id}>
          <strong>{msg.role}:</strong> {msg.content}
        </div>
      ))}
      <button onClick={() => sendMessage('Hello!')}>Send</button>
      {status === 'streaming' && <button onClick={stop}>Stop</button>}
      <button onClick={clear}>Clear</button>
    </div>
  );
}
```

## Props

### SimbaChat

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `apiUrl` | `string` | Yes | Simba API base URL |
| `apiKey` | `string` | Yes | API key for authentication |
| `collection` | `string` | No | Collection name for RAG queries |
| `placeholder` | `string` | No | Input placeholder text |
| `className` | `string` | No | Additional CSS class |
| `style` | `CSSProperties` | No | Inline styles |
| `onError` | `(error: Error) => void` | No | Error callback |
| `onMessage` | `(message: ChatMessage) => void` | No | New message callback |

### SimbaChatBubble

Extends all `SimbaChat` props, plus:

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `position` | `'bottom-right' \| 'bottom-left'` | `'bottom-right'` | Bubble position |
| `bubbleIcon` | `ReactNode` | Chat icon | Custom bubble icon |
| `defaultOpen` | `boolean` | `false` | Start with chat open |

## Theming

Customize the appearance using CSS variables:

```css
:root {
  --simba-primary: #8b5cf6;
  --simba-primary-foreground: #ffffff;
  --simba-background: #ffffff;
  --simba-foreground: #0f172a;
  --simba-muted: #f1f5f9;
  --simba-muted-foreground: #64748b;
  --simba-border: #e2e8f0;
  --simba-radius: 0.5rem;
}
```

## License

MIT
