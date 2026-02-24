# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import json
from typing import List
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

class SynthesizedFeatureContext(BaseModel):
    feature_name: str = Field(description="A concise, descriptive name for the feature.")
    problem_statement: str = Field(description="What was happening before this feature or bugfix was implemented. Why was it needed?")
    solution_description: str = Field(description="How the feature works, what changes were made, and what happens after it is implemented.")
    how_to_try_it: str = Field(description="Actionable steps, CLI commands, or configurations for a user to try this feature locally.")
    key_takeaways: List[str] = Field(description="A list of 2-4 key points or takeaways about this update.")

class AgentOrchestrator:
    def __init__(self, api_key: str | None = None, model: str = "gemini-2.5-flash"):
        self.model = model
        # The genai Client automatically looks for GEMINI_API_KEY if not provided
        self.client = genai.Client(api_key=api_key or os.environ.get("GEMINI_API_KEY"))

    def synthesize_feature(self, changelog_content: str, pr_texts: List[str]) -> SynthesizedFeatureContext:
        """
        Synthesizes the raw changelog text and GitHub PR/Issue discussions into structured context
        for downstream content generation.
        """
        pr_joined = "\n\n".join(pr_texts)
        prompt = f"""
        You are an expert Developer Relations engineer analyzing a new feature or fix for the Gemini CLI.
        Your goal is to synthesize the raw changelog entry and the associated GitHub Pull Request(s) and discussions 
        into a clean, structured JSON format that will be used to write blog posts and tutorial videos.

        # Context Provided
        ## Official Changelog Entry:
        {changelog_content}

        ## GitHub Pull Request & Issue Data:
        {pr_joined}

        Extract the core problem, the solution, actionable ways to test the feature, and key takeaways.
        """
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=SynthesizedFeatureContext,
                temperature=0.2
            )
        )
        
        # We parse the text attribute as JSON into our Pydantic model
        data = json.loads(response.text)
        return SynthesizedFeatureContext(**data)
