'use client';

import React, { useState, useEffect } from 'react';
import {
    Box,
    Paper,
    Typography,
    Drawer,
    List,
    ListItem,
    ListItemButton,
    ListItemText,
    ListItemIcon,
    Divider,
    IconButton,
    Toolbar,
    AppBar,
    Breadcrumbs,
    Link,
    Chip,
    Card,
    CardContent,
    Accordion,
    AccordionSummary,
    AccordionDetails,
    Dialog,
    DialogTitle,
    DialogContent,
    Button,
    Tooltip,
    Zoom,
    Fade,
} from '@mui/material';
import {
    Menu as MenuIcon,
    ChevronRight,
    ExpandMore,
    Fullscreen,
    FullscreenExit,
    ZoomIn,
    ZoomOut,
    Print,
    Share,
    BookmarkBorder,
    Bookmark,
    TrendingUp,
    BarChart,
    PieChart,
    Timeline,
    Assessment,
    Security,
    CloudQueue,
    Close,
} from '@mui/icons-material';

interface DrillDownData {
    [key: string]: any;
}

interface ChartConfig {
    type: 'bar' | 'pie' | 'line' | 'area';
    data: any[];
    title: string;
    description?: string;
}

interface ReportSection {
    id: string;
    title: string;
    content: string;
    contentType: 'markdown' | 'html';
    order: number;
    isInteractive: boolean;
    drillDownData?: DrillDownData;
    chartsConfig?: ChartConfig[];
}

interface InteractiveReportData {
    report: {
        id: string;
        title: string;
        version: string;
        brandingConfig: any;
        customCss?: string;
    };
    sections: ReportSection[];
    navigation: Array<{
        id: string;
        title: string;
        order: number;
        hasInteractiveContent: boolean;
    }>;
}

interface InteractiveReportViewerProps {
    reportData: InteractiveReportData;
    onClose?: () => void;
}

const DRAWER_WIDTH = 280;

const getSectionIcon = (title: string) => {
    const lowerTitle = title.toLowerCase();
    if (lowerTitle.includes('executive') || lowerTitle.includes('summary')) return <Assessment />;
    if (lowerTitle.includes('cost') || lowerTitle.includes('financial')) return <TrendingUp />;
    if (lowerTitle.includes('technical') || lowerTitle.includes('architecture')) return <CloudQueue />;
    if (lowerTitle.includes('security') || lowerTitle.includes('compliance')) return <Security />;
    if (lowerTitle.includes('chart') || lowerTitle.includes('analysis')) return <BarChart />;
    return <ChevronRight />;
};

const InteractiveReportViewer: React.FC<InteractiveReportViewerProps> = ({
    reportData,
    onClose
}) => {
    const [drawerOpen, setDrawerOpen] = useState(true);
    const [currentSectionId, setCurrentSectionId] = useState(reportData.sections[0]?.id || '');
    const [fullscreen, setFullscreen] = useState(false);
    const [zoomLevel, setZoomLevel] = useState(100);
    const [bookmarkedSections, setBookmarkedSections] = useState<Set<string>>(new Set());
    const [drillDownDialog, setDrillDownDialog] = useState<{
        open: boolean;
        data: any;
        title: string;
    }>({ open: false, data: null, title: '' });

    const currentSection = reportData.sections.find(s => s.id === currentSectionId);

    useEffect(() => {
        // Apply custom CSS if provided
        if (reportData.report.customCss) {
            const styleElement = document.createElement('style');
            styleElement.textContent = reportData.report.customCss;
            document.head.appendChild(styleElement);

            return () => {
                document.head.removeChild(styleElement);
            };
        }
    }, [reportData.report.customCss]);

    const handleSectionClick = (sectionId: string) => {
        setCurrentSectionId(sectionId);
    };

    const handleDrillDown = (data: any, title: string) => {
        setDrillDownDialog({
            open: true,
            data,
            title
        });
    };

    const toggleBookmark = (sectionId: string) => {
        const newBookmarks = new Set(bookmarkedSections);
        if (newBookmarks.has(sectionId)) {
            newBookmarks.delete(sectionId);
        } else {
            newBookmarks.add(sectionId);
        }
        setBookmarkedSections(newBookmarks);
    };

    const handleZoom = (direction: 'in' | 'out' | 'reset') => {
        if (direction === 'in' && zoomLevel < 200) {
            setZoomLevel(zoomLevel + 10);
        } else if (direction === 'out' && zoomLevel > 50) {
            setZoomLevel(zoomLevel - 10);
        } else if (direction === 'reset') {
            setZoomLevel(100);
        }
    };

    const renderInteractiveContent = (section: ReportSection) => {
        if (!section.isInteractive) {
            return (
                <Box
                    dangerouslySetInnerHTML={{ __html: section.content }}
                    sx={{ fontSize: `${zoomLevel}%` }}
                />
            );
        }

        return (
            <Box sx={{ fontSize: `${zoomLevel}%` }}>
                <Box dangerouslySetInnerHTML={{ __html: section.content }} />

                {/* Interactive Charts */}
                {section.chartsConfig && section.chartsConfig.length > 0 && (
                    <Box sx={{ mt: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            Interactive Analysis
                        </Typography>
                        {section.chartsConfig.map((chart, index) => (
                            <Card key={index} sx={{ mb: 2 }}>
                                <CardContent>
                                    <Typography variant="subtitle1" gutterBottom>
                                        {chart.title}
                                    </Typography>
                                    {chart.description && (
                                        <Typography variant="body2" color="text.secondary" paragraph>
                                            {chart.description}
                                        </Typography>
                                    )}
                                    <Box
                                        sx={{
                                            height: 300,
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            bgcolor: 'grey.50',
                                            border: '1px dashed',
                                            borderColor: 'grey.300',
                                            cursor: 'pointer'
                                        }}
                                        onClick={() => handleDrillDown(chart.data, chart.title)}
                                    >
                                        <Box sx={{ textAlign: 'center' }}>
                                            {chart.type === 'bar' && <BarChart sx={{ fontSize: 48, color: 'primary.main' }} />}
                                            {chart.type === 'pie' && <PieChart sx={{ fontSize: 48, color: 'primary.main' }} />}
                                            {chart.type === 'line' && <Timeline sx={{ fontSize: 48, color: 'primary.main' }} />}
                                            <Typography variant="body2" sx={{ mt: 1 }}>
                                                Click to explore {chart.type} chart
                                            </Typography>
                                        </Box>
                                    </Box>
                                </CardContent>
                            </Card>
                        ))}
                    </Box>
                )}

                {/* Drill-down Data */}
                {section.drillDownData && Object.keys(section.drillDownData).length > 0 && (
                    <Box sx={{ mt: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            Detailed Analysis
                        </Typography>
                        {Object.entries(section.drillDownData).map(([key, value]) => (
                            <Accordion key={key}>
                                <AccordionSummary expandIcon={<ExpandMore />}>
                                    <Typography variant="subtitle2">
                                        {key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                                    </Typography>
                                </AccordionSummary>
                                <AccordionDetails>
                                    <Box
                                        sx={{
                                            p: 2,
                                            bgcolor: 'grey.50',
                                            borderRadius: 1,
                                            cursor: 'pointer'
                                        }}
                                        onClick={() => handleDrillDown(value, key)}
                                    >
                                        <Typography variant="body2">
                                            Click to explore detailed data
                                        </Typography>
                                    </Box>
                                </AccordionDetails>
                            </Accordion>
                        ))}
                    </Box>
                )}
            </Box>
        );
    };

    return (
        <Box sx={{ display: 'flex', height: '100vh' }}>
            {/* Navigation Drawer */}
            <Drawer
                variant="persistent"
                anchor="left"
                open={drawerOpen}
                sx={{
                    width: DRAWER_WIDTH,
                    flexShrink: 0,
                    '& .MuiDrawer-paper': {
                        width: DRAWER_WIDTH,
                        boxSizing: 'border-box',
                    },
                }}
            >
                <Toolbar>
                    <Typography variant="h6" noWrap component="div">
                        Navigation
                    </Typography>
                </Toolbar>
                <Divider />
                <List>
                    {reportData.navigation.map((navItem) => (
                        <ListItem key={navItem.id} disablePadding>
                            <ListItemButton
                                selected={currentSectionId === navItem.id}
                                onClick={() => handleSectionClick(navItem.id)}
                            >
                                <ListItemIcon>
                                    {getSectionIcon(navItem.title)}
                                </ListItemIcon>
                                <ListItemText
                                    primary={navItem.title}
                                    secondary={navItem.hasInteractiveContent ? 'Interactive' : null}
                                />
                                {navItem.hasInteractiveContent && (
                                    <Chip size="small" label="Interactive" color="primary" />
                                )}
                                {bookmarkedSections.has(navItem.id) && (
                                    <Bookmark color="primary" />
                                )}
                            </ListItemButton>
                        </ListItem>
                    ))}
                </List>
            </Drawer>

            {/* Main Content */}
            <Box
                component="main"
                sx={{
                    flexGrow: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    transition: 'margin 0.3s',
                    marginLeft: drawerOpen ? 0 : `-${DRAWER_WIDTH}px`,
                }}
            >
                {/* Top Toolbar */}
                <AppBar position="static" color="default" elevation={1}>
                    <Toolbar>
                        <IconButton
                            edge="start"
                            onClick={() => setDrawerOpen(!drawerOpen)}
                            sx={{ mr: 2 }}
                        >
                            <MenuIcon />
                        </IconButton>

                        <Breadcrumbs sx={{ flexGrow: 1 }}>
                            <Link color="inherit" href="#" onClick={() => { }}>
                                {reportData.report.title}
                            </Link>
                            <Typography color="text.primary">
                                {currentSection?.title}
                            </Typography>
                        </Breadcrumbs>

                        <Box sx={{ display: 'flex', gap: 1 }}>
                            <Tooltip title="Bookmark Section">
                                <IconButton
                                    onClick={() => toggleBookmark(currentSectionId)}
                                    color={bookmarkedSections.has(currentSectionId) ? 'primary' : 'default'}
                                >
                                    {bookmarkedSections.has(currentSectionId) ? <Bookmark /> : <BookmarkBorder />}
                                </IconButton>
                            </Tooltip>

                            <Tooltip title="Zoom Out">
                                <IconButton onClick={() => handleZoom('out')} disabled={zoomLevel <= 50}>
                                    <ZoomOut />
                                </IconButton>
                            </Tooltip>

                            <Typography variant="body2" sx={{ alignSelf: 'center', minWidth: 40 }}>
                                {zoomLevel}%
                            </Typography>

                            <Tooltip title="Zoom In">
                                <IconButton onClick={() => handleZoom('in')} disabled={zoomLevel >= 200}>
                                    <ZoomIn />
                                </IconButton>
                            </Tooltip>

                            <Tooltip title="Print">
                                <IconButton onClick={() => window.print()}>
                                    <Print />
                                </IconButton>
                            </Tooltip>

                            <Tooltip title="Share">
                                <IconButton>
                                    <Share />
                                </IconButton>
                            </Tooltip>

                            <Tooltip title={fullscreen ? "Exit Fullscreen" : "Fullscreen"}>
                                <IconButton onClick={() => setFullscreen(!fullscreen)}>
                                    {fullscreen ? <FullscreenExit /> : <Fullscreen />}
                                </IconButton>
                            </Tooltip>

                            {onClose && (
                                <Tooltip title="Close">
                                    <IconButton onClick={onClose}>
                                        <Close />
                                    </IconButton>
                                </Tooltip>
                            )}
                        </Box>
                    </Toolbar>
                </AppBar>

                {/* Content Area */}
                <Box
                    sx={{
                        flexGrow: 1,
                        p: 3,
                        overflow: 'auto',
                        bgcolor: 'background.default',
                    }}
                >
                    {currentSection && (
                        <Fade in={true} timeout={300}>
                            <Paper sx={{ p: 3, minHeight: '100%' }}>
                                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                    <Typography variant="h4" component="h1" sx={{ flexGrow: 1 }}>
                                        {currentSection.title}
                                    </Typography>
                                    {currentSection.isInteractive && (
                                        <Chip
                                            label="Interactive Content"
                                            color="primary"
                                            variant="outlined"
                                        />
                                    )}
                                </Box>

                                {renderInteractiveContent(currentSection)}
                            </Paper>
                        </Fade>
                    )}
                </Box>
            </Box>

            {/* Drill-down Dialog */}
            <Dialog
                open={drillDownDialog.open}
                onClose={() => setDrillDownDialog({ open: false, data: null, title: '' })}
                maxWidth="lg"
                fullWidth
            >
                <DialogTitle>
                    {drillDownDialog.title}
                    <IconButton
                        onClick={() => setDrillDownDialog({ open: false, data: null, title: '' })}
                        sx={{ position: 'absolute', right: 8, top: 8 }}
                    >
                        <Close />
                    </IconButton>
                </DialogTitle>
                <DialogContent>
                    <Box sx={{ minHeight: 400, p: 2 }}>
                        {drillDownDialog.data && (
                            <pre style={{ whiteSpace: 'pre-wrap', fontSize: '14px' }}>
                                {JSON.stringify(drillDownDialog.data, null, 2)}
                            </pre>
                        )}
                    </Box>
                </DialogContent>
            </Dialog>
        </Box>
    );
};

export default InteractiveReportViewer;