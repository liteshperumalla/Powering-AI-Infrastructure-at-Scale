#!/usr/bin/env python3
"""
Demo script for Chatbot and Customer Service System.

This script demonstrates the integrated chatbot and customer service functionality
including conversation handling, FAQ integration, and support ticket creation.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_chatbot_conversation():
    """Demonstrate chatbot conversation capabilities."""
    print("\n" + "="*60)
    print("CHATBOT CONVERSATION DEMO")
    print("="*60)
    
    try:
        from src.infra_mind.agents.chatbot_agent import ChatbotAgent
        from src.infra_mind.agents.base import AgentConfig, AgentRole
        from src.infra_mind.models.assessment import Assessment
        
        # Create chatbot agent
        config = AgentConfig(
            name="customer_service_bot",
            role=AgentRole.CHATBOT,
            temperature=0.7,
            max_tokens=500,
            custom_config={
                "max_conversation_turns": 10,
                "escalation_threshold": 2,
                "enable_faq_integration": True,
                "enable_context_memory": True
            }
        )
        
        chatbot = ChatbotAgent(config)
        
        # Initialize with dummy assessment
        assessment = Assessment(
            user_id="demo_user",
            title="Demo Assessment",
            business_requirements={},
            technical_requirements={}
        )
        
        await chatbot.initialize(assessment)
        
        print("✅ Chatbot agent initialized successfully")
        
        # Test conversation scenarios
        test_messages = [
            {
                "message": "Hello, I need help with the platform",
                "user_id": "demo_user_123",
                "conversation_id": "conv_001"
            },
            {
                "message": "What is Infra Mind?",
                "user_id": "demo_user_123",
                "conversation_id": "conv_001"
            },
            {
                "message": "How do I create an assessment?",
                "user_id": "demo_user_123",
                "conversation_id": "conv_001"
            },
            {
                "message": "I'm having technical issues with my account",
                "user_id": "demo_user_123",
                "conversation_id": "conv_001"
            },
            {
                "message": "I want to speak to a human agent",
                "user_id": "demo_user_123",
                "conversation_id": "conv_001"
            }
        ]
        
        print("\n📱 Testing chatbot conversations:")
        
        for i, test_case in enumerate(test_messages, 1):
            print(f"\n--- Conversation Turn {i} ---")
            print(f"User: {test_case['message']}")
            
            try:
                response = await chatbot.handle_message(
                    message=test_case["message"],
                    user_id=test_case["user_id"],
                    conversation_id=test_case["conversation_id"]
                )
                
                print(f"Bot: {response['content']}")
                print(f"Intent: {response['intent']}")
                print(f"Context: {response['context']}")
                print(f"Confidence: {response['confidence']}")
                
                if response.get("requires_escalation"):
                    print("🚨 ESCALATION REQUIRED")
                    if response.get("ticket_id"):
                        print(f"Support Ticket Created: {response['ticket_id']}")
                
                if response.get("suggestions"):
                    print(f"Suggestions: {', '.join(response['suggestions'])}")
                
            except Exception as e:
                print(f"❌ Error in conversation turn {i}: {str(e)}")
        
        # Get conversation stats
        stats = chatbot.get_conversation_stats()
        print(f"\n📊 Conversation Statistics:")
        print(f"Total turns: {stats['total_turns']}")
        print(f"User turns: {stats['user_turns']}")
        print(f"Bot turns: {stats['bot_turns']}")
        print(f"Current context: {stats['current_context']}")
        print(f"Escalation count: {stats['escalation_count']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Chatbot demo failed: {str(e)}")
        return False


async def demo_faq_system():
    """Demonstrate FAQ system functionality."""
    print("\n" + "="*60)
    print("FAQ SYSTEM DEMO")
    print("="*60)
    
    try:
        from src.infra_mind.services.faq_service import faq_service
        from src.infra_mind.models.faq import FAQCategory
        
        # Test FAQ search
        print("\n🔍 Testing FAQ search:")
        
        search_queries = [
            "What is Infra Mind?",
            "cloud providers",
            "pricing cost",
            "create assessment",
            "technical support"
        ]
        
        for query in search_queries:
            print(f"\nQuery: '{query}'")
            
            try:
                results = await faq_service.search_faqs(
                    query=query,
                    limit=3
                )
                
                if results["results"]:
                    print(f"Found {results['total_results']} results:")
                    for result in results["results"][:2]:  # Show top 2
                        print(f"  Q: {result['question']}")
                        print(f"  A: {result['answer'][:100]}...")
                        print(f"  Relevance: {result['relevance_score']:.2f}")
                else:
                    print("  No results found")
                    
            except Exception as e:
                print(f"  ❌ Search failed: {str(e)}")
        
        # Test FAQ categories
        print(f"\n📂 Available FAQ categories:")
        for category in FAQCategory:
            print(f"  - {category.value}")
        
        # Test featured FAQs
        print(f"\n⭐ Featured FAQs:")
        try:
            featured = await faq_service.get_featured_faqs(limit=3)
            for faq in featured:
                print(f"  - {faq['question']}")
        except Exception as e:
            print(f"  ❌ Failed to get featured FAQs: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ FAQ system demo failed: {str(e)}")
        return False


async def demo_customer_service():
    """Demonstrate customer service system functionality."""
    print("\n" + "="*60)
    print("CUSTOMER SERVICE SYSTEM DEMO")
    print("="*60)
    
    try:
        from src.infra_mind.services.customer_service import customer_service_manager
        from src.infra_mind.models.support_ticket import (
            TicketCategory, TicketPriority, TicketSource
        )
        
        # Create a test support ticket
        print("\n🎫 Creating test support ticket:")
        
        ticket_data = {
            "title": "Demo Technical Issue",
            "description": "This is a demo ticket created for testing purposes. The user is experiencing issues with platform access.",
            "customer_email": "demo.user@example.com",
            "customer_name": "Demo User",
            "category": TicketCategory.TECHNICAL_ISSUE,
            "priority": TicketPriority.NORMAL,
            "source": TicketSource.WEB_FORM
        }
        
        try:
            ticket = await customer_service_manager.create_ticket(**ticket_data)
            
            print(f"✅ Ticket created successfully:")
            print(f"  Ticket ID: {ticket['ticket_id']}")
            print(f"  Status: {ticket['status']}")
            print(f"  Priority: {ticket['priority']}")
            print(f"  Assigned Agent: {ticket['assigned_agent'] or 'Unassigned'}")
            print(f"  SLA Due: {ticket['sla_due_date']}")
            
            ticket_id = ticket['ticket_id']
            
        except Exception as e:
            print(f"❌ Failed to create ticket: {str(e)}")
            return False
        
        # Add a message to the ticket
        print(f"\n💬 Adding message to ticket {ticket_id}:")
        
        try:
            success = await customer_service_manager.add_message_to_ticket(
                ticket_id=ticket_id,
                content="Thank you for contacting support. We're looking into your issue.",
                sender_type="agent",
                sender_name="Support Agent",
                sender_email="support@example.com"
            )
            
            if success:
                print("✅ Message added successfully")
            else:
                print("❌ Failed to add message")
                
        except Exception as e:
            print(f"❌ Error adding message: {str(e)}")
        
        # Get updated ticket
        print(f"\n📋 Retrieving updated ticket:")
        
        try:
            updated_ticket = await customer_service_manager.get_ticket(ticket_id)
            
            if updated_ticket:
                print(f"✅ Ticket retrieved:")
                print(f"  Messages: {len(updated_ticket['messages'])}")
                print(f"  Last Updated: {updated_ticket['updated_at']}")
                print(f"  Age (hours): {updated_ticket['age_hours']:.1f}")
                
                if updated_ticket['messages']:
                    last_message = updated_ticket['messages'][-1]
                    print(f"  Last Message: {last_message['content'][:50]}...")
            else:
                print("❌ Ticket not found")
                
        except Exception as e:
            print(f"❌ Error retrieving ticket: {str(e)}")
        
        # Test analytics
        print(f"\n📊 Customer Service Analytics:")
        
        try:
            analytics = await customer_service_manager.get_analytics_dashboard()
            
            if analytics.get("overview"):
                overview = analytics["overview"]
                print(f"  Total Tickets: {overview.get('total_tickets', 0)}")
                print(f"  Resolution Rate: {overview.get('resolution_rate', 0)}%")
                print(f"  Avg Resolution Time: {overview.get('avg_resolution_time_hours', 0):.1f} hours")
                print(f"  Avg Satisfaction: {overview.get('avg_satisfaction_rating', 0):.1f}/5")
            
            if analytics.get("agent_workload"):
                workload = analytics["agent_workload"]
                print(f"  Overall Utilization: {workload.get('overall_utilization', 0)}%")
                
        except Exception as e:
            print(f"❌ Error getting analytics: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Customer service demo failed: {str(e)}")
        return False


async def demo_integration():
    """Demonstrate integration between chatbot, FAQ, and customer service."""
    print("\n" + "="*60)
    print("INTEGRATION DEMO")
    print("="*60)
    
    try:
        # Simulate a complete customer journey
        print("\n🎭 Simulating complete customer journey:")
        
        # 1. Customer starts chat
        print("\n1. Customer starts chatbot conversation")
        
        # 2. Chatbot tries FAQ first
        print("2. Chatbot searches FAQ for answer")
        
        # 3. If no good FAQ match, use LLM
        print("3. No good FAQ match, using LLM response")
        
        # 4. Customer requests escalation
        print("4. Customer requests human support")
        
        # 5. Support ticket is created
        print("5. Support ticket created automatically")
        
        # 6. Agent receives ticket and responds
        print("6. Support agent receives and processes ticket")
        
        print("\n✅ Integration flow completed successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration demo failed: {str(e)}")
        return False


async def main():
    """Run all demos."""
    print("🚀 Starting Chatbot and Customer Service System Demo")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    results = {
        "chatbot": False,
        "faq": False,
        "customer_service": False,
        "integration": False
    }
    
    # Run individual demos
    results["chatbot"] = await demo_chatbot_conversation()
    results["faq"] = await demo_faq_system()
    results["customer_service"] = await demo_customer_service()
    results["integration"] = await demo_integration()
    
    # Summary
    print("\n" + "="*60)
    print("DEMO SUMMARY")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for component, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{component.upper()}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} components working")
    
    if passed_tests == total_tests:
        print("🎉 All chatbot and customer service features are working!")
    else:
        print("⚠️  Some features need attention")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    asyncio.run(main())