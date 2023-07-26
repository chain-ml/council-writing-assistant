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

Now we're ready to interact with our Agent.

### First Interaction

```python
# Run Agent

chat_history.add_user_message("Write a detailed research article about the history of video games.")
result = agent.execute(run_context, Budget(1200))
```

Here are the logs:
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

And let's get the outputs:

```python
print(result.messages[-1].message.message)
```

```markdown
# The History of Video Games: A Detailed Exploration

## Introduction

The history of video games is a fascinating journey that spans over half a century, from the rudimentary games of the 1950s to the immersive and complex digital worlds of today. This article will delve into the evolution of video games, tracing their origins, the technological advancements that have shaped them, and the cultural impact they have had over the years. We will explore the key milestones in the development of video games, the influential figures who have driven this industry forward, and the trends that have defined each era. Whether you are a seasoned gamer or simply interested in the intersection of technology and culture, this exploration of video game history promises to be an enlightening read.

## The Early Days: 1950s - 1970s

The history of video games began in the 1950s when scientists started to design simple games and simulations as part of their computer science research. The first video game, "Tennis for Two," was created in 1958 by physicist William Higinbotham. It was a simple tennis game, similar to the classic 1970s video game Pong, and it was quite a hit at a Brookhaven National Laboratory open house.

The 1970s marked a significant era in the history of video games with the birth of arcade games. The first commercially successful video game, Pong, was released by Atari in 1972. Pong was a simple tennis game that became a huge hit, sparking the beginning of the video game industry. This success led to the proliferation of arcade games, with titles like Space Invaders (1978) and Pac-Man (1980) becoming cultural phenomena. These games not only dominated arcades but also entered homes with the advent of home consoles.

The late 1970s also saw the advent of home consoles, a significant milestone in the video game industry. The Magnavox Odyssey, released in 1972, was the first home video game console. However, it was the Atari 2600, released in 1977, that popularized home video gaming. The Atari 2600 offered interchangeable game cartridges, a feature that allowed players to switch games at their leisure. This marked the beginning of the home console era, setting the stage for future consoles like the Nintendo Entertainment System and the Sega Genesis.

## The Golden Age: 1980s - 1990s

The 1980s and 1990s are often referred to as the "golden age" of video games. This era saw the release of iconic games like Super Mario Bros., The Legend of Zelda, and Sonic the Hedgehog. These games introduced characters that are still beloved today and set the standard for future video games.

The 1990s also saw the rise of 3D graphics in video games. Games like Doom and Quake were pioneers in this field, offering players a new level of immersion and realism. The transition from 2D to 3D gaming was a significant milestone in the evolution of video games, providing a more immersive and realistic gaming experience.

## The Modern Era: 2000s - Present

The 2000s brought about a revolution in video game technology with the introduction of online gaming. Games like World of Warcraft and Call of Duty allowed players to connect and play with others around the world, creating a global gaming community. This era also saw the rise of multiplayer gaming, where players could compete or cooperate with each other, adding a new dimension to the gaming experience.

The advent of smartphones and tablets in the late 2000s led to the emergence of mobile gaming. Games like Angry Birds and Candy Crush became immensely popular, and the convenience of playing games on handheld devices opened up gaming to a wider audience. Mobile gaming has since become a significant segment of the video game industry, with its easy accessibility and wide range of games appealing to both casual and hardcore gamers.

The most recent development in the evolution of video games is the advent of virtual and augmented reality games. These technologies provide an even more immersive gaming experience, allowing players to interact with the game environment in new and exciting ways. Games like Pokemon Go, which uses augmented reality to overlay game elements onto the real world, and Oculus Rift, a virtual reality gaming platform, are at the forefront of this new gaming revolution.

## Impact on Society

The video game industry has had a profound impact on society in various ways. Economically, it has grown into a multi-billion dollar industry, providing employment opportunities and contributing significantly to global economies. In 2020, the global video games market was valued at approximately 159.3 billion U.S. dollars.

Video games have also permeated popular culture, influencing music, film, and fashion. Characters and narratives from games have become part of our collective cultural consciousness, and esports events draw audiences comparable to traditional sports.

In the realm of education and skill development, video games have been recognized for their potential to enhance cognitive skills such as problem-solving, strategic thinking, and hand-eye coordination. They are increasingly being used in educational settings, from elementary schools to universities, for teaching a variety of subjects.

However, the impact of video games on society is not without controversy. Criticisms include the portrayal of violence, the potential for addiction, and the risk of social isolation. Despite these concerns, research on these topics is ongoing and often inconclusive, and many argue that the benefits of gaming outweigh the potential negatives.

## Conclusion

From the simple games of the 1950s to the immersive digital worlds of today, the history of video games is a testament to the power of innovation and creativity. As we look to the future, it's exciting to imagine what the next chapter in this dynamic industry will bring.
```

### Second Interaction

```python
chat_history.add_user_message("Can you please add more details in each section?")
result = agent.execute(run_context, Budget(600))
```

Logs

```
[2023-07-26 13:00:49-0400 INFO MainThread council.agents.agent:execute:60] message="agent execution started"
[2023-07-26 13:00:49-0400 INFO MainThread council.agents.agent:execute:62] message="agent iteration started" iteration="3"
[2023-07-26 13:01:07-0400 INFO MainThread council.agents.agent:execute:71] message="chain execution started" chain="Article Writer" execution_unit="Article Writer: In the "Early History of Video Games" section, add more information about the first video games, the birth of arcade games, and the advent of home consoles."
[2023-07-26 13:01:07-0400 INFO chain_Article Writer_0 council.skills.skill_base:execute_skill:82] message="skill execution started" skill="SectionWriterSkill"
[2023-07-26 13:02:47-0400 INFO chain_Article Writer_0 council.skills.skill_base:execute_skill:85] message="skill execution ended" skill="SectionWriterSkill" skill_message="I've written or edited the article and placed it in the 'data' field."
[2023-07-26 13:02:47-0400 INFO MainThread council.agents.agent:execute:76] message="chain execution ended" chain="Article Writer" execution_unit="Article Writer: In the "Early History of Video Games" section, add more information about the first video games, the birth of arcade games, and the advent of home consoles."
[2023-07-26 13:02:47-0400 INFO MainThread council.agents.agent:execute:71] message="chain execution started" chain="Article Writer" execution_unit="Article Writer: In the "Evolution of Video Games" section, provide more details about the transition from 2D to 3D gaming, the rise of online and multiplayer gaming, the emergence of mobile gaming, and the advent of virtual and augmented reality games."
[2023-07-26 13:02:47-0400 INFO chain_Article Writer_0 council.skills.skill_base:execute_skill:82] message="skill execution started" skill="SectionWriterSkill"
[2023-07-26 13:04:27-0400 INFO chain_Article Writer_0 council.skills.skill_base:execute_skill:85] message="skill execution ended" skill="SectionWriterSkill" skill_message="I've written or edited the article and placed it in the 'data' field."
[2023-07-26 13:04:27-0400 INFO MainThread council.agents.agent:execute:76] message="chain execution ended" chain="Article Writer" execution_unit="Article Writer: In the "Evolution of Video Games" section, provide more details about the transition from 2D to 3D gaming, the rise of online and multiplayer gaming, the emergence of mobile gaming, and the advent of virtual and augmented reality games."
[2023-07-26 13:04:27-0400 INFO MainThread council.agents.agent:execute:71] message="chain execution started" chain="Article Writer" execution_unit="Article Writer: Please add more details to the "Introduction" section, specifically about the importance of understanding the history of video games."
[2023-07-26 13:04:27-0400 INFO chain_Article Writer_0 council.skills.skill_base:execute_skill:82] message="skill execution started" skill="SectionWriterSkill"
[2023-07-26 13:06:29-0400 INFO chain_Article Writer_0 council.skills.skill_base:execute_skill:85] message="skill execution ended" skill="SectionWriterSkill" skill_message="I've written or edited the article and placed it in the 'data' field."
[2023-07-26 13:06:29-0400 INFO MainThread council.agents.agent:execute:76] message="chain execution ended" chain="Article Writer" execution_unit="Article Writer: Please add more details to the "Introduction" section, specifically about the importance of understanding the history of video games."
[2023-07-26 13:08:26-0400 INFO MainThread council.agents.agent:execute:88] message="agent execution ended"
```

Output

```python
print(result.messages[-1].message.message)
```

```
# The History of Video Games: A Detailed Exploration

## Introduction

The history of video games is a fascinating journey that spans over half a century, from the rudimentary games of the 1950s to the immersive and complex digital worlds of today. This article will delve into the evolution of video games, tracing their origins, the technological advancements that have shaped them, and the cultural impact they have had over the years. Understanding the history of video games is crucial for several reasons. Firstly, it provides insight into the technological advancements that have occurred over the years. From simple 2D graphics to complex 3D environments, from standalone games to massively multiplayer online games, the progression of video game technology mirrors the broader advancements in computing and digital technology. 

Secondly, the history of video games offers a unique perspective on cultural trends and shifts. Video games, like any form of media, reflect and shape the society in which they are created. They are influenced by, and in turn influence, popular culture, societal norms, and global events. 

Lastly, studying the history of video games allows us to appreciate the creativity and innovation of game developers. The evolution of video games is a testament to human ingenuity, with each new generation of games pushing the boundaries of what is possible. 

## The Early Days: 1950s - 1970s

The history of video games began in the 1950s when scientists started to design simple games and simulations as part of their computer science research. The first video game, "Tennis for Two," was created in 1958 by physicist William Higinbotham. It was a simple tennis game, similar to the classic 1970s video game Pong, and it was quite a hit at a Brookhaven National Laboratory open house. This game was played on an oscilloscope, a piece of electronic test equipment, and was a far cry from the sophisticated games we see today.

The 1970s marked a significant era in the history of video games with the birth of arcade games. The first commercially successful video game, Pong, was released by Atari in 1972. Pong was a simple tennis game that became a huge hit, sparking the beginning of the video game industry. This success led to the proliferation of arcade games, with titles like Space Invaders (1978) and Pac-Man (1980) becoming cultural phenomena. These games not only dominated arcades but also entered homes with the advent of home consoles. The popularity of these games led to the establishment of gaming as a mainstream hobby and the arcade as a major social venue for teenagers.

The late 1970s also saw the advent of home consoles, a significant milestone in the video game industry. The Magnavox Odyssey, released in 1972, was the first home video game console. However, it was the Atari 2600, released in 1977, that popularized home video gaming. The Atari 2600 offered interchangeable game cartridges, a feature that allowed players to switch games at their leisure. This marked the beginning of the home console era, setting the stage for future consoles like the Nintendo Entertainment System and the Sega Genesis. The introduction of home consoles brought about a shift in the gaming landscape, making video games accessible to a wider audience and allowing gamers to enjoy their favorite games in the comfort of their own homes.

## The Golden Age: 1980s - 1990s

The 1980s and 1990s are often referred to as the "golden age" of video games. This era saw the release of iconic games like Super Mario Bros., The Legend of Zelda, and Sonic the Hedgehog. These games introduced characters that are still beloved today and set the standard for future video games.

The 1990s also saw the rise of 3D graphics in video games. Games like Doom and Quake were pioneers in this field, offering players a new level of immersion and realism. The transition from 2D to 3D gaming was a significant milestone in the evolution of video games. It allowed for the creation of more complex and realistic environments, characters, and gameplay mechanics. This shift also led to the development of new genres, such as first-person shooters and real-time strategy games, which took full advantage of the possibilities offered by 3D graphics.

## The Modern Era: 2000s - Present

The 2000s brought about a revolution in video game technology with the introduction of online gaming. Games like World of Warcraft and Call of Duty allowed players to connect and play with others around the world, creating a global gaming community. This era also saw the rise of multiplayer gaming, where players could compete or cooperate with each other, adding a new dimension to the gaming experience. Multiplayer gaming not only fostered social interaction but also led to the emergence of competitive gaming or esports, which has since become a significant aspect of the gaming culture.

The advent of smartphones and tablets in the late 2000s led to the emergence of mobile gaming. Games like Angry Birds and Candy Crush became immensely popular, and the convenience of playing games on handheld devices opened up gaming to a wider audience. Mobile gaming has since become a significant segment of the video game industry, with its easy accessibility and wide range of games appealing to both casual and hardcore gamers. The rise of mobile gaming also led to the development of new monetization models, such as freemium and in-app purchases, which have significantly influenced the economics of the gaming industry.

The most recent development in the evolution of video games is the advent of virtual and augmented reality games. These technologies provide an even more immersive gaming experience, allowing players to interact with the game environment in new and exciting ways. Games like Pokemon Go, which uses augmented reality to overlay game elements onto the real world, and Oculus Rift, a virtual reality gaming platform, are at the forefront of this new gaming revolution. These technologies are not only changing the way we play games but also have potential applications in fields like education, training, and therapy.

## Impact on Society

The video game industry has had a profound impact on society in various ways. Economically, it has grown into a multi-billion dollar industry, providing employment opportunities and contributing significantly to global economies. In 2020, the global video games market was valued at approximately 159.3 billion U.S. dollars.

Video games have also permeated popular culture, influencing music, film, and fashion. Characters and narratives from games have become part of our collective cultural consciousness, and esports events draw audiences comparable to traditional sports.

In the realm of education and skill development, video games have been recognized for their potential to enhance cognitive skills such as problem-solving, strategic thinking, and hand-eye coordination. They are increasingly being used in educational settings, from elementary schools to universities, for teaching a variety of subjects.

However, the impact of video games on society is not without controversy. Criticisms include the portrayal of violence, the potential for addiction, and the risk of social isolation. Despite these concerns, research on these topics is ongoing and often inconclusive, and many argue that the benefits of gaming outweigh the potential negatives.

## Conclusion

From the simple games of the 1950s to the immersive digital worlds of today, the history of video games is a testament to the power of innovation and creativity. As we look to the future, it's exciting to imagine what the next chapter in this dynamic industry will bring.
```

## Remarks

After a second iteration, the Article is expanded. Feel free to keep exploring this example in the notebook [run_agent.ipynb](../run_agent.ipynb)