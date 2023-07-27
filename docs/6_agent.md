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

chat_history.add_user_message("Write a detailed research article about the history of box manufacturing.")
result = agent.execute(run_context, Budget(1800))
```

And let's get the outputs:

```python
print(result.messages[-1].message.message)
```

```markdown
# Introduction

The history of box manufacturing is a captivating exploration that traces the evolution of a simple yet indispensable item in our daily lives. The box, in its various forms and materials, has been a fundamental component of commerce, storage, and transportation for centuries. This article aims to delve into the rich history of box manufacturing, exploring its origins, development, and the technological advancements that have shaped it over time.

The significance of box manufacturing cannot be overstated. Boxes are ubiquitous, serving a myriad of purposes in different sectors. From packaging consumer goods to storing valuable items, from facilitating global trade to aiding in logistics and supply chain management, boxes play a crucial role. They are an integral part of our economy and society, and their production and use have significant environmental implications.

Understanding the history of box manufacturing provides valuable insights into the evolution of industrial processes, technological innovation, and societal change. It sheds light on how we have managed to efficiently package, store, and transport goods across vast distances. Moreover, it highlights the challenges and opportunities in the industry, informing future directions for sustainable and innovative box manufacturing.

# Early History of Box Manufacturing

The early history of box manufacturing is as diverse as the uses of the boxes themselves. Initially, boxes were primarily made of wood and were used for a variety of purposes. Large wooden crates were used for transporting heavy goods such as machinery and agricultural products, while smaller, intricately designed boxes were used for storing personal items like jewelry and documents. Some boxes were even used as burial containers in ancient civilizations.

The evolution of box designs and materials was driven by the need for more efficient and durable packaging solutions. The introduction of cardboard in the 19th century marked a significant milestone in the history of box manufacturing. Cardboard boxes were lighter, cheaper, and easier to produce than wooden boxes, making them an ideal choice for packaging consumer goods. They were also more versatile, as they could be easily shaped and customized to fit a wide range of products.

Key pioneers in the field of box manufacturing include Robert Gair, a paper bag maker from Brooklyn, who invented the pre-cut cardboard box in 1890. Gair's invention was a result of a fortunate accident: a press knife mistakenly cut through thousands of seed bags instead of pressing them. This led Gair to the idea of creating a machine that could cut and crease cardboard in one operation. This innovation significantly reduced the time and effort required to assemble boxes, paving the way for mass production. Another notable figure is Albert Jones of New York, who patented the first corrugated cardboard box in 1871. Jones' invention provided a stronger and more durable alternative to the traditional wooden crates, revolutionizing the packaging industry.

# Industrial Revolution and Box Manufacturing

The Industrial Revolution, a period of rapid industrialization from the mid-18th to mid-19th century, brought about significant changes in agriculture, manufacturing, mining, and transport that had a profound effect on the socio-economic and cultural conditions of the time. One of the industries that was greatly impacted by this revolution was box manufacturing.

The Industrial Revolution had a profound impact on box manufacturing, transforming it from a labor-intensive, manual process to a mechanized, efficient one. Prior to the revolution, boxes were primarily made by hand, which was a time-consuming and costly process. The advent of steam-powered machinery and assembly line techniques during the Industrial Revolution enabled the mass production of boxes. This not only increased the efficiency and speed of box production but also significantly reduced the cost, making boxes more accessible to a wider market. The revolution also led to the development of new materials and designs, further enhancing the versatility and utility of boxes.

Technological advancements in box production continued throughout the 20th century. The invention of corrugated cardboard in the 1950s, for example, provided a more durable and versatile material for box manufacturing. Corrugated boxes quickly became the standard for shipping and packaging, thanks to their strength, lightweight properties, and cost-effectiveness.

The emergence of mass production techniques during the Industrial Revolution had significant effects on the box manufacturing industry. It led to the standardization of box sizes and designs, which facilitated easier storage and transportation. This standardization also made it possible to produce boxes in large quantities, meeting the growing demand for packaging in the burgeoning consumer goods industry.

Mass production also opened up new opportunities for branding and marketing. Companies began to use boxes not just as a means of packaging and transporting goods, but also as a medium for advertising their products. This led to the development of printed boxes, which allowed companies to display their logos, product information, and other marketing messages directly on the box.

# Modern Box Manufacturing

In the contemporary era, box manufacturing has evolved into a sophisticated industry, leveraging cutting-edge technologies and innovative materials. The process has become highly automated, with a strong emphasis on efficiency, precision, and sustainability.

Modern box manufacturing methods have been revolutionized by the advent of automation and digital technology. The process typically begins with the design phase, where box specifications such as dimensions, material type, and print design are determined. Computer-aided design (CAD) software is often used in this phase to create precise and customizable box designs.

The materials used in box manufacturing have also evolved. While cardboard remains a popular choice due to its cost-effectiveness and versatility, other materials like plastic, metal, and even glass are used for specific applications. For instance, plastic boxes are often used for food packaging due to their durability and resistance to moisture, while metal and glass boxes are used for high-end products like perfumes and spirits.

Automation plays a pivotal role in modern box manufacturing. Automated machines are used to cut, fold, and glue the boxes, significantly increasing the speed and efficiency of the production process. These machines can produce large quantities of boxes in a short amount of time, reducing labor costs and increasing productivity.

Digital technology has also transformed the industry. Computer-aided manufacturing (CAM) systems are used to control the machinery, ensuring precision and consistency in box production. Moreover, digital printing technology has enabled high-quality, customizable prints on boxes, enhancing their aesthetic appeal and marketing potential.

Sustainability has become a key consideration in box manufacturing. The industry faces increasing pressure to reduce its environmental impact, leading to several initiatives aimed at promoting sustainability. These include the use of recycled or recyclable materials, reducing waste in the production process, and implementing energy-efficient manufacturing practices.

Many manufacturers are also exploring the use of alternative, eco-friendly materials. For instance, biodegradable plastics and plant-based materials are being used to create sustainable packaging solutions. Additionally, companies are investing in research and development to innovate new, environmentally-friendly box designs and manufacturing processes.

# Conclusion

The history of box manufacturing is a captivating narrative that mirrors the broader evolution of human society, industrial processes, and technological advancements. It began with the rudimentary wooden boxes of the early days, which were primarily used for storage and transportation of goods. The design and size of these boxes were dictated by their intended use, with larger crates for heavy goods and smaller boxes for personal items.

The introduction of cardboard in the 19th century marked a significant turning point in the history of box manufacturing. Cardboard boxes, being lighter, cheaper, and easier to produce, revolutionized the packaging industry. This innovation was further propelled by pioneers like Robert Gair, whose invention of the pre-cut cardboard box in 1890 paved the way for mass production.

The Industrial Revolution brought about transformative changes in box manufacturing. The advent of steam-powered machinery and assembly line techniques enabled mass production, making boxes more accessible to a wider market. Technological advancements, such as the invention of corrugated cardboard in the 1950s, provided more durable and versatile materials for box manufacturing, setting new standards for shipping and packaging.

In the modern era, box manufacturing has become a highly automated process, with advanced machinery and digital technology playing a pivotal role. The use of computer-aided design (CAD) and computer-aided manufacturing (CAM) has streamlined the production process, allowing for greater precision and customization.

Environmental considerations have also come to the forefront in box manufacturing. With the growing awareness of the environmental impact of packaging waste, manufacturers are increasingly focusing on sustainability. This has led to the development of eco-friendly materials and recycling programs, as well as efforts to reduce the overall use of packaging.

Looking ahead, the box manufacturing industry is poised for further innovation and development. The trend towards automation and sustainability is likely to continue, driven by advancements in technology and a growing emphasis on environmental responsibility. We may also see the emergence of new materials and designs, as manufacturers strive to meet the changing needs of consumers and businesses.

In conclusion, the evolution of box manufacturing offers a fascinating glimpse into our past, while also providing valuable insights into our future. The humble box, often overlooked and taken for granted, has played a crucial role in our society and economy. Its story is a testament to human ingenuity and innovation, reminding us of our capacity to adapt and evolve in the face of changing circumstances. As we continue to navigate the challenges and opportunities of the 21st century, the lessons from the history of box manufacturing will undoubtedly serve as a valuable guide.
```

### Second Interaction

Let's send another message to our Agent:

```python
chat_history.add_user_message("Can you please add a section (including subsections) on boxes in popular culture?")
result = agent.execute(run_context, Budget(600))
```

And then we'll get the revised Article:

```python
print(result.messages[-1].message.message)
```

```
# Introduction

The history of box manufacturing is a captivating exploration that traces the evolution of a simple yet indispensable item in our daily lives. The box, in its various forms and materials, has been a fundamental component of commerce, storage, and transportation for centuries. This article aims to delve into the rich history of box manufacturing, exploring its origins, development, and the technological advancements that have shaped it over time.

The significance of box manufacturing cannot be overstated. Boxes are ubiquitous, serving a myriad of purposes in different sectors. From packaging consumer goods to storing valuable items, from facilitating global trade to aiding in logistics and supply chain management, boxes play a crucial role. They are an integral part of our economy and society, and their production and use have significant environmental implications.

Understanding the history of box manufacturing provides valuable insights into the evolution of industrial processes, technological innovation, and societal change. It sheds light on how we have managed to efficiently package, store, and transport goods across vast distances. Moreover, it highlights the challenges and opportunities in the industry, informing future directions for sustainable and innovative box manufacturing.

# Early History of Box Manufacturing

The early history of box manufacturing is as diverse as the uses of the boxes themselves. Initially, boxes were primarily made of wood and were used for a variety of purposes. Large wooden crates were used for transporting heavy goods such as machinery and agricultural products, while smaller, intricately designed boxes were used for storing personal items like jewelry and documents. Some boxes were even used as burial containers in ancient civilizations.

In ancient civilizations, boxes were used for a variety of purposes. In Egypt, for example, wooden boxes were used to store grains and other food items, while in Rome, they were used to transport goods across the vast Roman Empire. In China, boxes were often made of bamboo or other local materials and were used for storage and transportation. These early boxes were often decorated with intricate designs and symbols, reflecting the cultural and artistic sensibilities of the time.

The evolution of box designs and materials was driven by the needs of the time and the available resources. For instance, the use of metal boxes became popular during the Middle Ages for their durability and security. These boxes were often used to store valuable items such as gold, silver, and important documents. The designs of these boxes also evolved, with the introduction of locks and other security features.

The transition from wooden boxes to cardboard boxes marked a significant milestone in the history of box manufacturing. The first cardboard box was produced in England in 1817, but it wasn't until the mid-19th century that the cardboard box as we know it today was invented. This was largely due to the efforts of pioneers like Albert Jones of New York, who patented a method for making a stronger, single-piece cardboard box in 1856. This innovation paved the way for the mass production of cardboard boxes, revolutionizing the packaging industry and transforming global trade.

# Industrial Revolution and Box Manufacturing

The Industrial Revolution, which spanned from the late 18th to early 19th century, brought about significant changes in various sectors, including box manufacturing. The advent of new technologies and the shift from manual labor to mechanized production transformed the industry, leading to the mass production of boxes and the development of new box designs and materials.

## Impact of the Industrial Revolution on Box Manufacturing

The Industrial Revolution had a profound impact on box manufacturing. Prior to this period, boxes were primarily handmade, which was a labor-intensive and time-consuming process. However, the advent of steam power and mechanized production methods during the Industrial Revolution allowed for the mass production of boxes, significantly reducing production time and costs. This not only increased the availability of boxes but also made them more affordable, leading to a surge in demand.

The Industrial Revolution also led to significant improvements in transportation and logistics, which further boosted the box manufacturing industry. The development of railways and steamships allowed for the efficient transportation of goods, increasing the need for sturdy and reliable boxes for packaging and shipping. This led to the development of stronger and more durable boxes, such as the corrugated cardboard box, which remains a staple in the packaging industry today.

## Technological Advancements in Box Production

The Industrial Revolution ushered in a wave of technological advancements that revolutionized box production. One of the most significant developments was the invention of the cardboard box. In 1817, Sir Malcolm Thornhill, a British industrialist, produced the first commercial cardboard box. However, it wasn't until 1856 that the first machine for producing large quantities of cardboard boxes was invented by Henry Brown.

Another major advancement was the development of the corrugated cardboard box. In 1871, Henry G. Morse patented a machine for producing corrugated cardboard, which was stronger and more durable than regular cardboard. This invention revolutionized the packaging industry, as corrugated cardboard boxes were not only sturdy but also lightweight and easy to produce in large quantities.

## Emergence of Mass Production and its Effects

The emergence of mass production during the Industrial Revolution had a profound effect on box manufacturing. The ability to produce boxes in large quantities significantly reduced production costs, making boxes more affordable and accessible. This led to a surge in demand for boxes, not only for packaging and shipping goods but also for storing personal items.

Mass production also led to the standardization of box sizes and designs, which facilitated logistics and supply chain management. Standardized boxes were easier to stack and transport, improving efficiency in warehouses and during transportation. Moreover, the ability to produce boxes in large quantities allowed for the development of custom boxes, catering to specific needs and preferences.

The emergence of mass production also had significant societal implications. It led to the creation of new jobs in box manufacturing and related industries, contributing to economic growth. However, it also raised environmental concerns due to the increased use of resources and waste generation. These challenges continue to shape the box manufacturing industry today, driving efforts towards sustainable and innovative box manufacturing practices.

# Modern Box Manufacturing

Modern box manufacturing has come a long way from its humble beginnings. Today, boxes are made from a variety of materials, including cardboard, plastic, and metal. Cardboard remains the most popular material due to its cost-effectiveness, versatility, and recyclability. The manufacturing process involves cutting and folding sheets of cardboard into the desired shape and size, often using automated machinery for efficiency and precision.

Automation and digital technology have revolutionized box manufacturing. Computer-aided design (CAD) software allows for precise design and customization of boxes, while automated cutting and folding machines ensure consistent quality and high production speed. Moreover, technologies such as barcoding and RFID tagging have improved inventory management and tracking of boxes in the supply chain.

Environmental considerations and sustainability have become increasingly important in box manufacturing. The industry has made significant strides in reducing its environmental impact through the use of recycled materials, energy-efficient manufacturing processes, and sustainable sourcing practices. Moreover, many companies are exploring innovative solutions such as biodegradable boxes and reusable packaging systems to further reduce waste and carbon emissions.

# Boxes in Popular Culture

Boxes have not only been a practical tool in our daily lives but have also found their place in popular culture. They have been represented in various forms of media, carrying symbolic meanings, and have had a significant impact on popular culture.

In media, boxes have often been used as a plot device in films, literature, and television. They have been used to create suspense, as in the famous phrase "What's in the box?" from the film "Se7en". In children's literature and animation, boxes have often been portrayed as magical objects that hold surprises, as seen in the "Jack-in-the-box" or the "Pandora's box".

Symbolically, boxes often represent the unknown, secrets, or potential. They can symbolize confinement or limitation, as in the phrase "thinking outside the box". On the other hand, they can also symbolize abundance and surprise, as in the concept of a "gift box".

The impact of boxes on popular culture is profound. They have influenced language, idioms, and expressions. They have inspired art, design, and fashion. They have shaped the way we think about space, storage, and organization. In essence, boxes, in their simplicity and functionality, have left an indelible mark on our culture and society.

# Conclusion

The journey of box manufacturing is a testament to human ingenuity and adaptability. From the rudimentary wooden boxes of ancient civilizations to the sophisticated, automated production of modern cardboard and plastic boxes, the industry has continually evolved to meet changing societal needs and technological advancements. This evolution has been driven by a variety of factors, including the need for efficient storage and transportation, the impact of the industrial revolution, and the advent of mass production techniques.

In the current era, box manufacturing is characterized by a focus on sustainability and efficiency. The industry has embraced automation and digital technology, leading to increased production speeds and improved precision. At the same time, there is a growing emphasis on environmental responsibility. Manufacturers are increasingly using recycled materials and implementing processes that minimize waste and reduce carbon emissions. These trends reflect a broader societal shift towards sustainable practices and a recognition of the environmental impact of manufacturing processes.

Looking ahead, the future of box manufacturing is likely to be shaped by continued technological innovation and an increasing focus on sustainability. Developments in materials science could lead to the creation of new types of boxes that are more durable, lightweight, and environmentally friendly. Advances in automation and digital technology could further increase efficiency and reduce costs. At the same time, manufacturers will need to navigate challenges such as changing regulations, fluctuating demand, and the need for ongoing innovation.

In conclusion, the history of box manufacturing offers valuable insights into the evolution of industry and technology. It is a story of continual adaptation and innovation, driven by changing societal needs and technological advancements. As we look to the future, it is clear that box manufacturing will continue to play a crucial role in our economy and society, and that the industry will need to continue evolving to meet new challenges and opportunities.
```

## Conclusion

This marks the end of the tutorial. Feel free to keep exploring this example in the notebook [run_agent.ipynb](../run_agent.ipynb) by asking for more edits. You can also try running the Agent with your own request. Thanks for reading!