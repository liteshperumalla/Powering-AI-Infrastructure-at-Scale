// MongoDB initialization script for Infra Mind
// This script creates the database and initial collections

// Switch to the infra_mind database
db = db.getSiblingDB('infra_mind');

// Create collections with validation
db.createCollection('assessments', {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["user_id", "status", "created_at"],
            properties: {
                user_id: { bsonType: "string" },
                status: { bsonType: "string" },
                created_at: { bsonType: "date" }
            }
        }
    }
});

db.createCollection('recommendations', {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["assessment_id", "agent_name", "created_at"],
            properties: {
                assessment_id: { bsonType: "string" },
                agent_name: { bsonType: "string" },
                created_at: { bsonType: "date" }
            }
        }
    }
});

db.createCollection('users', {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["email", "created_at"],
            properties: {
                email: { bsonType: "string" },
                created_at: { bsonType: "date" }
            }
        }
    }
});

db.createCollection('reports');
db.createCollection('metrics');
db.createCollection('agent_metrics');

// Create indexes for better performance
db.assessments.createIndex({ "user_id": 1, "status": 1 });
db.assessments.createIndex({ "created_at": -1 });
db.recommendations.createIndex({ "assessment_id": 1, "agent_name": 1 });
db.users.createIndex({ "email": 1 }, { unique: true });
db.metrics.createIndex({ "timestamp": -1 });

print("✅ Infra Mind database initialized successfully!");
print("📊 Collections created:");
print("   • assessments");
print("   • recommendations");
print("   • users");
print("   • reports");
print("   • metrics");
print("   • agent_metrics");
print("🔍 Indexes created for optimal performance");