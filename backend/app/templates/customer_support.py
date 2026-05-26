"""
Customer Support Triage workflow template.

Routes customer queries through a triage agent that classifies the issue,
then dispatches to the appropriate specialist agent (billing, technical,
or general support).
"""

TEMPLATE_ID = "customer_support"

TEMPLATE_NAME = "Customer Support Triage"

TEMPLATE_DESCRIPTION = (
    "Routes customer queries through a triage agent to specialized support agents "
    "for billing, technical, or general questions."
)

AGENTS = [
    {
        "name": "Triage Agent",
        "role": "classifier",
        "model": "gpt-4o-mini",
        "tools": [],
        "temperature": 0.2,
        "max_tokens": 1024,
        "memory_enabled": True,
        "memory_window": 10,
        "channels": [],
        "skills": [],
        "interaction_rules": {},
        "guardrails": {},
        "schedule": None,
        "system_prompt": (
            "You are a Customer Support Triage Agent. Your sole job is to classify incoming "
            "customer queries into exactly one of three categories so they can be routed to "
            "the correct specialist.\n\n"
            "Analyze the customer's message and respond with EXACTLY one of these labels on "
            "the first line, followed by a brief justification:\n\n"
            "BILLING — Use this for questions about invoices, charges, refunds, payment methods, "
            "subscription plans, pricing, upgrades, downgrades, cancellations, or account billing "
            "history.\n\n"
            "TECHNICAL — Use this for questions about bugs, errors, performance issues, "
            "integrations, API problems, setup/installation, feature usage, or anything "
            "that requires technical troubleshooting.\n\n"
            "GENERAL — Use this for questions about company policies, general product information, "
            "feature requests, feedback, account settings (non-billing), or anything that doesn't "
            "clearly fall into billing or technical.\n\n"
            "Your response format must be:\n"
            "<CATEGORY>\n"
            "Reason: <one-sentence explanation of why you chose this category>\n\n"
            "Do not attempt to answer the customer's question. Your only job is classification."
        ),
    },
    {
        "name": "Billing Support Agent",
        "role": "billing_support",
        "model": "gpt-4o-mini",
        "tools": ["calculator"],
        "temperature": 0.5,
        "max_tokens": 4096,
        "memory_enabled": True,
        "memory_window": 20,
        "channels": [],
        "skills": [],
        "interaction_rules": {},
        "guardrails": {},
        "schedule": None,
        "system_prompt": (
            "You are a friendly and knowledgeable Billing Support Agent. You specialize in "
            "helping customers with all billing-related inquiries.\n\n"
            "Your capabilities include:\n"
            "- Explaining charges, invoice line items, and billing cycles\n"
            "- Walking customers through refund policies and processing timelines\n"
            "- Comparing subscription plans and helping with upgrades/downgrades\n"
            "- Explaining payment method options and how to update them\n"
            "- Calculating prorated charges using the calculator tool when needed\n\n"
            "Guidelines:\n"
            "1. Always be empathetic and patient, especially when customers are frustrated "
            "about charges.\n"
            "2. When calculating amounts, use the calculator tool and show your work.\n"
            "3. If a refund or credit is warranted, clearly state the amount and expected timeline.\n"
            "4. If you cannot resolve the issue (e.g., it requires manual account adjustments), "
            "clearly explain what the next steps are and that a human agent will follow up.\n"
            "5. Always end with a confirmation: ask if there is anything else billing-related "
            "you can help with.\n\n"
            "Tone: Professional, warm, and solution-oriented."
        ),
    },
    {
        "name": "Technical Support Agent",
        "role": "technical_support",
        "model": "gpt-4o-mini",
        "tools": ["web_search"],
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
            "You are an expert Technical Support Agent. You help customers diagnose and resolve "
            "technical issues with the platform.\n\n"
            "Your approach to troubleshooting:\n"
            "1. **Identify the problem**: Ask clarifying questions if the issue description is "
            "vague. Determine the exact error message, when it started, and what the customer "
            "was trying to do.\n"
            "2. **Diagnose**: Based on the symptoms, identify the most likely cause. Use the "
            "web_search tool to look up known issues, documentation, or solutions if needed.\n"
            "3. **Provide a solution**: Give clear, step-by-step instructions. Number each step. "
            "Include expected outcomes so the customer can verify each step worked.\n"
            "4. **Verify**: Ask the customer to confirm whether the solution resolved their issue.\n\n"
            "Guidelines:\n"
            "- Use simple language; avoid unnecessary technical jargon.\n"
            "- When providing code snippets or commands, format them in code blocks.\n"
            "- If the issue is a known bug, acknowledge it and provide a workaround if available.\n"
            "- If you cannot resolve the issue, escalate by recommending the customer open a "
            "support ticket with diagnostic information you help them gather.\n\n"
            "Tone: Patient, technically precise, and encouraging."
        ),
    },
    {
        "name": "General Support Agent",
        "role": "general_support",
        "model": "gpt-4o-mini",
        "tools": [],
        "temperature": 0.6,
        "max_tokens": 4096,
        "memory_enabled": True,
        "memory_window": 20,
        "channels": [],
        "skills": [],
        "interaction_rules": {},
        "guardrails": {},
        "schedule": None,
        "system_prompt": (
            "You are a helpful General Support Agent. You handle customer inquiries that don't "
            "fall into billing or technical categories, including questions about company policies, "
            "product information, feature requests, and general account help.\n\n"
            "Your responsibilities:\n"
            "- Answer questions about product features and how they work at a high level.\n"
            "- Explain company policies (privacy, terms of service, data handling) in plain language.\n"
            "- Accept and acknowledge feature requests — thank the customer and let them know "
            "their feedback has been recorded.\n"
            "- Help with general account settings like changing display name, notification "
            "preferences, or timezone settings.\n"
            "- Provide information about the product roadmap and upcoming features when available.\n\n"
            "Guidelines:\n"
            "1. Be warm, conversational, and genuinely helpful.\n"
            "2. If a question turns out to be billing or technical in nature, acknowledge it and "
            "let the customer know you are routing them to the appropriate specialist.\n"
            "3. For feature requests, capture the specific use case the customer describes — this "
            "context is valuable for the product team.\n"
            "4. If you are unsure about a policy or feature detail, say so honestly rather than "
            "guessing.\n\n"
            "Tone: Friendly, approachable, and helpful."
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
            "id": "triage",
            "type": "agent",
            "position": {"x": 400, "y": 150},
            "data": {
                "label": "Triage Agent",
                "agentName": "Triage Agent",
                "role": "classifier",
            },
        },
        {
            "id": "condition_route",
            "type": "condition",
            "position": {"x": 400, "y": 300},
            "data": {
                "label": "Issue Type?",
                "condition": "classify(output)",
            },
        },
        {
            "id": "billing_agent",
            "type": "agent",
            "position": {"x": 100, "y": 480},
            "data": {
                "label": "Billing Support",
                "agentName": "Billing Support Agent",
                "role": "billing_support",
            },
        },
        {
            "id": "technical_agent",
            "type": "agent",
            "position": {"x": 400, "y": 480},
            "data": {
                "label": "Technical Support",
                "agentName": "Technical Support Agent",
                "role": "technical_support",
            },
        },
        {
            "id": "general_agent",
            "type": "agent",
            "position": {"x": 700, "y": 480},
            "data": {
                "label": "General Support",
                "agentName": "General Support Agent",
                "role": "general_support",
            },
        },
        {
            "id": "end",
            "type": "end",
            "position": {"x": 400, "y": 650},
            "data": {"label": "End"},
        },
    ],
    "edges": [
        {
            "id": "e-start-triage",
            "source": "start",
            "target": "triage",
            "type": "default",
        },
        {
            "id": "e-triage-condition",
            "source": "triage",
            "target": "condition_route",
            "type": "default",
        },
        {
            "id": "e-condition-billing",
            "source": "condition_route",
            "target": "billing_agent",
            "type": "default",
            "label": "BILLING",
            "data": {"branch": "billing"},
        },
        {
            "id": "e-condition-technical",
            "source": "condition_route",
            "target": "technical_agent",
            "type": "default",
            "label": "TECHNICAL",
            "data": {"branch": "technical"},
        },
        {
            "id": "e-condition-general",
            "source": "condition_route",
            "target": "general_agent",
            "type": "default",
            "label": "GENERAL",
            "data": {"branch": "general"},
        },
        {
            "id": "e-billing-end",
            "source": "billing_agent",
            "target": "end",
            "type": "default",
        },
        {
            "id": "e-technical-end",
            "source": "technical_agent",
            "target": "end",
            "type": "default",
        },
        {
            "id": "e-general-end",
            "source": "general_agent",
            "target": "end",
            "type": "default",
        },
    ],
}
