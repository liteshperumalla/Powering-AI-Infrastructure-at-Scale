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
  useMediaQuery,
  Stack,
} from '@mui/material';
import {
  CloudQueue,
  Security,
  Analytics,
  Speed,
} from '@mui/icons-material';
import { useRouter } from 'next/navigation';
export default function Home() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const router = useRouter();

  return (
    <>
      {/* Navigation Bar */}
      <AppBar position="static" elevation={1}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Infra Mind
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
          background: 'linear-gradient(135deg, #1976d2 0%, #42a5f5 100%)',
          color: 'white',
          py: { xs: 8, md: 12 },
        }}
      >
        <Container maxWidth="lg">
          <Box
            sx={{
              display: 'flex',
              flexDirection: { xs: 'column', md: 'row' },
              alignItems: 'center',
              gap: 4,
            }}
          >
            <Box sx={{ flex: 1 }}>
              <Typography
                variant={isMobile ? 'h3' : 'h2'}
                component="h1"
                gutterBottom
                sx={{ fontWeight: 'bold' }}
              >
                Powering AI Infrastructure at Scale
              </Typography>
              <Typography
                variant="h6"
                component="p"
                sx={{ mb: 4, opacity: 0.9 }}
              >
                Intelligent AI-powered advisory platform that empowers businesses to strategically plan, simulate, and scale their AI infrastructure with confidence.
              </Typography>
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                <Button
                  variant="contained"
                  size="large"
                  sx={{
                    bgcolor: 'white',
                    color: 'primary.main',
                    '&:hover': { bgcolor: 'grey.100' },
                  }}
                  onClick={() => router.push('/auth/login')}
                >
                  Start Assessment
                </Button>
                <Button
                  variant="outlined"
                  size="large"
                  sx={{
                    borderColor: 'white',
                    color: 'white',
                    '&:hover': { borderColor: 'grey.300', bgcolor: 'rgba(255,255,255,0.1)' },
                  }}
                  onClick={() => router.push('/auth/login')}
                >
                  Learn More
                </Button>
              </Stack>
            </Box>
            <Box sx={{ flex: 1, display: { xs: 'none', md: 'block' } }}>
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center',
                  alignItems: 'center',
                  height: 300,
                  bgcolor: 'rgba(255,255,255,0.1)',
                  borderRadius: 2,
                  p: 3,
                }}
              >
                <CloudQueue sx={{ fontSize: 80, mb: 2, opacity: 0.8 }} />
                <Typography variant="h5" sx={{ mb: 1, textAlign: 'center' }}>
                  AI-Powered Infrastructure
                </Typography>
                <Typography variant="body1" sx={{ opacity: 0.8, textAlign: 'center' }}>
                  Get intelligent recommendations for your cloud infrastructure
                </Typography>
              </Box>
            </Box>
          </Box>
        </Container>
      </Box>

      {/* Features Section */}
      <Container maxWidth="lg" sx={{ py: 8 }}>
        <Typography
          variant="h3"
          component="h2"
          textAlign="center"
          gutterBottom
          sx={{ mb: 6 }}
        >
          Core Capabilities
        </Typography>
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: {
              xs: '1fr',
              sm: 'repeat(2, 1fr)',
              md: 'repeat(4, 1fr)',
            },
            gap: 3,
          }}
        >
          <Card sx={{ height: '100%', textAlign: 'center', p: 2 }}>
            <CardContent>
              <CloudQueue sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
              <Typography variant="h6" component="h3" gutterBottom>
                Multi-Cloud Intelligence
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Deep expertise across AWS, Azure, and GCP platforms with real-time pricing and service recommendations.
              </Typography>
            </CardContent>
          </Card>
          <Card sx={{ height: '100%', textAlign: 'center', p: 2 }}>
            <CardContent>
              <Security sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
              <Typography variant="h6" component="h3" gutterBottom>
                Compliance Mapping
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Regulatory awareness for GDPR, HIPAA, CCPA compliance with automated compliance validation.
              </Typography>
            </CardContent>
          </Card>
          <Card sx={{ height: '100%', textAlign: 'center', p: 2 }}>
            <CardContent>
              <Analytics sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
              <Typography variant="h6" component="h3" gutterBottom>
                AI Agent System
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Multi-agent coordination with specialized roles: CTO, MLOps, Infrastructure, and Compliance experts.
              </Typography>
            </CardContent>
          </Card>
          <Card sx={{ height: '100%', textAlign: 'center', p: 2 }}>
            <CardContent>
              <Speed sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
              <Typography variant="h6" component="h3" gutterBottom>
                Simulation & Modeling
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Infrastructure scaling scenarios and cost projections with detailed ROI analysis.
              </Typography>
            </CardContent>
          </Card>
        </Box>
      </Container>

      {/* CTA Section */}
      <Box sx={{ bgcolor: 'grey.50', py: 8 }}>
        <Container maxWidth="md" sx={{ textAlign: 'center' }}>
          <Typography variant="h4" component="h2" gutterBottom>
            Ready to Scale Your AI Infrastructure?
          </Typography>
          <Typography variant="h6" color="text.secondary" sx={{ mb: 4 }}>
            Get personalized recommendations from our AI advisory platform
          </Typography>
          <Button
            variant="contained"
            size="large"
            onClick={() => router.push('/auth/login')}
            sx={{ px: 4, py: 1.5 }}
          >
            Start Your Assessment
          </Button>
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
              © 2024 Infra Mind. All rights reserved.
            </Typography>
          </Box>
        </Container>
      </Box>
    </>
  );
}
