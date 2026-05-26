"""
Research & Summarize workflow template.

A 3-agent pipeline: Researcher searches the web, Writer creates a report,
Reviewer provides feedback. Includes a revision loop back to the Writer
when the Reviewer requests changes.
"""

TEMPLATE_ID = "research_summarize"

TEMPLATE_NAME = "Research & Summarize"

TEMPLATE_DESCRIPTION = (
    "A 3-agent pipeline: Researcher searches the web, Writer creates a report, "
    "Reviewer provides feedback. Includes a revision loop."
)

AGENTS = [
    {
        "name": "Researcher",
        "role": "researcher",
        "model": "gpt-4o-mini",
        "tools": ["web_search", "web_scrape"],
        "temperature": 0.3,
        "max_tokens": 4096,
        "memory_enabled": True,
        "memory_window": 20,
        "channels": [],
        "skills": [],
        "interaction_rules": {},
        "guardrails": {},
        "schedule": None,
        "system_prompt": (
            "You are a thorough and methodical Research Agent. Your job is to investigate "
            "a given topic by searching the web and gathering relevant, high-quality information.\n\n"
            "When you receive a research request:\n"
            "1. Break the topic into 3-5 key subtopics or questions that need answering.\n"
            "2. Use the web_search tool to find authoritative sources for each subtopic.\n"
            "3. Use the web_scrape tool to extract detailed content from the most promising URLs.\n"
            "4. Organize your findings into a structured format with the following sections:\n"
            "   - **Topic Overview**: A brief summary of what the topic is about.\n"
            "   - **Key Findings**: Numbered list of the most important facts, data points, and insights.\n"
            "   - **Sources**: List of URLs and source names you consulted.\n"
            "   - **Open Questions**: Any areas where information was unclear or conflicting.\n\n"
            "Always prioritize accuracy over speed. If sources conflict, note the discrepancy. "
            "Cite your sources inline using [Source Name] notation. Do not fabricate information."
        ),
    },
    {
        "name": "Writer",
        "role": "writer",
        "model": "gpt-4o-mini",
        "tools": [],
        "temperature": 0.7,
        "max_tokens": 8192,
        "memory_enabled": True,
        "memory_window": 20,
        "channels": [],
        "skills": [],
        "interaction_rules": {},
        "guardrails": {},
        "schedule": None,
        "system_prompt": (
            "You are a skilled Report Writer Agent. Your job is to take raw research findings "
            "and transform them into a clear, well-structured, and engaging report.\n\n"
            "When you receive research findings:\n"
            "1. Read through all the findings carefully and identify the narrative thread.\n"
            "2. Write a polished report with the following structure:\n"
            "   - **Title**: A clear, descriptive title for the report.\n"
            "   - **Executive Summary**: 2-3 sentences summarizing the key takeaways.\n"
            "   - **Introduction**: Context and why this topic matters.\n"
            "   - **Main Body**: Organized into logical sections with headers. Present the "
            "information in a flowing narrative, not just a list of facts.\n"
            "   - **Conclusion**: Key takeaways and any recommended next steps.\n"
            "   - **References**: Properly formatted source list.\n\n"
            "If you receive revision feedback from the Reviewer, carefully address each point "
            "of feedback. Maintain the overall structure but improve the specific areas mentioned. "
            "Explain what changes you made at the top of your revised output.\n\n"
            "Write in a professional but accessible tone. Avoid jargon unless it is defined. "
            "Use concrete examples and data points from the research to support claims."
        ),
    },
    {
        "name": "Reviewer",
        "role": "reviewer",
        "model": "gpt-4o-mini",
        "tools": [],
        "temperature": 0.4,
        "max_tokens": 4096,
        "memory_enabled": True,
        "memory_window": 20,
        "channels": [],
        "skills": [],
        "interaction_rules": {},
        "guardrails": {},
        "schedule": None,
        "system_prompt": (
            "You are a critical Report Reviewer Agent. Your job is to evaluate reports for "
            "quality, accuracy, clarity, and completeness, then either approve them or request "
            "specific revisions.\n\n"
            "When you receive a report to review, evaluate it against these criteria:\n"
            "1. **Accuracy**: Are claims supported by the cited sources? Are there unsupported statements?\n"
            "2. **Completeness**: Does the report cover all important aspects of the topic? "
            "Are there obvious gaps?\n"
            "3. **Clarity**: Is the writing clear and well-organized? Is the logical flow easy to follow?\n"
            "4. **Structure**: Does it have a proper title, executive summary, introduction, "
            "body, conclusion, and references?\n"
            "5. **Tone**: Is the tone appropriate and consistent throughout?\n\n"
            "After your review, respond with EXACTLY one of these two formats:\n\n"
            "If the report meets quality standards:\n"
            "APPROVED: [paste the final report here in full]\n\n"
            "If the report needs improvement:\n"
            "NEEDS_REVISION: [provide specific, actionable feedback organized by category — "
            "list exactly what needs to change and why]\n\n"
            "Be constructive but rigorous. Do not approve reports that have significant gaps "
            "or factual issues. A good report should be something you would be comfortable "
            "presenting to a stakeholder."
        ),
    },
]

GRAPH_DEFINITION = {
    "nodes": [
        {
            "id": "start",
            "type": "start",
            "position": {"x": 400, "y": 0},
            "data": {"label": "Start"},
        },
        {
            "id": "researcher",
            "type": "agent",
            "position": {"x": 400, "y": 150},
            "data": {
                "label": "Researcher",
                "agentName": "Researcher",
                "role": "researcher",
            },
        },
        {
            "id": "writer",
            "type": "agent",
            "position": {"x": 400, "y": 300},
            "data": {
                "label": "Writer",
                "agentName": "Writer",
                "role": "writer",
            },
        },
        {
            "id": "reviewer",
            "type": "agent",
            "position": {"x": 400, "y": 450},
            "data": {
                "label": "Reviewer",
                "agentName": "Reviewer",
                "role": "reviewer",
            },
        },
        {
            "id": "condition_review",
            "type": "condition",
            "position": {"x": 400, "y": 600},
            "data": {
                "label": "Approved?",
                "condition": "output.startswith('APPROVED:')",
            },
        },
        {
            "id": "end",
            "type": "end",
            "position": {"x": 400, "y": 750},
            "data": {"label": "End"},
        },
    ],
    "edges": [
        {
            "id": "e-start-researcher",
            "source": "start",
            "target": "researcher",
            "type": "default",
        },
        {
            "id": "e-researcher-writer",
            "source": "researcher",
            "target": "writer",
            "type": "default",
        },
        {
            "id": "e-writer-reviewer",
            "source": "writer",
            "target": "reviewer",
            "type": "default",
        },
        {
            "id": "e-reviewer-condition",
            "source": "reviewer",
            "target": "condition_review",
            "type": "default",
        },
        {
            "id": "e-condition-end",
            "source": "condition_review",
            "target": "end",
            "type": "default",
            "label": "approved",
            "data": {"branch": "true"},
        },
        {
            "id": "e-condition-writer",
            "source": "condition_review",
            "target": "writer",
            "type": "default",
            "label": "needs_revision",
            "data": {"branch": "false"},
        },
    ],
}
