
### What did you learn from implementing a multi-agent workflow?

Implementing a multi-agent workflow taught me the importance of **role separation**, **modular communication**, and **iterative refinement** in AI system design. By clearly dividing responsibilities between a Planner and a Reviewer, I saw how complex tasks like travel planning could be broken down into specialized, manageable subtasks — one focusing on generation and the other on validation. It highlighted how **cooperation between agents can simulate expert workflows**, much like in real-world scenarios where one person drafts a plan and another audits it. I also realized that designing effective system prompts is just as crucial as model selection: clear instructions significantly impact each agent’s performance. Furthermore, orchestrating the agents to operate in sequence helped me understand how to **enforce intermediate checks**, ensuring quality before presenting output to users. Overall, this experience deepened my understanding of how **multi-agent systems can increase robustness, accuracy, and user trust** in LLM-based applications.

&nbsp;

### Challenges faced and how you addressed them

One of the main challenges I faced was designing **prompts that were specific enough to guide agent behavior** without making them overly rigid. Initially, the Planner Agent produced vague or overly ambitious itineraries that didn’t account for logistical realities like transit time or budget constraints. To address this, I restructured the Planner prompt with **explicit formatting rules** and **concrete examples**, emphasizing realistic pacing, activity durations, and cost estimates. Another challenge was ensuring the Reviewer Agent **used the `internet_search` tool meaningfully** rather than repeating the Planner’s content or glossing over potential errors. I had to carefully engineer the Reviewer prompt to encourage tool usage for validation, not just summarization, and included a detailed checklist and a structured Delta List format.

&nbsp;

### Any creative ideas, variations, or design choices

I explored several creative design choices to make the Planner–Reviewer workflow more robust and user-friendly. Prompt-wise, I treated both agents as domain experts with distinct personalities: the Planner acts like a knowledgeable concierge, while the Reviewer plays the role of a skeptical auditor. I gave the Reviewer a structured “Delta List” output format inspired by professional document review processes, which makes the corrections easy to trace and understand. Finally, I added clear formatting rules (Markdown sections, budget breakdowns, etc.) to ensure the output was both informative and scannable. These design choices aimed to make the app feel collaborative, trustworthy, and practical for real use.

&nbsp;

### Note any external tools or GenAI assistance used and why.

NA