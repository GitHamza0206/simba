import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">
          Configure your Simba instance.
        </p>
      </div>

      {/* API Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>API Configuration</CardTitle>
          <CardDescription>Manage your API keys and endpoints.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">API Key</label>
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
              Use this key to authenticate API requests.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Widget Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>Widget Configuration</CardTitle>
          <CardDescription>Customize the appearance of your chat widget.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">Primary Color</label>
              <div className="flex gap-2">
                <input
                  type="color"
                  defaultValue="#2563eb"
                  className="h-10 w-20 cursor-pointer rounded-md border"
                />
                <input
                  type="text"
                  defaultValue="#2563eb"
                  className="flex-1 rounded-md border px-3 py-2 text-sm"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Widget Position</label>
              <select className="w-full rounded-md border px-3 py-2 text-sm">
                <option value="bottom-right">Bottom Right</option>
                <option value="bottom-left">Bottom Left</option>
              </select>
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Welcome Message</label>
            <textarea
              defaultValue="Hi! How can I help you today?"
              rows={3}
              className="w-full rounded-md border px-3 py-2 text-sm"
            />
          </div>

          <Button>Save Changes</Button>
        </CardContent>
      </Card>

      {/* Embed Code */}
      <Card>
        <CardHeader>
          <CardTitle>Embed Code</CardTitle>
          <CardDescription>Add Simba to your website.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <pre className="overflow-x-auto rounded-md bg-muted p-4 text-sm">
            {`<script src="https://cdn.simba.ai/widget.js"></script>
<script>
  Simba.init({
    apiKey: 'your-api-key',
    theme: 'light'
  });
</script>`}
          </pre>
          <Button variant="outline">Copy to Clipboard</Button>
        </CardContent>
      </Card>

      {/* LLM Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>LLM Configuration</CardTitle>
          <CardDescription>Configure your AI model settings.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">Provider</label>
              <select className="w-full rounded-md border px-3 py-2 text-sm">
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
                <option value="ollama">Ollama (Local)</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Model</label>
              <select className="w-full rounded-md border px-3 py-2 text-sm">
                <option value="gpt-4o-mini">GPT-4o Mini</option>
                <option value="gpt-4o">GPT-4o</option>
                <option value="gpt-4-turbo">GPT-4 Turbo</option>
              </select>
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Temperature: 0.1</label>
            <input type="range" min="0" max="1" step="0.1" defaultValue="0.1" className="w-full" />
          </div>

          <Button>Save Configuration</Button>
        </CardContent>
      </Card>
    </div>
  );
}
