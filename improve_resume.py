
from agents.resume_analyser import ResumeAnalysisAgent

class Improver(ResumeAnalysisAgent):
    def __init__(self):
        pass
    
    
    def improve_resume(self, improvement_areas, target_role=""):
        """Generate suggestions to improve the resume"""
        if not self.resume_text:
            return {}
        
        try:
           
            improvements = {}
            
  
            for area in improvement_areas:
           
                if area == "Skills Highlighting" and self.resume_weaknesses:
                    skill_improvements = {
                        "description": "Your resume needs to better highlight key skills that are important for the role.",
                        "specific": []
                    }
                 
                    before_after_examples = {}
                    
                    for weakness in self.resume_weaknesses:
                        skill_name = weakness.get("skill", "")
                        if "suggestions" in weakness and weakness["suggestions"]:
                            for suggestion in weakness["suggestions"]:
                                skill_improvements["specific"].append(f"**{skill_name}**: {suggestion}")
                        
                        if "example" in weakness and weakness["example"]:
                       
                            resume_chunks = self.resume_text.split('\n\n')
                            relevant_chunk = ""
                            
                            
                            for chunk in resume_chunks:
                                if skill_name.lower() in chunk.lower() or "experience" in chunk.lower():
                                    relevant_chunk = chunk
                                    break
                            
                            if relevant_chunk:
                                before_after_examples = {
                                    "before": relevant_chunk.strip(),
                                    "after": relevant_chunk.strip() + "\n• " + weakness["example"]
                                }
                    
                    if before_after_examples:
                        skill_improvements["before_after"] = before_after_examples
                    
                    improvements["Skills Highlighting"] = skill_improvements
 
            remaining_areas = [area for area in improvement_areas if area not in improvements]
            
            if remaining_areas:
                llm = ChatOpenAI(model="gpt-4o", api_key=self.api_key)
                
                # Create a context with resume analysis and weaknesses
                weaknesses_text = ""
                if self.resume_weaknesses:
                    weaknesses_text = "Resume Weaknesses:\n"
                    for i, weakness in enumerate(self.resume_weaknesses):
                        weaknesses_text += f"{i+1}. {weakness['skill']}: {weakness['detail']}\n"
                        if "suggestions" in weakness:
                            for j, sugg in enumerate(weakness["suggestions"]):
                                weaknesses_text += f"   - {sugg}\n"
                
                context = f"""
                Resume Content:
                {self.resume_text}
                
                Skills to focus on: {', '.join(self.extracted_skills)}
                
                Strengths: {', '.join(self.analysis_result.get('strengths', []))}
                
                Areas for improvement: {', '.join(self.analysis_result.get('missing_skills', []))}
                
                {weaknesses_text}
                
                Target role: {target_role if target_role else "Not specified"}
                """
                
                prompt = f"""
                Provide detailed suggestions to improve this resume in the following areas: {', '.join(remaining_areas)}.
                
                {context}
                
                For each improvement area, provide:
                1. A general description of what needs improvement
                2. 3-5 specific actionable suggestions
                3. Where relevant, provide a before/after example
                
                Format the response as a JSON object with improvement areas as keys, each containing:
                - "description": general description
                - "specific": list of specific suggestions
                - "before_after": (where applicable) a dict with "before" and "after" examples
                
                Only include the requested improvement areas that aren't already covered.
                Focus particularly on addressing the resume weaknesses identified.
                """
                
                response = llm.invoke(prompt)
                
                # Try to parse JSON from the response
                ai_improvements = {}
                
                # Extract from markdown code blocks if present
                json_match = re.search(r'```(?:json)?\s*([\s\S]+?)\s*```', response.content)
                if json_match:
                    try:
                        ai_improvements = json.loads(json_match.group(1))
                        # Merge with existing improvements
                        improvements.update(ai_improvements)
                    except json.JSONDecodeError:
                        pass
                
                # If JSON parsing failed, create structured output manually
                if not ai_improvements:
                    sections = response.content.split("##")
                    
                    for section in sections:
                        if not section.strip():
                            continue
                            
                        lines = section.strip().split("\n")
                        area = None
                        
                        for line in lines:
                            if not area and line.strip():
                                area = line.strip()
                                improvements[area] = {
                                    "description": "",
                                    "specific": []
                                }
                            elif area and "specific" in improvements[area]:
                                if line.strip().startswith("- "):
                                    improvements[area]["specific"].append(line.strip()[2:])
                                elif not improvements[area]["description"]:
                                    improvements[area]["description"] += line.strip()
            
            # Ensure all requested areas are included
            for area in improvement_areas:
                if area not in improvements:
                    improvements[area] = {
                        "description": f"Improvements needed in {area}",
                        "specific": ["Review and enhance this section"]
                    }
            
            return improvements
        
        except Exception as e:
            print(f"Error generating resume improvements: {e}")
            return {area: {"description": "Error generating suggestions", "specific": []} for area in improvement_areas}