'use client';

import React, { useState, useEffect } from 'react';
import {
    Box,
    Card,
    CardContent,
    Typography,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Alert,
    CircularProgress,
    Button
} from '@mui/material';
import { useRouter } from 'next/navigation';
import { useDispatch } from 'react-redux';
import { apiClient } from '../services/api';
import { setCurrentAssessment } from '../store/slices/assessmentSlice';

interface AssessmentSelectorProps {
    redirectPath: string;
    title?: string;
    description?: string;
}

const AssessmentSelector: React.FC<AssessmentSelectorProps> = ({
    redirectPath,
    title = "Select Assessment",
    description = "Please select an assessment to view this page"
}) => {
    const [assessments, setAssessments] = useState<any[]>([]);
    const [selectedId, setSelectedId] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const router = useRouter();
    const dispatch = useDispatch();

    useEffect(() => {
        loadAssessments();
    }, []);

    const loadAssessments = async () => {
        try {
            const response = await apiClient.getAssessments();
            setAssessments(response.assessments || []);
        } catch (err: any) {
            setError(err.message || 'Failed to load assessments');
        } finally {
            setLoading(false);
        }
    };

    const handleSelect = () => {
        if (selectedId) {
            const assessment = assessments.find(a => a.id === selectedId);
            if (assessment) {
                dispatch(setCurrentAssessment(assessment));
            }
            router.push(`${redirectPath}?assessment_id=${selectedId}`);
        }
    };

    if (loading) {
        return (
            <Box sx={{ p: 3, textAlign: 'center' }}>
                <CircularProgress />
                <Typography sx={{ mt: 2 }}>Loading assessments...</Typography>
            </Box>
        );
    }

    if (error) {
        return (
            <Box sx={{ p: 3 }}>
                <Alert severity="error">{error}</Alert>
            </Box>
        );
    }

    return (
        <Box sx={{ p: 3, maxWidth: 600, mx: 'auto' }}>
            <Card>
                <CardContent>
                    <Typography variant="h5" color="text.primary" gutterBottom>
                        {title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                        {description}
                    </Typography>

                    {assessments.length === 0 ? (
                        <Alert severity="info">
                            No assessments found. Please create an assessment first.
                        </Alert>
                    ) : (
                        <>
                            <FormControl fullWidth sx={{ mb: 2 }}>
                                <InputLabel>Assessment</InputLabel>
                                <Select
                                    value={selectedId}
                                    label="Assessment"
                                    onChange={(e) => setSelectedId(e.target.value)}
                                >
                                    {assessments.map((assessment) => (
                                        <MenuItem key={assessment.id} value={assessment.id}>
                                            {assessment.title} - {assessment.status}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                            <Button
                                variant="contained"
                                fullWidth
                                onClick={handleSelect}
                                disabled={!selectedId}
                            >
                                Continue
                            </Button>
                        </>
                    )}
                </CardContent>
            </Card>
        </Box>
    );
};

export default AssessmentSelector;
