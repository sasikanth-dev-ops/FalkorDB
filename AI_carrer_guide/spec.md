# Software Design Document (SDD): AI Career Mentor

## 1. Executive Summary
AI Career Mentor is an agentic career intelligence platform designed to help students discover the right opportunities, track their growth, and build a measurable path toward career readiness. The product transforms scattered student data—skills, goals, projects, and completed learning milestones—into a persistent, queryable memory graph that powers AI-guided career advice.

The platform is built for the modern student ecosystem where opportunities are abundant but hard to navigate. Instead of static lists or generic resume advice, AI Career Mentor acts as a personal career co-pilot: it remembers the student over time, matches them to relevant hackathons, internships, open-source programs, and research opportunities, and recommends a personalized roadmap based on their current profile and target role.

This project is designed to stand out in an international hackathon setting by combining:
- persistent agentic memory,
- graph-based reasoning,
- live opportunity discovery,
- AI-driven personalization,
- and an interactive visual dashboard that makes the system understandable and trustworthy.

---

## 2. Problem Statement
Students today struggle with a fragmented career discovery process:
- They discover opportunities through scattered sources like Unstop, WeMakeDevs, GitHub, and newsletters.
- Their skills, goals, and project history are spread across chat messages, resumes, and personal notes.
- They do not have a system that remembers their progress and helps them improve over time.
- Generic advice often fails because it does not reason over the student’s actual trajectory.

As a result, many students miss relevant opportunities due to poor matching, lack of strategy, and limited visibility into their readiness.

The core challenge is not just finding opportunities; it is understanding the student as a dynamic profile and turning that understanding into high-confidence recommendations.

---

## 3. Product Vision
AI Career Mentor aims to become the intelligent memory layer for student career development.

The product envisions a future where every student has an AI mentor that:
- understands their evolving skill profile,
- remembers their goals and completed work,
- tracks missing competencies,
- matches them to the most relevant opportunities,
- and creates actionable roadmaps to close skill gaps.

This is not a traditional recommendation engine. It is a persistent, graph-aware, agentic assistant that reasons over personal context and external opportunity data to deliver highly relevant guidance.

---

## 4. Target Users
### 4.1 Primary Users
- Students in engineering, product, AI, blockchain, web development, and related fields
- Early-stage developers preparing for internships, hackathons, and open-source work
- Students with strong motivation but limited visibility into what they should pursue next

### 4.2 Secondary Users
- Career coaches or mentors
- Hackathon communities and student communities
- Clubs and developer groups looking to guide members effectively

### 4.3 Core User Needs
- Discover opportunities aligned with their current profile
- Get personalized guidance based on skills and learning goals
- Understand why they are a match or a mismatch for a program
- Track learning progress across time and sessions
- See a visual map of their skills, goals, and next actions

---

## 5. Business and Hackathon Relevance
This project maps strongly to the Agent Memory & Coordination and Agents That Act on Connected Data themes.

Why it matters at international scale:
- It solves a real-world problem affecting millions of students globally.
- It demonstrates practical use of graph memory, agent orchestration, and hybrid retrieval.
- It brings together data collection, memory extraction, reasoning, and user-facing intelligence in one cohesive system.
- It is a strong demo because it shows a clear before/after story: the AI understands a student, learns from their interaction history, and recommends meaningful next steps.

This is the kind of system judges can immediately grasp:
“Your AI remembers the student, understands their journey, and helps them navigate career opportunities more effectively than a static search engine.”

---

## 6. Core Product Experience
### 6.1 User Flow
1. A student signs in and initializes their profile.
2. They chat naturally with the AI mentor about their skills, interests, projects, and career aspirations.
3. The system extracts structured facts from the conversation.
4. The graph memory updates with new skills, goals, project information, and learning milestones.
5. The student asks for opportunities or roadmaps.
6. The AI searches live opportunity data and matches them against the student graph.
7. The system returns:
   - a ranked list of opportunities,
   - match percentages,
   - missing prerequisites,
   - suggested resources,
   - and a tailored study roadmap.
8. The student can review memory and graphs visually to understand why they were recommended.

### 6.2 Example Interaction
User: “I am building projects in FastAPI and Python and want to participate in AI hackathons.”

AI system:
- stores Python and FastAPI as skill nodes,
- identifies AI hackathon interest as a goal,
- looks for matching events with AI/ML/Backend requirements,
- finds missing skills such as LangChain or vector databases,
- suggests a personalized roadmap and relevant opportunities.

---

## 7. System Architecture
### 7.1 High-Level Components
- Frontend (Streamlit): Chat interface, memory panel, opportunity explorer, graph visualizer
- Backend API (FastAPI): Auth, profile management, chat endpoints, graph retrieval endpoints
- Agent Orchestration Layer (LangChain / LangGraph): Planner, memory extractor, evaluator, roadmap generator
- Graph Memory Layer (FalkorDB): Persistent knowledge graph for student, skill, goal, project, and opportunity data
- Vector Retrieval Layer (ChromaDB): Semantic matching over description text and contextual embeddings
- Scraping Layer: Web scrapers that fetch live opportunities from sources such as Unstop, WeMakeDevs, GitHub, and other relevant platforms
- Job Queue Layer (Celery + Redis): Background scraping, indexing, and refresh jobs

### 7.2 Architectural Principle
The system is designed around a memory-first architecture. The AI does not operate on one-off prompt context alone; it continuously updates a structured memory graph that captures the student’s progression in a durable form.

This architectural pattern allows the system to provide:
- long-term continuity,
- explainable recommendations,
- multi-hop reasoning,
- and stronger personalization than prompt-only LLM systems.

---

## 8. Technology Stack
### 8.1 Frontend
- Streamlit
- Pyvis
- Plotly
- Custom CSS / dashboard components

### 8.2 Backend
- FastAPI
- Pydantic v2
- Uvicorn
- Python-dotenv
- JWT authentication support

### 8.3 AI and Agent Layer
- LangChain
- LangGraph
- Google Gemini (gemini-2.5-flash or equivalent)

### 8.4 Memory and Retrieval
- FalkorDB graph database (local Docker service) with the official Python `falkordb` client
- OpenCypher
- ChromaDB

### 8.5 Data Collection and Background Jobs
- BeautifulSoup4
- Celery
- Redis
- Requests

### 8.6 Deployment and DevOps
- Docker / Docker Compose
- .env configuration
- Python 3.11+

---

## 9. Data Model
### 9.1 Core Entities
#### Student
- id
- name
- branch
- year
- target_role
- current_goals

#### Skill
- id
- name
- category

#### Goal
- id
- description
- target_date

#### Project
- id
- title
- repo_url
- tech_stack
- description

#### Opportunity / Event
- id
- title
- type
- platform
- deadline
- url
- category

#### Course
- id
- title
- provider
- duration_hours
- url

### 9.2 Relationship Types
- (:Student)-[:HAS_SKILL]->(:Skill)
- (:Student)-[:HAS_GOAL]->(:Goal)
- (:Student)-[:BUILDING_PROJECT]->(:Project)
- (:Event)-[:REQUIRES_SKILL]->(:Skill)
- (:Course)-[:TEACHES_SKILL]->(:Skill)
- (:Skill)-[:PREREQUISITE_FOR]->(:Skill)
- (:Student)-[:LIKES_EVENT]->(:Event)

### 9.3 Graph Memory Benefits
This model enables:
- rich relationships between student state and external opportunities,
- skill gap detection,
- path analysis between current skills and future goals,
- explainable, graph-native recommendations.

---

## 10. Agentic Workflow
The AI layer operates as a coordination system rather than a single monolithic prompt.

### 10.1 Planner Agent
Responsible for understanding the user request and decomposing it into actionable tasks such as:
- update memory,
- score opportunity match,
- generate a roadmap,
- or retrieve graph context.

### 10.2 Memory Extractor Agent
Reads user conversation and extracts:
- new skills,
- changed goals,
- project experience,
- roles of interest,
- learning milestones.

These are expressed as graph mutation operations and written to the knowledge graph.

### 10.3 Readiness Evaluator Agent
Computes student-to-opportunity compatibility by evaluating:
- skill overlap,
- missing prerequisites,
- event difficulty,
- time-to-deadline,
- and similarity with previously successful project patterns.

### 10.4 Roadmap Generator Agent
Uses the gap between current student state and target opportunity to generate a step-by-step skill progression plan.

### 10.5 Audit Logger
Captures token usage, tool calls, graph operations, and latency to ensure traceability and future evaluation.

---

## 11. Hybrid GraphRAG Retrieval
To provide accurate recommendations, the system combines two retrieval strategies.

### 11.1 Structured Retrieval: Graph Traversal
Graph queries answer structured questions such as:
- “Which opportunities require Python and React?”
- “What skills are missing for a given hackathon?”
- “What is the shortest learning path from my current skills to my goal?”

### 11.2 Unstructured Retrieval: Vector Search
Vector search handles semantic questions such as:
- “Find hackathons similar to the ones I liked before.”
- “What opportunities are best for someone interested in AI and systems design?”

### 11.3 Combined Result
The final recommendation engine blends:
- graph constraints,
- vector semantic similarity,
- and personalized historical memory,

to deliver better, more grounded results than either method alone.

---

## 12. Cypher Query Patterns
### Pattern A: Memory Update
```cypher
MATCH (s:Student {id: $student_id})
MERGE (sk:Skill {name: $skill_name})
ON CREATE SET sk.category = $category
MERGE (s)-[r:HAS_SKILL]->(sk)
SET r.proficiency = $proficiency, r.updated_at = timestamp()
RETURN s, r, sk;
```

### Pattern B: Opportunity Match
```cypher
MATCH (s:Student {id: $student_id})
MATCH (e:Event)
MATCH (e)-[r:REQUIRES_SKILL]->(req_skill:Skill)
OPTIONAL MATCH (s)-[h:HAS_SKILL]->(req_skill)
WITH e,
     count(req_skill) AS total_required,
     count(h) AS matched_skills,
     collect(CASE WHEN h IS NULL THEN req_skill.name END) AS missing_skills
RETURN e.id AS event_id,
       e.title AS event_title,
       total_required,
       matched_skills,
       missing_skills,
       (toFloat(matched_skills) / total_required) * 100 AS match_percentage
ORDER BY match_percentage DESC;
```

### Pattern C: Student Memory Retrieval
```cypher
MATCH (s:Student {id: $student_id})
OPTIONAL MATCH (s)-[r1:HAS_SKILL]->(sk:Skill)
OPTIONAL MATCH (s)-[r2:HAS_GOAL]->(g:Goal)
OPTIONAL MATCH (s)-[:BUILDING_PROJECT]->(p:Project)
RETURN s.name AS student_name,
       collect(DISTINCT {skill: sk.name, level: r1.proficiency}) AS skills,
       collect(DISTINCT {goal: g.description, target: g.target_date}) AS goals,
       collect(DISTINCT {project: p.title, tech: p.tech_stack}) AS projects;
```

---

## 13. Frontend Experience
### 13.1 Chat Workspace
The primary user interaction surface is a chat panel where the student can naturally converse with the AI mentor.

### 13.2 Live Memory Inspector
This panel shows:
- current skills,
- goals,
- recent graph mutations,
- activity history,
- and last few Cypher operations.

### 13.3 Graph Visualizer
The graph view renders the student network as a connected graph showing relationships among:
- student,
- skills,
- projects,
- goals,
- and opportunity nodes.

### 13.4 Opportunity Dashboard
Displays:
- opportunity cards,
- deadlines,
- match scores,
- required skills,
- and recommended learning resources.

---

## 14. API Design
### Implemented API surface
- GET /health
- GET /api/v1/health
- GET /api/v1/student/{student_id}
- POST /api/v1/student/profile
- GET /api/v1/opportunities
- GET /api/v1/graph/state/{student_id}
- POST /api/v1/chat/message
- POST /api/v1/opportunities/scrape
- GET /api/v1/roadmap?student_id={student_id}

The chat workflow uses a LangGraph pipeline for structured memory extraction, graph persistence, opportunity matching, roadmap generation, and a grounded response. It requires `GEMINI_API_KEY`. The opportunity endpoint supports optional student matching and filters. The student profile write endpoint upserts basic profile fields and the supplied skills and goals.

The scrape endpoint reads source URLs from configuration, accepts JSON feeds or schema.org Event JSON-LD, normalizes and upserts opportunities, and links required skills. It does not accept user-provided URLs, restricts source hosts, requires HTTPS, and rejects redirects.

### Planned API surface
- POST /api/v1/auth/register
- POST /api/v1/auth/login
- GET /api/v1/student/me
- GET /api/v1/roadmap

Authentication and integrations verified against the live source sites are not implemented yet. The dedicated roadmap endpoint returns steps for the highest-ranked opportunity for the requested student. Controllers should remain thin; business logic belongs in the agent, scraper, and database layers.

---

## 15. Scraping and Data Ingestion Strategy
The system ingests opportunities from multiple sources and normalizes them into one unified opportunity graph.

### Current implementation
- Source URLs are configured through `UNSTOP_SCRAPE_URL`, `WEMAKEDEVS_SCRAPE_URL`, and `GITHUB_BOUNTIES_SCRAPE_URL`.
- The adapter accepts recognized JSON feed arrays and schema.org Event JSON-LD.
- Records receive stable IDs from platform and canonical URL and are merged into `Event` nodes.
- Required skills are merged into `Skill` nodes and linked via `REQUIRES_SKILL`.
- Only HTTPS URLs on the expected source domains are accepted; redirects are rejected.
- Live page/API compatibility has not yet been verified; dynamic pages without supported structured data fail explicitly.

### Supported Sources
- Unstop
- WeMakeDevs
- GitHub-related events and bounties
- Open-source and student-focused program listings

### Normalization Layer
Every scraper outputs a structured JSON payload that is normalized into the shared event schema, ensuring compatibility with the graph database and recommendation engine.

### Why This Matters
The AI only works effectively when it is grounded in fresh, relevant opportunity data. Continuous ingestion creates a live system rather than a static demo.

---

## 16. Personalized Roadmap Generation
One of the strongest differentiators of the product is the ability to convert opportunity gaps into actionable learning plans.

Example output:
- Current state: Python + FastAPI + beginner ML
- Target: AI hackathon / GenAI project challenge
- Missing skills: LangChain, vector DB, prompt engineering, model evaluation
- Roadmap:
  1. Learn LangChain fundamentals
  2. Build a basic RAG project
  3. Practice prompt evaluation
  4. Build a final portfolio project
  5. Apply to relevant hackathons

This creates value beyond opportunity matching: the product helps students act on clear next steps.

---

## 17. Implementation Phases
### Phase 1: Foundation and Graph Setup
Deliverables:
- environment configuration,
- graph schema and bootstrap script,
- initial graph seed data,
- database indexes and connection management

Validation:
- run database setup successfully,
- verify graph initialization and compatibility with Cypher queries

### Phase 2: Backend API and Domain Models
Deliverables:
- FastAPI app,
- student schemas,
- opportunity DTOs,
- auth and chat endpoints,
- graph state API

Validation:
- Swagger UI loads at /docs,
- core endpoints return stable responses

### Phase 3: Agentic Memory and Orchestration
Deliverables:
- planner,
- memory extractor,
- readiness evaluator,
- roadmap generator,
- audit logger

Validation:
- user chat updates memory graph,
- skill extraction from natural conversation works reliably,
- match scores behave as expected

Implementation status: the first chat workflow is implemented at `POST /api/v1/chat/message`. It uses Gemini structured output to extract explicit student facts, LangGraph to coordinate memory persistence, optional opportunity retrieval, roadmap generation, and response composition. A Gemini API key and a running FalkorDB instance are required for end-to-end execution; unit tests use controlled fakes and do not replace a live provider/database check.

### Phase 4: Hybrid GraphRAG and Scraping
Deliverables:
- ChromaDB integration,
- graph traversal retriever,
- multi-source scraping pipeline,
- normalized opportunity mapping

Validation:
- combined vector + graph retrieval returns useful contextual results

### Phase 5: Frontend Dashboard
Deliverables:
- Streamlit chat frontend,
- memory panel,
- graph visualizer,
- opportunity recommendations UI

Validation:
- end-to-end interaction works from chat to graph update to recommendation

### Phase 6: Evaluation and Submission Polish
Deliverables:
- benchmark suite,
- performance evaluation,
- final README,
- architecture explanation,
- demo flow refinement

Validation:
- retention, recommendation quality, and GraphRAG performance are measured and documented

---

## 18. Evaluation Strategy
To make the project feel credible and robust, we define measurable evaluation criteria.

### 18.1 Memory Retention
Measure whether the system retains student knowledge across sessions and chat turns.

Example metric:
- Student says they learned Python and FastAPI.
- After a later session, the system correctly retrieves those skills and uses them for recommendations.

### 18.2 Opportunity Match Quality
Measure how relevant the recommended opportunities are to the student profile.

Example metric:
- percent of recommended opportunities aligned with skill and role interest,
- number of missing prerequisite skills correctly identified.

### 18.3 Graph Retrieval Accuracy
Compare graph-based retrieval to pure vector retrieval or baseline recommendation methods.

### 18.4 Roadmap Utility
Evaluate whether the suggested roadmap is actionable and appropriate for the student’s current state.

---

## 19. Risks and Mitigations
### Risk: Weak or noisy memory extraction
Mitigation: use clear schema definitions and controlled extraction prompts with graph-safe updates.

### Risk: Incomplete or inconsistent opportunity data
Mitigation: normalize every source through a shared schema and validate required fields.

### Risk: Recommendation overfitting
Mitigation: combine graph constraints with semantic retrieval and user feedback loops.

### Risk: Unclear demo story for judges
Mitigation: design UI and narrative around a crisp end-to-end workflow: chat → memory → recommendation → roadmap.

---

## 20. Why This Project Stands Out
AI Career Mentor is stronger than a simple AI assistant because it is designed around persistent memory and reasoning over relationships.

It moves beyond generic “best opportunities” suggestions toward a truly personalized system that can say:
- what the student knows,
- what they are aiming for,
- what they still need,
- what is relevant now,
- and how to get there.

That makes the project valuable not just as a product demo, but as a real-world career intelligence system.
---

## 21. Final Product Positioning Statement
AI Career Mentor is an agentic career guidance platform that turns a student’s growth journey into a memory graph and turns that graph into personalized opportunity matching, skill-gap analysis, and roadmap generation.

It helps students move from uncertainty to clarity by giving them a persistent AI mentor that learns, adapts, and recommends intelligently over time.

---

## 22. Submission Summary
This project is positioned as a practical, innovative, and globally relevant AI product that combines:
- agentic architecture,
- graph database memory,
- live opportunity discovery,
- semantic retrieval,
- personalized learning guidance,
- and visual explainability.

It is designed to impress at an international hackathon by showing not just AI capability, but AI that understands context, remembers the user, and drives meaningful action.
