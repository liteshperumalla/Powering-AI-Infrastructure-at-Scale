# Data Visualization Components

This document describes the data visualization components implemented for the Infra Mind AI Infrastructure Advisory Platform.

## Overview

The visualization system provides comprehensive data representation for:
- Multi-cloud cost comparisons
- Service performance analysis
- Infrastructure assessment results
- Recommendation tables with detailed comparisons
- Professional report previews

## Components

### 1. CostComparisonChart

**Purpose**: Visualizes cost comparisons across cloud providers (AWS, Azure, GCP)

**Features**:
- Bar chart and pie chart views
- Stacked cost breakdown (compute, storage, networking)
- Interactive tooltips with detailed cost information
- Provider color coding
- Cost summary with visual indicators

**Props**:
```typescript
interface CostComparisonChartProps {
    data: CostData[];
    title?: string;
    showBreakdown?: boolean;
}
```

**Usage**:
```tsx
<CostComparisonChart
    data={costData}
    title="Monthly Cost Comparison"
    showBreakdown={true}
/>
```

### 2. RecommendationScoreChart

**Purpose**: Multi-dimensional analysis of service recommendations using radar and line charts

**Features**:
- Radar chart for multi-dimensional comparison
- Line chart for trend analysis
- Interactive view switching
- Performance metrics across 6 dimensions:
  - Cost Efficiency
  - Performance
  - Scalability
  - Security
  - Compliance
  - Business Alignment

**Props**:
```typescript
interface RecommendationScoreChartProps {
    data: ScoreData[];
    title?: string;
}
```

### 3. AssessmentResultsChart

**Purpose**: Displays infrastructure assessment results with current vs target scores

**Features**:
- Bar chart, area chart, and pie chart views
- Current score vs target score comparison
- Improvement percentage indicators
- Overall assessment score calculation
- Category-wise breakdown

**Props**:
```typescript
interface AssessmentResultsChartProps {
    data: AssessmentData[];
    title?: string;
    showComparison?: boolean;
}
```

### 4. RecommendationTable

**Purpose**: Detailed tabular view of service recommendations with expandable details

**Features**:
- Sortable and filterable table
- Expandable rows with pros/cons analysis
- Provider color coding
- Confidence scoring with star ratings
- Business alignment progress bars
- Implementation complexity indicators
- Cost trend analysis

**Props**:
```typescript
interface RecommendationTableProps {
    recommendations: ServiceRecommendation[];
    title?: string;
}
```

### 5. ReportPreview

**Purpose**: Professional preview of generated reports with key metrics and export options

**Features**:
- Report metadata display
- Key findings and recommendations summary
- Estimated savings and compliance scores
- Section overview with icons
- Export functionality (PDF, view full report)

**Props**:
```typescript
interface ReportPreviewProps {
    report: ReportData;
    onDownload?: (reportId: string) => void;
    onView?: (reportId: string) => void;
}
```

## Technology Stack

- **Recharts**: Primary charting library for all visualizations
- **Material-UI**: UI components and theming
- **TypeScript**: Type safety and better development experience
- **React**: Component framework

## Chart Types Supported

1. **Bar Charts**: Cost comparisons, assessment scores
2. **Pie Charts**: Cost distribution, assessment categories
3. **Radar Charts**: Multi-dimensional service analysis
4. **Line Charts**: Trend analysis and performance metrics
5. **Area Charts**: Cumulative data visualization

## Interactive Features

- **View Switching**: Toggle between different chart types
- **Hover Tooltips**: Detailed information on hover
- **Expandable Tables**: Detailed analysis in table rows
- **Color Coding**: Consistent provider and category identification
- **Responsive Design**: Works on desktop and mobile devices

## Data Flow

```
Backend APIs → Data Processing → Chart Components → User Interface
```

1. **Data Collection**: Real-time data from cloud provider APIs
2. **Processing**: Data transformation and aggregation
3. **Visualization**: Interactive charts and tables
4. **User Interaction**: Filtering, sorting, and detailed views

## Usage Examples

### Dashboard Integration

```tsx
// Dashboard with multiple visualization components
<Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 3 }}>
    <CostComparisonChart data={costData} />
    <RecommendationScoreChart data={scoreData} />
</Box>
<AssessmentResultsChart data={assessmentData} />
<RecommendationTable recommendations={recommendations} />
```

### Standalone Demo

Visit `/visualization-demo` to see all components in action with sample data.

## Customization

### Theming

Components inherit from Material-UI theme:

```tsx
// Custom theme colors are automatically applied
const theme = createTheme({
    palette: {
        primary: { main: '#1976d2' },
        secondary: { main: '#dc004e' },
    },
});
```

### Provider Colors

Consistent color scheme across all components:
- **AWS**: #FF9900 (Orange)
- **Azure**: #0078D4 (Blue)
- **GCP**: #4285F4 (Google Blue)

## Performance Considerations

- **Lazy Loading**: Components load data on demand
- **Memoization**: React.memo used for expensive calculations
- **Responsive Containers**: Charts adapt to container size
- **Efficient Re-renders**: Optimized state management

## Testing

Comprehensive test suite includes:
- Component rendering tests
- Data transformation tests
- User interaction tests
- Accessibility tests

Run tests:
```bash
npm test
```

## Future Enhancements

1. **Real-time Updates**: WebSocket integration for live data
2. **Export Options**: Additional formats (Excel, CSV)
3. **Advanced Filtering**: More granular data filtering
4. **Custom Dashboards**: User-configurable layouts
5. **Animation**: Smooth transitions and loading states

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Accessibility

- ARIA labels for screen readers
- Keyboard navigation support
- High contrast mode compatibility
- Focus management for interactive elements