# flake8: noqa=E501
# pylint: disable=line-too-long

"""Optimized prompts for LLM operations with token efficiency."""

from dataclasses import dataclass
from typing import Literal


@dataclass
class PromptTemplate:
    """Template for LLM prompts with system and user messages."""

    system: str
    user: str


# Clear, directive system prompts
SYSTEM_PROMPTS = {
    "summarizer": "You are a professional news summarizer. Provide clear, accurate summaries without preamble or meta-commentary.",
    "bullet_points": "You extract key information as concise bullet points. Output only the bullets with no introduction.",
    "headline": "You craft engaging, accurate headlines. Output only the headline with no explanation.",
}


# Summarization prompts (optimized for clarity and token efficiency)
SUMMARY_PROMPTS = {
    "concise": PromptTemplate(
        system=SYSTEM_PROMPTS["summarizer"],
        user="Summarize this article in 2-3 clear, informative sentences.\n\nTitle: {title}\nContent: {content}\n\nOutput only the summary.",
    ),
    "summary": PromptTemplate(
        system=SYSTEM_PROMPTS["summarizer"],
        user="Write a concise paragraph (4-6 sentences) covering the main key points of this article.\n\nTitle: {title}\nContent: {content}\n\nFocus on: what happened, why it matters, and key implications. Output only the paragraph.",
    ),
    "ultra_concise": PromptTemplate(
        system=SYSTEM_PROMPTS["summarizer"],
        user="Provide a single sentence summary of this article.\n\nTitle: {title}\nContent: {content}\n\nOutput only the summary.",
    ),
    "bullet_points": PromptTemplate(
        system=SYSTEM_PROMPTS["bullet_points"],
        user="Extract 4-6 key facts from this article as bullet points.\n\nTitle: {title}\nContent: {content}\n\nEach bullet should be one complete sentence. Output only the bullets.",
    ),
    "structured": PromptTemplate(
        system=SYSTEM_PROMPTS["summarizer"],
        user="""Summarize this article in three parts.

Title: {title}
Content: {content}

Format:
- What: [One sentence describing what happened]
- Why: [One sentence explaining the significance]
- Impact: [One sentence on implications or outcomes]

Output only these three bullets.""",
    ),
}


# Newsletter generation prompts
NEWSLETTER_PROMPTS = {
    "section_intro": PromptTemplate(
        system="You write engaging, professional newsletter introductions. Be concise and welcoming.",
        user="Write a single engaging sentence introducing this newsletter section.\n\nTopic: {topic}\nNumber of articles: {count}\n\nOutput only the introduction sentence.",
    ),
    "headline_optimizer": PromptTemplate(
        system=SYSTEM_PROMPTS["headline"],
        user="Create a more engaging version of this headline. Keep it under 12 words and maintain accuracy.\n\nOriginal: {title}\n\nOutput only the new headline.",
    ),
}


# Batch processing prompts (for multiple articles)
BATCH_PROMPTS = {
    "bulk_summary": PromptTemplate(
        system=SYSTEM_PROMPTS["summarizer"],
        user="""Provide a one-sentence summary for each article below.

{articles}

Format your response as:
[1] <summary>
[2] <summary>
...

Output only the numbered summaries.""",
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
def truncate_content(content: str, max_chars: int = 2000) -> str:
    """Truncate content to save tokens while preserving meaning.

    Args:
        content: Article content to truncate
        max_chars: Maximum character count (default: 2000, ~500 tokens)

    Returns:
        Truncated content with ellipsis if needed
    """
    if len(content) <= max_chars:
        return content

    # Try to break at sentence boundary
    truncated = content[:max_chars]
    last_period = max(
        truncated.rfind(". "),
        truncated.rfind("! "),
        truncated.rfind("? "),
    )

    if last_period > max_chars * 0.75:  # Only use if we keep at least 75%
        return truncated[: last_period + 1].strip()

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
        content = truncate_content(article.get("content", ""), max_chars=600)
        title = article.get("title", "Untitled")
        formatted.append(f"[{idx}] {title}\n{content}")

    return "\n\n---\n\n".join(formatted)
