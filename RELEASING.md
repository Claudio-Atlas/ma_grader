# Releasing MA Grader (Windows .exe + macOS .dmg)

You build the installers in the cloud with GitHub Actions — no Windows machine
and no Python needed on anyone's computer. You push the code to GitHub once,
then every time you tag a version, GitHub builds **both** a Windows `.exe` and a
macOS `.dmg` and posts them on your repo's Releases page. You download them and
send them to your coworkers.

This is a one-time setup (~15 min). After that, cutting a new release is three
commands.

---

## Part A — One-time setup: put the code on GitHub

You'll do this from the Terminal on your Mac. Copy/paste each block.

### 1. Make sure Git is installed

```bash
git --version
```

If it prints a version, you're set. If it instead pops up a box offering to
install "command line developer tools," click **Install**, wait, then re-run.

### 2. Install the GitHub CLI (makes signing in painless)

```bash
brew install gh
```

(If you don't have Homebrew, install it first from https://brew.sh, then run the
line above.)

### 3. Sign in to GitHub

```bash
gh auth login
```

Choose: **GitHub.com** → **HTTPS** → **Login with a web browser**. It shows a
one-time code; press Enter, your browser opens, paste the code, authorize. Done.

### 4. Turn your project folder into a repo and push it

```bash
cd ~/Desktop/ma_grader
git init
git add .
git commit -m "MA Grader app + Windows/macOS build workflow"
gh repo create ma_grader --private --source=. --remote=origin --push
```

That last command creates a **private** repo named `ma_grader` on your GitHub
account and uploads everything. (`.gitignore` keeps the heavy stuff — node
modules, the Python venv, old build output — out of the upload, so it's quick.)

> Your Anthropic API key is **not** in the code — it lives encrypted on each
> machine. Nothing secret gets pushed.

---

## Part B — Cut a release (build the installers)

Every time you want fresh installers (e.g. after fixing a grading bug):

### 1. Save and push any changes

```bash
cd ~/Desktop/ma_grader
git add .
git commit -m "describe what changed"
git push
```

### 2. Tag a version and push the tag

Pick the next version number. The app is currently **0.1.1**, so:

```bash
git tag v0.1.1
git push origin v0.1.1
```

> Tags must start with `v`. Next time bump it (`v0.1.2`, `v0.2.0`, …). If you
> bump the number, also change `"version"` in `desktop/package.json` to match so
> the installer filename and the in-app About box agree.

### 3. Watch it build

Open your repo on github.com → **Actions** tab. You'll see a run with two jobs,
**Build (windows-latest)** and **Build (macos-latest)**. They take ~10–15
minutes. Green checkmarks = done.

### 4. Grab the installers

Go to the repo's **Releases** page (right-hand sidebar on the repo home, or
`https://github.com/<you>/ma_grader/releases`). The new release will have two
files attached:

- `MA-Grader-Setup-0.1.1.exe`  ← Windows
- `MA Grader-0.1.1.dmg`        ← macOS (Apple Silicon)

Download whichever you need.

---

## Part C — Send it to a coworker

Two easy ways:

- **Send the file** — the `.exe` (or `.dmg`) over email/Drive/Slack. It's
  self-contained; they don't need Python or anything else.
- **Send the link** — if the coworker has a GitHub account, just send them the
  Releases page URL and they download it themselves.

### What the coworker does

**Windows (`.exe`):** double-click it. Windows SmartScreen may show a blue
"Windows protected your PC" box because the app isn't code-signed. They click
**More info → Run anyway** — once. It installs like any normal program and won't
warn again.

**macOS (`.dmg`):** double-click, drag **MA Grader** into Applications, eject the
disk image. First launch: **right-click the app → Open → Open** (bypasses the
unsigned-app warning, just once).

### Everyone uses their own API key

The AI paper-grading feature needs an Anthropic API key. Each person enters
**their own** key in the app under **Settings → API key** (it's stored encrypted
on their machine). Don't share yours.

---

## Notes & options

- **macOS build is Apple-Silicon (arm64).** That covers M1/M2/M3+ Macs. If a
  coworker has an old Intel Mac and it won't run, tell me and I'll add an Intel
  build to the workflow.
- **Removing the SmartScreen / Gatekeeper warnings** requires paid code signing
  (Windows: ~$10/mo Azure Trusted Signing; macOS: your Apple Developer ID). The
  warnings are cosmetic — the app works fine past them. Say the word and I'll
  wire signing into the same workflow.
- **Manual build without tagging:** on the Actions tab, pick "Build installers" →
  **Run workflow**. That builds both installers and attaches them as downloadable
  *artifacts* on the run page (no Release is created).
- **Cost:** GitHub Actions' free tier easily covers a handful of builds a month
  on a private repo.
