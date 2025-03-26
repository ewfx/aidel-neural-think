from fastapi import WebSocket
from typing import Any,List,Set,Tuple
import json
import json_repair
import re
from gpt_researcher import GPTResearcher
from urllib.parse import quote



class BasicReport:
    def __init__(
        self,
        query: str,
        query_domains: list,
        report_type: str,
        report_source: str,
        source_urls,
        document_urls,
        tone: Any,
        config_path: str,
        websocket: WebSocket,
        headers=None
    ):
        self.query = query
        self.query_domains = query_domains
        self.report_type = report_type
        self.report_source = report_source
        self.source_urls = source_urls
        self.document_urls = document_urls
        self.tone = tone
        self.config_path = config_path
        self.websocket = websocket
        self.headers = headers or {}

        self.global_context: str = ""
        #self.global_written_sections: List[str] = []
        # self.global_urls: Set[str] = set(
        #     self.source_urls) if self.source_urls else set()








        # with open('/home/anonymousa/Projects/wf-hackathon/gpt-researcher/backend/report_type/queries/extract_companies.txt', 'r') as file:
        #     self.query = file.read()


    async def _extract_entity_data(self) -> Tuple[List[str],str]:

        with open('/home/anonymousa/Projects/wf-hackathon/gpt-researcher/backend/report_type/queries/used/extract_companies.txt', 'r') as file:
            role = file.read()

        researcher = GPTResearcher(
            query=role,
            query_domains=self.query_domains,
            report_type="custom_report",
            report_source="local",
            source_urls=self.source_urls,
            document_urls=self.document_urls,
            config_path=self.config_path,
            websocket=self.websocket,
            headers=self.headers,
            complement_source_urls=False,
            agent="Company names extractor agent",
            role="Extract company names from the following data ",
            report_format="json"
        )

        await researcher.conduct_research()

        self.global_context+=researcher.context

        report = await researcher.write_report()

        report_json = json.loads(extract_json_with_regex(report))

        entities=list(set(report_json['companies']))
        print(entities)

        with open("/home/anonymousa/Projects/wf-hackathon/gpt-researcher/backend/report_type/output/entities.txt","w") as file:
            for entity in entities:
                file.write(entity + "\n")


        return entities,report
    

    async def _get_entity_info(self,company) -> Tuple[dict,str]:
            
        print(f"\n\n\nResearching on {company}")
        print(f"\n\n\nQuery Domains:{self.query_domains}")

        with open('/home/anonymousa/Projects/wf-hackathon/gpt-researcher/backend/report_type/queries/used/old_entity_search_query.txt', 'r') as file:
            query = file.read()

        # with open('/home/anonymousa/Projects/wf-hackathon/gpt-researcher/backend/report_type/queries/used/new_rate_entities.txt', 'r') as file:
        #     role = file.read()

        
        company_researcher = GPTResearcher(
        #query=research_query.format(company=company),
        #TODO: Optimize this query
        query=query.format(entity=company),
        query_domains=["https://wikipedia.org","https://opencorporates.com","https://www.sec.gov/edgar/","https://ofac.treasury.gov/",        "https://reuters.com", "https://bbc.com", "https://forbes.com", "https://bloomberg.com", "https://ft.com", "https://sec.gov", "https://justice.gov",
        "https://fbi.gov", "https://consumerfinance.gov", "https://corporationwiki.com", "https://opencorporates.com", "https://oag.ca.gov",
        "https://nasdaq.com", "https://wsj.com", "https://cnbc.com", "https://law360.com", "https://classaction.org", "https://glassdoor.com",
        "https://ripoffreport.com", "https://investopedia.com"],
        report_type="custom_company",
        report_source="web",
        #source_urls=["https://www.wikidata.org/","https://opencorporates.com/","https://www.sec.gov/edgar/","https://ofac.treasury.gov/"],
        source_urls=[f"http://192.168.1.13:8084/search?q={quote(company)}&minMatch=0.85"],
        document_urls=self.document_urls,
        config_path=self.config_path,
        websocket=self.websocket,
        headers=self.headers,
        complement_source_urls=True,
        agent="Company Researcher agent",
        role="Research about fraudelent acts by companies",
        report_format="json",
        tone=company #tone used for company name
        )
        await company_researcher.conduct_research()

        self.global_context+=company_researcher.context

        company_report=await company_researcher.write_report()
        company_data = json.loads(extract_json_with_regex(company_report))
        print(company_data)

        with open("/home/anonymousa/Projects/wf-hackathon/gpt-researcher/backend/report_type/output/company_rating.txt","a") as file:
            file.write(str(company_data)+"\n")



        return company_data,company_report



    async def _classify_transactions(self) -> Tuple[list,str]:
        with open('/home/anonymousa/Projects/wf-hackathon/gpt-researcher/backend/report_type/queries/used/classify_transactions.txt', 'r') as file:
            role = file.read()

        researcher = GPTResearcher(
            query=role,
            query_domains=self.query_domains,
            report_type="custom_report",
            report_source="local",
            source_urls=self.source_urls,
            document_urls=self.document_urls,
            config_path=self.config_path,
            websocket=self.websocket,
            headers=self.headers,
            complement_source_urls=False,
            agent="Transaction classifier agent",
            role=role,
            report_format="json",
            context=self.global_context
        )

        await researcher.conduct_research()
        transaction_report=await researcher.write_report()
        transaction_data = json.loads(extract_json_with_regex(transaction_report))
        print(transaction_data)

        with open("/home/anonymousa/Projects/wf-hackathon/gpt-researcher/backend/report_type/output/transaction_classification.txt","a") as file:
            file.write(str(transaction_data)+"\n")


        return transaction_data,transaction_report     





    async def run(self):


        entities,entity_extract_report= await self._extract_entity_data()

        company_risk_scores=[]

        for entity in entities:

            data,_=await self._get_entity_info(entity)
            company_risk_scores.append(data)

            
        
        print(company_risk_scores)


        self.global_context+=str(company_risk_scores)


        await self._classify_transactions()



        return entity_extract_report
    

# async def handle_json_error(response):
#     try:
#         agent_dict = json_repair.loads(response)
#         if agent_dict.get("companies"):
#             return agent_dict["companies"]
#     except Exception as e:
#         print(f"⚠️ Error in reading JSON and failed to repair with json_repair: {e}")
#         print(f"⚠️ LLM Response: `{response}`")

#     json_string = extract_json_with_regex(response)
#     if json_string:
#         try:
#             json_data = json.loads(json_string)
#             return json_data["companies"]
#         except json.JSONDecodeError as e:
#             print(f"Error decoding JSON: {e}")

#     print("No JSON found in the string. Falling back to Default Agent.")
#     return "Default Agent", (
#         "You are an AI critical thinker research assistant. Your sole purpose is to write well written, "
#         "critically acclaimed, objective and structured reports on given text."
#     )


def extract_json_with_regex(response):
    json_match = re.search(r"{.*?}", response, re.DOTALL)
    if json_match:
        return json_match.group(0)
    return None
