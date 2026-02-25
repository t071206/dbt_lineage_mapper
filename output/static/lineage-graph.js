/**
 * DBT Lineage Graph Visualization
 */

// Global variables
let cy = null;
let elements = [];
let projectColors = {};
let currentLayout = 'dagre';
let edgeBundling = false;
let edgeStyle = 'bezier';
let groupByProject = false;

/**
 * Initialize the Cytoscape graph with the provided elements
 */
function initializeGraph(graphElements) {
    // Store the elements
    elements = graphElements;
    
    // Generate colors for projects
    generateProjectColors();
    
    // Initialize Cytoscape
    cy = cytoscape({
        container: document.getElementById('cy'),
        elements: elements,
        style: getGraphStyles(),
        layout: getLayoutOptions(currentLayout),
        wheelSensitivity: 0.2
    });
    
    // Register event handlers
    registerEventHandlers();
    
    // Fit the graph to the viewport
    cy.fit();
    cy.center();
}

/**
 * Generate a color palette for projects
 */
function generateProjectColors() {
    // Get all unique projects
    const projects = new Set();
    elements.forEach(ele => {
        if (ele.group === 'nodes' && ele.data.project) {
            projects.add(ele.data.project);
        }
    });
    
    // Define a color palette
    const colorPalette = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ];
    
    // Assign colors to projects
    let colorIndex = 0;
    projects.forEach(project => {
        projectColors[project] = colorPalette[colorIndex % colorPalette.length];
        colorIndex++;
    });
    
    // Update the project legend
    updateProjectLegend();
}

/**
 * Update the project legend with colors
 */
function updateProjectLegend() {
    const legendDiv = document.getElementById('project-legend');
    legendDiv.innerHTML = '';
    
    // Add legend items for each project
    Object.keys(projectColors).sort().forEach(project => {
        const color = projectColors[project];
        const item = document.createElement('div');
        item.className = 'legend-item';
        
        const colorBox = document.createElement('div');
        colorBox.className = 'legend-color';
        colorBox.style.backgroundColor = color;
        
        const label = document.createElement('div');
        label.textContent = project;
        
        item.appendChild(colorBox);
        item.appendChild(label);
        legendDiv.appendChild(item);
    });
    
    // Add project options to the selector
    const selector = document.getElementById('project-selector');
    selector.innerHTML = '<option value="all">All Projects</option>';
    
    Object.keys(projectColors).sort().forEach(project => {
        const option = document.createElement('option');
        option.value = project;
        option.textContent = project;
        selector.appendChild(option);
    });
}

/**
 * Get the graph styles for Cytoscape
 */
function getGraphStyles() {
    return [
        // Node styles
        {
            selector: 'node',
            style: {
                'label': 'data(label)',
                'text-valign': 'center',
                'text-halign': 'center',
                'color': '#fff',
                'text-outline-width': 2,
                'text-outline-color': function(ele) {
                    return getNodeColor(ele);
                },
                'background-color': function(ele) {
                    return getNodeColor(ele);
                },
                'width': 'label',
                'height': 'label',
                'padding': '10px',
                'shape': function(ele) {
                    return ele.data('type') === 'source' ? 'rectangle' : 'round-rectangle';
                },
                'border-width': function(ele) {
                    return ele.data('missing') ? 3 : 0;
                },
                'border-color': '#ff0000',
                'border-style': 'solid'
            }
        },
        // Source node styles
        {
            selector: 'node.source',
            style: {
                'background-image-opacity': 0.5
            }
        },
        // Edge styles
        {
            selector: 'edge',
            style: {
                'width': 2,
                'line-color': '#333',
                'target-arrow-color': '#333',
                'target-arrow-shape': 'triangle',
                'curve-style': edgeStyle,
                'arrow-scale': 1.5
            }
        },
        // Cross-project edge styles
        {
            selector: 'edge.crossProject',
            style: {
                'line-color': '#ff0000',
                'target-arrow-color': '#ff0000'
            }
        },
        // Inferred edge styles
        {
            selector: 'edge[inferred = true]',
            style: {
                'line-style': 'dashed',
                'line-dash-pattern': [6, 3]
            }
        }
    ];
}

/**
 * Get the color for a node based on its project and type
 */
function getNodeColor(ele) {
    const data = ele.data();
    
    // External reference nodes have a white background with red border
    if (data.missing) {
        return 'white';
    }
    
    // Source nodes have a grey background
    if (data.type === 'source') {
        return '#7f7f7f';
    }
    
    // Regular nodes get their project color
    return projectColors[data.project] || '#333';
}

/**
 * Get the layout options for the specified algorithm
 */
function getLayoutOptions(algorithm) {
    const commonOptions = {
        fit: true,
        padding: 50
    };
    
    switch (algorithm) {
        case 'dagre':
            return {
                name: 'dagre',
                rankDir: 'LR',
                nodeSep: 80,
                rankSep: 150,
                padding: 100,
                edgeSep: 10,
                marginX: 20,
                marginY: 20,
                ...commonOptions
            };
        case 'klay':
            return {
                name: 'klay',
                rankDir: 'LR',
                spacing: 50,
                borderSpacing: 10,
                ...commonOptions
            };
        case 'breadthfirst':
            return {
                name: 'breadthfirst',
                directed: true,
                spacingFactor: 1.75,
                ...commonOptions
            };
        case 'cose':
            return {
                name: 'cose',
                idealEdgeLength: 150,
                nodeOverlap: 20,
                refresh: 20,
                fit: true,
                padding: 50,
                randomize: false,
                componentSpacing: 100,
                nodeRepulsion: 400000,
                edgeElasticity: 100,
                nestingFactor: 5,
                gravity: 80,
                numIter: 1000,
                initialTemp: 200,
                coolingFactor: 0.95,
                minTemp: 1.0
            };
        default:
            return {
                name: 'dagre',
                rankDir: 'LR',
                ...commonOptions
            };
    }
}

/**
 * Register event handlers for the graph and UI elements
 */
function registerEventHandlers() {
    // Layout algorithm selector
    document.getElementById('layout-algorithm').addEventListener('change', function(evt) {
        currentLayout = evt.target.value;
        applyLayout();
    });
    
    // Edge style selector
    document.getElementById('edge-style').addEventListener('change', function(evt) {
        edgeStyle = evt.target.value;
        updateEdgeStyle();
    });
    
    // Edge bundling toggle
    document.getElementById('toggle-bundling').addEventListener('change', function(evt) {
        edgeBundling = evt.target.checked;
        toggleEdgeBundling();
    });
    
    // Apply layout button
    document.getElementById('apply-layout').addEventListener('click', function() {
        applyLayout();
    });
    
    // Fit button
    document.getElementById('fit-button').addEventListener('click', function() {
        cy.fit();
        cy.center();
    });
    
    // Toggle control panel
    document.getElementById('toggle-control-panel').addEventListener('click', function() {
        const panel = document.getElementById('control-panel');
        panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
    });
}

/**
 * Apply the current layout to the graph
 */
function applyLayout() {
    // Get layout options
    const options = getLayoutOptions(currentLayout);
    
    // Apply layout
    cy.layout(options).run();
}

/**
 * Update the edge style
 */
function updateEdgeStyle() {
    cy.style()
        .selector('edge')
        .style({
            'curve-style': edgeStyle
        })
        .update();
}

/**
 * Toggle edge bundling
 */
function toggleEdgeBundling() {
    if (edgeBundling) {
        cy.edges().unbundled();
        cy.edgeBundle({
            bundleEdges: true,
            bundlingStrength: 0.7,
            bundlingSeparation: 50,
            bundlingStiffness: 0.9,
            bundlingNodeDist: 80,
            bundleEdgesMaxIterations: 50
        });
    } else {
        cy.edges().unbundled();
    }
}

// Initialize when the page loads
document.addEventListener('DOMContentLoaded', function() {
    // The elements will be provided by the template
    if (typeof elementsJson !== 'undefined') {
        try {
            console.log("Initializing graph with elements:", elementsJson);
            
            // Check if the container exists
            const container = document.getElementById('cy');
            if (!container) {
                console.error("Graph container element with ID 'cy' not found!");
                return;
            }
            
            // Check if Cytoscape is loaded
            if (typeof cytoscape === 'undefined') {
                console.error("Cytoscape library not loaded!");
                return;
            }
            
            // Initialize the graph
            initializeGraph(elementsJson);
            
            console.log("Graph initialization completed successfully");
        } catch (error) {
            console.error("Error initializing graph:", error);
            
            // Display error message on the page
            const container = document.getElementById('cy');
            if (container) {
                container.innerHTML = `
                    <div style="padding: 20px; color: red; text-align: center;">
                        <h3>Error initializing graph</h3>
                        <p>${error.message}</p>
                        <p>Please check the console for more details.</p>
                    </div>
                `;
            }
        }
    } else {
        console.error("Graph elements data (elementsJson) is not defined!");
        
        // Display error message on the page
        const container = document.getElementById('cy');
        if (container) {
            container.innerHTML = `
                <div style="padding: 20px; color: red; text-align: center;">
                    <h3>Error initializing graph</h3>
                    <p>Graph elements data is not defined.</p>
                    <p>Please check the console for more details.</p>
                </div>
            `;
        }
    }
});
