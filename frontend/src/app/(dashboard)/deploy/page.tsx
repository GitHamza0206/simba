"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CodeBlock } from "@/components/ui/code-block";
import { API_URL } from "@/lib/constants";
import { Copy, Check, Sparkles, MessageSquare, MessageCircle } from "lucide-react";

const INLINE_CHAT_EXAMPLE = `import { SimbaChat } from 'simba-chat';
import 'simba-chat/styles.css';

function App() {
  return (
    <SimbaChat
      apiUrl="${API_URL}"
      organizationId="your-organization-id"
      apiKey="your-api-key"
      collection="default"
      placeholder="Ask me anything..."
    />
  );
}`;

const BUBBLE_CHAT_EXAMPLE = `import { SimbaChatBubble } from 'simba-chat';
import 'simba-chat/styles.css';

function App() {
  return (
    <SimbaChatBubble
      apiUrl="${API_URL}"
      organizationId="your-organization-id"
      apiKey="your-api-key"
      position="bottom-right"
      defaultOpen={false}
    />
  );
}`;

const THEMING_EXAMPLE = `:root {
  --simba-primary: #8b5cf6;
  --simba-primary-foreground: #ffffff;
  --simba-background: #ffffff;
  --simba-foreground: #0f172a;
  --simba-muted: #f1f5f9;
  --simba-muted-foreground: #64748b;
  --simba-border: #e2e8f0;
  --simba-radius: 0.5rem;
}`;

const AGENT_PROMPT = `Add a Simba chat widget to my website.

## Package
Install: npm install simba-chat

## Configuration
- API URL: ${API_URL}
- Organization ID: (required for multi-tenant access)
- API Key: (optional, for authenticated access)
- Collection: "default" (or specify your collection name)

## Integration Options

### Option 1: Inline Chat
\`\`\`tsx
import { SimbaChat } from 'simba-chat';
import 'simba-chat/styles.css';

<SimbaChat
  apiUrl="${API_URL}"
  organizationId="your-organization-id"
  apiKey="your-api-key"
  collection="default"
  placeholder="Ask me anything..."
  onError={(error) => console.error(error)}
  onMessage={(message) => console.log('New message:', message)}
/>
\`\`\`

### Option 2: Floating Bubble
\`\`\`tsx
import { SimbaChatBubble } from 'simba-chat';
import 'simba-chat/styles.css';

<SimbaChatBubble
  apiUrl="${API_URL}"
  organizationId="your-organization-id"
  apiKey="your-api-key"
  position="bottom-right"
  defaultOpen={false}
/>
\`\`\`

### Option 3: Custom UI with Hook
\`\`\`tsx
import { useSimbaChat } from 'simba-chat';

const { messages, status, sendMessage, stop, clear } = useSimbaChat({
  apiUrl: '${API_URL}',
  organizationId: 'your-organization-id',
  apiKey: 'your-api-key',
  collection: 'default',
});
\`\`\`

## Available Props
| Prop | Type | Required | Description |
|------|------|----------|-------------|
| apiUrl | string | Yes | Simba API base URL |
| organizationId | string | Yes | Organization ID for multi-tenant requests |
| apiKey | string | No | API key for authentication |
| collection | string | No | Collection name for RAG queries |
| placeholder | string | No | Input placeholder text |
| position | 'bottom-right' \\| 'bottom-left' | No | Bubble position |
| onError | (error) => void | No | Error callback |
| onMessage | (message) => void | No | New message callback |

## Theming (CSS Variables)
\`\`\`css
:root {
  --simba-primary: #8b5cf6;
  --simba-primary-foreground: #ffffff;
  --simba-background: #ffffff;
  --simba-foreground: #0f172a;
  --simba-muted: #f1f5f9;
  --simba-border: #e2e8f0;
  --simba-radius: 0.5rem;
}
\`\`\`

Place the component in your app's root layout or wherever you want the chat to appear. Remember to import the styles CSS file.`;

export default function DeployPage() {
  const [copiedApiUrl, setCopiedApiUrl] = useState(false);
  const [copiedPrompt, setCopiedPrompt] = useState(false);

  const copyApiUrl = async () => {
    await navigator.clipboard.writeText(API_URL);
    setCopiedApiUrl(true);
    setTimeout(() => setCopiedApiUrl(false), 2000);
  };

  const copyPrompt = async () => {
    await navigator.clipboard.writeText(AGENT_PROMPT);
    setCopiedPrompt(true);
    setTimeout(() => setCopiedPrompt(false), 2000);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Deploy</h1>
        <p className="text-muted-foreground">
          Add Simba chat to your website or application.
        </p>
      </div>

      {/* API Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>API Configuration</CardTitle>
          <CardDescription>Your API credentials for the chat widget.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">API URL</label>
            <div className="flex gap-2">
              <code className="flex-1 rounded-md border bg-muted px-3 py-2 text-sm font-mono">
                {API_URL}
              </code>
              <Button variant="outline" size="sm" onClick={copyApiUrl}>
                {copiedApiUrl ? (
                  <Check className="h-4 w-4 text-green-600" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">API Key (Optional)</label>
            <div className="flex gap-2">
              <input
                type="password"
                value="sk-xxxxxxxxxxxxxxxx"
                readOnly
                className="flex-1 rounded-md border bg-muted px-3 py-2 text-sm"
              />
              <Button variant="outline">Regenerate</Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Use this key to authenticate API requests from your widget.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Installation */}
      <Card>
        <CardHeader>
          <CardTitle>Installation</CardTitle>
          <CardDescription>Install the simba-chat package in your project.</CardDescription>
        </CardHeader>
        <CardContent>
          <CodeBlock code="npm install simba-chat" language="bash" />
        </CardContent>
      </Card>

      {/* Quick Start */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Start</CardTitle>
          <CardDescription>Choose your preferred integration style.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Inline Chat */}
          <div className="space-y-3">
            <h4 className="font-medium flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              Inline Chat
            </h4>
            <p className="text-sm text-muted-foreground">
              Embed the chat directly in your page layout.
            </p>
            <CodeBlock code={INLINE_CHAT_EXAMPLE} language="tsx" />
          </div>

          {/* Floating Bubble */}
          <div className="space-y-3">
            <h4 className="font-medium flex items-center gap-2">
              <MessageCircle className="h-4 w-4" />
              Floating Bubble
            </h4>
            <p className="text-sm text-muted-foreground">
              Add a floating chat bubble to the corner of your site.
            </p>
            <CodeBlock code={BUBBLE_CHAT_EXAMPLE} language="tsx" />
          </div>
        </CardContent>
      </Card>

      {/* Theming */}
      <Card>
        <CardHeader>
          <CardTitle>Theming</CardTitle>
          <CardDescription>Customize the chat widget appearance with CSS variables.</CardDescription>
        </CardHeader>
        <CardContent>
          <CodeBlock code={THEMING_EXAMPLE} language="css" />
        </CardContent>
      </Card>

      {/* Coding Agent Prompt */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            Coding Agent Prompt
          </CardTitle>
          <CardDescription>
            Copy this prompt and paste it into Claude, Cursor, or your favorite AI coding assistant.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="relative">
            <pre className="max-h-64 overflow-auto rounded-md bg-muted p-4 text-xs font-mono whitespace-pre-wrap">
              {AGENT_PROMPT}
            </pre>
            <Button
              variant="outline"
              size="sm"
              className="absolute top-2 right-2"
              onClick={copyPrompt}
            >
              {copiedPrompt ? (
                <Check className="h-4 w-4 text-green-600" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
