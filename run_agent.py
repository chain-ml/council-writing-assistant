import itertools
import threading
import time

class Spinner:
    def __init__(self, message="Working..."):
        self.spinner_cycle = itertools.cycle(['-', '/', '|', '\\'])
        self.running = False
        self.spinner_thread = threading.Thread(target=self.init_spinner, args=(message,))

    def start(self):
        self.running = True
        self.spinner_thread.start()

    def stop(self):
        self.running = False
        self.spinner_thread.join()

    def init_spinner(self, message):
        while self.running:
            print(f'\r{message} {next(self.spinner_cycle)}', end='', flush=True)
            time.sleep(0.1)
        # clear spinner from console
        print('\r', end='', flush=True)

import logging

logging.basicConfig(
    format="[%(name)s:%(funcName)s:] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S%z",
)
logging.getLogger("council").setLevel(logging.INFO)

from council.runners import Budget
from council.contexts import AgentContext, ChatHistory
from council.agents import Agent
from council.chains import Chain
from council.llm.openai_llm_configuration import OpenAILLMConfiguration
from council.llm.openai_llm import OpenAILLM

from skills import SectionWriterSkill, OutlineWriterSkill, GoogleSearchContextBuilderSkill, GoogleNewsContextBuilderSkill
from controller import WritingAssistantController
from evaluator import BasicEvaluatorWithSource

import dotenv
dotenv.load_dotenv()
openai_llm = OpenAILLM(config=OpenAILLMConfiguration.from_env())

# Create Skills

outline_skill = OutlineWriterSkill(openai_llm)
writing_skill = SectionWriterSkill(openai_llm)
google_search_context_builder_skill = GoogleSearchContextBuilderSkill()
google_news_context_builder_skill = GoogleNewsContextBuilderSkill()

# Create Chains

outline_chain = Chain(
    name="Outline Writer",
    description="Write or revise the outline (i.e. section headers) of a research article in markdown format. Always give this Chain the highest score when there should be structural changes to the article (e.g. new sections)",
    runners=[outline_skill]
)

writer_chain = Chain(
    name="Article Writer",
    description="Write or revise specific section bodies of a research article in markdown format. Use this chain to write the main research article content.",
    runners=[writing_skill]
)

gsearch_chain = Chain(
    name="Google Search",
    description="Google Search is a web search engine. Use this chain when your own knowledge is not sufficient for the article, including when you need information from after your training cutoff date.",
    runners=[google_search_context_builder_skill]
)

gnews_chain = Chain(
    name="Google News",
    description="Google News is a platform aggregating timely news articles from global sources. Use this chain when your own knowledge is not sufficient for the article, including when you need information from after your training cutoff date.",
    runners=[google_news_context_builder_skill]
)

# Create Controller

controller = WritingAssistantController(
    openai_llm,
    top_k_execution_plan=5
)

# Initialize Agent

chat_history = ChatHistory()
run_context = AgentContext(chat_history)
agent = Agent(controller, [outline_chain, writer_chain, gsearch_chain, gnews_chain], BasicEvaluatorWithSource())

def main():
    print("Write a message to the ResearchWritingAssistant or type 'quit' to exit.")

    while True:
        user_input = input("\nYour message (e.g. Tell me about the history of box manufacturing.): ")
        if user_input.lower() == 'quit':
            break
        else:
            if user_input == '':
                user_input = "Tell me about the history of box manufacturing."

            s = Spinner()
            s.start()
            chat_history.add_user_message(user_input)
            result = agent.execute(run_context, Budget(900))
            s.stop()
            print(f"\n```markdown\n{result.messages[-1].message.message}\n```\n")

    print("Goodbye!")

if __name__ == "__main__":
    main()