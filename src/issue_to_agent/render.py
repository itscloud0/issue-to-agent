from __future__ import annotations

import html
import json

from .models import TaskPack


def render_json(pack: TaskPack) -> str:
    return json.dumps(pack.to_dict(), indent=2, sort_keys=True) + "\n"


def render_markdown(pack: TaskPack) -> str:
    lines = [
        "# Issue Agent Pack",
        "",
        f"**Issue:** {pack.issue.title}",
    ]
    if pack.issue.url:
        lines.append(f"**URL:** {pack.issue.url}")
    if pack.issue.labels:
        lines.append("**Labels:** " + ", ".join(pack.issue.labels))

    lines.extend(
        [
            "",
            "## Ready-To-Paste Agent Prompt",
            "",
            "```text",
            pack.prompt.rstrip(),
            "```",
            "",
            "## Relevant Files",
            "",
        ]
    )
    if pack.relevant_files:
        for hit in pack.relevant_files:
            lines.append(f"### `{hit.path}`")
            lines.append(f"- Score: {hit.score}")
            for reason in hit.reasons:
                lines.append(f"- {reason}")
            if hit.snippets:
                lines.append("")
                lines.append("```text")
                lines.extend(hit.snippets)
                lines.append("```")
            lines.append("")
    else:
        lines.append("No relevant files were detected. Start with repo search.")
        lines.append("")

    lines.extend(["## Suggested Commands", ""])
    if pack.repository.commands:
        lines.extend(f"- `{command}`" for command in pack.repository.commands)
    else:
        lines.append("- No commands detected.")

    lines.extend(["", "## Acceptance Criteria", ""])
    lines.extend(f"- {criterion}" for criterion in pack.acceptance_criteria)

    lines.extend(["", "## Risks", ""])
    if pack.risks:
        lines.extend(f"- {risk}" for risk in pack.risks)
    else:
        lines.append("- No obvious risks detected by static scan.")

    lines.extend(["", "## Repo Instructions", ""])
    if pack.repository.instructions:
        for instruction in pack.repository.instructions:
            lines.append(f"### `{instruction.path}`")
            lines.append("")
            lines.append("```text")
            lines.append(instruction.excerpt)
            lines.append("```")
            lines.append("")
    else:
        lines.append("No AGENTS.md, CLAUDE.md, or common editor instruction file detected.")

    return "\n".join(lines).rstrip() + "\n"


def render_html(pack: TaskPack) -> str:
    file_cards = "\n".join(render_file_card(hit) for hit in pack.relevant_files)
    if not file_cards:
        file_cards = "<p>No relevant files were detected. Start with repo search.</p>"

    commands = "".join(
        f"<li><code>{html.escape(command)}</code></li>"
        for command in pack.repository.commands
    ) or "<li>No commands detected.</li>"
    criteria = "".join(
        f"<li>{html.escape(criterion)}</li>" for criterion in pack.acceptance_criteria
    )
    risks = "".join(f"<li>{html.escape(risk)}</li>" for risk in pack.risks)
    if not risks:
        risks = "<li>No obvious risks detected by static scan.</li>"

    labels = ""
    if pack.issue.labels:
        labels = "".join(
            f"<span class=\"pill\">{html.escape(label)}</span>"
            for label in pack.issue.labels
        )

    source_line = ""
    if pack.issue.url:
        source_line = f"<p><a href=\"{html.escape(pack.issue.url)}\">{html.escape(pack.issue.url)}</a></p>"
    body_excerpt = html.escape(shorten(pack.issue.body or "No issue body provided.", 900))
    instruction_count = len(pack.repository.instructions)
    command_count = len(pack.repository.commands)
    file_count = len(pack.relevant_files)
    instructions = "\n".join(
        f"""
        <div class="instruction">
          <h3>{html.escape(instruction.path)}</h3>
          <pre>{html.escape(instruction.excerpt)}</pre>
        </div>
        """
        for instruction in pack.repository.instructions
    ) or "<p>No agent instruction file detected.</p>"

    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Issue Agent Pack - {html.escape(pack.issue.title)}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f5f7fb;
      --panel: #ffffff;
      --text: #1f2933;
      --muted: #596575;
      --border: #d9e0ea;
      --accent: #0f766e;
      --accent-2: #b45309;
      --ink: #111827;
    }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font: 15px/1.5 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 28px 20px 48px;
    }}
    header {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      margin-bottom: 24px;
      padding: 24px;
    }}
    h1, h2, h3 {{
      line-height: 1.2;
      margin: 0 0 12px;
    }}
    h1 {{
      font-size: 38px;
      letter-spacing: 0;
    }}
    h2 {{
      font-size: 20px;
      margin-top: 0;
    }}
    h3 {{
      font-size: 16px;
    }}
    .subtitle {{
      color: var(--muted);
      margin: 0;
      max-width: 820px;
    }}
    .pill {{
      display: inline-block;
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 2px 9px;
      margin: 10px 6px 0 0;
      color: var(--accent);
      background: #eefaf8;
      font-size: 13px;
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      margin-top: 20px;
    }}
    .metric {{
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px;
      background: #f8fafc;
    }}
    .metric strong {{
      display: block;
      color: var(--ink);
      font-size: 22px;
      line-height: 1;
    }}
    .metric span {{
      color: var(--muted);
      font-size: 13px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: minmax(0, 1.1fr) minmax(320px, 0.9fr);
      gap: 20px;
      align-items: start;
    }}
    section, article {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 18px;
      margin-bottom: 16px;
    }}
    .full {{
      grid-column: 1 / -1;
    }}
    code, pre {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
      font-size: 13px;
    }}
    pre {{
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      background: #f2f4f1;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 12px;
    }}
    ul {{
      padding-left: 20px;
      margin: 0;
    }}
    .score {{
      color: var(--accent-2);
      font-weight: 700;
    }}
    .body-excerpt {{
      color: var(--muted);
      white-space: pre-wrap;
    }}
    a {{
      color: var(--accent);
    }}
    @media (max-width: 820px) {{
      .grid {{
        grid-template-columns: 1fr;
      }}
      .metrics {{
        grid-template-columns: 1fr;
      }}
      h1 {{
        font-size: 28px;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>Issue Agent Pack</h1>
      <p class="subtitle">{html.escape(pack.issue.title)}</p>
      {labels}
      <div class="metrics">
        <div class="metric"><strong>{file_count}</strong><span>likely files</span></div>
        <div class="metric"><strong>{command_count}</strong><span>commands</span></div>
        <div class="metric"><strong>{instruction_count}</strong><span>instruction files</span></div>
      </div>
    </header>
    <div class="grid">
      <div>
        <section>
          <h2>Issue summary</h2>
          {source_line}
          <p class="body-excerpt">{body_excerpt}</p>
        </section>
        <section>
          <h2>Likely files</h2>
          {file_cards}
        </section>
      </div>
      <aside>
        <section>
          <h2>Commands</h2>
          <ul>{commands}</ul>
        </section>
        <section>
          <h2>Acceptance criteria</h2>
          <ul>{criteria}</ul>
        </section>
        <section>
          <h2>Risk areas</h2>
          <ul>{risks}</ul>
        </section>
        <section>
          <h2>Repo Instructions</h2>
          {instructions}
        </section>
      </aside>
      <section class="full">
        <h2>Agent-ready prompt</h2>
        <pre>{html.escape(pack.prompt.rstrip())}</pre>
      </section>
    </div>
  </main>
</body>
</html>
"""
    return clean_trailing_spaces(document)

def render_prompt(pack: TaskPack) -> str:
    return pack.prompt

def render_file_card(hit: object) -> str:
    reasons = "".join(f"<li>{html.escape(reason)}</li>" for reason in hit.reasons)
    snippets = ""
    if hit.snippets:
        snippets = "<pre>" + html.escape("\n".join(hit.snippets)) + "</pre>"
    return f"""
    <article>
      <h3><code>{html.escape(hit.path)}</code></h3>
      <p class="score">Score {hit.score}</p>
      <ul>{reasons}</ul>
      {snippets}
    </article>
    """


def shorten(text: str, limit: int) -> str:
    normalized = "\n".join(line.rstrip() for line in text.strip().splitlines())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def clean_trailing_spaces(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.splitlines()) + "\n"
