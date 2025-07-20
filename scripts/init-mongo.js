// MongoDB initialization script
// This script runs when MongoDB container starts for the first time

// Switch to the infra_mind database
db = db.getSiblingDB('infra_mind');

// Create a user for the application
db.createUser({
    user: 'infra_mind_user',
    pwd: 'infra_mind_password',
    roles: [
        {
            role: 'readWrite',
            db: 'infra_mind'
        }
    ]
});

// Create initial collections with validation (optional)
db.createCollection('users');
db.createCollection('assessments');
db.createCollection('recommendations');
db.createCollection('reports');
db.createCollection('workflow_states');
db.createCollection('metrics');
db.createCollection('web_research_data');

print('MongoDB initialization completed for Infra Mind');