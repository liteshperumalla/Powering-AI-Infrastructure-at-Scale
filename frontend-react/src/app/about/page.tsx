'use client';

import React from 'react';
import {
  Container,
  Typography,
  Box,
  Button,
  Card,
  CardContent,
  AppBar,
  Toolbar,
  useTheme,
  Grid,
  Divider,
} from '@mui/material';
import {
  ArrowBack,
  CloudQueue,
  Security,
  Analytics,
  Speed,
  People,
  TrendingUp,
} from '@mui/icons-material';
import { useRouter } from 'next/navigation';

export default function About() {
  const theme = useTheme();
  const router = useRouter();

  return (
    <>
      {/* Navigation Bar */}
      <AppBar position="static" elevation={1}>
        <Toolbar>
          <Button
            startIcon={<ArrowBack />}
            color="inherit"
            onClick={() => router.push('/')}
            sx={{ mr: 2 }}
          >
            Home
          </Button>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            About Infra Mind
          </Typography>
          <Button color="inherit" onClick={() => router.push('/auth/login')}>
            Login
          </Button>
          <Button
            color="inherit"
            variant="outlined"
            sx={{ ml: 1 }}
            onClick={() => router.push('/auth/register')}
          >
            Get Started
          </Button>
        </Toolbar>
      </AppBar>

      {/* Hero Section */}
      <Box
        sx={{
          background: theme.palette.mode === 'dark' 
            ? 'linear-gradient(135deg, #1565c0 0%, #1976d2 100%)'
            : 'linear-gradient(135deg, #1976d2 0%, #42a5f5 100%)',
          color: 'white',
          py: { xs: 6, md: 8 },
        }}
      >
        <Container maxWidth="lg">
          <Box sx={{ textAlign: 'center' }}>
            <Typography
              variant="h2"
              component="h1"
              gutterBottom
              sx={{ fontWeight: 'bold', mb: 2 }}
            >
              About Infra Mind
            </Typography>
            <Typography
              variant="h6"
              component="p"
              sx={{ opacity: 0.9, maxWidth: 800, mx: 'auto' }}
            >
              Empowering businesses to strategically plan, simulate, and scale their AI infrastructure with confidence through intelligent AI-powered advisory services.
            </Typography>
          </Box>
        </Container>
      </Box>

      {/* Mission Section */}
      <Container maxWidth="lg" sx={{ py: 8 }}>
        <Grid container spacing={6} alignItems="center">
          <Grid item xs={12} md={6}>
            <Typography variant="h3" component="h2" gutterBottom>
              Our Mission
            </Typography>
            <Typography variant="body1" paragraph sx={{ fontSize: '1.1rem', lineHeight: 1.7 }}>
              We believe that AI infrastructure shouldn't be a barrier to innovation. Our mission is to democratize access to enterprise-grade AI infrastructure planning and scaling through intelligent, automated advisory services.
            </Typography>
            <Typography variant="body1" paragraph sx={{ fontSize: '1.1rem', lineHeight: 1.7 }}>
              By leveraging advanced AI agents and multi-cloud expertise, we help organizations make informed decisions about their infrastructure investments, ensuring they can scale efficiently while maintaining security and compliance.
            </Typography>
          </Grid>
          <Grid item xs={12} md={6}>
            <Box
              sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                p: 4,
                bgcolor: theme.palette.mode === 'dark' ? 'grey.900' : 'grey.50',
                borderRadius: 2,
              }}
            >
              <CloudQueue sx={{ fontSize: 100, color: 'primary.main', mb: 2 }} />
              <Typography variant="h5" sx={{ textAlign: 'center', mb: 1 }}>
                AI-First Approach
              </Typography>
              <Typography variant="body1" sx={{ textAlign: 'center', opacity: 0.8 }}>
                Intelligent agents analyze your requirements and provide tailored infrastructure recommendations
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Container>

      <Divider />

      {/* What We Do Section */}
      <Container maxWidth="lg" sx={{ py: 8 }}>
        <Typography
          variant="h3"
          component="h2"
          textAlign="center"
          gutterBottom
          sx={{ mb: 6 }}
        >
          What We Do
        </Typography>
        <Grid container spacing={4}>
          <Grid item xs={12} md={4}>
            <Card sx={{ height: '100%', textAlign: 'center', p: 3 }}>
              <CardContent>
                <Analytics sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
                <Typography variant="h5" component="h3" gutterBottom>
                  Infrastructure Assessment
                </Typography>
                <Typography variant="body1">
                  Comprehensive 8-step assessment process that captures your business requirements, technical architecture, and scaling needs to provide personalized recommendations.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card sx={{ height: '100%', textAlign: 'center', p: 3 }}>
              <CardContent>
                <Security sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
                <Typography variant="h5" component="h3" gutterBottom>
                  Compliance & Security
                </Typography>
                <Typography variant="body1">
                  Built-in compliance mapping for GDPR, HIPAA, CCPA, and other regulations with automated security best practices and vulnerability assessments.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card sx={{ height: '100%', textAlign: 'center', p: 3 }}>
              <CardContent>
                <TrendingUp sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
                <Typography variant="h5" component="h3" gutterBottom>
                  Cost Optimization
                </Typography>
                <Typography variant="body1">
                  Real-time pricing analysis across multiple cloud providers with detailed cost projections and ROI modeling for informed decision making.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Container>

      <Divider />

      {/* Technology Section */}
      <Container maxWidth="lg" sx={{ py: 8 }}>
        <Typography
          variant="h3"
          component="h2"
          textAlign="center"
          gutterBottom
          sx={{ mb: 6 }}
        >
          Our Technology
        </Typography>
        <Grid container spacing={6} alignItems="center">
          <Grid item xs={12} md={6}>
            <Typography variant="h4" component="h3" gutterBottom>
              Multi-Agent AI System
            </Typography>
            <Typography variant="body1" paragraph sx={{ fontSize: '1.1rem', lineHeight: 1.7 }}>
              Our platform is powered by specialized AI agents that work together to provide comprehensive infrastructure recommendations:
            </Typography>
            <Box sx={{ pl: 2 }}>
              <Typography variant="body1" paragraph sx={{ fontSize: '1.1rem' }}>
                • <strong>CTO Agent:</strong> Strategic technology leadership and architectural decisions
              </Typography>
              <Typography variant="body1" paragraph sx={{ fontSize: '1.1rem' }}>
                • <strong>MLOps Agent:</strong> Machine learning infrastructure and model deployment
              </Typography>
              <Typography variant="body1" paragraph sx={{ fontSize: '1.1rem' }}>
                • <strong>Infrastructure Agent:</strong> Cloud platform optimization and scaling
              </Typography>
              <Typography variant="body1" paragraph sx={{ fontSize: '1.1rem' }}>
                • <strong>Compliance Agent:</strong> Security and regulatory compliance
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} md={6}>
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: 'repeat(2, 1fr)',
                gap: 2,
              }}
            >
              <Card sx={{ p: 2, textAlign: 'center' }}>
                <People sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                <Typography variant="h6">Multi-Cloud</Typography>
                <Typography variant="body2" color="text.secondary">
                  AWS, Azure, GCP, Alibaba, IBM
                </Typography>
              </Card>
              <Card sx={{ p: 2, textAlign: 'center' }}>
                <Speed sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                <Typography variant="h6">Real-Time</Typography>
                <Typography variant="body2" color="text.secondary">
                  Live pricing & analysis
                </Typography>
              </Card>
              <Card sx={{ p: 2, textAlign: 'center' }}>
                <Security sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                <Typography variant="h6">Secure</Typography>
                <Typography variant="body2" color="text.secondary">
                  Enterprise-grade security
                </Typography>
              </Card>
              <Card sx={{ p: 2, textAlign: 'center' }}>
                <Analytics sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                <Typography variant="h6">Intelligent</Typography>
                <Typography variant="body2" color="text.secondary">
                  AI-powered insights
                </Typography>
              </Card>
            </Box>
          </Grid>
        </Grid>
      </Container>

      {/* CTA Section */}
      <Box sx={{ 
        bgcolor: theme.palette.mode === 'dark' ? 'grey.900' : 'grey.50', 
        py: 8 
      }}>
        <Container maxWidth="md" sx={{ textAlign: 'center' }}>
          <Typography variant="h4" component="h2" gutterBottom>
            Ready to Get Started?
          </Typography>
          <Typography 
            variant="h6" 
            color="text.secondary" 
            sx={{ mb: 4 }}
          >
            Join organizations worldwide who trust Infra Mind for their AI infrastructure planning
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              size="large"
              onClick={() => router.push('/assessment')}
              sx={{ px: 4, py: 1.5 }}
            >
              Start Assessment
            </Button>
            <Button
              variant="outlined"
              size="large"
              onClick={() => router.push('/auth/register')}
              sx={{ px: 4, py: 1.5 }}
            >
              Create Account
            </Button>
          </Box>
        </Container>
      </Box>

      {/* Footer */}
      <Box sx={{ bgcolor: 'grey.900', color: 'white', py: 4 }}>
        <Container maxWidth="lg">
          <Box
            sx={{
              display: 'flex',
              flexDirection: { xs: 'column', md: 'row' },
              justifyContent: 'space-between',
              alignItems: { xs: 'flex-start', md: 'center' },
              gap: 2,
            }}
          >
            <Box>
              <Typography variant="h6" gutterBottom>
                Infra Mind
              </Typography>
              <Typography variant="body2" color="grey.400">
                Empowering businesses to strategically plan and scale their AI infrastructure with confidence.
              </Typography>
            </Box>
            <Typography variant="body2" color="grey.400">
              © 2025 Infra Mind. All rights reserved.
            </Typography>
          </Box>
        </Container>
      </Box>
    </>
  );
}