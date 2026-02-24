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

import pytest
from unittest.mock import MagicMock
from src.agent import AgentOrchestrator, SynthesizedFeatureContext

def test_agent_orchestrator_synthesize_feature(mocker):
    # Mock the genai client
    mock_client = MagicMock()
    mock_model_response = MagicMock()
    
    # We will simulate the raw JSON response returned by the google-genai model
    mock_model_response.text = '''
    {
        "feature_name": "Mock Feature",
        "problem_statement": "There was a bug causing the CLI to crash.",
        "solution_description": "We added a null check and fixed the error.",
        "how_to_try_it": "Run `gemini-cli --mock-feature`",
        "key_takeaways": ["It doesn't crash anymore", "It works great"]
    }
    '''
    
    mock_client.models.generate_content.return_value = mock_model_response
    
    # Patch the actual init so it uses our mock client
    mocker.patch('google.genai.Client', return_value=mock_client)
    
    orchestrator = AgentOrchestrator(api_key="fake-key")
    
    changelog_content = "Added a mock feature (#123)."
    pr_texts = ["# PR 123\\n## Description\\nFixed a bug."]
    
    result = orchestrator.synthesize_feature(changelog_content, pr_texts)
    
    # Verify the output is the correct Pydantic model
    assert isinstance(result, SynthesizedFeatureContext)
    assert result.feature_name == "Mock Feature"
    assert "null check" in result.solution_description
    assert len(result.key_takeaways) == 2

    # Verify that we correctly passed the config schema
    generate_content_calls = mock_client.models.generate_content.call_args_list
    assert len(generate_content_calls) == 1
    
    call_kwargs = generate_content_calls[0][1]
    assert call_kwargs["model"] == "gemini-2.5-flash"
    assert "Added a mock feature (#123)." in call_kwargs["contents"]
    
    # Verify config schema
    config = call_kwargs["config"]
    assert config.response_mime_type == "application/json"
    assert config.response_schema == SynthesizedFeatureContext
