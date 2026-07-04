# ChronoResearch — Project Context

## What We Are Building
ChronoResearch is a Streamlit web app where users upload research 
papers (PDFs) and the app builds a living knowledge graph using 
Cognee memory. Users can then ask natural language questions that 
are answered by searching across ALL papers simultaneously — 
finding connections, contradictions, and concept evolution across 
papers and time.

## Hackathon Context
- Hackathon: WeMakeDevs "The Hangover Part AI" 
- Dates: June 29 – July 5, 2026
- Prize target: Grand Prize 2 — Best Use of Cognee Cloud (iPhone 17)
- Side prize target: Best Blog (Keychron keyboard)
- Judging criteria: Impact, Creativity, Technical Excellence, 
  Best Use of Cognee, UX, Presentation Quality

## The Core Idea
"Papers That Talk To Each Other"
- Upload 5-6 AI research papers (PDFs)
- Cognee builds a knowledge graph connecting concepts across papers
- Ask: "How did attention mechanisms evolve across these papers?"
- Get answers that span multiple papers with graph traversal

## All 4 Cognee APIs Must Be Used
- remember() → ingest PDF text into knowledge graph
- recall() → query across all papers with hybrid search
- improve() → enrich graph after feedback
- forget() → remove a paper from memory cleanly
