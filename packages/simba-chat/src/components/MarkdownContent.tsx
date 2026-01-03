import ReactMarkdown from "react-markdown";
import { cn } from "../utils/cn";

interface MarkdownContentProps {
  content: string;
  className?: string;
}

export function MarkdownContent({ content, className }: MarkdownContentProps) {
  return (
    <div className={cn("simba-markdown", className)}>
      <ReactMarkdown
        components={{
          p: ({ children }) => (
            <p className="simba-markdown-p">{children}</p>
          ),
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="simba-markdown-link"
            >
              {children}
            </a>
          ),
          ul: ({ children }) => (
            <ul className="simba-markdown-ul">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="simba-markdown-ol">{children}</ol>
          ),
          li: ({ children }) => (
            <li className="simba-markdown-li">{children}</li>
          ),
          code: ({ children, className }) => {
            const isInline = !className;
            return isInline ? (
              <code className="simba-markdown-code-inline">{children}</code>
            ) : (
              <code className="simba-markdown-code-block">{children}</code>
            );
          },
          pre: ({ children }) => (
            <pre className="simba-markdown-pre">{children}</pre>
          ),
          blockquote: ({ children }) => (
            <blockquote className="simba-markdown-blockquote">
              {children}
            </blockquote>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
