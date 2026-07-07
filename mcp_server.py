# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
from mcp.server.fastmcp import FastMCP
import skills

# Initialize the Model Context Protocol (MCP) server
# This exposes our specialized cognitive skills as tools that any MCP-compliant agent
# (like Antigravity or standard Gemini LLM clients) can discover and execute.
mcp = FastMCP("Runtime Terrors Companion Server")

@mcp.tool()
def calculate_athletic_recovery(duration_minutes: int, intensity_rpe: int) -> str:
    """
    Calculates training load metrics and a recovery score (0-100) to balance athletic training
    with academic fatigue. Returns a recovery score and specific resting recommendations.
    """
    try:
        res = skills.calculate_recovery_index(duration_minutes, intensity_rpe)
        return (
            f"Training Load: {res['training_load']} load units.\n"
            f"Recovery Score: {res['recovery_score']}/100.\n"
            f"Recommendation: {res['recommendation']}"
        )
    except Exception as e:
        return f"Error calculating recovery index: {str(e)}"

@mcp.tool()
def parse_markdown_study_notes(markdown_content: str) -> str:
    """
    Parses a student's raw markdown notes to extract structured academic milestones
    including subject, topic, completion status, and performance grade.
    """
    try:
        milestones = skills.parse_study_markdown(markdown_content)
        if not milestones:
            return "No valid milestones found. Ensure the content contains fields like 'Subject:', 'Topic:', 'Status:', 'Grade:'."
        
        result_lines = []
        for i, m in enumerate(milestones, 1):
            result_lines.append(
                f"Milestone #{i}:\n"
                f"  - Subject: {m.get('subject')}\n"
                f"  - Topic: {m.get('topic')}\n"
                f"  - Status: {m.get('status')}\n"
                f"  - Grade: {m.get('grade')}/100\n"
            )
        return "\n".join(result_lines)
    except Exception as e:
        return f"Error parsing study notes: {str(e)}"

@mcp.tool()
def calculate_spaced_repetition_sm2(
    ease_factor: float, interval_days: int, consecutive_correct: int, quality: int
) -> str:
    """
    Computes the next review date and updates spaced repetition metrics using the
    SuperMemo SM-2 algorithm. 
    Quality rating is 0 (total blackout) to 5 (perfect recall).
    """
    try:
        new_ef, new_interval, next_date, new_streak = skills.calculate_sm2_review(
            ease_factor, interval_days, consecutive_correct, quality
        )
        return (
            f"SM-2 Spaced Repetition Update:\n"
            f"  - New Ease Factor (EF): {new_ef}\n"
            f"  - New Interval (Days): {new_interval}\n"
            f"  - Next Scheduled Review Date: {next_date}\n"
            f"  - Consecutive Correct Streak: {new_streak}"
        )
    except Exception as e:
        return f"Error running SM-2 algorithm: {str(e)}"

if __name__ == "__main__":
    # Start the MCP server when run as a script
    mcp.run()
