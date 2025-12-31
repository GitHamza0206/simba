import Link from "next/link";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-background to-muted">
      <div className="container flex flex-col items-center justify-center gap-8 px-4 py-16">
        <h1 className="text-center text-5xl font-bold tracking-tight sm:text-6xl">
          Welcome to{" "}
          <span className="bg-gradient-to-r from-primary to-blue-400 bg-clip-text text-transparent">
            Simba
          </span>
        </h1>

        <p className="max-w-2xl text-center text-lg text-muted-foreground">
          AI-powered customer service assistant that answers questions fast and accurately.
          Upload your knowledge base and let Simba handle customer inquiries.
        </p>

        <div className="flex gap-4">
          <Link
            href="/documents"
            className="inline-flex h-11 items-center justify-center rounded-md bg-primary px-8 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          >
            Get Started
          </Link>
          <Link
            href="https://github.com/GitHamza0206/simba"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex h-11 items-center justify-center rounded-md border border-input bg-background px-8 text-sm font-medium shadow-sm transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          >
            View on GitHub
          </Link>
        </div>

        <div className="mt-8 grid gap-6 sm:grid-cols-3">
          <FeatureCard
            title="Fast Responses"
            description="Get answers in under 2 seconds with streaming responses"
          />
          <FeatureCard
            title="Accurate Answers"
            description="Strong evaluations ensure quality and prevent hallucinations"
          />
          <FeatureCard
            title="Easy Integration"
            description="Embed with a single line of code using our npm package"
          />
        </div>
      </div>
    </div>
  );
}

function FeatureCard({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-lg border bg-card p-6 shadow-sm">
      <h3 className="font-semibold">{title}</h3>
      <p className="mt-2 text-sm text-muted-foreground">{description}</p>
    </div>
  );
}
