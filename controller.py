from council.contexts import AgentContext, ScoredChatMessage, ChatMessage, ChatMessageKind
from council.chains import Chain
from council.llm import LLMMessage, LLMBase
from council.utils import Option
from council.runners import Budget
from council.controllers import ControllerBase, ExecutionUnit

import logging
from string import Template
from typing import List, Tuple

logger = logging.getLogger("council")

class WritingAssistantController(ControllerBase):
    """
    A controller that uses an LLM to decide the execution plan
    """

    _llm: LLMBase

    def __init__(
        self,
        llm: LLMBase,
        response_threshold: float = 0,
        top_k_execution_plan: int = 5,
    ):
        """
        Initialize a new instance

        Parameters:
            llm (LLMBase): the instance of LLM to use
            response_threshold (float): a minimum threshold to select a response from its score
            top_k_execution_plan (int): maximum number of execution plan returned
        """
        self._llm = llm
        self._response_threshold = response_threshold
        self._top_k = top_k_execution_plan

        # Controller state variables 
        self._article = ""
        self._outline = ""
        self._iteration = 0

    def get_plan(
        self, context: AgentContext, chains: List[Chain], budget: Budget
    ) -> List[ExecutionUnit]:
        
        """
        Planning phase.
        """

        system_prompt = "You are the Controller module for an AI assistant built to write and revise research articles."

        main_prompt_template = Template("""
        # Task Description
        Your task is to decide how best to write or revise the ARTICLE. Considering the ARTICLE OUTLINE, ARTICLE, and the CONVERSATION HISTORY,
        use your avaiable CHAINS to decide what steps to take next. You are not responsible for writing any sections,
        you are only responsible for deciding what to do next. You will delegate work to other agents via CHAINS.

        # Instructions

        You may delegate work to one or more CHAINS.
        Consider the name and description of each chain and decide whether or how you want to use it. 
        Only give instructions to relevant chains.
        You can decide to invoke the same chain multiple times, with different instructions. 
        Provide chain instructions that are relevant towards completing your TASK.
        You will also give each chain invocation a score out of 10, so that their execution can be prioritized.

        ## CHAINS (provided as a list of chain names and descriptions)
        $chains

        ## CONVERSATION HISTORY
        $conversation_history

        ## ARTCILE OUTLINE
        $outline

        ## ARTICLE
        $article

        # Contoller Decision formatted precisely as: {chain name};{score out of 10};{instructions on a single line}
        """)

        # Increment iteration
        self._iteration += 1

        # Get the Chain details
        chain_details = "\n ".join(
            [f"name: {c.name}, description: {c.description}" for c in chains]
        )

        # Get the conversation history
        conversation_history = [f"{m.kind}: {m.message}" for m in context.chatHistory.messages]

        messages = [
            LLMMessage.system_message(system_prompt),
            LLMMessage.user_message(
                main_prompt_template.substitute(
                    chains=chain_details,
                    outline=self._outline,
                    article=self._article,
                    conversation_history=conversation_history,
                )
            ),
        ]

        response = self._llm.post_chat_request(messages)[0]
        logger.debug(f"controller get_plan response: {response}")

        parsed = response.splitlines()
        parsed = [p for p in parsed if len(p) > 0]
        parsed = [self.parse_line(line, chains) for line in parsed]

        filtered = [
            r.unwrap()
            for r in parsed
            if r.is_some() and r.unwrap()[1] > self._response_threshold
        ]
        if (filtered is None) or (len(filtered) == 0):
            return []

        filtered.sort(key=lambda item: item[1], reverse=True)

        result = []
        print("CONTROLLER")
        for chain, score, instruction in filtered: 
            initial_state = ChatMessage.chain(
                message=instruction, data={"article": self._article, "outline": self._outline, "iteration": self._iteration}
            )
            print(f"{chain.name};{score};{instruction}")
            exec_unit = ExecutionUnit(
                chain,
                budget,
                initial_state=initial_state,
                name=f"{chain.name}: {instruction}"
            )
            result.append(exec_unit)

        result = result[: self._top_k]
        return result

    @staticmethod
    def parse_line(line: str, chains: List[Chain]) -> Option[Tuple[Chain, int, str]]:
        result: Option[Tuple[Chain, int]] = Option.none()
        try:
            (name, score, instruction) = line.split(";")[:3]
            chain = next(filter(lambda item: item.name == name, chains))
            result = Option.some((chain, int(score), instruction))
        except Exception as e:
            print(e)
            logger.error(f"Controller parsing error: {e}.\n{line}")
        finally:
            return result
        
    def select_responses(self, context: AgentContext) -> List[ScoredChatMessage]:

        """
        Aggregation phase. 

        Get latest iteration results from Evaluator and aggregate if applicable.
        """

        all_eval_results = sorted(context.evaluationHistory[-1], key=lambda x: x.score, reverse=True)
        current_iteration_results = []
        for scored_result in all_eval_results:
            message = scored_result.message
            if message.data['iteration'] == self._iteration:
                current_iteration_results.append(message)

        ## If multiple outlines or articles were generated in the last iteration, 
        ## use LLM calls to aggregate them.

        outlines = []
        articles = []
        conversation_history = [f"{m.kind}: {m.message}" for m in context.chatHistory.messages]

        for message in current_iteration_results:
            source = message.source
            if source == "SectionWriterSkill":
                articles.append(message.data['article'])
            elif source == "OutlineWriterSkill":
                outlines.append(message.data['outline'])

        ### Outline Aggregation

        system_prompt = "You are an expert-level AI writing editor. Your role is to aggregate multiple suggestions for an article outline into a single one."
        main_prompt_template = Template("""
        # Task Description
        Your task is to combine one or more article outlines into a single one written in markdown format.

        # Instructions
        Read the CHAT HISTORY, EXISTING OUTLINE, and POSSIBLE OUTLINES. Then respond with a single article outline that best matches what is being requested in the CHAT HISTORY.

        ## CONVERSATION HISTORY
        $conversation_history

        ## EXISTING OUTLINE
        $existing_outline

        ## POSSIBLE OUTLINES
        $possible_outlines

        ## OUTLINE
        ```markdown
        """)

        if len(outlines) > 0:
            messages = [
                LLMMessage.system_message(system_prompt),
                LLMMessage.user_message(
                    main_prompt_template.substitute(
                        conversation_history=conversation_history,
                        existing_outline=self._outline,
                        possible_outlines=outlines
                    )
                ),
            ]
            response = self._llm.post_chat_request(messages)[0]
            self._outline = response

        ### Article Aggregation

        system_prompt = "You are an expert-level AI writing editor. Your role is to aggregate multiple partial articles into a single, complete article."
        main_prompt_template = Template("""
        # Task Description
        Your task is to combine one or more partial articles into a single one written in markdown format.

        # Instructions
        Read the CHAT HISTORY, EXISTING ARTICLE, and PARTIAL ARTICLES. Then respond with a single article that best matches what is being requested in the CHAT HISTORY.

        ## CONVERSATION HISTORY
        $conversation_history

        ## EXISTING ARTICLE
        $existing_article
                                        
        ## PARTIAL ARTICLES
        $partial_articles

        ## ARTICLE
        ```markdown
        """)

        if len(articles) > 0:
            messages = [
                LLMMessage.system_message(system_prompt),
                LLMMessage.user_message(
                    main_prompt_template.substitute(
                        conversation_history=conversation_history,
                        existing_article=self._article,
                        partial_articles = articles
                    )
                ),
            ]
            response = self._llm.post_chat_request(messages)[0]
            self._article = response

        ### Decide whether to keep iterating or to return the article
        ### to the user for review.

        system_prompt = "You are an expert-level AI writing editor. Your role is to decide whether to keep editing the ARTICLE."
        main_prompt_template = Template("""
        # Task Description
        Your task is to decide whether:
        1. To keep editing the ARTICLE, or
        2. To return the article to the requesting agent.

        # Instructions
        Read the ARTICLE and CHAT HISTORY then consider the following instructions:
        - If the ARTICLE still has placeholders or empty sections, KEEP EDITING.
        - If the ARTICLE is incoherent, KEEP EDITING.
        - If the ARTICLE does not include everything being requested in the CHAT HISTORY, KEEP EDITING.
        - If the ARTICLE does not include every section in ARTICLE OUTLINE, KEEP EDITING.
        - The ARTICLE is only COMPLETE when it covers every section and subsection in the ARTICLE OUTLINE.
        - If the ARTICLE is COMPLETE, RETURN TO REQUESTING AGENT.

        ## ARTCILE OUTLINE
        $outline

        ## ARTICLE
        $article

        ## CONVERSATION HISTORY
        $conversation_history

        # Your Response (exactly one of ["KEEP EDITING", "RETURN TO REQUESTING AGENT"])
        """)

        messages = [
            LLMMessage.system_message(system_prompt),
            LLMMessage.user_message(
                main_prompt_template.substitute(
                    article=self._article,
                    outline=self._outline,
                    conversation_history=conversation_history,
                )
            ),
        ]

        response = self._llm.post_chat_request(messages)[0]
        logger.debug(f"outline: {self._outline}")
        print("OUTLINE")
        print(self._outline)
        logger.debug(f"article: {self._article}")
        print("ARTICLE")
        print(self._article)
        logger.debug(f"controller editing decision: {response}")

        if "KEEP EDITING" in response:
            return []
        else:
            return [ScoredChatMessage(ChatMessage(message=self._article, kind=ChatMessageKind.Agent), 1.0)]

   
