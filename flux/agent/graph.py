import json
import os
import concurrent.futures
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from agent.state import FluxState
from agent.tools import (
    youtube_search,
    youtube_music_search,
    itunes_podcast_search,
    tmdb_movie_search,
    google_news_search
)
from agent.prompts import (
    PREFERENCE_EXTRACTION_PROMPT,
    CROSS_DOMAIN_SYNTHESIS_PROMPT,
    FINAL_OUTPUT_PROMPT
)


def get_llm():
    primary_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7)
    try:
        fallback_llm = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY", "dummy"),
            model="google/gemini-2.0-flash-exp:free",
            temperature=0.7
        )
        return primary_llm.with_fallbacks([fallback_llm])
    except ImportError:
        return primary_llm


def _parse_json_safe(content: str, fallback: dict) -> dict:
    """Strip markdown fences and parse JSON safely."""
    content = content.strip()
    if content.startswith("```"):
        parts = content.split("```")
        content = parts[1] if len(parts) > 1 else content
        if content.startswith("json"):
            content = content[4:]
    try:
        return json.loads(content)
    except Exception:
        return fallback


def extract_preferences_node(state: FluxState) -> FluxState:
    """Extract structured preferences + per-domain search queries using LLM."""
    memory_str = "\n".join(
        f"{m['role'].upper()}: {m['content']}"
        for m in state.get("conversation_memory", [])[-6:]  # last 3 turns
    ) or "None"

    prompt = PREFERENCE_EXTRACTION_PROMPT.format(
        conversation_memory=memory_str,
        user_input=state["user_input"]
    )

    try:
        if not os.getenv("GROQ_API_KEY") and not os.getenv("OPENROUTER_API_KEY"):
            raise ValueError("No API keys available")

        llm = get_llm()
        response = llm.invoke([
            SystemMessage(content="You are a JSON extraction expert. Return only valid JSON."),
            HumanMessage(content=prompt)
        ])
        preferences = _parse_json_safe(response.content, {
            "genres": [], "moods": [], "topics": [],
            "keywords": [state["user_input"]],
            "search_queries": {
                "videos": state["user_input"],
                "music": state["user_input"],
                "movies": state["user_input"],
                "podcasts": state["user_input"],
                "news": state["user_input"]
            }
        })
    except Exception as e:
        print(f"Preference extraction error: {e}")
        kw = state["user_input"]
        preferences = {
            "genres": [], "moods": [], "topics": [],
            "keywords": [kw],
            "search_queries": {k: kw for k in ["videos", "music", "movies", "podcasts", "news"]}
        }

    # Ensure search_queries always exists
    if "search_queries" not in preferences:
        kw = " ".join(preferences.get("keywords", [state["user_input"]]))
        preferences["search_queries"] = {k: kw for k in ["videos", "music", "movies", "podcasts", "news"]}

    state["preferences"] = preferences
    return state


def parallel_search_node(state: FluxState) -> FluxState:
    """Execute parallel searches for each domain."""
    sq = state["preferences"].get("search_queries", {})
    fallback = " ".join(state["preferences"].get("keywords", [state["user_input"]]))

    domain_results = {}
    
    def run_tool(domain, query):
        tools_map = {
            "videos": youtube_search,
            "music": youtube_music_search,
            "podcasts": itunes_podcast_search,
            "movies": tmdb_movie_search,
            "news": google_news_search
        }
        try:
            return tools_map[domain].invoke({"query": query})
        except:
            return []

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        executor_map = {}
        for domain in ["videos", "music", "podcasts", "movies", "news"]:
            query_val = sq.get(domain, "").strip() or fallback
            
            if domain in ["music", "movies"] and "," in query_val:
                titles = [t.strip() for t in query_val.split(",") if t.strip()][:6]
                for title in titles:
                    f = executor.submit(run_tool, domain, title)
                    executor_map[f] = domain
            else:
                f = executor.submit(run_tool, domain, query_val)
                executor_map[f] = domain

        for domain in ["videos", "music", "podcasts", "movies", "news"]:
            domain_results[domain] = []

        for future in concurrent.futures.as_completed(executor_map):
            dom = executor_map[future]
            res = future.result()
            if res:
                if dom in ["music", "movies"] and len(res) > 0:
                    domain_results[dom].append(res[0])
                else:
                    domain_results[dom].extend(res)

    for dom in domain_results:
        domain_results[dom] = domain_results[dom][:6]

    state["domain_results"] = domain_results
    return state


def cross_domain_synthesis_node(state: FluxState) -> FluxState:
    """LLM synthesizes insight, scores domains, and suggests a follow-up question."""
    prompt = CROSS_DOMAIN_SYNTHESIS_PROMPT.format(
        preferences=json.dumps(state["preferences"]),
        videos=json.dumps(state["domain_results"].get("videos", [])[:2]),
        music=json.dumps(state["domain_results"].get("music", [])[:2]),
        movies=json.dumps(state["domain_results"].get("movies", [])[:2]),
        podcasts=json.dumps(state["domain_results"].get("podcasts", [])[:2]),
        news=json.dumps(state["domain_results"].get("news", [])[:2])
    )

    default_scores = {k: 7 for k in ["videos", "music", "movies", "podcasts", "news"]}

    try:
        if not os.getenv("GROQ_API_KEY") and not os.getenv("OPENROUTER_API_KEY"):
            raise ValueError("No API keys available")

        llm = get_llm()
        response = llm.invoke([
            SystemMessage(content="You are a recommendation synthesizer. Return only valid JSON."),
            HumanMessage(content=prompt)
        ])
        parsed = _parse_json_safe(response.content, {
            "insight": "Your recommendations span multiple domains.",
            "domain_scores": default_scores,
            "follow_up_question": "Would you like to refine any of these recommendations?"
        })
        state["cross_domain_insight"] = parsed.get("insight", "Your recommendations span multiple domains.")
        state["domain_scores"] = parsed.get("domain_scores", default_scores)
        state["follow_up_question"] = parsed.get("follow_up_question", "")
    except Exception as e:
        print(f"Synthesis error: {e}")
        state["cross_domain_insight"] = "Your recommendations span multiple domains."
        state["domain_scores"] = default_scores
        state["follow_up_question"] = ""

    return state


def format_output_node(state: FluxState) -> FluxState:
    """Format final output for Streamlit UI."""
    output = {
        "preferences": state["preferences"],
        "insight": state["cross_domain_insight"],
        "domain_scores": state.get("domain_scores", {}),
        "follow_up_question": state.get("follow_up_question", ""),
        "results": {
            "videos":   state["domain_results"].get("videos", []),
            "music":    state["domain_results"].get("music", []),
            "movies":   state["domain_results"].get("movies", []),
            "podcasts": state["domain_results"].get("podcasts", []),
            "news":     state["domain_results"].get("news", [])
        }
    }
    state["final_output"] = json.dumps(output, indent=2)
    return state


def build_graph():
    """Build and compile the LangGraph StateGraph."""
    graph = StateGraph(FluxState)
    graph.add_node("extract_preferences", extract_preferences_node)
    graph.add_node("parallel_search", parallel_search_node)
    graph.add_node("cross_domain_synthesis", cross_domain_synthesis_node)
    graph.add_node("format_output", format_output_node)

    graph.add_edge(START, "extract_preferences")
    graph.add_edge("extract_preferences", "parallel_search")
    graph.add_edge("parallel_search", "cross_domain_synthesis")
    graph.add_edge("cross_domain_synthesis", "format_output")
    graph.add_edge("format_output", END)

    return graph.compile()


flux_graph = build_graph()
