# AI Career Mentor — 2-Minute Hackathon Demo

**Purpose:** Show the complete value loop: conversation → persistent memory → opportunity match → actionable next step.

> Replace bracketed stage directions with the real UI and a real opportunity from your demo dataset. Do not describe a feature as live unless it is working in the build you present.

## Timed script

**Suggested demo profile:** `seed-student-005` (Python + Data Analysis, targeting Machine Learning Engineer). In the dashboard profile picker, select this profile to show the graph path from Python to a missing Machine Learning requirement. Refresh WeMakeDevs listings before the demo. Synthetic seed fixtures are hidden by default and must not be presented as real opportunities.

### 0:00–0:18 — The problem
**On screen:** Open the app on its main dashboard or chat view.

**Say:**  
“Students don’t have a shortage of opportunities. They have a context problem. Opportunities are scattered across platforms, while each student’s skills, projects, and goals are scattered across resumes, notes, and conversations. Most tools show a list; they don’t understand the person behind the search.”

### 0:18–0:33 — Introduce the product
**On screen:** Show the chat and briefly point out the memory or graph area.

**Say:**  
“This is AI Career Mentor: a career co-pilot designed to remember a student’s progress and connect it to relevant opportunities. Its key idea is persistent graph memory—not just another one-off chatbot conversation.”

### 0:33–0:55 — Give the mentor context
**On screen:** Enter and send:  
`I use Python and Data Analysis, and I want to prepare for a machine learning research internship. Please build me a roadmap.`

**Say:**  
“I’ll give it a realistic starting point: what I know and the opportunity I want to prepare for. The system should use the profile and graph relationships—not just that message—to work out a useful next step.”

### 0:55–1:15 — Show memory
**On screen:** Show the updated memory inspector or graph. Point out only facts actually captured in the running build.

**Say:**  
“Here, the student’s skills and goal are represented as connected information. For this seeded profile, Python connects to Machine Learning through a prerequisite relationship. That path becomes the first roadmap step, with a learning resource attached.”

### 1:15–1:40 — Show a recommendation and its reasoning
**On screen:** Open opportunity recommendations. Use a verified live listing if one has been ingested. Seed records use `example.org` URLs and are synthetic fixtures, not real opportunities. Show the requirements, direct skill matches, missing skills, and (when FalkorDB returns one) the prerequisite path behind a suggested next step.

**Say:**  
“Now the mentor compares the student's skills with opportunity requirements through FalkorDB. This path—from a skill the student has, through graph prerequisites, to a skill an opportunity requires—explains what to learn next. It is evidence for a learning path, not a claim that the student already has the target skill.”

### 1:40–1:53 — Turn the gap into an action
**On screen:** Show the roadmap or ask for next steps.

**Say:**  
“The result is a practical next step: a focused learning path that connects the student’s current skills to the opportunity they want to pursue.”

### 1:53–2:00 — Close
**On screen:** Leave the recommendation and memory/roadmap visible.

**Say:**  
“AI Career Mentor turns a student’s evolving journey into personalized opportunity discovery and a clear path to readiness. It doesn’t just answer, ‘What can I apply to?’ It helps answer, ‘What should I do next, and why?’”

## Rehearsal checklist

- Use a prepared student profile and a verified, live opportunity record so the demo does not depend on a live scrape. If only seed data is available, clearly call it synthetic.
- Verify the memory update, recommendation, and roadmap before presenting; adapt the narration to what the build actually demonstrates.
- Keep one screen or tab ready for each stage to avoid navigation delays.
- If a step fails, explain the intended stage honestly and continue with a prepared screenshot or seeded result; do not imply that a non-working feature succeeded.
- Rehearse with a timer and trim explanation before cutting the memory-to-recommendation flow.
