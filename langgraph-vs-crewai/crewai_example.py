from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

# 1. Define Specialized Agents
researcher = Agent(
    role="Senior Systems Analyst",
    goal="Uncover high-impact architectural facts about emerging software paradigms",
    backstory="You are a veteran technical analyst specializing in enterprise distributed systems.",
    llm=llm,
    verbose=True
)

editor = Agent(
    role="Principal Technical Editor",
    goal="Condense complex research findings into crisp, actionable executive summaries",
    backstory="You edit high-level engineering publications and demand concise, zero-fluff communication.",
    llm=llm,
    verbose=True
)

# 2. Define Granular Tasks
task1 = Task(
    description="Analyze the architectural benefits of Model Context Protocol for enterprise software.",
    expected_output="Detailed technical findings outlining integration standards and security controls.",
    agent=researcher
)

task2 = Task(
    description="Refine the analyst's findings into three clear, impactful executive takeaways.",
    expected_output="Three concise bullet points formatted for technical decision makers.",
    agent=editor
)

# 3. Assemble and Run the Crew
tech_crew = Crew(
    agents=[researcher, editor],
    tasks=[task1, task2],
    process=Process.sequential,
    verbose=True
)

if __name__ == "__main__":
    result = tech_crew.kickoff()
    print("--- CREWAI FINAL RESULT ---")
    print(result)
