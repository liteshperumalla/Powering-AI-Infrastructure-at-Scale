'use client';

import React, { useState, useEffect } from 'react';
import {
    Container,
    Typography,
    Box,
    Card,
    CardContent,
    Grid,
    Chip,
    Button,
    TextField,
    InputAdornment,
    ToggleButton,
    ToggleButtonGroup,
    Rating,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    List,
    ListItem,
    ListItemText,
    Divider,
} from '@mui/material';
import {
    Cloud,
    Search,
    FilterList,
    CloudQueue,
    Computer,
    Storage,
} from '@mui/icons-material';
import ResponsiveLayout from '@/components/ResponsiveLayout';
import ProtectedRoute from '@/components/ProtectedRoute';
import { apiClient, CloudService } from '@/services/api';

export default function CloudServicesPage() {
    const [services, setServices] = useState<CloudService[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedProvider, setSelectedProvider] = useState<string>('');
    const [selectedCategory, setSelectedCategory] = useState<string>('');
    const [availableCategories, setAvailableCategories] = useState<string[]>([]);
    const [selectedService, setSelectedService] = useState<CloudService | null>(null);
    const [detailsOpen, setDetailsOpen] = useState(false);

    // Load categories on component mount
    useEffect(() => {
        const loadCategories = async () => {
            try {
                const categoriesResponse = await apiClient.getCloudServiceCategories();
                setAvailableCategories(categoriesResponse.categories.map(cat => cat.name));
            } catch (error) {
                console.error('Failed to load categories:', error);
                // Fallback to common categories
                setAvailableCategories(['Compute', 'Database', 'Storage', 'AI/ML', 'Containers', 'Serverless']);
            }
        };
        
        loadCategories();
    }, []);

    useEffect(() => {
        const loadServices = async () => {
            try {
                setLoading(true);
                
                // Build filters from current state
                const filters: any = {};
                if (selectedProvider) {
                    filters.provider = selectedProvider;
                }
                if (selectedCategory) {
                    filters.category = selectedCategory;
                }
                if (searchQuery) {
                    filters.search = searchQuery;
                }
                
                // Debug logging
                console.log('🔍 Cloud Services Filter Debug:', {
                    selectedProvider,
                    selectedCategory,
                    searchQuery,
                    filters
                });
                
                // Use timeout with Promise.race - increased timeout for real SDK calls
                const timeoutPromise = new Promise((_, reject) => {
                    setTimeout(() => reject(new Error('Request timeout')), 65000); // 65 seconds for real cloud SDK calls
                });
                
                const apiPromise = apiClient.getCloudServices({
                    ...filters,
                    limit: 50 // Get up to 50 services
                });
                
                const response = await Promise.race([apiPromise, timeoutPromise]);
                
                // Check if response has services array
                if (response && response.services && Array.isArray(response.services)) {
                    console.log('📡 API Response:', {
                        servicesCount: response.services.length,
                        firstService: response.services[0]?.name,
                        firstProvider: response.services[0]?.provider,
                        allProviders: [...new Set(response.services.map(s => s.provider))]
                    });
                    
                    setServices(response.services);
                } else {
                    console.log('⚠️ Invalid response structure, using fallback data');
                    throw new Error('Invalid response structure');
                }
            } catch (error) {
                console.error('Failed to load services:', error);
                // Check if it's a timeout error
                if (error.message === 'Request timeout') {
                    console.log('⏱️ Request timed out, using fallback data');
                    // Provide fallback data for common services
                    setServices([
                        {
                            id: 'aws-ec2',
                            name: 'Amazon EC2',
                            provider: 'AWS',
                            category: 'Compute',
                            description: 'Scalable virtual servers in the cloud',
                            pricing_model: 'Pay-as-you-use',
                            pricing: {
                                starting_price: '0.0116',
                                unit: 'per hour'
                            },
                            regions: ['us-east-1', 'us-west-2', 'eu-west-1'],
                            features: ['Auto Scaling', 'Load Balancing', 'Spot Instances'],
                            compliance: ['SOC2', 'ISO27001', 'GDPR'],
                            region_availability: ['us-east-1', 'us-west-2', 'eu-west-1'],
                            use_cases: ['Web applications', 'Big data', 'Machine learning'],
                            integration: ['CloudWatch', 'IAM', 'VPC'],
                            cost_optimization_tips: ['Use Reserved Instances', 'Right-size instances'],
                            rating: 4.5
                        },
                        {
                            id: 'azure-vm',
                            name: 'Azure Virtual Machines',
                            provider: 'Azure',
                            category: 'Compute',
                            description: 'On-demand scalable computing resources',
                            pricing_model: 'Pay-as-you-use',
                            pricing: {
                                starting_price: '0.012',
                                unit: 'per hour'
                            },
                            regions: ['eastus', 'westus2', 'westeurope'],
                            features: ['Auto Scaling', 'Availability Sets', 'Managed Disks'],
                            compliance: ['SOC2', 'ISO27001', 'HIPAA'],
                            region_availability: ['eastus', 'westus2', 'westeurope'],
                            use_cases: ['Enterprise apps', 'Development', 'Testing'],
                            integration: ['Azure Monitor', 'Azure AD', 'VNet'],
                            cost_optimization_tips: ['Use B-series for variable workloads'],
                            rating: 4.3
                        },
                        {
                            id: 'gcp-compute',
                            name: 'Google Compute Engine',
                            provider: 'GCP',
                            category: 'Compute',
                            description: 'High-performance virtual machines',
                            pricing_model: 'Pay-as-you-use',
                            pricing: {
                                starting_price: '0.010',
                                unit: 'per hour'
                            },
                            regions: ['us-central1', 'us-west1', 'europe-west1'],
                            features: ['Preemptible VMs', 'Live Migration', 'Custom Machine Types'],
                            compliance: ['SOC2', 'ISO27001', 'GDPR'],
                            region_availability: ['us-central1', 'us-west1', 'europe-west1'],
                            use_cases: ['Batch processing', 'Web services', 'Analytics'],
                            integration: ['Cloud Monitoring', 'IAM', 'VPC'],
                            cost_optimization_tips: ['Use preemptible instances', 'Sustained use discounts'],
                            rating: 4.4
                        },
                        {
                            id: 'aws-s3',
                            name: 'Amazon S3',
                            provider: 'AWS',
                            category: 'Storage',
                            description: 'Object storage built to store and retrieve any amount of data',
                            pricing_model: 'Pay-as-you-use',
                            pricing: {
                                starting_price: '0.023',
                                unit: 'per GB/month'
                            },
                            regions: ['Global'],
                            features: ['99.999999999% durability', 'Versioning', 'Cross-region replication'],
                            compliance: ['SOC2', 'PCI DSS', 'HIPAA'],
                            region_availability: ['Global'],
                            use_cases: ['Backup', 'Data archiving', 'Content distribution'],
                            integration: ['CloudFront', 'Lambda', 'Glacier'],
                            cost_optimization_tips: ['Use appropriate storage classes', 'Lifecycle policies'],
                            rating: 4.7
                        }
                    ]);
                } else {
                    // Fallback to empty array for other errors
                    setServices([]);
                }
            } finally {
                setLoading(false);
            }
        };

        loadServices();
    }, [selectedProvider, selectedCategory, searchQuery]); // Re-load when filters change

    const handleProviderChange = (
        event: React.MouseEvent<HTMLElement>,
        newProvider: string,
    ) => {
        setSelectedProvider(newProvider);
    };

    const handleServiceDetails = (service: CloudService) => {
        setSelectedService(service);
        setDetailsOpen(true);
    };

    const handleCloseDetails = () => {
        setDetailsOpen(false);
        setSelectedService(null);
    };

    const getProviderIcon = (provider: string) => {
        switch (provider) {
            case 'AWS': return <CloudQueue />;
            case 'Azure': return <Computer />;
            case 'GCP': return <Storage />;
            case 'Alibaba': 
            case 'alibaba': return <Cloud />;
            case 'IBM': 
            case 'ibm': return <CloudQueue />;
            default: return <Cloud />;
        }
    };

    const getProviderColor = (provider: string) => {
        switch (provider) {
            case 'AWS': return '#FF9900';
            case 'Azure': return '#0078D4';
            case 'GCP': return '#4285F4';
            case 'Alibaba':
            case 'alibaba': return '#FF6A00';
            case 'IBM':
            case 'ibm': return '#006699';
            default: return '#666';
        }
    };

    // Remove local filtering since it's now done by the API
    const filteredServices = services;

    return (
        <ProtectedRoute>
            <ResponsiveLayout title="Cloud Services">
                <Container maxWidth="lg" sx={{ mt: 3 }}>
                    <Box sx={{ mb: 4 }}>
                        <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                            <Cloud sx={{ fontSize: 40 }} />
                            Cloud Services Catalog
                        </Typography>
                        <Typography variant="body1" color="text.secondary">
                            Explore and compare cloud services from major providers to find the best fit for your infrastructure needs.
                        </Typography>
                    </Box>

                    {/* Filters */}
                    <Card sx={{ mb: 4 }}>
                        <CardContent>
                            <Grid container spacing={3} alignItems="center">
                                <Grid item xs={12} md={4}>
                                    <TextField
                                        fullWidth
                                        placeholder="Search services..."
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                        size="small"
                                        InputProps={{
                                            startAdornment: (
                                                <InputAdornment position="start">
                                                    <Search />
                                                </InputAdornment>
                                            ),
                                        }}
                                    />
                                </Grid>

                                <Grid item xs={12} md={8}>
                                    <Typography variant="body2" gutterBottom>
                                        Cloud Providers
                                    </Typography>
                                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                                        <ToggleButtonGroup 
                                            value={selectedProvider} 
                                            onChange={handleProviderChange}
                                            exclusive
                                            size="small"
                                        >
                                            <ToggleButton value="AWS">
                                                <CloudQueue sx={{ mr: 1 }} />
                                                AWS
                                            </ToggleButton>
                                            <ToggleButton value="Azure">
                                                <Computer sx={{ mr: 1 }} />
                                                Azure
                                            </ToggleButton>
                                            <ToggleButton value="GCP">
                                                <Storage sx={{ mr: 1 }} />
                                                GCP
                                            </ToggleButton>
                                            <ToggleButton value="Alibaba">
                                                <Cloud sx={{ mr: 1, color: '#FF6A00' }} />
                                                Alibaba
                                            </ToggleButton>
                                            <ToggleButton value="IBM">
                                                <CloudQueue sx={{ mr: 1, color: '#006699' }} />
                                                IBM
                                            </ToggleButton>
                                        </ToggleButtonGroup>
                                    </Box>
                                </Grid>

                                <Grid item xs={12}>
                                    <Typography variant="body2" gutterBottom>
                                        Category
                                    </Typography>
                                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                                        <Chip
                                            label="All"
                                            onClick={() => setSelectedCategory('')}
                                            color={selectedCategory === '' ? 'primary' : 'default'}
                                            variant={selectedCategory === '' ? 'filled' : 'outlined'}
                                            size="small"
                                        />
                                        {availableCategories.map(category => (
                                            <Chip
                                                key={category}
                                                label={category}
                                                onClick={() => setSelectedCategory(category)}
                                                color={selectedCategory === category ? 'primary' : 'default'}
                                                variant={selectedCategory === category ? 'filled' : 'outlined'}
                                                size="small"
                                            />
                                        ))}
                                    </Box>
                                </Grid>
                            </Grid>
                        </CardContent>
                    </Card>

                    {/* Services Grid */}
                    {loading ? (
                        <Box sx={{ textAlign: 'center', py: 4 }}>
                            <Typography>Loading services...</Typography>
                        </Box>
                    ) : filteredServices.length === 0 ? (
                        <Card>
                            <CardContent sx={{ textAlign: 'center', py: 6 }}>
                                <Cloud sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
                                <Typography variant="h6" gutterBottom>
                                    No Services Found
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                    Try adjusting your search criteria or filters.
                                </Typography>
                            </CardContent>
                        </Card>
                    ) : (
                        <Grid container spacing={3}>
                            {filteredServices.map((service) => (
                                <Grid item xs={12} md={6} lg={4} key={service.id}>
                                    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                                        <CardContent sx={{ flexGrow: 1 }}>
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                                                <Box sx={{ color: getProviderColor(service.provider) }}>
                                                    {getProviderIcon(service.provider)}
                                                </Box>
                                                <Typography variant="h6" sx={{ flexGrow: 1 }}>
                                                    {service.name}
                                                </Typography>
                                                <Chip 
                                                    label={service.category} 
                                                    size="small" 
                                                    variant="outlined"
                                                />
                                            </Box>

                                            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                                {service.description}
                                            </Typography>

                                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                                <Rating value={service.rating} precision={0.1} size="small" readOnly />
                                                <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                                                    ({service.rating})
                                                </Typography>
                                            </Box>

                                            {service.pricing && (
                                                <Typography variant="body2" sx={{ mb: 2 }}>
                                                    <strong>Starting at:</strong> ${service.pricing.starting_price} {service.pricing.unit}
                                                </Typography>
                                            )}

                                            <Box sx={{ mb: 2 }}>
                                                <Typography variant="body2" gutterBottom>
                                                    <strong>Key Features:</strong>
                                                </Typography>
                                                {(service.features || []).slice(0, 3).map((feature, index) => (
                                                    <Chip 
                                                        key={index}
                                                        label={feature} 
                                                        size="small" 
                                                        variant="outlined"
                                                        sx={{ mr: 0.5, mb: 0.5 }}
                                                    />
                                                ))}
                                            </Box>

                                            <Box sx={{ mb: 2 }}>
                                                <Typography variant="body2" gutterBottom>
                                                    <strong>Compliance:</strong>
                                                </Typography>
                                                {(service.compliance || []).map((comp, index) => (
                                                    <Chip 
                                                        key={index}
                                                        label={comp} 
                                                        size="small" 
                                                        color="success"
                                                        variant="outlined"
                                                        sx={{ mr: 0.5, mb: 0.5 }}
                                                    />
                                                ))}
                                            </Box>
                                        </CardContent>

                                        <Box sx={{ p: 2, pt: 0 }}>
                                            <Button 
                                                variant="outlined" 
                                                fullWidth
                                                size="small"
                                                onClick={() => handleServiceDetails(service)}
                                            >
                                                View Details
                                            </Button>
                                        </Box>
                                    </Card>
                                </Grid>
                            ))}
                        </Grid>
                    )}

                    {/* Service Details Dialog */}
                    <Dialog 
                        open={detailsOpen} 
                        onClose={handleCloseDetails}
                        maxWidth="md"
                        fullWidth
                    >
                        {selectedService && (
                            <>
                                <DialogTitle>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                        <Box sx={{ color: getProviderColor(selectedService.provider) }}>
                                            {getProviderIcon(selectedService.provider)}
                                        </Box>
                                        <Typography variant="h5">
                                            {selectedService.name}
                                        </Typography>
                                        <Chip 
                                            label={selectedService.category} 
                                            size="small" 
                                            variant="outlined"
                                        />
                                    </Box>
                                </DialogTitle>
                                
                                <DialogContent>
                                    <Box sx={{ mb: 3 }}>
                                        <Typography variant="body1" paragraph>
                                            {selectedService.description}
                                        </Typography>
                                        
                                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                            <Rating value={selectedService.rating} precision={0.1} size="small" readOnly />
                                            <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                                                ({selectedService.rating})
                                            </Typography>
                                        </Box>
                                    </Box>

                                    <Grid container spacing={3}>
                                        <Grid item xs={12} md={6}>
                                            <Typography variant="h6" gutterBottom>
                                                Pricing
                                            </Typography>
                                            <Typography variant="body2">
                                                <strong>Model:</strong> {selectedService.pricing?.model || selectedService.pricing_model}
                                            </Typography>
                                            {selectedService.pricing && (
                                                <Typography variant="body2">
                                                    <strong>Starting Price:</strong> ${selectedService.pricing.starting_price} {selectedService.pricing.unit}
                                                </Typography>
                                            )}
                                        </Grid>

                                        <Grid item xs={12} md={6}>
                                            <Typography variant="h6" gutterBottom>
                                                Features
                                            </Typography>
                                            <List dense>
                                                {(selectedService.features || []).map((feature, index) => (
                                                    <ListItem key={index} sx={{ py: 0.5 }}>
                                                        <Typography variant="body2">• {feature}</Typography>
                                                    </ListItem>
                                                ))}
                                            </List>
                                        </Grid>

                                        <Grid item xs={12} md={6}>
                                            <Typography variant="h6" gutterBottom>
                                                Compliance
                                            </Typography>
                                            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                                                {(selectedService.compliance || []).map((comp, index) => (
                                                    <Chip 
                                                        key={index}
                                                        label={comp} 
                                                        size="small" 
                                                        color="success"
                                                        variant="outlined"
                                                    />
                                                ))}
                                            </Box>
                                        </Grid>

                                        <Grid item xs={12} md={6}>
                                            <Typography variant="h6" gutterBottom>
                                                Region Availability
                                            </Typography>
                                            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                                                {(selectedService.region_availability || []).slice(0, 5).map((region, index) => (
                                                    <Chip 
                                                        key={index}
                                                        label={region} 
                                                        size="small" 
                                                        variant="outlined"
                                                    />
                                                ))}
                                                {(selectedService.region_availability || []).length > 5 && (
                                                    <Chip 
                                                        label={`+${(selectedService.region_availability || []).length - 5} more`}
                                                        size="small" 
                                                        variant="outlined"
                                                        color="primary"
                                                    />
                                                )}
                                            </Box>
                                        </Grid>

                                        {selectedService.use_cases && (
                                            <Grid item xs={12}>
                                                <Typography variant="h6" gutterBottom>
                                                    Use Cases
                                                </Typography>
                                                <List dense>
                                                    {(selectedService.use_cases || []).map((useCase, index) => (
                                                        <ListItem key={index} sx={{ py: 0.5 }}>
                                                            <Typography variant="body2">• {useCase}</Typography>
                                                        </ListItem>
                                                    ))}
                                                </List>
                                            </Grid>
                                        )}

                                        {selectedService.integration && (
                                            <Grid item xs={12}>
                                                <Typography variant="h6" gutterBottom>
                                                    Integrations
                                                </Typography>
                                                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                                                    {(selectedService.integration || []).map((integration, index) => (
                                                        <Chip 
                                                            key={index}
                                                            label={integration} 
                                                            size="small" 
                                                            variant="outlined"
                                                            color="primary"
                                                        />
                                                    ))}
                                                </Box>
                                            </Grid>
                                        )}
                                    </Grid>
                                </DialogContent>
                                
                                <DialogActions>
                                    <Button onClick={handleCloseDetails}>
                                        Close
                                    </Button>
                                    <Button variant="contained">
                                        Add to Assessment
                                    </Button>
                                </DialogActions>
                            </>
                        )}
                    </Dialog>
                </Container>
            </ResponsiveLayout>
        </ProtectedRoute>
    );
}