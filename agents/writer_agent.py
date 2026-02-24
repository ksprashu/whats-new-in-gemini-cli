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
import google.genai as genai
from typing import List, Dict

class WriterAgent:
    def __init__(self):
        # Support both common Gemini/Google API key environment variables
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Neither GOOGLE_API_KEY nor GEMINI_API_KEY environment variable is set")
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-3-pro-preview"

    def _extract_status(self, text: str) -> tuple[str, str]:
        """
        Helper method to extract the [STATUS: ...] tag from the end of the text.
        """
        status = "Available" # Default
        if "[STATUS: Experimental]" in text:
            status = "Experimental"
            text = text.replace("[STATUS: Experimental]", "").strip()
        elif "[STATUS: Available]" in text:
            status = "Available"
            text = text.replace("[STATUS: Available]", "").strip()
        return text, status

    def generate_report(self, feature_text: str, github_context: List[Dict]) -> tuple[str, str]:
        """
        Generates a comprehensive report using Gemini and extracts the feature status.
        """
        context_str = ""
        for item in github_context:
            context_str += f"URL: {item['url']}\n"
            if "title" in item:
                context_str += f"Title: {item['title']}\n"
            context_str += f"Description: {item['description']}\n\n"

        prompt = f"""
You are an expert technical writer and technology journalist tracking the Gemini CLI.
Based on the following changelog snippet and detailed GitHub context (PRs and Issues), write a comprehensive report.

Crucially, you must write the report in the **third person**, similar to a tech news journalist covering a release. DO NOT use "We are excited to...", instead describe the changes objectively.

Changelog Snippet:
{feature_text}

GitHub Context:
{context_str}

Please generate the report EXACTLY following this Markdown template (do not include the triple backticks in your output):

# [Feature Name] - [Elevator Pitch / Tagline]

> **Status:** [Experimental / Available]

<!-- 
=========================================
  USER MODE SECTIONS (Public Facing)
========================================= 
-->

## The Headline
*Write this like a tech journalist! Fun, engaging, and in the third person. What is the feature, and why will the user love it? Replace formal jargon with exciting, relatable benefits.*

## Quick Start / How to Try It Out
*Concise instructions on how the user can interact with the feature.*
* **Prerequisites / Flags**: Does it need an experimental flag in `.gemini/config.ts`?
* **Commands**: Provide the exact CLI command or prompt to trigger it. E.g., `gemini prompt "..."`

## Use Cases (Why you need this)
*2-3 bullet points of real-world scenarios where this feature saves the developer time or effort.*

## What to Expect (Things to Look Out For)
*A brief, user-friendly heads-up on edge cases, latency, or expected behaviors.*

<!-- === ADMIN === -->

## Technical Deep Dive (Admin)
*The highly technical walkthrough extracted from PRs and GitHub issues. Explain the architecture, the "Under the Hood" mechanics, API transitions, or significant refactors backing this feature.*

## Background & Context (Admin)
*The history. Why was this built? What were the limitations before? Reference specific friction points, community feedback, or issue numbers.*

## Content & Demo Scenarios (Admin)
*Actionable ideas for blogs, videos, and podcasts. Include "Wow" factors.*
* **Scenario A [Name]:** Goal -> Action -> The "Wow" Factor.
* **Scenario B [Name]:** Goal -> Action -> The "Wow" Factor.

## Social Media Hooks (Admin)
*2-3 short, catchy drafts for X/Twitter or LinkedIn posts to promote this feature.*

IMPORTANT: At the very end of your response, on a new line, you MUST append a status tag.
If the feature is explicitly marked as experimental, beta, or requires an experimental configuration flag to enable, output: [STATUS: Experimental]
Otherwise, output: [STATUS: Available]
"""
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        return self._extract_status(response.text)

    def reformat_report(self, old_report_content: str) -> tuple[str, str]:
        """
        Takes an existing report, reformats it into the new structure, and extracts the feature status.
        """
        prompt = f"""
You are an expert technical editor. I have an existing "What's New" report about a Gemini CLI feature. 
I need you to rewrite/reorganize this report into a new standardized format.

Existing Report Content:
---
{old_report_content}
---

Please rewrite the content into these THREE sections exactly as named below:
1. **Summary Report**: Merge the existing summary, background, and walkthrough information into a cohesive, third-person journalistic narrative.
2. **Things to Look Out For**: Extract or infer any warnings, experimental statuses, or configuration steps mention in the original report.
3. **Demo Scenarios**: Rewrite the existing demo ideation to be even more engaging and actionable.

Maintain the third-person journalistic tone. Do not lose any technical details from the original. Format in Markdown.

IMPORTANT: At the very end of your response, on a new line, you MUST append a status tag based on the content of the report.
If the feature is explicitly marked as experimental, beta, or requires an experimental configuration flag to enable, output: [STATUS: Experimental]
Otherwise, output: [STATUS: Available]
"""
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        return self._extract_status(response.text)
