# Skill Implementation: Article Outline Writer

We'll start building our Research Writing Assistant by implementing a Skill to generate article **outlines**. 

By asking an LLM to generate the outline of an article, rather than an article directly, we're really asking it to begin the writing process with a plan

Let's get set up to build a Skill in Council.


```python
from council.skills import SkillBase
from council.contexts import ChatMessage, SkillContext, LLMContext
from council.llm import LLMBase, LLMMessage

from string import Template
```

The first thing we'll do is define **prompts** for this **Skill**.


```python
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
```

There are a couple of things to notice here. First, we're using Python's built-in string **Templates** for main prompts. Templates are perfect for building prompts with substitution variables. These variables will be substituted at execution time using information from the **ChainContext** - structured information that is made available to Chains when they're invoked by a Controller (we will learn more about Controllers later!)

For now, it's just important to see that our intention with this prompt is that we want to generate or edit a research article outline based on:
- conversation history
- an existing / previously generated outline
- other specific instructions
- one in-context example

Next, let's define the **OutlineWriterSkill**.

We'll begin by extending the `SkillBase` class.


```python
class OutlineWriterSkill(SkillBase):
    """Write or revise the outline of an article."""

    def __init__(self, llm: LLMBase):
        """Build a new OutlineWriterSkill."""

        super().__init__(name="OutlineWriterSkill")

        self.llm = self.new_monitor("llm", llm)
        self.system_prompt = "You are an expert..."
        self.main_prompt_template = Template("# Task Description ...")
```

Next, we'll implement the skill's `execute` funciton.


```python
def execute(self, context: SkillContext) -> ChatMessage:
    """Execute `OutlineWriterSkill`."""
```

First, we'll want to read the conversation history from the `context`, since our prompt template is expecting to use it.


```python
chat_message_history = [
    f"{m.kind}: {m.message}" for m in context.messages
]
```

Similarly, we want to get both the instructions and the article outline (if it exists) from the `context`. Unlike the conversation history, which is always managed automatically by Council, the instructions and article outline will be managed by a custom defined **Controller**. When we build our Controller, we will see how to manage state for Chains and Skills such that they can be invoked with data.

Get the instructions. 

This code assumes that the OutlineWriterSkill will be invoked with an `intial_state` where the `message` field is an instruction for the skill, e.g.: "*Update the outline to include a section on environmental policy.*"


```python
instructions = context.last_message.message
```

Get the outline.

This code assumes that the skill will be invoked with an `initial_state` that includes 'outline' as a key in the `data` field. If the outline doesn't already exist, `context.last_message.data['outline']` will return `None`. 


```python
outline = context.last_message.data['outline']
```

Now that we have `conversation_history`, `instructions`, and `outline` populated, we just need to fill in the skill's main prompt template and post a chat request to our LLM instance.


```python
 # Create the main LLM prompt by substituting variables
main_prompt = self.main_prompt_template.substitute(
    conversation_history=chat_message_history,
    article=article,
    article_outline=outline,
    instructions=instructions
)

# Package messages for the LLM call
messages_to_llm = [
    LLMMessage.system_message(self.system_prompt),
    LLMMessage.assistant_message(
        main_prompt
    ),
]

# Send messages to LLM
llm_result = self.llm.inner.post_chat_request(
    context=LLMContext.from_context(context, self.llm),
    messages=messages_to_llm, 
    temperature=0.1
)
llm_response = llm_result.first_choice

# Format the Skill response
return ChatMessage.skill(
    source=self.name,
    message="I've edited the outline and placed the response in the 'data' field.",
    data={'outline': llm_response, 'instructions': instructions},
)
```

Finally, here is the entire OutlineWriterSkill implementation.


```python
class OutlineWriterSkill(SkillBase):
    """Write or revise the outline of an article."""

    def __init__(self, llm: LLMBase):
        """Build a new OutlineWriterSkill."""

        super().__init__(name="OutlineWriterSkill")

        self.llm = self.new_monitor("llm", llm)

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

    def execute(self, context: SkillContext) -> ChatMessage:
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

        llm_result = self.llm.inner.post_chat_request(
            context=LLMContext.from_context(context, self.llm),
            messages=messages_to_llm,
            temperature=0.1
        )

        llm_response = llm_result.first_choice

        return ChatMessage.skill(
            source=self.name,
            message="I've edited the outline and placed the response in the 'data' field.",
            data={'outline': llm_response, 'instructions': instructions, 'iteration': iteration},
        )
```

In the [next part](./3_article_section_writer_skill.md), we will define one more skill: **ArticleSectionWriterSkill**
