from council.skills import SkillBase
from council.contexts import ChatMessage, ChainContext
from council.runners import Budget
from council.llm import LLMBase, LLMMessage

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
        First consider the CONVERSATION HISTORY, ARTICLE OUTLINE, and COMMENTS.
        Then consider the INSTRUCTIONS and write a NEW OR IMPROVED OUTLINE for the article.
        Always write the outline in markdown using appropriate section headers.

        ## CONVERSATION HISTORY
        $conversation_history

        ## ARTICLE OUTLINE
        $article_outline

        ## INSTRUCTIONS
        $instructions

        ## NEW OR IMPROVED OUTLINE
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

        llm_response = self.llm.post_chat_request(messages=messages_to_llm)[0]

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
        Your task is to write specific sections of research articles using your own knowledge 
        or using information available using various sources. 
        First consider the CONVERSATION HISTORY, ARTICLE OUTLINE, ARTICLE, COMMENTS, and INSTRUCTIONS.
        Then revise the article according to the context and instructions provided below. 
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
            revision_instructions=instructions
        )

        messages_to_llm = [
            LLMMessage.system_message(self.system_prompt),
            LLMMessage.assistant_message(
                main_prompt
            ),
        ]

        llm_response = self.llm.post_chat_request(messages=messages_to_llm)[0]

        return ChatMessage.skill(
            source=self.name,
            message="I've written or edited the article and placed it in the 'data' field.",
            data={'article': llm_response, 'instructions': instructions, 'iteration': iteration},
        )
    