import streamlit as st
from openai import OpenAI
import os
import re
import ast
import bs4, requests

client = OpenAI()


SYSTEM_PROMPT = "You are a smart and intelligent Named Entity Recognition (NER) system. I will provide you the definition of the entities you need to extract, the sentence from where your extract the entities and the output format with examples."

USER_PROMPT_1 = "Are you clear about your role?"

ASSISTANT_PROMPT_1 = "Sure, I'm ready to help you with your NER task. Please provide me with the necessary information to get started."

GUIDELINES_PROMPT = (
    "Entity Definition:\n"
    "1. PERSON: Short name or full name of a person from any geographic regions.\n"
    "2. DATE: Any format of dates. Dates can also be in natural language.\n"
    "3. LOC: Name of any geographic location, like cities, countries, continents, districts etc.\n"
    "4. ADDRESS: Any name related to a street, building, house or business.\n"
    "4. SUSPECTS: Names of all persons identified as the alleged perpetrator of suspicious activity.\n"
    "5. VICTIMS: Name of all person identified as the victims in the incicent.\n"
    "6. INCIDENT: Description of all circumstances and events of the text involving the victims and suspects.\n"
    "7. SOCIALMEDIA: Full name or detail of any social media mentioned.\n"
    "8. URL: Any URL that may be linked to the INCIDENT or PERSON mentioned.\n"
    "\n"
    "Output Format:\n"
    "{{'PERSON': [list of entities present], 'DATE': [list of entities present], 'LOC': [list of entities present],"
    "'SUSPECTS': [list of entities present], 'VICTIMS': [list of entities present], 'INCIDENT': [list of entities present],"
    "'SOCIAL MEDIA': [list of entities present], 'URL': [list of entities present]}}\n"
    "If no entities are presented in any category make the answer None\n"
    "\n"
    "Examples:\n"
    "\n"
    "1. Sentence: By 12th January 2015 thirteen-year-old Sunmaya Ayamnus had been missing from her home in Pokhara in Nepal for nearly a month when our team intercepted her. \n"
    "The suspect, Okesh Kitesh, promised to marry her shortly after they met each other on TikTok. \n"
    "Okesh and another suspect named Mangali Mans met up with Sunmaya and took her into the city, where they handed her over to a man named Sankar Raknas at Club Sixteen on Middle Path St. \n"
    "Sankar kept Sunmaya in hiding and made a video of her saying that she was safe and telling her family not to worry about her. \n"
    "He then created a Facebook account for her (https://www.facebook.com/Sunmaya.Ayamnus.100709/) and posted the video on it. \n"
    "Several days later, Okesh returned to the city, moved Sunmaya to a new location, and raped her. \n"
    "Weeks later, he attempted to cross the border with her when our staff stopped them and intercepted Sunmaya. \n"
    "They provided her with counseling about human trafficking and reunited her with her family, then filed a human trafficking case against the suspects. \n"
    "Police arrested two of the suspects immediately. \n"
    "Output: {{'PERSON': ['Sunmaya Ayamnus', 'Okesh Kitesh', 'Mangali Mans', 'Sankar Raknas'], 'DATE': ['12th January 2015'],"
    "'SUSPECT':['Okesh Kitesh', 'Mangali Mans', 'Sankar Raknas'], 'VICTIM':['Sunmaya Ayamnus'], 'SOCIAL MEDIA':['Facebook', 'TikTok']}}\n"
    "'LOC': ['Nepal', 'Pokhara'], 'ADDRESS':['Club Sixteen, Middle Path St'], 'INCIDENT': ['Human trafficking'], 'URL':['https://www.facebook.com/Sunmaya.Ayamnus.100709/']"
    "\n"
    "2. Sentence: In June 2021 two men, Jitesh Raja, Vinod Masa, came to Zeba Warsi's village in near Bharatpur in Chitwan district in Nepal with the \n"
    "promises of a new job in India. \n"
    "They took him to New Delhi, the capital in Northwestern India, and said he needed a blood test in Kolkata. At a clinic close to the JW Mariott hotel, he was drugged, \n and doctors removed one of his two kidneys.\n"
    "The traffickers gave him $4,500 and sent him packing back to Nepal.\n"
    "Output: {{'PERSON': ['Jitesh Raja', 'Vinod Masa', 'Zeba Warsi'], 'DATE': ['June 2021'], 'LOC': ['Bharatpur', 'Chitwan district', 'Nepal', 'India', 'New Delhi', 'Kolkata'], \n "
    "'SUSPECT':['Jitesh Raja', 'Vinod Masa'], 'VICTIM':['Zeba Warsi'], 'SOCIAL MEDIA':[None]}}\n"
    "'ADDRESS':['JW Mariott hotel'], 'INCIDENT': ['Organ trafficking'], 'URL':[None]"
    "\n"
    "3. Sentence: {}\n"
    "Output: "
)

COLORED_ENTITY = {"PERSON": "red", "DATE": "blue", "LOC": "green"}


def openai_chat_completion_response(final_prompt):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT_1},
            {"role": "assistant", "content": ASSISTANT_PROMPT_1},
            {"role": "user", "content": final_prompt},
        ],
    )

    return response.choices[0].message.content.strip(" \n")


URL = "https://www.cbc.ca/news/canada/hamilton/human-trafficking-arrests-1.7114076"

URL = st.text_input("Your url")
if st.button("Submit"):
    response = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    soup = bs4.BeautifulSoup(response.text, "lxml")
    text = soup.body.get_text(" ", strip=True)
    st.write(text)
    GUIDELINES_PROMPT = GUIDELINES_PROMPT.format(text)
    ners = openai_chat_completion_response(GUIDELINES_PROMPT)

    # Convert the corrected string to a dictionary
    ners_dictionary = ast.literal_eval(ners)
    st.write(ners_dictionary)
    with open("data/example.txt", "w") as file:
        # Write the text to the file
        file.write(text)
    # Error
    # Ollama
    # call
    # failed
    # with status code 404. Details: model
    # 'nomic-embed-text'
    # not found,
    # try pulling it first
    # #
    # for entity_type, entity_list in ners_dictionary.items():
    #     entity_list = list(set(entity_list))
    #     for ent in entity_list:
    #         if ent != 'None':
    #             my_sentence = re.sub(ent, ":"+COLORED_ENTITY[entity_type]+"["+ent+"\["+entity_type+"\]"+"]", my_sentence)
    # st.markdown(my_sentence)
