from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages


class FluxState(TypedDict):
    """State schema for FLUX recommendation agent."""
    messages: Annotated[list, add_messages]
    user_input: str
    conversation_memory: list   # [{role, content}] rolling cross-turn context
    preferences: dict           # {genres, moods, topics, keywords, search_queries}
    domain_results: dict        # {videos, movies, music, podcasts, news}
    domain_scores: dict         # {videos: 0-10, ...} LLM-rated relevance
    follow_up_question: str     # LLM suggested next question for user
    cross_domain_insight: str
    final_output: str
