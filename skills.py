from council.skills import SkillBase
from council.contexts import ChatMessage, ChainContext, SkillContext
from council.runners import Budget
from council.llm import LLMBase, LLMMessage
from council.skills.google.google_context import GoogleSearchEngine, GoogleNewsSearchEngine

from string import Template


class OutlineWriterSkill(SkillBase):
    """Write or revise the outline of an article."""

    def __init__(self, llm: LLMBase):
        """Build a new OutlineWriterSkill."""

        super().__init__(name="OutlineWriterSkill")

        self.llm = llm

        self.system_prompt = "You are an expert research writer and editor. Your role is to create and refine the outlines of research articles in markdown format."

        self.main_prompt_template = Template("""
        # Task Description
        Your task is to write or revise the outline of a research article.
        First consider the CONVERSATION HISTORY and ARTICLE OUTLINE.
        Then consider the INSTRUCTIONS and write a NEW OR IMPROVED OUTLINE for the article.
        Always write the outline in markdown using appropriate section headers.
        Make sure that every section has at least three relevant subsections.
       The NEW OR IMPROVED OUTLINE must only include section or subsection headers.
                                             
        ## BEGIN EXAMPLE ##

        ## CONVERSATION HISTORY
        ['ChatMessageKind.User: Write a detailed research article about the history of video games.']

        ## ARTICLE OUTLINE

        ## INSTRUCTIONS
        Create an outline for the research article about the history of video games. The outline should include sections such as Introduction, Early History, Evolution of Video Games, Impact on Society, and Conclusion.

        ## NEW OR IMPROVED OUTLINE
        ```markdown          
        # Introduction
        ## Brief overview of the topic
        ## Importance of studying the history of video games
        ## Scope of the research

        # Early History of Video Games
        ## Pre-digital era games
        ## Inception of digital video games
        ## Key pioneers and their contributions

        # Evolution of Video Games
        ## Transition from arcade to home consoles
        ## Impact of technological advancements on game development
        ## Emergence of different gaming genres

        # Impact on Society
        ## Influence on popular culture
        ## Economic impact
        ## Psychological effects of video gaming

        # Conclusion
        ## Recap of the evolution and impact of video games
        ## Current trends and future prospects
        ## Final thoughts and reflections
        ```
        
        ## END EXAMPLE ##

        ## CONVERSATION HISTORY
        $conversation_history

        ## ARTICLE OUTLINE
        $article_outline

        ## INSTRUCTIONS
        $instructions

        ## NEW OR IMPROVED OUTLINE
        ```markdown
        """)

    def execute(self, context: ChainContext, _budget: Budget) -> ChatMessage:
        """Execute `OutlineWriterSkill`."""

        # Get the chat message history
        chat_message_history = [
            f"{m.kind}: {m.message}" for m in context.messages
        ]

        # Get the article
        article = context.last_message.data['article']

        # Get the outline
        outline = context.last_message.data['outline']

        # Get the iteration
        iteration = context.last_message.data['iteration']

        # Get the instructions
        instructions = context.last_message.message
        
        main_prompt = self.main_prompt_template.substitute(
            conversation_history=chat_message_history,
            article=article,
            article_outline=outline,
            instructions=instructions
        )

        messages_to_llm = [
            LLMMessage.system_message(self.system_prompt),
            LLMMessage.assistant_message(
                main_prompt
            ),
        ]

        llm_response = self.llm.post_chat_request(messages=messages_to_llm, temperature=0.1)[0]

        return ChatMessage.skill(
            source=self.name,
            message="I've edited the outline and placed the response in the 'data' field.",
            data={'outline': llm_response, 'instructions': instructions, 'iteration': iteration},
        )
    

class SectionWriterSkill(SkillBase):
    """Write a specific section of an article."""

    def __init__(self, llm: LLMBase):
        """Build a new SectionWriterSkill."""

        super().__init__(name="SectionWriterSkill")
        self.llm = llm

        self.system_prompt = "You are an expert research writer and editor. Your role is to write or revise detailed sections of research articles in markdown format."

        self.main_prompt_template = Template("""
        # Task Description
        Your task is to write specific sections of research articles using your own knowledge.
        First consider the CONVERSATION HISTORY, ARTICLE OUTLINE, ARTICLE, and INSTRUCTIONS.
        Then revise the article according to the context and INSTRUCTIONS provided below.
        All headings, sections, and subsections must consist of at least three detailed paragraphs each.
        The entire REVISED ARTICLE should be written using markdown formatting. 

        ## CONVERSATION HISTORY
        $conversation_history

        ## ARTICLE OUTLINE
        $outline

        ## ARTICLE
        $article

        ## INSTRUCTIONS
        $instructions

        ## REVISED ARTICLE
        ```markdown
        """)

    def execute(self, context: ChainContext, _budget: Budget) -> ChatMessage:
        """Execute `SectionWriterSkill`."""

        # Get the chat message history
        conversation_history = [
            f"{m.kind}: {m.message}" for m in context.messages
        ]

        # Get the article
        article = context.last_message.data['article']
        
        # Get the outline
        outline = context.last_message.data['outline']

        # Get the iteration
        iteration = context.last_message.data['iteration']
       
        # Get the instructions
        instructions = context.last_message.message
        
        main_prompt = self.main_prompt_template.substitute(
            conversation_history=conversation_history,
            outline=outline,
            article=article,
            instructions=instructions
        )

        messages_to_llm = [
            LLMMessage.system_message(self.system_prompt),
            LLMMessage.assistant_message(
                main_prompt
            ),
        ]

        llm_response = self.llm.post_chat_request(messages=messages_to_llm, temperature=0.1)[0]

        return ChatMessage.skill(
            source=self.name,
            message="I've written or edited the article and placed it in the 'data' field.",
            data={'article': llm_response, 'instructions': instructions, 'iteration': iteration},
        )


class GoogleSearchContextBuilderSkill(SkillBase):
    """Build context from Google Search results.""" 

    def __init__(self):
        """Build a new GoogleSearchContextBuilderSkill."""
        super().__init__(name="GoogleSearchContextBuilderSkill")
        self.gs = GoogleSearchEngine.from_env()

    def execute(self, context: SkillContext, budget: Budget) -> ChatMessage:
        """Execute `GoogleSearchContextBuilderSkill`."""

        # Get the iteration
        iteration = context.last_message.data['iteration']

        # Get the instructions
        instructions = context.last_message.message

        # Run Google Search
        search_results = self.gs.execute(query=instructions, nb_results=10)
        response_count = len(search_results)
        
        # Build the context
        context = ""
        if response_count > 0:
            for result in search_results:
                r = result.dict()
                date = r.get("date", "")
                if date is None:
                    date = ""
                text = "Date: " + date + "\n" + "Content: " + "\n" + r.get("title", "") +  " " + r.get("snippet", "") + "\n\n"
                context += text

        return ChatMessage.skill(
            source=self.name,
            message=f"{self.name} {response_count} responses for {instructions}",
            data={'context': context, 'instructions': instructions, 'iteration': iteration},
        )


class GoogleNewsContextBuilderSkill(SkillBase):
    """Build context from Google News results.""" 

    def __init__(self):
        """Build a new GoogleNewsContextBuilderSkill."""
        super().__init__(name="GoogleNewsContextBuilderSkill")
        self.gn = GoogleNewsSearchEngine(period="90d", suffix="")

    def execute(self, context: SkillContext, budget: Budget) -> ChatMessage:
        """Execute `GoogleNewsContextBuilderSkill`."""

        # Get the iteration
        iteration = context.last_message.data['iteration']

        # Get the instructions
        instructions = context.last_message.message

        # Run Google News
        search_results = self.gn.execute(query=instructions, nb_results=10)
        response_count = len(search_results)

        # Build the context
        context = ""
        if response_count > 0:
            for result in search_results:
                r = result.dict()
                date = r.get("date", "")
                if date is None:
                    date = ""
                text = "Date: " + date + "\n" + "Content: " + "\n" + r.get("title", "") +  " " + r.get("snippet", "") + "\n\n"
                context += text

        return ChatMessage.skill(
            source=self.name,
            message=f"{self.name} {response_count} responses for {instructions}",
            data={'context': context, 'instructions': instructions, 'iteration': iteration},
        )
