# FLUX Design & Architecture

Building a cross-domain recommendation engine was about solving three main problems: speed, reliability, and "vibe" consistency. We didn't want a generic search app; we wanted a curated experience that feels like a premium editorial product.

## 1. The Strategy: Brainstorm then Fetch
Instead of a simple "search for X", FLUX uses an LLM to brainstorm 5-6 highly relevant titles (movies, songs, etc.) based on the user's mood. We then fetch metadata for these specific titles in parallel. This ensures that the results are always high-quality and directly relevant, rather than just returning whatever a search engine thinks is popular.

## 2. Robustness & Zero-Failure Lookups
API keys are fragile. We built a multi-layered lookup system to ensure the UI never shows an empty state:
- **Movies/Music:** We fall back from official APIs to broad iTunes metadata and then to YouTube video thumbnails (trailers). Using YouTube as a fallback for movie posters is our "secret sauce" for 100% visual density.
- **News:** We use a custom RSS parser for Google Newsheadlines, completely bypassing the need for scraping libraries that get blocked easily.

## 3. Parallel Execution (LangGraph)
We used LangGraph to manage the state and tool execution. Since we need to query 5 different domains (Video, Music, Movies, Podcasts, News), we used a `ThreadPoolExecutor` to run all 5 searches simultaneously. This dropped our response time from ~5 seconds to under 1 second.

## 4. Engineering the UI
Streamlit's default look didn't fit the "Vogue/Premium" aesthetic we wanted. We bypassed the limitations by:
- Injecting raw CSS to hide Streamlit headers/footers.
- Using serif typography (Playfair Display) for an editorial feel.
- Writing custom HTML templates for the recommendation cards instead of using standard table/list widgets.

## TL;DR
FLUX is a parallelized recommendation agent that uses AI brainstorming for curation and a robust, multi-layer fallback system to ensure it never fails, regardless of API status.
