import logging

logging.basicConfig(
    format="[%(asctime)s %(levelname)s %(threadName)s %(name)s:%(funcName)s:%(lineno)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S%z",
)
logging.getLogger("council").setLevel(logging.DEBUG)

from council.runners import Budget
from council.contexts import AgentContext, ChatHistory
from council.agents import Agent
from council.chains import Chain
from council.llm.openai_llm_configuration import OpenAILLMConfiguration
from council.llm.openai_llm import OpenAILLM

from skills import SectionWriterSkill, OutlineWriterSkill
from controller import WritingAssistantController
from evaluator import BasicEvaluatorWithSource

import dotenv
dotenv.load_dotenv()
openai_llm = OpenAILLM(config=OpenAILLMConfiguration.from_env())

# Create Skills

outline_skill = OutlineWriterSkill(openai_llm)
writing_skill = SectionWriterSkill(openai_llm)

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

# Create Controller

controller = WritingAssistantController(
    openai_llm,
    top_k_execution_plan=1
)

# Initialize Agent

chat_history = ChatHistory()
run_context = AgentContext(chat_history)
agent = Agent(controller, [outline_chain, writer_chain], BasicEvaluatorWithSource())

# Run Agent

chat_history.add_user_message("What is the financial performance of Microsoft?")
result = agent.execute(run_context, Budget(900))
print(result.messages[-1].message.message)