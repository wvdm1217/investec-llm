import os
import json
import base64
import dotenv
import requests
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits.openapi.spec import reduce_openapi_spec
from langchain_community.utilities import RequestsWrapper
from langchain_community.agent_toolkits.openapi import planner


class EnvChecker:
    def __init__(self, env_vars):
        self.env_vars = env_vars
        dotenv.load_dotenv()
        self.check_env_vars()

    def check_env_vars(self):
        for var in self.env_vars:
            assert os.getenv(var) is not None, f"Environment variable {var} is not set."


env_vars = [
    "INVESTEC_CLIENT_ID",
    "INVESTEC_CLIENT_SECRET",
    "INVESTEC_API_KEY",
    "OPENAI_API_KEY",
]
checker = EnvChecker(env_vars)
checker.check_env_vars()

class InvestecAPIClient:
    def __init__(self):
        self.client_id = os.getenv("INVESTEC_CLIENT_ID")
        self.client_secret = os.getenv("INVESTEC_CLIENT_SECRET")
        self.api_key = os.getenv("INVESTEC_API_KEY")
        response = self.get_access_token()
        self.access_token = response["access_token"]

    def get_access_token(self):
        url = "https://openapi.investec.com/identity/v2/oauth2/token"
        data = "grant_type=client_credentials"
        credentials = f"{self.client_id}:{self.client_secret}"
        headers = {
            "Authorization": f"Basic {base64.b64encode(credentials.encode()).decode()}",
            "Content-Type": "application/x-www-form-urlencoded",
            "x-api-key": self.api_key,
        }
        response = requests.request("POST", url=url, headers=headers, data=data)

        return response.json()

    def get_auth_header(self):
        return {"Authorization": f"Bearer {self.access_token}"}

if __name__ == "__main__":
    client = InvestecAPIClient()
    headers = client.get_auth_header()
    requests_wrapper = RequestsWrapper(headers=headers)

    with open("swagger.json") as f:
        swagger_spec = json.load(f)
    api_spec = reduce_openapi_spec(swagger_spec)

    llm = ChatOpenAI(model_name="gpt-4", temperature=0.0)

    agent = planner.create_openapi_agent(
        api_spec,
        requests_wrapper,
        llm,
        allow_dangerous_requests=True,
    )
    user_query = "How much money do I have in my accounts?"
    agent.invoke(user_query)
