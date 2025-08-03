'use client';

import React, { useRef, useEffect, useState } from 'react';
import * as d3 from 'd3';
import { Box, Card, CardContent, Typography, FormControl, InputLabel, Select, MenuItem, Tooltip, IconButton } from '@mui/material';
import { ZoomIn, ZoomOut, Refresh } from '@mui/icons-material';

interface DataPoint {
    id: string;
    x: number;
    y: number;
    category: string;
    value: number;
    label: string;
    metadata?: Record<string, unknown>;
}

interface D3InteractiveChartProps {
    data: DataPoint[];
    title: string;
    width?: number;
    height?: number;
    chartType?: 'scatter' | 'bubble' | 'network';
    colorScheme?: string[];
    onPointClick?: (point: DataPoint) => void;
    onZoom?: (transform: d3.ZoomTransform) => void;
}

export default function D3InteractiveChart({
    data,
    title,
    width = 800,
    height = 500,
    chartType = 'scatter',
    colorScheme = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#00ff88'],
    onPointClick,
    onZoom,
}: D3InteractiveChartProps) {
    const svgRef = useRef<SVGSVGElement>(null);
    const [selectedCategory, setSelectedCategory] = useState<string>('all');
    const [zoomLevel, setZoomLevel] = useState(1);
    const [hoveredPoint, setHoveredPoint] = useState<DataPoint | null>(null);

    const margin = { top: 20, right: 30, bottom: 40, left: 50 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const categories = Array.from(new Set(data.map(d => d.category)));
    const filteredData = selectedCategory === 'all'
        ? data
        : data.filter(d => d.category === selectedCategory);

    useEffect(() => {
        if (!svgRef.current || !filteredData.length) return;

        const svg = d3.select(svgRef.current);
        svg.selectAll('*').remove();

        // Create scales
        const xScale = d3.scaleLinear()
            .domain(d3.extent(filteredData, d => d.x) as [number, number])
            .range([0, innerWidth]);

        const yScale = d3.scaleLinear()
            .domain(d3.extent(filteredData, d => d.y) as [number, number])
            .range([innerHeight, 0]);

        const colorScale = d3.scaleOrdinal()
            .domain(categories)
            .range(colorScheme);

        const sizeScale = d3.scaleSqrt()
            .domain(d3.extent(filteredData, d => d.value) as [number, number])
            .range([4, 20]);

        // Create main group
        const g = svg.append('g')
            .attr('transform', `translate(${margin.left},${margin.top})`);

        // Add axes
        const xAxis = d3.axisBottom(xScale);
        const yAxis = d3.axisLeft(yScale);

        g.append('g')
            .attr('class', 'x-axis')
            .attr('transform', `translate(0,${innerHeight})`)
            .call(xAxis);

        g.append('g')
            .attr('class', 'y-axis')
            .call(yAxis);

        // Add grid lines
        g.append('g')
            .attr('class', 'grid')
            .attr('transform', `translate(0,${innerHeight})`)
            .call(xAxis.tickSize(-innerHeight).tickFormat(() => ''))
            .style('stroke-dasharray', '3,3')
            .style('opacity', 0.3);

        g.append('g')
            .attr('class', 'grid')
            .call(yAxis.tickSize(-innerWidth).tickFormat(() => ''))
            .style('stroke-dasharray', '3,3')
            .style('opacity', 0.3);

        // Create zoom behavior
        const zoom = d3.zoom<SVGSVGElement, unknown>()
            .scaleExtent([0.5, 5])
            .on('zoom', (event) => {
                const { transform } = event;
                setZoomLevel(transform.k);

                // Update scales
                const newXScale = transform.rescaleX(xScale);
                const newYScale = transform.rescaleY(yScale);

                // Update axes
                g.select('.x-axis').call(xAxis.scale(newXScale));
                g.select('.y-axis').call(yAxis.scale(newYScale));

                // Update points
                g.selectAll('.data-point')
                    .attr('cx', (d: DataPoint) => newXScale(d.x))
                    .attr('cy', (d: DataPoint) => newYScale(d.y));

                if (onZoom) {
                    onZoom(transform);
                }
            });

        svg.call(zoom);

        // Add data points
        const points = g.selectAll('.data-point')
            .data(filteredData)
            .enter()
            .append('circle')
            .attr('class', 'data-point')
            .attr('cx', d => xScale(d.x))
            .attr('cy', d => yScale(d.y))
            .attr('r', d => chartType === 'bubble' ? sizeScale(d.value) : 6)
            .attr('fill', d => colorScale(d.category) as string)
            .attr('stroke', '#fff')
            .attr('stroke-width', 2)
            .style('cursor', 'pointer')
            .style('opacity', 0.8);

        // Add interactions
        points
            .on('mouseover', function (event, d) {
                d3.select(this)
                    .transition()
                    .duration(200)
                    .attr('r', (d: DataPoint) => (chartType === 'bubble' ? sizeScale(d.value) : 6) * 1.5)
                    .style('opacity', 1);

                setHoveredPoint(d);
            })
            .on('mouseout', function (event, d) {
                d3.select(this)
                    .transition()
                    .duration(200)
                    .attr('r', (d: DataPoint) => chartType === 'bubble' ? sizeScale(d.value) : 6)
                    .style('opacity', 0.8);

                setHoveredPoint(null);
            })
            .on('click', function (event, d) {
                if (onPointClick) {
                    onPointClick(d);
                }
            });

        // Add animations
        points
            .style('opacity', 0)
            .transition()
            .duration(1000)
            .delay((d, i) => i * 50)
            .style('opacity', 0.8);

    }, [filteredData, innerWidth, innerHeight, chartType, colorScheme, onPointClick, onZoom]);

    const handleZoomIn = () => {
        const svg = d3.select(svgRef.current);
        svg.transition().call(
            (d3.zoom<SVGSVGElement, unknown>().scaleBy as (transition: d3.Transition<SVGSVGElement, unknown, null, undefined>, k: number) => void),
            1.5
        );
    };

    const handleZoomOut = () => {
        const svg = d3.select(svgRef.current);
        svg.transition().call(
            (d3.zoom<SVGSVGElement, unknown>().scaleBy as (transition: d3.Transition<SVGSVGElement, unknown, null, undefined>, k: number) => void),
            1 / 1.5
        );
    };

    const handleReset = () => {
        const svg = d3.select(svgRef.current);
        svg.transition().call(
            (d3.zoom<SVGSVGElement, unknown>().transform as (transition: d3.Transition<SVGSVGElement, unknown, null, undefined>, transform: d3.ZoomTransform) => void),
            d3.zoomIdentity
        );
        setZoomLevel(1);
    };

    return (
        <Card>
            <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6">{title}</Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <FormControl size="small" sx={{ minWidth: 120 }}>
                            <InputLabel>Category</InputLabel>
                            <Select
                                value={selectedCategory}
                                label="Category"
                                onChange={(e) => setSelectedCategory(e.target.value)}
                            >
                                <MenuItem value="all">All</MenuItem>
                                {categories.map(category => (
                                    <MenuItem key={category} value={category}>
                                        {category}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                        <Tooltip title="Zoom In">
                            <IconButton onClick={handleZoomIn} size="small">
                                <ZoomIn />
                            </IconButton>
                        </Tooltip>
                        <Tooltip title="Zoom Out">
                            <IconButton onClick={handleZoomOut} size="small">
                                <ZoomOut />
                            </IconButton>
                        </Tooltip>
                        <Tooltip title="Reset Zoom">
                            <IconButton onClick={handleReset} size="small">
                                <Refresh />
                            </IconButton>
                        </Tooltip>
                    </Box>
                </Box>

                <Box sx={{ position: 'relative' }}>
                    <svg
                        ref={svgRef}
                        width={width}
                        height={height}
                        style={{ border: '1px solid #e0e0e0', borderRadius: '4px' }}
                    />

                    {hoveredPoint && (
                        <Box
                            sx={{
                                position: 'absolute',
                                top: 10,
                                left: 10,
                                bgcolor: 'background.paper',
                                border: '1px solid #e0e0e0',
                                borderRadius: 1,
                                p: 1,
                                boxShadow: 2,
                                zIndex: 1000,
                            }}
                        >
                            <Typography variant="body2" fontWeight="bold">
                                {hoveredPoint.label}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                                Category: {hoveredPoint.category}
                            </Typography>
                            <Typography variant="caption" display="block" color="text.secondary">
                                Value: {hoveredPoint.value}
                            </Typography>
                            <Typography variant="caption" display="block" color="text.secondary">
                                Position: ({hoveredPoint.x.toFixed(2)}, {hoveredPoint.y.toFixed(2)})
                            </Typography>
                        </Box>
                    )}
                </Box>

                <Box sx={{ mt: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="caption" color="text.secondary">
                        Zoom: {(zoomLevel * 100).toFixed(0)}% | Points: {filteredData.length}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                        {categories.map((category, index) => (
                            <Box
                                key={category}
                                sx={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 0.5,
                                }}
                            >
                                <Box
                                    sx={{
                                        width: 12,
                                        height: 12,
                                        bgcolor: colorScheme[index % colorScheme.length],
                                        borderRadius: '50%',
                                    }}
                                />
                                <Typography variant="caption">{category}</Typography>
                            </Box>
                        ))}
                    </Box>
                </Box>
            </CardContent>
        </Card>
    );
}