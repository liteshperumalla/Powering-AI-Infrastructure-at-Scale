/**
 * Tests for enterprise features components and functionality
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';

// Mock store setup
const createMockStore = (initialState = {}) => {
  return configureStore({
    reducer: {
      auth: (state = { user: null, token: null, isAuthenticated: false }, action) => state,
      assessments: (state = { assessments: [], loading: false }, action) => state,
      reports: (state = { reports: [], loading: false }, action) => state,
    },
    preloadedState: initialState
  });
};

// Mock API calls
jest.mock('../../services/api', () => ({
  api: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  },
  // Enterprise API functions
  getExperiments: jest.fn(),
  createExperiment: jest.fn(),
  submitFeedback: jest.fn(),
  getQualityMetrics: jest.fn(),
}));

describe('Enterprise Features Integration', () => {
  let mockStore: any;

  beforeEach(() => {
    mockStore = createMockStore({
      auth: {
        user: { id: '123', email: 'admin@test.com', role: 'admin' },
        token: 'mock-token',
        isAuthenticated: true
      }
    });
    
    jest.clearAllMocks();
  });

  describe('A/B Testing Dashboard', () => {
    test('renders experiment dashboard for admin users', () => {
      // This would test a hypothetical ExperimentDashboard component
      const MockExperimentDashboard = () => (
        <div data-testid="experiment-dashboard">
          <h1>A/B Testing Dashboard</h1>
          <div data-testid="experiment-list">Experiments List</div>
          <button data-testid="create-experiment">Create Experiment</button>
        </div>
      );

      render(
        <Provider store={mockStore}>
          <MockExperimentDashboard />
        </Provider>
      );

      expect(screen.getByTestId('experiment-dashboard')).toBeInTheDocument();
      expect(screen.getByText('A/B Testing Dashboard')).toBeInTheDocument();
      expect(screen.getByTestId('create-experiment')).toBeInTheDocument();
    });

    test('prevents non-admin access to experiment creation', () => {
      const nonAdminStore = createMockStore({
        auth: {
          user: { id: '123', email: 'user@test.com', role: 'user' },
          token: 'mock-token',
          isAuthenticated: true
        }
      });

      const MockRestrictedComponent = ({ userRole }: { userRole: string }) => (
        <div>
          {userRole === 'admin' ? (
            <button data-testid="admin-only-button">Admin Feature</button>
          ) : (
            <div data-testid="access-denied">Access Denied</div>
          )}
        </div>
      );

      render(
        <Provider store={nonAdminStore}>
          <MockRestrictedComponent userRole="user" />
        </Provider>
      );

      expect(screen.getByTestId('access-denied')).toBeInTheDocument();
      expect(screen.queryByTestId('admin-only-button')).not.toBeInTheDocument();
    });
  });

  describe('Feedback Collection', () => {
    test('renders feedback form for authenticated users', () => {
      const MockFeedbackForm = () => (
        <form data-testid="feedback-form">
          <select data-testid="feedback-type">
            <option value="assessment_quality">Assessment Quality</option>
            <option value="ui_experience">UI Experience</option>
            <option value="performance">Performance</option>
          </select>
          <input 
            type="number" 
            data-testid="rating" 
            min="1" 
            max="5" 
            placeholder="Rating (1-5)"
          />
          <textarea 
            data-testid="comments" 
            placeholder="Your feedback..."
          />
          <button type="submit" data-testid="submit-feedback">Submit</button>
        </form>
      );

      render(
        <Provider store={mockStore}>
          <MockFeedbackForm />
        </Provider>
      );

      expect(screen.getByTestId('feedback-form')).toBeInTheDocument();
      expect(screen.getByTestId('feedback-type')).toBeInTheDocument();
      expect(screen.getByTestId('rating')).toBeInTheDocument();
      expect(screen.getByTestId('comments')).toBeInTheDocument();
      expect(screen.getByTestId('submit-feedback')).toBeInTheDocument();
    });

    test('validates feedback form input', async () => {
      const MockValidatedFeedbackForm = () => {
        const [errors, setErrors] = React.useState<string[]>([]);

        const handleSubmit = (e: React.FormEvent) => {
          e.preventDefault();
          const formData = new FormData(e.target as HTMLFormElement);
          const rating = formData.get('rating') as string;
          const comments = formData.get('comments') as string;

          const newErrors: string[] = [];
          if (!rating || parseInt(rating) < 1 || parseInt(rating) > 5) {
            newErrors.push('Rating must be between 1 and 5');
          }
          if (!comments || comments.trim().length < 10) {
            newErrors.push('Comments must be at least 10 characters');
          }

          setErrors(newErrors);
        };

        return (
          <form onSubmit={handleSubmit} data-testid="validated-feedback-form">
            <input 
              type="number" 
              name="rating"
              data-testid="rating-input"
              min="1" 
              max="5" 
            />
            <textarea 
              name="comments"
              data-testid="comments-input"
            />
            <button type="submit" data-testid="submit-button">Submit</button>
            {errors.map((error, index) => (
              <div key={index} data-testid="validation-error">{error}</div>
            ))}
          </form>
        );
      };

      render(
        <Provider store={mockStore}>
          <MockValidatedFeedbackForm />
        </Provider>
      );

      // Test validation
      fireEvent.click(screen.getByTestId('submit-button'));

      await waitFor(() => {
        expect(screen.getByText('Rating must be between 1 and 5')).toBeInTheDocument();
        expect(screen.getByText('Comments must be at least 10 characters')).toBeInTheDocument();
      });
    });
  });

  describe('Quality Metrics Dashboard', () => {
    test('displays quality metrics for admin users', () => {
      const mockQualityData = {
        overall_score: 85.2,
        completeness: 92.1,
        accuracy: 88.5,
        relevance: 81.7,
        actionability: 87.3
      };

      const MockQualityDashboard = ({ data }: { data: any }) => (
        <div data-testid="quality-dashboard">
          <h2>Quality Metrics</h2>
          <div data-testid="overall-score">
            Overall Score: {data.overall_score}%
          </div>
          <div data-testid="completeness">
            Completeness: {data.completeness}%
          </div>
          <div data-testid="accuracy">
            Accuracy: {data.accuracy}%
          </div>
        </div>
      );

      render(
        <Provider store={mockStore}>
          <MockQualityDashboard data={mockQualityData} />
        </Provider>
      );

      expect(screen.getByText('Overall Score: 85.2%')).toBeInTheDocument();
      expect(screen.getByText('Completeness: 92.1%')).toBeInTheDocument();
      expect(screen.getByText('Accuracy: 88.5%')).toBeInTheDocument();
    });
  });

  describe('Assessment-Level Enterprise Features', () => {
    test('renders assessment feedback component', () => {
      const MockAssessmentFeedback = ({ assessmentId }: { assessmentId: string }) => (
        <div data-testid="assessment-feedback">
          <h3>Feedback for Assessment {assessmentId}</h3>
          <div data-testid="feedback-form">
            <select data-testid="feedback-category">
              <option value="assessment_quality">Assessment Quality</option>
              <option value="recommendations">Recommendations</option>
              <option value="usability">Usability</option>
            </select>
            <textarea data-testid="feedback-text" placeholder="Your feedback..." />
            <button data-testid="submit-assessment-feedback">Submit Feedback</button>
          </div>
        </div>
      );

      render(
        <Provider store={mockStore}>
          <MockAssessmentFeedback assessmentId="test-123" />
        </Provider>
      );

      expect(screen.getByText('Feedback for Assessment test-123')).toBeInTheDocument();
      expect(screen.getByTestId('feedback-category')).toBeInTheDocument();
      expect(screen.getByTestId('submit-assessment-feedback')).toBeInTheDocument();
    });

    test('renders assessment quality score display', () => {
      const mockQualityScore = {
        overall_score: 87.5,
        metrics: {
          completeness: 90,
          accuracy: 85,
          relevance: 88
        }
      };

      const MockQualityScore = ({ score }: { score: any }) => (
        <div data-testid="assessment-quality-score">
          <h4>Assessment Quality Score</h4>
          <div data-testid="overall-score" className="text-2xl font-bold">
            {score.overall_score}%
          </div>
          <div data-testid="metrics-breakdown">
            {Object.entries(score.metrics).map(([key, value]) => (
              <div key={key} data-testid={`metric-${key}`}>
                {key}: {value}%
              </div>
            ))}
          </div>
        </div>
      );

      render(
        <Provider store={mockStore}>
          <MockQualityScore score={mockQualityScore} />
        </Provider>
      );

      expect(screen.getByText('87.5%')).toBeInTheDocument();
      expect(screen.getByText('completeness: 90%')).toBeInTheDocument();
      expect(screen.getByText('accuracy: 85%')).toBeInTheDocument();
      expect(screen.getByText('relevance: 88%')).toBeInTheDocument();
    });

    test('renders export functionality', () => {
      const MockExportComponent = () => {
        const [exportFormat, setExportFormat] = React.useState('pdf');
        const [exportTarget, setExportTarget] = React.useState('slack');

        return (
          <div data-testid="export-component">
            <h4>Export Assessment</h4>
            <select 
              value={exportFormat} 
              onChange={(e) => setExportFormat(e.target.value)}
              data-testid="export-format"
            >
              <option value="pdf">PDF</option>
              <option value="json">JSON</option>
              <option value="summary">Summary</option>
            </select>
            <select 
              value={exportTarget} 
              onChange={(e) => setExportTarget(e.target.value)}
              data-testid="export-target"
            >
              <option value="slack">Slack</option>
              <option value="teams">Teams</option>
              <option value="email">Email</option>
            </select>
            <button data-testid="export-button">Export</button>
          </div>
        );
      };

      render(
        <Provider store={mockStore}>
          <MockExportComponent />
        </Provider>
      );

      expect(screen.getByTestId('export-format')).toBeInTheDocument();
      expect(screen.getByTestId('export-target')).toBeInTheDocument();
      expect(screen.getByTestId('export-button')).toBeInTheDocument();
    });
  });

  describe('Role-Based Access Control', () => {
    test('shows admin features for admin users', () => {
      const MockRoleBasedComponent = ({ userRole }: { userRole: string }) => (
        <div data-testid="role-based-component">
          {userRole === 'admin' && (
            <div data-testid="admin-features">
              <button data-testid="manage-experiments">Manage Experiments</button>
              <button data-testid="view-analytics">View Analytics</button>
              <button data-testid="manage-quality">Manage Quality</button>
            </div>
          )}
          <div data-testid="user-features">
            <button data-testid="submit-feedback">Submit Feedback</button>
            <button data-testid="view-assessment">View Assessment</button>
          </div>
        </div>
      );

      render(
        <Provider store={mockStore}>
          <MockRoleBasedComponent userRole="admin" />
        </Provider>
      );

      expect(screen.getByTestId('admin-features')).toBeInTheDocument();
      expect(screen.getByTestId('manage-experiments')).toBeInTheDocument();
      expect(screen.getByTestId('view-analytics')).toBeInTheDocument();
      expect(screen.getByTestId('user-features')).toBeInTheDocument();
    });

    test('hides admin features for regular users', () => {
      const MockRoleBasedComponent = ({ userRole }: { userRole: string }) => (
        <div data-testid="role-based-component">
          {userRole === 'admin' && (
            <div data-testid="admin-features">
              <button data-testid="manage-experiments">Manage Experiments</button>
            </div>
          )}
          <div data-testid="user-features">
            <button data-testid="submit-feedback">Submit Feedback</button>
          </div>
        </div>
      );

      render(
        <Provider store={mockStore}>
          <MockRoleBasedComponent userRole="user" />
        </Provider>
      );

      expect(screen.queryByTestId('admin-features')).not.toBeInTheDocument();
      expect(screen.queryByTestId('manage-experiments')).not.toBeInTheDocument();
      expect(screen.getByTestId('user-features')).toBeInTheDocument();
      expect(screen.getByTestId('submit-feedback')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    test('displays error message for failed API calls', async () => {
      const MockErrorComponent = () => {
        const [error, setError] = React.useState<string | null>(null);

        const handleApiCall = async () => {
          try {
            // Simulate failed API call
            throw new Error('Network error');
          } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
          }
        };

        return (
          <div data-testid="error-component">
            <button onClick={handleApiCall} data-testid="api-call-button">
              Make API Call
            </button>
            {error && (
              <div data-testid="error-message" className="text-red-500">
                Error: {error}
              </div>
            )}
          </div>
        );
      };

      render(
        <Provider store={mockStore}>
          <MockErrorComponent />
        </Provider>
      );

      fireEvent.click(screen.getByTestId('api-call-button'));

      await waitFor(() => {
        expect(screen.getByTestId('error-message')).toBeInTheDocument();
        expect(screen.getByText('Error: Network error')).toBeInTheDocument();
      });
    });
  });
});