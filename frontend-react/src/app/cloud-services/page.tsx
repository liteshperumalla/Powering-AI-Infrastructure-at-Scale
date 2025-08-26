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
import Navigation from '@/components/Navigation';
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
                
                const response = await apiClient.getCloudServices({
                    ...filters,
                    limit: 50 // Get up to 50 services
                });
                
                console.log('📡 API Response:', {
                    servicesCount: response.services.length,
                    firstService: response.services[0]?.name,
                    firstProvider: response.services[0]?.provider,
                    allProviders: [...new Set(response.services.map(s => s.provider))]
                });
                
                setServices(response.services);
            } catch (error) {
                console.error('Failed to load services:', error);
                // Fallback to empty array instead of showing error
                setServices([]);
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
            <Navigation title="Cloud Services">
                <Container maxWidth="lg">
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

                                            <Typography variant="body2" sx={{ mb: 2 }}>
                                                <strong>Starting at:</strong> ${service.pricing.starting_price} {service.pricing.unit}
                                            </Typography>

                                            <Box sx={{ mb: 2 }}>
                                                <Typography variant="body2" gutterBottom>
                                                    <strong>Key Features:</strong>
                                                </Typography>
                                                {service.features.slice(0, 3).map((feature, index) => (
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
                                                {service.compliance.map((comp, index) => (
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
                                                <strong>Model:</strong> {selectedService.pricing.model}
                                            </Typography>
                                            <Typography variant="body2">
                                                <strong>Starting Price:</strong> ${selectedService.pricing.starting_price} {selectedService.pricing.unit}
                                            </Typography>
                                        </Grid>

                                        <Grid item xs={12} md={6}>
                                            <Typography variant="h6" gutterBottom>
                                                Features
                                            </Typography>
                                            <List dense>
                                                {selectedService.features.map((feature, index) => (
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
                                                {selectedService.compliance.map((comp, index) => (
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
                                                {selectedService.region_availability.slice(0, 5).map((region, index) => (
                                                    <Chip 
                                                        key={index}
                                                        label={region} 
                                                        size="small" 
                                                        variant="outlined"
                                                    />
                                                ))}
                                                {selectedService.region_availability.length > 5 && (
                                                    <Chip 
                                                        label={`+${selectedService.region_availability.length - 5} more`}
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
                                                    {selectedService.use_cases.map((useCase, index) => (
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
                                                    {selectedService.integration.map((integration, index) => (
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
            </Navigation>
        </ProtectedRoute>
    );
}