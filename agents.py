"""
MediScan AI - Multi-Agent System
4 coordinated agents powered by LangChain + Groq
"""

import streamlit as st
from langchain_core.tools import Tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate

from database import (
    search_medicine, check_interaction, get_all_medicine_names,
    find_medicine_by_name, MEDICINES, INTERACTIONS, PHARMACIES
)


# ============================================================
# LLM SETUP
# ============================================================
@st.cache_resource(show_spinner=False)
def get_llm():
    """Get Groq LLM using API key from session state."""
    api_key = st.session_state.get("groq_api_key", "")
    if not api_key:
        return None
    return ChatGroq(
        groq_api_key=api_key,
        model_name="llama-3.1-8b-instant",
        temperature=0.3,
        max_tokens=700
    )


# ============================================================
# TOOLS
# ============================================================
def medicine_lookup_tool(query: str) -> str:
    results = search_medicine(query)
    if not results:
        return f"No medicine found matching '{query}'."
    output = []
    for med in results[:2]:
        output.append(
            f"**{med['name']}** (Generic: {med['generic']})\n"
            f"- Category: {med['category']}\n"
            f"- Uses: {med['uses']}\n"
            f"- Side Effects: {med['side_effects']}\n"
            f"- Dosage: {med['dosage']}\n"
            f"- Interactions: {med['interactions']}"
        )
    return "\n\n".join(output)


def interaction_check_tool(query: str) -> str:
    """Input format: 'DrugA, DrugB'"""
    parts = [p.strip() for p in query.split(",")]
    if len(parts) < 2:
        return "Please provide two medicines separated by comma: 'DrugA, DrugB'"
    result = check_interaction(parts[0], parts[1])
    return (f"Severity: {result['severity']}\n"
            f"Risk: {result['risk']}\n"
            f"Action: {result['action']}")


def list_medicines_tool(query: str = "") -> str:
    names = get_all_medicine_names()
    return f"Available medicines ({len(names)}): " + ", ".join(names)


def list_pharmacies_tool(query: str = "") -> str:
    result = []
    for p in PHARMACIES[:5]:
        result.append(f"🏪 {p['name']} ({p['area']}, {p['city']}) — ⭐{p['rating']} — {p['phone']}")
    return "\n".join(result)


def severity_analyzer_tool(query: str) -> str:
    """Input: comma-separated symptoms"""
    symptoms = [s.strip().lower() for s in query.split(",")]
    severe_flags = ["chest pain", "breathing difficulty", "unconscious",
                    "severe bleeding", "paralysis", "seizure"]
    moderate_flags = ["fever", "vomiting", "diarrhea", "rash", "dizziness"]
    severity, advice = "MILD", "Monitor symptoms. Consult doctor if persists > 48 hours."
    for s in symptoms:
        for flag in severe_flags:
            if flag in s:
                return "Severity: SEVERE\nAdvice: 🚨 EMERGENCY! Go to nearest hospital immediately."
    for s in symptoms:
        for flag in moderate_flags:
            if flag in s:
                severity = "MODERATE"
                advice = "Consult a doctor within 24 hours. Take rest and stay hydrated."
    return f"Severity: {severity}\nAdvice: {advice}"


# ============================================================
# AGENT FACTORY
# ============================================================
def _build_agent(llm, tools, role_desc, name):
    prompt = PromptTemplate.from_template(f"""
You are the {name} for MediScan AI.
{role_desc}

IMPORTANT: Only use tools to get information. Never make up medicine data.
Always add a medical disclaimer. Answer concisely.

Available tools:
{{tools}}

Tool names: {{tool_names}}

Question: {{input}}

Use this format:
Thought: what should I do?
Action: tool name
Action Input: input
Observation: result
... (repeat if needed)
Thought: I now know the final answer
Final Answer: your answer

{{agent_scratchpad}}
""")
    agent = create_react_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=False,
                         handle_parsing_errors=True, max_iterations=5)


def create_medicine_agent(llm):
    tools = [
        Tool(name="MedicineLookup", func=medicine_lookup_tool,
             description="Look up medicine info by name. Input: medicine name."),
        Tool(name="ListMedicines", func=list_medicines_tool,
             description="List all medicines. Input: empty string."),
    ]
    return _build_agent(llm, tools,
        "You provide accurate medicine information from our verified database.",
        "Medicine Info Agent")


def create_interaction_agent(llm):
    tools = [
        Tool(name="InteractionCheck", func=interaction_check_tool,
             description="Check interaction between two drugs. Input: 'DrugA, DrugB'"),
    ]
    return _build_agent(llm, tools,
        "You check if two or more medicines are safe to take together.",
        "Drug Interaction Agent")


def create_symptom_agent(llm):
    tools = [
        Tool(name="SeverityAnalyzer", func=severity_analyzer_tool,
             description="Analyze symptoms severity. Input: comma-separated symptoms."),
        Tool(name="MedicineLookup", func=medicine_lookup_tool,
             description="Look up medicine by name."),
    ]
    return _build_agent(llm, tools,
        "You analyze symptoms, assess severity, and suggest general guidance. Never diagnose.",
        "Symptom Triage Agent")


def create_pharmacy_agent(llm):
    tools = [
        Tool(name="ListPharmacies", func=list_pharmacies_tool,
             description="List verified pharmacies. Input: empty string."),
    ]
    return _build_agent(llm, tools,
        "You help users find verified pharmacies.",
        "Pharmacy Finder Agent")


# ============================================================
# COORDINATOR (Master Agent / Router)
# ============================================================
class CoordinatorAgent:
    """Routes queries to the right specialist agent."""

    def __init__(self, llm):
        self.llm = llm
        self.medicine_agent = create_medicine_agent(llm)
        self.interaction_agent = create_interaction_agent(llm)
        self.symptom_agent = create_symptom_agent(llm)
        self.pharmacy_agent = create_pharmacy_agent(llm)

    def route(self, query: str) -> str:
        q = query.lower()
        interaction_kw = ["interaction", "together", "combine", "mix", "saath", "sath", "safe to take"]
        symptom_kw = ["symptom", "feel", "pain", "fever", "headache", "vomiting",
                      "dizzy", "sick", "tabiyat", "dard", "bukhar"]
        pharmacy_kw = ["pharmacy", "medical store", "chemist", "dukaan", "shop", "near me"]

        med_names_lower = [m["name"].lower() for m in MEDICINES]
        generic_names_lower = [m["generic"].lower().split()[0] for m in MEDICINES]
        all_names = med_names_lower + generic_names_lower
        found_meds = sum(1 for name in all_names if name in q)

        if any(kw in q for kw in pharmacy_kw):
            return self._run(self.pharmacy_agent, query, "🏪 **Pharmacy Finder Agent**")
        if any(kw in q for kw in interaction_kw) or found_meds >= 2:
            return self._run(self.interaction_agent, query, "⚗️ **Interaction Agent**")
        if any(kw in q for kw in symptom_kw):
            return self._run(self.symptom_agent, query, "🩺 **Symptom Triage Agent**")
        return self._run(self.medicine_agent, query, "💊 **Medicine Info Agent**")

    def _run(self, agent, query, label):
        try:
            result = agent.invoke({"input": query})
            return f"{label}\n\n{result['output']}"
        except Exception as e:
            return f"⚠️ {label} error: {str(e)}"


# ============================================================
# AGENT INFO (for UI)
# ============================================================
AGENT_INFO = [
    {"name": "Coordinator", "icon": "🎯",
     "desc": "Routes queries to the right specialist",
     "handles": "All incoming queries"},
    {"name": "Medicine Info", "icon": "💊",
     "desc": "Looks up medicine details from database",
     "handles": "'What is Panadol?'"},
    {"name": "Interaction", "icon": "⚗️",
     "desc": "Checks if two drugs are safe together",
     "handles": "'Warfarin + Aspirin safe?'"},
    {"name": "Symptom Triage", "icon": "🩺",
     "desc": "Assesses symptom severity",
     "handles": "'I have fever and headache'"},
    {"name": "Pharmacy Finder", "icon": "🏪",
     "desc": "Finds verified pharmacies nearby",
     "handles": "'Pharmacies near me'"},
]
