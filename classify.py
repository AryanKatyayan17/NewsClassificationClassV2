import os
import re
import json
import pprint
from dotenv import load_dotenv
from ollama import chat
from tqdm import tqdm

OUTPUT_FILE = "test_classified_news.json"

class Classify:
    def __init__(self):
        self.system_prompt= """<|think|>
        You are a strict JSON geopolitical threat classification system.
        Classify the provided news article into threat categories and assign a severity level.
        Return ONLY valid JSON.

        OUTPUT RULES:
        - Return a single valid JSON object — nothing else.
        - No markdown fences, comments, or extra text.
        - Start your response with '{' and end with '}'.
        - All strings must be properly JSON-escaped (escape newlines, tabs, quotes).

        CATEGORIES (use ONLY these exact strings):
        - "Military Affairs": Armed forces, defense policies, military operations, weapons systems, troop deployments, defense spending.
        - "Diplomacy": International relations, treaties, negotiations, sanctions, diplomatic summits, ambassadorial activities.
        - "Conflict": Active or escalating tensions, disputes, armed hostilities, wars, ceasefire violations between groups or nations.
        - "Crime": Criminal activities, organized crime, law enforcement operations, terrorism-related arrests, public safety incidents.
        - "Economic Security": Threats to economic stability, trade wars, sanctions impact, supply chain disruptions, energy security, financial system risks.
        - "Security": National security concerns, intelligence operations, border security, protective measures NOT covered by Military Affairs, Cyberattacks, or Crime.
        - "Domestic Political Stability": Internal political crises, coups, protests, governance failures, election interference, civil unrest.
        - "Cyberattacks": Digital intrusions, ransomware, state-sponsored hacking, critical infrastructure cyber threats, data breaches with geopolitical implications.

        SEVERITY LEVELS (use ONLY these exact strings):
        - "Low": Routine or informational news with no immediate threat. Examples: scheduled military exercises, routine diplomatic meetings, policy announcements, minor cyber probes.
        - "Medium": Moderate threat or developing situation that may impact regional stability or safety. Examples: rising diplomatic tensions, trade disputes, non-critical cyber incidents, protest movements gaining momentum.
        - "High": Significant threat or escalation with potential to impact stability, safety, or international relations. Examples: military buildups near borders, major sanctions packages, large-scale civil unrest, critical infrastructure breaches.
        - "Alert": Critical or immediate threat requiring urgent attention. Examples: active armed conflict, major terrorist attacks, coups in progress, widespread attacks on critical infrastructure, imminent military invasion.

        IMPORTANT RULES FOR SPECIFIC FIELDS:
        - categories: MUST contain between 1 and 3 values from the allowed list above. Do not invent new categories. Do not force 3 if fewer are relevant. Only assign a category if the article DIRECTLY relates to its definition — tangential mentions do not qualify.
        - categories (Security): Use "Security" ONLY when the content does not fit more specifically into "Military Affairs", "Cyberattacks", or "Crime". It is a fallback category, not a default.
        - severity: MUST be exactly ONE of: "Low", "Medium", "High", "Alert". Never assign more than one.
        - severity (assessment): Base severity strictly on what is REPORTED in the article. Do not speculate. Evaluate using: (1) Immediacy — is the threat active or imminent? (2) Scale — local, regional, or global impact? (3) Affected parties — how many people, nations, or systems? (4) Escalation — is the situation worsening or contained?
        - severity (ambiguity): When the article is ambiguous or lacks detail, default to the LOWER applicable severity level.

        EDGE CASE RULES:
        - Multi-event articles: Assign the severity of the MOST severe event described.
        - Opinion or editorial pieces: Classify based on the underlying topic and assign "Low" unless a concrete threat is described.
        - Unclear category fit: Select the closest matching category. Never return an empty categories array.

        SCHEMA:
        {
        "categories": ["string — 1 to 3 values from allowed categories list, REQUIRED"],
        "severity": "string — exactly one of: Low|Medium|High|Alert, REQUIRED"
        }

        EXAMPLES:

        Input: "NATO announced a large-scale troop deployment near the Russian border following intelligence reports of military buildup."
        Output:
        {
        "categories": ["Military Affairs", "Conflict"],
        "severity": "High"
        }

        Input: "The EU and Japan signed a new trade agreement aimed at reducing tariffs on agricultural products."
        Output:
        {
        "categories": ["Diplomacy", "Economic Security"],
        "severity": "Low"
        }

        Input: "A state-sponsored hacking group breached the power grid of three European nations, causing widespread outages."
        Output:
        {
        "categories": ["Cyberattacks", "Security", "Conflict"],
        "severity": "Alert"
        }

        Input: "Thousands of protesters clashed with police in the capital after disputed election results were announced."
        Output:
        {
        "categories": ["Domestic Political Stability", "Conflict"],
        "severity": "High"
        }

        Input: "The central bank governor warned that ongoing sanctions could trigger a currency crisis within months."
        Output:
        {
        "categories": ["Economic Security", "Diplomacy"],
        "severity": "Medium"
        }

        Extract ONLY explicitly stated information. Return ONLY JSON.
        """

    def extract_json(self,output):
        try:
            match = re.search(r"\{.*\}", output, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return None
        except:
            return None

    def loop_label_article(self,article):
        try:
            user_prompt=f"""
            Title: {article.get("title","")}
            Content: {article.get("text", "")[:4000]}
            """
            response=chat(
                model="gemma4:e2b",
                messages=[
                    {
                        "role": "system",
                        "content": self.system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                options={"temperature":0.1, "format":"json"}
            )

            result= response.message.content
            return result
            
        except Exception as e:
            print(f"Error classifying article: {e}")
            return None
        
    def label_article(self,articles):
        classified_articles=[]

        for article in tqdm(articles, desc="Classifying articles"):
            raw_result = self.loop_label_article(article)

            if raw_result is None:
                continue

            parsed_result= self.extract_json(raw_result)

            if parsed_result is None:
                continue

            enriched_article={
                **article,
                "classification": parsed_result
            }

            classified_articles.append(enriched_article)

        return classified_articles
    
    def save_articles(self, articles):
        if os.path.exists(OUTPUT_FILE):
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        else:
            existing_data = []


        # Create a dictionary using URL as key
        combined_data = {article["url"]: article for article in existing_data}

        # Add new classified articles, overwrite if same URL
        for article in articles:
            combined_data[article["url"]] = article


        # Convert back to list
        final_data = list(combined_data.values())

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(final_data, f, ensure_ascii=False, indent=4)