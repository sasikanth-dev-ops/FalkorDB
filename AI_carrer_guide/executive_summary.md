# AI Career Mentor
## A persistent AI co-pilot for student career growth

**AI Career Mentor helps students turn career uncertainty into clear, personalized next steps.** It remembers a student's evolving skills, goals, and projects, connects that profile to relevant opportunities, and explains what to do next to become a stronger candidate.

### The problem

Students face a fragmented path from learning to opportunity. Hackathons, internships, open-source programs, and learning resources are scattered across platforms. At the same time, a student's skills, projects, interests, and goals are spread across resumes, notes, and conversations. Generic search and one-off AI advice rarely account for this full context, so students can miss relevant opportunities or struggle to decide which skills to build next.

### The solution

AI Career Mentor acts as a career co-pilot with persistent, graph-based memory. A student can describe their experience and ambitions in natural conversation. The system extracts useful facts, stores them as connected student, skill, goal, project, and opportunity data, and uses that context to:

- find and rank relevant opportunities;
- show matching skills and missing prerequisites;
- explain why an opportunity fits the student;
- recommend a practical learning roadmap toward a chosen goal; and
- remember progress between conversations.

### What makes it different

The system combines **persistent agent memory and knowledge-graph reasoning** rather than relying only on a prompt or a flat list. A graph represents how a student's skills relate to projects, goals, and opportunity requirements. Graph queries support structured checks and skill-gap analysis; bounded prerequisite paths expose how an existing skill can prepare the student for a missing opportunity requirement. Those paths are used to order roadmap steps and shown as evidence, while inferred prerequisites are kept distinct from skills the student actually owns. Opportunity text ranking currently uses token overlap; embedding-based retrieval is planned, not implemented.

The experience also makes this reasoning visible. Students can inspect the profile facts used by the mentor, explore their connected skill and project graph, and see the basis for recommendations. This is intended to make the system more understandable and useful—not just more conversational.

### How it works

1. The student shares skills, goals, and project experience through chat or profile setup.
2. The memory workflow extracts structured facts and updates the student's graph.
3. Opportunity data is collected from supported sources and normalized into a common format.
4. The matcher checks explicit skill requirements in FalkorDB; bounded prerequisite paths explain indirect learning routes, and token overlap ranks free-text searches.
5. The student receives ranked opportunities, match explanations, identified gaps, and suggested next steps.
6. As the student reports new learning or project progress, the memory and recommendations can evolve.

### Hackathon demonstration

In a short end-to-end demo, a student says they are building with Python and FastAPI and want to join an AI hackathon. The mentor records those skills and that goal, searches the available opportunity data, shows a matching event with its requirements, identifies missing skills, and proposes a focused roadmap. The memory view makes the update visible, demonstrating the journey from conversation to persistent memory to actionable recommendation.

### Technology and intended impact

The current stack includes FastAPI, Streamlit, FalkorDB with its official Python client, LangGraph, and Google Gemini. ChromaDB and embedding-based retrieval are not implemented. The architecture separates the user interface, API, agent workflow, graph memory, and opportunity ingestion so each part can be developed and evaluated independently.

The goal is to help students—especially those without easy access to individualized career guidance—make better-informed decisions about what to pursue and how to prepare. The project will evaluate memory retention, opportunity-match quality, skill-gap accuracy, and roadmap usefulness; these are evaluation goals, not claimed results.
