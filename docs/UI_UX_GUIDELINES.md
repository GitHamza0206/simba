# Simba UI/UX Design Guidelines

## Design Philosophy

Simba's interface should feel **invisible**. The best customer service experience is one where users find answers effortlessly, without thinking about the tool itself.

### Core Principles

1. **Speed over decoration** - Every millisecond matters in support
2. **Clarity over cleverness** - Users need answers, not puzzles
3. **Trust through transparency** - Show sources, indicate confidence
4. **Accessibility always** - Support all users, all devices

---

## Visual Identity

### Color System

```css
/* Primary Palette */
--simba-primary: #2563eb;       /* Blue 600 - Primary actions */
--simba-primary-hover: #1d4ed8; /* Blue 700 - Hover states */
--simba-primary-light: #dbeafe; /* Blue 100 - Backgrounds */

/* Neutral Palette */
--simba-gray-50: #f9fafb;       /* Backgrounds */
--simba-gray-100: #f3f4f6;      /* Cards, inputs */
--simba-gray-200: #e5e7eb;      /* Borders */
--simba-gray-500: #6b7280;      /* Secondary text */
--simba-gray-900: #111827;      /* Primary text */

/* Semantic Colors */
--simba-success: #10b981;       /* Green - Positive feedback */
--simba-warning: #f59e0b;       /* Amber - Caution */
--simba-error: #ef4444;         /* Red - Errors */
--simba-info: #3b82f6;          /* Blue - Information */

/* Dark Mode */
--simba-dark-bg: #0f172a;       /* Slate 900 */
--simba-dark-card: #1e293b;     /* Slate 800 */
--simba-dark-border: #334155;   /* Slate 700 */
--simba-dark-text: #f1f5f9;     /* Slate 100 */
```

### Typography

```css
/* Font Family */
--simba-font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
--simba-font-mono: 'JetBrains Mono', 'Fira Code', monospace;

/* Font Sizes */
--simba-text-xs: 0.75rem;    /* 12px - Labels, badges */
--simba-text-sm: 0.875rem;   /* 14px - Secondary text */
--simba-text-base: 1rem;     /* 16px - Body text */
--simba-text-lg: 1.125rem;   /* 18px - Subheadings */
--simba-text-xl: 1.25rem;    /* 20px - Headings */
--simba-text-2xl: 1.5rem;    /* 24px - Large headings */

/* Line Heights */
--simba-leading-tight: 1.25;
--simba-leading-normal: 1.5;
--simba-leading-relaxed: 1.75;

/* Font Weights */
--simba-font-normal: 400;
--simba-font-medium: 500;
--simba-font-semibold: 600;
--simba-font-bold: 700;
```

### Spacing Scale

```css
/* Spacing (based on 4px grid) */
--simba-space-1: 0.25rem;   /* 4px */
--simba-space-2: 0.5rem;    /* 8px */
--simba-space-3: 0.75rem;   /* 12px */
--simba-space-4: 1rem;      /* 16px */
--simba-space-5: 1.25rem;   /* 20px */
--simba-space-6: 1.5rem;    /* 24px */
--simba-space-8: 2rem;      /* 32px */
--simba-space-10: 2.5rem;   /* 40px */
--simba-space-12: 3rem;     /* 48px */
```

### Border Radius

```css
--simba-radius-sm: 0.25rem;    /* 4px - Small elements */
--simba-radius-md: 0.375rem;   /* 6px - Buttons, inputs */
--simba-radius-lg: 0.5rem;     /* 8px - Cards */
--simba-radius-xl: 0.75rem;    /* 12px - Modals */
--simba-radius-2xl: 1rem;      /* 16px - Large containers */
--simba-radius-full: 9999px;   /* Pills, avatars */
```

---

## Component Guidelines

### Chat Widget

The chat widget is the primary user touchpoint. It must be:

#### Layout

```
┌─────────────────────────────┐
│  ◄ Simba Support      ─ ✕  │  <- Header (40px)
├─────────────────────────────┤
│                             │
│  ┌─────────────────────┐   │
│  │ Assistant message   │   │  <- Messages area
│  └─────────────────────┘   │     (scrollable)
│                             │
│         ┌─────────────────┐ │
│         │ User message    │ │
│         └─────────────────┘ │
│                             │
│  ┌─────────────────────┐   │
│  │ Assistant typing... │   │
│  └─────────────────────┘   │
│                             │
├─────────────────────────────┤
│  ┌─────────────────────┐   │  <- Input area
│  │ Type a message...   │ ▶ │
│  └─────────────────────┘   │
└─────────────────────────────┘

Dimensions:
- Width: 380px (desktop), 100% (mobile)
- Height: 600px (desktop), 100vh (mobile)
- Min-height: 400px
```

#### Message Bubbles

```
Assistant messages:
- Align: Left
- Background: --simba-gray-100 (light) / --simba-dark-card (dark)
- Max-width: 85%
- Border-radius: 0 --radius-lg --radius-lg --radius-lg

User messages:
- Align: Right
- Background: --simba-primary
- Text color: White
- Max-width: 85%
- Border-radius: --radius-lg --radius-lg 0 --radius-lg
```

#### States

```
Loading:
- Show typing indicator (3 animated dots)
- Disable input while processing

Error:
- Show inline error message
- Provide retry action
- Log for debugging

Empty:
- Welcome message with suggested questions
- Quick action buttons
```

### Input Field

```
┌──────────────────────────────────────┬───┐
│ Type your message...                 │ ▶ │
└──────────────────────────────────────┴───┘

States:
- Default: Gray border, placeholder text
- Focus: Primary color border, shadow
- Disabled: Reduced opacity, no interaction
- Error: Red border, error message below

Behavior:
- Auto-grow up to 4 lines
- Enter to send, Shift+Enter for newline
- Debounce typing indicator
```

### Buttons

```
Primary Button:
┌────────────────────┐
│   Send Message     │  <- Blue bg, white text
└────────────────────┘

Secondary Button:
┌────────────────────┐
│   View Sources     │  <- White bg, blue text, blue border
└────────────────────┘

Ghost Button:
     Clear Chat         <- No bg, blue text

Icon Button:
    [✕]                 <- Minimal, for close/actions

States for all:
- Default
- Hover (darker/lighter)
- Active (pressed)
- Disabled (50% opacity)
- Loading (spinner)
```

### Source Citations

When displaying AI responses with sources:

```
┌─────────────────────────────────────────┐
│ Here's what I found about billing...    │
│                                         │
│ Your subscription renews on the 1st     │
│ of each month. [1]                      │
│                                         │
│ ─────────────────────────────────────── │
│ Sources:                                │
│ [1] billing-faq.md - "Renewal dates"    │
│ [2] pricing.md - "Monthly plans"        │
└─────────────────────────────────────────┘

- Inline citations: Superscript numbers
- Source list: Collapsible, at bottom
- Each source: Clickable, shows preview
```

### Feedback Component

```
Was this helpful?
   ┌───┐  ┌───┐
   │ 👍 │  │ 👎 │
   └───┘  └───┘

After selection (negative):
┌─────────────────────────────────────────┐
│ What went wrong?                        │
│                                         │
│ ○ Incorrect information                 │
│ ○ Didn't answer my question             │
│ ○ Hard to understand                    │
│ ○ Other: [________________]             │
│                                         │
│              [Submit Feedback]          │
└─────────────────────────────────────────┘
```

---

## Dashboard Guidelines

### Navigation

```
┌─────────────────┬───────────────────────────────────┐
│                 │                                   │
│   SIMBA         │  Dashboard / Documents            │
│                 │                                   │
│   ─────────     ├───────────────────────────────────┤
│                 │                                   │
│   📊 Dashboard  │                                   │
│   📄 Documents  │     Main Content Area             │
│   💬 Convos     │                                   │
│   📈 Analytics  │                                   │
│   ⚙️ Settings   │                                   │
│                 │                                   │
│                 │                                   │
│   ─────────     │                                   │
│                 │                                   │
│   👤 Profile    │                                   │
│                 │                                   │
└─────────────────┴───────────────────────────────────┘

Sidebar:
- Width: 240px (expanded), 64px (collapsed)
- Collapsible on desktop
- Drawer on mobile
```

### Data Tables

```
┌────────────────────────────────────────────────────────────┐
│ Documents                               [+ Upload] [⋮]     │
├────────────────────────────────────────────────────────────┤
│ □  Name              Status      Size     Modified    ⋮    │
├────────────────────────────────────────────────────────────┤
│ □  user-guide.pdf    ● Ready     2.4MB    2h ago     ⋮    │
│ □  faq.md            ○ Parsing   156KB    5m ago     ⋮    │
│ □  pricing.docx      ● Ready     89KB     1d ago     ⋮    │
├────────────────────────────────────────────────────────────┤
│ Showing 1-3 of 24                    [◄] [1] [2] [3] [►]   │
└────────────────────────────────────────────────────────────┘

Features:
- Sortable columns
- Bulk selection
- Inline actions menu
- Pagination or infinite scroll
- Search/filter bar
```

### Cards

```
┌────────────────────────────────────┐
│                                    │
│  Total Conversations               │
│                                    │
│  1,234                             │
│  ↑ 12% from last week              │
│                                    │
└────────────────────────────────────┘

- Consistent padding (24px)
- Subtle shadow
- Clear hierarchy
- Trend indicators
```

---

## Interaction Patterns

### Loading States

```
Skeleton loading (preferred):
┌─────────────────────────────────────┐
│ ████████████████████                │
│ ██████████████████████████          │
│ █████████████████                   │
└─────────────────────────────────────┘

Spinner (for actions):
[○ Loading...]

Progress bar (for uploads):
[████████░░░░░░░░░░░░] 45%
```

### Empty States

```
┌─────────────────────────────────────┐
│                                     │
│            📄                       │
│                                     │
│     No documents yet                │
│                                     │
│  Upload your first document to      │
│  start building your knowledge      │
│  base.                              │
│                                     │
│       [+ Upload Document]           │
│                                     │
└─────────────────────────────────────┘

Elements:
- Relevant illustration/icon
- Clear heading
- Helpful description
- Primary action
```

### Error States

```
Inline error:
┌─────────────────────────────────────┐
│ ⚠️ Failed to load documents         │
│    Network error. Please try again. │
│                        [Retry]      │
└─────────────────────────────────────┘

Toast notification:
┌─────────────────────────────────────┐
│ ✕  Document upload failed           │
└─────────────────────────────────────┘

Full page error:
┌─────────────────────────────────────┐
│                                     │
│            ⚠️                        │
│                                     │
│    Something went wrong             │
│                                     │
│  We're having trouble loading       │
│  this page. Please try again.       │
│                                     │
│   [Refresh]  [Contact Support]      │
│                                     │
└─────────────────────────────────────┘
```

### Confirmations

```
Destructive action:
┌─────────────────────────────────────┐
│                                     │
│    Delete Document?                 │
│                                     │
│  This will permanently delete       │
│  "user-guide.pdf" and remove it     │
│  from your knowledge base.          │
│                                     │
│  [Cancel]          [Delete]         │
│                     ↑ red           │
└─────────────────────────────────────┘

Rules:
- Always confirm destructive actions
- Use clear, specific language
- Highlight the destructive button
- Provide escape route
```

---

## Responsive Design

### Breakpoints

```css
/* Mobile first approach */
--simba-screen-sm: 640px;   /* Small tablets */
--simba-screen-md: 768px;   /* Tablets */
--simba-screen-lg: 1024px;  /* Small desktop */
--simba-screen-xl: 1280px;  /* Desktop */
--simba-screen-2xl: 1536px; /* Large desktop */
```

### Widget Adaptations

```
Desktop (>768px):
- Floating widget in corner
- 380px width, 600px height
- Minimize/maximize

Mobile (<768px):
- Full screen overlay
- Bottom sheet entry
- Gesture to dismiss
```

### Dashboard Adaptations

```
Desktop (>1024px):
- Full sidebar visible
- Multi-column layouts
- Hover interactions

Tablet (768px-1024px):
- Collapsible sidebar
- Simplified tables
- Touch-friendly targets

Mobile (<768px):
- Bottom navigation
- Single column
- Pull-to-refresh
```

---

## Accessibility

### Requirements

- **WCAG 2.1 AA compliance** minimum
- **Keyboard navigation** for all interactions
- **Screen reader support** with proper ARIA labels
- **Focus indicators** visible and clear
- **Color contrast** 4.5:1 minimum for text

### Keyboard Shortcuts

```
Widget:
- Cmd/Ctrl + K: Open widget
- Escape: Close widget
- Enter: Send message
- Arrow up: Edit last message

Dashboard:
- /: Focus search
- g + d: Go to documents
- g + c: Go to conversations
- ?: Show keyboard shortcuts
```

### ARIA Patterns

```tsx
// Chat widget
<div role="log" aria-label="Chat messages" aria-live="polite">
  <div role="listitem" aria-label="Assistant message">
    {message}
  </div>
</div>

// Input
<input
  role="textbox"
  aria-label="Type your message"
  aria-describedby="input-hint"
/>

// Loading
<div role="status" aria-label="Loading response">
  <span className="sr-only">Assistant is typing</span>
</div>
```

---

## Animation Guidelines

### Principles

1. **Purposeful** - Animations convey meaning
2. **Fast** - 150-300ms for most interactions
3. **Subtle** - Don't distract from content
4. **Reducible** - Respect prefers-reduced-motion

### Timing

```css
--simba-duration-fast: 150ms;    /* Micro-interactions */
--simba-duration-normal: 200ms;  /* Standard transitions */
--simba-duration-slow: 300ms;    /* Larger movements */

--simba-ease-in: cubic-bezier(0.4, 0, 1, 1);
--simba-ease-out: cubic-bezier(0, 0, 0.2, 1);
--simba-ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
```

### Common Animations

```css
/* Fade in */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Slide up (for messages) */
@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Typing indicator */
@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}
```

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Dark Mode

### Implementation

```tsx
// Theme provider
<ThemeProvider defaultTheme="system" storageKey="simba-theme">
  <App />
</ThemeProvider>

// Usage
const { theme, setTheme } = useTheme();
```

### Color Mapping

```css
:root {
  --background: var(--simba-gray-50);
  --foreground: var(--simba-gray-900);
  --card: white;
  --border: var(--simba-gray-200);
}

.dark {
  --background: var(--simba-dark-bg);
  --foreground: var(--simba-dark-text);
  --card: var(--simba-dark-card);
  --border: var(--simba-dark-border);
}
```

---

## Theming for Customers

The widget must be customizable for customer branding:

### Customizable Properties

```typescript
interface SimbaTheme {
  // Colors
  primaryColor: string;
  backgroundColor: string;
  textColor: string;

  // Typography
  fontFamily: string;
  fontSize: 'small' | 'medium' | 'large';

  // Layout
  borderRadius: 'none' | 'small' | 'medium' | 'large';
  position: 'bottom-right' | 'bottom-left' | 'inline';

  // Branding
  logo?: string;
  title?: string;
  welcomeMessage?: string;
}
```

### Example Configurations

```typescript
// Corporate style
{
  primaryColor: '#1a365d',
  borderRadius: 'small',
  fontFamily: 'Arial, sans-serif'
}

// Playful style
{
  primaryColor: '#7c3aed',
  borderRadius: 'large',
  fontFamily: 'Nunito, sans-serif'
}
```

---

## Design Checklist

Before shipping any UI component:

- [ ] Works on mobile (320px+)
- [ ] Works on desktop (1920px)
- [ ] Keyboard navigable
- [ ] Screen reader tested
- [ ] Loading state handled
- [ ] Error state handled
- [ ] Empty state handled
- [ ] Dark mode supported
- [ ] Animations respect reduced-motion
- [ ] Touch targets are 44px+ on mobile
- [ ] Color contrast passes WCAG AA
- [ ] Matches design system tokens
