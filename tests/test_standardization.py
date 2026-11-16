"""
Standardization Test Suite (Requirements 1 to 6):
Validates the exact 6 core requirements:
1. Context Sharing & Hover Blackboard
2. External Tool Integration via MCP
3. Structured Output using Pydantic (JSON, Table, Markdown)
4. Agentic Design Patterns Evaluation Matrix
5. Task Monitoring & Logging using Callbacks
6. Agent-to-Agent (A2A) Protocol & CrewAI + Google ADK Interoperability
"""

import pytest
from backend.agents.blackboard import HoverBlackboard, compare_messaging_architectures
from backend.tools.mcp_tools import ClinicalGuidelinesMCPTool, MedicalCalculatorMCPTool
from backend.models.structured_report import StructuredClinicalReport
from backend.agents.patterns import evaluate_agentic_design_patterns
from backend.agents.callbacks import TelemetryMonitoringCallback
from backend.agents.a2a_protocol import A2AMessage, A2APerformative, A2ADispatcher
from backend.agents.crewai_adk_interop import run_crewai_adk_interop_pipeline
from backend.agents.triage_agent import TriageAgent
from backend.models.patient import PatientIntake, VitalSigns, ConsciousnessLevel, Gender


def test_requirement_1_hover_blackboard_and_messaging():
    """Requirement 1: Context Sharing, State Updates & Hover Blackboard Architecture."""
    bb = HoverBlackboard()
    triggered = []
    
    # Register reactive listener
    bb.subscribe("TRIAGE_POSTED", lambda entry: triggered.append(entry.entry_id))
    bb.post("TRIAGE_POSTED", "TriageAgent", {"patient_id": "P-101", "severity": 85})
    assert len(triggered) == 1
    
    # Test comparative evaluation of messaging architectures
    comp = compare_messaging_architectures()
    assert len(comp["patterns_evaluated"]) >= 3
    assert "verdict" in comp


def test_requirement_2_mcp_clinical_tools():
    """Requirement 2: External Tool Integration using Model Context Protocol (MCP)."""
    # 1. Guidelines Lookup Tool
    kb_tool = ClinicalGuidelinesMCPTool()
    kb_res = kb_tool.execute("respiratory_distress")
    assert kb_res["status"] == "SUCCESS"
    assert "VENTILATOR" in kb_res["protocol"]["required_equipment"]
    assert kb_tool.get_mcp_schema().name == "clinical_guidelines_lookup"
    
    # 2. Medical Calculator Tool (NEWS2)
    calc_tool = MedicalCalculatorMCPTool()
    calc_res = calc_tool.execute("NEWS2", {
        "heart_rate": 140, "systolic_bp": 75, "oxygen_saturation": 82.0,
        "respiratory_rate": 34, "consciousness_level": "VOICE", "temperature_celsius": 39.2
    })
    assert calc_res["calculated_score"] >= 12
    assert calc_res["clinical_risk_tier"] == "HIGH_CRITICAL"
    assert calc_tool.get_mcp_schema().name == "medical_calculator"


def test_requirement_3_structured_pydantic_output():
    """Requirement 3: Structured Output using Pydantic (JSON, Table, Markdown)."""
    patient = PatientIntake(
        patient_id="P-PYD-01",
        name="James Logan",
        age=45,
        gender=Gender.MALE,
        chief_complaint="Acute severe chest pressure",
        symptoms=["Chest pain", "Shortness of breath"],
        vitals=VitalSigns(
            heart_rate=125, systolic_bp=85, diastolic_bp=55,
            oxygen_saturation=90.0, respiratory_rate=28,
            temperature_celsius=37.2, consciousness_level=ConsciousnessLevel.ALERT
        )
    )
    triage = TriageAgent().evaluate(patient)
    report = StructuredClinicalReport.from_workflow(patient=patient, triage=triage)
    
    # Format A: Structured JSON
    json_out = report.model_dump_json()
    assert "P-PYD-01" in json_out
    assert report.severity_score >= 0
    
    # Format B: Structured Markdown
    md_out = report.to_structured_markdown()
    assert "### 📋 Clinical Summary Report" in md_out
    assert "James Logan" in md_out
    
    # Format C: Structured Tabular Row Dictionary
    row_dict = report.to_structured_table_row()
    assert row_dict["Patient ID"] == "P-PYD-01"
    assert "NEWS2" in row_dict


def test_requirement_4_agentic_design_patterns():
    """Requirement 4: Agentic Design Patterns Implementation & Comparative Evaluation."""
    patterns = evaluate_agentic_design_patterns()
    assert len(patterns) == 4
    pattern_names = [p.pattern_name for p in patterns]
    assert "Hover Blackboard Pattern" in pattern_names
    assert "Hierarchical Supervisor Pattern" in pattern_names
    assert any("Evaluator-Optimizer" in p for p in pattern_names)
    assert "Sequential Pipeline Pattern" in pattern_names


def test_requirement_5_callback_monitoring():
    """Requirement 5: Task Monitoring & Logging using Callback Functions."""
    monitor = TelemetryMonitoringCallback()
    
    # Test lifecycle callbacks
    monitor.on_agent_start("TriageAgent", {"patient_id": "P-101"})
    monitor.on_tool_start("TriageAgent", "medical_calculator", {"calc_type": "NEWS2"})
    monitor.on_tool_end("TriageAgent", "medical_calculator", {"calculated_score": 12})
    monitor.on_agent_finish("TriageAgent", {"status": "SUCCESS"}, execution_time_ms=18.5)
    monitor.on_state_change("P-101", "WAITING", "ALLOCATED", "Priority Knapsack Solution")
    
    timeline = monitor.get_timeline(limit=10)
    assert len(timeline) == 5
    events = [s["event"] for s in timeline]
    assert "AGENT_START" in events
    assert "TOOL_INVOKED" in events
    assert "TOOL_COMPLETED" in events
    assert "AGENT_FINISH" in events
    assert "STATE_MUTATION" in events


def test_requirement_6_a2a_protocol_and_interop():
    """Requirement 6: Agent to Agent Communication using A2A Protocol & CrewAI + Google ADK."""
    # 1. Test A2A Dispatcher with FIPA performatives
    dispatcher = A2ADispatcher()
    
    def mock_receiver(msg: A2AMessage) -> A2AMessage:
        return A2AMessage(
            conversation_id=msg.conversation_id,
            sender_id="ADK_Agent",
            receiver_id=msg.sender_id,
            performative=A2APerformative.AGREE,
            payload={"status": "CONTRACT_ACCEPTED"}
        )
        
    dispatcher.register_agent("ADK_Agent", mock_receiver)
    req = A2AMessage(
        conversation_id="CONV-TEST-01",
        sender_id="CrewAI_Agent",
        receiver_id="ADK_Agent",
        performative=A2APerformative.REQUEST,
        payload={"task": "ALLOCATE_BED"}
    )
    reply = dispatcher.send(req)
    assert reply is not None
    assert reply.performative == A2APerformative.AGREE
    
    # 2. Test End-to-End Interop Pipeline
    patient = PatientIntake(
        patient_id="P-INTEROP-1",
        name="Sarah Connor",
        age=42,
        gender=Gender.FEMALE,
        chief_complaint="Severe shortness of breath",
        symptoms=["Cyanosis"],
        vitals=VitalSigns(
            heart_rate=142, systolic_bp=74, diastolic_bp=42,
            oxygen_saturation=79.0, respiratory_rate=36,
            temperature_celsius=38.5, consciousness_level=ConsciousnessLevel.VOICE
        )
    )
    res = run_crewai_adk_interop_pipeline(patient)
    assert res["interoperability_status"] == "SUCCESSFUL_A2A_EXCHANGE"
    assert "CrewAI" in res["frameworks_used"]
    assert "Google ADK" in res["frameworks_used"]
    assert res["a2a_message_count"] >= 1
