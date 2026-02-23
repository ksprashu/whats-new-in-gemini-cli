import os
import google.genai as genai
from typing import List, Dict

class WriterAgent:
    def __init__(self):
        # We'll expect GEMINI_API_KEY to be in the environment
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-3-pro-preview"

    def generate_report(self, feature_text: str, github_context: List[Dict]) -> str:
        """
        Generates a comprehensive report using Gemini.
        """
        context_str = ""
        for item in github_context:
            context_str += f"URL: {item['url']}\n"
            if "title" in item:
                context_str += f"Title: {item['title']}\n"
            context_str += f"Description: {item['description']}\n\n"

        prompt = f"""
You are an expert technical writer and technology journalist tracking the Gemini CLI.
Based on the following changelog snippet and detailed GitHub context (PRs and Issues), write a comprehensive "What's New" report.

Crucially, you must write the report in the **third person**, similar to a tech news journalist covering a release. DO NOT use "We are excited to...", instead describe the changes objectively (e.g., "In the v0.29 release of Gemini CLI on 19th Feb, the following new feature was introduced... This stemmed from the fact that users were requesting...").

Changelog Snippet:
{feature_text}

GitHub Context:
{context_str}

Please include the following sections in your report:
1. **Feature Summary**: A high-level overview of the feature. **Important:** If the feature is marked as experimental or note says to enable it in configuration, highlight this visibly right at the beginning of the report (e.g., as an "Experimental Feature" callout or icon).
2. **Background & Context**: Why was this change made? What problem does it solve? (Grounded in PR/Issue discussions).
3. **How-To Guide**: Step-by-step instructions or examples on how to use the feature.
4. **Walkthrough / Technical Deep Dive**: Explain how it works under the hood if possible.
5. **Next Steps for Demos**: Provide robust, detailed ideation on how to deep-dive into this product feature. What scenarios make for a great demo? How can a developer showcase it to end users? Make this section highly engaging and actionable.

Format the report in standard Markdown.
"""
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        return response.text
