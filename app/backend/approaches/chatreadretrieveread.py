import openai
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryType
from approaches.approach import Approach
from text import nonewlines

# Simple retrieve-then-read implementation, using the Cognitive Search and OpenAI APIs directly. It first retrieves
# top documents from search, then constructs a prompt with them, and then uses OpenAI to generate an completion 
# (answer) with that prompt.
class ChatReadRetrieveReadApproach(Approach):
    prompt_prefix = """<|im_start|>system
    You are a financial experts sales marketing in a tech company, and this is the template for you to provide the following data if anyone wants to display the full company data they want to search for. If anyone wants to search only the specific information such as company address or company link, just give them the only specific information about its company address or company link, it doesn't matter if the data you have is not real time, just display what is available according to the latest data available you have until september 2021. Don't apologize for any mistake. Combine your answer from your data and my data provided from internal PDF and add the caption you provide it from your data or our internal data (pdf), this is the result or template i show you below : 
'1. Company name
2. Company address
3. Company link
4. Company industry
5. Number of employees
6. List of names Board of Directors
7. List of names Board of Commissioners
8. Vision and mission of the company
9. Customers who use company services
10. Product that company sold
11. Company competitors
12. Company partners
13. Company S,W,O,T
14. Company's Target Market
15. Financial Report last 3 years
16. Revenue Report last 3 years
17. Company's EBITDA last 3 years
18. Company's Net Income last 3 years
19. Total Borrowings last 3 years
20. Total Equity last 3 years
21. Total Assets last 3 years'
{follow_up_questions_prompt}
{injected_prompt}
Sources:
{sources}
<|im_end|>
{chat_history}
"""

    follow_up_questions_prompt_content = """'"""

    query_prompt_template = """

Chat History:
{chat_history}

Question:
{question}

Search query:
"""

    def __init__(self, search_client: SearchClient, chatgpt_deployment: str, gpt_deployment: str, sourcepage_field: str, content_field: str):
        self.search_client = search_client
        self.chatgpt_deployment = chatgpt_deployment
        self.gpt_deployment = gpt_deployment
        self.sourcepage_field = sourcepage_field
        self.content_field = content_field

    def run(self, history: list[dict], overrides: dict) -> any:
        use_semantic_captions = True if overrides.get("semantic_captions") else False
        top = overrides.get("top") or 3
        exclude_category = overrides.get("exclude_category") or None
        filter = "category ne '{}'".format(exclude_category.replace("'", "''")) if exclude_category else None

        # STEP 1: Generate an optimized keyword search query based on the chat history and the last question
        prompt = self.query_prompt_template.format(chat_history=self.get_chat_history_as_text(history, include_last_turn=False), question=history[-1]["user"])
        completion = openai.Completion.create(
            engine=self.gpt_deployment, 
            prompt=prompt, 
            temperature=0.0, 
            max_tokens=32, 
            n=1, 
            stop=["\n"])
        q = completion.choices[0].text

        # STEP 2: Retrieve relevant documents from the search index with the GPT optimized query
        if overrides.get("semantic_ranker"):
            r = self.search_client.search(q, 
                                          filter=filter,
                                          query_type=QueryType.SEMANTIC, 
                                          query_language="en-us", 
                                          query_speller="lexicon", 
                                          semantic_configuration_name="default", 
                                          top=top, 
                                          query_caption="extractive|highlight-false" if use_semantic_captions else None)
        else:
            r = self.search_client.search(q, filter=filter, top=top)
        if use_semantic_captions:
            results = [doc[self.sourcepage_field] + ": " + nonewlines(" . ".join([c.text for c in doc['@search.captions']])) for doc in r]
        else:
            results = [doc[self.sourcepage_field] + ": " + nonewlines(doc[self.content_field]) for doc in r]
        content = "\n".join(results)

        follow_up_questions_prompt = self.follow_up_questions_prompt_content if overrides.get("suggest_followup_questions") else ""
        
        # Allow client to replace the entire prompt, or to inject into the exiting prompt using >>>
        prompt_override = overrides.get("prompt_template")
        if prompt_override is None:
            prompt = self.prompt_prefix.format(injected_prompt="", sources=content, chat_history=self.get_chat_history_as_text(history), follow_up_questions_prompt=follow_up_questions_prompt)
        elif prompt_override.startswith(">>>"):
            prompt = self.prompt_prefix.format(injected_prompt=prompt_override[3:] + "\n", sources=content, chat_history=self.get_chat_history_as_text(history), follow_up_questions_prompt=follow_up_questions_prompt)
        else:
            prompt = prompt_override.format(sources=content, chat_history=self.get_chat_history_as_text(history), follow_up_questions_prompt=follow_up_questions_prompt)

        # STEP 3: Generate a contextual and content specific answer using the search results and chat history
        completion = openai.Completion.create(
            engine=self.chatgpt_deployment, 
            prompt=prompt, 
            temperature=overrides.get("temperature") or 0.7, 
            max_tokens=3072, 
            n=1, 
            stop=["<|im_end|>", "<|im_start|>"])

        return {"data_points": results, "answer": completion.choices[0].text, "thoughts": f"Searched for:<br>{q}<br><br>Prompt:<br>" + prompt.replace('\n', '<br>')}
    
    def get_chat_history_as_text(self, history, include_last_turn=True, approx_max_tokens=1000) -> str:
        history_text = ""
        for h in reversed(history if include_last_turn else history[:-1]):
            history_text = """<|im_start|>user""" +"\n" + h["user"] + "\n" + """<|im_end|>""" + "\n" + """<|im_start|>assistant""" + "\n" + (h.get("bot") + """<|im_end|>""" if h.get("bot") else "") + "\n" + history_text
            if len(history_text) > approx_max_tokens*4:
                break    
        return history_text





"""
       Note: The openai-python library support for Azure OpenAI is in preview.
        import os
        import openai
        openai.api_type = "azure"
        openai.api_base = "https://cog-xv4xblym6zqvw.openai.azure.com/"
        openai.api_version = "2023-03-15-preview"
        openai.api_key = os.getenv("OPENAI_API_KEY")

        response = openai.ChatCompletion.create(
        engine="chat",
        messages = [{"role":"system","content":"You are a financial experts sales marketing in a tech company, and this is the template for you to provide the following data if anyone wants to display the full company data they want to search for. If anyone wants to search only the specific information such as company address or company link, just give them the only specific information about its company address or company link, it doesn't matter if the data you have is not real time, just display what is available according to the latest data available you have until september 2021. Don't apologize for any mistake. this is the result or template i show you below : \n'1. Company name\n2. Company address\n3. Company link\n4. Company industry\n5. Number of employees\n6. List of names Board of Directors\n7. List of names Board of Commissioners\n8. Vision and mission of the company\n9. Customers who use company services\n10. Product that company sold\n11. Company competitors\n12. Company partners\n13. Company S,W,O,T\n14. Company's Target Market\n15. Top 3 News about the company\n16. Top 3 Company's Achievements\n17. Financial Report last 3 years\n18. Revenue Report last 3 years\n19. Company's EBITDA last 3 years\n20. Company's Net Income last 3 years\n21. Total Borrowings last 3 years\n22. Total Equity last 3 years\n23. Total Assets last 3 years'"}],
        temperature=0.7,
        max_tokens=800,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None)
"""