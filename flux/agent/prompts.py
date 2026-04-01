PREFERENCE_EXTRACTION_PROMPT = """You are a preference extraction expert for a cross-domain recommendation system.
Given a user's natural language input (and optional prior conversation context), extract structured preferences.

Prior conversation context (may be empty):
{conversation_memory}

Current user input: {user_input}

Return ONLY a valid JSON object with these keys:
- genres: [list of genres/categories]
- moods: [list of moods/feelings]
- topics: [list of topics/themes]
- keywords: [list of general key search terms]
- search_queries: {{
    "videos": "<optimised YouTube search query>",
    "music": "<comma-separated list of 5 specific song/album titles with artist names>",
    "movies": "<comma-separated list of 5 specific movie titles based on user preferences>",
    "podcasts": "<optimised podcast search query>",
    "news": "<optimised news search query>"
  }}

For 'music' and 'movies', provide 5 specific recommendations as a comma-separated list.
Return only valid JSON, no markdown or extra text."""


CROSS_DOMAIN_SYNTHESIS_PROMPT = """You are a world-class cross-domain recommendation synthesizer.
Given user preferences and results from 5 domains, produce a rich insight and score each domain.

User preferences: {preferences}

Domain results (samples):
- Videos: {videos}
- Music: {music}
- Movies: {movies}
- Podcasts: {podcasts}
- News: {news}

Return a JSON object with these exact keys:
{{
  "insight": "<2-3 sentence insight explaining cross-domain connections, themes, moods, and why these recommendations work together — written warmly and personally>",
  "domain_scores": {{
    "videos": <0-10 relevance score>,
    "music": <0-10 relevance score>,
    "movies": <0-10 relevance score>,
    "podcasts": <0-10 relevance score>,
    "news": <0-10 relevance score>
  }},
  "follow_up_question": "<one short, engaging follow-up question to refine recommendations further — natural and conversational>"
}}

Return only valid JSON."""


FINAL_OUTPUT_PROMPT = """You are a friendly recommendation curator.
Present the user's cross-domain recommendations in a warm, engaging way.

Preferences: {preferences}
Connection insight: {insight}
Results: {results}

Create a natural, conversational summary recommending these items."""
