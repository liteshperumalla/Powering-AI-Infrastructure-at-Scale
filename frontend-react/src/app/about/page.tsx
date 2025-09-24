'use client';

import React from 'react';
import {
  Container,
  Typography,
  Box,
  Button,
  Card,
  CardContent,
  useTheme,
  Grid,
  Divider,
} from '@mui/material';
import {
  CloudQueue,
  Security,
  Analytics,
  Speed,
  People,
  TrendingUp,
} from '@mui/icons-material';
import { useRouter } from 'next/navigation';
import ResponsiveLayout from '@/components/ResponsiveLayout';

export default function About() {
  const theme = useTheme();
  const router = useRouter();

  return (
    <ResponsiveLayout title="About Infra Mind" fullWidth>

      {/* Hero Section */}
      <Box
        sx={{
          background: `linear-gradient(135deg, ${theme.palette.primary.main}10, ${theme.palette.secondary.main}10)`,
          minHeight: { xs: '60vh', md: '70vh' },
          display: 'flex',
          alignItems: 'center',
          position: 'relative',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'radial-gradient(circle at 30% 40%, rgba(59, 130, 246, 0.1) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(139, 92, 246, 0.1) 0%, transparent 50%)',
            pointerEvents: 'none',
          }
        }}
      >
        <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
          <Box sx={{ textAlign: 'center' }}>
            <Typography
              variant="h2"
              component="h1"
              fontWeight={700}
              gutterBottom
              sx={{ 
                background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                mb: 3,
              }}
            >
              About Infra Mind
            </Typography>
            <Typography
              variant="h6"
              component="p"
              color="text.secondary"
              sx={{ maxWidth: 800, mx: 'auto' }}
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
              We believe that AI infrastructure shouldn&apos;t be a barrier to innovation. Our mission is to democratize access to enterprise-grade AI infrastructure planning and scaling through intelligent, automated advisory services.
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
            <Card sx={{ 
              height: '100%', 
              textAlign: 'center', 
              p: 3,
              transition: 'all 0.3s ease-in-out',
              '&:hover': {
                transform: 'translateY(-8px)',
                boxShadow: 4,
              }
            }}>
              <CardContent sx={{ flex: 1 }}>
                <Box
                  sx={{
                    width: 64,
                    height: 64,
                    bgcolor: theme.palette.primary.main,
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mx: 'auto',
                    mb: 2,
                  }}
                >
                  <Analytics sx={{ fontSize: 32, color: 'white' }} />
                </Box>
                <Typography variant="h5" component="h3" gutterBottom fontWeight={600}>
                  Infrastructure Assessment
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Comprehensive 8-step assessment process that captures your business requirements, technical architecture, and scaling needs to provide personalized recommendations.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card sx={{ 
              height: '100%', 
              textAlign: 'center', 
              p: 3,
              transition: 'all 0.3s ease-in-out',
              '&:hover': {
                transform: 'translateY(-8px)',
                boxShadow: 4,
              }
            }}>
              <CardContent sx={{ flex: 1 }}>
                <Box
                  sx={{
                    width: 64,
                    height: 64,
                    bgcolor: theme.palette.success.main,
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mx: 'auto',
                    mb: 2,
                  }}
                >
                  <Security sx={{ fontSize: 32, color: 'white' }} />
                </Box>
                <Typography variant="h5" component="h3" gutterBottom fontWeight={600}>
                  Compliance & Security
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Built-in compliance mapping for GDPR, HIPAA, CCPA, and other regulations with automated security best practices and vulnerability assessments.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card sx={{ 
              height: '100%', 
              textAlign: 'center', 
              p: 3,
              transition: 'all 0.3s ease-in-out',
              '&:hover': {
                transform: 'translateY(-8px)',
                boxShadow: 4,
              }
            }}>
              <CardContent sx={{ flex: 1 }}>
                <Box
                  sx={{
                    width: 64,
                    height: 64,
                    bgcolor: theme.palette.secondary.main,
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mx: 'auto',
                    mb: 2,
                  }}
                >
                  <TrendingUp sx={{ fontSize: 32, color: 'white' }} />
                </Box>
                <Typography variant="h5" component="h3" gutterBottom fontWeight={600}>
                  Cost Optimization
                </Typography>
                <Typography variant="body1" color="text.secondary">
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
              <Card sx={{ 
                p: 2, 
                textAlign: 'center',
                transition: 'all 0.3s ease-in-out',
                '&:hover': {
                  transform: 'scale(1.05)',
                  boxShadow: 3,
                }
              }}>
                <Box sx={{ color: theme.palette.primary.main, mb: 1 }}>
                  <People sx={{ fontSize: 40 }} />
                </Box>
                <Typography variant="h6" fontWeight={600}>Multi-Cloud</Typography>
                <Typography variant="body2" color="text.secondary">
                  AWS, Azure, GCP, Alibaba, IBM
                </Typography>
              </Card>
              <Card sx={{ 
                p: 2, 
                textAlign: 'center',
                transition: 'all 0.3s ease-in-out',
                '&:hover': {
                  transform: 'scale(1.05)',
                  boxShadow: 3,
                }
              }}>
                <Box sx={{ color: theme.palette.warning.main, mb: 1 }}>
                  <Speed sx={{ fontSize: 40 }} />
                </Box>
                <Typography variant="h6" fontWeight={600}>Real-Time</Typography>
                <Typography variant="body2" color="text.secondary">
                  Live pricing & analysis
                </Typography>
              </Card>
              <Card sx={{ 
                p: 2, 
                textAlign: 'center',
                transition: 'all 0.3s ease-in-out',
                '&:hover': {
                  transform: 'scale(1.05)',
                  boxShadow: 3,
                }
              }}>
                <Box sx={{ color: theme.palette.success.main, mb: 1 }}>
                  <Security sx={{ fontSize: 40 }} />
                </Box>
                <Typography variant="h6" fontWeight={600}>Secure</Typography>
                <Typography variant="body2" color="text.secondary">
                  Enterprise-grade security
                </Typography>
              </Card>
              <Card sx={{ 
                p: 2, 
                textAlign: 'center',
                transition: 'all 0.3s ease-in-out',
                '&:hover': {
                  transform: 'scale(1.05)',
                  boxShadow: 3,
                }
              }}>
                <Box sx={{ color: theme.palette.secondary.main, mb: 1 }}>
                  <Analytics sx={{ fontSize: 40 }} />
                </Box>
                <Typography variant="h6" fontWeight={600}>Intelligent</Typography>
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
              onClick={() => router.push('/assessments')}
              sx={{
                borderRadius: 3,
                px: 4,
                py: 1.5,
                fontSize: '1.1rem',
                textTransform: 'none',
                fontWeight: 600,
              }}
            >
              Start Assessment
            </Button>
            <Button
              variant="outlined"
              size="large"
              onClick={() => router.push('/auth/login')}
              sx={{
                borderRadius: 3,
                px: 4,
                py: 1.5,
                fontSize: '1.1rem',
                textTransform: 'none',
                fontWeight: 600,
              }}
            >
              Sign In
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
    </ResponsiveLayout>
  );
}