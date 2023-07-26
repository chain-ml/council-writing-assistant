# WritingAssistantAgent Implementation

Now that we've defined all of the components of our solution, we can combine them into a Council Agent.

## Setup

First, we'll set up logging.

```python
# Set up logging

import logging

logging.basicConfig(
    format="[%(asctime)s %(levelname)s %(threadName)s %(name)s:%(funcName)s:%(lineno)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S%z",
)
logging.getLogger("council").setLevel(logging.INFO)
```

Next, we'll import classes from the Council framework and our custom components.

```python
# Council imports

from council.runners import Budget
from council.contexts import AgentContext, ChatHistory
from council.agents import Agent
from council.chains import Chain
from council.llm.openai_llm_configuration import OpenAILLMConfiguration
from council.llm.openai_llm import OpenAILLM

from skills import SectionWriterSkill, OutlineWriterSkill
from controller import WritingAssistantController
from evaluator import BasicEvaluatorWithSource
```

Next, we'll create an LLM instance.

```python
# Read environment variables and initialize OpenAI LLM instance

import dotenv
dotenv.load_dotenv()
openai_llm = OpenAILLM(config=OpenAILLMConfiguration.from_env())
```

## Initializing Agent Components

First, we'll create Skills.

```python
# Create Skills

outline_skill = OutlineWriterSkill(openai_llm)
writing_skill = SectionWriterSkill(openai_llm)
```

Next, we'll create simple Chains to wrap those skills.

```python
# Create Chains

outline_chain = Chain(
    name="Outline Writer",
    description="Write or revise the outline (i.e. section headers) of a research article in markdown format. Only use this chain when the ARTICLE OUTLINE is missing or incomplete.",
    runners=[outline_skill]
)

writer_chain = Chain(
    name="Article Writer",
    description="Write or revise specific section bodies of a research article in markdown format. Use this chain to write the main research article content.",
    runners=[writing_skill]
)
```

And now the Controller.

```python
# Create Controller

controller = WritingAssistantController(
    openai_llm,
    top_k_execution_plan=3
)
```

And finally the Agent.

```python
# Initialize Agent

chat_history = ChatHistory()
run_context = AgentContext(chat_history)
agent = Agent(controller, [outline_chain, writer_chain], BasicEvaluatorWithSource())
```

## Running the Agent

```python
# Run Agent

chat_history.add_user_message("Write a detailed research article about the history of video games.")
result = agent.execute(run_context, Budget(1200))
```

```
[2023-07-26 12:54:30-0400 INFO MainThread council.agents.agent:execute:60] message="agent execution started"
[2023-07-26 12:54:30-0400 INFO MainThread council.agents.agent:execute:62] message="agent iteration started" iteration="1"
[2023-07-26 12:54:36-0400 INFO MainThread council.agents.agent:execute:71] message="chain execution started" chain="Outline Writer" execution_unit="Outline Writer: Create an outline for the research article about the history of video games. The outline should include sections such as Introduction, Early History, Evolution of Video Games, Impact on Society, and Conclusion."
[2023-07-26 12:54:36-0400 INFO chain_Outline Writer_0 council.skills.skill_base:execute_skill:82] message="skill execution started" skill="OutlineWriterSkill"
[2023-07-26 12:54:49-0400 INFO chain_Outline Writer_0 council.skills.skill_base:execute_skill:85] message="skill execution ended" skill="OutlineWriterSkill" skill_message="I've edited the outline and placed the response in the 'data' field."
[2023-07-26 12:54:49-0400 INFO MainThread council.agents.agent:execute:76] message="chain execution ended" chain="Outline Writer" execution_unit="Outline Writer: Create an outline for the research article about the history of video games. The outline should include sections such as Introduction, Early History, Evolution of Video Games, Impact on Society, and Conclusion."
[2023-07-26 12:54:49-0400 INFO MainThread council.agents.agent:execute:71] message="chain execution started" chain="Article Writer" execution_unit="Article Writer: Once the outline is ready, start writing the Introduction section, providing a brief overview of the topic and what the article will cover."
[2023-07-26 12:54:49-0400 INFO chain_Article Writer_0 council.skills.skill_base:execute_skill:82] message="skill execution started" skill="SectionWriterSkill"
[2023-07-26 12:55:00-0400 INFO chain_Article Writer_0 council.skills.skill_base:execute_skill:85] message="skill execution ended" skill="SectionWriterSkill" skill_message="I've written or edited the article and placed it in the 'data' field."
[2023-07-26 12:55:00-0400 INFO MainThread council.agents.agent:execute:76] message="chain execution ended" chain="Article Writer" execution_unit="Article Writer: Once the outline is ready, start writing the Introduction section, providing a brief overview of the topic and what the article will cover."
[2023-07-26 12:56:02-0400 INFO MainThread council.agents.agent:execute:62] message="agent iteration started" iteration="2"
[2023-07-26 12:56:17-0400 INFO MainThread council.agents.agent:execute:71] message="chain execution started" chain="Article Writer" execution_unit="Article Writer: Expand the 'Evolution of Video Games' section to include more information about the transition from 2D to 3D gaming, the rise of online and multiplayer gaming, the emergence of mobile gaming, and the advent of virtual and augmented reality games."
[2023-07-26 12:56:17-0400 INFO chain_Article Writer_0 council.skills.skill_base:execute_skill:82] message="skill execution started" skill="SectionWriterSkill"
[2023-07-26 12:57:17-0400 INFO chain_Article Writer_0 council.skills.skill_base:execute_skill:85] message="skill execution ended" skill="SectionWriterSkill" skill_message="I've written or edited the article and placed it in the 'data' field."
[2023-07-26 12:57:17-0400 INFO MainThread council.agents.agent:execute:76] message="chain execution ended" chain="Article Writer" execution_unit="Article Writer: Expand the 'Evolution of Video Games' section to include more information about the transition from 2D to 3D gaming, the rise of online and multiplayer gaming, the emergence of mobile gaming, and the advent of virtual and augmented reality games."
[2023-07-26 12:57:17-0400 INFO MainThread council.agents.agent:execute:71] message="chain execution started" chain="Article Writer" execution_unit="Article Writer: Revise the 'Early History of Video Games' section to include more details about the birth of arcade games and the advent of home consoles."
[2023-07-26 12:57:17-0400 INFO chain_Article Writer_0 council.skills.skill_base:execute_skill:82] message="skill execution started" skill="SectionWriterSkill"
[2023-07-26 12:58:15-0400 INFO chain_Article Writer_0 council.skills.skill_base:execute_skill:85] message="skill execution ended" skill="SectionWriterSkill" skill_message="I've written or edited the article and placed it in the 'data' field."
[2023-07-26 12:58:15-0400 INFO MainThread council.agents.agent:execute:76] message="chain execution ended" chain="Article Writer" execution_unit="Article Writer: Revise the 'Early History of Video Games' section to include more details about the birth of arcade games and the advent of home consoles."
[2023-07-26 12:58:15-0400 INFO MainThread council.agents.agent:execute:71] message="chain execution started" chain="Article Writer" execution_unit="Article Writer: Add more depth to the 'Impact on Society' section by discussing the economic impact of the video game industry, the influence of video games on popular culture, the role of video games in education and skill development, and controversies and criticisms such as violence, addiction, and social isolation."
[2023-07-26 12:58:15-0400 INFO chain_Article Writer_0 council.skills.skill_base:execute_skill:82] message="skill execution started" skill="SectionWriterSkill"
[2023-07-26 12:59:18-0400 INFO chain_Article Writer_0 council.skills.skill_base:execute_skill:85] message="skill execution ended" skill="SectionWriterSkill" skill_message="I've written or edited the article and placed it in the 'data' field."
[2023-07-26 12:59:18-0400 INFO MainThread council.agents.agent:execute:76] message="chain execution ended" chain="Article Writer" execution_unit="Article Writer: Add more depth to the 'Impact on Society' section by discussing the economic impact of the video game industry, the influence of video games on popular culture, the role of video games in education and skill development, and controversies and criticisms such as violence, addiction, and social isolation."
[2023-07-26 13:00:49-0400 INFO MainThread council.agents.agent:execute:88] message="agent execution ended"
```

