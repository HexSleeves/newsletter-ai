"""Optimized prompts for LLM operations with token efficiency."""

from dataclasses import dataclass
from typing import Literal


@dataclass
class PromptTemplate:
    """Template for LLM prompts with system and user messages."""

    system: str
    user: str


# Token-efficient system prompts
SYSTEM_PROMPTS = {
    "summarizer": "You are a concise news summarizer. Output only the summary, no preamble.",
    "bullet_points": "You extract key facts as bullet points. Output only bullets, no preamble.",
    "headline": "You create engaging headlines. Output only the headline.",
}


# Summarization prompts (optimized for token efficiency)
SUMMARY_PROMPTS = {
    "concise": PromptTemplate(
        system=SYSTEM_PROMPTS["summarizer"],
        user="Summarize in 2-3 sentences:\n\nTitle: {title}\n{content}",
    ),
    "ultra_concise": PromptTemplate(
        system=SYSTEM_PROMPTS["summarizer"],
        user="1-sentence summary:\n\n{title}\n{content}",
    ),
    "bullet_points": PromptTemplate(
        system=SYSTEM_PROMPTS["bullet_points"],
        user="Extract 3-5 key facts:\n\n{title}\n{content}",
    ),
    "structured": PromptTemplate(
        system=SYSTEM_PROMPTS["summarizer"],
        user="""Summarize:

Title: {title}

Key points:
{content}

Format: What | Why | Impact (1 sentence each)""",
    ),
}


# Newsletter generation prompts
NEWSLETTER_PROMPTS = {
    "section_intro": PromptTemplate(
        system="You write engaging newsletter section intros. Keep it brief and professional.",
        user="Write a 1-sentence intro for this section:\n\nTopic: {topic}\nArticles: {count}",
    ),
    "headline_optimizer": PromptTemplate(
        system=SYSTEM_PROMPTS["headline"],
        user="Make this headline more engaging (max 10 words):\n\n{title}",
    ),
}


# Batch processing prompts (for multiple articles)
BATCH_PROMPTS = {
    "bulk_summary": PromptTemplate(
        system=SYSTEM_PROMPTS["summarizer"],
        user="""Summarize each article (1 sentence each):

{articles}

Format: [1] summary | [2] summary | ...""",
    ),
}


def get_prompt(
    category: Literal["summary", "newsletter", "batch"],
    variant: str,
) -> PromptTemplate:
    """Get a prompt template by category and variant.

    Args:
        category: Prompt category (summary, newsletter, batch)
        variant: Specific prompt variant within category

    Returns:
        PromptTemplate with system and user messages

    Raises:
        KeyError: If category/variant combination doesn't exist
    """
    prompts_map = {
        "summary": SUMMARY_PROMPTS,
        "newsletter": NEWSLETTER_PROMPTS,
        "batch": BATCH_PROMPTS,
    }

    if category not in prompts_map:
        raise KeyError(f"Unknown prompt category: {category}")

    category_prompts = prompts_map[category]
    if variant not in category_prompts:
        raise KeyError(f"Unknown variant '{variant}' in category '{category}'")

    return category_prompts[variant]


def format_prompt(template: PromptTemplate, **kwargs) -> tuple[str, str]:
    """Format a prompt template with provided values.

    Args:
        template: PromptTemplate to format
        **kwargs: Values to substitute in template

    Returns:
        Tuple of (system_message, user_message)
    """
    system = template.system.format(**kwargs) if "{" in template.system else template.system
    user = template.user.format(**kwargs)
    return system, user


# Content truncation for token efficiency
def truncate_content(content: str, max_chars: int = 1500) -> str:
    """Truncate content to save tokens while preserving meaning.

    Args:
        content: Article content to truncate
        max_chars: Maximum character count (default: 1500, ~375 tokens)

    Returns:
        Truncated content with ellipsis if needed
    """
    if len(content) <= max_chars:
        return content

    # Try to break at sentence boundary
    truncated = content[:max_chars]
    last_period = truncated.rfind(". ")

    if last_period > max_chars * 0.7:  # Only use if we keep at least 70%
        return truncated[: last_period + 1]

    return truncated.rstrip() + "..."


# Batch formatting for efficient multi-article processing
def format_articles_batch(articles: list[dict], max_articles: int = 10) -> str:
    """Format multiple articles for batch processing.

    Args:
        articles: List of article dicts with 'title' and 'content'
        max_articles: Maximum articles to include in one batch

    Returns:
        Formatted string of articles
    """
    batch = articles[:max_articles]
    formatted = []

    for idx, article in enumerate(batch, 1):
        content = truncate_content(article.get("content", ""), max_chars=500)
        formatted.append(f"[{idx}] {article.get('title', 'Untitled')}\n{content}")

    return "\n\n".join(formatted)
