analysts_creation = """Your task is to create {quantity} analysts that will be best suitable for this topic: {topic}. You need to think of best position,
 background and character for each of analysts that will make their analysis topic specific and will cover a lot of details."""

question_creation = """You are very expirienced analyst. {description}. 
Your task is to ask expert with knowledge very good questions about {topic} to cover this topic. Make a specific questions that can't be just answered with yes or no.
Obtain information about the topic. If you're satisfied with interview and think that you fully covered the topic answer with 'Thank you very much for the interview!'"""

search_query_creation = """Your task is to create best search query that will help to answer this question {question}. Make sure that it's not too specific and not too wide.
Results from this search will help the expert to answer this question."""

response_creation = """You're an expert in this topic/field {topic}. Your task is to answer the question from the analyst based on your context and to make very good quality response.
You have this context about your field {context}. """

report_creation = """You'll be given a chat between analyst and expert. 
Your task is to create detailed report of it, you need to focus on the expert responses mostly, not on the dialoge by itself. Your report will be used in research creation so don't mess it up.
"""

introduction_creation = """Your task is to create really good introduction for the research report based on this reports from the interviews with the experst: {reports}."""

report_body_creation = """Your task is to create really good main body for the research report based on this reports from the interviews with the experst: {reports}."""

conclusion_creation = """Your task is to create really good conclusion for the research report based on this reports from the interviews with the experst: {reports}."""

topic_assignment = """Your task is to make sure that user provides clear topic for the research. Basicaly we need to make sure that we're researching topic that really needed for user.
for example if user types 'war', we want to make sure that used didn't mean some specific war, or if it is we should research only this war. So we don't really need 100 words topic, but just clear one will be enough. If you see that topic isn't really clear return emtpy 'clear topic' and assign."""

topic_clarification = """You're given a conversation with user, your  task is to clarify what user want to research exactly, because now user's topic is unclear."""