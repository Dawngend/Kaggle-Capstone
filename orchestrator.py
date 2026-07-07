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
import json
import sqlite3
from typing import Dict, Any, List
from google import genai
from google.genai import types

import database
import skills

class MultiAgentOrchestrator:
    """
    Orchestrates the Academic Tutor, Performance Coach, and Sophy Flashcard generators.
    Maintains memory context via SQLite database logs and implements fallback loops.
    """
    def __init__(self, db_path: str):
        self.db_path = db_path
        # Initialize Google GenAI client using Vertex AI backend with active GCP credentials
        try:
            self.client = genai.Client(
                vertexai=True,
                project="kaggle-day-5-501423",
                location="us-east1"
            )
            self.model_name = "gemini-2.5-flash"
        except Exception as e:
            print("Failed to initialize GenAI Client:", e)
            self.client = None
            self.model_name = ""

    def run_academic_tutor(self, user_id: int, subject: str, topic: str, query: str) -> str:
        """
        Academic Tutor Agent: Explains complex machine learning and data science topics.
        Generates byte-sized pipelines.
        """
        user_info = database.get_user(self.db_path, user_id)
        academic_level = user_info["academic_level"] if user_info else "Data Science Student"
        
        system_instruction = (
            "You are 'The Academic Tutor', an elite data science instructor at FEU Institute of Technology. "
            f"Your student's academic level is: {academic_level}. "
            "Explain complex concepts using clear, zero-fluff explanations, code snippets, and structured pipelines. "
            "Always include a brief check-in query at the end to assess student comprehension."
        )

        prompt = f"Subject: {subject}\nTopic: {topic}\nQuestion: {query}\n"
        
        try:
            if not self.client:
                raise ValueError("GenAI client not initialized.")
                
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2
                )
            )
            answer = response.text
        except Exception as e:
            answer = (
                f"[Fallback Tutor Mode]: API request failed ({str(e)}). Let me guide you on this topic:\n"
                f"*   Concept: Reviewing {topic} in {subject}.\n"
                f"*   Study Steps: 1. Read core formulas. 2. Implement a numpy-only demonstration. "
                "3. Assess validation accuracy."
            )

        database.log_conversation(self.db_path, user_id, "Academic Tutor", "user", query)
        database.log_conversation(self.db_path, user_id, "Academic Tutor", "assistant", answer)
        database.add_academic_milestone(self.db_path, user_id, subject, topic, "In Progress", 85.0)
        
        with database.get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT AVG(grade) FROM academic_milestones WHERE user_id = ?", (user_id,))
            avg_grade = cursor.fetchone()[0]
            if avg_grade:
                database.update_mastery_score(self.db_path, user_id, round(avg_grade, 2))
                
        return answer

    def run_performance_coach(self, user_id: int, session_type: str, duration: int, rpe: int, query: str) -> str:
        """
        Performance Coach Agent: Evaluates physical recovery index and adjusts training load.
        """
        res = skills.calculate_recovery_index(duration, rpe)
        recovery_score = res["recovery_score"]
        recommendation = res["recommendation"]
        
        system_instruction = (
            "You are 'The Performance Coach', an elite athletic coordinator. "
            "You evaluate athletic strain and manage performance loads to avoid academic and physical burnout. "
            "Reference the computed recovery score and recommendation in your advice."
        )

        prompt = (
            f"Physical Activity: {session_type}\n"
            f"Duration: {duration} mins, Intensity RPE: {rpe}/10\n"
            f"Calculated Recovery Score: {recovery_score}/100\n"
            f"Calculated Recommendation: {recommendation}\n"
            f"User Question: {query}\n"
        )

        try:
            if not self.client:
                raise ValueError("GenAI client not initialized.")
                
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3
                )
            )
            answer = response.text
        except Exception as e:
            answer = (
                f"[Fallback Coach Mode]: API request failed ({str(e)}).\n"
                f"*   Recovery Score: {recovery_score}/100\n"
                f"*   Load Balance Recommendation: {recommendation}"
            )

        database.log_conversation(self.db_path, user_id, "Performance Coach", "user", query)
        database.log_conversation(self.db_path, user_id, "Performance Coach", "assistant", answer)
        database.add_athletic_metric(self.db_path, user_id, session_type, duration, rpe, recovery_score)
        
        return answer

    def generate_study_flashcards(self, user_id: int, subject: str, topic: str, count: int = 3, language: str = "Taglish") -> List[Dict[str, str]]:
        """
        Sophy Study Engine Pipeline:
        1. Generates raw QA items using Gemini Developer/Vertex.
        2. Performs format verification check.
        3. Saves verified cards directly to SQLite 'flashcards' repository.
        """
        prompt = (
            f"Generate exactly {count} study flashcards for a student studying:\n"
            f"Subject: {subject}\n"
            f"Topic: {topic}\n"
            f"Language: {language} (use typical Taglish or Tagalog if specified, else English).\n"
            "Format the output strictly as a JSON array of objects, where each object has "
            "keys 'question' and 'answer'. "
            "Do not include any markdown backticks or extra explanation, return only the raw JSON array."
        )
        
        system_instruction = (
            "You are 'Sophy Study Companion', an adaptive Filipino tutor. "
            "You construct high-quality flashcards specifically tuned to the Filipino context using English, Tagalog, or Taglish. "
            "Your output must be structured, clear, and verify all formatting rules before outputting."
        )

        try:
            if not self.client:
                raise ValueError("GenAI client not initialized.")
                
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7
                )
            )
            raw_text = response.text.strip()
            # Strip markdown formatting if generated
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()
            
            cards = json.loads(raw_text)
            
            verified_cards = []
            for card in cards:
                if "question" in card and "answer" in card:
                    database.add_flashcard(self.db_path, user_id, card["question"], card["answer"])
                    verified_cards.append(card)
            return verified_cards
        except Exception as e:
            print("Failed to generate flashcards:", e)
            fallback = [
                {
                    "question": f"Ano ang core definition ng {topic} in {subject}?",
                    "answer": f"It is the main mechanism to handle learning optimization inside {subject} structures."
                },
                {
                    "question": f"Paano natin mai-apply ang {topic} sa practical problems?",
                    "answer": "We validate parameters locally and measure validation metric improvements."
                }
            ]
            for card in fallback:
                database.add_flashcard(self.db_path, user_id, card["question"], card["answer"])
            return fallback

    def generate_flashcards_from_text(self, user_id: int, subject: str, topic: str, text_content: str, count: int = 3, language: str = "Taglish") -> List[Dict[str, str]]:
        """
        Sophy Document Pipeline:
        1. Takes parsed document text and structures a prompt to generate flashcards.
        2. Verifies formatting and outputs JSON.
        3. Saves to SQLite.
        """
        truncated_text = text_content[:4000]
        
        prompt = (
            f"Generate exactly {count} study flashcards based on the following lecture module contents:\n"
            f"--- Lecture Module Content ---\n{truncated_text}\n------------------------------\n"
            f"Subject: {subject}\n"
            f"Topic: {topic}\n"
            f"Language: {language}\n"
            "Format the output strictly as a JSON array of objects, where each object has "
            "keys 'question' and 'answer'. "
            "Do not include any markdown backticks or extra explanation, return only the raw JSON array."
        )
        
        system_instruction = (
            "You are 'Sophy Study Companion', an adaptive Filipino tutor. "
            "You extract core key facts and terms from the provided lecture text and construct flashcards "
            "specifically tuned to the student using English, Tagalog, or Taglish."
        )

        try:
            if not self.client:
                raise ValueError("GenAI client not initialized.")
                
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.6
                )
            )
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()
            
            cards = json.loads(raw_text)
            
            verified_cards = []
            for card in cards:
                if "question" in card and "answer" in card:
                    database.add_flashcard(self.db_path, user_id, card["question"], card["answer"])
                    verified_cards.append(card)
            return verified_cards
        except Exception as e:
            print("Failed to generate flashcards from text:", e)
            fallback = [
                {
                    "question": f"Ano ang primary point discussed in the {topic} slide?",
                    "answer": f"It details how we optimize elements in the context of {subject}."
                }
            ]
            for card in fallback:
                database.add_flashcard(self.db_path, user_id, card["question"], card["answer"])
            return fallback
