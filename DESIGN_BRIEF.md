# Design brief — MA Grader desktop app

_Paste everything below into a Claude design session. Attach the screenshot of
the current app if you have one._

---

You are designing the visual language and high-fidelity screens for **MA Grader**,
a cross-platform desktop app (macOS + Windows) that college instructors use to
autograde spreadsheet assignments. The workflow is simple: an instructor drops a
ZIP of student submissions, picks the assignment (MA1 / MA2 / MA3), and the app
grades the whole class and produces graded workbooks plus an instructor master
sheet. It already works — I need you to make it look and feel exceptional.

## Build context (so your output is implementable)
- Stack: **Electron + React 18 + Tailwind CSS + Vite**. Deliver decisions that map
  to Tailwind theme tokens / CSS variables, not bespoke CSS I can't reuse.
- It's a **resizable desktop window**, default ~1040×760, min ~880×620. Not mobile,
  not a marketing site.
- Existing structure: `src/App.jsx` (screens/state), `src/ui.jsx` (Button, Card,
  Segmented, Stat, Badge), `index.css`, `tailwind.config.js`.

## Aesthetic direction
**Modern edtech with a "Tron × Tesla" signature.** Dark is the hero theme:
near-black surfaces, premium minimalism, and electric neon accents (think glowing
cyan/electric-blue hairlines and edges) used sparingly as energy, not decoration.
Tesla side = restraint, precision, lots of negative space, confident typography.
Tron side = thin luminous lines, subtle glow on interactive/active elements, a
high-tech feel. The result should feel like a premium instrument, not a toy.

**Critical tension to resolve:** this is a *trust-sensitive grading tool*. Scores,
student names, and feedback must be crisp and unmistakably legible. Reserve glow
and neon for accents, active states, and progress — never let it compromise the
readability of data. Numbers should use tabular figures.

## Theme requirements
- **Light + dark, auto-following the OS setting.** Dark is the signature identity;
  light must be an equally polished, Tesla-clean sibling (bright, minimal, the neon
  accent translated to a confident solid accent that still reads in daylight).
- All status colors must be **colorblind-safe** and pass **WCAG AA** contrast in
  both modes. Don't encode meaning by hue alone — pair with icon/label.

## Screens to design (full product, not just today's)
Current:
1. **Setup** — drop zone for the submissions ZIP (idle / hover / file-selected /
   dragging states), a "Course label" text field, an MA1/MA2/MA3 segmented control,
   an optional output-folder picker, and a primary "Grade submissions" action.
2. **Running** — live progress: "Grading 7 of 19", a progress bar, and the current
   student name. This is a hero moment for the Tron energy.
3. **Results** — summary stat cards (students graded, issues, assignment), buttons
   to open the instructor master workbook and the graded folder, an "issues / needs
   a look" list, and a scrollable student list with status badges.
4. **Error** — a calm, non-alarming failure state with a plain-language message.

Planned (design the system to absorb these):
5. **Manual grading panel** — for the MA3 written-analysis essay, which always needs
   a human. Show the student's written response, the rubric, a score input (0–5), and
   a save action that writes the score back. Likely a focused review flow / side panel,
   navigable student-to-student.
6. **History** — a list of past grading runs (course, assignment, date, counts) that
   can be re-opened.
7. **Settings** — default output/workspace folder, currency-rate cache controls, and
   theme override (system / light / dark).

## Components to specify
Buttons (primary / soft / subtle / ghost), segmented control, text input, the
drag-and-drop zone with all states, progress bar, stat/metric card, status badges
(graded / issue / manual-needed / not-submitted), list rows, side panel, empty
states, loading states, toasts. Define the **glow/elevation rules** precisely
(when a thing glows, how much, hover vs active vs focus) so it stays consistent and
restrained.

## Identity
Propose a simple **app icon / logo mark** that fits the Tron×Tesla feel and reads at
small sizes (dock, taskbar). A checkmark is the current placeholder — feel free to
go further.

## Deliverables (please produce visual mockups, not just description)
1. A one-page **design language**: full palette with hex values and semantic roles
   (surfaces, text, borders, accent, status) for **both** light and dark; type scale;
   spacing and radius scale; the glow/elevation rules; and motion guidance (durations,
   easing, what animates).
2. **High-fidelity mockups** of every screen above — all in dark (the hero), plus
   setup + results + manual-grading shown in light too.
3. **Component specs** with states.
4. A **Tailwind-ready token table** (colors, radii, shadows/glows) I can drop into
   `tailwind.config.js` and CSS variables, so the design is directly implementable.

Think like a product designer: propose and justify choices, flag risks (e.g.
neon-on-dark legibility, status-color accessibility), and don't just decorate the
existing layout — improve the hierarchy and flow where it helps. Ask me anything you
need before you start.
